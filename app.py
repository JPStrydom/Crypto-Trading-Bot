from bittrex import Bittrex
from logger import get_logger
import json
import time
import smtplib
import pydash as py_

logger = get_logger()

# Creating an instance of the Bittrex class with our secrets.json file
with open('secrets.json') as secrets_file:
    secrets = json.load(secrets_file)
    secrets_file.close()
    my_bittrex = Bittrex(secrets['bittrex']['bittrex_key'], secrets['bittrex']['bittrex_secret'])


def get_markets(main_market_filter=None):
    """
    Gets all the Bittrex markets and filters them based on the main market filter

    :param main_market_filter: Main market to filter on (ex: BTC, ETH, USDT)
    :type main_market_filter: str

    :return: All Bittrex markets (with filter applied, if any)
    :rtype : list
    """

    markets = my_bittrex.get_markets()
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

    coin_summary = my_bittrex.get_market_summary(coin_pair)
    if not coin_summary['success']:
        logger.error('Failed to fetch Bittrex market summary for the {} market'.format(coin_pair))
        return None
    return coin_summary['result'][0]['Last']


def get_closing_prices(coin_pair, period, unit):
    """
    Returns closing prices within a specified time frame for a coin pair

    :type coin_pair: str
    :type period: int
    :type unit: str

    :return: Array of closing prices
    """

    historical_data = my_bittrex.get_historical_data(coin_pair, period, unit)
    closing_prices = []
    for i in historical_data:
        closing_prices.append(i['C'])
    return closing_prices


def calculate_SMA(coin_pair, period, unit):
    """
    Returns the Simple Moving Average for a coin pair
    """

    total_closing = sum(get_closing_prices(coin_pair, period, unit))
    return total_closing / period


def calculate_EMA(coin_pair, period, unit):
    """
    Returns the Exponential Moving Average for a coin pair
    """

    closing_prices = get_closing_prices(coin_pair, period, unit)
    previous_ema = calculate_SMA(coin_pair, period, unit)
    current_ema = (closing_prices[-1] * (2 / (1 + period))) + (previous_ema * (1 - (2 / (1 + period))))
    return current_ema


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


def calculate_base_line(coin_pair, unit):
    """
    Calculates (26 period high + 26 period low) / 2
    Also known as the "Kijun-sen" line
    """

    closing_prices = get_closing_prices(coin_pair, 26, unit)
    period_high = max(closing_prices)
    period_low = min(closing_prices)
    return (period_high + period_low) / 2


def calculate_conversion_line(coin_pair, unit):
    """
    Calculates (9 period high + 9 period low) / 2
    Also known as the "Tenkan-sen" line
    """

    closing_prices = get_closing_prices(coin_pair, 9, unit)
    period_high = max(closing_prices)
    period_low = min(closing_prices)
    return (period_high + period_low) / 2


def calculate_leading_span_A(coin_pair, unit):
    """
    Calculates (Conversion Line + Base Line) / 2
    Also known as the "Senkou Span A" line
    """

    base_line = calculate_base_line(coin_pair, unit)
    conversion_line = calculate_conversion_line(coin_pair, unit)
    return (base_line + conversion_line) / 2


def calculate_leading_span_B(coin_pair, unit):
    """
    Calculates (52 period high + 52 period low) / 2
    Also known as the "Senkou Span B" line
    """

    closing_prices = get_closing_prices(coin_pair, 52, unit)
    period_high = max(closing_prices)
    period_low = min(closing_prices)
    return (period_high + period_low) / 2


def find_breakout(coin_pair, period, unit):
    """
    Finds breakout based on how close the High was to Closing and Low to Opening
    """

    hit = 0
    historical_data = my_bittrex.get_historical_data(coin_pair, period, unit)
    for i in historical_data:
        if (i['C'] == i['H']) and (i['O'] == i['L']):
            hit += 1

    if (hit / period) >= .75:
        return 'Breaking out!'
    else:
        return '#Bagholding'


def generate_URL(btc_coin_pair):
    """
    Generates the URL string for the coin pairs Bittrex page
    """

    return 'https://bittrex.com/Market/Index?MarketName={}'.format(btc_coin_pair)


def send_email(subject, message):
    """
    Used to send an email from the account specified in the secrets.json file to the entire
    address list specified in the secrets.json file

    :param subject: Email subject
    :type subject: str
    :param message: Email content
    :type message: str

    :return: Errors received from the smtp server (if any)
    :rtype : dict
    """

    from_address = secrets['gmail']['username']
    to_address_list = secrets['gmail']['address_list']
    login = secrets['gmail']['username']
    password = secrets['gmail']['password']
    smtp_server = 'smtp.gmail.com:587'

    header = 'From: %s\n' % from_address
    header += 'To: %s\n' % ','.join(to_address_list)
    header += 'Subject: %s\n\n' % subject
    message = header + message

    server = smtplib.SMTP(smtp_server)
    server.starttls()
    server.login(login, password)
    errors = server.sendmail(from_address, to_address_list, message)
    server.quit()
    return errors


def send_RSI_email(rsi, coin_pair, current_price, recipient_name):
    """
    Used to send a low RSI specific email from the account specified in the secrets.json file to the entire
    address list specified in the secrets.json file

    :param rsi: Low RSI
    :type rsi: float
    :param coin_pair: Coin pair the low RSI occurred on (ex: BTC-ETH)
    :type coin_pair: str
    :param current_price: Coin pair's current price
    :type current_price: float
    :param recipient_name: Name of the email's recipient (ex: John)
    :type recipient_name: str

    :return: Errors received from the smtp server (if any)
    :rtype : dict
    """

    main_market, coin = coin_pair.split('-')

    subject = 'Crypto Bot: Low RSI on {} Market'.format(coin_pair)
    message = "Howdy {},\n\nI've detected a low RSI of {} on the {} market. The current market price is {:.8f} {} per {}" \
              "\n\nHere's a Bittrex URL: {}\n\nRegards,\nCrypto Bot".format(recipient_name, round(rsi, 2), coin_pair,
                                                                            current_price, main_market, coin,
                                                                            generate_URL(coin_pair))
    send_email(subject, message)


if __name__ == '__main__':
    def get_signal():
        for coin_pair in btc_coin_pairs:
            rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit='thirtyMin')
            if rsi is not None and rsi <= 20:
                current_price = get_current_price(coin_pair)
                main_market, coin = coin_pair.split('-')
                print('{}: \tRSI: {} \tPrice: {:.8f} {}/{} \tURL: {}'.format(coin_pair, round(rsi, 2), current_price,
                                                                         main_market, coin,
                                                                         generate_URL(coin_pair)))
                if rsi <= 15:
                    send_RSI_email(rsi, coin_pair, current_price, 'JP')
        time.sleep(300)


    btc_coin_pairs = get_markets('BTC')
    while True:
        get_signal()
