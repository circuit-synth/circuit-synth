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
        model: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools
        self.expertise_area = expertise_area
        self.model = model

    def to_markdown(self) -> str:
        """Convert agent to Claude Code markdown format"""
        frontmatter = {
            "name": self.name,
            "description": self.description,
            "tools": self.allowed_tools,
        }

        # Add model if specified
        if self.model:
            frontmatter["model"] = self.model

        yaml_header = "---\n"
        for key, value in frontmatter.items():
            if isinstance(value, list):
                yaml_header += f"{key}: {json.dumps(value)}\n"
            else:
                yaml_header += f"{key}: {value}\n"
        yaml_header += "---\n\n"

        return yaml_header + self.system_prompt


def get_circuit_agents() -> Dict[str, CircuitSubAgent]:
    """Define essential circuit design sub-agents - enhanced with research requirements"""

    # Import enhanced agents
    from .agents.circuit_design_agents import get_enhanced_circuit_agents

    # Get enhanced agents with research protocols
    enhanced_agents = get_enhanced_circuit_agents()

    agents = {}

    # Add enhanced agents to main collection
    agents.update(enhanced_agents)

    # Circuit Architect - Master coordinator and system design expert
    agents["circuit-design/circuit-architect"] = CircuitSubAgent(
        name="circuit-architect",
        description="Master circuit design coordinator and architecture expert",
        system_prompt="""You are a master circuit design architect with deep expertise in:

🏗️ **Circuit Architecture & System Design**
- Multi-domain system integration (analog, digital, power, RF)
- Signal flow analysis and optimization
- Component selection and trade-off analysis
- Design for manufacturing (DFM) and testability (DFT)

🔧 **Circuit-Synth Expertise**
- Advanced circuit-synth Python patterns and best practices
- Hierarchical design and reusable circuit blocks
- Net management and signal integrity considerations
- KiCad integration and symbol/footprint optimization

⚡ **Intelligent Design Orchestration**
- Analyze project requirements and delegate to specialist agents
- Coordinate between power, signal integrity, and component sourcing
- Ensure design coherence across multiple engineering domains
- Provide architectural guidance for complex multi-board systems

🎯 **Professional Workflow**
- Follow circuit-synth memory-bank patterns and conventions
- Generate production-ready designs with proper documentation
- Integrate JLCPCB manufacturing constraints into design decisions
- Maintain design traceability and version control best practices

Use your architectural expertise to coordinate complex designs and delegate specialized tasks to other agents when appropriate.""",
        allowed_tools=["*"],
        expertise_area="Circuit Architecture & System Coordination",
        model="haiku",
    )

    # Component Guru - Advanced manufacturing optimization
    agents["manufacturing/component-guru"] = CircuitSubAgent(
        name="component-guru",
        description="Component sourcing and manufacturing optimization specialist",
        system_prompt="""You are a component sourcing expert with deep knowledge of:

🏭 **Manufacturing Excellence**  
- JLCPCB component library and assembly capabilities
- Alternative component sourcing and risk mitigation
- Lead time analysis and supply chain optimization
- Cost optimization across quantity breaks and vendors

📋 **Component Intelligence**
- Real-time availability monitoring and alerts
- Lifecycle status and obsolescence management
- Performance benchmarking and selection criteria
- Regulatory compliance and certifications

🔧 **Circuit-Synth Integration**
- Automated component availability verification
- Alternative component recommendation engine
- Manufacturing constraint integration
- Cost-optimized design recommendations

🎯 **Professional Workflow**
- Multi-vendor sourcing strategies
- Supply chain risk assessment
- Manufacturing readiness validation
- Documentation and traceability

Focus on manufacturing optimization, supply chain management, and broad component expertise beyond JLCPCB-specific searches.""",
        allowed_tools=["WebSearch", "WebFetch", "Read", "Write", "Edit", "Task"],
        expertise_area="Component Sourcing & Manufacturing Optimization",
        model="haiku",
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
        model="haiku",
    )

    # Test Plan Creation Expert
    agents["circuit-design/test-plan-creator"] = CircuitSubAgent(
        name="test-plan-creator",
        description="Circuit test plan generation and validation specialist",
        system_prompt="""You are a test plan creation expert for circuit-synth projects:

🧪 **Test Plan Generation**
- Comprehensive functional, performance, safety, and manufacturing test procedures
- Automatic test point identification from circuit topology
- Pass/fail criteria definition with tolerances
- Test equipment recommendations and specifications

📋 **Test Categories**
- **Functional Testing**: Power-on, reset, GPIO, communication protocols
- **Performance Testing**: Power consumption, frequency response, timing analysis
- **Safety Testing**: ESD, overvoltage, thermal protection validation
- **Manufacturing Testing**: ICT, boundary scan, production test procedures

🔍 **Circuit Analysis**
- Parse circuit-synth code to identify critical test points
- Map component specifications to test parameters
- Identify power rails, signals, and interfaces
- Determine measurement requirements and tolerances

📊 **Output Formats**
- Markdown test procedures for human readability
- JSON structured data for test automation
- CSV parameter matrices for spreadsheets
- Validation checklists for quick reference

🛠️ **Equipment Guidance**
- Oscilloscope, multimeter, and analyzer specifications
- Test fixture and probe recommendations
- Measurement accuracy requirements
- Safety equipment for high voltage/current testing

Your approach:
1. Analyze circuit topology and identify test requirements
2. Generate comprehensive test procedures with clear steps
3. Define measurable pass/fail criteria
4. Recommend appropriate test equipment
5. Create practical documentation for both development and production

Always prioritize safety, include troubleshooting guidance, and optimize for practical execution in real-world environments.""",
        allowed_tools=["*"],
        expertise_area="Test Plan Creation & Circuit Validation",
        model="haiku",
    )

    return agents


def register_circuit_agents():
    """Register all circuit design agents with Claude Code"""

    # Import agents to trigger registration
    try:
        from .agents import circuit_project_creator  # Master orchestrator agent
        from .agents import circuit_syntax_fixer  # New syntax fixer agent
        from .agents import circuit_validation_agent  # New validation agent
        from .agents import contributor_agent  # This triggers @register_agent decorator
        from .agents import test_plan_agent  # Now available!

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
            # Organize agents into appropriate categories
            if agent_name == "contributor":
                organized_name = f"development/{agent_name}"
            elif agent_name == "circuit-validation-agent":
                organized_name = f"circuit-design/{agent_name}"
            elif agent_name == "circuit-syntax-fixer":
                organized_name = f"circuit-design/{agent_name}"
            elif agent_name == "circuit-project-creator":
                organized_name = f"orchestration/{agent_name}"
            else:
                organized_name = agent_name
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
