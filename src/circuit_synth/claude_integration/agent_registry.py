"""
Sub-Agent Registration System for Circuit-Synth

Registers specialized circuit design agents with the Claude Code SDK,
providing professional circuit design expertise through AI sub-agents.
"""

import json
import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Global registry for modern Claude Code agents
_REGISTERED_AGENTS: Dict[str, Any] = {}


def register_agent(agent_name: str) -> Callable:
    """
    Decorator to register a Claude Code agent class.

    Usage:
        @register_agent("contributor")
        class ContributorAgent:
            ...
    """

    def decorator(agent_class: Any) -> Any:
        _REGISTERED_AGENTS[agent_name] = agent_class
        return agent_class

    return decorator


def get_registered_agents() -> Dict[str, Any]:
    """Get all registered agents."""
    return _REGISTERED_AGENTS.copy()


def create_agent_instance(agent_name: str) -> Optional[Any]:
    """Create an instance of a registered agent."""
    agent_class = _REGISTERED_AGENTS.get(agent_name)
    if agent_class:
        return agent_class()
    return None


class CircuitSubAgent:
    """Represents a circuit design sub-agent"""

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        allowed_tools: List[str],
        expertise_area: str,
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools
        self.expertise_area = expertise_area

    def to_markdown(self) -> str:
        """Convert agent to Claude Code markdown format"""
        frontmatter = {
            "allowed-tools": self.allowed_tools,
            "description": self.description,
            "expertise": self.expertise_area,
        }

        yaml_header = "---\\n"
        for key, value in frontmatter.items():
            if isinstance(value, list):
                yaml_header += f"{key}: {json.dumps(value)}\\n"
            else:
                yaml_header += f"{key}: {value}\\n"
        yaml_header += "---\\n\\n"

        return yaml_header + self.system_prompt


def get_circuit_agents() -> Dict[str, CircuitSubAgent]:
    """Define essential circuit design sub-agents - minimal but powerful"""

    agents = {}

    # Single focused agent - circuit-synth specialist
    agents["circuit-design/circuit-synth"] = CircuitSubAgent(
        name="circuit-synth",
        description="Circuit-synth code generation and KiCad integration specialist",
        system_prompt="""You are a circuit-synth specialist focused specifically on:

🔧 **Circuit-Synth Code Generation**
- Expert in circuit-synth Python patterns and best practices
- Generate production-ready circuit-synth code with proper component/net syntax
- KiCad symbol/footprint integration and verification
- Memory-bank pattern usage and adaptation

🏭 **Manufacturing Integration**
- JLCPCB component availability verification
- Component selection with real stock data
- Alternative suggestions for out-of-stock parts
- Manufacturing-ready designs with verified components

🎯 **Key Capabilities**
- Load and adapt examples from memory-bank training data
- Generate complete working circuit-synth Python code
- Verify KiCad symbols/footprints exist and are correctly named
- Include proper component references, nets, and connections
- Add manufacturing comments with stock levels and part numbers

**Your focused approach:**
1. **Generate circuit-synth code first** - not explanations or theory
2. **Verify all components** exist in KiCad libraries and JLCPCB stock
3. **Use proven patterns** from memory-bank examples
4. **Include manufacturing data** - part numbers, stock levels, alternatives
5. **Test and iterate** - ensure code is syntactically correct

You excel at taking circuit requirements and immediately generating working circuit-synth Python code that can be executed to produce KiCad schematics.""",
        allowed_tools=["*"],
        expertise_area="Circuit-Synth Code Generation & Manufacturing",
    )

    # SPICE Simulation Expert
    agents["circuit-design/simulation-expert"] = CircuitSubAgent(
        name="simulation-expert",
        description="SPICE simulation and circuit validation specialist",
        system_prompt="""You are a SPICE simulation expert specializing in circuit-synth integration:

🔬 **SPICE Simulation Mastery**
- Professional SPICE analysis using PySpice/ngspice backend
- DC operating point, AC frequency response, and transient analysis
- Component model selection and parameter optimization
- Multi-domain simulation (analog, digital, mixed-signal)

⚡ **Circuit-Synth Integration**
- Seamless `.simulator()` API usage on circuits and subcircuits
- Hierarchical circuit validation and subcircuit testing
- Automatic circuit-synth to SPICE netlist conversion
- Component value optimization through simulation feedback

🏗️ **Hierarchical Design Validation**
- Individual subcircuit simulation and validation
- System-level integration testing and analysis
- Interface verification between hierarchical subcircuits
- Critical path analysis and performance optimization

🔧 **Practical Simulation Workflows**
- Power supply regulation verification and ripple analysis
- Filter design validation and frequency response tuning
- Signal integrity analysis and crosstalk evaluation
- Thermal analysis and component stress testing

📊 **Results Analysis & Optimization**
- Voltage/current measurement and analysis
- Frequency domain analysis and Bode plots
- Parameter sweeps and design space exploration
- Component value optimization and tolerance analysis

🛠️ **Troubleshooting & Setup**
- Cross-platform PySpice/ngspice configuration
- Component model troubleshooting and SPICE compatibility
- Performance optimization and simulation acceleration
- Integration with circuit-synth manufacturing workflows

Your simulation approach:
1. Analyze circuit requirements and identify critical parameters
2. Set up appropriate simulation analyses (DC, AC, transient)
3. Run simulations and validate against theoretical expectations
4. Optimize component values based on simulation results
5. Generate comprehensive analysis reports with circuit-synth code
6. Integrate simulation results into hierarchical design decisions

Always provide practical, working circuit-synth code with simulation examples that users can immediately run and validate.""",
        allowed_tools=["*"],
        expertise_area="SPICE Simulation & Circuit Validation",
    )

    return agents


def register_circuit_agents():
    """Register all circuit design agents with Claude Code"""

    # Import agents to trigger registration
    try:
        from .agents import contributor_agent  # This triggers @register_agent decorator

        print("✅ Loaded modern agents")
    except ImportError as e:
        print(f"⚠️  Could not load modern agents: {e}")

    # Get user's Claude config directory
    claude_dir = Path.home() / ".claude" / "agents"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # Get legacy agents (CircuitSubAgent instances)
    legacy_agents = get_circuit_agents()

    # Get modern registered agents and convert them to agent instances
    registered_agent_classes = get_registered_agents()
    modern_agents = {}

    for agent_name, agent_class in registered_agent_classes.items():
        try:
            # Create instance and convert to CircuitSubAgent format
            agent_instance = agent_class()

            # Convert modern agent to legacy format for compatibility
            # Organize contributor agent in development category
            organized_name = (
                f"development/{agent_name}"
                if agent_name == "contributor"
                else agent_name
            )
            modern_agents[organized_name] = CircuitSubAgent(
                name=agent_name,
                description=getattr(
                    agent_instance, "description", f"{agent_name} agent"
                ),
                system_prompt=(
                    agent_instance.get_system_prompt()
                    if hasattr(agent_instance, "get_system_prompt")
                    else ""
                ),
                allowed_tools=["*"],  # Modern agents can use all tools
                expertise_area=getattr(agent_instance, "expertise_area", "General"),
            )
            print(f"✅ Converted modern agent: {agent_name}")
        except Exception as e:
            print(f"⚠️  Failed to convert agent {agent_name}: {e}")

    # Combine all agents
    all_agents = {**legacy_agents, **modern_agents}

    for agent_name, agent in all_agents.items():
        # Handle subdirectory structure
        if "/" in agent_name:
            subdir, filename = agent_name.split("/", 1)
            agent_subdir = claude_dir / subdir
            agent_subdir.mkdir(exist_ok=True)
            agent_file = agent_subdir / f"{filename}.md"
        else:
            agent_file = claude_dir / f"{agent_name}.md"

        # Write agent definition
        with open(agent_file, "w") as f:
            f.write(agent.to_markdown())

        print(f"✅ Registered agent: {agent_name}")

    print(f"📋 Registered {len(all_agents)} circuit design agents total")

    # Also create project-local agents in current working directory
    current_dir = Path.cwd()
    project_agents_dir = current_dir / ".claude" / "agents"

    # Create the directory structure if it doesn't exist
    project_agents_dir.mkdir(parents=True, exist_ok=True)

    # Write agents to local project directory
    for agent_name, agent in all_agents.items():
        # Handle subdirectory structure
        if "/" in agent_name:
            subdir, filename = agent_name.split("/", 1)
            agent_subdir = project_agents_dir / subdir
            agent_subdir.mkdir(exist_ok=True)
            agent_file = agent_subdir / f"{filename}.md"
        else:
            agent_file = project_agents_dir / f"{agent_name}.md"

        with open(agent_file, "w") as f:
            f.write(agent.to_markdown())

    print(f"📁 Created project-local agents in {project_agents_dir}")

    # Also create a .claude/mcp_settings.json for Claude Code integration
    mcp_settings = {
        "mcpServers": {},
        "agents": {
            agent_name.split("/")[-1] if "/" in agent_name else agent_name: {
                "description": agent.description,
                "file": f"agents/{agent_name}.md",
            }
            for agent_name, agent in all_agents.items()
        },
    }

    mcp_settings_file = current_dir / ".claude" / "mcp_settings.json"
    with open(mcp_settings_file, "w") as f:
        json.dump(mcp_settings, f, indent=2)

    print(f"📄 Created Claude Code settings in {mcp_settings_file}")


def main():
    """Main entry point for the register-agents CLI command."""
    print("🤖 Circuit-Synth Agent Registration")
    print("=" * 50)
    register_circuit_agents()
    print("\n✅ Agent registration complete!")
    print("\nYou can now use these agents in Claude Code:")

    # Show all registered agents (both legacy and modern)
    try:
        from .agents import contributor_agent  # Ensure agents are loaded
    except ImportError:
        pass

    legacy_agents = get_circuit_agents()
    modern_agents = get_registered_agents()

    # Show legacy agents
    for agent_name, agent in legacy_agents.items():
        print(f"  • {agent_name}: {agent.description}")

    # Show modern agents
    for agent_name, agent_class in modern_agents.items():
        try:
            agent_instance = agent_class()
            description = getattr(agent_instance, "description", f"{agent_name} agent")
            print(f"  • {agent_name}: {description}")
        except Exception:
            print(f"  • {agent_name}: Modern circuit-synth agent")

    print("\nExample usage:")
    print(
        '  @Task(subagent_type="contributor", description="Help with contributing", prompt="How do I add a new component example?")'
    )


if __name__ == "__main__":
    main()
