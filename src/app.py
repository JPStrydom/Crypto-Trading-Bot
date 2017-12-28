import pydash as py_
import time
import json
from requests.exceptions import SSLError

from src.bittrex import Bittrex
from src.messenger import Messenger
from src.database import Database
from src.logger import logger
from src.directory_utilities import get_json_from_file

secrets_file_directory = "../database/secrets.json"
secrets_template = {
    "bittrex": {
        "bittrexKey": "BITTREX_API_KEY",
        "bittrexSecret": "BITTREX_SECRET"
    },
    "gmail": {
        "addressList": [
            "EXAMPLE_RECIPIENT_1@GMAIL.COM",
            "EXAMPLE_RECIPIENT_2@GMAIL.COM",
            "ETC..."
        ],
        "username": "EXAMPLE_EMAIL@GMAIL.COM",
        "password": "GMAIL_PASSWORD"
    },
    "tradeParameters": {
        "tickerInterval": "TICKER_INTERVAL",
        "buy": {
            "btcAmount": 0,
            "rsiThreshold": 0,
            "24HourVolumeThreshold": 0,
            "minimumUnitPrice": 0,
            "maxOpenTrades": 0
        },
        "sell": {
            "rsiThreshold": 0,
            "profitMarginThreshold": 0
        }
    },
    "pauseParameters": {
        "buy": {
            "rsiThreshold": 0,
            "pauseTime": 0
        },
        "sell": {
            "profitMarginThreshold": 0,
            "pauseTime": 0
        }
    }
}
secrets = get_json_from_file(secrets_file_directory, secrets_template)
if secrets == secrets_template:
    print("Please completed the `secrets.json` file in your `database` directory")
    exit()
trade_params = secrets["tradeParameters"]
pause_params = secrets["pauseParameters"]
buy_trade_params = trade_params["buy"]
sell_trade_params = trade_params["sell"]
buy_pause_params = pause_params["buy"]
sell_pause_params = pause_params["sell"]

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
    if not markets["success"]:
        logger.error("Failed to fetch Bittrex markets")
        exit()

    markets = markets["result"]
    if main_market_filter is not None:
        market_check = main_market_filter + "-"
        markets = py_.filter_(markets, lambda market: market_check in market["MarketName"])
    markets = py_.map_(markets, lambda market: market["MarketName"])
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
    if not coin_summary["success"]:
        logger.error("Failed to fetch Bittrex market summary for the {} market".format(coin_pair))
        return None
    if price_type == "ask":
        return coin_summary["result"][0]["Ask"]
    if price_type == "bid":
        return coin_summary["result"][0]["Bid"]
    return coin_summary["result"][0]["Last"]


def get_current_24hr_volume(coin_pair):
    """
    Gets current 24 hour market volume for a coin pair

    :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
    :type coin_pair: str

    :return: Coin pair's current 24 hour market volume
    :rtype : float
    """
    coin_summary = Bittrex.get_market_summary(coin_pair)
    if not coin_summary["success"]:
        logger.error("Failed to fetch Bittrex market summary for the {} market".format(coin_pair))
        return None
    return coin_summary["result"][0]["BaseVolume"]


def get_closing_prices(coin_pair, period, unit):
    """
    Returns closing prices within a specified time frame for a coin pair

    :param coin_pair: String literal for the market (ex: BTC-LTC)
    :type coin_pair: str
    :param period: Number of periods to query
    :type period: int
    :param unit: Ticker interval (one of: 'oneMin', 'fiveMin', 'thirtyMin', 'hour', 'week', 'day', and 'month')
    :type unit: str

    :return: Array of closing prices
    :rtype : list
    """
    historical_data = Bittrex.get_historical_data(coin_pair, period, unit)
    closing_prices = []
    for i in historical_data:
        closing_prices.append(i["C"])
    return closing_prices


def calculate_RSI(coin_pair, period, unit):
    """
    Calculates the Relative Strength Index for a coin_pair
    If the returned value is above 75, it's overbought (SELL IT!)
    If the returned value is below 25, it's oversold (BUY IT!)

    :param coin_pair: String literal for the market (ex: BTC-LTC)
    :type coin_pair: str
    :param period: Number of periods to query
    :type period: int
    :param unit: Ticker interval (one of: 'oneMin', 'fiveMin', 'thirtyMin', 'hour', 'week', 'day', and 'month')
    :type unit: str

    :return: RSI
    :rtype : float
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


def buy(coin_pair, btc_quantity, price, stats, trade_time_limit=2):
    """
    Used to place a buy order to Bittrex. Wait until the order is completed.
    If the order is not filled within trade_time_limit minutes cancel it.

    :param coin_pair: String literal for the market (ex: BTC-LTC)
    :type coin_pair: str
    :param btc_quantity: The amount of BTC to buy with
    :type btc_quantity: float
    :param price: The price at which to buy
    :type price: float
    :param stats: The buy stats object
    :type stats: dict
    :param trade_time_limit: The time in minutes to wait fot the order before cancelling it
    :type trade_time_limit: float
    """
    buy_data = Bittrex.buy_limit(coin_pair, btc_quantity / price, price)
    if not buy_data["success"]:
        return logger.error("Failed to buy on {} market.".format(coin_pair))
    Database.store_initial_buy(coin_pair, buy_data["result"]["uuid"])

    buy_order_data = get_order(buy_data["result"]["uuid"], trade_time_limit * 60)
    Database.store_buy(buy_order_data["result"], stats)

    Messenger.send_buy_email(buy_order_data["result"], stats)
    Messenger.print_buy(coin_pair, price, stats["rsi"], stats["24HrVolume"])
    Messenger.play_sw_imperial_march()


def sell(coin_pair, price, stats, trade_time_limit=2):
    """
    Used to place a sell order to Bittrex. Wait until the order is completed.
    If the order is not filled within trade_time_limit minutes cancel it.

    :param coin_pair: String literal for the market (ex: BTC-LTC)
    :type coin_pair: str
    :param price: The price at which to buy
    :type price: float
    :param stats: The buy stats object
    :type stats: dict
    :param trade_time_limit: The time in minutes to wait fot the order before cancelling it
    :type trade_time_limit: float
    """
    trade = Database.get_open_trade(coin_pair)
    sell_data = Bittrex.sell_limit(coin_pair, trade["quantity"], price)
    if not sell_data["success"]:
        return logger.error("Failed to sell on {} market.".format(coin_pair))

    sell_order_data = get_order(sell_data["result"]["uuid"], trade_time_limit * 60)
    # TODO: Handle partial/incomplete sales
    Database.store_sell(sell_order_data["result"], stats)

    Messenger.send_sell_email(sell_order_data["result"], stats)
    Messenger.print_sell(coin_pair, price, stats["rsi"], stats["profitMargin"])
    Messenger.play_sw_theme()


def get_order(order_uuid, trade_time_limit):
    """
    Used to get an order from Bittrex by it's UUID.
    First wait until the order is completed before retrieving it.
    If the order is not completed within trade_time_limit seconds, cancel it.

    :param order_uuid: The order's UUID
    :type order_uuid: str
    :param trade_time_limit: The time in seconds to wait fot the order before cancelling it
    :type trade_time_limit: float

    :return: Order object
    :rtype : dict
    """
    start_time = time.time()
    order_data = Bittrex.get_order(order_uuid)
    while time.time() - start_time <= trade_time_limit and order_data["result"]["IsOpen"]:
        time.sleep(10)
        order_data = Bittrex.get_order(order_uuid)

    if order_data["result"]["IsOpen"]:
        error_str = Messenger.print_order_error(order_uuid, trade_time_limit, order_data["result"]["Exchange"])
        logger.error(error_str)
        # TODO: Handle partial/incomplete sales. Don't cancel sells. Perhaps just up the price?
        Bittrex.cancel(order_uuid)
        return order_data

    return order_data


def check_buy_parameters(rsi, day_volume, current_buy_price):
    """
    Used to check if the buy conditions have been met

    :param rsi: The coin pair's current RSI
    :type rsi: float
    :param day_volume: The coin pair's current 24 hour volume
    :type day_volume: float
    :param current_buy_price: The coin pair's current price
    :type current_buy_price: float

    :return: Boolean indicating if the buy conditions have been met
    :rtype : bool
    """
    return (rsi is not None and rsi <= buy_trade_params["rsiThreshold"] and
            day_volume >= buy_trade_params["24HourVolumeThreshold"] and
            current_buy_price > buy_trade_params["minimumUnitPrice"])


def check_sell_parameters(rsi, profit_margin):
    """
    Used to check if the sell conditions have been met

    :param rsi: The coin pair's current RSI
    :type rsi: float
    :param profit_margin: The coin pair's current profit margin
    :type profit_margin: float

    :return: Boolean indicating if the sell conditions have been met
    :rtype : bool
    """
    return ((rsi is not None and rsi >= sell_trade_params["rsiThreshold"] and
             profit_margin > sell_trade_params["minProfitMarginThreshold"]) or
            profit_margin > sell_trade_params["profitMarginThreshold"])


def buy_strategy(coin_pair):
    """
    Applies the buy checks on the coin pair and handles the results appropriately

    :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
    :type coin_pair: str
    """
    if (len(Database.trades["trackedCoinPairs"]) >= buy_trade_params["maxOpenTrades"] or
            coin_pair in Database.trades["trackedCoinPairs"]):
        return
    rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit=trade_params["tickerInterval"])
    day_volume = get_current_24hr_volume(coin_pair)
    current_buy_price = get_current_price(coin_pair, "ask")

    if check_buy_parameters(rsi, day_volume, current_buy_price):
        buy_stats = {
            "rsi": rsi,
            "24HrVolume": day_volume
        }
        buy(coin_pair, buy_trade_params["btcAmount"], current_buy_price, buy_stats)
    elif rsi is not None and rsi <= buy_pause_params["rsiThreshold"]:
        Messenger.print_no_buy(coin_pair, rsi, day_volume, current_buy_price)
    else:
        Messenger.print_pause(coin_pair, rsi, buy_pause_params["pauseTime"], "buy")
        Database.pause_buy(coin_pair)


def sell_strategy(coin_pair):
    """
    Applies the sell checks on the coin pair and handles the results appropriately

    :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
    :type coin_pair: str
    """
    if (coin_pair in Database.app_data["pausedTrackedCoinPairs"] or
            coin_pair not in Database.trades["trackedCoinPairs"]):
        return
    rsi = calculate_RSI(coin_pair=coin_pair, period=14, unit=trade_params["tickerInterval"])
    current_sell_price = get_current_price(coin_pair, "bid")
    profit_margin = Database.get_profit_margin(coin_pair, current_sell_price)

    if check_sell_parameters(rsi, profit_margin):
        sell_stats = {
            "rsi": rsi,
            "profitMargin": profit_margin
        }
        sell(coin_pair, current_sell_price, sell_stats)
    elif rsi is not None and profit_margin >= sell_pause_params["profitMarginThreshold"]:
        Messenger.print_no_sell(coin_pair, rsi, profit_margin, current_sell_price)
    else:
        Messenger.print_pause(coin_pair, profit_margin, sell_pause_params["pauseTime"], "sell")
        Database.pause_sell(coin_pair)


if __name__ == "__main__":
    def analyse_pauses():
        if Database.check_resume(buy_pause_params["pauseTime"], "buy"):
            Database.store_coin_pairs(get_markets("BTC"))
            Messenger.print_resume_pause(len(Database.app_data["coinPairs"]), "buy")
        if Database.check_resume(sell_pause_params["pauseTime"], "sell"):
            Messenger.print_resume_pause(Database.app_data["pausedTrackedCoinPairs"], "sell")
            Database.resume_sells()


    def analyse_buys():
        trade_len = len(Database.trades["trackedCoinPairs"])
        pause_trade_len = len(Database.app_data["pausedTrackedCoinPairs"])
        if (trade_len < 1 or pause_trade_len == trade_len) and trade_len < buy_trade_params["maxOpenTrades"]:
            for coin_pair in Database.app_data["coinPairs"]:
                buy_strategy(coin_pair)


    def analyse_sells():
        for coin_pair in Database.trades["trackedCoinPairs"]:
            if coin_pair not in Database.app_data["pausedTrackedCoinPairs"]:
                sell_strategy(coin_pair)


    try:
        if len(Database.app_data["coinPairs"]) < 1:
            Database.store_coin_pairs(get_markets("BTC"))
        Messenger.print_header(len(Database.app_data["coinPairs"]))
    except ConnectionError as exception:
        Messenger.print_exception_error("connection")
        logger.exception(exception)
        exit()

    while True:
        try:
            analyse_pauses()
            analyse_buys()
            analyse_sells()
            time.sleep(10)

        except ConnectionError as exception:
            Messenger.print_exception_error("connection")
            logger.exception(exception)
            time.sleep(10)
        except SSLError as exception:
            Messenger.print_exception_error("SSL")
            logger.exception(exception)
            time.sleep(10)
        except json.decoder.JSONDecodeError as exception:
            Messenger.print_exception_error("JSONDecode")
            logger.exception(exception)
            time.sleep(10)
        except TypeError as exception:
            Messenger.print_exception_error("typeError")
            logger.exception(exception)
            time.sleep(10)
        except KeyError as exception:
            Messenger.print_exception_error("keyError")
            logger.exception(exception)
            exit()
        except ValueError as exception:
            Messenger.print_exception_error("valueError")
            logger.exception(exception)
            exit()
        except Exception:
            Messenger.print_exception_error("unknown")
            logger.exception(Exception)
            exit()
