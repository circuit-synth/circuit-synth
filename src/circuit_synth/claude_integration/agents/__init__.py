"""
Claude Code Agents for Circuit-Synth

Modern agent definitions using the @register_agent decorator.
"""

# Import all agents to trigger registration
from . import contributor_agent

# from . import test_plan_agent  # Currently not available

__all__ = ["contributor_agent"]
