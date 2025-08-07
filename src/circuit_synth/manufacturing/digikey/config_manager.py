#!/usr/bin/env python3
"""
DigiKey Configuration Manager

Provides secure and flexible configuration management for DigiKey API credentials.
Supports multiple configuration sources with proper precedence.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DigiKeyConfigManager:
    """
    Manages DigiKey API configuration with multiple source support.

    Configuration precedence (highest to lowest):
    1. Direct parameters (programmatic)
    2. Environment variables
    3. User config file (~/.circuit_synth/digikey_config.json)
    4. Project .env file (if python-dotenv installed)
    """

    CONFIG_FILENAME = "digikey_config.json"
    USER_CONFIG_DIR = Path.home() / ".circuit_synth"

    @classmethod
    def get_config_paths(cls) -> list[Path]:
        """Get list of potential configuration file paths."""
        paths = [
            cls.USER_CONFIG_DIR / cls.CONFIG_FILENAME,  # User home config
            Path.cwd() / ".circuit_synth" / cls.CONFIG_FILENAME,  # Project config
        ]
        return paths

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> Optional[dict]:
        """
        Load configuration from JSON file.

        Args:
            config_path: Specific path to config file, or None to search defaults

        Returns:
            Configuration dict or None if not found
        """
        if config_path:
            paths = [config_path]
        else:
            paths = cls.get_config_paths()

        for path in paths:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        config = json.load(f)
                        logger.info(f"Loaded DigiKey config from: {path}")
                        return config
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")

        return None

    @classmethod
    def save_to_file(
        cls,
        client_id: str,
        client_secret: str,
        sandbox_mode: bool = False,
        config_path: Optional[Path] = None,
    ) -> bool:
        """
        Save configuration to JSON file.

        Args:
            client_id: DigiKey Client ID
            client_secret: DigiKey Client Secret
            sandbox_mode: Whether to use sandbox API
            config_path: Path to save config, or None for default user location

        Returns:
            True if saved successfully
        """
        if not config_path:
            config_path = cls.USER_CONFIG_DIR / cls.CONFIG_FILENAME

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "sandbox_mode": sandbox_mode,
        }

        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            # Set restrictive permissions (owner read/write only)
            config_path.chmod(0o600)

            logger.info(f"Saved DigiKey config to: {config_path}")
            print(f"✅ DigiKey configuration saved to: {config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    @classmethod
    def load_from_env(cls) -> Optional[dict]:
        """
        Load configuration from environment variables.

        Returns:
            Configuration dict or None if not set
        """
        client_id = os.environ.get("DIGIKEY_CLIENT_ID")
        client_secret = os.environ.get("DIGIKEY_CLIENT_SECRET")

        if client_id and client_secret:
            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "sandbox_mode": os.environ.get(
                    "DIGIKEY_CLIENT_SANDBOX", "False"
                ).lower()
                == "true",
                "cache_dir": os.environ.get("DIGIKEY_STORAGE_PATH"),
            }

        return None

    @classmethod
    def load_from_dotenv(cls) -> Optional[dict]:
        """
        Load configuration from .env file using python-dotenv.

        Returns:
            Configuration dict or None if not available
        """
        try:
            from dotenv import find_dotenv, load_dotenv

            # Find and load .env file
            env_file = find_dotenv()
            if env_file:
                load_dotenv(env_file)
                logger.info(f"Loaded .env file from: {env_file}")

                # Now try loading from environment
                return cls.load_from_env()

        except ImportError:
            # python-dotenv not installed
            pass

        return None

    @classmethod
    def get_config(
        cls,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        sandbox_mode: Optional[bool] = None,
        config_path: Optional[Path] = None,
    ) -> dict:
        """
        Get configuration from all available sources.

        Args:
            client_id: Direct Client ID (highest precedence)
            client_secret: Direct Client Secret
            sandbox_mode: Direct sandbox mode setting
            config_path: Specific config file path

        Returns:
            Complete configuration dict

        Raises:
            ValueError: If no valid configuration found
        """
        config = {
            "client_id": "",
            "client_secret": "",
            "sandbox_mode": False,
            "cache_dir": None,
        }

        # Load from file (lowest precedence)
        file_config = cls.load_from_file(config_path)
        if file_config:
            config.update(file_config)

        # Load from .env file
        dotenv_config = cls.load_from_dotenv()
        if dotenv_config:
            config.update(dotenv_config)

        # Load from environment variables
        env_config = cls.load_from_env()
        if env_config:
            config.update(env_config)

        # Apply direct parameters (highest precedence)
        if client_id:
            config["client_id"] = client_id
        if client_secret:
            config["client_secret"] = client_secret
        if sandbox_mode is not None:
            config["sandbox_mode"] = sandbox_mode

        # Validate configuration
        if not config["client_id"] or not config["client_secret"]:
            raise ValueError(
                "DigiKey API credentials not configured. Please provide:\n"
                "1. Direct parameters when creating client\n"
                "2. Environment variables (DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET)\n"
                "3. Config file (~/.circuit_synth/digikey_config.json)\n"
                "4. .env file in project directory\n"
                "\nRun 'circuit-synth configure-digikey' to set up credentials."
            )

        return config

    @classmethod
    def interactive_setup(cls) -> bool:
        """
        Interactive setup wizard for DigiKey credentials.

        Returns:
            True if setup completed successfully
        """
        print("\n" + "=" * 60)
        print("DigiKey API Configuration Setup")
        print("=" * 60)

        print("\nTo use DigiKey integration, you need API credentials.")
        print("Visit https://developer.digikey.com/ to get them.\n")

        # Get credentials from user
        client_id = input("Enter your DigiKey Client ID: ").strip()
        if not client_id:
            print("❌ Client ID is required")
            return False

        client_secret = input("Enter your DigiKey Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret is required")
            return False

        # Ask about sandbox mode
        sandbox = input("Use sandbox mode? (y/N): ").strip().lower() == "y"

        # Ask where to save
        print("\nWhere would you like to save the configuration?")
        print("1. User home (~/.circuit_synth/digikey_config.json) [Recommended]")
        print("2. Current project (./.circuit_synth/digikey_config.json)")
        print("3. Don't save (use environment variables)")

        choice = input("\nChoice (1/2/3) [1]: ").strip() or "1"

        if choice == "1":
            config_path = cls.USER_CONFIG_DIR / cls.CONFIG_FILENAME
            success = cls.save_to_file(client_id, client_secret, sandbox, config_path)

        elif choice == "2":
            config_path = Path.cwd() / ".circuit_synth" / cls.CONFIG_FILENAME
            success = cls.save_to_file(client_id, client_secret, sandbox, config_path)

        elif choice == "3":
            print("\n✅ Configuration not saved.")
            print("\nTo use these credentials, set environment variables:")
            print(f"export DIGIKEY_CLIENT_ID='{client_id}'")
            print(f"export DIGIKEY_CLIENT_SECRET='{client_secret}'")
            if sandbox:
                print(f"export DIGIKEY_CLIENT_SANDBOX=True")
            success = True

        else:
            print("❌ Invalid choice")
            return False

        if success:
            print("\n✅ DigiKey configuration complete!")
            print("\nTest your setup with:")
            print("  python -m circuit_synth.manufacturing.digikey.test_connection")

        return success


def configure_digikey_cli():
    """CLI command for configuring DigiKey credentials."""
    import sys

    success = DigiKeyConfigManager.interactive_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Run interactive setup if executed directly
    configure_digikey_cli()
