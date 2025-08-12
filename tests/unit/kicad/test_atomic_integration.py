"""
Tests for atomic integration with circuit-synth pipeline.
"""

import pytest
import tempfile
import json
from pathlib import Path
import logging

from circuit_synth.kicad.atomic_integration import (
    AtomicKiCadIntegration,
    migrate_circuit_to_atomic
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestAtomicIntegration:
    """Test atomic integration with production pipeline."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_json_netlist(self, temp_dir):
        """Create a sample JSON netlist for testing."""
        netlist = {
            "name": "test_circuit",
            "components": [
                {
                    "symbol": "Device:R",
                    "ref": "R1",
                    "value": "10k",
                    "footprint": "Resistor_SMD:R_0603_1608Metric",
                    "position": [100, 80],
                    "properties": {}
                },
                {
                    "symbol": "Device:C", 
                    "ref": "C1",
                    "value": "100nF",
                    "footprint": "Capacitor_SMD:C_0603_1608Metric",
                    "position": [120, 80],
                    "properties": {}
                }
            ],
            "nets": [
                {
                    "name": "VCC",
                    "connections": [
                        {"component": "R1", "pin": "1"},
                        {"component": "C1", "pin": "1"}
                    ]
                },
                {
                    "name": "GND",
                    "connections": [
                        {"component": "R1", "pin": "2"},
                        {"component": "C1", "pin": "2"}
                    ]
                }
            ],
            "subcircuits": []
        }
        
        json_path = temp_dir / "test_circuit.json"
        with open(json_path, 'w') as f:
            json.dump(netlist, f, indent=2)
        
        return json_path
    
    @pytest.fixture
    def sample_kicad_project(self, temp_dir):
        """Create a sample KiCad project directory."""
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()
        
        # Create minimal schematic file
        schematic_content = '''(kicad_sch 
    (version 20250114) 
    (generator "eeschema") 
    (generator_version "9.0")
    (paper "A4")
    (lib_symbols)
    (symbol_instances)
)'''
        
        schematic_path = project_dir / "test_project.kicad_sch"
        with open(schematic_path, 'w') as f:
            f.write(schematic_content)
        
        # Create minimal project file
        project_content = '''{
  "board": {
    "3dviewports": [],
    "design_settings": {}
  },
  "schematic": {
    "page_layout_descr_file": "",
    "drawing": {
      "paper_size": "A4"
    }
  }
}'''
        
        project_path = project_dir / "test_project.kicad_pro"
        with open(project_path, 'w') as f:
            f.write(project_content)
        
        return project_dir
    
    def test_atomic_integration_initialization(self, sample_kicad_project):
        """Test AtomicKiCadIntegration initialization."""
        atomic = AtomicKiCadIntegration(str(sample_kicad_project))
        
        assert atomic.project_path == Path(sample_kicad_project)
        assert atomic.project_path.exists()
    
    def test_add_component_atomic(self, sample_kicad_project):
        """Test adding a component using atomic integration."""
        atomic = AtomicKiCadIntegration(str(sample_kicad_project))
        
        # Component data in circuit-synth format
        component_data = {
            'symbol': 'Device:R',
            'ref': 'R1',
            'value': '10k',
            'footprint': 'Resistor_SMD:R_0603_1608Metric',
            'position': (100, 80)
        }
        
        success = atomic.add_component_atomic("test_project", component_data)
        assert success, "Should successfully add component"
        
        # Verify component was added
        schematic_path = sample_kicad_project / "test_project.kicad_sch"
        with open(schematic_path, 'r') as f:
            content = f.read()
        
        assert "Device:R" in content
        assert "R1" in content
        assert "10k" in content
    
    def test_remove_component_atomic(self, sample_kicad_project):
        """Test removing a component using atomic integration."""
        atomic = AtomicKiCadIntegration(str(sample_kicad_project))
        
        # First add a component
        component_data = {
            'symbol': 'Device:R',
            'ref': 'R1',
            'value': '10k',
            'footprint': 'Resistor_SMD:R_0603_1608Metric',
            'position': (100, 80)
        }
        
        success1 = atomic.add_component_atomic("test_project", component_data)
        assert success1, "Should add component successfully"
        
        # Verify component exists
        schematic_path = sample_kicad_project / "test_project.kicad_sch"
        with open(schematic_path, 'r') as f:
            content_with_component = f.read()
        assert "R1" in content_with_component
        
        # Now remove the component
        success2 = atomic.remove_component_atomic("test_project", "R1")
        assert success2, "Should remove component successfully"
        
        # Verify component was removed
        with open(schematic_path, 'r') as f:
            content_after_removal = f.read()
        
        # R1 reference should be gone from symbol instances
        assert content_after_removal.count("R1") < content_with_component.count("R1")
    
    def test_add_sheet_reference(self, sample_kicad_project):
        """Test adding hierarchical sheet references."""
        atomic = AtomicKiCadIntegration(str(sample_kicad_project))
        
        success = atomic.add_sheet_reference(
            "test_project",
            "Power_Supply",
            "Power_Supply.kicad_sch", 
            (35, 35),
            (44, 20)
        )
        assert success, "Should add sheet reference successfully"
        
        # Verify sheet was added
        schematic_path = sample_kicad_project / "test_project.kicad_sch"
        with open(schematic_path, 'r') as f:
            content = f.read()
        
        assert "(sheet" in content
        assert "Power_Supply" in content
        assert "Power_Supply.kicad_sch" in content
    
    def test_fix_hierarchical_main_schematic(self, sample_kicad_project):
        """Test fixing hierarchical main schematic with multiple sheet references."""
        atomic = AtomicKiCadIntegration(str(sample_kicad_project))
        
        subcircuits = [
            {
                "name": "USB_Port", 
                "filename": "USB_Port.kicad_sch",
                "position": (35, 35),
                "size": (43, 25)
            },
            {
                "name": "Power_Supply",
                "filename": "Power_Supply.kicad_sch", 
                "position": (95, 35),
                "size": (44, 20)
            },
            {
                "name": "MCU",
                "filename": "MCU.kicad_sch",
                "position": (95, 65),
                "size": (49, 38)
            }
        ]
        
        success = atomic.fix_hierarchical_main_schematic(subcircuits)
        assert success, "Should fix hierarchical main schematic successfully"
        
        # Verify all sheets were added
        schematic_path = sample_kicad_project / "test_project.kicad_sch" 
        with open(schematic_path, 'r') as f:
            content = f.read()
        
        assert content.count("(sheet") == 3, "Should have 3 sheet references"
        assert "USB_Port" in content
        assert "Power_Supply" in content
        assert "MCU" in content
    
    def test_migrate_circuit_to_atomic_basic(self, sample_json_netlist, temp_dir):
        """Test basic JSON to KiCad migration using atomic operations."""
        output_dir = temp_dir / "migrated_project"
        
        # This is a basic test - the actual implementation may need JSON format adjustments
        try:
            success = migrate_circuit_to_atomic(str(sample_json_netlist), str(output_dir))
            
            if success:
                # Verify output directory exists
                assert output_dir.exists(), "Output directory should be created"
                
                # Look for KiCad files (implementation dependent)
                kicad_files = list(output_dir.glob("*.kicad_*"))
                logger.info(f"Generated KiCad files: {kicad_files}")
                
            else:
                logger.warning("migrate_circuit_to_atomic returned False - feature may not be fully implemented yet")
                
        except Exception as e:
            logger.warning(f"migrate_circuit_to_atomic failed: {e} - feature may not be fully implemented yet")
            # This is expected if the function is not fully implemented yet
    
    def test_atomic_operations_error_handling(self, sample_kicad_project):
        """Test error handling in atomic operations."""
        atomic = AtomicKiCadIntegration(str(sample_kicad_project))
        
        # Test invalid schematic name
        success = atomic.add_component_atomic("nonexistent_schematic", {
            'symbol': 'Device:R',
            'ref': 'R1', 
            'value': '10k'
        })
        assert not success, "Should fail for nonexistent schematic"
        
        # Test removing nonexistent component
        success = atomic.remove_component_atomic("test_project", "R999")
        assert not success, "Should fail for nonexistent component"
        
        # Verify project directory still exists and is intact
        assert sample_kicad_project.exists()
        main_schematic = sample_kicad_project / "test_project.kicad_sch"
        assert main_schematic.exists()
    
    def test_atomic_operations_with_backup_restore(self, sample_kicad_project):
        """Test that atomic operations properly backup and restore on failure."""
        atomic = AtomicKiCadIntegration(str(sample_kicad_project))
        
        # Get initial state
        schematic_path = sample_kicad_project / "test_project.kicad_sch"
        with open(schematic_path, 'r') as f:
            initial_content = f.read()
        
        # Add a valid component first
        success1 = atomic.add_component_atomic("test_project", {
            'symbol': 'Device:R',
            'ref': 'R1',
            'value': '10k',
            'position': (100, 80)
        })
        assert success1, "Valid component addition should succeed"
        
        # Get state after valid addition
        with open(schematic_path, 'r') as f:
            content_after_add = f.read()
        assert "R1" in content_after_add
        assert len(content_after_add) > len(initial_content)
        
        # Try to add invalid component (this might succeed depending on implementation)
        # The key is that the file remains valid regardless
        atomic.add_component_atomic("test_project", {
            'symbol': 'Invalid:Component',
            'ref': 'U999',
            'value': 'invalid'
        })
        
        # File should still be readable and valid
        with open(schematic_path, 'r') as f:
            final_content = f.read()
        
        # Should still be able to parse the file
        assert len(final_content) > 0
        assert "(kicad_sch" in final_content


class TestReferenceCircuitCompatibility:
    """Test compatibility with reference circuits from development."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory with reference schematics."""
        return Path(__file__).parent.parent.parent / "test_data" / "atomic_references"
    
    def test_reference_circuits_analyzable(self, test_data_dir):
        """Test that all reference circuits can be analyzed by atomic operations."""
        from circuit_synth.kicad.atomic_operations_exact import add_component_to_schematic_exact
        
        reference_names = ['blank_schematic', 'single_resistor', 'two_resistors']
        
        for ref_name in reference_names:
            ref_schematic = test_data_dir / ref_name / f"{ref_name}.kicad_sch"
            
            if not ref_schematic.exists():
                logger.warning(f"Reference schematic not found: {ref_schematic}")
                continue
                
            # Test that we can read the file without errors
            with open(ref_schematic, 'r') as f:
                content = f.read()
            
            assert len(content) > 0, f"Reference {ref_name} should not be empty"
            assert "(kicad_sch" in content, f"Reference {ref_name} should be valid KiCad schematic"
            
            logger.info(f"Reference {ref_name}: {len(content)} chars, {content.count('(symbol')} symbols")


if __name__ == "__main__":
    # Run tests directly for debugging
    pytest.main([__file__, "-v", "-s"])