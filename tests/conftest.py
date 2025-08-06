import os
import shutil
from pathlib import Path

import pytest

from circuit_synth.core.circuit import Circuit
from circuit_synth.core.decorators import get_current_circuit, set_current_circuit
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache


@pytest.fixture(scope="session", autouse=True)
def configure_kicad_paths():
    """
    Configure KiCad paths and clear symbol cache for tests.

    Now that KiCad is installed in CI, we can use real KiCad symbols everywhere.
    """
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
