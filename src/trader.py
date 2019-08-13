import pydash as py_
import time

from bittrex import Bittrex
from messenger import Messenger
from database import Database
from logger import logger

bittrex_trade_commission = 0.0025


class Trader(object):
    """
    Used for handling all trade functionality
    """

    def __init__(self, secrets, settings):
        self.trade_params = settings["tradeParameters"]
        self.pause_params = settings["pauseParameters"]

        self.Bittrex = Bittrex(secrets)
        self.Messenger = Messenger(settings)
        self.Database = Database()

    def initialise(self):
        """
        Fetch the initial coin pairs to track and to print the header line
        """
        try:
            if len(self.Database.app_data["coinPairs"]) < 1:
                self.Database.store_coin_pairs(self.get_markets("BTC"))
            self.Messenger.print_header(len(self.Database.app_data["coinPairs"]))
        except ConnectionError as exception:
            self.Messenger.print_error("connection", [], True)
            logger.exception(exception)
            exit()

    def analyse_pauses(self):
        """
        Checks all the paused buy pairs and the balance notification timer and reactivate the necessary ones
        """
        if self.Database.check_resume(self.pause_params["buy"]["pauseTime"], "buy"):
            self.Database.store_coin_pairs(self.get_markets("BTC"))
            self.Messenger.print_resume_pause(len(self.Database.app_data["coinPairs"]))

    def analyse_buys(self):
        """
        Analyse all the un-paused coin pairs for buy signals and apply buys
        """
        for coin_pair in self.Database.app_data["coinPairs"]:
            self.buy_strategy(coin_pair)

    def buy_strategy(self, coin_pair):
        """
        Applies the buy checks on the coin pair and handles the results appropriately

        :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
        :type coin_pair: str
        """
        rsi = self.calculate_rsi(coin_pair=coin_pair, period=14, unit=self.trade_params["tickerInterval"])
        day_volume = self.get_current_24hr_volume(coin_pair)
        current_buy_price = self.get_current_price(coin_pair, "ask")

        pause_rsi = self.pause_params["buy"]["rsiThreshold"]
        pause_day_volume = self.pause_params["buy"]["24HourVolumeThreshold"]
        pause_time = self.pause_params["buy"]["pauseTime"]

        if rsi is None:
            return

        break_even_sale_price = current_buy_price / (1 - 2 * bittrex_trade_commission)
        desired_profit_percentage = 0
        desired_profit_price = break_even_sale_price
        if "sell" in self.trade_params and "desiredProfitPercentage" in self.trade_params["sell"]:
            desired_profit_percentage = self.trade_params["sell"]["desiredProfitPercentage"]
            desired_profit_price = break_even_sale_price * (1 + desired_profit_percentage / 100)
        if self.check_buy_parameters(rsi, day_volume, current_buy_price):
            buy_stats = {"rsi": rsi, "24HrVolume": day_volume}
            self.buy(
                coin_pair,
                current_buy_price,
                buy_stats,
                break_even_sale_price,
                desired_profit_percentage,
                desired_profit_price
            )
        elif "buy" in self.pause_params and (rsi >= pause_rsi > 0 or day_volume <= pause_day_volume):
            self.Messenger.print_pause(coin_pair, [rsi, day_volume], pause_time)
            self.Database.pause_buy(coin_pair)
        else:
            self.Messenger.print_no_buy(
                coin_pair,
                rsi,
                day_volume,
                current_buy_price,
                break_even_sale_price,
                desired_profit_percentage,
                desired_profit_price
            )

    def check_buy_parameters(self, rsi, day_volume, current_buy_price):
        """
        Used to check if the buy conditions have been met

        :param rsi: The coin pair's current RSI
        :type rsi: float
        :param day_volume: The coin pair's current 24 hour volume
        :type day_volume: float
        :param current_buy_price: The coin pair's current price
        :type current_buy_price: float

        :return: Boolean indicating if the buy conditions have been met
        :rtype: bool
        """
        rsi_check = rsi <= self.trade_params["buy"]["rsiThreshold"]
        day_volume_check = day_volume >= self.trade_params["buy"]["24HourVolumeThreshold"]
        current_buy_price_check = current_buy_price >= self.trade_params["buy"]["minimumUnitPrice"]

        return rsi_check and day_volume_check and current_buy_price_check

    def buy(self, coin_pair, price, stats, break_even_sale_price, desired_profit_percentage, desired_profit_price):
        """
        Used to place a buy order to Bittrex. Wait until the order is completed.
        If the order is not filled within trade_time_limit minutes cancel it.

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param price: The price at which to buy
        :type price: float
        :param stats: The buy stats object
        :type stats: dict
        :param break_even_sale_price: The minimum sale price (including commission) to break even (ex: 0.005 BTC/LTC)
        :type break_even_sale_price: float
        :param desired_profit_percentage: The desired profit percentage
        :type desired_profit_percentage: float
        :param desired_profit_price: The sale price required to make the desired profit
        :type desired_profit_price: float
        """
        self.Messenger.print_buy(
            coin_pair,
            price,
            stats["rsi"],
            stats["24HrVolume"],
            break_even_sale_price,
            desired_profit_percentage,
            desired_profit_price
        )
        self.Messenger.play_sw_imperial_march()

    def get_markets(self, main_market_filter=None):
        """
        Gets all the Bittrex markets and filters them based on the main market filter

        :param main_market_filter: Main market to filter on (ex: BTC, ETH, USDT)
        :type main_market_filter: str

        :return: All Bittrex markets (with filter applied, if any)
        :rtype: list
        """
        markets = self.Bittrex.get_markets()
        if not markets["success"]:
            error_str = self.Messenger.print_error("market", [], True)
            logger.error(error_str)
            exit()

        markets = markets["result"]
        if main_market_filter is not None:
            market_check = main_market_filter + "-"
            markets = py_.filter_(markets, lambda market: market_check in market["MarketName"])
        markets = py_.map_(markets, lambda market: market["MarketName"])
        return markets

    def get_current_price(self, coin_pair, price_type):
        """
        Gets current market price for a coin pair

        :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
        :type coin_pair: str
        :param price_type: The type of price to get (one of: 'ask', 'bid')
        :type price_type: str

        :return: Coin pair's current market price
        :rtype: float
        """
        coin_summary = self.Bittrex.get_market_summary(coin_pair)
        if not coin_summary["success"]:
            error_str = self.Messenger.print_error("coinMarket", [coin_pair])
            logger.error(error_str)
            return None
        if price_type == "ask":
            return coin_summary["result"][0]["Ask"]
        if price_type == "bid":
            return coin_summary["result"][0]["Bid"]
        return coin_summary["result"][0]["Last"]

    def get_current_24hr_volume(self, coin_pair):
        """
        Gets current 24 hour market volume for a coin pair

        :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
        :type coin_pair: str

        :return: Coin pair's current 24 hour market volume
        :rtype: float
        """
        coin_summary = self.Bittrex.get_market_summary(coin_pair)
        if not coin_summary["success"]:
            error_str = self.Messenger.print_error("coinMarket", [coin_pair])
            logger.error(error_str)
            return None
        return coin_summary["result"][0]["BaseVolume"]

    def get_closing_prices(self, coin_pair, period, unit):
        """
        Returns closing prices within a specified time frame for a coin pair

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param period: Number of periods to query
        :type period: int
        :param unit: Ticker interval (one of: 'oneMin', 'fiveMin', 'thirtyMin', 'hour', 'week', 'day', and 'month')
        :type unit: str

        :return: Array of closing prices
        :rtype: list
        """
        historical_data = self.Bittrex.get_historical_data(coin_pair, period, unit)
        closing_prices = []
        for i in historical_data:
            closing_prices.append(i["C"])
        return closing_prices

    def get_order(self, order_uuid, trade_time_limit):
        """
        Used to get an order from Bittrex by it's UUID.
        First wait until the order is completed before retrieving it.
        If the order is not completed within trade_time_limit seconds, cancel it.

        :param order_uuid: The order's UUID
        :type order_uuid: str
        :param trade_time_limit: The time in seconds to wait fot the order before cancelling it
        :type trade_time_limit: float

        :return: Order object
        :rtype: dict
        """
        start_time = time.time()
        order_data = self.Bittrex.get_order(order_uuid)
        while time.time() - start_time <= trade_time_limit and order_data["result"]["IsOpen"]:
            time.sleep(10)
            order_data = self.Bittrex.get_order(order_uuid)

        if order_data["result"]["IsOpen"]:
            error_str = self.Messenger.print_error(
                "order", [order_uuid, trade_time_limit, order_data["result"]["Exchange"]]
            )
            logger.error(error_str)
            if order_data["result"]["Type"] == "LIMIT_BUY":
                self.Bittrex.cancel(order_uuid)

        return order_data

    def calculate_rsi(self, coin_pair, period, unit):
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
        :rtype: float
        """
        closing_prices = self.get_closing_prices(coin_pair, period * 3, unit)
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
