"""
Template Manager for circuit-synth project creation

Handles loading and managing circuit templates for base circuits and examples.
"""

from pathlib import Path
from typing import Dict, Optional
import shutil

from .project_config import Circuit, ProjectConfig, CircuitTemplate


class TemplateManager:
    """Manages loading and rendering of circuit templates"""

    def __init__(self):
        # Get templates directory from package data
        self.package_dir = Path(__file__).parent.parent.parent  # Get to circuit_synth/
        self.templates_dir = self.package_dir / "data" / "templates"
        self.base_circuits_dir = self.templates_dir / "base_circuits"
        self.example_circuits_dir = self.templates_dir / "example_circuits"

    def load_circuit(self, circuit: Circuit) -> str:
        """Load circuit template code

        Args:
            circuit: Circuit enum value

        Returns:
            Python code as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        # Get template directory based on circuit's template_dir attribute
        template_dir = self.templates_dir / circuit.template_dir
        template_file = template_dir / f"{circuit.value}.py"

        if not template_file.exists():
            raise FileNotFoundError(
                f"Circuit template not found: {template_file}\n"
                f"Expected location: {template_dir}"
            )

        return template_file.read_text()

    def copy_circuit_to_project(
        self,
        circuit: Circuit,
        project_path: Path,
        is_first: bool = False
    ) -> None:
        """Copy circuit template to project directory

        Args:
            circuit: Circuit to copy
            project_path: Destination project directory
            is_first: If True, name it main.py; otherwise use circuit name
        """
        circuit_code = self.load_circuit(circuit)

        # Create circuit-synth directory if it doesn't exist
        circuit_dir = project_path / "circuit-synth"
        circuit_dir.mkdir(exist_ok=True)

        # Determine target filename
        if is_first:
            target_filename = "main.py"
        else:
            target_filename = f"{circuit.value}.py"

        # Write the circuit file
        target_file = circuit_dir / target_filename
        target_file.write_text(circuit_code)

    def list_available_circuits(self) -> list[Circuit]:
        """Get list of all available circuits

        Returns:
            List of Circuit enums
        """
        return list(Circuit)

    def validate_templates(self) -> Dict[str, bool]:
        """Validate that all template files exist

        Returns:
            Dictionary mapping template names to existence status
        """
        results = {}

        # Check all circuits
        for circuit in Circuit:
            template_dir = self.templates_dir / circuit.template_dir
            template_file = template_dir / f"{circuit.value}.py"
            results[circuit.value] = template_file.exists()

        return results


class READMEGenerator:
    """Generates README.md customized for project configuration"""

    def generate(self, config: ProjectConfig, project_path: Path) -> str:
        """Generate README content based on configuration

        Args:
            config: Project configuration
            project_path: Project directory path

        Returns:
            README markdown content
        """
        project_name = config.project_name or project_path.name

        # Start with header
        readme = f"""# {project_name}

A circuit-synth project for PCB design with Python.

## 🚀 Quick Start

```bash
# Run your circuit
uv run python circuit-synth/main.py
```

This will generate KiCad project files that you can open in KiCad.

"""

        # Add section about included circuits
        if config.has_circuits():
            readme += f"""## 📁 Included Circuits ({len(config.circuits)})

This project includes the following circuit templates:

"""
            for idx, circuit in enumerate(config.circuits, 1):
                filename = "main.py" if idx == 1 else f"{circuit.value}.py"
                readme += f"{idx}. **{circuit.display_name}** ({circuit.difficulty}): {circuit.description}\n"
                readme += f"   - File: `circuit-synth/{filename}`\n\n"

            readme += "\nYou can run any circuit file independently or use them as reference for your own designs.\n\n"

        # Add circuit-synth basics
        readme += """## 🏗️ Circuit-Synth Basics

### Creating Components

```python
from circuit_synth import Component, Net, circuit

# Create a resistor
resistor = Component(
    symbol="Device:R",           # KiCad symbol
    ref="R",                     # Reference prefix
    value="10k",                 # Component value
    footprint="Resistor_SMD:R_0603_1608Metric"
)
```

### Defining Nets and Connections

```python
# Create nets (electrical connections)
vcc = Net('VCC_3V3')
gnd = Net('GND')

# Connect component pins to nets
resistor[1] += vcc   # Pin 1 to VCC
resistor[2] += gnd   # Pin 2 to GND
```

### Generating KiCad Projects

```python
@circuit(name="My_Circuit")
def my_circuit():
    # Your circuit code here
    pass

if __name__ == '__main__':
    circuit_obj = my_circuit()
    circuit_obj.generate_kicad_project(
        project_name="my_project",
        generate_pcb=True
    )
```

"""

        # Add documentation links
        readme += """## 📖 Documentation

- Circuit-Synth: https://circuit-synth.readthedocs.io
- KiCad: https://docs.kicad.org

"""

        # Add Claude agents section if included
        if config.include_agents:
            readme += """## 🤖 AI-Powered Design with Claude Code

This project includes specialized circuit design agents in `.claude/agents/`:

- **circuit-architect**: Master circuit design coordinator
- **circuit-synth**: Circuit code generation and KiCad integration
- **simulation-expert**: SPICE simulation and validation
- **component-guru**: Component sourcing and manufacturing optimization

Use natural language to design circuits with AI assistance!

"""

        # Add next steps
        readme += """## 🚀 Next Steps

1. Open `circuit-synth/main.py` and review the base circuit
2. Run the circuit to generate KiCad files
3. Open the generated `.kicad_pro` file in KiCad
4. Modify the circuit or create your own designs

**Happy circuit designing!** 🎛️
"""

        return readme


class CLAUDEMDGenerator:
    """Generates CLAUDE.md customized for project configuration"""

    def generate(self, config: ProjectConfig) -> str:
        """Generate CLAUDE.md content based on configuration

        Args:
            config: Project configuration

        Returns:
            CLAUDE.md markdown content
        """

        claude_md = """# CLAUDE.md

Project-specific guidance for Claude Code when working with this circuit-synth project.

## 🚀 Project Overview

This is a **circuit-synth project** for PCB design with Python code.

"""

        # Add info about included circuits
        if config.has_circuits():
            claude_md += f"""## 📝 Included Circuits ({len(config.circuits)})

This project includes the following circuit templates:

"""
            for idx, circuit in enumerate(config.circuits, 1):
                filename = "main.py" if idx == 1 else f"{circuit.value}.py"
                claude_md += f"{idx}. **{circuit.display_name}** ({circuit.difficulty})\n"
                claude_md += f"   - {circuit.description}\n"
                claude_md += f"   - File: `circuit-synth/{filename}`\n\n"

            claude_md += "You can modify these circuits or use them as reference for creating new designs.\n\n"

        # Add available tools
        if config.include_agents:
            claude_md += """## ⚡ Available Tools & Commands

### Slash Commands
- `/find-symbol` - Search KiCad symbol libraries
- `/find-footprint` - Search KiCad footprint libraries
- `/find_stm32` - STM32-specific component search

### Specialized Agents
- **circuit-architect** - Master coordinator for complex projects
- **circuit-synth** - Circuit code generation and KiCad integration
- **simulation-expert** - SPICE simulation and validation
- **component-guru** - Component sourcing and manufacturing

"""

        # Add workflow guidance
        claude_md += """## 🔧 Development Workflow

1. **Component Selection**: Use `/find-symbol` and `/find-footprint` to find KiCad components
2. **Circuit Design**: Write Python code using circuit-synth
3. **Generate KiCad**: Run the Python file to create KiCad project
4. **Validate**: Open in KiCad and verify the design

## 📚 Quick Reference

### Component Creation
```python
component = Component(
    symbol="Device:R",
    ref="R",
    value="10k",
    footprint="Resistor_SMD:R_0603_1608Metric"
)
```

### Net Connections
```python
vcc = Net("VCC_3V3")
component[1] += vcc
```

---

**This project is optimized for AI-powered circuit design with Claude Code!** 🎛️
"""

        return claude_md
