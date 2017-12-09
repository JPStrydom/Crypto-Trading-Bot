import logging

logging.basicConfig(filename='logs/error.log', level=logging.WARNING, format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y/%m/%d %I:%M:%S %p')

logger = logging