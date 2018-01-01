import logging
import datetime

from directory_utilities import validate_or_make_directory

date = "{:%Y-%m-%d}".format(datetime.datetime.now())
log_file_string = "../logs/{}.log".format(date)

validate_or_make_directory(log_file_string)

logging.basicConfig(filename=log_file_string, level=logging.WARNING, format="%(asctime)s - %(levelname)s: %(message)s",
                    datefmt="%Y/%m/%d %I:%M:%S %p")

logger = logging
