import logging
from pathlib import Path

from config.config import Config

# Map log level strings to logging constants
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def setup_logger(
    name="app_logger",
    log_file=Config.LOG_FILE,
    log_level_str="ERROR",
):
    # Create a Path object for the log file
    log_path = Path(log_file)

    # Ensure the log directory exists using pathlib
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Map string log level to logging constant
    log_level = LOG_LEVELS.get(
        log_level_str.upper(), logging.INFO
    )  # Default to INFO if invalid

    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Create a formatter that formats the log output
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s -  %(levelname)s -  %(funcName)s - %(message)s"
    )

    # Create a file handler that logs to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Create a stream handler to log to the console (stdout)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
