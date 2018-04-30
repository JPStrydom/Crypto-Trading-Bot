# Crypto Trading Bot

![](https://static01.nyt.com/images/2015/03/08/sunday-review/08ROBOT/08ROBOT-master1050.gif)

## Introduction

Use Crypto Trading Bot to autonomously trade and monitor over 250 crypto currencies on Bittrex. Users can configure their
own custom trading parameters which will control when the bot buys and sells.

#### Features:
* Tracking for over 250 coins on Bittrex
* Automated trading based on user configurations
* Automated technical analysis (TA)
* Trade analysis and tracking
* Email alerts for trades and signals
* Slack notifications for trades and signals
* Informative console outputs for user monitoring
* Logging to track and document errors on the Bittrex API
* Well documented script

Users can add their own algorithms and trading strategies based on technical analysis signals such as RSI, 24 Hour Volume,
and Unit Price.

#### Coming Soon:
* Bollinger Bands
* Moving Average

#### Shoutouts:
* Bittrex for an awesome API
* Eric Somdahl for writing the Python wrapper for the Bittrex API
* Abenezer Mamo for creating the [Crypto Signals](https://github.com/AbenezerMamo/crypto-signal) project which formed the
foundation for this project

## How to setup
1) This project requires Python 3.X.X, which can be be found [here](https://www.python.org/ftp/python/3.6.3/python-3.6.3.exe).

2) To install the dependencies for this project, run one of the following commands:
    * Windows: `pip3 install -r requirements.txt`
    
        *NOTE: If you receive a `'pip3' is not recognized as an internal or external command` error, you 
        need to add `pip3` to your environmental `path` variable.*
        
    * Unix: `sudo pip3 install -r requirements.txt` 

3) Add a directory named `database` to the root directory of your project and add a `secrets.json` file to it. If you 
run the project without adding this file, the program will create it for you and populate it with the template values.
The contents of the file should mirror the following:
    ```json
    {
        "bittrex": {
            "bittrexKey": "BITTREX_API_KEY",
            "bittrexSecret": "BITTREX_SECRET"
        },
        "gmail": {
            "recipientName": "Folks",
            "addressList": [
                "EXAMPLE_RECIPIENT_1@GMAIL.COM",
                "EXAMPLE_RECIPIENT_2@GMAIL.COM",
                "ETC..."
            ],
            "username": "EXAMPLE_EMAIL@GMAIL.COM",
            "password": "GMAIL_PASSWORD"
        },
        "slack": {
            "channel": "SLACK_CHANNEL",
            "token": "SLACK_TOKEN"
        }
    }
    ```
    1) To use the **Bittrex** functionality, you need to setup the following:
        * **`bittrex_key`** is your Bittrex API key you can get from [here](https://bittrex.com/Manage#sectionApi)
        * **`bittrex_secret`** is your Bittrex API secret key
        
        *NOTE: The `READ INFO`, `TRADE LIMIT`, and `TRADE MARKET` permissions need to be enabled on your API key in
        order for the trade functionality to be available*
        
    2) To use the **Gmail** functionality, you need to setup the following:
        * **`username`** is your Gmail account's username (*usually your account's email address*)
        * **`password`** is your Gmail account's password
        * **`address_list`** is the list of recipients you'd like to send emails to
         
        If you don't want to use the email notifications, you can leave out the `gmail` code.
    
    3) To use the **Slack** functionality, you need to setup the following:
        * **`channel`** is your Slack groups's channel (*usually starts with a '#' character*)
        * **`token`** is your Slack account's authentication token (*you need to create a Slack app on the Slack API website 
        for your group - from which you can generate this authentication token*)
         
        If you don't want to use the Slack notifications, you can leave out the `slack` code.

4) Add a `settings.json` file to the newly created `database` directory. If you run the project without adding this file, 
the program will create it for you and populate it with the template values. The contents of the file should mirror the 
following:
    ```json
    {
        "sound": false,
        "tradeParameters": {
            "tickerInterval": "TICKER_INTERVAL",
            "buy": {
                "btcAmount": 0,
                "rsiThreshold": 0,
                "24HourVolumeThreshold": 0,
                "minimumUnitPrice": 0,
                "maxOpenTrades": 0
            },
            "sell": {
                "lossMarginThreshold": 0,
                "rsiThreshold": 0,
                "minProfitMarginThreshold": 0,
                "profitMarginThreshold": 0
            }
        },
        "pauseParameters": {
            "buy": {
                "rsiThreshold": 0,
                "pauseTime": 0
            },
            "sell": {
                "profitMarginThreshold": 0,
                "pauseTime": 0
            },
            "balance": {
                "pauseTime": 0
           }
        }
    }
    ```
    1) To use the **Sound** functionality, you need to setup the following:
         * **`sound`** is a boolean that determines whether audio notifications should be played
         
        If you don't want to receive audio notifications, you can leave out the `sound` code or set it to `false`.
    
    2) To use the **Trade** functionality, you need to setup the following:
        * **`tickerInterval`** is the exchange ticker interval you want to use. It should be one of the following: `oneMin`,
        `fiveMin`, `thirtyMin`, `hour`, `week`, `day`, `month`
        * **`buy`**: 
            * `btcAmount` is the amount of BTC you want the bot to spend per buy
            * `rsiThreshold` is the upper RSI buy threshold. An RSI lower than this will result in a buy signal
            * `24HourVolumeThreshold` is the lower 24 hour volume buy threshold. Coin pairs with a 24 hour volume lower than 
            this will not be considered for buying
            * `minimumUnitPrice` is the lower unit price buy threshold. Coin pairs with a unit price lower than this will not 
            be considered for buying 
            * `maxOpenTrades` is the maximum amount of open trades the bot is allowed to have at one time 
        * **`sell`**: 
            * `lossMarginThreshold` is the lower loss margin threshold. Coin pairs with a profit margin lower than this 
            will be sold if their RSI is above the `sell` `rsiThreshold`. If this value is omitted or set to zero (`0`), 
            this parameter will be ignored and coin pairs will not be sold at a loss
            * `rsiThreshold` is the lower RSI sell threshold. An RSI higher than this will result in a sell signal
            * `minProfitMarginThreshold` is the upper minimum profit margin sell threshold. Coin pairs with a profit margin 
            lower than this will not be sold
            * `profitMarginThreshold` is the upper profit margin sell threshold. Coin pairs with a profit margin higher than 
            this will be sold regardless of its RSI
    
    3) To use the **Pause** functionality, you need to setup the following:
        * **`buy`**: 
            * `rsiThreshold` is the lower RSI pause threshold. An RSI higher than this will result in the coin pair not being 
            tracked for `pauseTime` minutes
            * `pauseTime` is the amount of minutes to pause coin pair tracking by
        * **`sell`**: 
            * `profitMarginThreshold` is the upper profit margin pause threshold. A profit margin lower than this will result 
            in the coin pair not being tracked for `pauseTime` minutes
            * `pauseTime` is the amount of minutes to pause coin pair tracking by
            If you prefer to sell at a small loss rather than holding onto (pausing) sell coin pairs, the `lossMarginThreshold` 
            **trade** parameter should be set appropriately and then the `sell` **pause** parameter may be omitted.
        * **`balance`**: 
            * `pauseTime` is the amount of minutes you would like to wait in between balance notification Slack messages 
            (i.e. every *x* minutes, you will receive a Slack message containing a breakdown of your exchange balance
            and the percentage change since your last balance notification message). 


## How to run
Navigate to the `src` file directory in terminal, and run the command `python app.py` to start the trading bot.

*NOTE: I would highly recommend getting the python IDE **PyCharm** by JetBrains. Its a great development tool and makes 
running and debugging this project a breeze. A free community edition can be found 
[here](https://www.jetbrains.com/pycharm/download).*

## Trading
This system allows you to autonomously make and track crypto currency trades on Bittrex. It uses a local database strategy 
to ensure data is not lost.

To use this functionality, first set the desired trade parameters in the `settings.json` file. An example of reasonably 
successful trading parameters can be found below:
```json
{
    "sound": false,
    "tradeParameters": {
        "tickerInterval": "fiveMin",
        "buy": {
            "btcAmount": 0.001,
            "rsiThreshold": 20,
            "24HourVolumeThreshold": 25,
            "minimumUnitPrice": 0.00001,
            "maxOpenTrades": 3
        },
        "sell": {
            "lossMarginThreshold": -2.5,
            "rsiThreshold": 50,
            "minProfitMarginThreshold": 0.5,
            "profitMarginThreshold": 2.5
        }
    },
    "pauseParameters": {}
}
```

The `analyse_buys()` and `analyse_sells()` functions will then apply the `buy_strategy(coin_pair)` and 
`sell_strategy(coin_pair)` functions to each valid coin pair on Bittrex. These functions will check each coin pair for 
buy/sell signals by utilising the the following two functions:
```python
from directory_utilities import get_json_from_file

settings_file_directory = "../database/settings.json"
settings = get_json_from_file(settings_file_directory)

buy_trade_params = settings["tradeParameters"]["buy"]
sell_trade_params = settings["tradeParameters"]["sell"]

def check_buy_parameters(rsi, day_volume, current_buy_price):
    """
    Used to check if the buy conditions have been met

    :param rsi: The coin pair's current RSI
    :type rsi: float
    :param day_volume: The coin pair's current 24 hour volume
    :type day_volume: float
    :param current_buy_price: The coin pair's current price
    :type current_buy_price: float

    :return: Boolean indicating if the buy conditions have been met
    :rtype: bool
    """
    rsi_check = rsi is not None and rsi <= buy_trade_params["buy"]["rsiThreshold"]
    day_volume_check = day_volume >= buy_trade_params["buy"]["24HourVolumeThreshold"]
    current_buy_price_check = current_buy_price >= buy_trade_params["buy"]["minimumUnitPrice"]
    
    return rsi_check and day_volume_check and current_buy_price_check


def check_sell_parameters(rsi, profit_margin):
    """
    Used to check if the sell conditions have been met

    :param rsi: The coin pair's current RSI
    :type rsi: float
    :param profit_margin: The coin pair's current profit margin
    :type profit_margin: float

    :return: Boolean indicating if the sell conditions have been met
    :rtype: bool
    """
    rsi_check = rsi is not None and rsi >= sell_trade_params["sell"]["rsiThreshold"]
    lower_profit_check = profit_margin >= sell_trade_params["sell"]["minProfitMarginThreshold"]        
    upper_profit_check = profit_margin >= sell_trade_params["sell"]["profitMarginThreshold"]
    loss_check = (sell_trade_params["lossMarginThreshold"] is not None and
                  0 > sell_trade_params["lossMarginThreshold"] >= profit_margin)

    return (rsi_check and lower_profit_check) or upper_profit_check or loss_check
```

See the source code for a more detailed description.

## Donations

If you found this project helpful and would like to support me, you can donate to one of the following crypto addresses:

* **BTC**: 1E3xMaoFfuk52HaCb7KRbHmezeUumcyRjy
* **ETH**: 0x6D5f8775Dc844D8B1E6f2359abF9939E75A7A225


## Liability
I am not your financial adviser, nor is this tool. Use this program cautiously as it will trade with your crypto-currencies. 
None of the contributors to this project are liable for any loses you may incur. Be wise and always do your own research.


![](https://cdn-images-1.medium.com/max/1600/1*SKlPuk4vscYs3bl1bFdT5g.gif)
