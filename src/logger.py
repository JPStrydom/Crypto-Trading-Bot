import logging

from src.directory_utilities import validate_or_make_directory

log_file_string = 'logs/error.log'

validate_or_make_directory(log_file_string)

logging.basicConfig(filename='logs/error.log', level=logging.WARNING, format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y/%m/%d %I:%M:%S %p')

logger = logging
