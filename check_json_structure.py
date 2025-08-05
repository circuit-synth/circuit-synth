#!/usr/bin/env python3
import json
import tempfile
from circuit_synth.core.netlist_exporter import NetlistExporter

# Load the test circuit
exec(open('test_hierarchical_resistors.py').read())

# Create the circuit
circuit = main_circuit()

# Generate JSON with the exporter
exporter = NetlistExporter()
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json_str = exporter.generate_json_netlist(circuit)
    f.write(json_str)
    print(f"JSON written to: {f.name}")
    
    # Parse and analyze
    data = json.loads(json_str)
    
    print("\nTop-level structure:")
    print(f"  - name: {data.get('name', 'N/A')}")
    print(f"  - version: {data.get('version', 'N/A')}")
    print(f"  - components: {len(data.get('components', {}))}")
    print(f"  - nets: {len(data.get('nets', {}))}")
    print(f"  - subcircuits: {len(data.get('subcircuits', {}))}")
    
    print("\nSubcircuits:")
    for sub_name, sub_data in data.get('subcircuits', {}).items():
        print(f"\n  {sub_name}:")
        if isinstance(sub_data, list):
            print(f"    Instances: {len(sub_data)}")
            for inst in sub_data:
                print(f"      - {inst.get('instance_label', 'N/A')}")
                print(f"        instance_nets: {inst.get('instance_nets', 'N/A')}")
        else:
            print(f"    Type: {type(sub_data)}")