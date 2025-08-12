"""
Tests for atomic KiCad operations.
"""

import pytest
import tempfile
from pathlib import Path

from circuit_synth.kicad.atomic_operations_exact import (
    add_component_to_schematic_exact as add_component_to_schematic,
    remove_component_from_schematic_exact as remove_component_from_schematic
)


class TestAtomicOperations:
    """Test atomic component operations."""
    
    def test_add_component_to_blank_schematic(self):
        """Test adding a component to a blank schematic."""
        blank_content = '(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (paper "A4") (lib_symbols) (symbol_instances))'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.kicad_sch"
            
            # Write blank schematic
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(blank_content)
            
            # Add component
            success = add_component_to_schematic(
                file_path,
                lib_id="Device:R",
                reference="R1", 
                value="10k",
                position=(100, 50)
            )
            
            assert success is True
            
            # Verify component was added
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "Device:R" in content
            assert "R1" in content
            assert "10k" in content
    
    def test_remove_component_from_schematic(self):
        """Test removing a component from schematic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.kicad_sch"
            
            # First add a component
            blank_content = '(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (paper "A4") (lib_symbols) (symbol_instances))'
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(blank_content)
            
            add_component_to_schematic(
                file_path,
                lib_id="Device:R", 
                reference="R1",
                value="10k"
            )
            
            # Verify component exists
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "R1" in content
            
            # Remove component
            success = remove_component_from_schematic(file_path, "R1")
            assert success is True
            
            # Verify component is gone
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "R1" not in content
            assert "Device:R" not in content
    
    def test_remove_nonexistent_component(self):
        """Test removing component that doesn't exist."""
        blank_content = '(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (paper "A4") (lib_symbols) (symbol_instances))'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.kicad_sch"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(blank_content)
            
            # Try to remove non-existent component
            success = remove_component_from_schematic(file_path, "R999")
            assert success is False
    
    def test_add_multiple_components(self):
        """Test adding multiple components."""
        blank_content = '(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (paper "A4") (lib_symbols) (symbol_instances))'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.kicad_sch"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(blank_content)
            
            # Add first component
            success1 = add_component_to_schematic(
                file_path,
                lib_id="Device:R",
                reference="R1",
                value="10k"
            )
            
            # Add second component  
            success2 = add_component_to_schematic(
                file_path,
                lib_id="Device:R",
                reference="R2", 
                value="22k"
            )
            
            assert success1 is True
            assert success2 is True
            
            # Verify both components exist
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "R1" in content
            assert "R2" in content
            assert "10k" in content
            assert "22k" in content