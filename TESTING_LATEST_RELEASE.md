# Testing circuit-synth 0.10.13

Quick guide to test the latest release of circuit-synth with a simple voltage divider circuit.

## Prerequisites

- Python 3.12 or higher
- pip package manager
- Git (optional, for cloning)

## Installation

```bash
# Create a virtual environment
python3 -m venv test_venv
source test_venv/bin/activate  # On Windows: test_venv\Scripts\activate

# Install the latest circuit-synth release
pip install --upgrade circuit-synth==0.10.13
```

## Quick Test: Create a Voltage Divider Circuit

### Option 1: Run Interactive Test (Recommended)

```bash
# Create test directory
mkdir circuit_synth_test && cd circuit_synth_test

# Create test file
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""Test circuit-synth 0.10.13 with a voltage divider circuit"""

from circuit_synth import circuit, Component, Net

@circuit(name="voltage_divider")
def create_voltage_divider():
    """Create a simple voltage divider with 2 resistors"""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    r2 = Component(symbol="Device:R", ref="R2", value="10k")

    vcc = Net("VCC")
    gnd = Net("GND")
    mid = Net("MIDPOINT")

    r1[1] += vcc
    r1[2] += mid
    r2[1] += mid
    r2[2] += gnd

    return locals()

if __name__ == "__main__":
    circuit_obj = create_voltage_divider()

    print("=" * 60)
    print("Circuit-Synth 0.10.13 Test")
    print("=" * 60)
    print(f"Circuit: {circuit_obj.name}")
    print(f"Components: {len(circuit_obj._components)}")
    print(f"Nets: {len(circuit_obj.nets)}")

    # Generate KiCad project
    print("\nGenerating KiCad project...")
    result = circuit_obj.generate_kicad_project(
        project_name="voltage_divider_test",
        generate_pcb=True
    )

    if result.get("success"):
        print("✅ KiCad project generated successfully!")
        print(f"   Project: voltage_divider_test/")
    else:
        print("❌ Failed to generate KiCad project")

    # Generate BOM
    print("\nGenerating BOM...")
    try:
        bom = circuit_obj.generate_bom(project_name="voltage_divider_test")
        if bom.get("success"):
            print(f"✅ BOM generated with {bom.get('component_count')} components")
        else:
            print("⚠️  BOM generation skipped (kicad-cli may not be installed)")
    except Exception as e:
        print(f"⚠️  BOM generation skipped: {type(e).__name__}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
EOF

# Run the test
python main.py
```

### Option 2: Quick CLI Test

```bash
# Test installation and version
python -c "from circuit_synth import __version__; print(f'circuit-synth {__version__} installed')"

# Test basic import
python -c "from circuit_synth import Circuit, Component, Net; print('✅ Core classes imported successfully')"
```

## Expected Results

### Successful Test Output Should Show:
```
============================================================
Circuit-Synth 0.10.13 Test
============================================================
Circuit: voltage_divider
Components: 2
Nets: 3

Generating KiCad project...
✅ KiCad project generated successfully!
   Project: voltage_divider_test/

Generating BOM...
✅ BOM generated with 2 components

============================================================
Test Complete!
============================================================
```

### Generated Files
After running the test, you should see:
```
voltage_divider_test/
├── voltage_divider_test.kicad_sch   (Schematic)
├── voltage_divider_test.kicad_pcb   (PCB layout)
├── voltage_divider_test.kicad_pro   (Project config)
├── voltage_divider_test.net         (Netlist)
├── voltage_divider_test.json        (Circuit JSON)
└── voltage_divider_test.csv         (Bill of Materials)
```

## Testing Checklist

- [ ] Install circuit-synth 0.10.13 successfully
- [ ] Import core classes (Circuit, Component, Net)
- [ ] Create circuit with components and nets
- [ ] Generate KiCad project (schematic + PCB)
- [ ] Generate BOM in CSV format
- [ ] Verify all output files are created
- [ ] Check no errors in execution

## Version Information

To verify you're testing the correct version:

```bash
python -c "import circuit_synth; circuit_synth.print_version_info()"
```

Should show: `Git Commit: a8af0be` and `Version: 0.10.13`

## Key Changes in 0.10.13

- Updated kicad-sch-api to 0.3.5 (with public property accessors)
- Fixed dictionary iteration bug in code generator (8 locations)
- PCB generation improvements
- All unit tests passing (351 passed, 27 skipped)

## Troubleshooting

### KiCad CLI Not Found
If you see `kicad-cli not found` warnings, this is expected unless KiCad 7.0+ is installed. The core functionality works without it.

### Template Not Found Error
This is a known build issue. If you see it, the installation may be incomplete. Try:
```bash
pip install --force-reinstall --no-cache-dir circuit-synth==0.10.13
```

### Missing Dependencies
If you get import errors, ensure all dependencies are installed:
```bash
pip install --upgrade -r <(pip freeze | grep -E 'numpy|scipy|matplotlib|pydantic|kicad-sch-api')
```

## Need Help?

- Check the main README.md for full documentation
- Review examples in the repository
- Check GitHub issues: https://github.com/circuit-synth/circuit-synth/issues

---

**Test Date**: October 26, 2025
**Version**: 0.10.13
**Status**: Ready for production use ✅
