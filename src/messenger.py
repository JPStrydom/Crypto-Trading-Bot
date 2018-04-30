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

    def __init__(self, secrets, settings):
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
        if "sound" in settings:
            self.sound = settings["sound"]

        self.header_str = "\nTracking {} Bittrex Markets\n"

        self.bittrex_url = "https://bittrex.com/Market/Index?MarketName={}"

        self.console_str = {
            "buy": {
                "pause": "Pause buy tracking on {} with a high RSI of {} and a 24 hour volume of {} {} for {} minutes.",
                "resume": "Resuming tracking on all {} markets.",
                "message": "Buy on {:<10}\t->\t\tRSI: {:>2}\t\t24 Hour Volume: {:>5} {}\t\tBuy Price: {:.8f}\t\tURL: {}"
            },
            "sell": {
                "pause": "Pause sell tracking on {} with a low profit margin of {}% and an RSI of {} for {} minutes.",
                "resume": "Resume sell tracking on {}.",
                "message": "Sell on {:<10}\t->\t\tRSI: {:>2}\t\tProfit Margin: {:>4}%\t\tSell Price: {:.8f}\t\tURL: {}",
                "previousMessage": ""
            }
        }

        self.email_str = {
            "buy": {
                "subject": "Crypto Bot: Buy on {} Market",
                "message": ("Howdy {},\n\nI've just bought {} {} on the {} market - which is currently valued at {} {}."
                            "\n\nThe market currently has an RSI of {} and a 24 hour market volume of {} {}."
                            "\n\nHere's a Bittrex URL: {}\n\nRegards,\nCrypto Bot")
            },
            "sell": {
                "subject": "Crypto Bot: Sell on {} Market",
                "message": ("Howdy {},\n\nI've just sold {} {} on the {} market - which is currently valued at {} {}."
                            "\n\nThe market currently has an RSI of {} and a {} of {}% was made.\n\n"
                            "Here's a Bittrex URL: {}\n\nRegards,\nCrypto Bot")
            }
        }

        self.slack_str = {
            "buy": {
                "emoji": ":heavy_minus_sign:",
                "message": "*Buy on {}*\n>>>\n_RSI: *{}*_\n_24 Hour Volume: *{} {}*_"},
            "sell": {
                "profit_emoji": ":heavy_check_mark:",
                "loss_emoji": ":x:",
                "message": "*Sell on {}*\n>>>\n_RSI: *{}*_\n_Profit Margin: *{}%*_"
            },
            "balance": {
                "emoji": ":bell:",
                "header": "*User Balances*\n\n>>>",
                "subHeader": "\n• *{}*\n",
                "subHeaderUntracked": "\n• *{} _(Untracked)_*\n",
                "subHeaderTotal": "\n*_{}_* {}\n",
                "balance": ">_Balance_: *{} {}*\n",
                "btcValue": ">_BTC Value_: *{} BTC*\n"
            }
        }

        self.error_str = {
            "market": "Failed to fetch Bittrex markets.",
            "coinMarket": "Failed to fetch Bittrex market summary for the {} market.",
            "sell": "Failed to sell on {} market. Bittrex error message: {}",
            "buy": "Failed to buy on {} market. Bittrex error message: {}",
            "order": "Failed to complete order with UUID {} within {} seconds on {} market. URL: {}",
            "balance": "Failed to fetch user Bittrex balances.",

            "SSL": "An SSL error occurred.",
            "connection": "Unable to connect to the internet.",
            "JSONDecode": "Failed to decode JSON.",
            "typeError": "Type error occurred.",
            "keyError": "Invalid key provided to obj/dict.",
            "valueError": "Value error occurred.",
            "unknown": "An unknown exception occurred.",

            "general": "See the latest log file for more information."
        }

    def send_email(self, subject, message):
        """
        Used to send an email from the account specified in the secrets.json file to the entire
        address list specified in the secrets.json file

        :param subject: Email subject
        :type subject: str
        :param message: Email content
        :type message: str

        :return: Errors received from the smtp server (if any)
        :rtype: dict
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

    def send_buy_gmail(self, order, stats, recipient_name=None):
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
        subject = self.email_str["buy"]["subject"].format(order["Exchange"])
        message = self.email_str["buy"]["message"].format(
            recipient_name, round(order["Quantity"], 4), coin, order["Exchange"], order["Price"], main_market,
            ceil(stats["rsi"]), floor(stats["24HrVolume"]), main_market, self.get_bittrex_URL(order["Exchange"])
        )
        self.send_email(subject, message)

    def send_sell_gmail(self, order, stats, recipient_name=None):
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

        type_str = "profit"
        if stats["profitMargin"] <= 0:
            type_str = "loss"

        main_market, coin = order["Exchange"].split("-")
        subject = self.email_str["sell"]["subject"].format(order["Exchange"])
        message = self.email_str["sell"]["message"].format(
            recipient_name, round(order["Quantity"], 4), coin, order["Exchange"], order["Price"], main_market,
            floor(stats["rsi"]), type_str, abs(round(stats["profitMargin"], 2)), self.get_bittrex_URL(order["Exchange"])
        )
        self.send_email(subject, message)

    def send_balance_slack(self, balance_items, previous_total_balance):
        """
        Used to send a user balance Slack message

        :param balance_items: A list containing all the user's correctly formatted coin balance objects
        :type balance_items: list
        :param previous_total_balance: The previous total balance's BTC value
        :type previous_total_balance: float

        :return: The current balance's total BTC value
        :rtype: float
        """
        slack_emoji = self.slack_str["balance"]["emoji"] * 8 + "\n"
        slack_message = slack_emoji + self.slack_str["balance"]["header"]
        total_balance = 0

        for balance in balance_items:
            sub_header = self.slack_str["balance"]["subHeader"]
            if not balance["IsTracked"] and balance["Currency"] != "BTC":
                sub_header = self.slack_str["balance"]["subHeaderUntracked"]
            slack_message += sub_header.format(balance["Currency"])

            if balance["Currency"] != "BTC":
                slack_message += self.slack_str["balance"]["balance"].format(balance["Balance"], balance["Currency"])

            slack_message += self.slack_str["balance"]["btcValue"].format(balance["BtcValue"])

            total_balance += balance["BtcValue"]

        total_balance = round(total_balance, 8)
        percentage_change_str = ""
        if previous_total_balance is not None:
            percentage_change = round((total_balance - previous_total_balance) * 100 / previous_total_balance, 2)
            if abs(percentage_change) > 0:
                icon = "▲ "
                if percentage_change < 0:
                    icon = "▼ "
                percentage_change_str = "_(" + icon + str(abs(percentage_change)) + "%)_"
        slack_message += self.slack_str["balance"]["subHeaderTotal"].format("Total Balance", percentage_change_str) + (
            self.slack_str["balance"]["btcValue"].format(round(total_balance, 8))
        )

        self.send_slack(slack_message)
        return total_balance

    def send_buy_slack(self, coin_pair, rsi, day_volume):
        """
        Used to send a buy's Slack message

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param day_volume: Coin pair's current 24 hour volume
        :type day_volume: float
        """
        main_market, coin = coin_pair.split("-")
        slack_emoji = self.slack_str["buy"]["emoji"] * 8 + "\n"
        slack_message = slack_emoji + self.slack_str["buy"]["message"].format(coin_pair, ceil(rsi), floor(day_volume),
                                                                              main_market)
        self.send_slack(slack_message)

    def send_sell_slack(self, coin_pair, rsi, profit_margin):
        """
        Used to send a sale's Slack message

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param profit_margin: Profit made on the trade
        :type profit_margin: float
        """
        emoji_type = "profit_emoji"
        if profit_margin <= 0:
            emoji_type = "loss_emoji"

        slack_emoji = self.slack_str["sell"][emoji_type] * 8 + "\n"
        slack_message = slack_emoji + self.slack_str["sell"]["message"].format(coin_pair, floor(rsi),
                                                                               round(profit_margin, 2))
        self.send_slack(slack_message)

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
            coin_pair, ceil(rsi), floor(day_volume), main_market, current_buy_price, self.get_bittrex_URL(coin_pair)
        )
        cprint(message, "blue", attrs=["bold"])

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
        message = self.console_str["sell"]["message"].format(
            coin_pair, floor(rsi), round(profit_margin, 2), current_sell_price, self.get_bittrex_URL(coin_pair)
        )
        color = "green"
        if profit_margin <= 0:
            color = "red"
        cprint(message, color, attrs=["bold"])

    def print_pause(self, coin_pair, data, pause_time, pause_type):
        """
        Used to print coin pause info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param data: Relevant pause values
        :type data: list
        :param pause_time: The amount of minutes to tracking will be paused on the coin pair
        :type pause_time: float
        :param pause_type: Type of pause (one of: 'buy', 'sell')
        :type pause_type: str
        """
        if pause_type == "buy":
            main_market, coin = coin_pair.split("-")
            data[0] = floor(data[0])
            data[1] = floor(data[1])
            print_str = self.console_str[pause_type]["pause"].format(
                coin_pair, data[0], data[1], main_market, round(pause_time)
            )
            cprint(print_str, "yellow")
        elif pause_type == "sell":
            data[0] = round(data[0], 2)
            data[1] = floor(data[1])
            print_str = self.console_str[pause_type]["pause"].format(coin_pair, data[0], data[1], round(pause_time))
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
            coin_pair, ceil(rsi), floor(day_volume), main_market, current_buy_price, self.get_bittrex_URL(coin_pair)
        )
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
        print_str = "No " + self.console_str["sell"]["message"].format(
            coin_pair, floor(rsi), round(profit_margin, 2), current_sell_price, self.get_bittrex_URL(coin_pair)
        )
        if print_str != self.console_str["sell"]["previousMessage"]:
            color = "magenta"
            if profit_margin <= 0:
                color = "red"
            self.console_str["sell"]["previousMessage"] = print_str
            cprint(print_str, color)

    def print_resume_pause(self, data, pause_type):
        """
        Used to print coin pause resume info to the console

        :param data: Relevant resume value
        :type data: float
        :param pause_type: Type of pause (one of: 'buy', 'sell')
        :type pause_type: str
        """
        print_str = self.console_str[pause_type]["resume"].format(data)
        cprint(print_str, "yellow", attrs=["bold"])

    def print_error(self, error_type, data=None, will_exit=False):
        """
        Prints the error type message to the console

        :param error_type: The error type
            (one of: 'market', 'coinMarket', 'sell', 'buy', 'order', 'connection', 'SSL', 'JSONDecode', 'keyError',
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
        elif error_type in ["sell", "buy"]:
            error_str = error_str.format(data[0], data[1])
        elif error_type == "order":
            error_str = error_str.format(data[0], data[1], data[2], self.get_bittrex_URL(data[2]))

        cprint("\n" + error_str + suffix, "red", attrs=["bold"])
        cprint(self.error_str["general"] + "\n", "grey", attrs=["bold"])
        self.play_beep()

        return error_str

    def get_bittrex_URL(self, coin_pair):
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
