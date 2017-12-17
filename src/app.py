import pydash as py_

from src.bittrex import Bittrex
from src.messenger import Messenger
from src.database import Database
from src.logger import logger
from src.directory_utilities import get_json_from_file


secrets_file_directory = 'database/secrets.json'
secrets_template = {
    "bittrex": {
        "bittrex_key": "BITTREX_API_KEY",
        "bittrex_secret": "BITTREX_SECRET"
    },
    "gmail": {
        "address_list": [
            "EXAMPLE_RECIPIENT_1@GMAIL.COM",
            "EXAMPLE_RECIPIENT_2@GMAIL.COM",
            "ETC..."
        ],
        "username": "EXAMPLE_EMAIL@GMAIL.COM",
        "password": "GMAIL_PASSWORD"
    }
}
secrets = get_json_from_file(secrets_file_directory, secrets_template)
if secrets == secrets_template:
    print('Please completed the `secrets.json` file in your `database` directory')
    exit()

Bittrex = Bittrex(secrets)
Messenger = Messenger(secrets)
Database = Database()


def get_markets(main_market_filter=None):
    """
    Gets all the Bittrex markets and filters them based on the main market filter

    :param main_market_filter: Main market to filter on (ex: BTC, ETH, USDT)
    :type main_market_filter: str

    :return: All Bittrex markets (with filter applied, if any)
    :rtype : list
    """

    markets = Bittrex.get_markets()
    if not markets['success']:
        logger.error('Failed to fetch Bittrex markets')
        exit()

    markets = markets['result']
    if main_market_filter is not None:
        market_check = main_market_filter + '-'
        markets = py_.filter_(markets, lambda market: market_check in market['MarketName'])
    markets = py_.map_(markets, lambda market: market['MarketName'])
    return markets


def get_current_price(coin_pair, price_type):
    """
    Gets current market price for a coin pair

    :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
    :type coin_pair: str
    :param price_type: The type of price to get (one of: 'ask', 'bid')
    :type price_type: str

    :return: Coin pair's current market price
    :rtype : float
    """

    coin_summary = Bittrex.get_market_summary(coin_pair)
    if not coin_summary['success']:
        logger.error('Failed to fetch Bittrex market summary for the {} market'.format(coin_pair))
        return None
    if price_type == 'ask':
        return coin_summary['result'][0]['Ask']
    if price_type == 'bid':
        return coin_summary['result'][0]['Bid']
    return coin_summary['result'][0]['Last']


def get_current_24hr_volume(coin_pair):
    """
    Gets current 24 hour market volume for a coin pair

    :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
    :type coin_pair: str

    :return: Coin pair's current 24 hour market volume
    :rtype : float
    """

    coin_summary = Bittrex.get_market_summary(coin_pair)
    if not coin_summary['success']:
        logger.error('Failed to fetch Bittrex market summary for the {} market'.format(coin_pair))
        return None
    return coin_summary['result'][0]['BaseVolume']


def get_closing_prices(coin_pair, period, unit):
    """
    Returns closing prices within a specified time frame for a coin pair

    :type coin_pair: str
    :type period: int
    :type unit: str

    :return: Array of closing prices
    """

    historical_data = Bittrex.get_historical_data(coin_pair, period, unit)
    closing_prices = []
    for i in historical_data:
        closing_prices.append(i['C'])
    return closing_prices


def calculate_RSI(coin_pair, period, unit):
    """
    Calculates the Relative Strength Index for a coin_pair
    If the returned value is above 70, it's overbought (SELL IT!)
    If the returned value is below 30, it's oversold (BUY IT!)
    """

    closing_prices = get_closing_prices(coin_pair, period * 3, unit)
    count = 0
    change = []
    # Calculating price changes
    for i in closing_prices:
        if count != 0:
            change.append(i - closing_prices[count - 1])
        count += 1
        if count == 15:
            break
    # Calculating gains and losses
    advances = []
    declines = []
    for i in change:
        if i > 0:
            advances.append(i)
        if i < 0:
            declines.append(abs(i))
    average_gain = (sum(advances) / 14)
    average_loss = (sum(declines) / 14)
    new_avg_gain = average_gain
    new_avg_loss = average_loss
    for _ in closing_prices:
        if 14 < count < len(closing_prices):
            close = closing_prices[count]
            new_change = close - closing_prices[count - 1]
            add_loss = 0
            add_gain = 0
            if new_change > 0:
                add_gain = new_change
            if new_change < 0:
                add_loss = abs(new_change)
            new_avg_gain = (new_avg_gain * 13 + add_gain) / 14
            new_avg_loss = (new_avg_loss * 13 + add_loss) / 14
            count += 1

    if new_avg_loss == 0:
        return None

    rs = new_avg_gain / new_avg_loss
    new_rs = 100 - 100 / (1 + rs)
    return new_rs


def buy_strategy(coin_pair):
    if coin_pair in Database.trades['trackedCoinPairs']:
        return
    print_str = 'Buy on {: <10} \t-> \t\tRSI: {} \t\t24 Hour Volume: {: >6} {} \t\tURL: {}'
    rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='fiveMin')
    day_volume = get_current_24hr_volume(coin_pair)
    current_buy_price = get_current_price(coin_pair, 'ask')
    if rsi is not None and rsi <= 30 and day_volume >= 10:
        Messenger.send_RSI_email(rsi, coin_pair, day_volume, 'JP')
        # Messenger.play_beep()
        main_market, coin = coin_pair.split('-')
        print(print_str.format(coin_pair, round(rsi), round(day_volume), main_market,
                               Messenger.generate_bittrex_URL(coin_pair)))
        Database.store_buy(coin_pair, current_buy_price, rsi, day_volume)


def sell_strategy(coin_pair):
    if coin_pair not in Database.trades['trackedCoinPairs']:
        return
    print_str = 'Sell on {: <10} \t-> \t\tRSI: {} \t\tProfit Margin: {} % \t\tURL: {}'
    rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='fiveMin')
    day_volume = get_current_24hr_volume(coin_pair)
    current_sell_price = get_current_price(coin_pair, 'bid')
    profit_margin = Database.get_profit_margin(coin_pair, current_sell_price)
    if rsi is not None and rsi >= 45 and profit_margin >= 1:
        print(print_str.format(coin_pair, round(rsi), round(profit_margin, 2),
                               Messenger.generate_bittrex_URL(coin_pair)))
        Database.store_sell(coin_pair, current_sell_price, rsi, day_volume)


if __name__ == '__main__':
    def analyse_buys():
        if len(Database.trades['trackedCoinPairs']) < 1:
            for coin_pair in btc_coin_pairs:
                buy_strategy(coin_pair)


    def analyse_sells():
        for coin_pair in Database.trades['trackedCoinPairs']:
            sell_strategy(coin_pair)


    btc_coin_pairs = get_markets('BTC')
    print('Tracking {} Bittrex markets'.format(len(btc_coin_pairs)))
    while True:
        try:
            analyse_buys()
            analyse_sells()
        except Exception:
            logger.exception(Exception)
