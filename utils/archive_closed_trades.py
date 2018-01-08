from pydash import py_

from directory_utilities import get_json_from_file, write_json_to_file

trades_file_directory = "../database/trades.json"
trades = get_json_from_file(trades_file_directory)

archived_trades_file_directory = "../database/archive/archived-trades.json"
archived_trades = get_json_from_file(archived_trades_file_directory, [])

new_archived_trades = py_.filter_(trades["trades"], lambda trade: "sell" in trade and trade not in archived_trades)
if len(new_archived_trades) > 0:
    archived_trades += new_archived_trades
    write_json_to_file(archived_trades_file_directory, archived_trades)
    print("Archived {} closed trades.".format(len(new_archived_trades)))
else:
    print("No closed trades to archive.")

num_of_initial_trades = len(trades["trades"])
trades["trades"] = py_.filter_(trades["trades"], lambda trade: "sell" not in trade)

if len(trades["trades"]) < num_of_initial_trades:
    write_json_to_file(trades_file_directory, trades)
    print("Removed {} closed trades from active trades.".format(num_of_initial_trades - len(trades["trades"])))
else:
    print("No closed trades to remove from active trades.")
