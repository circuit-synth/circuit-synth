"""
CLI-based Provider abstraction for command-line AI tools

This module provides providers that invoke LLMs via CLI tools (like `claude -p`)
rather than APIs. It's separate from llm_providers.py to avoid confusion.

Supports:
- Claude CLI (local `claude` command)
- OpenRouter CLI (via custom wrapper script)
- Any custom CLI tool via config
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for a CLI-based AI provider"""
    name: str
    enabled: bool
    command_template: List[str]
    api_key_env: Optional[str] = None
    requires_api_key: bool = False


class CLIProvider:
    """CLI-based provider for running AI models via command-line tools"""

    def __init__(self, name: str, config: Dict):
        """Initialize provider

        Args:
            name: Provider name (e.g., 'claude-cli', 'openrouter')
            config: Provider config from TOML
        """
        self.name = name
        self.enabled = config.get('enabled', True)
        self.command_template = config.get('command_template', [])
        self.api_key_env = config.get('api_key_env')
        self.requires_api_key = self.api_key_env is not None

        # Validate API key if required
        if self.requires_api_key and not os.getenv(self.api_key_env):
            self.enabled = False
            print(f"⚠️  Provider {name} disabled: {self.api_key_env} not set")

    def build_command(self, prompt_file: Path, model: str, output_file: Path) -> List[str]:
        """Build command with substitutions

        Args:
            prompt_file: Path to prompt file
            model: Model name
            output_file: Path to output file

        Returns:
            Command as list of strings
        """
        cmd = []
        env_vars = os.environ.copy()

        for part in self.command_template:
            # Substitute placeholders
            substituted = (
                part.replace('{prompt_file}', str(prompt_file))
                    .replace('{model}', model)
                    .replace('{output_file}', str(output_file))
            )

            # Handle environment variable substitutions (e.g., ${API_KEY})
            if '${' in substituted:
                for key, value in env_vars.items():
                    substituted = substituted.replace(f'${{{key}}}', value)

            cmd.append(substituted)

        return cmd

    def is_available(self) -> bool:
        """Check if provider is available

        Returns:
            True if provider can be used
        """
        if not self.enabled:
            return False

        # Check if API key is set (if required)
        if self.requires_api_key:
            if not os.getenv(self.api_key_env):
                return False

        # For CLI providers, check if command exists
        if self.command_template:
            try:
                cmd = self.command_template[0]

                # Handle relative paths (e.g., tools/openrouter-cli.py)
                if '/' in cmd:
                    # Relative or absolute path - check if file exists
                    from pathlib import Path
                    cmd_path = Path(cmd)
                    if not cmd_path.is_absolute():
                        # Make relative to repo root
                        repo_root = Path(__file__).parent.parent.parent
                        cmd_path = repo_root / cmd
                    return cmd_path.exists() and os.access(cmd_path, os.X_OK)
                else:
                    # System command - use 'which'
                    result = subprocess.run(['which', cmd], capture_output=True)
                    return result.returncode == 0
            except:
                return False

        return True

    def __repr__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"CLIProvider({self.name}, {status})"


class CLIProviderManager:
    """Manages multiple CLI-based AI providers"""

    def __init__(self, config: Dict):
        """Initialize with config

        Args:
            config: Full config dict with 'providers' section
        """
        self.providers = {}

        # Load providers from config
        providers_config = config.get('providers', {})
        for name, provider_config in providers_config.items():
            self.providers[name] = CLIProvider(name, provider_config)

    def get_provider(self, name: str) -> Optional[CLIProvider]:
        """Get provider by name

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        return self.providers.get(name)

    def get_available_providers(self) -> List[CLIProvider]:
        """Get list of available providers

        Returns:
            List of providers that are enabled and available
        """
        return [p for p in self.providers.values() if p.is_available()]

    def print_status(self):
        """Print status of all providers"""
        print("CLI Provider Status:")
        for name, provider in self.providers.items():
            available = "✓" if provider.is_available() else "✗"
            reason = ""
            if not provider.enabled:
                reason = "(disabled in config)"
            elif provider.requires_api_key and not os.getenv(provider.api_key_env):
                reason = f"({provider.api_key_env} not set)"

            print(f"  {available} {name:20s} {reason}")
