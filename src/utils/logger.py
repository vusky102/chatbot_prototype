import logging
import sys
from pathlib import Path

_logger_initialized = False

def get_logger(name: str = "backend") -> logging.Logger:
    global _logger_initialized
    
    logger = logging.getLogger(name)
    
    if not _logger_initialized:
        logger.setLevel(logging.DEBUG)

        log_file = Path("backend.log")

        # Create handlers
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Create formatters and add it to handlers
        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(log_format)
        console_handler.setFormatter(log_format)

        # Add handlers to the root logger to capture all our custom loggers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        # Avoid adding console_handler to root if Streamlit already handles console output,
        # but since we want formatted output, we can add it to our specific logger instead of root.
        
        logger.addHandler(console_handler)
        
        _logger_initialized = True

    return logger
