import smtplib
import winsound
from termcolor import cprint


class Messenger(object):
    """
    Used for handling messaging functionality
    """

    def __init__(self, secrets):
        self.from_address = secrets['gmail']['username']
        self.to_address_list = secrets['gmail']['address_list']
        self.login = secrets['gmail']['username']
        self.password = secrets['gmail']['password']
        self.smtp_server = 'smtp.gmail.com:587'

        self.header_str = '\nTracking {} Bittrex Markets\n'

        self.buy_str = 'Buy on {:<10}\t->\t\tRSI: {:>2}\t\t24 Hour Volume: {:>5} {}\t\t Buy Price: {:.8f}\t\tURL: {}'
        self.sell_str = 'Sell on {:<10}\t->\t\tRSI: {:>2}\t\tProfit Margin: {:>4} %\t\t Sell Price: {:.8f}\t\tURL: {}'

        self.previous_no_sell_str = ''

        self.error_str = {
            'connection': '\nUnable to connect to the internet. Please check your connection and try again.\n',
            'JSONDecode': '\nFailed to decode JSON.\n',
            'unknown': '\nAn unknown exception occurred.\n'
        }

    @staticmethod
    def generate_bittrex_URL(btc_coin_pair):
        """
        Generates the URL string for the coin pairs Bittrex page
        """

        return 'https://bittrex.com/Market/Index?MarketName={}'.format(btc_coin_pair)

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

        header = 'From: %s\n' % self.from_address
        header += 'To: %s\n' % ','.join(self.to_address_list)
        header += 'Subject: %s\n\n' % subject
        message = header + message

        server = smtplib.SMTP(self.smtp_server)
        server.starttls()
        server.login(self.login, self.password)
        errors = server.sendmail(self.from_address, self.to_address_list, message)
        server.quit()
        return errors

    def send_RSI_email(self, rsi, coin_pair, day_volume, recipient_name='Folks'):
        """
        Used to send a low RSI specific email from the account specified in the secrets.json file to the entire
        address list specified in the secrets.json file

        :param rsi: Low RSI
        :type rsi: float
        :param coin_pair: Coin pair the low RSI occurred on (ex: BTC-ETH)
        :type coin_pair: str
        :param day_volume: Coin pair's current 24 hour volume
        :type day_volume: float
        :param recipient_name: Name of the email's recipient (ex: John)
        :type recipient_name: str

        :return: Errors received from the smtp server (if any)
        :rtype : dict
        """

        subject = 'Crypto Bot: Low RSI on {} Market'.format(coin_pair)
        message = "Howdy {},\n\nI've detected a low RSI of {} on the {} market. " \
                  "The current 24 hour market volume is {}\n\nHere's a Bittrex URL: {}" \
                  "\n\nRegards,\nCrypto Bot".format(recipient_name, round(rsi, 2), coin_pair, day_volume,
                                                    self.generate_bittrex_URL(coin_pair))
        self.send_email(subject, message)

    def print_header(self, num_of_coin_pairs):
        """
        Used to print the console header

        :param num_of_coin_pairs: Amount of available Bittrex market pairs
        :type num_of_coin_pairs: int
        """
        cprint(self.header_str.format(num_of_coin_pairs), attrs=['bold', 'underline'])

    def print_buy(self, coin_pair, rsi, day_volume, current_buy_price):
        """
        Used to print a buy's info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param day_volume: Coin pair's current 24 hour volume
        :type day_volume: float
        :param current_buy_price: Market's current price
        :type current_buy_price: float
        """
        main_market, coin = coin_pair.split('-')
        cprint(self.buy_str.format(coin_pair, round(rsi), round(day_volume), main_market, current_buy_price,
                                   self.generate_bittrex_URL(coin_pair)), 'blue', attrs=['bold'])

    def print_sell(self, coin_pair, rsi, profit_margin, current_sell_price):
        """
        Used to print a sales's info to the console

        :param coin_pair: String literal for the market (ex: BTC-LTC)
        :type coin_pair: str
        :param rsi: The coin pair's RSI
        :type rsi: float
        :param profit_margin: Profit made on the trade
        :type profit_margin: float
        :param current_sell_price: Market's current price
        :type current_sell_price: float
        """
        cprint(self.sell_str.format(coin_pair, round(rsi), round(profit_margin, 2), current_sell_price,
                                    self.generate_bittrex_URL(coin_pair)), 'green', attrs=['bold'])

    def print_no_buy_string(self, coin_pair, rsi, day_volume, current_buy_price):
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
        main_market, coin = coin_pair.split('-')
        print_str = 'No ' + self.buy_str.format(coin_pair, round(rsi), round(day_volume), main_market,
                                                current_buy_price, self.generate_bittrex_URL(coin_pair))
        cprint(print_str, 'grey')

    def print_no_sell_string(self, coin_pair, rsi, profit_margin, current_sell_price):
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
        print_str = 'No ' + self.sell_str.format(coin_pair, round(rsi), round(profit_margin, 2), current_sell_price,
                                                 self.generate_bittrex_URL(coin_pair))
        if print_str != self.previous_no_sell_str:
            self.previous_no_sell_str = print_str
            cprint(print_str, 'red')

    def print_error_string(self, error_type):
        """
        Prints the error type message to the console

        :param error_type: The error type (one of: 'connection', 'JSONDecode', 'unknown')
        """
        cprint(self.error_str[error_type], 'red', attrs=['bold'])

    @staticmethod
    def play_beep(frequency=2000, duration=1000):
        """
        Used to play a beep sound

        :param frequency: The frequency of the beep
        :type frequency: int
        :param duration: The duration of the beep
        :type duration: int
        """
        winsound.Beep(frequency, duration)
