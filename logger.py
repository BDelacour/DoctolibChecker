import logging


def init_logger(name):
    logger = logging.getLogger(name=name)

    logger.setLevel('INFO')

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
