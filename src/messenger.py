import smtplib
import winsound
import time
from termcolor import cprint
from math import floor, ceil


class Messenger(object):
    """
    Used for handling messaging functionality
    """

    def __init__(self, secrets):
        self.from_address = secrets["gmail"]["username"]
        self.to_address_list = secrets["gmail"]["addressList"]
        self.login = secrets["gmail"]["username"]
        self.password = secrets["gmail"]["password"]
        self.smtp_server = "smtp.gmail.com:587"

        self.header_str = "\nTracking {} Bittrex Markets\n"

        self.recipient_name = secrets["gmail"]["recipientName"]

        self.bittrex_url = "https://bittrex.com/Market/Index?MarketName={}"

        self.pause_str = {
            "buy": "Pause buy tracking on {} with a high RSI of {} for {} minutes.",
            "sell": "Pause sell tracking on {} with a low profit margin of {}% for {} minutes."
        }
        self.resume_str = {
            "buy": "Resuming tracking on all {} markets.",
            "sell": "Resume sell tracking on {}."
        }

        self.buy_str = "Buy on {:<10}\t->\t\tRSI: {:>2}\t\t24 Hour Volume: {:>5} {}\t\tBuy Price: {:.8f}\t\tURL: {}"
        self.sell_str = "Sell on {:<10}\t->\t\tRSI: {:>2}\t\tProfit Margin: {:>4} %\t\tSell Price: {:.8f}\t\tURL: {}"

        self.previous_no_sell_str = ""

        self.error_str = {
            "connection": "Unable to connect to the internet. Please check your connection and try again.",
            "SSL": "An SSL error occurred. Waiting 30 seconds and then retrying.",
            "JSONDecode": "Failed to decode JSON.",
            "keyError": "Invalid key provided to obj/dict.",
            "valueError": "Value error occurred.",
            "typeError": "Type error occurred.",
            "unknown": "An unknown exception occurred."
        }

        self.order_error_str = "Failed to complete order with UUID {} within {} seconds on {} market."

    def generate_bittrex_URL(self, coin_pair):
        """
        Generates the URL string for the coin pairs Bittrex page
        """
        return self.bittrex_url.format(coin_pair)

    def send_email(self, subject, message):
        """
        Used to send an email from the account specified in the secrets.json file to the entire
        address list specified in the secrets.json file

        :param subject: Email subject
        :type subject: str
        :param message: Email content
        :type message: str

        :return: Errors received from the smtp server (if any)
        :rtype : dict
        """
        header = "From: %s\n" % self.from_address
        header += "To: %s\n" % ",".join(self.to_address_list)
        header += "Subject: %s\n\n" % subject
        message = header + message

        server = smtplib.SMTP(self.smtp_server)
        server.starttls()
        server.login(self.login, self.password)
        errors = server.sendmail(self.from_address, self.to_address_list, message)
        server.quit()
        return errors

    def send_RSI_email(self, coin_pair, rsi, day_volume, recipient_name=None):
        """
        Used to send a low RSI specific email from the account specified in the secrets.json file to the entire
        address list specified in the secrets.json file

        :param coin_pair: Coin pair the low RSI occurred on (ex: BTC-ETH)
        :type coin_pair: str
        :param rsi: Low RSI
        :type rsi: float
        :param day_volume: Coin pair's current 24 hour volume
        :type day_volume: float
        :param recipient_name: Name of the email's recipient (ex: John)
        :type recipient_name: str
        """
        if recipient_name is None:
            recipient_name = self.recipient_name
        subject = "Crypto Bot: Low RSI on {} Market".format(coin_pair)
        message = (
            "Howdy {},\n\nI've detected a low RSI of {} on the {} market. The current 24 hour market volume is {}\n\n"
            "Here's a Bittrex URL: {}\n\nRegards,\nCrypto Bot"
        ).format(recipient_name, ceil(rsi), coin_pair, floor(day_volume), self.generate_bittrex_URL(coin_pair))
        self.send_email(subject, message)

    def send_buy_email(self, order, stats, recipient_name=None):
        """
        Used to send a buy specific email from the account specified in the secrets.json file to the entire
        address list specified in the secrets.json file

        :param order: Bittrex trade object results field
        :type order: dict
        :param stats: The stats related to the trade
        :type stats: dict
        :param recipient_name: Name of the email"s recipient (ex: John)
        :type recipient_name: str
        """
        if recipient_name is None:
            recipient_name = self.recipient_name
        main_market, coin = order["Exchange"].split("-")
        subject = "Crypto Bot: Buy on {} Market".format(order["Exchange"])
        message = (
            "Howdy {},\n\nI've just bought {} {} on the {} market - which is currently valued at {} {}.\n\n"
            "The market currently has an RSI of {} and a 24 hour market volume of {} {}.\n\n"
            "Here's a Bittrex URL: {}\n\nRegards,\nCrypto Bot"
        ).format(recipient_name, round(order["Quantity"], 4), coin, order["Exchange"], order["Price"], main_market,
                 ceil(stats["rsi"]), floor(stats["24HrVolume"]), main_market,
                 self.generate_bittrex_URL(order["Quantity"]))
        self.send_email(subject, message)

    def send_sell_email(self, order, stats, recipient_name=None):
        """
        Used to send a sell specific email from the account specified in the secrets.json file to the entire
        address list specified in the secrets.json file

        :param order: Bittrex trade object results field
        :type order: dict
        :param stats: The stats related to the trade
        :type stats: dict
        :param recipient_name: Name of the email's recipient (ex: John)
        :type recipient_name: str
        """
        if recipient_name is None:
            recipient_name = self.recipient_name
        main_market, coin = order["Exchange"].split("-")
        subject = "Crypto Bot: Sell on {} Market".format(order["Exchange"])
        message = (
            "Howdy {},\n\nI've just sold {} {} on the {} market - which is currently valued at {} {}.\n\n"
            "The market currently has an RSI of {} and a profit of {}% was made.\n\n"
            "Here's a Bittrex URL: {}\n\nRegards,\nCrypto Bot"
        ).format(recipient_name, round(order["Quantity"], 4), coin, order["Exchange"], order["Price"], main_market,
                 floor(stats["rsi"]), round(stats["profitMargin"], 2), self.generate_bittrex_URL(order["Exchange"]))
        self.send_email(subject, message)

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
        cprint(self.buy_str.format(coin_pair, ceil(rsi), floor(day_volume), main_market, current_buy_price,
                                   self.generate_bittrex_URL(coin_pair)), "blue", attrs=["bold"])

    def print_sell(self, coin_pair, current_sell_price, rsi, profit_margin):
        """
        Used to print a sales's info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param current_sell_price: Market's current price
        :type current_sell_price: float
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param profit_margin: Profit made on the trade
        :type profit_margin: float
        """
        cprint(self.sell_str.format(coin_pair, floor(rsi), round(profit_margin, 2), current_sell_price,
                                    self.generate_bittrex_URL(coin_pair)), "green", attrs=["bold"])

    def print_pause(self, coin_pair, value, pause_time, pause_type):
        """
        Used to print coin pause info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param value: Relevant resume value
        :type value: float
        :param pause_time: The amount of minutes to tracking will be paused on the coin pair
        :type pause_time: float
        :param pause_type: Type of pause (one of: 'buy', 'sell')
        :type pause_type: str
        """
        if value is None:
            value = 'N/A'
        elif value < 0:
            value = round(value, 2)
        else:
            value = floor(value)
        print_str = self.pause_str[pause_type].format(coin_pair, value, round(pause_time))
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
        print_str = "No " + self.buy_str.format(coin_pair, ceil(rsi), floor(day_volume), main_market,
                                                current_buy_price, self.generate_bittrex_URL(coin_pair))
        cprint(print_str, "grey")

    def print_no_sell(self, coin_pair, rsi, profit_margin, current_sell_price):
        """
        Used to print a no-sales's info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param profit_margin: Profit made on the trade
        :type profit_margin: float
        :param current_sell_price: Market's current price
        :type current_sell_price: float
        """
        print_str = "No " + self.sell_str.format(coin_pair, floor(rsi), round(profit_margin, 2), current_sell_price,
                                                 self.generate_bittrex_URL(coin_pair))
        if print_str != self.previous_no_sell_str:
            color = "magenta"
            if profit_margin <= 0:
                color = "red"
            self.previous_no_sell_str = print_str
            cprint(print_str, color)

    def print_resume_pause(self, value, pause_type):
        """
        Used to print coin pause resume info to the console

        :param value: Relevant resume value
        :type value: float
        :param pause_type: Type of pause (one of: 'buy', 'sell')
        :type pause_type: str
        """
        print_str = self.resume_str[pause_type].format(value)
        cprint(print_str, "yellow", attrs=["bold"])

    def print_exception_error(self, error_type):
        """
        Prints the error type message to the console

        :param error_type: The error type
            (one of: 'connection', 'SSL', 'JSONDecode', 'keyError', 'valueError', 'typeError', 'unknown')
        :type error_type: str
        """
        cprint("\n" + self.error_str[error_type] + "\n", "red", attrs=["bold"])
        self.play_beep()

    def print_order_error(self, order_uuid, trade_time_limit, coin_pair):
        """
        Prints an order error message to the console

        :param order_uuid: The order UUID
        :type order_uuid: str
        :param trade_time_limit: The trade time limit in seconds
        :type trade_time_limit: float
        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str

        :return: Error string
        :rtype : str
        """
        error_str = self.order_error_str.format(order_uuid, trade_time_limit, coin_pair)
        cprint("\n" + error_str + "\n", "red", attrs=["bold"])
        return error_str

    @staticmethod
    def play_beep(frequency=1000, duration=1000):
        """
        Used to play a beep sound

        :param frequency: The frequency of the beep
        :type frequency: int
        :param duration: The duration of the beep
        :type duration: int
        """
        winsound.Beep(frequency, duration)

    @staticmethod
    def play_sw_theme():
        """
        Used to play the Star Wars theme song
        """
        winsound.Beep(1046, 800)
        winsound.Beep(1567, 800)
        winsound.Beep(1396, 50)
        winsound.Beep(1318, 50)
        winsound.Beep(1174, 50)
        winsound.Beep(2093, 800)

        time.sleep(0.3)

        winsound.Beep(1567, 600)
        winsound.Beep(1396, 50)
        winsound.Beep(1318, 50)
        winsound.Beep(1174, 50)
        winsound.Beep(2093, 800)

        time.sleep(0.3)

        winsound.Beep(1567, 600)
        winsound.Beep(1396, 50)
        winsound.Beep(1318, 50)
        winsound.Beep(1396, 50)
        winsound.Beep(1174, 800)

    @staticmethod
    def play_sw_imperial_march():
        """
        Used to play the Star Wars Imperial March song
        """
        winsound.Beep(440, 500)
        winsound.Beep(440, 500)
        winsound.Beep(440, 500)

        winsound.Beep(349, 375)
        winsound.Beep(523, 150)
        winsound.Beep(440, 600)

        winsound.Beep(349, 375)
        winsound.Beep(523, 150)
        winsound.Beep(440, 1000)

        time.sleep(0.2)

        winsound.Beep(659, 500)
        winsound.Beep(659, 500)
        winsound.Beep(659, 500)

        winsound.Beep(698, 375)
        winsound.Beep(523, 150)
        winsound.Beep(415, 600)

        winsound.Beep(349, 375)
        winsound.Beep(523, 150)
        winsound.Beep(440, 1000)
