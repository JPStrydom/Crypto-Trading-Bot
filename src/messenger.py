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

    def __init__(self, secrets):
        self.gmail = False
        if "gmail" in secrets:
            self.gmail = True
            self.from_address = secrets["gmail"]["username"]
            self.to_address_list = secrets["gmail"]["addressList"]
            self.login = secrets["gmail"]["username"]
            self.password = secrets["gmail"]["password"]
            self.recipient_name = secrets["gmail"]["recipientName"]
            self.smtp_server_address = "smtp.gmail.com:587"

        self.slack = False
        if "slack" in secrets:
            self.slack = True
            self.slack_channel = secrets["slack"]["channel"]
            self.slack_client = SlackClient(secrets["slack"]["token"])

        self.sound = False
        if "sound" in secrets:
            self.sound = secrets["sound"]

        self.header_str = "\nTracking {} Bittrex Markets\n"

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
        self.sell_str = "Sell on {:<10}\t->\t\tRSI: {:>2}\t\tProfit Margin: {:>4}%\t\tSell Price: {:.8f}\t\tURL: {}"

        self.slack_buy_str = {
            "emoji": ":money_with_wings:",
            "message": "*Buy on {}*\n>>>\n_RSI: *{}*_\n_24 Hour Volume: *{} {}*_"
        }
        self.slack_sell_str = {
            "emoji": ":moneybag:",
            "message": "*Sell on {}*\n>>>\n_RSI: *{}*_\n_Profit Margin: *{}%*_"
        }

        self.previous_no_sell_str = ""

        self.exception_error_str = {
            "SSL": "An SSL error occurred.",
            "connection": "Unable to connect to the internet.",
            "JSONDecode": "Failed to decode JSON.",
            "typeError": "Type error occurred.",
            "keyError": "Invalid key provided to obj/dict.",
            "valueError": "Value error occurred.",
            "unknown": "An unknown exception occurred."
        }

        self.order_error_str = "Failed to complete order with UUID {} within {} seconds on {} market. URL: {}"

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
        if not self.gmail:
            return

        header = "From: %s\n" % self.from_address
        header += "To: %s\n" % ",".join(self.to_address_list)
        header += "Subject: %s\n\n" % subject
        message = header + message

        server = smtplib.SMTP(self.smtp_server_address)
        server.starttls()
        server.login(self.login, self.password)
        errors = server.sendmail(self.from_address, self.to_address_list, message)
        server.quit()

        return errors

    def send_slack(self, message):
        """
        Send slack message to notify users

        :param message: The message to send on the slack channel
        :type message: str
        """
        if not self.slack:
            return

        self.slack_client.api_call(
            "chat.postMessage",
            channel=self.slack_channel,
            text=message
        )

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
        message = self.buy_str.format(coin_pair, ceil(rsi), floor(day_volume), main_market, current_buy_price,
                                      self.generate_bittrex_URL(coin_pair))
        slack_emoji = self.slack_buy_str["emoji"] * 8 + "\n"
        slack_message = slack_emoji + self.slack_buy_str["message"].format(coin_pair, ceil(rsi), floor(day_volume),
                                                                           main_market)

        cprint(message, "blue", attrs=["bold"])
        self.send_slack(slack_message)

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
        message = self.sell_str.format(coin_pair, floor(rsi), round(profit_margin, 2), current_sell_price,
                                       self.generate_bittrex_URL(coin_pair))
        slack_emoji = self.slack_sell_str["emoji"] * 8 + "\n"
        slack_message = slack_emoji + self.slack_sell_str["message"].format(coin_pair, floor(rsi),
                                                                            round(profit_margin, 2))

        cprint(message, "green", attrs=["bold"])
        self.send_slack(slack_message)

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

    def print_exception_error(self, error_type, will_exit=False):
        """
        Prints the error type message to the console

        :param error_type: The error type
            (one of: 'connection', 'SSL', 'JSONDecode', 'keyError', 'valueError', 'typeError', 'unknown')
        :type error_type: str
        :param will_exit: Whether the program is exiting or not
        :type will_exit: bool
        """
        suffix = " Waiting 10 seconds and then retrying."
        if will_exit:
            suffix = " Exiting program."
        cprint("\n" + self.exception_error_str[error_type] + suffix + "\n", "red", attrs=["bold"])
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
        error_str = self.order_error_str.format(order_uuid, trade_time_limit, coin_pair,
                                                self.generate_bittrex_URL(coin_pair))
        cprint("\n" + error_str + "\n", "red", attrs=["bold"])
        return error_str

    def generate_bittrex_URL(self, coin_pair):
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

    def play_sw_theme(self):
        """
        Used to play the Star Wars theme song
        """
        self.play_beep(1046, 880)
        self.play_beep(1567, 880)
        self.play_beep(1396, 55)
        self.play_beep(1318, 55)
        self.play_beep(1174, 55)
        self.play_beep(2093, 880)

        time.sleep(0.3)

        self.play_beep(1567, 600)
        self.play_beep(1396, 55)
        self.play_beep(1318, 55)
        self.play_beep(1174, 55)
        self.play_beep(2093, 880)

        time.sleep(0.3)

        self.play_beep(1567, 600)
        self.play_beep(1396, 55)
        self.play_beep(1318, 55)
        self.play_beep(1396, 55)
        self.play_beep(1174, 880)

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
