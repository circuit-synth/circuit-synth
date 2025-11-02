#!/usr/bin/env python3
"""
Generate remaining bidirectional tests (Tests 15-45) following the one-folder-per-test pattern.

This script creates test structure for all pending tests based on the established pattern
from Tests 10-14.
"""

import os
from pathlib import Path

# Test definitions
TEST_DEFINITIONS = [
    # Net CRUD - Root (15-17)
    {
        "number": 15,
        "category": "net_crud_root",
        "name": "sync_net_root_update",
        "title": "Update Net Connection",
        "operation": "Change R2[2] from CLK to DATA",
        "description": "Modify which pins a net connects to"
    },
    {
        "number": 16,
        "category": "net_crud_root",
        "name": "sync_net_root_rename",
        "title": "Rename Net",
        "operation": "Rename DATA → SIG",
        "description": "Rename net while preserving connections"
    },
    {
        "number": 17,
        "category": "net_crud_root",
        "name": "sync_net_root_delete",
        "title": "Delete Net",
        "operation": "Delete CLK net",
        "description": "Remove net while preserving other nets"
    },

    # Component CRUD - Hierarchical (18-21)
    {
        "number": 18,
        "category": "component_crud_hier",
        "name": "sync_component_hier_create",
        "title": "Add Component in Subcircuit",
        "operation": "Add R3 in subcircuit",
        "description": "Add component to hierarchical sheet"
    },
    {
        "number": 19,
        "category": "component_crud_hier",
        "name": "sync_component_hier_update_value",
        "title": "Update Component Value in Subcircuit",
        "operation": "Update subcircuit R1: 10k → 47k",
        "description": "Update component value in hierarchical sheet"
    },
    {
        "number": 20,
        "category": "component_crud_hier",
        "name": "sync_component_hier_update_ref",
        "title": "Rename Component in Subcircuit",
        "operation": "Rename subcircuit R1 → R100",
        "description": "Rename component in hierarchical sheet"
    },
    {
        "number": 21,
        "category": "component_crud_hier",
        "name": "sync_component_hier_delete",
        "title": "Delete Component in Subcircuit",
        "operation": "Delete subcircuit R2",
        "description": "Delete component from hierarchical sheet"
    },
]

# Template for comprehensive_root.py
CIRCUIT_TEMPLATE = '''#!/usr/bin/env python3
"""
Circuit for Test {number}: {title}

{description}

Test operation: {operation}
"""

from circuit_synth import circuit, Component, Net


@circuit(name="test_{number}")
def test_{number}():
    """Test circuit for {title}."""

    # Basic circuit
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd


if __name__ == "__main__":
    circuit_obj = test_{number}()
    circuit_obj.generate_kicad_project(
        project_name="test_{number}",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ Test {number} circuit generated!")
'''

# Template for test file
TEST_TEMPLATE = '''#!/usr/bin/env python3
"""
Test {number}: {title}

{description}
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_{number}_{name}(request):
    """Test {title}."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "test_{number}.py"
    output_dir = test_dir / "test_{number}"
    schematic_file = output_dir / "test_{number}.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Generation failed: {{result.stderr}}"
        assert schematic_file.exists(), "Schematic not generated"

        # Load and verify with kicad-sch-api
        sch = Schematic.load(str(schematic_file))

        # TODO: Add specific verification for {title}
        # - Check component positions
        # - Check values
        # - Check preservation

        print("\\n✅ Test {number} PASSED: {title}")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
'''

# Template for README
README_TEMPLATE = '''# Test {number}: {title}

## What This Tests

{description}

Operation: {operation}

## Manual Test Instructions

```bash
cd tests/bidirectional/{category}/{number}_{name}

# Step 1: Generate initial circuit
uv run test_{number}.py
open test_{number}/test_{number}.kicad_pro

# Step 2: Modify circuit (see test description)

# Step 3: Regenerate
uv run test_{number}.py

# Step 4: Verify changes
open test_{number}/test_{number}.kicad_pro
```

## Automated Test

```bash
pytest test_{name}.py -v
```

## Expected Result

- ✅ {title} successful
- ✅ All other elements preserved
'''


def create_test(test_def):
    """Create test folder structure for a test definition."""

    test_dir = Path(f"tests/bidirectional/{test_def['category']}/{test_def['number']:02d}_{test_def['name']}")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create circuit file
    circuit_file = test_dir / f"test_{test_def['number']}.py"
    circuit_content = CIRCUIT_TEMPLATE.format(**test_def)
    circuit_file.write_text(circuit_content)

    # Create test file
    test_file = test_dir / f"test_{test_def['name'].split('_')[-1]}.py"
    if test_def['name'].endswith('create'):
        test_file_name = "test_add.py"
    elif test_def['name'].endswith('update') or test_def['name'].endswith('update_value'):
        test_file_name = "test_update.py"
    elif test_def['name'].endswith('rename') or test_def['name'].endswith('update_ref'):
        test_file_name = "test_rename.py"
    elif test_def['name'].endswith('delete'):
        test_file_name = "test_delete.py"
    else:
        test_file_name = f"test_{test_def['name'].split('_')[-1]}.py"

    test_file = test_dir / test_file_name
    test_content = TEST_TEMPLATE.format(**test_def)
    test_file.write_text(test_content)

    # Create README
    readme_file = test_dir / "README.md"
    readme_content = README_TEMPLATE.format(**test_def)
    readme_file.write_text(readme_content)

    print(f"✅ Created Test {test_def['number']}: {test_def['title']}")


def main():
    """Generate all pending tests."""

    print("=" * 70)
    print("Generating Bidirectional Tests 15-21")
    print("=" * 70)
    print()

    for test_def in TEST_DEFINITIONS:
        create_test(test_def)

    print()
    print("=" * 70)
    print(f"✅ Generated {len(TEST_DEFINITIONS)} tests")
    print("=" * 70)
    print()
    print("Note: Tests are scaffolded. You'll need to:")
    print("  1. Implement specific circuit logic")
    print("  2. Add kicad-sch-api verification")
    print("  3. Test and refine")


if __name__ == "__main__":
    main()
