"""Logging configuration and utilities."""

import logging
import sys
from typing import Optional
from pathlib import Path

import structlog


def setup_logger(name: str, level: str = "INFO") -> structlog.stdlib.BoundLogger:
    """Set up structured logging."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger(name)


def get_logger(name: str, level: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    if level:
        logging.getLogger(name).setLevel(getattr(logging, level.upper()))
    
    return structlog.get_logger(name)


def configure_file_logging(log_file: str, level: str = "INFO") -> None:
    """Configure logging to file."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, level.upper()))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add file handler to root logger
    logging.getLogger().addHandler(file_handler)