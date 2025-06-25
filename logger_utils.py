import logging
from logging.handlers import TimedRotatingFileHandler
import os

LOG_FILENAME = "app.log"

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Usuń istniejące handlery, jeśli są (by nie dublować wpisów)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Handler rotujący plik logu codziennie o północy, z datą w nazwie archiwum
    handler = TimedRotatingFileHandler(
        LOG_FILENAME,
        when="midnight",
        interval=1,
        backupCount=30,  # ile archiwalnych plików trzymać
        encoding="utf-8",
        utc=False
    )
    handler.suffix = "%Y-%m-%d"  # archiwalne pliki: app.log.2025-06-25
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