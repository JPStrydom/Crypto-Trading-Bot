import pydash as py_
import time

from bittrex import Bittrex
from messenger import Messenger
from database import Database
from logger import logger


class Trader(object):
    """
    Used for handling all trade functionality
    """

    def __init__(self, secrets, settings):
        self.trade_params = settings["tradeParameters"]
        self.pause_params = settings["pauseParameters"]

        self.Bittrex = Bittrex(secrets)
        self.Messenger = Messenger(secrets, settings)
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
        Checks all the paused buy and sell pairs and the balance notification timer and reactivate the necessary ones
        """
        if self.Database.check_resume(self.pause_params["buy"]["pauseTime"], "buy"):
            self.Database.store_coin_pairs(self.get_markets("BTC"))
            self.Messenger.print_resume_pause(len(self.Database.app_data["coinPairs"]), "buy")
        if "sell" in self.pause_params and self.Database.check_resume(self.pause_params["sell"]["pauseTime"], "sell"):
            self.Messenger.print_resume_pause(self.Database.app_data["pausedTrackedCoinPairs"], "sell")
            self.Database.resume_sells()
        if "balance" in self.pause_params and self.Database.check_resume(self.pause_params["balance"]["pauseTime"],
                                                                         "balance"):
            current_balance = self.Messenger.send_balance_slack(self.get_non_zero_balances(),
                                                                self.Database.get_previous_total_balance())
            self.Database.reset_balance_notifier(current_balance)

    def analyse_buys(self):
        """
        Analyse all the un-paused coin pairs for buy signals and apply buys
        """
        trade_len = len(self.Database.trades["trackedCoinPairs"])
        pause_trade_len = len(self.Database.app_data["pausedTrackedCoinPairs"])
        if (trade_len < 1 or pause_trade_len == trade_len) and trade_len < self.trade_params["buy"]["maxOpenTrades"]:
            for coin_pair in self.Database.app_data["coinPairs"]:
                self.buy_strategy(coin_pair)

    def analyse_sells(self):
        """
        Analyse all the un-paused tracked coin pairs for sell signals and apply sells
        """
        for coin_pair in self.Database.trades["trackedCoinPairs"]:
            if coin_pair not in self.Database.app_data["pausedTrackedCoinPairs"]:
                self.sell_strategy(coin_pair)

    def buy_strategy(self, coin_pair):
        """
        Applies the buy checks on the coin pair and handles the results appropriately

        :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
        :type coin_pair: str
        """
        if (len(self.Database.trades["trackedCoinPairs"]) >= self.trade_params["buy"]["maxOpenTrades"] or
                coin_pair in self.Database.trades["trackedCoinPairs"]):
            return
        rsi = self.calculate_RSI(coin_pair=coin_pair, period=14, unit=self.trade_params["tickerInterval"])
        day_volume = self.get_current_24hr_volume(coin_pair)
        current_buy_price = self.get_current_price(coin_pair, "ask")

        if rsi is None:
            return

        if self.check_buy_parameters(rsi, day_volume, current_buy_price):
            buy_stats = {
                "rsi": rsi,
                "24HrVolume": day_volume
            }
            self.buy(coin_pair, self.trade_params["buy"]["btcAmount"], current_buy_price, buy_stats)
        elif "buy" in self.pause_params and rsi >= self.pause_params["buy"]["rsiThreshold"] > 0:
            self.Messenger.print_pause(coin_pair, [rsi, day_volume], self.pause_params["buy"]["pauseTime"], "buy")
            self.Database.pause_buy(coin_pair)
        else:
            self.Messenger.print_no_buy(coin_pair, rsi, day_volume, current_buy_price)

    def sell_strategy(self, coin_pair):
        """
        Applies the sell checks on the coin pair and handles the results appropriately

        :param coin_pair: Coin pair market to check (ex: BTC-ETH, BTC-FCT)
        :type coin_pair: str
        """
        if (coin_pair in self.Database.app_data["pausedTrackedCoinPairs"] or
                coin_pair not in self.Database.trades["trackedCoinPairs"]):
            return
        rsi = self.calculate_RSI(coin_pair=coin_pair, period=14, unit=self.trade_params["tickerInterval"])
        current_sell_price = self.get_current_price(coin_pair, "bid")
        profit_margin = self.Database.get_profit_margin(coin_pair, current_sell_price)

        if rsi is None:
            return

        if self.check_sell_parameters(rsi, profit_margin):
            sell_stats = {
                "rsi": rsi,
                "profitMargin": profit_margin
            }
            self.sell(coin_pair, current_sell_price, sell_stats)
        elif "sell" in self.pause_params and profit_margin <= self.pause_params["sell"]["profitMarginThreshold"] < 0:
            self.Messenger.print_pause(coin_pair, [profit_margin, rsi], self.pause_params["sell"]["pauseTime"], "sell")
            self.Database.pause_sell(coin_pair)
        else:
            self.Messenger.print_no_sell(coin_pair, rsi, profit_margin, current_sell_price)

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

    def check_sell_parameters(self, rsi, profit_margin):
        """
        Used to check if the sell conditions have been met

        :param rsi: The coin pair's current RSI
        :type rsi: float
        :param profit_margin: The coin pair's current profit margin
        :type profit_margin: float

        :return: Boolean indicating if the sell conditions have been met
        :rtype: bool
        """
        rsi_check = rsi >= self.trade_params["sell"]["rsiThreshold"]
        lower_profit_check = profit_margin >= self.trade_params["sell"]["minProfitMarginThreshold"]
        upper_profit_check = profit_margin >= self.trade_params["sell"]["profitMarginThreshold"]
        loss_check = ("lossMarginThreshold" in self.trade_params["sell"] and
                      0 > self.trade_params["sell"]["lossMarginThreshold"] >= profit_margin)

        return (rsi_check and lower_profit_check) or upper_profit_check or (rsi_check and loss_check)

    def buy(self, coin_pair, btc_quantity, price, stats, trade_time_limit=2):
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
        buy_quantity = round(btc_quantity / price, 8)
        buy_data = self.Bittrex.buy_limit(coin_pair, buy_quantity, price)
        if not buy_data["success"]:
            error_str = self.Messenger.print_error("buy", [coin_pair, buy_data["message"]])
            logger.error(error_str)
            return
        self.Database.store_initial_buy(coin_pair, buy_data["result"]["uuid"])

        buy_order_data = self.get_order(buy_data["result"]["uuid"], trade_time_limit * 60)
        self.Database.store_buy(buy_order_data["result"], stats)

        self.Messenger.print_buy(coin_pair, price, stats["rsi"], stats["24HrVolume"])
        self.Messenger.send_buy_slack(coin_pair, stats["rsi"], stats["24HrVolume"])
        self.Messenger.send_buy_gmail(buy_order_data["result"], stats)
        self.Messenger.play_sw_imperial_march()

    def sell(self, coin_pair, price, stats, trade_time_limit=2):
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
        trade = self.Database.get_open_trade(coin_pair)
        sell_data = self.Bittrex.sell_limit(coin_pair, trade["quantity"], price)
        if not sell_data["success"]:
            error_str = self.Messenger.print_error("sell", [coin_pair, sell_data["message"]])
            logger.error(error_str)
            return

        sell_order_data = self.get_order(sell_data["result"]["uuid"], trade_time_limit * 60)
        # TODO: Handle partial/incomplete sales.
        self.Database.store_sell(sell_order_data["result"], stats)

        self.Messenger.print_sell(coin_pair, price, stats["rsi"], stats["profitMargin"])
        self.Messenger.send_sell_slack(coin_pair, stats["rsi"], stats["profitMargin"])
        self.Messenger.send_sell_gmail(sell_order_data["result"], stats)
        self.Messenger.play_sw_theme()

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

    def calculate_RSI(self, coin_pair, period, unit):
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

    def get_non_zero_balances(self):
        """
        Gets all non-zero user coin balances in the correct format
        """
        balances_data = self.Bittrex.get_balances()
        if not balances_data["success"]:
            error_str = self.Messenger.print_error("balance")
            logger.error(error_str)
            return
        non_zero_balances = py_.filter_(balances_data["result"], lambda balance_item: balance_item["Balance"] > 0)
        return py_.map_(non_zero_balances, lambda balance: self.create_balance_object(balance))

    def create_balance_object(self, balance_item):
        """
        Creates a new balance object containing only the relevant values and the BTC value of the coin's balance

        :param balance_item: The Bittrex user balance object for a coin
        :type balance_item: dict
        """
        btc_price = 1
        is_tracked = False
        if balance_item["Currency"] != "BTC":
            coin_pair = "BTC-" + balance_item["Currency"]
            is_tracked = coin_pair in self.Database.trades["trackedCoinPairs"]
            btc_price = self.get_current_price(coin_pair, "bid")

        try:
            btc_value = round(btc_price * balance_item["Balance"], 8)
        except TypeError as exception:
            logger.exception(exception)
            btc_value = 0

        return py_.assign(
            py_.pick(balance_item, "Currency", "Balance"),
            {"BtcValue": btc_value, "IsTracked": is_tracked}
        )
