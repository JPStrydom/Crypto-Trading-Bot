# Crypto Trading Bot - Tracker Branch

![](https://static01.nyt.com/images/2015/03/08/sunday-review/08ROBOT/08ROBOT-master1050.gif)

## Introduction

This branch is a simplified version of the main [Crypto Trading Bot](https://github.com/JPStrydom/Crypto-Trading-Bot) 
project (the master branch of this repository). Unlike the main project, this tracker branch is only used to monitor over 
250 crypto currencies on Bittrex (i.e. only report on indicators). Users can configure their own custom monitoring parameters 
which will control when the bot issues a buy signal.

#### Features:
* Tracking for over 250 coins on Bittrex
* Automated monitoring based on user configurations
* Automated technical analysis (TA)
* Trade analysis and tracking
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
        }
    }
    ```
    1) To use the **Bittrex** functionality, you need to setup the following:
        * **`bittrex_key`** is your Bittrex API key you can get from [here](https://bittrex.com/Manage#sectionApi)
        * **`bittrex_secret`** is your Bittrex API secret key
        
        *NOTE: Only the `READ INFO` permissions need to be enabled on your API key in order for the monitoring 
        functionality to be available*

4) Add a `settings.json` file to the newly created `database` directory. If you run the project without adding this file, 
the program will create it for you and populate it with the template values. The contents of the file should mirror the 
following:
    ```json
    {
        "sound": false,
        "tradeParameters": {            
            "market": "MARKET",
            "tickerInterval": "TICKER_INTERVAL",
            "buy": {
                "rsiThreshold": 0,
                "24HourVolumeThreshold": 0,
                "minimumUnitPrice": 0
            },
            "sell": {
                "desiredProfitPercentage": 0
            }
        },
        "pauseParameters": {
            "buy": {
                "rsiThreshold": 0,
                "pauseTime": 0
            }
        }
    }
    ```
    1) To use the **Sound** functionality, you need to setup the following:
         * **`sound`** is a boolean that determines whether audio notifications should be played
         
        If you don't want to receive audio notifications, you can leave out the `sound` code or set it to `false`.
    
    2) To use the **Trade** functionality, you need to setup the following:
        * **`market`** is the exchange market you would like to monitor on (ex: "BTC", "USDT", "ETH", etc.). If it is 
        omitted, all markets are considered.
        * **`tickerInterval`** is the exchange ticker interval you want to use. It should be one of the following: `oneMin`,
        `fiveMin`, `thirtyMin`, `hour`, `week`, `day`, `month`
        * **`buy`**: 
            * `rsiThreshold` is the upper RSI buy threshold. An RSI lower than this will result in a buy signal
            * `24HourVolumeThreshold` is the lower 24 hour volume buy threshold. Coin pairs with a 24 hour volume lower than 
            this will not be considered for buying
            * `minimumUnitPrice` is the lower unit price buy threshold. Coin pairs with a unit price lower than this will not 
            be considered for buying
        * **`sell`**: 
            * `desiredProfitPercentage` is the percentage profit you would like to make on trades, the system will then 
            calculate at what price you need to sell in order to make said profit. This takes Bittrex's commission into 
            consideration
    
    3) To use the **Pause** functionality, you need to setup the following:
        * **`buy`**: 
            * `rsiThreshold` is the lower RSI pause threshold. An RSI higher than this will result in the coin pair not being 
            tracked for `pauseTime` minutes
            * `24HourVolumeThreshold` is the upper 24 hour volume pause threshold. Coin pairs with a 24 hour volume lower 
            than this will not be tracked for `pauseTime` minutes
            * `pauseTime` is the amount of minutes to pause coin pair tracking by


## How to run
Navigate to the `src` file directory in terminal, and run the command `python app.py` to start the trading bot.

*NOTE: I would highly recommend getting the python IDE **PyCharm** by JetBrains. Its a great development tool and makes 
running and debugging this project a breeze. A free community edition can be found 
[here](https://www.jetbrains.com/pycharm/download).*

## Monitoring
This system allows you to monitor and track crypto currency signals on Bittrex. It uses a local database strategy 
to ensure data is not lost.

To use this functionality, first set the desired monitoring parameters in the `settings.json` file. An example of reasonably 
successful monitoring parameters can be found below:
```json
{
    "sound": false,
    "tradeParameters": {
        "tickerInterval": "fiveMin",
        "buy": {
            "rsiThreshold": 20,
            "24HourVolumeThreshold": 25,
            "minimumUnitPrice": 0.00001
        }
    },
    "pauseParameters": {}
}
```

The `analyse_buys()` function will then apply the `buy_strategy(coin_pair)`  function to each valid coin pair on Bittrex. 
These functions will check each coin pair for buy signals by utilising the the following function:
```python
from directory_utilities import get_json_from_file

settings_file_directory = "../database/settings.json"
settings = get_json_from_file(settings_file_directory)

buy_trade_params = settings["tradeParameters"]["buy"]

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
```

See the source code for a more detailed description.

## Donations

If you found this project helpful and would like to support me, you can donate to one of the following crypto addresses:

* **BTC**: 1E3xMaoFfuk52HaCb7KRbHmezeUumcyRjy
* **ETH**: 0x2f647427313229E6AB320F826f759B9fCFd34658


## Liability
I am not your financial adviser, nor is this tool. Use this program cautiously as it will trade with your crypto-currencies. 
None of the contributors to this project are liable for any loses you may incur. Be wise and always do your own research.


![](https://cdn-images-1.medium.com/max/1600/1*SKlPuk4vscYs3bl1bFdT5g.gif)
