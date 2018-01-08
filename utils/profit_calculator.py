from pydash import py_

from directory_utilities import get_json_from_file

archived_trades_file_directory = "../database/archive/archived-trades.json"
archived_trades = get_json_from_file(archived_trades_file_directory, [])

completed_archived_trades = py_.filter_(archived_trades, lambda trade: trade["sell"]["dateClosed"] is not None)

profit_btc = round(
    py_.sum_by(
        completed_archived_trades,
        lambda trade: (
            trade["sell"]["price"] -
            trade["buy"]["price"] -
            trade["buy"]["commissionPaid"] -
            trade["sell"]["commissionPaid"]
        )
    ),
    8
)
avg_profit_btc = round(profit_btc / len(completed_archived_trades), 8)

total_buy_btc = py_.sum_by(
    completed_archived_trades,
    lambda trade: (
        trade["buy"]["price"] +
        trade["buy"]["commissionPaid"] +
        trade["sell"]["commissionPaid"]
    )

)
total_sell_btc = py_.sum_by(
    completed_archived_trades,
    lambda trade: trade["sell"]["price"]
)
profit_margin = round(100 * total_sell_btc / total_buy_btc - 100, 2)

print("Total completed trades: {}\n".format(len(completed_archived_trades)))

print("Total profit: {} BTC".format(profit_btc))
print("Average profit: {} BTC per trade\n".format(avg_profit_btc))

print("Total profit margin: {}%".format(profit_margin))
