"""Advanced logging configuration with structured logging."""

import logging
import logging.handlers
import structlog
from pathlib import Path
from typing import Dict, Any


def setup_advanced_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    app_name: str = "genesis",
    enable_json: bool = True
) -> None:
    """Set up advanced logging with structured output and rotation."""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if enable_json else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=getattr(logging, log_level.upper()),
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{app_name}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{app_name}_errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    
    # Add handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_function_call(func_name: str, args: Dict[str, Any] = None, 
                     result: Any = None, duration: float = None) -> None:
    """Log function calls with parameters and results."""
    logger = get_logger("function_calls")
    
    log_data = {
        "function": func_name,
        "args": args or {},
    }
    
    if result is not None:
        log_data["result_type"] = type(result).__name__
        
    if duration is not None:
        log_data["duration_ms"] = round(duration * 1000, 2)
    
    logger.info("Function called", **log_data)


def log_api_request(method: str, path: str, status_code: int, 
                   duration: float, user_id: str = None) -> None:
    """Log API requests with timing and user information."""
    logger = get_logger("api_requests")
    
    logger.info(
        "API request completed",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration * 1000, 2),
        user_id=user_id
    )


def log_error_with_context(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log errors with additional context information."""
    logger = get_logger("errors")
    
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True
    )