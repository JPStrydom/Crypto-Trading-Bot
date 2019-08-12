import pydash as py_
import time

from directory_utilities import get_json_from_file, write_json_to_file
from logger import logger


class Database(object):
    """
    Used to store trade history locally
    """

    instance = None

    def __new__(cls):
        if not Database.instance:
            Database.instance = Database.__Database()
        return Database.instance

    class __Database:
        def __init__(self):
            default_app_data = {
                "coinPairs": [], "pausedTrackedCoinPairs": [],
                "pauseTime": {"buy": None}
            }

            self.app_data_file_string = "../database/app-data.json"

            self.app_data = get_json_from_file(self.app_data_file_string, default_app_data)

        def pause_buy(self, coin_pair):
            """
            Used to pause buy tracking on the coin pair

            :param coin_pair: String literal for the market (ex: BTC-LTC)
            :type coin_pair: str
            """
            self.app_data["coinPairs"].remove(coin_pair)

            write_json_to_file(self.app_data_file_string, self.app_data)

        def store_coin_pairs(self, btc_coin_pairs):
            """
            Used to store the latest Bittrex available markets and update the buy pause time

            :param btc_coin_pairs: String list of market pairs
            :type btc_coin_pairs: list
            """
            self.app_data["coinPairs"] = btc_coin_pairs
            self.app_data["pauseTime"]["buy"] = time.time()

            write_json_to_file(self.app_data_file_string, self.app_data)

        def check_resume(self, pause_time, pause_type):
            """
            Used to check if the pause type can be un-paused

            :param pause_time: The amount of minutes tracking should be paused
            :type pause_time: int
            :param pause_type: The pause type to check (one of: 'buy', 'sell', 'balance)
            :type pause_type: str
            """
            if self.app_data["pauseTime"][pause_type] is None:
                return False
            return time.time() - self.app_data["pauseTime"][pause_type] >= pause_time * 60
