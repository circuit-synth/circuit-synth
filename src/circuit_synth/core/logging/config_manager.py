"""
Configuration Manager for Unified Logging System
===============================================

Centralized configuration management for the unified logging system with support for:
- YAML-based configuration files
- Environment variable overrides
- Development and production profiles
- Dynamic configuration updates
- Validation and defaults
"""

import os
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


@dataclass
class SinkConfig:
    """Configuration for a logging sink."""

    enabled: bool = True
    path: Optional[str] = None
    level: str = "DEBUG"
    format: Optional[str] = None
    rotation: Optional[str] = None
    retention: Optional[str] = None
    compression: Optional[str] = None
    filter_type: Optional[str] = None
    enqueue: bool = True


@dataclass
class ComponentConfig:
    """Configuration for a specific component."""

    level: str = "INFO"
    include_prompt_content: bool = True
    max_prompt_length: int = 1000
    forward_to_python: bool = True
    enable_memory_tracking: bool = False
    enable_cpu_tracking: bool = False


@dataclass
class MultiUserConfig:
    """Configuration for multi-user support."""

    enable_user_isolation: bool = True
    session_timeout_hours: int = 24
    max_sessions_per_user: int = 10
    session_cleanup_interval_minutes: int = 60


@dataclass
class PerformanceConfig:
    """Configuration for performance settings."""

    async_logging: bool = True
    buffer_size: int = 1000
    flush_interval_seconds: int = 5
    worker_threads: int = 2


class LoggingConfig:
    """Centralized logging configuration management."""

    def __init__(
        self, config_path: str = "src/circuit_synth/core/logging/logging_config.yaml"
    ):
        self.config_path = Path(config_path)
        self.config = {}
        self._lock = threading.RLock()
        self._load_config()
        self._apply_environment_overrides()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        with self._lock:
            if not self.config_path.exists():
                self.config = self._get_default_config()
                self._save_default_config()
                return

            try:
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                self.config = self._get_default_config()

    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides."""
        with self._lock:
            env = os.getenv("CIRCUIT_SYNTH_ENV", "development")

            # Apply environment-specific configuration
            if env in self.config.get("environments", {}):
                env_config = self.config["environments"][env]
                self._deep_merge(self.config, env_config)

            # Direct environment variable overrides
            env_overrides = {
                "CIRCUIT_SYNTH_LOG_LEVEL": "logging.level",
                "CIRCUIT_SYNTH_LOG_CONSOLE": "logging.sinks.console.enabled",
                "CIRCUIT_SYNTH_LOG_ASYNC": "logging.performance.async_logging",
                "CIRCUIT_SYNTH_LOG_DIR": "logging.log_directory",
            }

            for env_var, config_path in env_overrides.items():
                env_value = os.getenv(env_var)
                if env_value is not None:
                    # Convert string values to appropriate types
                    if env_value.lower() in ("true", "false"):
                        env_value = env_value.lower() == "true"
                    elif env_value.isdigit():
                        env_value = int(env_value)

                    self._set_nested_value(config_path, env_value)

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Deep merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _set_nested_value(self, path: str, value: Any) -> None:
        """Set a nested configuration value using dot notation."""
        keys = path.split(".")
        current = self.config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path."""
        with self._lock:
            keys = path.split(".")
            value = self.config

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

    def set(self, path: str, value: Any) -> None:
        """Set configuration value by dot-separated path."""
        with self._lock:
            self._set_nested_value(path, value)

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()
        self._apply_environment_overrides()

    def _save_default_config(self) -> None:
        """Save default configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save default config: {e}")

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "logging": {
                "level": "INFO",
                "log_directory": "logs",
                "format": {
                    "console": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[component]: <10}</cyan> | <blue>{extra[user]: <12}</blue> | <yellow>{extra[session]: <8}</yellow> | {message}",
                    "file": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[component]: <10} | {extra[user]: <12} | {extra[session]: <8} | {extra[request_id]: <12} | {message}",
                },
                "sinks": {
                    "console": {"enabled": True, "level": "INFO", "colorize": True},
                    "main_file": {
                        "enabled": True,
                        "path": "logs/circuit_synth_{time:YYYY-MM-DD}.log",
                        "rotation": "100 MB",
                        "retention": "30 days",
                        "compression": "gz",
                        "level": "DEBUG",
                    },
                    "performance_file": {
                        "enabled": True,
                        "path": "logs/performance_{time:YYYY-MM-DD}.jsonl",
                        "rotation": "50 MB",
                        "retention": "7 days",
                        "level": "DEBUG",
                        "filter_type": "performance",
                    },
                    "llm_conversations": {
                        "enabled": True,
                        "path": "logs/llm_conversations_{time:YYYY-MM-DD}.jsonl",
                        "rotation": "200 MB",
                        "retention": "90 days",
                        "level": "DEBUG",
                        "filter_type": "llm_conversation",
                    },
                },
                "components": {
                    "LLM": {
                        "level": "INFO",
                        "include_prompt_content": True,
                        "max_prompt_length": 1000,
                    },
                    "RUST": {"level": "INFO", "forward_to_python": True},
                    "PERF": {
                        "level": "DEBUG",
                        "enable_memory_tracking": True,
                        "enable_cpu_tracking": False,
                    },
                },
                "multi_user": {
                    "enable_user_isolation": True,
                    "session_timeout_hours": 24,
                    "max_sessions_per_user": 10,
                    "session_cleanup_interval_minutes": 60,
                },
                "performance": {
                    "async_logging": True,
                    "buffer_size": 1000,
                    "flush_interval_seconds": 5,
                    "worker_threads": 2,
                },
            },
            "environments": {
                "development": {
                    "logging": {
                        "level": "DEBUG",
                        "sinks": {
                            "console": {"enabled": True, "level": "DEBUG"},
                            "main_file": {
                                "path": "logs/dev_circuit_synth_{time:YYYY-MM-DD}.log",
                                "rotation": "10 MB",
                                "retention": "3 days",
                            },
                        },
                        "performance": {
                            "async_logging": False,  # Synchronous for easier debugging
                            "buffer_size": 100,
                        },
                    }
                },
                "production": {
                    "logging": {
                        "level": "INFO",
                        "sinks": {
                            "console": {
                                "enabled": False  # No console output in production
                            },
                            "main_file": {
                                "path": "/var/log/circuit_synth/circuit_synth_{time:YYYY-MM-DD}.log",
                                "rotation": "100 MB",
                                "retention": "30 days",
                            },
                            "error_file": {
                                "enabled": True,
                                "path": "/var/log/circuit_synth/errors_{time:YYYY-MM-DD}.log",
                                "rotation": "50 MB",
                                "retention": "90 days",
                                "level": "ERROR",
                            },
                        },
                        "components": {
                            "LLM": {
                                "include_prompt_content": False,  # Privacy in production
                                "max_prompt_length": 500,
                            }
                        },
                        "performance": {
                            "async_logging": True,
                            "buffer_size": 5000,
                            "flush_interval_seconds": 5,
                        },
                    }
                },
                "testing": {
                    "logging": {
                        "level": "DEBUG",
                        "sinks": {
                            "console": {"enabled": True, "level": "DEBUG"},
                            "main_file": {
                                "path": "logs/test_circuit_synth_{time:YYYY-MM-DD}.log",
                                "rotation": "5 MB",
                                "retention": "1 day",
                            },
                        },
                        "performance": {"async_logging": False, "buffer_size": 50},
                    }
                },
            },
            "cost_tracking": {
                "enabled": True,
                "providers": {
                    "openai": {
                        "gpt-4": {"input": 0.03, "output": 0.06},
                        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
                    },
                    "anthropic": {
                        "claude-3-opus": {"input": 0.015, "output": 0.075},
                        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
                        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
                    },
                    "google": {
                        "gemini-pro": {"input": 0.001, "output": 0.002},
                        "gemini-pro-vision": {"input": 0.002, "output": 0.004},
                    },
                },
            },
        }

    def get_sink_config(self, sink_name: str) -> SinkConfig:
        """Get configuration for a specific sink."""
        sink_data = self.get(f"logging.sinks.{sink_name}", {})
        return SinkConfig(**sink_data)

    def get_component_config(self, component_name: str) -> ComponentConfig:
        """Get configuration for a specific component."""
        component_data = self.get(f"logging.components.{component_name}", {})
        return ComponentConfig(**component_data)

    def get_multi_user_config(self) -> MultiUserConfig:
        """Get multi-user configuration."""
        multi_user_data = self.get("logging.multi_user", {})
        return MultiUserConfig(**multi_user_data)

    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration."""
        performance_data = self.get("logging.performance", {})
        return PerformanceConfig(**performance_data)

    def get_cost_config(self, provider: str, model: str) -> Dict[str, float]:
        """Get cost configuration for a specific provider and model."""
        return self.get(f"cost_tracking.providers.{provider}.{model}", {})

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check required sections
        required_sections = ["logging", "logging.sinks", "logging.components"]
        for section in required_sections:
            if not self.get(section):
                issues.append(f"Missing required configuration section: {section}")

        # Validate log levels
        valid_levels = [
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        main_level = self.get("logging.level")
        if main_level and main_level not in valid_levels:
            issues.append(f"Invalid logging level: {main_level}")

        # Validate sink configurations
        sinks = self.get("logging.sinks", {})
        for sink_name, sink_config in sinks.items():
            if isinstance(sink_config, dict):
                level = sink_config.get("level")
                if level and level not in valid_levels:
                    issues.append(f"Invalid level for sink {sink_name}: {level}")

        # Validate paths exist for file sinks
        log_dir = Path(
            self.get(
                "logging.log_directory", str(Path.home() / ".circuit-synth" / "logs")
            )
        )
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create log directory {log_dir}: {e}")

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        with self._lock:
            return self.config.copy()

    def __str__(self) -> str:
        """String representation of configuration."""
        return yaml.dump(self.config, default_flow_style=False, indent=2)
