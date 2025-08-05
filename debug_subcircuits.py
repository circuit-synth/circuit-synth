#!/usr/bin/env python3
"""Debug script to understand subcircuit parameters"""

from circuit_synth import Circuit, Component, Net, circuit
import json

# Load the test circuit
exec(open('test_hierarchical_resistors.py').read())

# Generate the circuit
circuit = main_circuit()

# Convert to JSON to inspect structure
circuit_json = circuit.to_dict()

# Save full JSON for inspection
with open('debug_circuit.json', 'w') as f:
    json.dump(circuit_json, f, indent=2)

print("Full circuit JSON saved to debug_circuit.json")

# Look for signal_processing subcircuit info
if 'subcircuits' in circuit_json:
    for name, data in circuit_json['subcircuits'].items():
        if 'signal_processing' in name:
            print(f"\nFound signal_processing: {name}")
            print(f"Type: {type(data)}")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        print(f"  Instance: {item.get('instance_label', 'no label')}")
                        print(f"  Parameters: {item.get('parameters', 'no parameters')}")
                        print(f"  Instance nets: {item.get('instance_nets', 'no instance_nets')}")