"""
Template Manager for circuit-synth project creation

Handles loading and managing circuit templates for base circuits and examples.
"""

from pathlib import Path
from typing import Dict, Optional
import shutil

from .project_config import BaseCircuit, ExampleCircuit, ProjectConfig, CircuitTemplate


class TemplateManager:
    """Manages loading and rendering of circuit templates"""

    def __init__(self):
        # Get templates directory from package data
        self.package_dir = Path(__file__).parent.parent.parent  # Get to circuit_synth/
        self.templates_dir = self.package_dir / "data" / "templates"
        self.base_circuits_dir = self.templates_dir / "base_circuits"
        self.example_circuits_dir = self.templates_dir / "example_circuits"

    def load_base_circuit(self, circuit: BaseCircuit) -> str:
        """Load base circuit template code

        Args:
            circuit: BaseCircuit enum value

        Returns:
            Python code as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_file = self.base_circuits_dir / f"{circuit.value}.py"

        if not template_file.exists():
            raise FileNotFoundError(
                f"Base circuit template not found: {template_file}\n"
                f"Expected location: {self.base_circuits_dir}"
            )

        return template_file.read_text()

    def load_example(self, example: ExampleCircuit) -> Dict[str, str]:
        """Load example circuit (may be single or multiple files)

        Args:
            example: ExampleCircuit enum value

        Returns:
            Dictionary mapping filename to code content
            For single-file examples: {"example.py": "code..."}
            For multi-file examples: {"main.py": "...", "subcircuit.py": "..."}

        Raises:
            FileNotFoundError: If example template doesn't exist
        """
        example_dir = self.example_circuits_dir / example.value

        # Check if it's a directory (multi-file example)
        if example_dir.is_dir():
            # Multi-file example - load all .py files
            python_files = list(example_dir.glob("*.py"))
            if not python_files:
                raise FileNotFoundError(
                    f"No Python files found in example directory: {example_dir}"
                )

            return {
                f.name: f.read_text()
                for f in python_files
            }
        else:
            # Single-file example
            example_file = example_dir.with_suffix(".py")

            if not example_file.exists():
                raise FileNotFoundError(
                    f"Example template not found: {example_file}\n"
                    f"Looked for directory: {example_dir}\n"
                    f"Looked for file: {example_file}"
                )

            return {example_file.name: example_file.read_text()}

    def copy_base_circuit_to_project(
        self,
        circuit: BaseCircuit,
        project_path: Path,
        target_filename: str = "main.py"
    ) -> None:
        """Copy base circuit template to project directory

        Args:
            circuit: BaseCircuit to copy
            project_path: Destination project directory
            target_filename: Name for the circuit file (default: main.py)
        """
        circuit_code = self.load_base_circuit(circuit)

        # Create circuit-synth directory if it doesn't exist
        circuit_dir = project_path / "circuit-synth"
        circuit_dir.mkdir(exist_ok=True)

        # Write the circuit file
        target_file = circuit_dir / target_filename
        target_file.write_text(circuit_code)

    def copy_example_to_project(
        self,
        example: ExampleCircuit,
        project_path: Path
    ) -> None:
        """Copy example circuit(s) to project directory

        Args:
            example: ExampleCircuit to copy
            project_path: Destination project directory
        """
        example_files = self.load_example(example)

        # Create circuit-synth directory if it doesn't exist
        circuit_dir = project_path / "circuit-synth"
        circuit_dir.mkdir(exist_ok=True)

        # Create examples subdirectory
        examples_dir = circuit_dir / "examples"
        examples_dir.mkdir(exist_ok=True)

        # Create example-specific subdirectory for multi-file examples
        if len(example_files) > 1:
            example_subdir = examples_dir / example.value
            example_subdir.mkdir(exist_ok=True)
            target_dir = example_subdir
        else:
            target_dir = examples_dir

        # Write all files
        for filename, code in example_files.items():
            target_file = target_dir / filename
            target_file.write_text(code)

    def get_template_info(self, circuit: BaseCircuit) -> CircuitTemplate:
        """Get metadata about a circuit template

        Args:
            circuit: BaseCircuit to get info for

        Returns:
            CircuitTemplate with metadata
        """
        # Load the code to analyze it
        code = self.load_base_circuit(circuit)

        # Extract docstring for description
        lines = code.split('\n')
        description = ""
        for line in lines:
            if '"""' in line or "'''" in line:
                # Found docstring start
                desc_lines = []
                in_docstring = True
                for next_line in lines[lines.index(line)+1:]:
                    if '"""' in next_line or "'''" in next_line:
                        break
                    desc_lines.append(next_line)
                description = '\n'.join(desc_lines).strip()
                break

        # Map difficulty from enum
        difficulty_map = {
            "Beginner ⭐": "beginner",
            "Intermediate ⭐⭐": "intermediate",
            "Advanced ⭐⭐⭐": "advanced"
        }
        complexity_level = difficulty_map.get(circuit.difficulty, "beginner")

        return CircuitTemplate(
            name=circuit.value,
            display_name=circuit.display_name,
            difficulty=circuit.difficulty,
            description=circuit.description,
            code=code,
            complexity_level=complexity_level
        )

    def list_available_base_circuits(self) -> list[BaseCircuit]:
        """Get list of all available base circuits

        Returns:
            List of BaseCircuit enums
        """
        return list(BaseCircuit)

    def list_available_examples(self) -> list[ExampleCircuit]:
        """Get list of all available example circuits

        Returns:
            List of ExampleCircuit enums
        """
        return list(ExampleCircuit)

    def validate_templates(self) -> Dict[str, bool]:
        """Validate that all template files exist

        Returns:
            Dictionary mapping template names to existence status
        """
        results = {}

        # Check base circuits
        for circuit in BaseCircuit:
            template_file = self.base_circuits_dir / f"{circuit.value}.py"
            results[f"base:{circuit.value}"] = template_file.exists()

        # Check examples
        for example in ExampleCircuit:
            example_path = self.example_circuits_dir / example.value
            # Could be directory or file
            example_file = example_path.with_suffix(".py")
            exists = example_path.is_dir() or example_file.exists()
            results[f"example:{example.value}"] = exists

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

        # Add section about the base circuit
        readme += f"""## 📁 Base Circuit: {config.base_circuit.display_name}

**Difficulty:** {config.base_circuit.difficulty}

{config.base_circuit.description}

The main circuit file is `circuit-synth/main.py`.

"""

        # Add section about examples if any
        if config.has_examples():
            readme += """## 📚 Example Circuits Included

This project includes additional example circuits in `circuit-synth/examples/`:

"""
            for example in config.examples:
                readme += f"- **{example.display_name}** ({example.difficulty}): {example.description}\n"

            readme += "\nYou can run any example circuit independently or use them as reference for your own designs.\n\n"

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

        # Add info about base circuit
        claude_md += f"""## 📝 Base Circuit

**Circuit Type:** {config.base_circuit.display_name}
**Difficulty:** {config.base_circuit.difficulty}

{config.base_circuit.description}

The main circuit is in `circuit-synth/main.py`.

"""

        # Add examples info if any
        if config.has_examples():
            claude_md += """## 📚 Example Circuits

This project includes example circuits for reference:

"""
            for example in config.examples:
                claude_md += f"- **{example.display_name}**: {example.description}\n"

            claude_md += "\nThese examples are in `circuit-synth/examples/` and can be used as reference or starting points.\n\n"

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
