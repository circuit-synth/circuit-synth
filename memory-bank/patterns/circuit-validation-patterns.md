# Circuit Validation Patterns

## Core Validation Workflow
```python
from circuit_synth.validation import validate_and_improve_circuit, get_circuit_design_context

# Standard validation pattern
code, is_valid, status = validate_and_improve_circuit(circuit_code)
if is_valid:
    print(f"✅ {status}")
else:
    print(f"⚠️ {status}")
```

## Context-Aware Generation Pattern
```python
# Get context for specific circuit type
context = get_circuit_design_context("esp32")  # or "power", "usb", "analog"

# Use context in generation prompts
enhanced_prompt = f"""
{context}

Generate circuit code for: {user_request}
"""
```

## Enhanced Agent Integration
```python
from circuit_synth.claude_integration.enhanced_circuit_agent import ValidatedCircuitGenerator

generator = ValidatedCircuitGenerator()
validated_circuit = await generator.generate_validated_circuit(prompt, circuit_type)
```

## Common Validation Issues Fixed
- Missing `from circuit_synth import Component, Net, circuit`
- Component/Net classes used without proper imports
- @circuit decorator without import
- Syntax errors in circuit definitions
- Runtime execution failures

## Circuit Type Contexts Available
- `general` - Basic circuit patterns and best practices
- `power` - Power supply design specifics (regulators, decoupling)
- `mcu`/`stm32`/`esp32` - Microcontroller design patterns
- `usb` - USB interface design with protection
- `analog` - Analog circuit design considerations