"""
Claude Code Agents for Circuit-Synth

The legacy @register_agent persona system (contributor_agent, test_plan_agent,
circuit_design_agents, etc.) was retired along with its agent_registry module;
those files were removed. ``circuit_creator_agent`` remains (used by
tools/utilities/circuit_creator_cli.py) and is imported directly by its consumer,
so this package init intentionally imports nothing eagerly.
"""

__all__: list = []
