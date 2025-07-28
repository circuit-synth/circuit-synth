import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from circuit_synth.core.circuit import Circuit
from circuit_synth.core.decorators import get_current_circuit, set_current_circuit
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

# Check if we're in CI environment
IS_CI = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'

# Skip marker for tests that require KiCad installation
require_kicad = pytest.mark.skipif(IS_CI, reason="Requires KiCad installation (not available in CI)")

def _create_mock_symbol_data(symbol: str):
    """Create mock symbol data for testing."""
    lib_name, symbol_name = symbol.split(':', 1) if ':' in symbol else ('Device', symbol)
    return {
        'name': symbol_name,
        'library': lib_name,
        'pins': [
            {'number': '1', 'name': '1', 'type': 'passive'},
            {'number': '2', 'name': '2', 'type': 'passive'}
        ],
        'properties': {
            'Reference': 'R',
            'Value': '',
            'Footprint': '',
            'Datasheet': ''
        }
    }

@pytest.fixture(scope="session", autouse=True)
def configure_kicad_paths():
    """
    Configure KiCad paths or mock symbol cache for CI environment.
    """
    # Check if we're in CI environment (no KiCad installation)
    is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'
    
    if is_ci:
        # Mock the symbol cache for CI
        with patch.object(SymbolLibCache, 'get_symbol_data', side_effect=_create_mock_symbol_data):
            with patch.object(SymbolLibCache, '_find_kicad_symbol_dirs', return_value=[]):
                yield
    else:
        # Use real KiCad installation for local development
        # Clear any existing cache
        cache_dir = SymbolLibCache._get_cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear in-memory cache
        SymbolLibCache._library_data.clear()
        SymbolLibCache._symbol_index.clear()
        SymbolLibCache._library_index.clear()
        SymbolLibCache._index_built = False

        yield

        # Clean up after tests
        cache_dir = SymbolLibCache._get_cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)


@pytest.fixture(autouse=True, scope="function")
def mock_active_circuit():
    """
    Automatically create a throwaway circuit before each test,
    so that Component(...) does not fail with 'No active circuit found'.
    """
    old_circuit = get_current_circuit()
    set_current_circuit(Circuit(name="TestCircuit"))
    try:
        yield
    finally:
        set_current_circuit(old_circuit)