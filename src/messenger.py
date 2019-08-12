import smtplib
import time
from slackclient import SlackClient
from termcolor import cprint
from math import floor, ceil

try:
    import winsound
except ImportError:
    winsound = None


class Messenger(object):
    """
    Used for handling messaging functionality
    """

    def __init__(self, settings):
        self.sound = False
        if "sound" in settings:
            self.sound = settings["sound"]

        self.header_str = "\nTracking {} Bittrex Markets\n"

        self.bittrex_url = "https://bittrex.com/Market/Index?MarketName={}"

        self.console_str = {
            "buy": {
                "pause": "Pause buy tracking on {} with a high RSI of {} and a 24 hour volume of {} {} for {} minutes.",
                "resume": "Resuming tracking on all {} markets.",
                "message": "Buy on {:<10}\t->\t\tRSI: {:>2}\t\t24 Hour Volume: {:>5} {}\t\tBuy Price: {:.8f}\t\tURL: {}"
            }
        }

        self.error_str = {
            "market": "Failed to fetch Bittrex markets.",
            "coinMarket": "Failed to fetch Bittrex market summary for the {} market.",

            "SSL": "An SSL error occurred.",
            "connection": "Unable to connect to the internet.",
            "JSONDecode": "Failed to decode JSON.",
            "typeError": "Type error occurred.",
            "keyError": "Invalid key provided to obj/dict.",
            "valueError": "Value error occurred.",
            "unknown": "An unknown exception occurred.",

            "general": "See the latest log file for more information."
        }

    def print_header(self, num_of_coin_pairs):
        """
        Used to print the console header

        :param num_of_coin_pairs: Number of available Bittrex market pairs
        :type num_of_coin_pairs: int
        """
        cprint(self.header_str.format(num_of_coin_pairs), attrs=["bold", "underline"])

    def print_buy(self, coin_pair, current_buy_price, rsi, day_volume):
        """
        Used to print a buy's info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param current_buy_price: Market's current price
        :type current_buy_price: float
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param day_volume: Coin pair's current 24 hour volume
        :type day_volume: float
        """
        main_market, coin = coin_pair.split("-")
        message = self.console_str["buy"]["message"].format(
            coin_pair, ceil(rsi), floor(day_volume), main_market, current_buy_price, self.get_bittrex_url(coin_pair)
        )
        cprint(message, "blue", attrs=["bold"])

    def print_pause(self, coin_pair, data, pause_time):
        """
        Used to print coin pause info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param data: Relevant pause values
        :type data: list
        :param pause_time: The amount of minutes to tracking will be paused on the coin pair
        :type pause_time: float
        """
        main_market, coin = coin_pair.split("-")
        data[0] = floor(data[0])
        data[1] = floor(data[1])
        print_str = self.console_str["buy"]["pause"].format(
            coin_pair, data[0], data[1], main_market, round(pause_time)
        )
        cprint(print_str, "yellow")

    def print_no_buy(self, coin_pair, rsi, day_volume, current_buy_price):
        """
        Used to print a no-buy's info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param day_volume: Coin pair's current 24 hour volume
        :type day_volume: float
        :param current_buy_price: Market's current price
        :type current_buy_price: float
        """
        main_market, coin = coin_pair.split("-")
        print_str = "No " + self.console_str["buy"]["message"].format(
            coin_pair, ceil(rsi), floor(day_volume), main_market, current_buy_price, self.get_bittrex_url(coin_pair)
        )
        cprint(print_str, "grey")

    def print_resume_pause(self, data):
        """
        Used to print coin pause resume info to the console

        :param data: Relevant resume value
        :type data: float
        """
        print_str = self.console_str["buy"]["resume"].format(data)
        cprint(print_str, "yellow", attrs=["bold"])

    def print_error(self, error_type, data=None, will_exit=False):
        """
        Prints the error type message to the console

        :param error_type: The error type
            (one of: 'market', 'coinMarket', 'connection', 'SSL', 'JSONDecode', 'keyError',
            'valueError', 'typeError', 'unknown')
        :type error_type: str
        :param data: Relevant error information
        :type data: list
        :param will_exit: Whether the program is exiting or not
        :type will_exit: bool

        :return: Error string
        :rtype: str
        """
        suffix = ""
        if will_exit:
            suffix = " Exiting program."
        elif error_type in ['connection', 'SSL', 'JSONDecode', 'keyError', 'valueError', 'typeError', 'unknown']:
            suffix = " Waiting 10 seconds and then retrying."

        error_str = self.error_str[error_type]
        if error_type == "coinMarket":
            error_str = error_str.format(data[0])
        elif error_type == "buy":
            error_str = error_str.format(data[0], data[1])
        elif error_type == "order":
            error_str = error_str.format(data[0], data[1], data[2], self.get_bittrex_url(data[2]))

        cprint("\n" + error_str + suffix, "red", attrs=["bold"])
        cprint(self.error_str["general"] + "\n", "grey", attrs=["bold"])
        self.play_beep()

        return error_str

    def get_bittrex_url(self, coin_pair):
        """
        Generates the URL string for the coin pairs Bittrex page
        """
        return self.bittrex_url.format(coin_pair)

    def play_beep(self, frequency=1000, duration=1000):
        """
        Used to play a beep sound

        :param frequency: The frequency of the beep
        :type frequency: int
        :param duration: The duration of the beep
        :type duration: int
        """
        if not self.sound or winsound is None:
            return
        winsound.Beep(frequency, duration)

    def play_sw_imperial_march(self):
        """
        Used to play the Star Wars Imperial March song
        """
        self.play_beep(440, 500)
        self.play_beep(440, 500)
        self.play_beep(440, 500)

        self.play_beep(349, 375)
        self.play_beep(523, 150)
        self.play_beep(440, 600)

        self.play_beep(349, 375)
        self.play_beep(523, 150)
        self.play_beep(440, 1000)

        time.sleep(0.2)

        self.play_beep(659, 500)
        self.play_beep(659, 500)
        self.play_beep(659, 500)

        self.play_beep(698, 375)
        self.play_beep(523, 150)
        self.play_beep(415, 600)

        self.play_beep(349, 375)
        self.play_beep(523, 150)
        self.play_beep(440, 1000)
