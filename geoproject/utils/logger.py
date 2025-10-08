import logging
import sys

def setup_logger():
    """Sets up the main application logger."""

    logger = logging.getLogger("TerrainAnnotator")
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers if called more than once
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a handler to print logs to the console
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger

# Create a default logger instance for the application to import
log = setup_logger()