#!/usr/bin/env python3
"""
Test Rust backend with hierarchical circuit data.
"""

import json
import logging
import rust_kicad_schematic_writer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a hierarchical circuit structure similar to ESP32 example
hierarchical_data = {
    "name": "main",
    "components": {},  # Main circuit has no direct components
    "nets": {},  # Main circuit has no direct nets
    "subcircuits": [
        {
            "name": "USB_Port",
            "components": {
                "J1": {
                    "symbol": "Connector:USB_C_Receptacle_USB2.0",
                    "reference": "J1",
                    "value": "USB-C",
                    "position": {"x": 50.0, "y": 50.0},
                    "rotation": 0.0,
                    "pins": []
                },
                "R1": {
                    "symbol": "Device:R",
                    "reference": "R1",
                    "value": "5.1k",
                    "position": {"x": 70.0, "y": 50.0},
                    "rotation": 0.0,
                    "pins": []
                }
            },
            "nets": {
                "VBUS": {
                    "name": "VBUS",
                    "connected_pins": [
                        {"component_ref": "J1", "pin_id": "A4"},
                        {"component_ref": "R1", "pin_id": "1"}
                    ]
                }
            },
            "subcircuits": []
        },
        {
            "name": "Power_Supply",
            "components": {
                "U1": {
                    "symbol": "Regulator_Linear:AMS1117-3.3",
                    "reference": "U1",
                    "value": "AMS1117-3.3",
                    "position": {"x": 100.0, "y": 100.0},
                    "rotation": 0.0,
                    "pins": []
                },
                "C1": {
                    "symbol": "Device:C",
                    "reference": "C1",
                    "value": "10uF",
                    "position": {"x": 80.0, "y": 100.0},
                    "rotation": 0.0,
                    "pins": []
                }
            },
            "nets": {
                "VCC_3V3": {
                    "name": "VCC_3V3",
                    "connected_pins": [
                        {"component_ref": "U1", "pin_id": "2"},
                        {"component_ref": "C1", "pin_id": "1"}
                    ]
                }
            },
            "subcircuits": []
        }
    ]
}

# Configuration for Rust backend
config = {
    "paper_size": "A4",
    "generator": "rust_kicad_schematic_writer",
    "title": "Hierarchical Test Circuit",
    "version": "1.0"
}

print("Testing Rust backend with hierarchical circuit...")
print(f"  Main circuit: {hierarchical_data['name']}")
print(f"  Subcircuits: {len(hierarchical_data['subcircuits'])}")
for sc in hierarchical_data['subcircuits']:
    print(f"    - {sc['name']}: {len(sc['components'])} components, {len(sc['nets'])} nets")

try:
    # Test if Rust can handle hierarchical data
    logger.info("Calling Rust to generate hierarchical schematic...")
    
    # Try to generate schematic with Rust
    schematic_content = rust_kicad_schematic_writer.generate_schematic_from_python(
        hierarchical_data, config
    )
    
    print(f"\n✅ Rust successfully generated hierarchical schematic!")
    print(f"  Size: {len(schematic_content)} bytes")
    
    # Write to file
    with open("test_rust_hierarchical.kicad_sch", "w") as f:
        f.write(schematic_content)
    print(f"  Written to: test_rust_hierarchical.kicad_sch")
    
    # Show first few lines
    lines = schematic_content.split('\n')[:5]
    print("\n  First lines:")
    for line in lines:
        print(f"    {line}")
        
except Exception as e:
    print(f"\n❌ Rust failed with hierarchical data: {e}")
    import traceback
    traceback.print_exc()