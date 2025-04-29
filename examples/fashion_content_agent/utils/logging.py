"""
Logging functionality for the Fashion Content Agent.
"""
import logging
import os
from typing import Any

def setup_logging(log_file: str = "logs/fashion_agent.log") -> None:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to the log file (default: logs/fashion_agent.log)
    """
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure basic logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get the root logger and set its level
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

def log_error(message: str) -> None:
    """Log an error message."""
    logger = logging.getLogger()
    logger.error(message)

def log_success(message: str) -> None:
    """Log a success message."""
    logger = logging.getLogger()
    logger.info(message)

def log_batch_operation(operation: str, total: int, successful: int, failed: int) -> None:
    """Log a batch operation."""
    logger = logging.getLogger()
    message = f"Batch {operation} completed: {successful}/{total} successful, {failed} failed"
    logger.info(message) 