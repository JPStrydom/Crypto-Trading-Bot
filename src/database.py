import pydash as py_
import time

from src.directory_utilities import get_json_from_file, write_json_to_file
from src.logger import logger

bittrex_trade_commission = 0.0025


class Database(object):
    """
    Used to store trade history locally
    """

    def __init__(self):
        default_trades = {"trackedCoinPairs": [], "trades": []}
        default_app_data = {"coinPairs": [], "pauseTime": {"buy": None, "sell": None}}

        self.trades_file_string = "database/trades.json"
        self.app_data_file_string = "database/app-data.json"

        self.trades = get_json_from_file(self.trades_file_string, default_trades)
        self.app_data = get_json_from_file(self.app_data_file_string, default_app_data)

    @staticmethod
    def convert_bittrex_order_object(bittrex_order, stats=None):
        """
        Used to convert a Bittrex order object to a database buy object
        and add stats to it of they are provided.

        :param bittrex_order: Bittrex buy order object
        :type bittrex_order: dict
        :param stats: The buy stats to store
        :type stats: dict
        """
        database_order = {
            "orderUuid": bittrex_order["OrderUuid"],
            "dateOpened": bittrex_order["Opened"],
            "dateClosed": bittrex_order["Closed"],
            "price": bittrex_order["Price"],
            "unitPrice": bittrex_order["PricePerUnit"],
            "commissionPaid": bittrex_order["CommissionPaid"]
        }
        if stats is not None:
            database_order["stats"] = stats
        return database_order

    def store_initial_buy(self, coin_pair, buy_order_uuid):
        """
        Used to place an initial trade in the database

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param buy_order_uuid: The buy order's UUID
        :type buy_order_uuid: str
        """
        if coin_pair in self.trades["trackedCoinPairs"]:
            return logger.warning("Trying to buy on the {} market which is already tracked.".format(coin_pair))

        new_buy_object = {
            "coinPair": coin_pair,
            "quantity": 0,
            "buy": {
                "orderUuid": buy_order_uuid
            }
        }

        self.trades["trackedCoinPairs"].append(coin_pair)
        self.trades["trades"].append(new_buy_object)

        write_json_to_file(self.trades_file_string, self.trades)

    def store_buy(self, bittrex_order, stats):
        """
        Used to place a buy trade in the database

        :param bittrex_order: Bittrex buy order object
        :type bittrex_order: dict
        :param stats: The buy stats to store
        :type stats: dict
        """
        if bittrex_order["Exchange"] not in self.trades["trackedCoinPairs"]:
            return logger.warning(
                "Trying to buy on the {} market without an initial buy object.".format(bittrex_order["Exchange"])
            )

        order = self.convert_bittrex_order_object(bittrex_order, stats)

        trade = self.get_open_trade(bittrex_order["Exchange"])
        trade["quantity"] = bittrex_order["Quantity"] - bittrex_order["QuantityRemaining"]
        trade["buy"] = order

        write_json_to_file(self.trades_file_string, self.trades)

    def store_sell(self, bittrex_order, stats):
        """
        Used to place a sell trade in the database

        :param bittrex_order: Bittrex sell order object
        :type bittrex_order: dict
        :param stats: The sell stats to store
        :type stats: dict
        """
        if bittrex_order["Exchange"] not in self.trades["trackedCoinPairs"]:
            return logger.warning(
                "Trying to sell on the {} market which is not tracked.".format(bittrex_order["Exchange"])
            )

        order = self.convert_bittrex_order_object(bittrex_order, stats)

        trade = self.get_open_trade(bittrex_order["Exchange"])
        trade["sell"] = order
        self.trades["trackedCoinPairs"].remove(bittrex_order["Exchange"])

        write_json_to_file(self.trades_file_string, self.trades)

    def get_open_trade(self, coin_pair):
        """
        Used to get the coin pair's unsold trade in the database

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str

        :return: The open trade object
        :rtype : dict
        """
        trade_index = py_.find_index(self.trades["trades"],
                                     lambda trade: trade["coinPair"] == coin_pair and "sell" not in trade)

        if trade_index == -1:
            logger.error("Could not find open trade for {} coin pair".format(coin_pair))
            return None

        return self.trades["trades"][trade_index]

    def get_profit_margin(self, coin_pair, current_price, trade=None):
        """
        Used to get the profit margin for a coin pair"s trade

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param current_price: Market"s current price
        :type current_price: float
        :param trade: The trade to calculate the profit margin on
            Not required. If not passed in the function will go find it
        :type trade: dict

        :return: Profit margin
        :rtype : float
        """
        if trade is None:
            trade = self.get_open_trade(coin_pair)

        buy_btc_quantity = round(trade["buy"]["price"] / (1 - bittrex_trade_commission), 8)
        sell_btc_quantity = round(trade["quantity"] * current_price * (1 - bittrex_trade_commission), 8)

        profit_margin = 100 * (sell_btc_quantity - buy_btc_quantity) / buy_btc_quantity

        return profit_margin

    def store_coin_pairs(self, btc_coin_pairs):
        self.app_data["coinPairs"] = btc_coin_pairs
        self.app_data["pauseTime"]["buy"] = time.time()

        write_json_to_file(self.app_data_file_string, self.app_data)

    def resume_sells(self):
        no_sell_trades = py_.filter_(
            self.trades["trades"],
            lambda trade: trade["coinPair"] not in self.trades["trackedCoinPairs"] and "sell" not in trade
        )
        no_sell_trades = py_.map_(no_sell_trades, lambda trade: trade["coinPair"])

        if len(no_sell_trades) < 1:
            return

        for sell in no_sell_trades:
            self.trades["trackedCoinPairs"].append(sell)
        self.app_data["pauseTime"]["sell"] = None

        # TODO: Add proper print function
        print("Resuming sells on {}".format(no_sell_trades))

        write_json_to_file(self.trades_file_string, self.trades)
        write_json_to_file(self.app_data_file_string, self.app_data)

    def pause_buy(self, coin_pair):
        self.app_data["coinPairs"].remove(coin_pair)

        write_json_to_file(self.app_data_file_string, self.app_data)

    def pause_sell(self, coin_pair):
        self.trades["trackedCoinPairs"].remove(coin_pair)
        self.app_data["pauseTime"]["sell"] = time.time()

        write_json_to_file(self.trades_file_string, self.trades)
        write_json_to_file(self.app_data_file_string, self.app_data)

    def check_resume(self, pause_time, pause_type):
        if self.app_data["pauseTime"][pause_type] is None:
            return False
        return time.time() - self.app_data["pauseTime"][pause_type] >= pause_time * 60
