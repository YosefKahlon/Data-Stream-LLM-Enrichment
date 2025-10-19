
import logging
from typing import Union
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

def setup_logger(name: str, level: Union[str, LogLevel] = "INFO") -> logging.Logger:
    """Setup logger with consistent format"""
    logger = logging.getLogger(name)
    
    # Accept LogLevel enum or string values (case-insensitive)
    if isinstance(level, LogLevel):
        level_name = level.value
    else:
        level_name = str(level).upper()

    numeric_level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger