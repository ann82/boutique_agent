"""
Logging functionality for the Fashion Content Agent.
"""
import logging
import os
from typing import Any, Optional

def setup_logging(log_file: str = "logs/fashion_agent.log") -> None:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to the log file
    """
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(os.path.abspath(log_file))
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

def log_error(message: str, error: Optional[Exception] = None) -> None:
    """Log an error message."""
    logger = logging.getLogger()
    if error:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(message)

def log_success(message: str) -> None:
    """Log a success message."""
    logger = logging.getLogger()
    logger.info(message)

def log_batch_operation(operation: str, total: int, successful: Optional[int] = None, failed: Optional[int] = None) -> None:
    """Log a batch operation."""
    logger = logging.getLogger()
    if successful is not None and failed is not None:
        logger.info(f"Batch {operation} completed: {successful}/{total} successful, {failed} failed")
    else:
        logger.info(f"Batch {operation}: Processing {total} items") 