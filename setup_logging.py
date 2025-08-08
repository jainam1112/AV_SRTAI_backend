#!/usr/bin/env python3
"""
Configure logging for bio extraction debugging
"""

import logging
import sys
import os
from datetime import datetime

def setup_bio_extraction_logging(log_level=logging.INFO):
    """
    Setup comprehensive logging for bio extraction debugging
    """
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"bio_extraction_{timestamp}.log")
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("bio_extraction").setLevel(log_level)
    logging.getLogger("openai").setLevel(logging.WARNING)  # Reduce OpenAI noise
    logging.getLogger("httpx").setLevel(logging.WARNING)   # Reduce HTTP noise
    
    logger = logging.getLogger(__name__)
    logger.info(f"Bio extraction logging initialized. Log file: {log_file}")
    
    return log_file

if __name__ == "__main__":
    # Test logging setup
    log_file = setup_bio_extraction_logging(logging.DEBUG)
    
    logger = logging.getLogger("bio_extraction")
    logger.info("Testing bio extraction logging")
    logger.debug("Debug message test")
    logger.warning("Warning message test")
    logger.error("Error message test")
    
    print(f"Logging test complete. Check log file: {log_file}")
