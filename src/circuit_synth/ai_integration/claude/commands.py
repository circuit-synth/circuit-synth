"""
Context-Aware Slash Commands for Circuit-Synth

Provides intelligent slash commands that understand circuit design context
and provide rapid development capabilities.
"""

import os
from pathlib import Path
from typing import Dict, List


class CircuitCommand:
    """Represents a context-aware circuit design slash command"""

    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        allowed_tools: List[str] = None,
        argument_hint: str = None,
    ):
        self.name = name
        self.description = description
        self.content = content
        self.allowed_tools = allowed_tools or ["*"]
        self.argument_hint = argument_hint

    def to_markdown(self) -> str:
        """Convert to Claude Code slash command format"""
        frontmatter = f"""---
allowed-tools: {self.allowed_tools if isinstance(self.allowed_tools, str) else str(self.allowed_tools)}
description: {self.description}"""

        if self.argument_hint:
            frontmatter += f"\\nargument-hint: {self.argument_hint}"

        frontmatter += "\\n---\\n\\n"

        return frontmatter + self.content


def get_circuit_commands() -> Dict[str, CircuitCommand]:
    """Define essential circuit design slash commands - minimal and focused"""

    commands = {}

    # Only keep the one command that provides genuine automation value
    commands["check-manufacturing"] = CircuitCommand(
        name="check-manufacturing",
        description="Real-time component availability and DFM validation",
        content="""Quick manufacturing readiness check with real-time component availability.

🏭 **Manufacturing Validation**

**Automated Checks:**
1. **Component Availability**: Real-time JLC stock verification for all components
2. **DFM Compliance**: Check against JLC assembly capabilities
3. **Alternative Suggestions**: Find equivalent in-stock components

**Use the circuit-synth agent** to:
- Extract all components from current circuit-synth code
- Check real-time JLC availability and pricing
- Suggest alternatives for out-of-stock components
- Validate package types against JLC assembly capabilities

**Quick Report:**
- ✅/❌ Status for each component with stock levels
- 🔄 Alternative suggestions for problematic components  
- 💰 Current pricing at 100/1K/10K quantities
- ⚠️ Any DFM issues or assembly constraints""",
    )

    return commands


def register_circuit_commands():
    """Register intelligent circuit design slash commands"""

    # Get user's Claude config directory
    claude_dir = Path.home() / ".claude" / "commands"
    claude_dir.mkdir(parents=True, exist_ok=True)

    commands = get_circuit_commands()

    for cmd_name, command in commands.items():
        cmd_file = claude_dir / f"{cmd_name}.md"

        # Write command definition
        with open(cmd_file, "w") as f:
            f.write(command.to_markdown())

        print(f"✅ Registered command: /{cmd_name}")

    print(f"⚡ Registered {len(commands)} essential circuit command")

    # Also create project-local commands for development
    project_commands_dir = (
        Path(__file__).parent.parent.parent.parent / ".claude" / "commands"
    )
    if project_commands_dir.exists():
        for cmd_name, command in commands.items():
            cmd_file = project_commands_dir / f"{cmd_name}.md"
            with open(cmd_file, "w") as f:
                f.write(command.to_markdown())
        print(f"📁 Also created project-local commands for development")


if __name__ == "__main__":
    register_circuit_commands()
