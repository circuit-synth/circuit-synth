"""
Template Manager for circuit-synth project creation

Handles loading and managing circuit templates for base circuits and examples.
"""

import shutil
from pathlib import Path
from typing import Dict, Optional

from .project_config import Circuit, CircuitTemplate, ProjectConfig


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

        return template_file.read_text(encoding="utf-8")

    def copy_circuit_to_project(
        self, circuit: Circuit, project_path: Path, is_first: bool = False
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
        target_file.write_text(circuit_code, encoding="utf-8")

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

## Quick Start

```bash
# Run your circuit
uv run python circuit-synth/main.py
```

This will generate KiCad project files that you can open in KiCad.

"""

        # Add section about included circuits
        if config.has_circuits():
            readme += f"""## Included Circuits ({len(config.circuits)})

This project includes the following circuit templates:

"""
            for idx, circuit in enumerate(config.circuits, 1):
                filename = "main.py" if idx == 1 else f"{circuit.value}.py"
                readme += f"{idx}. **{circuit.display_name}** ({circuit.difficulty}): {circuit.description}\n"
                readme += f"   - File: `circuit-synth/{filename}`\n\n"

            readme += "\nYou can run any circuit file independently or use them as reference for your own designs.\n\n"

        # Add circuit-synth basics
        readme += """## Circuit-Synth Basics

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
        generate_pcb=False
    )
```

### Manufacturing File Generation

All circuit templates automatically generate manufacturing files:

```python
# After generate_kicad_project(), templates also generate:

# 1. BOM (Bill of Materials) - CSV format for component ordering
bom_result = circuit_obj.generate_bom(project_name="my_project")

# 2. PDF Schematic - Documentation and review
pdf_result = circuit_obj.generate_pdf_schematic(project_name="my_project")
```

**Generated files:**
- `my_project/my_project_bom.csv` - Component list with references and values
- `my_project/my_project_schematic.pdf` - Printable schematic documentation

"""

        # Add documentation links
        readme += """## Documentation

- Circuit-Synth: https://circuit-synth.readthedocs.io
- KiCad: https://docs.kicad.org

"""

        # Add Claude agents section if included
        if config.include_agents:
            readme += """## AI-Powered Design with Claude Code

This project ships Claude Code helpers for circuit design:

- **`design-circuit` skill** — describe a circuit in natural language and let
  Claude write the circuit-synth Python, generate the KiCad schematic, simulate,
  and refine it (`.claude/skills/design-circuit/`).
- **`tools/find_symbol.py`** — look up exact KiCad symbol/footprint ids:
  `uv run python tools/find_symbol.py <query> [--footprints]`.
- **`tools/simulate_example.py`** — known-good DC SPICE reference: runs a DC
  operating-point analysis via ngspice (auto-uses KiCad's bundled `ngspice.dll`
  on Windows). Copy its pattern to verify your own circuit's node voltages.
- **`tools/simulate_filter.py`** — known-good AC-sweep reference: an op-amp
  low-pass filter driven by a `Simulation_SPICE:VSIN` source (AC magnitude 1 V);
  prints passband gain, -3 dB cutoff, and roll-off via
  `circuit.simulate().ac_analysis(...)` and the `cutoff_frequency`/`bode` helpers.
- **kicad-sch-api MCP server** (optional) — enable with
  `uv add mcp-kicad-sch-api` (config in `.mcp.json`).

Declare simulation sources with KiCad's real `Simulation_SPICE` symbols —
`Simulation_SPICE:VDC` for a DC supply, `Simulation_SPICE:VSIN` for an AC/transient
stimulus (NOT the fictitious `Device:V`). Pin 1 is `+`, pin 2 is `-`.

"""

        # Add next steps
        readme += """## Next Steps

1. Open `circuit-synth/main.py` and review the base circuit
2. Run the circuit to generate KiCad files
3. Open the generated `.kicad_pro` file in KiCad
4. Modify the circuit or create your own designs

**Happy circuit designing!**
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

## Project Overview

This is a **circuit-synth project** for PCB design with Python code.

"""

        # Add info about included circuits
        if config.has_circuits():
            claude_md += f"""## Included Circuits ({len(config.circuits)})

This project includes the following circuit templates:

"""
            for idx, circuit in enumerate(config.circuits, 1):
                filename = "main.py" if idx == 1 else f"{circuit.value}.py"
                claude_md += (
                    f"{idx}. **{circuit.display_name}** ({circuit.difficulty})\n"
                )
                claude_md += f"   - {circuit.description}\n"
                claude_md += f"   - File: `circuit-synth/{filename}`\n\n"

            claude_md += "You can modify these circuits or use them as reference for creating new designs.\n\n"

        # Add available tools
        if config.include_agents:
            claude_md += """## AI Tooling

This project ships these Claude Code helpers:

- **`design-circuit` skill** (`.claude/skills/design-circuit/`) — iterative loop
  to design a circuit from a prompt: write circuit-synth Python, generate the
  KiCad schematic, simulate, and refine.
- **`tools/find_symbol.py`** — resolve exact KiCad `Lib:Symbol` / footprint ids:
  `uv run python tools/find_symbol.py <query> [--footprints]`.
- **`tools/simulate_example.py`** — known-good SPICE reference (DC operating
  point via ngspice; auto-uses KiCad's bundled `ngspice.dll` on Windows). Copy
  its pattern to verify node voltages: `circuit.simulate().operating_point()`.
- **`tools/simulate_filter.py`** — known-good AC-sweep reference (op-amp low-pass
  filter). Copy its pattern for frequency-domain checks:
  `circuit.simulate().ac_analysis(start_hz, stop_hz, points)` then
  `.cutoff_frequency("NET")` / `.passband_gain_db("NET")` / `.bode("NET")`.
- **kicad-sch-api MCP server** (optional) — direct schematic tools; enable with
  `uv add mcp-kicad-sch-api` (config in `.mcp.json`).

Declare simulation sources with real `Simulation_SPICE` symbols:
`Simulation_SPICE:VDC` (DC supply) or `Simulation_SPICE:VSIN` (AC/transient
stimulus, carries AC magnitude 1 V) — NOT the fictitious `Device:V`. Pin 1 = `+`,
pin 2 = `-`.

"""

        # Add workflow guidance
        claude_md += """## Development Workflow

1. **Component Selection**: Find KiCad symbols/footprints (browse
   `<KiCad>/share/kicad/symbols` or use the KiCad symbol editor)
2. **Circuit Design**: Write Python code using circuit-synth
3. **Generate KiCad**: Run the Python file to create KiCad project
4. **Manufacturing Files**: Templates automatically generate BOM and PDF
5. **Validate**: Open in KiCad and verify the design

## Quick Reference

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

### Manufacturing Exports
```python
# All templates automatically generate manufacturing files:
circuit_obj.generate_bom(project_name="my_project")          # BOM CSV
circuit_obj.generate_pdf_schematic(project_name="my_project")  # PDF schematic
```

**Output:**
- BOM: `my_project/my_project_bom.csv`
- PDF: `my_project/my_project_schematic.pdf`

---

**This project is optimized for AI-powered circuit design with Claude Code!**
"""

        return claude_md
