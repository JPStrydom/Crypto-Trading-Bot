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

    def simulate_buy(self, coin_pair, rsi, price, btc_amount=1):
        if coin_pair in self.simulated_trades['trackedCoinPairs']:
            return logger.warning("Trying to buy on the {} market, which is already a tracked coin pair")
        current_date = datetime.now().strftime('%Y/%m/%d %I:%M:%S')
        new_buy_object = {
            "coinPair": coin_pair,
            "amount": btc_amount * (1 - bittrex_trade_commission) / price,
            "buy": {
                "date": current_date,
                "rsi": rsi,
                "price": price
            }
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
        sell_object = {
            "date": current_date,
            "rsi": rsi,
            "price": price
        }

        with open(self.file_string, 'w') as simulated_trades_file:
            self.simulated_trades['trackedCoinPairs'].remove(coin_pair)
            simulated_trade = self.get_simulated_trade(coin_pair)
            simulated_trade['sell'] = sell_object
            simulated_trade['profit_margin'] = self.get_simulated_profit_margin(coin_pair, price)
            json.dump(self.simulated_trades, simulated_trades_file, indent=4)
            simulated_trades_file.close()

    def get_simulated_trade(self, coin_pair):
        trade_index = py_.find_index(self.simulated_trades['trades'],
                                     lambda trade: trade['coinPair'] == coin_pair)
        return self.simulated_trades['trades'][trade_index]

    def get_simulated_profit_margin(self, coin_pair, current_price):
        trade = self.get_simulated_trade(coin_pair)
        buy_btc_amount = trade['amount'] * trade['buy']['price']
        sell_btc_amount = trade['amount'] * current_price * (1 - bittrex_trade_commission)

        return 100 * (sell_btc_amount - buy_btc_amount) / buy_btc_amount
