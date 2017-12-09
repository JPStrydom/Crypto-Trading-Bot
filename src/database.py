import json
from datetime import datetime
import pydash as py_

from src.logger import logger

bittrex_trade_commission = 0.0025


class Database(object):
    """
    Used for requesting Bittrex with API key and API secret
    """

    def __init__(self, trade_strategy_index):
        self.file_string = 'database/simulated-trades-{}.json'.format(trade_strategy_index)
        try:
            with open(self.file_string) as simulated_trades_file:
                self.simulated_trades = json.load(simulated_trades_file)
                simulated_trades_file.close()
        except (IOError, json.decoder.JSONDecodeError):
            with open(self.file_string, 'w') as simulated_trades_file:
                self.simulated_trades = {"trackedCoinPairs": [], "trades": []}
                json.dump(self.simulated_trades, simulated_trades_file, indent=4)
                simulated_trades_file.close()

    def simulate_buy(self, coin_pair, rsi, price, amount=1):
        if coin_pair in self.simulated_trades['trackedCoinPairs']:
            return logger.warning("Trying to buy on the {} market, which is already a tracked coin pair")
        current_date = datetime.now().strftime('%Y/%m/%d %I:%M:%S')
        new_buy_object = {
            "coinPair": coin_pair,
            "amount": amount * (1 - bittrex_trade_commission),
            "buy": {
                "date": current_date,
                "rsi": rsi,
                "price": price
            },
            "sell": {}
        }
        with open(self.file_string, 'w') as simulated_trades_file:
            self.simulated_trades['trackedCoinPairs'].append(coin_pair)
            self.simulated_trades['trades'].append(new_buy_object)
            json.dump(self.simulated_trades, simulated_trades_file, indent=4)
            simulated_trades_file.close()

    def simulate_sell(self, coin_pair, rsi, price):
        if coin_pair not in self.simulated_trades['trackedCoinPairs']:
            return logger.warning("Trying to sell on the {} market, which is not a tracked coin pair")
        current_date = datetime.now().strftime('%Y/%m/%d %I:%M:%S')
        new_sell_object = {
            "date": current_date,
            "rsi": rsi,
            "price": price
        }

        with open(self.file_string, 'w') as simulated_trades_file:
            self.simulated_trades['trackedCoinPairs'].remove(coin_pair)
            trade_index = py_.find_index(self.simulated_trades['trades'],
                                         lambda trade: trade['sell'] == {} and trade['coinPair'] == coin_pair)
            self.simulated_trades['trades'][trade_index]['sell'] = new_sell_object
            json.dump(self.simulated_trades, simulated_trades_file, indent=4)
            simulated_trades_file.close()

    def find_buy_price(self, coin_pair):
        trade_index = py_.find_index(self.simulated_trades['trades'],
                                     lambda trade: trade['coinPair'] == coin_pair)
        return self.simulated_trades['trades'][trade_index]['buy']['price']
