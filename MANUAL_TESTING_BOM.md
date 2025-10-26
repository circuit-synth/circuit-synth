# Manual Testing Guide: BOM Export Feature

Complete guide to manually test the BOM export functionality (PR #289, Issue #274).

## Prerequisites

Before testing, verify:

```bash
# 1. Check KiCad is installed and kicad-cli is available
kicad-cli --version
# Output should show: KiCad Command-line Interface 8.0.x or later

# 2. Verify circuit-synth is installed in development mode
python3 -c "from circuit_synth import circuit, Component; print('✓ circuit-synth imported successfully')"

# 3. Verify you're on the feat/bom-export-integration branch
git branch --show-current
# Should output: feat/bom-export-integration
```

## Test 1: Basic BOM Generation

**Objective**: Verify that `circuit.generate_bom()` creates a valid CSV file

**Steps:**

1. Create a test script:

```bash
cat > test_bom_basic.py << 'EOF'
from circuit_synth import circuit, Component

@circuit(name="SimpleTest")
def simple_circuit():
    """A simple test circuit"""
    r1 = Component(symbol="Device:R", value="10k", ref="R1")
    r2 = Component(symbol="Device:R", value="1k", ref="R2")
    c1 = Component(symbol="Device:C", value="100nF", ref="C1")
    led = Component(symbol="Device:LED", value="Red", ref="D1")
    return locals()

if __name__ == "__main__":
    circuit = simple_circuit()
    print(f"Circuit: {circuit.name}")
    print(f"Components: {len(circuit._components)}")

    # Generate BOM
    result = circuit.generate_bom(project_name="test_bom_basic")

    print(f"\nBOM Generation Result:")
    print(f"  Success: {result['success']}")
    print(f"  File: {result['file']}")
    print(f"  Component count: {result['component_count']}")
    print(f"  Project path: {result['project_path']}")

    # Display the generated CSV
    print(f"\nGenerated BOM Content:")
    with open(result['file'], 'r') as f:
        print(f.read())
EOF
```

2. Run the test:

```bash
python3 test_bom_basic.py
```

**Expected Output:**
```
Circuit: SimpleTest
Components: 4

BOM Generation Result:
  Success: True
  File: test_bom_basic/test_bom_basic.csv
  Component count: 4
  Project path: test_bom_basic

Generated BOM Content:
"Refs","Value","Footprint","Qty","DNP"
"C1","100nF","","1",""
"D1","Red","","1",""
"R1","10k","","1",""
"R2","1k","","1",""
```

**Verification:**
- ✅ BOM file exists at specified path
- ✅ CSV contains correct header row
- ✅ All 4 components listed
- ✅ Component count matches circuit components
- ✅ CSV is properly quoted

---

## Test 2: Custom Output Path

**Objective**: Verify custom output file path works correctly

**Steps:**

1. Create test script:

```bash
cat > test_bom_custom_path.py << 'EOF'
from circuit_synth import circuit, Component
from pathlib import Path

@circuit(name="CustomPathTest")
def test_circuit():
    Component(symbol="Device:R", value="10k", ref="R1")
    Component(symbol="Device:C", value="100nF", ref="C1")
    return locals()

if __name__ == "__main__":
    circuit = test_circuit()

    # Generate BOM with custom output path
    custom_path = "manufacturing/exported_bom.csv"
    result = circuit.generate_bom(
        project_name="test_custom",
        output_file=custom_path
    )

    print(f"Custom Output Test:")
    print(f"  Result: {result['success']}")
    print(f"  Expected path: {custom_path}")
    print(f"  Actual path: {result['file']}")
    print(f"  File exists: {result['file'].exists()}")

    if result['file'].exists():
        print(f"  File size: {result['file'].stat().st_size} bytes")
        print(f"  ✅ Custom output path works!")
EOF
```

2. Run the test:

```bash
python3 test_bom_custom_path.py
```

**Expected Output:**
```
Custom Output Test:
  Result: True
  Expected path: manufacturing/exported_bom.csv
  Actual path: manufacturing/exported_bom.csv
  File exists: True
  File size: 95 bytes
  ✅ Custom output path works!
```

**Verification:**
- ✅ Custom path is respected
- ✅ Parent directories created automatically
- ✅ File exists and has content

---

## Test 3: Large Circuit

**Objective**: Verify BOM generation works with many components

**Steps:**

1. Create test script:

```bash
cat > test_bom_large.py << 'EOF'
from circuit_synth import circuit, Component

@circuit(name="LargeCircuit")
def large_circuit():
    """Circuit with 30 components"""
    # 15 resistors
    for i in range(1, 16):
        Component(symbol="Device:R", value=f"{i*10}k", ref=f"R{i}")

    # 10 capacitors
    for i in range(1, 11):
        Component(symbol="Device:C", value=f"{i}uF", ref=f"C{i}")

    # 5 LEDs
    for i in range(1, 6):
        Component(symbol="Device:LED", value="Red", ref=f"D{i}")

    return locals()

if __name__ == "__main__":
    circuit = large_circuit()
    expected_count = len(circuit._components)

    print(f"Large Circuit Test:")
    print(f"  Total components in circuit: {expected_count}")

    result = circuit.generate_bom(project_name="test_large")

    print(f"  Components in BOM: {result['component_count']}")
    print(f"  Match: {result['component_count'] == expected_count}")

    if result['component_count'] == expected_count:
        print(f"  ✅ All {expected_count} components exported!")
EOF
```

2. Run the test:

```bash
python3 test_bom_large.py
```

**Expected Output:**
```
Large Circuit Test:
  Total components in circuit: 30
  Components in BOM: 30
  Match: True
  ✅ All 30 components exported!
```

**Verification:**
- ✅ All components counted correctly
- ✅ BOM matches circuit size
- ✅ Handles large circuits without issues

---

## Test 4: Component Grouping

**Objective**: Verify component grouping by value consolidates identical parts

**Steps:**

1. Create test script:

```bash
cat > test_bom_grouping.py << 'EOF'
from circuit_synth import circuit, Component
import csv

@circuit(name="GroupTest")
def group_circuit():
    """Circuit with duplicate component values"""
    # 5 resistors of same value
    for i in range(1, 6):
        Component(symbol="Device:R", value="10k", ref=f"R{i}")

    # 3 capacitors of same value
    for i in range(1, 4):
        Component(symbol="Device:C", value="100nF", ref=f"C{i}")

    return locals()

if __name__ == "__main__":
    circuit = group_circuit()

    print(f"Grouping Test:")
    print(f"  Total components: {len(circuit._components)}")

    # Generate BOM with grouping
    result = circuit.generate_bom(
        project_name="test_grouping",
        group_by="Value"
    )

    print(f"  Generated BOM with grouping")

    # Read and display grouped BOM
    with open(result['file'], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"  Rows in BOM: {len(rows)}")
        print(f"\n  Grouped components:")
        for row in rows:
            print(f"    {row['Refs']:20} | {row['Value']:10} | {row['Qty']}")
EOF
```

2. Run the test:

```bash
python3 test_bom_grouping.py
```

**Expected Output:**
```
Grouping Test:
  Total components: 8
  Generated BOM with grouping
  Rows in BOM: 2

  Grouped components:
    R1,R2,R3,R4,R5     | 10k        | 5
    C1,C2,C3           | 100nF      | 3
```

**Verification:**
- ✅ Components with same value grouped together
- ✅ References consolidated in single row
- ✅ Quantity correctly calculated
- ✅ Row count reduced from 8 to 2

---

## Test 5: Error Handling

**Objective**: Verify proper error handling when kicad-cli is unavailable

**Steps:**

1. Test with KiCad unavailable:

```bash
# Temporarily rename kicad-cli (if in PATH)
which kicad-cli  # Note the location

# Create test script:
cat > test_bom_errors.py << 'EOF'
from circuit_synth import circuit, Component

@circuit(name="ErrorTest")
def test_circuit():
    Component(symbol="Device:R", value="10k", ref="R1")
    return locals()

if __name__ == "__main__":
    circuit = test_circuit()
    result = circuit.generate_bom(project_name="test_error")

    if result['success']:
        print("✅ BOM generated successfully")
    else:
        print(f"❌ BOM generation failed:")
        print(f"  Error: {result['error']}")

        # Check for expected error message
        if "kicad-cli" in result['error']:
            print("  ✅ Error message mentions kicad-cli")
EOF
python3 test_bom_errors.py
```

**Expected Output:**
```
❌ BOM generation failed:
  Error: kicad-cli not found. Make sure KiCad 8.0+ is installed...
  ✅ Error message mentions kicad-cli
```

**Verification:**
- ✅ Graceful error handling
- ✅ Clear error message
- ✅ No Python traceback

---

## Test 6: Integration with KiCad Project

**Objective**: Verify generated KiCad files exist and are valid

**Steps:**

1. Create test script:

```bash
cat > test_bom_kicad_files.py << 'EOF'
from circuit_synth import circuit, Component
from pathlib import Path

@circuit(name="KiCadTest")
def test_circuit():
    Component(symbol="Device:R", value="10k", ref="R1")
    return locals()

if __name__ == "__main__":
    circuit = test_circuit()
    result = circuit.generate_bom(project_name="test_kicad")

    project_path = result['project_path']

    print(f"KiCad Project Files:")
    print(f"  Project path: {project_path}")

    # Check for expected files
    expected_files = [
        "test_kicad.kicad_sch",  # Schematic
        "test_kicad.json",        # JSON netlist
        "test_kicad.csv"          # BOM
    ]

    for filename in expected_files:
        filepath = project_path / filename
        exists = filepath.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {filename}: {exists}")
EOF
```

2. Run the test:

```bash
python3 test_bom_kicad_files.py
```

**Expected Output:**
```
KiCad Project Files:
  Project path: test_kicad
  ✅ test_kicad.kicad_sch: True
  ✅ test_kicad.json: True
  ✅ test_kicad.csv: True
```

**Verification:**
- ✅ KiCad schematic generated
- ✅ JSON netlist created
- ✅ BOM CSV exported

---

## Test 7: Reusing Existing Project

**Objective**: Verify that generate_bom() reuses existing projects

**Steps:**

1. Create test script:

```bash
cat > test_bom_reuse.py << 'EOF'
from circuit_synth import circuit, Component
import time

@circuit(name="ReuseTest")
def test_circuit():
    Component(symbol="Device:R", value="10k", ref="R1")
    return locals()

if __name__ == "__main__":
    circuit = test_circuit()

    print(f"Project Reuse Test:")

    # First generation
    result1 = circuit.generate_bom(project_name="test_reuse")
    mtime1 = result1['file'].stat().st_mtime
    print(f"  First generation: {result1['file']}")

    # Wait a bit
    time.sleep(1)

    # Second generation (should reuse)
    result2 = circuit.generate_bom(project_name="test_reuse")
    mtime2 = result2['file'].stat().st_mtime
    print(f"  Second generation: {result2['file']}")

    print(f"  Same file: {result1['file'] == result2['file']}")
    print(f"  File was regenerated: {mtime2 > mtime1}")

    if result1['file'] == result2['file']:
        print(f"  ✅ Project reuse works!")
EOF
```

2. Run the test:

```bash
python3 test_bom_reuse.py
```

**Expected Output:**
```
Project Reuse Test:
  First generation: test_reuse/test_reuse.csv
  Second generation: test_reuse/test_reuse.csv
  Same file: True
  File was regenerated: True
  ✅ Project reuse works!
```

**Verification:**
- ✅ Same project directory used
- ✅ BOM regenerated with latest circuit data
- ✅ No duplicate project creation

---

## Test 8: CSV Format Validation

**Objective**: Verify the generated CSV is valid and properly formatted

**Steps:**

1. Create test script:

```bash
cat > test_bom_csv_format.py << 'EOF'
import csv
from circuit_synth import circuit, Component

@circuit(name="CSVTest")
def test_circuit():
    Component(symbol="Device:R", value="10k", ref="R1")
    Component(symbol="Device:C", value="100nF", ref="C1")
    return locals()

if __name__ == "__main__":
    circuit = test_circuit()
    result = circuit.generate_bom(project_name="test_csv")

    print(f"CSV Format Validation:")

    # Read and validate CSV
    with open(result['file'], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        print(f"  Header fields: {reader.fieldnames}")
        print(f"  Row count: {len(rows)}")

        # Validate header
        required_fields = ["Refs", "Value", "Footprint", "Qty"]
        has_required = all(field in reader.fieldnames for field in required_fields)
        print(f"  ✅ Has required fields: {has_required}")

        # Validate rows
        for i, row in enumerate(rows):
            has_cols = len(row) == len(reader.fieldnames)
            if not has_cols:
                print(f"  ❌ Row {i} has wrong column count")
                break
        else:
            print(f"  ✅ All rows properly formatted")
EOF
```

2. Run the test:

```bash
python3 test_bom_csv_format.py
```

**Expected Output:**
```
CSV Format Validation:
  Header fields: ['Refs', 'Value', 'Footprint', 'Qty', 'DNP']
  Row count: 2
  ✅ Has required fields: True
  ✅ All rows properly formatted
```

**Verification:**
- ✅ CSV has proper header row
- ✅ All rows have consistent column count
- ✅ Required fields present

---

## Cleanup

After testing, remove test files:

```bash
rm -f test_bom_*.py
rm -rf test_bom_* test_kicad test_custom test_grouping test_large test_error
rm -rf manufacturing/
```

---

## Summary Checklist

Run through all tests and mark completion:

- [ ] Test 1: Basic BOM Generation
- [ ] Test 2: Custom Output Path
- [ ] Test 3: Large Circuit
- [ ] Test 4: Component Grouping
- [ ] Test 5: Error Handling
- [ ] Test 6: KiCad Project Integration
- [ ] Test 7: Project Reuse
- [ ] Test 8: CSV Format Validation

**If all tests pass:** ✅ Feature is ready for production

---

## Troubleshooting

### "kicad-cli not found"
```bash
# Verify KiCad installation
kicad-cli --version

# Add to PATH if needed (example for macOS)
export PATH="/Applications/KiCad/Contents/MacOS:$PATH"
```

### Empty or missing CSV
- Check that all components have `ref` parameter
- Verify component symbols exist in KiCad libraries
- Check for error messages in result dictionary

### CSV file not found
- Check project path exists
- Verify write permissions in directory
- Look for error message: `result['error']`

---

## Next Steps After Testing

Once manual testing is complete:

1. **Merge PR**: Review and merge #289 to main
2. **Run CI/CD**: Ensure automated tests pass
3. **Update issue**: Mark #274 as resolved
4. **Consider related features**:
   - #276: Gerber Generation
   - #278: Manufacturing Package (depends on this)
