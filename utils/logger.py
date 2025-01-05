import logging
import sys
import os

def setup_logger(name=__name__, level=logging.INFO, log_file='scraper.log'):
    """
    Sets up a logger with the specified name and level.

    Parameters:
        name (str): Name of the logger.
        level (int): Logging level.
        log_file (str): Path to the log file.

    Returns:
        logging.Logger: Configured logger.
    """
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set up a StreamHandler to output logs to the console
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Set up a FileHandler to output logs to a file (scraper.log)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Configure the logger with the specified name and level
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if the logger already has handlers
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(file_handler)

    return logger
