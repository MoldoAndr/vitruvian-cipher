"""Logging configuration with structured logging support."""

import logging
import sys
from typing import Any

from app.config import get_settings, LogLevel


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Configure root logger
    logging.basicConfig(
        level=settings.log_level.value,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(settings.logs_dir / "app.log"),
        ],
    )

    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("dramatiq").setLevel(logging.INFO)
    logging.getLogger("pika").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class ContextLogger:
    """Logger with automatic context injection."""

    def __init__(self, name: str, **context: Any):
        """Initialize context logger.

        Args:
            name: Logger name
            **context: Default context fields
        """
        self.logger = get_logger(name)
        self.context = context

    def _format_message(self, message: str, **extra_context: Any) -> str:
        """Format message with context.

        Args:
            message: Log message
            **extra_context: Additional context fields

        Returns:
            Formatted message
        """
        context = {**self.context, **extra_context}
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"{message} | {context_str}"
        return message

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.logger.debug(self._format_message(message, **kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(self._format_message(message, **kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self.logger.critical(self._format_message(message, **kwargs))
