"""
Sub-Agent Registration System for Circuit-Synth

Registers specialized circuit design agents with the Claude Code SDK,
providing professional circuit design expertise through AI sub-agents.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


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
    agents["circuit-synth"] = CircuitSubAgent(
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

    return agents


def register_circuit_agents():
    """Register all circuit design agents with Claude Code"""

    # Get user's Claude config directory
    claude_dir = Path.home() / ".claude" / "agents"
    claude_dir.mkdir(parents=True, exist_ok=True)

    agents = get_circuit_agents()

    for agent_name, agent in agents.items():
        agent_file = claude_dir / f"{agent_name}.md"

        # Write agent definition
        with open(agent_file, "w") as f:
            f.write(agent.to_markdown())

        print(f"✅ Registered agent: {agent_name}")

    print(f"📋 Registered {len(agents)} circuit design agent")

    # Also create project-local agents for development
    project_agents_dir = (
        Path(__file__).parent.parent.parent.parent / ".claude" / "agents"
    )
    if project_agents_dir.exists():
        for agent_name, agent in agents.items():
            agent_file = project_agents_dir / f"{agent_name}.md"
            with open(agent_file, "w") as f:
                f.write(agent.to_markdown())
        print(f"📁 Also created project-local agents for development")


if __name__ == "__main__":
    register_circuit_agents()
