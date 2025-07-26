# KiCad Project Notes Management System

The Project Notes Management System provides a structured way to store and manage project-specific data for KiCad projects, including datasheets, component specifications, analysis results, and user notes.

## Overview

When working with a KiCad project, the system creates a `circuit_synth_notes/` folder within the project directory with the following structure:

```
circuit_synth_notes/
├── datasheets/           # PDF datasheets
├── component_cache/      # JSON files with extracted component specs
├── analysis_history/     # Previous analysis results
├── user_notes/          # User annotations and notes
└── config.json          # Configuration and metadata
```

## Usage

### Basic Usage

```python
from circuit_synth.kicad import ProjectNotesManager

# Initialize for a KiCad project
manager = ProjectNotesManager("/path/to/kicad/project")

# Create the notes folder structure
manager.ensure_notes_folder()
```

### Component Caching

Store detailed component specifications:

```python
from circuit_synth.llm_analysis.models.component_cache import (
    CachedComponent, ComponentSpecs, ElectricalSpecs, ThermalSpecs
)

# Create component specs
component = CachedComponent(
    component_id="U1",
    part_number="ESP32-S3-MINI-1",
    manufacturer="Espressif",
    description="WiFi+BLE MCU Module",
    specs=ComponentSpecs(
        electrical=ElectricalSpecs(
            voltage_ratings={"min": 3.0, "nominal": 3.3, "max": 3.6},
            current_ratings={"active": 0.240, "sleep": 0.00001}
        ),
        thermal=ThermalSpecs(
            operating_temp_min=-40,
            operating_temp_max=85
        ),
        features=["Dual-core", "WiFi", "Bluetooth 5.0"]
    ),
    confidence="high",
    source="datasheet"
)

# Save to cache
manager.save_component_specs(component)

# Retrieve later
cached = manager.get_component_specs("U1")
```

### Datasheet Management

```python
# Save a datasheet PDF
datasheet_path = manager.save_datasheet(
    pdf_path="/path/to/datasheet.pdf",
    component_id="U1",
    part_number="ESP32-S3-MINI-1"
)

# Get datasheet path
pdf = manager.get_datasheet_path("U1")
```

### Analysis Results

Store and retrieve circuit analysis results:

```python
# Save analysis results
analysis_data = {
    "circuit_type": {"types": ["microcontroller"], "confidence": "high"},
    "subcircuits": {...},
    "recommendations": [...]
}

path = manager.save_analysis_result(analysis_data, "circuit_analysis")

# Retrieve analysis history
history = manager.get_analysis_history(
    analysis_type="circuit_analysis",
    limit=10
)
```

### User Notes

Add annotations and design notes:

```python
# Add a design note
note_path = manager.add_user_note(
    title="Design Review Notes",
    content="## Key Decisions\n\n- Selected ESP32 for WiFi capability...",
    component_id="U1"  # Optional component reference
)
```

### Export Summary

Get an overview of cached data:

```python
summary = manager.export_cache_summary()
print(f"Cached components: {summary['statistics']['cached_components']}")
print(f"Datasheets: {summary['statistics']['datasheets']}")
print(f"Analysis records: {summary['statistics']['analyses']}")
```

## Integration with Circuit Analysis

The project notes system integrates seamlessly with the circuit analysis workflow:

```python
# See examples/analyze_with_notes.py for complete example
from circuit_synth.kicad import ProjectNotesManager
from circuit_synth.scripts.llm_circuit_analysis import two_phase_analyze_circuits

# Analyze circuit and automatically store results
async def analyze_with_notes(project_path):
    manager = ProjectNotesManager(project_path)
    manager.ensure_notes_folder()
    
    # Load and analyze circuit
    circuit_json = load_circuit_from_kicad(project_path)
    results = await two_phase_analyze_circuits([circuit_json])
    
    # Store results
    manager.save_analysis_result(results[0], "circuit_analysis")
    
    # Cache component information from analysis
    # ... (see full example)
```

## Features

- **Automatic folder creation**: Creates organized folder structure on first use
- **Component caching**: Store detailed specifications with Pydantic validation
- **Datasheet management**: Organize PDF datasheets with proper naming
- **Analysis history**: Track all analysis runs with timestamps
- **User notes**: Add markdown-formatted notes and annotations
- **Thread-safe**: Safe for concurrent access in parallel analysis
- **Export capabilities**: Generate summaries and statistics

## Data Models

The system uses Pydantic models for data validation:

- `ComponentSpecs`: Complete specifications (electrical, thermal, mechanical)
- `CachedComponent`: Component with specs, metadata, and confidence levels
- `ComponentCache`: Collection of cached components for a project

See `src/circuit_synth/llm_analysis/models/component_cache.py` for details.

## Examples

- `examples/test_project_notes.py`: Basic functionality demonstration
- `examples/analyze_with_notes.py`: Integration with circuit analysis workflow

## Future Enhancements

- Datasheet text extraction and indexing
- Component search across projects
- Version control for component specs
- Integration with component databases
- Automatic datasheet fetching from URLs