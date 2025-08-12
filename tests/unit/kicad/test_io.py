"""
Tests for KiCad File I/O Layer.
"""

import pytest
import tempfile
from pathlib import Path

from circuit_synth.kicad.io import KiCadFileIO


class TestKiCadFileIO:
    """Test KiCadFileIO class."""
    
    def test_read_write_basic(self):
        """Test basic read/write operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.kicad_sch"
            content = "(kicad_sch (version 20250114) (paper \"A4\"))"
            
            # Test write
            io = KiCadFileIO()
            io.write(content, file_path)
            
            # Test file exists
            assert io.exists(file_path)
            assert file_path.exists()
            
            # Test read
            read_content = io.read(file_path)
            assert read_content == content
    
    def test_atomic_write(self):
        """Test atomic write operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "atomic_test.kicad_sch"
            content = "(kicad_sch (version 20250114))"
            
            io = KiCadFileIO()
            io.write(content, file_path, atomic=True)
            
            # Verify no temp file remains
            temp_files = list(Path(tmpdir).glob("*.tmp"))
            assert len(temp_files) == 0
            
            # Verify content
            assert io.read(file_path) == content
    
    def test_backup_creation(self):
        """Test backup file creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "backup_test.kicad_sch"
            original_content = "(kicad_sch (version 1))"
            new_content = "(kicad_sch (version 2))"
            
            io = KiCadFileIO(create_backups=True)
            
            # Create original file
            io.write(original_content, file_path)
            
            # Overwrite with new content (should create backup)
            io.write(new_content, file_path)
            
            # Check backup was created
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            assert backup_path.exists()
            
            # Verify backup contains original content
            backup_content = io.read(backup_path)
            assert backup_content == original_content
            
            # Verify main file has new content
            main_content = io.read(file_path)
            assert main_content == new_content
    
    def test_read_nonexistent_file(self):
        """Test reading non-existent file raises appropriate error."""
        io = KiCadFileIO()
        
        with pytest.raises(FileNotFoundError):
            io.read("/non/existent/path.kicad_sch")
    
    def test_directory_creation(self):
        """Test that parent directories are created automatically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "deep" / "nested" / "path" / "test.kicad_sch"
            content = "(kicad_sch)"
            
            io = KiCadFileIO()
            io.write(content, nested_path)
            
            assert nested_path.exists()
            assert io.read(nested_path) == content
    
    def test_no_backups(self):
        """Test that backups can be disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "no_backup_test.kicad_sch"
            
            io = KiCadFileIO(create_backups=False)
            
            # Create and overwrite file
            io.write("original", file_path)
            io.write("modified", file_path)
            
            # Check no backup was created
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            assert not backup_path.exists()
            
            # Verify content
            assert io.read(file_path) == "modified"