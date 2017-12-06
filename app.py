from bittrex import Bittrex
import json
import time
import smtplib

# Creating an instance of the Bittrex class with our secrets.json file
with open('secrets.json') as secrets_file:
    secrets = json.load(secrets_file)
    secrets_file.close()
    my_bittrex = Bittrex(secrets['bittrex']['bittrex_key'], secrets['bittrex']['bittrex_secret'])

btc_coin_pairs = [
    'BTC-LTC',
    'BTC-DOGE',
    'BTC-VTC',
    'BTC-PPC',
    'BTC-FTC',
    'BTC-RDD',
    'BTC-NXT',
    'BTC-DASH',
    'BTC-POT',
    'BTC-BLK',
    'BTC-EMC2',
    'BTC-XMY',
    'BTC-AUR',
    'BTC-EFL',
    'BTC-GLD',
    'BTC-SLR',
    'BTC-PTC',
    'BTC-GRS',
    'BTC-NLG',
    'BTC-RBY',
    'BTC-XWC',
    'BTC-MONA',
    'BTC-THC',
    'BTC-ENRG',
    'BTC-ERC',
    'BTC-VRC',
    'BTC-CURE',
    'BTC-XMR',
    'BTC-CLOAK',
    'BTC-START',
    'BTC-KORE',
    'BTC-XDN',
    'BTC-TRUST',
    'BTC-NAV',
    'BTC-XST',
    'BTC-BTCD',
    'BTC-VIA',
    'BTC-PINK',
    'BTC-IOC',
    'BTC-CANN',
    'BTC-SYS',
    'BTC-NEOS',
    'BTC-DGB',
    'BTC-BURST',
    'BTC-EXCL',
    'BTC-SWIFT',
    'BTC-DOPE',
    'BTC-BLOCK',
    'BTC-ABY',
    'BTC-BYC',
    'BTC-XMG',
    'BTC-BLITZ',
    'BTC-BAY',
    'BTC-FAIR',
    'BTC-SPR',
    'BTC-VTR',
    'BTC-XRP',
    'BTC-GAME',
    'BTC-COVAL',
    'BTC-NXS',
    'BTC-XCP',
    'BTC-BITB',
    'BTC-GEO',
    'BTC-FLDC',
    'BTC-GRC',
    'BTC-FLO',
    'BTC-NBT',
    'BTC-MUE',
    'BTC-XEM',
    'BTC-CLAM',
    'BTC-DMD',
    'BTC-GAM',
    'BTC-SPHR',
    'BTC-OK',
    'BTC-SNRG',
    'BTC-PKB',
    'BTC-CPC',
    'BTC-AEON',
    'BTC-ETH',
    'BTC-GCR',
    'BTC-TX',
    'BTC-BCY',
    'BTC-EXP',
    'BTC-INFX',
    'BTC-OMNI',
    'BTC-AMP',
    'BTC-AGRS',
    'BTC-XLM',
    'BTC-CLUB',
    'BTC-VOX',
    'BTC-EMC',
    'BTC-FCT',
    'BTC-MAID',
    'BTC-EGC',
    'BTC-SLS',
    'BTC-RADS',
    'BTC-DCR',
    'BTC-SAFEX',
    'BTC-BSD',
    'BTC-XVG',
    'BTC-PIVX',
    'BTC-XVC',
    'BTC-MEME',
    'BTC-STEEM',
    'BTC-2GIVE',
    'BTC-LSK',
    'BTC-PDC',
    'BTC-BRK',
    'BTC-DGD',
    'BTC-WAVES',
    'BTC-RISE',
    'BTC-LBC',
    'BTC-SBD',
    'BTC-BRX',
    'BTC-ETC',
    'BTC-STRAT',
    'BTC-UNB',
    'BTC-SYNX',
    'BTC-TRIG',
    'BTC-EBST',
    'BTC-VRM',
    'BTC-SEQ',
    'BTC-XAUR',
    'BTC-SNGLS',
    'BTC-REP',
    'BTC-SHIFT',
    'BTC-ARDR',
    'BTC-XZC',
    'BTC-NEO',
    'BTC-ZEC',
    'BTC-ZCL',
    'BTC-IOP',
    'BTC-GOLOS',
    'BTC-UBQ',
    'BTC-KMD',
    'BTC-GBG',
    'BTC-SIB',
    'BTC-ION',
    'BTC-LMC',
    'BTC-QWARK',
    'BTC-CRW',
    'BTC-SWT',
    'BTC-TIME',
    'BTC-MLN',
    'BTC-ARK',
    'BTC-DYN',
    'BTC-TKS',
    'BTC-MUSIC',
    'BTC-DTB',
    'BTC-INCNT',
    'BTC-GBYTE',
    'BTC-GNT',
    'BTC-NXC',
    'BTC-EDG',
    'BTC-LGD',
    'BTC-TRST',
    'BTC-WINGS',
    'BTC-RLC',
    'BTC-GNO',
    'BTC-GUP',
    'BTC-LUN',
    'BTC-APX',
    'BTC-TKN',
    'BTC-HMQ',
    'BTC-ANT',
    'BTC-SC',
    'BTC-BAT',
    'BTC-ZEN',
    'BTC-1ST',
    'BTC-QRL',
    'BTC-CRB',
    'BTC-PTOY',
    'BTC-MYST',
    'BTC-CFI',
    'BTC-BNT',
    'BTC-NMR',
    'BTC-SNT',
    'BTC-DCT',
    'BTC-XEL',
    'BTC-MCO',
    'BTC-ADT',
    'BTC-FUN',
    'BTC-PAY',
    'BTC-MTL',
    'BTC-STORJ',
    'BTC-ADX',
    'BTC-OMG',
    'BTC-CVC',
    'BTC-PART',
    'BTC-QTUM',
    'BTC-BCC',
    'BTC-DNT',
    'BTC-ADA',
    'BTC-MANA',
    'BTC-SALT',
    'BTC-TIX',
    'BTC-RCN',
    'BTC-VIB',
    'BTC-MER',
    'BTC-POWR',
    'BTC-BTG',
    'BTC-ENG'
]


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


def send_RSI_email(rsi, coin_pair, recipient_name):
    subject = 'Crypto Bot: Low RSI on {} Market'.format(coin_pair)
    message = "Howdy {},\n\nI've detected a low RSI of {} on the {} market.\n\nHere's a Bittrex URL: {}\n\nRegards," \
              '\nCrypto Bot'.format(recipient_name, round(rsi, 2), coin_pair, generate_URL(coin_pair))
    send_email(subject, message)


if __name__ == '__main__':
    def get_signal():
        for i in btc_coin_pairs:
            rsi = calculate_RSI(coin_pair=i, period=14, unit='thirtyMin')
            if rsi is not None and rsi <= 20:
                print('{}: \tRSI: {} \tURL: {}'.format(i, round(rsi, 2), generate_URL(i)))
                if rsi <= 15:
                    send_RSI_email(rsi, i, 'JP')
        time.sleep(300)

    while True:
        get_signal()
