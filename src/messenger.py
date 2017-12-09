import smtplib


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

    def generate_bittrex_URL(self, btc_coin_pair):
        """
        Generates the URL string for the coin pairs Bittrex page
        """

        return 'https://bittrex.com/Market/Index?MarketName={}'.format(self, btc_coin_pair)

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

    def send_RSI_email(self, rsi, coin_pair, current_price, recipient_name='Folks'):
        """
        Used to send a low RSI specific email from the account specified in the secrets.json file to the entire
        address list specified in the secrets.json file

        :param rsi: Low RSI
        :type rsi: float
        :param coin_pair: Coin pair the low RSI occurred on (ex: BTC-ETH)
        :type coin_pair: str
        :param current_price: Coin pair's current price
        :type current_price: float
        :param recipient_name: Name of the email's recipient (ex: John)
        :type recipient_name: str

        :return: Errors received from the smtp server (if any)
        :rtype : dict
        """

        main_market, coin = coin_pair.split('-')

        subject = 'Crypto Bot: Low RSI on {} Market'.format(coin_pair)
        message = "Howdy {},\n\nI've detected a low RSI of {} on the {} market. " \
                  "The current market price is {:.8f} {} per {}\n\nHere's a Bittrex URL: {}" \
                  "\n\nRegards,\nCrypto Bot".format(recipient_name, round(rsi, 2), coin_pair, current_price,
                                                    main_market, coin, self.generate_bittrex_URL(coin_pair))
        self.send_email(subject, message)
