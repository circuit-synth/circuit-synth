"""
Logging configuration module for Circuit Synth.
Provides simple, non-Docker configuration with environment variable support.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional


class LoggingConfig:
    """Configuration class for Circuit Synth logging system."""

    # Default configuration values
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LOG_DIR = "logs"
    DEFAULT_MAX_LOG_SIZE = 100 * 1024 * 1024  # 100MB
    DEFAULT_BACKUP_COUNT = 10
    DEFAULT_LOG_FORMAT = "%(asctime)s.%(msecs)03d %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

    def __init__(self):
        """Initialize logging configuration from environment variables."""
        self.log_level = self._get_log_level()
        self.log_dir = Path(os.getenv("CIRCUIT_SYNTH_LOG_DIR", self.DEFAULT_LOG_DIR))
        self.max_log_size = int(
            os.getenv("CIRCUIT_SYNTH_MAX_LOG_SIZE", str(self.DEFAULT_MAX_LOG_SIZE))
        )
        self.backup_count = int(
            os.getenv("CIRCUIT_SYNTH_BACKUP_COUNT", str(self.DEFAULT_BACKUP_COUNT))
        )
        self.log_format = os.getenv("CIRCUIT_SYNTH_LOG_FORMAT", self.DEFAULT_LOG_FORMAT)
        self.date_format = os.getenv(
            "CIRCUIT_SYNTH_DATE_FORMAT", self.DEFAULT_DATE_FORMAT
        )

        # Create base log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_level(self) -> str:
        """Get log level from environment variable with validation."""
        level = os.getenv("LOG_LEVEL", self.DEFAULT_LOG_LEVEL).upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if level not in valid_levels:
            print(
                f"Warning: Invalid LOG_LEVEL '{level}'. Using default '{self.DEFAULT_LOG_LEVEL}'"
            )
            return self.DEFAULT_LOG_LEVEL

        return level

    def get_numeric_log_level(self) -> int:
        """Convert string log level to numeric value."""
        return getattr(logging, self.log_level)

    def setup_directory_structure(self):
        """Create the complete directory structure for logging."""
        directories = [
            self.log_dir / "users",
            self.log_dir / "system",
            self.log_dir / "performance",
            self.log_dir / "master",
            self.log_dir / "archive",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_formatter(self) -> logging.Formatter:
        """Get a configured formatter instance."""
        return logging.Formatter(self.log_format, datefmt=self.date_format)

    def get_file_handler(
        self, log_path: Path, level: Optional[int] = None
    ) -> logging.FileHandler:
        """
        Create a configured file handler.

        Args:
            log_path: Path to the log file
            level: Optional log level for this handler

        Returns:
            Configured FileHandler instance
        """
        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setLevel(level or self.get_numeric_log_level())
        handler.setFormatter(self.get_formatter())
        return handler

    def get_rotating_file_handler(self, log_path: Path, level: Optional[int] = None):
        """
        Create a rotating file handler for log rotation.

        Args:
            log_path: Path to the log file
            level: Optional log level for this handler

        Returns:
            Configured RotatingFileHandler instance
        """
        from logging.handlers import RotatingFileHandler

        handler = RotatingFileHandler(
            log_path,
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        handler.setLevel(level or self.get_numeric_log_level())
        handler.setFormatter(self.get_formatter())
        return handler

    def configure_root_logger(self):
        """Configure the root logger with basic settings."""
        logging.basicConfig(
            level=self.get_numeric_log_level(),
            format=self.log_format,
            datefmt=self.date_format,
        )

    @property
    def log_paths(self) -> Dict[str, Path]:
        """Get standard log paths for different components."""
        return {
            "users": self.log_dir / "users",
            "system": self.log_dir / "system",
            "performance": self.log_dir / "performance",
            "master": self.log_dir / "master",
            "archive": self.log_dir / "archive",
        }


# Global configuration instance
_config = None


def get_config() -> LoggingConfig:
    """Get or create the global logging configuration instance."""
    global _config
    if _config is None:
        _config = LoggingConfig()
        _config.setup_directory_structure()
    return _config


def setup_logging():
    """
    Initialize the logging system with default configuration.
    This should be called once at application startup.
    """
    config = get_config()
    config.configure_root_logger()

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    return config
