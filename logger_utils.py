import logging
import os
import traceback
from datetime import datetime
# Globalny logger
logger = None

def setup_logger(log_file="app.log", console_level="INFO", file_level="DEBUG"):
    """Konfiguruje globalny logger z obsługą pliku i konsoli."""
    global logger
    
    # Usuń poprzednie handlery, jeśli istnieją
    if logger:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    
    # Utwórz logger
    logger = logging.getLogger("xmi_generator")
    logger.setLevel(logging.DEBUG)  # Najniższy poziom logowania
    
    # Formatowanie wiadomości
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    
    # Handler dla konsoli
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, console_level))
    console_handler.setFormatter(formatter)
    
    # Handler dla pliku
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, file_level))
    file_handler.setFormatter(formatter)
    
    # Dodaj handlery
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Funkcje pomocnicze do różnych poziomów logowania
def log_debug(message):
    """Loguje wiadomość na poziomie DEBUG."""
    global logger
    if logger:
        logger.debug(message)

def log_info(message):
    """Loguje wiadomość na poziomie INFO."""
    global logger
    if logger:
        logger.info(message)

def log_warning(message):
    """Loguje wiadomość na poziomie WARNING."""
    global logger
    if logger:
        logger.warning(message)

def log_error(message):
    """Loguje wiadomość na poziomie ERROR."""
    global logger
    if logger:
        logger.error(message)

def log_exception(e, message="Wystąpił wyjątek"):
    """Loguje wyjątek wraz z pełnym traceback."""
    global logger
    if logger:
        logger.error(f"{message}: {str(e)}")
        logger.error(traceback.format_exc())