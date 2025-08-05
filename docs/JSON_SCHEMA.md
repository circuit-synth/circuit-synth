# Circuit-Synth JSON Schema Documentation

## Overview

This document describes the JSON schema used by circuit-synth as the canonical intermediate representation for circuit data. The schema supports hierarchical circuit designs with full component and connectivity information.

## Schema Structure

### Top-Level Circuit Object

```json
{
  "name": "string",                 // Required: Circuit name
  "description": "string",          // Optional: Circuit description
  "tstamps": "string",             // Optional: KiCad timestamp path
  "source_file": "string",         // Optional: Source schematic file
  "components": {},                // Component dictionary (see below)
  "nets": {},                      // Net connectivity (see below)
  "subcircuits": [],               // Array of nested circuits
  "annotations": []                // Optional: Circuit annotations
}
```

### Components Object

Components are stored as a dictionary with reference designators as keys:

```json
"components": {
  "U1": {
    "symbol": "string",           // Required: KiCad symbol library reference
    "ref": "string",              // Required: Reference designator
    "value": "string",            // Optional: Component value (e.g., "10k", "100nF")
    "footprint": "string",        // Optional: KiCad footprint library reference
    "datasheet": "string",        // Optional: Datasheet URL
    "description": "string",      // Optional: Component description
    "properties": {},             // Optional: Additional properties
    "tstamps": "string",         // Optional: KiCad timestamp
    "pins": []                   // Array of pin definitions (see below)
  }
}
```

### Pin Definition

Each pin in the component's pins array:

```json
{
  "pin_id": "string|number",      // Pin identifier (number or string)
  "name": "string",               // Pin name (e.g., "VCC", "GND")
  "number": "string",             // Pin number on package
  "func": "string",               // Pin function/type (e.g., "passive", "power_in")
  "unit": "number",               // Unit number (for multi-unit symbols)
  "x": "number",                  // X coordinate (schematic position)
  "y": "number",                  // Y coordinate (schematic position)
  "length": "number",             // Pin length
  "orientation": "number"         // Pin orientation (degrees)
}
```

### Nets Object

Nets define electrical connections between component pins:

```json
"nets": {
  "VCC_3V3": [                    // Net name as key
    {
      "component": "U1",          // Component reference
      "pin_id": 3                 // Pin ID (number format)
    },
    {
      "component": "R1",          // Another component
      "pin": {                    // Alternative pin format (object)
        "number": "1",
        "name": "~",
        "type": "passive"
      }
    }
  ]
}
```

### Subcircuits Array

Subcircuits are nested circuit definitions with the same structure:

```json
"subcircuits": [
  {
    "name": "Power_Supply",
    "description": "5V to 3.3V regulation",
    "components": {
      // Same component structure
    },
    "nets": {
      // Same net structure
    },
    "subcircuits": [
      // Can nest further
    ]
  }
]
```

### Annotations Array (Optional)

Circuit documentation and annotations:

```json
"annotations": [
  {
    "type": "textbox",
    "id": "unique-id",
    "text": "Design note or specification",
    "position": {"x": 50, "y": 30},
    "size": {"width": 40, "height": 15},
    "style": "note",
    "metadata": {
      "source": "automatic",
      "function": "create_power_supply"
    }
  }
]
```

## Complete Example

```json
{
  "name": "ESP32_Dev_Board",
  "description": "ESP32 development board with USB and power",
  "components": {
    "U1": {
      "symbol": "RF_Module:ESP32-C6-MINI-1",
      "ref": "U1",
      "footprint": "RF_Module:ESP32-C6-MINI-1",
      "description": "ESP32-C6 WiFi/BLE module",
      "pins": [
        {
          "pin_id": 0,
          "name": "GND",
          "number": "1",
          "func": "power_in",
          "unit": 1,
          "x": 0,
          "y": -5.08,
          "length": 2.54,
          "orientation": 0
        }
      ]
    },
    "C1": {
      "symbol": "Device:C",
      "ref": "C1",
      "value": "100nF",
      "footprint": "Capacitor_SMD:C_0603_1608Metric",
      "pins": [
        {"pin_id": 0, "name": "~", "number": "1", "func": "passive"},
        {"pin_id": 1, "name": "~", "number": "2", "func": "passive"}
      ]
    }
  },
  "nets": {
    "VCC_3V3": [
      {"component": "U1", "pin_id": 2},
      {"component": "C1", "pin_id": 0}
    ],
    "GND": [
      {"component": "U1", "pin_id": 0},
      {"component": "C1", "pin_id": 1}
    ]
  },
  "subcircuits": [
    {
      "name": "USB_Interface",
      "description": "USB-C connector with ESD protection",
      "components": {},
      "nets": {}
    }
  ]
}
```

## Pin Reference Formats

The schema supports two formats for pin references in nets:

### 1. Legacy Format (pin_id)
```json
{"component": "U1", "pin_id": 3}
```

### 2. Modern Format (pin object)
```json
{
  "component": "U1",
  "pin": {
    "number": "4",
    "name": "VDD",
    "type": "power_in"
  }
}
```

Both formats are supported for backward compatibility.

## Data Types

- **Strings**: UTF-8 encoded text
- **Numbers**: IEEE 754 double precision
- **Arrays**: Ordered lists
- **Objects**: Key-value pairs

## Validation Notes

1. **Required Fields**: `name` for circuits, `symbol` and `ref` for components
2. **Reference Uniqueness**: Component references must be unique within a circuit
3. **Pin Connectivity**: Pins referenced in nets must exist in component definitions
4. **Hierarchical Paths**: Subcircuits can be nested to any depth

## Usage with Circuit-Synth

### Export to JSON
```python
# Generate JSON from circuit
circuit.generate_json_netlist("my_circuit.json")

# Or get dictionary
circuit_dict = circuit.to_dict()
```

### Import from JSON
```python
from circuit_synth.io import load_circuit_from_json_file

# Load circuit from JSON file
circuit = load_circuit_from_json_file("my_circuit.json")

# Or from dictionary
from circuit_synth.io import load_circuit_from_dict
circuit = load_circuit_from_dict(circuit_dict)
```

## Version Compatibility

- **Current Version**: 1.0 (implicit, not versioned in files)
- **Backward Compatibility**: Maintained for all 0.x versions
- **Forward Compatibility**: New fields can be added without breaking older parsers