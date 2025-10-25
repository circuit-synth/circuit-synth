#!/usr/bin/env python3
"""
Script to fix test imports: Replace Resistor/Capacitor/Inductor/Diode with Component
"""
import re
from pathlib import Path

# Test files to fix
test_files = [
    "tests/bidirectional/test_phase4_nets_connectivity.py",
    "tests/bidirectional/test_phase5_hierarchical_circuits.py",
    "tests/bidirectional/test_phase6_preservation.py",
    "tests/bidirectional/test_phase8_idempotency_stress.py",
    "tests/bidirectional/test_phase9_performance.py",
]

# Component type to symbol mapping
component_mappings = {
    'Resistor': ('Device:R', 'Resistor_SMD:R_0603_1608Metric'),
    'Capacitor': ('Device:C', 'Capacitor_SMD:C_0603_1608Metric'),
    'Inductor': ('Device:L', 'Inductor_SMD:L_0603_1608Metric'),
    'Diode': ('Device:D', 'Diode_SMD:D_0603_1608Metric'),
}

def fix_imports(content):
    """Fix import statements to use Component instead of specific component types"""
    # Pattern: from circuit_synth import Resistor, Capacitor, etc.
    pattern = r'from circuit_synth import ([^#\n]+)'

    def replace_import(match):
        imports = match.group(1).strip()
        # Remove component type classes, keep Net, Component, circuit
        imports_list = [i.strip() for i in imports.split(',')]
        keep_imports = []
        has_component_types = False

        for imp in imports_list:
            if imp in ['Resistor', 'Capacitor', 'Inductor', 'Diode']:
                has_component_types = True
            else:
                keep_imports.append(imp)

        if has_component_types:
            # Add Component if not already there
            if 'Component' not in keep_imports:
                keep_imports.insert(0, 'Component')
            # Ensure Net is there for connections
            if 'Net' not in keep_imports and 'Net' not in imports:
                keep_imports.append('Net')

        return f"from circuit_synth import {', '.join(keep_imports)}"

    content = re.sub(pattern, replace_import, content)
    return content

def fix_component_instantiation(content, comp_type, symbol, footprint):
    """Fix component instantiation to use Component class"""
    # Pattern: r1 = Resistor("R1", value="10k")
    # Or: r1 = Resistor("R1", value="10k", footprint=...)

    # Basic pattern: ComponentType(ref, value=...)
    pattern1 = rf'(\w+)\s*=\s*{comp_type}\s*\(\s*"([^"]+)"\s*,\s*value\s*=\s*"([^"]+)"\s*\)'

    def replace1(match):
        var_name = match.group(1)
        ref = match.group(2)
        value = match.group(3)
        return f'''{var_name} = Component(
                symbol="{symbol}",
                ref="{ref}",
                value="{value}",
                footprint="{footprint}"
            )'''

    content = re.sub(pattern1, replace1, content)

    # Pattern with existing footprint: ComponentType(ref, value=..., footprint=...)
    pattern2 = rf'(\w+)\s*=\s*{comp_type}\s*\(\s*"([^"]+)"\s*,\s*value\s*=\s*"([^"]+)"\s*,\s*footprint\s*=\s*"([^"]+)"\s*\)'

    def replace2(match):
        var_name = match.group(1)
        ref = match.group(2)
        value = match.group(3)
        existing_footprint = match.group(4)
        return f'''{var_name} = Component(
                symbol="{symbol}",
                ref="{ref}",
                value="{value}",
                footprint="{existing_footprint}"
            )'''

    content = re.sub(pattern2, replace2, content)

    return content

def process_file(filepath):
    """Process a single test file"""
    print(f"Processing {filepath}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Fix imports first
    content = fix_imports(content)

    # Fix component instantiations
    for comp_type, (symbol, footprint) in component_mappings.items():
        content = fix_component_instantiation(content, comp_type, symbol, footprint)

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"  ✅ Fixed {filepath}")

def main():
    repo_root = Path(__file__).parent.parent

    for test_file in test_files:
        filepath = repo_root / test_file
        if filepath.exists():
            process_file(filepath)
        else:
            print(f"⚠️  File not found: {filepath}")

    print("\n✅ All files processed!")

if __name__ == "__main__":
    main()
