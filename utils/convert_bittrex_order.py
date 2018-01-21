from bittrex import Bittrex
from database import Database
from directory_utilities import get_json_from_file

# Add your order UUID here
order_uuid = ""

secrets_file_directory = "../database/secrets.json"
secrets = get_json_from_file(secrets_file_directory)

Bittrex = Bittrex(secrets)
Database = Database()

order = Bittrex.get_order(order_uuid)
my_order = Database.convert_bittrex_order_object(order["result"])

print(my_order)
