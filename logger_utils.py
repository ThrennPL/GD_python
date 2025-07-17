import logging
from logging.handlers import TimedRotatingFileHandler
import os

LOG_FILENAME = "app.log"

def setup_logger(log_filename="app.log"):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler = TimedRotatingFileHandler(
        log_filename,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        utc=False
    )
    handler.suffix = "%Y-%m-%d"
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

def log_exception(message):
    logging.exception(message)

def log_debug(message):
    logging.debug(message)

def log_warning(message):
    logging.warning(message)