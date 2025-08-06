"""
Claude Code Agents for Circuit-Synth

Modern agent definitions using the @register_agent decorator.
"""

# Import all agents to trigger registration
from . import contributor_agent, test_plan_agent

__all__ = ["contributor_agent", "test_plan_agent"]
