"""
KiCad Project Import API

Provides programmatic access to import KiCad projects into circuit-synth Circuit objects.

This module wraps the existing KiCadToPythonSyncer CLI functionality and provides
a clean Python API for importing KiCad schematics.

Example:
    >>> from circuit_synth.kicad.importer import import_kicad_project
    >>> circuit = import_kicad_project("my_project.kicad_pro")
    >>> print(f"Imported {len(circuit.components)} components")
"""

from pathlib import Path
from typing import Optional, Union

from ..core.circuit import Circuit
from ..core.component import Component
from ..core.net import Net
from ..tools.kicad_integration.kicad_to_python_sync import KiCadToPythonSyncer


def import_kicad_project(
    kicad_project: Union[str, Path],
) -> Circuit:
    """
    Import KiCad project to circuit-synth Circuit object.

    Simple, focused function that does one thing well: import KiCad → Circuit.

    Args:
        kicad_project: Path to KiCad project. Accepts:
            - .kicad_pro file (KiCad project)
            - .json netlist (preferred, if already generated)
            - Directory containing KiCad project

    Returns:
        Circuit object containing imported components and nets.

    Raises:
        FileNotFoundError: If KiCad project file not found
        ValueError: If JSON netlist is malformed
        RuntimeError: If import fails (parsing errors, etc.)

    Examples:
        # Import to Circuit object
        >>> circuit = import_kicad_project("my_project.kicad_pro")
        >>> print(f"Found {len(circuit.components)} components")
        Found 5 components

        # Import from JSON netlist (faster)
        >>> circuit = import_kicad_project("my_project.json")

        # Import from directory
        >>> circuit = import_kicad_project("/path/to/kicad/project/")

    Notes:
        - Positions are preserved from KiCad schematic when available
        - Net connections are automatically reconstructed
        - Component properties (value, footprint, etc.) are preserved
        - Hierarchical circuits are flattened in current implementation

    See Also:
        - Circuit.generate_kicad_project(): Export Circuit to KiCad
        - load_kicad_json(): Lower-level import from JSON
        - kicad-to-python CLI: Generate Python code files
    """
    # Step 1: Load JSON data (handles .kicad_pro, .json, directory)
    json_data = load_kicad_json(kicad_project)

    # Step 2: Convert JSON to models.Circuit
    models_circuit = _json_to_models_circuit(json_data)

    # Step 3: Convert models.Circuit to API Circuit
    circuit = _convert_models_circuit_to_api_circuit(models_circuit)

    return circuit


def load_kicad_json(kicad_project: Union[str, Path]) -> dict:
    """
    Load JSON netlist from KiCad project.

    Lower-level function that handles finding/generating JSON from various inputs.
    Separated for testability and reusability.

    Args:
        kicad_project: Path to .kicad_pro, .json, or directory

    Returns:
        Parsed JSON data as dictionary

    Raises:
        FileNotFoundError: If project not found
        ValueError: If JSON is malformed
        RuntimeError: If JSON generation fails
    """
    kicad_project = Path(kicad_project)

    if not kicad_project.exists():
        raise FileNotFoundError(f"KiCad project not found: {kicad_project}")

    # Use KiCadToPythonSyncer's JSON loading logic
    # This handles .kicad_pro → JSON conversion, finding JSON, etc.
    syncer = KiCadToPythonSyncer(
        kicad_project_or_json=str(kicad_project),
        python_file="/tmp/dummy.py",  # Not used, but required by API
        preview_only=True,  # Don't write files
        create_backup=False,
    )

    return syncer.json_data


def _json_to_models_circuit(json_data: dict):
    """
    Convert JSON data to models.Circuit.

    Separated for testing - can test JSON → models.Circuit conversion independently.

    Args:
        json_data: Parsed JSON netlist

    Returns:
        models.Circuit object
    """
    from ..tools.utilities.models import Circuit as ModelsCircuit
    from ..tools.utilities.models import Component as ModelsComponent
    from ..tools.utilities.models import Net as ModelsNet

    # Extract project name
    circuit_name = json_data.get("name", "main")

    # Extract components
    components = []
    for ref, comp_data in json_data.get("components", {}).items():
        component = ModelsComponent(
            reference=comp_data.get("ref", ref),
            lib_id=comp_data.get("symbol", ""),
            value=comp_data.get("value", ""),
            footprint=comp_data.get("footprint", ""),
            position=(0.0, 0.0),  # Position not always in JSON
        )
        components.append(component)

    # Extract nets
    nets = []
    for net_name, connections in json_data.get("nets", {}).items():
        net_connections = []
        for conn in connections:
            comp_ref = conn.get("component")
            pin_num = conn.get("pin", {}).get("number", "")
            if not pin_num:
                pin_num = conn.get("pin_id", "")
            net_connections.append((comp_ref, str(pin_num)))

        net = ModelsNet(name=net_name, connections=net_connections)
        nets.append(net)

    # Create circuit
    circuit = ModelsCircuit(
        name=circuit_name,
        components=components,
        nets=nets,
        schematic_file=json_data.get("source_file", ""),
        is_hierarchical_sheet=False,
    )

    return circuit


def _convert_models_circuit_to_api_circuit(models_circuit) -> Circuit:
    """
    Convert models.Circuit (CLI dataclass) to Circuit (API class).

    Args:
        models_circuit: Circuit object from tools.utilities.models

    Returns:
        Circuit object from core.circuit

    The models.Circuit is a simple dataclass used by the CLI:
        - components: List[Component]
        - nets: List[Net]

    The API Circuit is a full-featured class:
        - components: Dict[ref, Component]
        - nets: Dict[name, Net]
    """
    from ..tools.utilities.models import Component as ModelsComponent
    from ..tools.utilities.models import Net as ModelsNet

    # Create API Circuit
    circuit = Circuit(
        name=models_circuit.name,
        description=f"Imported from {models_circuit.schematic_file}"
        if models_circuit.schematic_file
        else None,
    )

    # Convert and add components
    for models_comp in models_circuit.components:
        # Create API Component
        comp = Component(
            symbol=models_comp.lib_id,  # lib_id → symbol
            ref=models_comp.reference,
            value=models_comp.value,
            footprint=models_comp.footprint,
        )

        # Add to circuit
        circuit._components[comp.ref] = comp
        circuit._component_list.append(comp)
        circuit.register_reference(comp.ref)

    # Convert and add nets
    for models_net in models_circuit.nets:
        # Create API Net
        net = Net(name=models_net.name)

        # Add connections
        for comp_ref, pin_num in models_net.connections:
            if comp_ref in circuit._components:
                comp = circuit._components[comp_ref]
                # Convert pin_num to int if it's a digit, otherwise use as string
                pin = int(pin_num) if str(pin_num).isdigit() else str(pin_num)
                try:
                    net += comp[pin]
                except (KeyError, IndexError):
                    # Pin doesn't exist in component - log warning and skip
                    from ..core._logger import context_logger

                    context_logger.warning(
                        f"Pin {pin} not found on component {comp_ref}, skipping connection",
                        component="IMPORTER",
                    )
                    continue

        # Add net to circuit
        circuit._nets[net.name] = net

    return circuit
