# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation and Setup

**Primary method (recommended) - using uv:**
```bash
# Install the project in development mode
uv pip install -e ".[dev]"

# Install dependencies
uv sync
```

**Alternative method - using pip:**
```bash
# If uv is not available
pip install -e ".[dev]"
```

### Code Quality and Testing
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/

# Run tests (recommended with uv)
uv run pytest

# Run tests with coverage
uv run pytest --cov=circuit_synth

# Alternative with pip
pytest
pytest --cov=circuit_synth
```

### Building and Distribution

**Using uv (recommended):**
```bash
# Build package
uv build

# Install locally in development mode
uv pip install -e .
```

**Using traditional tools:**
```bash
# Build package
python -m build

# Install locally
pip install -e .
```

## Agent Workflow

This repository uses a structured agent workflow for handling complex tasks. Always start in **orchestrator** mode, which coordinates other specialized agents.

### Standard Workflow

1. **orchestrator**: Entry point for all complex tasks
   - Analyzes the overall request and breaks it down into coordinated subtasks
   - Delegates specialized work to appropriate agents
   - Manages dependencies and ensures proper sequencing

2. **architect**: Planning and analysis phase
   - Breaks down complex or unclear tasks into actionable steps
   - Gathers requirements and asks clarifying questions
   - Creates structured todo lists and implementation plans
   - Provides architectural guidance and design decisions

3. **code**: Implementation phase  
   - Performs actual coding changes following best practices
   - Reviews code against SOLID, KISS, YAGNI, and DRY principles
   - Implements solutions based on architect's plans
   - Ensures code quality and maintainability

### When to Use Each Agent

- **Start with orchestrator** for any multi-step or complex request
- Use **architect** when you need to plan, analyze requirements, or break down tasks
- Use **code** when you need to implement, review, or refactor code
- Let **orchestrator** coordinate the handoffs between agents

### Example Flow

```
User Request: "Add a new placement algorithm for PCB components"

orchestrator → architect (analyze requirements, plan implementation)
architect → code (implement the algorithm following the plan)  
orchestrator → (coordinate testing, documentation, integration)
```

## Repository Structure

### CRITICAL: Two Circuit-Synth Repositories

There are **TWO** distinct circuit-synth repositories that you must be aware of:

1. **Private Repository**: `Circuit_Synth2/` (closed source)
   - This is the original project where most functionality was initially developed
   - Contains the complete, mature implementation
   - Located at `/Users/shanemattner/Desktop/Circuit_Synth2/`
   - This is the private, closed-source version

2. **Open Source Repository**: `Circuit_Synth2/submodules/circuit-synth/` (open source)
   - This is the open-source version created as a submodule
   - Some functionality from the private repo was **not copied over properly**
   - Located at `/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth/`
   - **This is where all new development should happen**

### Development Guidelines

- **ALWAYS work in the open source repo**: `/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth/`
- When referencing functionality, be explicit about which repo you're looking at
- If functionality exists in the private repo but is missing from the open source repo, it needs to be ported over
- **Never make changes to the private repo** - all development goes in the open source version
- Keep track of which repo contains which functionality to avoid confusion

### Repository References

When discussing code or functionality:
- **Private repo**: Reference as "private Circuit_Synth2 repo" or "closed source repo"
- **Open source repo**: Reference as "open source circuit-synth repo" or "submodule repo"
- **Default assumption**: Unless specified otherwise, all work should be done in the **open source repo**

## Annotation System

The circuit-synth repository includes a comprehensive annotation system that enables automatic and manual documentation of Python-generated circuit designs. This system provides seamless integration between Python code documentation and KiCad schematic annotations.

### Overview

The annotation system consists of three main components:

1. **Decorator-based automatic annotations** - Extracts docstrings from decorated functions
2. **Manual annotation classes** - Provides structured annotation objects for custom documentation
3. **JSON export pipeline** - Serializes annotations to JSON for KiCad integration

### Key Components

#### 1. Decorator Flags (`@enable_comments`)

The `@enable_comments` decorator automatically extracts function docstrings and converts them into schematic annotations:

```python
from circuit_synth.annotations import enable_comments

@enable_comments
def create_amplifier_stage():
    """
    Creates a common-emitter amplifier stage.
    
    This circuit provides voltage amplification with a gain of approximately 100.
    Input impedance: ~1kΩ, Output impedance: ~3kΩ
    """
    # Circuit implementation...
    pass
```

#### 2. Manual Annotation Classes

Three annotation classes provide structured documentation capabilities:

**TextBox Annotations:**
```python
from circuit_synth.annotations import TextBox

# Create a text box annotation
note = TextBox(
    text="High-frequency bypass capacitor for supply rail filtering",
    position=(50, 30),
    size=(40, 15),
    style="note"
)
```

**TextProperty Annotations:**
```python
from circuit_synth.annotations import TextProperty

# Add property annotation to a component
component_note = TextProperty(
    text="R1: Sets bias current to 2.5mA",
    position=(10, 5),
    style="property"
)
```

**Table Annotations:**
```python
from circuit_synth.annotations import Table

# Create a specifications table
specs_table = Table(
    headers=["Parameter", "Min", "Typical", "Max", "Unit"],
    rows=[
        ["Supply Voltage", "3.0", "3.3", "3.6", "V"],
        ["Gain", "95", "100", "105", "dB"],
        ["Bandwidth", "1", "10", "20", "MHz"]
    ],
    position=(100, 50),
    title="Amplifier Specifications"
)
```

#### 3. JSON Export Pipeline

The annotation system includes a complete serialization pipeline that converts annotations to JSON format compatible with KiCad:

```python
from circuit_synth.annotations import export_annotations_to_json

# Export all annotations from a design
annotations = [text_box, component_note, specs_table]
json_output = export_annotations_to_json(annotations, "amplifier_design")
```

### Usage Examples

#### Automatic Annotation Workflow

1. **Decorate functions** with `@enable_comments` to enable automatic docstring extraction
2. **Write descriptive docstrings** following standard Python conventions
3. **Run the design generation** - annotations are captured automatically
4. **Export to JSON** for KiCad integration

```python
@enable_comments
def design_filter_circuit():
    """
    Second-order Butterworth low-pass filter.
    
    Cutoff frequency: 1kHz
    Roll-off: -40dB/decade above cutoff
    Input/Output impedance: 50Ω
    """
    # Implementation creates filter components
    return circuit
```

#### Manual Annotation Workflow

1. **Create annotation objects** during circuit generation
2. **Position annotations** relative to components or absolute coordinates
3. **Collect annotations** in a list or annotation manager
4. **Export to JSON** alongside automatic annotations

```python
def create_power_supply():
    # Create circuit components
    
    # Add manual annotations
    annotations = [
        TextBox(
            text="Regulation: ±0.1% line/load",
            position=(75, 25),
            style="specification"
        ),
        Table(
            headers=["Rail", "Voltage", "Current"],
            rows=[
                ["+5V", "5.00V", "2.0A"],
                ["-5V", "-5.00V", "0.5A"],
                ["+12V", "12.00V", "1.0A"]
            ],
            position=(120, 60),
            title="Power Rail Specifications"
        )
    ]
    
    return circuit, annotations
```

### Technical Implementation Details

#### Data Flow Architecture

The annotation system implements a robust data flow from Python generation to KiCad integration:

1. **Collection Phase**: Annotations are gathered during circuit generation
2. **Validation Phase**: Annotation objects are validated for completeness
3. **Serialization Phase**: Objects are converted to JSON with proper formatting
4. **Export Phase**: JSON is written with KiCad-compatible structure

#### S-expression Formatting Fixes

The system includes comprehensive S-expression formatting with proper string escaping for KiCad compatibility:

- **String Escaping**: Handles special characters in annotation text
- **Coordinate Formatting**: Ensures proper numeric formatting for positions
- **Style Mapping**: Maps annotation styles to KiCad text properties
- **Hierarchical Structure**: Maintains proper S-expression nesting

```python
# Example of formatted S-expression output
(text "High-frequency bypass capacitor" (at 50.8 76.2 0)
  (effects (font (size 1.27 1.27)) (justify left))
  (uuid "annotation-uuid-here")
)
```

#### JSON Schema Structure

The export pipeline follows a consistent JSON schema:

```json
{
  "design_name": "amplifier_design",
  "timestamp": "2025-01-27T10:30:00Z",
  "annotations": [
    {
      "type": "textbox",
      "id": "unique-id",
      "text": "annotation content",
      "position": {"x": 50, "y": 30},
      "size": {"width": 40, "height": 15},
      "style": "note",
      "metadata": {
        "source": "automatic|manual",
        "function": "function_name"
      }
    }
  ]
}
```

### Integration with KiCad

The annotation system provides seamless integration with KiCad schematics:

1. **JSON Import**: KiCad can import the generated JSON files
2. **S-expression Compatibility**: All formatting follows KiCad standards
3. **Layer Management**: Annotations are placed on appropriate schematic layers
4. **UUID Tracking**: Each annotation receives a unique identifier for updates

This implementation provides a complete end-to-end solution for documenting Python-generated circuit designs with both automatic and manual annotation capabilities.
