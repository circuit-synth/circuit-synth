#!/usr/bin/env python3
"""Debug: Check if circuit hierarchy is created."""

from hierarchical_circuit import hierarchical_circuit

print("=" * 80)
print("🔍 CYCLE 1: Checking Circuit Hierarchy")
print("=" * 80)

circuit_obj = hierarchical_circuit()

print(f"\nCircuit name: {circuit_obj.name}")
print(f"Circuit type: {type(circuit_obj)}")
print(f"Has child_instances attr: {hasattr(circuit_obj, 'child_instances')}")

if hasattr(circuit_obj, 'child_instances'):
    print(f"child_instances type: {type(circuit_obj.child_instances)}")
    print(f"child_instances value: {circuit_obj.child_instances}")
    print(f"Number of children: {len(circuit_obj.child_instances)}")

    if circuit_obj.child_instances:
        for i, child in enumerate(circuit_obj.child_instances):
            print(f"\n  Child {i}:")
            print(f"    Type: {type(child)}")
            print(f"    Data: {child}")
else:
    print("❌ child_instances attribute does NOT exist!")

print(f"\nComponents in circuit: {len(circuit_obj.components)}")
for comp_ref in circuit_obj.components:
    print(f"  - {comp_ref}")

print(f"\n_subcircuits attr exists: {hasattr(circuit_obj, '_subcircuits')}")
if hasattr(circuit_obj, '_subcircuits'):
    print(f"_subcircuits type: {type(circuit_obj._subcircuits)}")
    print(f"_subcircuits length: {len(circuit_obj._subcircuits)}")
    print(f"_subcircuits: {circuit_obj._subcircuits}")

    for i, sub in enumerate(circuit_obj._subcircuits):
        print(f"\n  Subcircuit {i}:")
        print(f"    Name: {sub.name if hasattr(sub, 'name') else 'NO NAME'}")
        print(f"    Type: {type(sub)}")
        if hasattr(sub, 'components'):
            print(f"    Components: {len(sub.components)}")
