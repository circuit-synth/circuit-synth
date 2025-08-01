# Claude Instructions for ESP32-S3 Development Board Example

## Project Overview
Complete ESP32-S3 development board demonstrating circuit-synth capabilities. This is the primary example for learning circuit-synth and serves as a reference for development board design.

## Development Commands
```bash
# Run the example
cd circuit-synth
python main.py

# Check generated files
ls ../kicad_project/

# Test and validate
uv run pytest --cov=circuit_synth

# Format code
black circuit-synth/
```

## Design Features
This example demonstrates:
- Modern ESP32-S3 microcontroller integration
- USB-C connector for power and programming
- Proper power regulation (5V → 3.3V)
- Status LEDs with current limiting
- Reset circuit with pull-up resistor
- Decoupling capacitors for clean power
- Test points for debugging
- Professional component selection

## Design Constraints
- Use ESP32-S3-MINI-1 for integrated antenna
- USB-C for modern connectivity standards
- Linear regulator for simplicity (suitable for development board power levels)
- SMD components for professional appearance
- JLCPCB-compatible components for manufacturability

## Testing Notes
- Verify USB-C power delivery (5V input)
- Check 3.3V regulation under load
- Test ESP32-S3 programming interface via USB
- Validate WiFi/Bluetooth functionality
- Confirm LED operation (power always on, user GPIO-controlled)
- Test reset button functionality

## Manufacturing Notes
- All components available on JLCPCB
- Standard 0603/0805 passive components
- Through-hole components avoided for automated assembly
- Proper footprint selection for hand soldering (if needed)