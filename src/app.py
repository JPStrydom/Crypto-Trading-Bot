import json
import pydash as py_

from src.bittrex import Bittrex
from src.messenger import Messenger
from src.database import Database
from src.logger import logger


def create_databases(num_of_strategies):
    database_array = []
    for strategy_index in range(num_of_strategies):
        database_array.append(Database(strategy_index))
    return database_array


with open('database/secrets.json') as secrets_file:
    secrets = json.load(secrets_file)
    secrets_file.close()
    Bittrex = Bittrex(secrets)
    Messenger = Messenger(secrets)
    number_of_strategies = 4
    Database_List = create_databases(number_of_strategies)


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


def get_current_price(coin_pair):
    """
    Gets current market price for a coin pair

    :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
    :type coin_pair: str

    :return: Coin pair's current market price
    :rtype : float
    """

    coin_summary = Bittrex.get_market_summary(coin_pair)
    if not coin_summary['success']:
        logger.error('Failed to fetch Bittrex market summary for the {} market'.format(coin_pair))
        return None
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
    return coin_summary['result'][0]['Volume']


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


def buy_strategy(coin_pair, strategy_index):
    if coin_pair in Database_List[strategy_index].simulated_trades['trackedCoinPairs']:
        return
    print_str = 'Strategy {} Buy on {} \t-> \tRSI: {} \tPrice: {:.8f} {}/{} \tURL: {}'
    if strategy_index == 0:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='thirtyMin')
        current_price = get_current_price(coin_pair)
        if rsi is not None and rsi <= 20:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_buy(coin_pair, current_price, rsi)
    if strategy_index == 1:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='thirtyMin')
        current_price = get_current_price(coin_pair)
        if rsi is not None and rsi <= 20:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_buy(coin_pair, current_price, rsi)
    if strategy_index == 2:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='fiveMin')
        current_price = get_current_price(coin_pair)
        if rsi is not None and rsi <= 20:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_buy(coin_pair, current_price, rsi)
    if strategy_index == 3:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='fiveMin')
        current_price = get_current_price(coin_pair)
        if rsi is not None and rsi <= 20:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_buy(coin_pair, current_price, rsi)


def sell_strategy(coin_pair, strategy_index):
    if coin_pair not in Database_List[strategy_index].simulated_trades['trackedCoinPairs']:
        return
    print_str = 'Strategy {} Sell on {} \t-> \tRSI: {} \tPrice: {:.8f} {}/{} \tURL: {}'
    if strategy_index == 0:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='thirtyMin')
        current_price = get_current_price(coin_pair)
        if rsi is not None and rsi >= 35:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_sell(coin_pair, current_price, rsi)
    if strategy_index == 1:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='fiveMin')
        current_price = get_current_price(coin_pair)
        if rsi is not None and rsi >= 35:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_sell(coin_pair, current_price, rsi)
    if strategy_index == 2:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='thirtyMin')
        current_price = get_current_price(coin_pair)
        profit_margin = Database_List[strategy_index].get_simulated_profit_margin(coin_pair, current_price)
        if profit_margin >= 2.5:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_sell(coin_pair, current_price, rsi)
    if strategy_index == 3:
        rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='fiveMin')
        current_price = get_current_price(coin_pair)
        profit_margin = Database_List[strategy_index].get_simulated_profit_margin(coin_pair, current_price)
        if profit_margin >= 2.5:
            main_market, coin = coin_pair.split('-')
            print(print_str.format(strategy_index, coin_pair, round(rsi, 2), current_price, coin, main_market,
                                   Messenger.generate_bittrex_URL(coin_pair)))
            Database_List[strategy_index].simulate_sell(coin_pair, current_price, rsi)


if __name__ == '__main__':
    def analyse_buys():
        for strategy_index in range(number_of_strategies):
            if len(Database_List[strategy_index].simulated_trades['trackedCoinPairs']) < 1:
                for coin_pair in btc_coin_pairs:
                    buy_strategy(coin_pair, strategy_index)


    def analyse_sells():
        for strategy_index in range(number_of_strategies):
            for coin_pair in Database_List[strategy_index].simulated_trades['trackedCoinPairs']:
                sell_strategy(coin_pair, strategy_index)


    btc_coin_pairs = get_markets('BTC')
    print('Tracking {} Bittrex markets'.format(len(btc_coin_pairs)))
    while True:
        try:
            analyse_buys()
            analyse_sells()
        except Exception:
            logger.exception(Exception)
