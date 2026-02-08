import logging
import sys
from pathlib import Path

def setup_logging():
    """
    Setup centralized logging configuration
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Console output
            logging.FileHandler('logs/app.log'),  # File output
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    
    return logger

# Create a default logger
logger = setup_logging()