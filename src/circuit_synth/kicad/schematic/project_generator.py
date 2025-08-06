"""
KiCad project generator using the new API.
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

import sexpdata

from ..core.s_expression import SExpressionParser
from ..core.types import Label, LabelType, Point, Schematic, SchematicSymbol, Sheet
from .component_manager import ComponentManager
from .connection_updater import ConnectionUpdater
from .geometry_utils import GeometryUtils
from .instance_utils import add_symbol_instance
from .placement import PlacementEngine, PlacementStrategy
from .sheet_manager import SheetManager
from .sheet_placement import SheetPlacement
from .wire_manager import WireManager

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """Generate new KiCad projects using the API."""

    def __init__(self, output_dir: str, project_name: str):
        """
        Initialize project generator.

        Args:
            output_dir: Directory where project will be created
            project_name: Name of the project
        """
        self.output_dir = Path(output_dir)
        self.project_name = project_name
        self.project_dir = self.output_dir / project_name

    def generate_from_circuit(self, circuit) -> None:
        """
        Generate a new KiCad project from a Circuit Synth circuit.

        Args:
            circuit: Circuit object to generate from
        """
        # Create project directory
        self.project_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Creating KiCad project in {self.project_dir}")

        # Copy blank project files
        self._copy_blank_project_files()

        # Create schematic
        schematic_path = self.project_dir / f"{self.project_name}.kicad_sch"
        self._generate_schematic(circuit, schematic_path)

    def _generate_uuid(self) -> str:
        """Generate a new UUID for KiCad elements."""
        return str(uuid.uuid4())

        logger.info(f"KiCad project '{self.project_name}' successfully generated")

    def _copy_blank_project_files(self):
        """Copy blank KiCad project files."""
        # Find the blank project template
        blank_project_dir = (
            Path(__file__).parent.parent.parent
            / "kicad"
            / "sch_gen"
            / "kicad_blank_project"
        )

        if not blank_project_dir.exists():
            raise FileNotFoundError(
                f"Blank project template not found at {blank_project_dir}"
            )

        # Copy project files
        for ext in [".kicad_pro", ".kicad_prl", ".kicad_pcb"]:
            src_file = blank_project_dir / f"kicad_blank_project{ext}"
            dst_file = self.project_dir / f"{self.project_name}{ext}"

            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                logger.debug(f"Copied {src_file.name} to {dst_file.name}")

    def _generate_schematic(self, circuit, schematic_path: Path):
        """Generate the schematic file from circuit."""
        has_components = hasattr(circuit, "_components") and circuit._components
        has_subcircuits = hasattr(circuit, "_subcircuits") and circuit._subcircuits

        if has_components and has_subcircuits:
            # Mixed design: root has both components and subcircuits
            # Use unified placement to place both in the same schematic
            self._generate_root_with_unified_placement(circuit, schematic_path)
        elif has_subcircuits:
            # Pure hierarchical design: only subcircuits, no components in root
            self._generate_hierarchical_design(circuit, schematic_path)
        else:
            # Simple design: only components, no subcircuits
            self._generate_simple_design(circuit, schematic_path)

    def _generate_simple_design(self, circuit, schematic_path: Path):
        """Generate a simple single-sheet design."""
        # Generate UUIDs for the sheets
        top_uuid = self._generate_uuid()
        sheet_uuid = self._generate_uuid()

        # 1. Generate the sub-sheet with the actual circuit
        sub_sheet_name = circuit.name if circuit.name != "UnnamedCircuit" else "circuit"
        sub_sheet_path = self.project_dir / f"{sub_sheet_name}.kicad_sch"
        self._generate_sub_sheet(circuit, sub_sheet_path, top_uuid, sheet_uuid)

        # 2. Generate the top-level sheet with sheet symbol
        sheet_placement = SheetPlacement()
        # Count nets to determine sheet size
        pin_count = len(circuit._nets) if hasattr(circuit, "_nets") else 10
        sheet_dims = sheet_placement.place_sheet(pin_count, sub_sheet_name)

        self._generate_top_sheet(
            schematic_path,
            [(sub_sheet_name, sub_sheet_path.name, sheet_dims, sheet_uuid)],
            top_uuid,
        )

        logger.info(
            f"Generated simple hierarchical schematic with top sheet: {schematic_path}"
        )

    def _generate_hierarchical_design(self, circuit, schematic_path: Path):
        """Generate a hierarchical design with multiple sub-sheets."""
        # Generate UUID for top sheet
        top_uuid = self._generate_uuid()

        # Prepare sheet information
        sheet_info = []
        sheet_placement = SheetPlacement()

        # Process main circuit
        main_sheet_name = f"{self.project_name}_main"
        main_sheet_path = self.project_dir / f"{main_sheet_name}.kicad_sch"
        main_sheet_uuid = self._generate_uuid()

        # Calculate sheet size for main circuit
        pin_count = len(circuit._nets) if hasattr(circuit, "_nets") else 10
        main_dims = sheet_placement.place_sheet(pin_count, main_sheet_name)
        sheet_info.append(
            (main_sheet_name, main_sheet_path.name, main_dims, main_sheet_uuid)
        )

        # Generate main circuit sheet
        self._generate_sub_sheet(circuit, main_sheet_path, top_uuid, main_sheet_uuid)

        # Process subcircuits
        for subcircuit in circuit._subcircuits:
            sub_name = subcircuit.name if hasattr(subcircuit, "name") else "subcircuit"
            sub_sheet_path = self.project_dir / f"{sub_name}.kicad_sch"
            sub_sheet_uuid = self._generate_uuid()

            # Calculate sheet size
            pin_count = len(subcircuit._nets) if hasattr(subcircuit, "_nets") else 10
            sub_dims = sheet_placement.place_sheet(pin_count, sub_name)
            sheet_info.append((sub_name, sub_sheet_path.name, sub_dims, sub_sheet_uuid))

            # Generate subcircuit sheet
            self._generate_sub_sheet(
                subcircuit, sub_sheet_path, top_uuid, sub_sheet_uuid
            )

        # Generate top-level sheet with all sheet symbols
        self._generate_top_sheet(schematic_path, sheet_info, top_uuid)

        logger.info(f"Generated hierarchical schematic with {len(sheet_info)} sheets")

    def _generate_root_with_unified_placement(self, circuit, schematic_path: Path):
        """
        Generate a root schematic with both components and sheets using unified placement.
        This is for the case where the root circuit has both components and subcircuits.
        """
        # Generate UUID for root sheet
        root_uuid = self._generate_uuid()

        # Create schematic
        schematic = Schematic()
        schematic.version = "20250114"
        schematic.generator = "circuit_synth"
        schematic.uuid = root_uuid

        # Get sheet size from paper size (default A4)
        paper_sizes = {
            "A4": (210.0, 297.0),
            "A3": (297.0, 420.0),
            "A2": (420.0, 594.0),
            "A1": (594.0, 841.0),
            "A0": (841.0, 1189.0),
        }
        sheet_size = paper_sizes.get("A4", (210.0, 297.0))

        # Initialize managers with sheet size
        component_manager = ComponentManager(schematic, sheet_size=sheet_size)
        sheet_manager = SheetManager(schematic)
        placement_engine = PlacementEngine(schematic, sheet_size=sheet_size)

        # Phase 1: Add all components to schematic
        component_map = {}
        for comp_id, comp in circuit._components.items():
            lib_id = self._get_library_id(comp)

            # Add component without placement
            kicad_comp = component_manager.add_component(
                library_id=lib_id,
                reference=comp.ref,
                value=comp.value,
                placement_strategy=None,  # We'll place manually
                footprint=comp.footprint,
            )

            if kicad_comp:
                component_map[comp_id] = kicad_comp
                add_symbol_instance(kicad_comp, self.project_name, f"/{root_uuid}")

        # Phase 2: Add sheets for subcircuits
        sheet_info = []
        if hasattr(circuit, "_subcircuits") and circuit._subcircuits:
            for subcircuit in circuit._subcircuits:
                sub_name = (
                    subcircuit.name if hasattr(subcircuit, "name") else "subcircuit"
                )
                sub_sheet_path = self.project_dir / f"{sub_name}.kicad_sch"
                sub_sheet_uuid = self._generate_uuid()

                # Create sheet
                pin_count = (
                    len(subcircuit._nets) if hasattr(subcircuit, "_nets") else 10
                )
                # Calculate proper sheet size based on pin count
                sheet_size = placement_engine._estimate_sheet_size(
                    Sheet(
                        name=sub_name,
                        filename=sub_sheet_path.name,
                        position=Point(0, 0),
                        size=(25.4, 25.4),
                        pins=[],
                    )
                )

                sheet = sheet_manager.add_sheet(
                    name=sub_name,
                    filename=sub_sheet_path.name,
                    position=(0, 0),  # Will be placed later
                    size=sheet_size,
                )

                # Store info for sub-sheet generation
                sheet_info.append(
                    (sub_name, subcircuit, sub_sheet_path, sub_sheet_uuid, sheet)
                )

        # Phase 3: Place all elements using unified placement
        # Place components first
        for comp in schematic.components:
            placement_engine.place_element(comp, "component", PlacementStrategy.AUTO)

        # Place sheets
        for sheet in schematic.sheets:
            placement_engine.place_element(sheet, "sheet", PlacementStrategy.AUTO)

        # Phase 4: Generate sub-sheets
        for sub_name, subcircuit, sub_sheet_path, sub_sheet_uuid, sheet in sheet_info:
            self._generate_sub_sheet(
                subcircuit, sub_sheet_path, root_uuid, sub_sheet_uuid
            )

        # Phase 5: Add wires/labels as needed
        # (Similar to existing _generate_sub_sheet logic)

        # Write the schematic
        parser = SExpressionParser()
        sexp_data = parser.from_schematic(schematic)
        parser.write_file(sexp_data, str(schematic_path))

        logger.info(
            f"Generated root schematic with {len(schematic.components)} components and {len(schematic.sheets)} sheets"
        )

    def _generate_top_sheet(
        self, schematic_path: Path, sheet_info: list, top_uuid: str
    ):
        """Generate the top-level sheet with sheet symbols.

        Args:
            schematic_path: Path to write the top-level schematic
            sheet_info: List of tuples (name, filename, dimensions, uuid)
            top_uuid: UUID for the top-level sheet
        """
        # Initialize parser
        parser = SExpressionParser()

        # Build sheet symbols
        sheet_symbols = []
        sheet_instances = []

        for i, (sheet_name, sheet_filename, sheet_dims, sheet_uuid) in enumerate(
            sheet_info
        ):
            x, y = sheet_dims.position
            width, height = sheet_dims.width, sheet_dims.height

            # Create sheet symbol
            sheet_symbol = [
                sexpdata.Symbol("sheet"),
                [sexpdata.Symbol("at"), x, y],
                [sexpdata.Symbol("size"), width, height],
                [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("in_bom"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("on_board"), sexpdata.Symbol("yes")],
                [sexpdata.Symbol("dnp"), sexpdata.Symbol("no")],
                [sexpdata.Symbol("fields_autoplaced"), sexpdata.Symbol("yes")],
                [
                    sexpdata.Symbol("stroke"),
                    [sexpdata.Symbol("width"), 0.1524],
                    [sexpdata.Symbol("type"), sexpdata.Symbol("solid")],
                ],
                [sexpdata.Symbol("fill"), [sexpdata.Symbol("color"), 0, 0, 0, 0.0000]],
                [sexpdata.Symbol("uuid"), sheet_uuid],
                [
                    sexpdata.Symbol("property"),
                    "Sheetname",
                    sheet_name,
                    [sexpdata.Symbol("at"), x, y - 0.7084, 0],
                    [
                        sexpdata.Symbol("effects"),
                        [
                            sexpdata.Symbol("font"),
                            [sexpdata.Symbol("size"), 1.27, 1.27],
                        ],
                        [
                            sexpdata.Symbol("justify"),
                            sexpdata.Symbol("left"),
                            sexpdata.Symbol("bottom"),
                        ],
                    ],
                ],
                [
                    sexpdata.Symbol("property"),
                    "Sheetfile",
                    sheet_filename,
                    [sexpdata.Symbol("at"), x, y + height + 0.7546, 0],
                    [
                        sexpdata.Symbol("effects"),
                        [
                            sexpdata.Symbol("font"),
                            [sexpdata.Symbol("size"), 1.27, 1.27],
                        ],
                        [
                            sexpdata.Symbol("justify"),
                            sexpdata.Symbol("left"),
                            sexpdata.Symbol("top"),
                        ],
                    ],
                ],
                [
                    sexpdata.Symbol("instances"),
                    [
                        sexpdata.Symbol("project"),
                        self.project_name,
                        [
                            sexpdata.Symbol("path"),
                            "/" + sheet_uuid,
                            [sexpdata.Symbol("page"), str(i + 2)],
                        ],
                    ],
                ],
            ]

            sheet_symbols.append(sheet_symbol)

            # Add sheet instance
            sheet_instances.append(
                [
                    sexpdata.Symbol("path"),
                    "/" + sheet_uuid,
                    [sexpdata.Symbol("page"), str(i + 2)],
                ]
            )

        # Generate the top-level sheet S-expression
        sexp_data = [
            sexpdata.Symbol("kicad_sch"),
            [sexpdata.Symbol("version"), 20250114],
            [sexpdata.Symbol("generator"), "eeschema"],
            [sexpdata.Symbol("generator_version"), "9.0"],
            [sexpdata.Symbol("uuid"), top_uuid],
            [sexpdata.Symbol("paper"), "A4"],
            [sexpdata.Symbol("lib_symbols")],
        ]

        # Add all sheet symbols
        sexp_data.extend(sheet_symbols)

        # Add sheet instances
        sexp_data.append(
            [
                sexpdata.Symbol("sheet_instances"),
                [sexpdata.Symbol("path"), "/", [sexpdata.Symbol("page"), "1"]],
            ]
        )

        # Add all other sheet instances
        for instance in sheet_instances:
            sexp_data[-1].append(instance)

        sexp_data.append([sexpdata.Symbol("embedded_fonts"), sexpdata.Symbol("no")])

        # Write the top-level sheet
        parser.write_file(sexp_data, str(schematic_path))

        logger.info(f"Generated top-level sheet with {len(sheet_info)} sheet symbols")

    def _generate_sub_sheet(
        self, circuit, sub_sheet_path: Path, top_uuid: str, sheet_uuid: str
    ):
        """Generate the sub-sheet with the actual circuit."""
        # Create empty schematic with proper defaults
        schematic = Schematic()
        schematic.version = "20250114"
        schematic.generator = "circuit_synth"
        schematic.uuid = sheet_uuid

        # Store hierarchical path for component instances
        hierarchical_path = f"/{top_uuid}/{sheet_uuid}"

        # Initialize parser
        parser = SExpressionParser()

        # Get sheet size from paper size (default A4)
        paper_sizes = {
            "A4": (210.0, 297.0),
            "A3": (297.0, 420.0),
            "A2": (420.0, 594.0),
            "A1": (594.0, 841.0),
            "A0": (841.0, 1189.0),
        }
        sheet_size = paper_sizes.get("A4", (210.0, 297.0))

        # Create managers
        component_manager = ComponentManager(schematic, sheet_size=sheet_size)
        wire_manager = WireManager(schematic)
        connection_updater = ConnectionUpdater(schematic)

        # Add components
        component_map = {}
        for comp_id, comp in circuit._components.items():
            # Determine library ID
            lib_id = self._get_library_id(comp)

            # Add component
            kicad_comp = component_manager.add_component(
                library_id=lib_id,
                reference=comp.ref,
                value=comp.value,
                placement_strategy=PlacementStrategy.AUTO,  # Use AUTO for dynamic placement
                footprint=comp.footprint,
            )

            if kicad_comp:
                component_map[comp_id] = kicad_comp
                # Add instance using centralized utility with hierarchical path
                add_symbol_instance(kicad_comp, self.project_name, hierarchical_path)

        # Create hierarchical labels for each pin instead of wires
        # This is the preferred approach for now
        # Track which positions already have labels for each net to avoid duplicates
        net_label_positions = {}  # {net_name: set of (x, y) tuples}

        for net in circuit._nets.values():
            # Initialize position tracking for this net if not already done
            if net.name not in net_label_positions:
                net_label_positions[net.name] = set()

            for pin in net.pins:
                # Find the component that owns this pin
                comp_ref = None
                pin_num = None

                # Search through components to find the pin
                for comp_id, comp in circuit._components.items():
                    for pin_id, comp_pin in comp._pins.items():
                        if comp_pin == pin:
                            comp_ref = comp.ref
                            pin_num = pin_id
                            break
                    if comp_ref:
                        break

                if comp_ref and pin_num:
                    # Find the KiCad component
                    kicad_comp = None
                    for symbol in schematic.components:
                        if symbol.reference == comp_ref:
                            kicad_comp = symbol
                            break

                    if kicad_comp:
                        # Get pin position
                        pin_pos = self._get_pin_position(kicad_comp, pin_num)
                        if pin_pos:
                            # Check if we already have a label at this position for this net
                            pos_tuple = (round(pin_pos.x, 2), round(pin_pos.y, 2))
                            if pos_tuple not in net_label_positions[net.name]:
                                # Find the actual pin object for proper label positioning
                                pin_obj = None
                                for pin in kicad_comp.pins:
                                    if pin.number == pin_num:
                                        pin_obj = pin
                                        break

                                if pin_obj:
                                    # Create label with dynamic positioning
                                    label = (
                                        GeometryUtils.create_dynamic_hierarchical_label(
                                            net.name,
                                            pin_obj,
                                            pin_pos,
                                            (
                                                kicad_comp.rotation
                                                if hasattr(kicad_comp, "rotation")
                                                else 0
                                            ),
                                        )
                                    )
                                    schematic.add_label(label)
                                    # Mark this position as having a label for this net
                                    net_label_positions[net.name].add(pos_tuple)
                                    logger.debug(
                                        f"Created label for net '{net.name}' at position {label.position}"
                                    )
                            else:
                                logger.debug(
                                    f"Skipping duplicate label for net '{net.name}' at position {pos_tuple}"
                                )

        # Write sub-sheet schematic
        sexp_data = parser.from_schematic(schematic)
        parser.write_file(sexp_data, str(sub_sheet_path))
        logger.info(f"Generated sub-sheet: {sub_sheet_path}")

    def _get_library_id(self, component) -> str:
        """Determine KiCad library ID from component."""
        # If symbol is already a library ID, use it
        if ":" in component.symbol:
            return component.symbol

        # Otherwise, map common symbols
        symbol_map = {
            "R": "Device:R",
            "C": "Device:C",
            "L": "Device:L",
            "D": "Device:D",
            "Q": "Device:Q_NPN_BCE",
            "U": "Device:R",  # Generic IC, use resistor as placeholder
        }

        # Try to match by reference prefix
        ref_prefix = "".join(c for c in component.ref if c.isalpha())
        return symbol_map.get(ref_prefix, "Device:R")

    def _generate_uuid(self) -> str:
        """Generate a KiCad-compatible UUID."""
        return str(uuid.uuid4())

    def _get_pin_position(
        self, component: SchematicSymbol, pin_num: str
    ) -> Optional[Point]:
        """
        Get the absolute position of a pin on a component.

        Args:
            component: The KiCad component
            pin_num: Pin number to find

        Returns:
            Absolute position of the pin, or None if not found
        """
        # Use GeometryUtils for proper pin position calculation with rotation support
        return GeometryUtils.get_actual_pin_position(component, pin_num)
