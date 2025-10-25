"""
Unit tests for bidirectional KiCad <-> Python synchronization.

These tests use pre-made KiCad fixture files to exercise the sync logic
without requiring manual intervention or KiCad GUI interaction.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer


class TestBidirectionalSync:
    """Test bidirectional synchronization between KiCad and Python."""

    @pytest.fixture
    def fixtures_dir(self):
        """Path to test fixtures directory."""
        return Path(__file__).parent.parent / "bidirectional" / "fixtures"

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_sync_blank_circuit_to_python(self, fixtures_dir, temp_workspace):
        """Test syncing a blank KiCad circuit to Python.

        Fixture: blank/ - Empty circuit with no components
        Expected: Python file with just 'pass' statement
        """
        # Copy blank fixture to workspace
        fixture_path = fixtures_dir / "blank"
        kicad_project = temp_workspace / "blank"
        shutil.copytree(fixture_path, kicad_project)

        # Create blank Python file
        python_file = temp_workspace / "blank_circuit.py"
        python_file.write_text("""#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="BlankCircuit")
def main():
    \"\"\"Test circuit\"\"\"
    pass


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="blank")
""")

        # Sync KiCad -> Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "blank.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success = syncer.sync()

        assert success, "Sync should succeed"

        # Verify result
        result = python_file.read_text()
        assert "pass" in result, "Blank circuit should keep 'pass' statement"
        assert "@circuit" in result, "Decorator should be preserved"
        assert "def main():" in result, "Function should be preserved"

    def test_sync_single_resistor_removes_pass(self, fixtures_dir, temp_workspace):
        """Test syncing a circuit with one resistor removes 'pass' statement.

        Fixture: single_resistor/ - Circuit with R1 (10k)
        Expected: Python file with R1 component, no 'pass'
        """
        # Copy single_resistor fixture to workspace
        fixture_path = fixtures_dir / "single_resistor"
        kicad_project = temp_workspace / "single_resistor"
        shutil.copytree(fixture_path, kicad_project)

        # Create Python file with just 'pass'
        python_file = temp_workspace / "resistor_circuit.py"
        python_file.write_text("""#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="ResistorCircuit")
def main():
    \"\"\"Test circuit\"\"\"
    pass


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
""")

        # Sync KiCad -> Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "single_resistor.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success = syncer.sync()

        assert success, "Sync should succeed"

        # Verify result
        result = python_file.read_text()
        assert "pass" not in result, "'pass' should be removed when components exist"
        assert "Component" in result, "Should have Component import/usage"
        assert "R1" in result, "Should have R1 component"
        assert "10k" in result, "Should have 10k value"
        assert "Device:R" in result, "Should have resistor symbol"

    def test_sync_preserves_user_comments(self, fixtures_dir, temp_workspace):
        """Test that user comments are preserved during sync.

        Fixture: single_resistor/ - Circuit with R1
        Expected: User comments preserved, component updated
        """
        # Copy fixture to workspace
        fixture_path = fixtures_dir / "single_resistor"
        kicad_project = temp_workspace / "single_resistor"
        shutil.copytree(fixture_path, kicad_project)

        # Create Python file with user comments
        python_file = temp_workspace / "commented_circuit.py"
        python_file.write_text("""#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="CommentedCircuit")
def main():
    \"\"\"Test circuit with comments\"\"\"
    # User note: This is a test circuit
    # TODO: Add more components later
    pass


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
""")

        # Sync KiCad -> Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "single_resistor.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success = syncer.sync()

        assert success, "Sync should succeed"

        # Verify result
        result = python_file.read_text()
        assert "# User note: This is a test circuit" in result, "User comment should be preserved"
        assert "# TODO: Add more components later" in result, "TODO comment should be preserved"
        assert "R1" in result, "Component should be added"
        assert "pass" not in result, "'pass' should be removed"

    def test_sync_preserves_custom_function_name(self, fixtures_dir, temp_workspace):
        """Test that custom function names are preserved during sync.

        Fixture: single_resistor/ - Circuit with R1
        Expected: Custom function name 'my_circuit' preserved
        """
        # Copy fixture to workspace
        fixture_path = fixtures_dir / "single_resistor"
        kicad_project = temp_workspace / "single_resistor"
        shutil.copytree(fixture_path, kicad_project)

        # Create Python file with custom function name
        python_file = temp_workspace / "custom_circuit.py"
        python_file.write_text("""#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="CustomCircuit")
def my_circuit():
    \"\"\"Custom function name\"\"\"
    pass


if __name__ == "__main__":
    circuit_obj = my_circuit()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
""")

        # Sync KiCad -> Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "single_resistor.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success = syncer.sync()

        assert success, "Sync should succeed"

        # Verify result
        result = python_file.read_text()
        assert "def my_circuit():" in result, "Custom function name should be preserved"
        assert "@circuit(name=\"CustomCircuit\")" in result, "Custom decorator should be preserved"
        assert "R1" in result, "Component should be added"
        assert "circuit_obj = my_circuit()" in result, "Function call should use custom name"

    def test_sync_idempotent(self, fixtures_dir, temp_workspace):
        """Test that multiple syncs produce identical results (idempotency).

        Fixture: single_resistor/ - Circuit with R1
        Expected: Running sync twice produces same result
        """
        # Copy fixture to workspace
        fixture_path = fixtures_dir / "single_resistor"
        kicad_project = temp_workspace / "single_resistor"
        shutil.copytree(fixture_path, kicad_project)

        # Create Python file
        python_file = temp_workspace / "idempotent_circuit.py"
        python_file.write_text("""#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="IdempotentCircuit")
def main():
    \"\"\"Test idempotency\"\"\"
    pass


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
""")

        # First sync
        syncer1 = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "single_resistor.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success1 = syncer1.sync()
        assert success1, "First sync should succeed"
        result1 = python_file.read_text()

        # Second sync
        syncer2 = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "single_resistor.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success2 = syncer2.sync()
        assert success2, "Second sync should succeed"
        result2 = python_file.read_text()

        # Results should be identical
        assert result1 == result2, "Multiple syncs should produce identical results (idempotent)"

        # Verify no duplicate content
        assert result2.count("R1") == 1, "Component should not be duplicated"
        assert result2.count("# Create components") <= 1, "Comment should not be duplicated"

    def test_sync_preserves_blank_lines_between_comments(self, fixtures_dir, temp_workspace):
        """Test that blank lines between comment groups are preserved.

        Fixture: single_resistor/ - Circuit with R1
        Expected: Blank lines between user comment groups preserved
        """
        # Copy fixture to workspace
        fixture_path = fixtures_dir / "single_resistor"
        kicad_project = temp_workspace / "single_resistor"
        shutil.copytree(fixture_path, kicad_project)

        # Create Python file with spaced comments
        python_file = temp_workspace / "spaced_circuit.py"
        python_file.write_text("""#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="SpacedCircuit")
def main():
    \"\"\"Test circuit with spaced comments\"\"\"
    # First comment group
    # More details here

    # Second comment group after blank line

    pass


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
""")

        # Sync KiCad -> Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "single_resistor.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success = syncer.sync()

        assert success, "Sync should succeed"

        # Verify result
        result = python_file.read_text()
        lines = result.split('\n')

        # Find the comment lines
        first_comment_idx = next(i for i, line in enumerate(lines) if "First comment group" in line)
        second_comment_idx = next(i for i, line in enumerate(lines) if "Second comment group" in line)

        # There should be blank lines between them
        between_lines = lines[first_comment_idx + 2:second_comment_idx]
        blank_lines = [line for line in between_lines if line.strip() == '']
        assert len(blank_lines) > 0, "Blank lines between comment groups should be preserved"

    def test_sync_limits_trailing_blank_lines(self, fixtures_dir, temp_workspace):
        """Test that trailing blank lines are limited to max 2.

        Fixture: single_resistor/ - Circuit with R1
        Expected: Excessive trailing blanks reduced to max 2
        """
        # Copy fixture to workspace
        fixture_path = fixtures_dir / "single_resistor"
        kicad_project = temp_workspace / "single_resistor"
        shutil.copytree(fixture_path, kicad_project)

        # Create Python file with many trailing blanks
        python_file = temp_workspace / "trailing_circuit.py"
        python_file.write_text("""#!/usr/bin/env python3
from circuit_synth import *


@circuit(name="TrailingCircuit")
def main():
    \"\"\"Test circuit with trailing blanks\"\"\"
    # Comment with lots of trailing space





    pass


if __name__ == "__main__":
    circuit_obj = main()
    circuit_obj.generate_kicad_project(project_name="single_resistor")
""")

        # Sync KiCad -> Python
        syncer = KiCadToPythonSyncer(
            kicad_project_or_json=str(kicad_project / "single_resistor.json"),
            python_file=str(python_file),
            preview_only=False
        )
        success = syncer.sync()

        assert success, "Sync should succeed"

        # Verify result
        result = python_file.read_text()

        # Find the component line and count trailing blanks before if __name__
        lines = result.split('\n')
        component_idx = next((i for i, line in enumerate(lines) if "Component" in line), None)
        if_name_idx = next(i for i, line in enumerate(lines) if "if __name__" in line)

        if component_idx:
            between_lines = lines[component_idx + 1:if_name_idx]
            blank_count = sum(1 for line in between_lines if line.strip() == '')
            assert blank_count <= 2, f"Should have max 2 trailing blank lines, found {blank_count}"
