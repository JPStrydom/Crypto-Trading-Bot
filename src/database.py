import pydash as py_
from datetime import datetime

from src.logger import logger
from src.directory_utilities import get_json_from_file, write_json_to_file

bittrex_trade_commission = 0.0025


class Database(object):
    """
    Used to store trade history locally
    """

    def __init__(self):
        self.file_string = 'database/trades.json'
        self.trades = get_json_from_file(self.file_string, {"trackedCoinPairs": [], "trades": []})

    def store_buy(self, coin_pair, price, rsi=-1, day_volume=-1, btc_amount=0.00001):
        """
        Used to place a trade in the database

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param price: Market's current price
        :type price: float
        :param rsi: Market's current RSI
        :type rsi: float
        :param day_volume: Market's 24 hour volume
        :type day_volume: float
        :param btc_amount: Amount of BTC to spend on coin
        :type btc_amount: float
        """
        if coin_pair in self.trades['trackedCoinPairs']:
            return logger.warning("Trying to buy on the {} market, which is already a tracked coin pair")

        current_date = datetime.now().strftime('%Y/%m/%d %I:%M:%S')

        new_buy_object = {
            "coinPair": coin_pair,
            "amount": round(btc_amount * (1 - bittrex_trade_commission) / price, 8),
            "buy": {
                "date": current_date,
                "rsi": rsi,
                "24HrVolume": day_volume,
                "price": price
            }
        }

        self.trades['trackedCoinPairs'].append(coin_pair)
        self.trades['trades'].append(new_buy_object)

        write_json_to_file(self.file_string, self.trades)

    def store_sell(self, coin_pair, price, rsi=-1, day_volume=-1):
        """
        Used to place a trade in the database

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param price: Market's current price
        :type price: float
        :param rsi: Market's current RSI
        :type rsi: float
        :param day_volume: Market's 24 hour volume
        :type day_volume: float
        """
        if coin_pair not in self.trades['trackedCoinPairs']:
            return logger.warning("Trying to sell on the {} market, which is not a tracked coin pair")

        current_date = datetime.now().strftime('%Y/%m/%d %I:%M:%S')
        trade = self.get_open_trade(coin_pair)

        sell_object = {
            "date": current_date,
            "rsi": rsi,
            "24HrVolume": day_volume,
            "price": price
        }
        profit_margin = self.get_profit_margin(coin_pair, price, trade)

        self.trades['trackedCoinPairs'].remove(coin_pair)
        trade['sell'] = sell_object
        trade['profitMargin'] = profit_margin

        write_json_to_file(self.file_string, self.trades)

    def get_open_trade(self, coin_pair):
        """
        Used to get the coin pair's unsold trade in the database

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str

        :return: The open trade object
        :rtype : dict
        """
        trade_index = py_.find_index(self.trades['trades'],
                                     lambda trade: trade['coinPair'] == coin_pair and 'sell' not in trade)

        if trade_index == -1:
            logger.error('Could not find open trade for {} coin pair'.format(coin_pair))
            return None

        return self.trades['trades'][trade_index]

    def get_profit_margin(self, coin_pair, current_price, trade=None):
        """
        Used to get the profit margin for a coin pair's trade

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param current_price: Market's current price
        :type current_price: float
        :param trade: The trade to calculate the profit margin on
            Not required. If not passed in the function will go find it
        :type trade: dict

        :return: Profit margin
        :rtype : float
        """
        if trade is None:
            trade = self.get_open_trade(coin_pair)

        buy_btc_amount = round(trade['amount'] * trade['buy']['price'] / (1 - bittrex_trade_commission), 8)
        sell_btc_amount = round(trade['amount'] * current_price * (1 - bittrex_trade_commission), 8)

        profit_margin = 100 * (sell_btc_amount - buy_btc_amount) / buy_btc_amount

        return profit_margin
