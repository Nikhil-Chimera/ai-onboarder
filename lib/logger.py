"""
Logging utilities for AI-Onboarder
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        record.name = f"{self.BOLD}{record.name}{self.RESET}"
        return super().format(record)

def create_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create a configured logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Format: [TIME] LEVEL - NAME - MESSAGE
    formatter = ColoredFormatter(
        fmt='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger

# Create module-level loggers
class Loggers:
    """Container for all application loggers"""
    
    def __init__(self):
        self.ingest = create_logger('INGEST')
        self.docs = create_logger('DOCS')
        self.chat = create_logger('CHAT')
        self.git = create_logger('GIT')
        self.agents = create_logger('AGENTS')
        self.video = create_logger('VIDEO')
        self.db = create_logger('DB')
    
    def separator(self, logger_name: str, message: str = ''):
        """Print a separator line"""
        logger = getattr(self, logger_name.lower(), self.ingest)
        logger.info('=' * 80)
        if message:
            logger.info(message)
            logger.info('=' * 80)
    
    def step(self, logger_name: str, message: str):
        """Log a major step"""
        logger = getattr(self, logger_name.lower(), self.ingest)
        logger.info(f"▶ {message}")

loggers = Loggers()

def log_dict(logger: logging.Logger, data: Dict[str, Any], prefix: str = ''):
    """Log a dictionary with nice formatting"""
    for key, value in data.items():
        logger.info(f"{prefix}{key}: {value}")
