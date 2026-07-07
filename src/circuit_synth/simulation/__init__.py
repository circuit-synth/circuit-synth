"""
Circuit-Synth SPICE Simulation Integration

This module provides SPICE simulation capabilities for circuit-synth designs
using PySpice as the backend and ngspice as the simulation engine.

Main Components:
- CircuitSimulator: Main simulation interface
- SpiceConverter: Converts circuit-synth to SPICE format
- SimulationResult: Results container with plotting capabilities
- AnalysisTypes: DC, AC, Transient analysis support

Example Usage:
    from circuit_synth import circuit, Component, Net
    from circuit_synth.simulation import CircuitSimulator

    @circuit
    def my_circuit():
        r1 = Component("Device:R", ref="R", value="10k")
        # ... circuit definition

    c = my_circuit()
    sim = c.simulator()  # Returns CircuitSimulator
    result = sim.dc_analysis(vin_range=(0, 5, 0.1))
    result.plot('VOUT')
"""

from .analysis import ACAnalysis, DCAnalysis, TransientAnalysis
from .converter import ResolvedModel, SimulationValidationError, SpiceConverter
from .manufacturer_models import ManufacturerModels, get_manufacturer_models
from .model_store import SpiceModelStore, get_model_store, resolve_mpn
from .models import ModelLibrary, SpiceModel, get_model_library
from .plotting import save_bode_plot, save_dc_transfer_plot, save_transient_plot
from .simulator import CircuitSimulator, SimulationResult
from .visualization import SimulationVisualizer, enhance_simulation_result

# Enhance SimulationResult with export capabilities
SimulationResult = enhance_simulation_result(SimulationResult)

__all__ = [
    "CircuitSimulator",
    "SimulationResult",
    "SpiceConverter",
    "SimulationValidationError",
    "ResolvedModel",
    "DCAnalysis",
    "ACAnalysis",
    "TransientAnalysis",
    "ModelLibrary",
    "SpiceModel",
    "get_model_library",
    "ManufacturerModels",
    "get_manufacturer_models",
    "SpiceModelStore",
    "get_model_store",
    "resolve_mpn",
    "SimulationVisualizer",
    "save_bode_plot",
    "save_transient_plot",
    "save_dc_transfer_plot",
]
