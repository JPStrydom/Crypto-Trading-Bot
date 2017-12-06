import logging

logging.basicConfig(filename='error.log', level=logging.WARNING, format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y/%m/%d %I:%M:%S %p')


def get_logger():
    return logging
