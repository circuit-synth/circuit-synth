"""
Claude Code SDK Integration for Circuit-Synth

This module provides professional integration with Claude Code SDK, including:
- Sub-agent registration and management
- Intelligent hook system for real-time design validation
- Context-aware slash commands
- Automated design optimization workflows

Note: Claude Code SDK is optional. If not available, this module provides
graceful fallback behavior.
"""


def register_circuit_agents():
    """Register circuit design agents - fallback implementation"""
    try:
        from .agent_registry import register_circuit_agents as _register

        return _register()
    except ImportError:
        print("⚠️  Claude Code SDK not available. Skipping agent registration.")
        print("   Install with: pip install circuit-synth[claude]")


def setup_circuit_hooks():
    """Setup circuit design hooks - fallback implementation"""
    try:
        from .hooks import setup_circuit_hooks as _setup

        return _setup()
    except ImportError:
        print("⚠️  Claude Code SDK not available. Skipping hook setup.")


def register_circuit_commands():
    """Register circuit design commands - fallback implementation"""
    try:
        from .commands import register_circuit_commands as _register

        return _register()
    except ImportError:
        print("⚠️  Claude Code SDK not available. Skipping command registration.")


__all__ = [
    "register_circuit_agents",
    "setup_circuit_hooks",
    "register_circuit_commands",
    "initialize_claude_integration",
]


def initialize_claude_integration():
    """Initialize complete Claude Code integration for circuit-synth"""
    print("🚀 Initializing Claude Code integration for circuit-synth...")

    try:
        # Try to import the full implementations
        from .agent_registry import register_circuit_agents as _register_agents
        from .commands import register_circuit_commands as _register_commands
        from .hooks import setup_circuit_hooks as _setup_hooks

        _register_agents()
        _setup_hooks()
        _register_commands()
        print("✅ Claude Code integration initialized for circuit-synth")

    except ImportError as e:
        print("⚠️  Claude Code SDK not available for full integration.")
        print(
            "   For AI-powered circuit design, install with: pip install circuit-synth[claude]"
        )
        print("   Or install Claude Code SDK separately: pip install claude-code-sdk")
        print(f"   Error: {e}")

        # Still provide basic functionality
        register_circuit_agents()
        setup_circuit_hooks()
        register_circuit_commands()
        print("ℹ️  Basic Claude integration setup complete (without SDK)")
