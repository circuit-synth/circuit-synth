"""
Modern KiCad schematic generator using kicad-sch-api.

This module provides a parallel implementation to the legacy main_generator.py
using the professional kicad-sch-api library for enhanced functionality.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import kicad-sch-api with graceful fallback
try:
    import kicad_sch_api as ksa
    KICAD_SCH_API_AVAILABLE = True
except ImportError:
    KICAD_SCH_API_AVAILABLE = False
    ksa = None

from ...core.circuit import Circuit
from ...core.component import Component
from ...core.net import Net
from ..config import KiCadConfig, validate_modern_api_requirements

logger = logging.getLogger(__name__)


class ModernKiCadGenerator:
    """
    Modern KiCad schematic file writer using kicad-sch-api.
    
    This generator focuses ONLY on schematic file writing with exact format
    preservation. Component placement, hierarchy, and layout are handled
    by the legacy system and passed in as positioned data.
    
    Features:
    - Exact KiCad format preservation
    - Professional validation  
    - Symbol library caching
    - Accepts pre-positioned components from legacy placement system
    """
    
    def __init__(self, output_dir: str = ".", project_name: str = "circuit"):
        """
        Initialize modern schematic file writer.
        
        Args:
            output_dir: Directory for output files
            project_name: Base name for generated files
        """
        if not KICAD_SCH_API_AVAILABLE:
            raise ImportError(
                "kicad-sch-api is required for modern generator. "
                "Install with: pip install kicad-sch-api>=0.1.1"
            )
        
        self.output_dir = Path(output_dir)
        self.project_name = project_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize schematic
        self.schematic = ksa.create_schematic(project_name)
        
        # Track generated components for reference
        self._component_map = {}  # circuit_synth ref -> kicad-sch-api component
        
        logger.info(f"Initialized modern KiCad generator for {project_name}")
    
    def write_positioned_schematic(self, positioned_components: List[Dict], nets: List[Dict], title_info: Dict = None) -> str:
        """
        Write schematic file using pre-positioned components from legacy placement system.
        
        Args:
            positioned_components: List of components with positions calculated by legacy system
            nets: List of nets/connections from legacy system  
            title_info: Title block information
            
        Returns:
            str: Path to generated .kicad_sch file
        """
        logger.info(f"Writing positioned schematic with {len(positioned_components)} components")
        
        # Add positioned components
        for comp_data in positioned_components:
            self._add_positioned_component(comp_data)
        
        # Add nets (legacy system handles wire generation)
        for net_data in nets:
            self._add_net_data(net_data)
        
        # Set title block
        if title_info:
            self._set_title_block_from_data(title_info)
        
        # Save schematic
        output_path = self.output_dir / f"{self.project_name}.kicad_sch"
        self.schematic.save(str(output_path), preserve_format=True)
        
        # Create KiCad project file
        project_file_path = self.output_dir / f"{self.project_name}.kicad_pro"
        self._create_project_file(project_file_path)
        
        # Validate output
        issues = self.schematic.validate()
        if issues:
            logger.warning(f"Generated schematic has {len(issues)} validation issues")
            for issue in issues[:3]:
                logger.warning(f"Validation: {issue}")
        
        logger.info(f"Generated positioned schematic: {output_path}")
        return str(output_path)
    
    def generate_schematic(self, circuit: Circuit) -> str:
        """
        Generate KiCad schematic from circuit-synth Circuit object.
        
        Args:
            circuit: Circuit object to convert
            
        Returns:
            str: Path to generated .kicad_sch file
        """
        logger.info(f"Generating schematic - Main: {len(circuit.components)} components, Subcircuits: {len(circuit._subcircuits)}")
        
        # Add components from main circuit
        self._add_components(circuit.components)
        
        # Add components from all subcircuits (flatten hierarchy for now)
        for subcircuit in circuit._subcircuits:
            logger.info(f"Processing subcircuit {subcircuit.name} with {len(subcircuit.components)} components")
            self._add_components(subcircuit.components)
        
        # Add connections from main circuit
        self._add_connections(circuit.nets)
        
        # Add connections from subcircuits
        for subcircuit in circuit._subcircuits:
            self._add_connections(subcircuit.nets)
        
        # Set title block
        self._set_title_block(circuit)
        
        # Save schematic
        output_path = self.output_dir / f"{self.project_name}.kicad_sch"
        self.schematic.save(str(output_path), preserve_format=True)
        
        # Create KiCad project file (.kicad_pro)
        project_file_path = self.output_dir / f"{self.project_name}.kicad_pro"
        self._create_project_file(project_file_path)
        
        # Validate output
        issues = self.schematic.validate()
        if issues:
            logger.warning(f"Generated schematic has {len(issues)} validation issues")
            for issue in issues[:3]:  # Log first 3 issues
                logger.warning(f"Validation: {issue}")
        
        logger.info(f"Generated schematic: {output_path}")
        return str(output_path)
    
    def _add_components(self, components) -> None:
        """Add components to schematic using modern API."""
        # Handle both list and dict formats
        if isinstance(components, dict):
            component_list = list(components.values())
        else:
            component_list = components if components else []
            
        logger.debug(f"Adding {len(component_list)} components")
        
        for component in component_list:
            try:
                # Convert circuit-synth component to kicad-sch-api component
                kicad_component = self.schematic.components.add(
                    lib_id=self._get_lib_id(component),
                    reference=component.ref,
                    value=component.value or "",
                    position=self._get_position(component),
                    footprint=getattr(component, 'footprint', None)
                )
                
                # Set additional properties
                self._set_component_properties(kicad_component, component)
                
                # Track mapping
                self._component_map[component.ref] = kicad_component
                
                logger.debug(f"Added component {component.ref}")
                
            except Exception as e:
                logger.error(f"Failed to add component {component.ref}: {e}")
                raise
    
    def _add_connections(self, nets) -> None:
        """Add wire connections using modern API."""
        logger.debug(f"Adding connections for {len(nets) if hasattr(nets, '__len__') else 'unknown'} nets")
        
        # Handle different net formats (dict vs list)
        net_items = nets.items() if isinstance(nets, dict) else enumerate(nets)
        
        for net_key, net_value in net_items:
            try:
                # Handle both Net objects and simple values
                if hasattr(net_value, 'connections'):
                    # Real Net object
                    net_name = getattr(net_value, 'name', str(net_key))
                    connections = net_value.connections
                elif hasattr(net_value, 'name'):
                    # Net object without connections
                    net_name = net_value.name
                    connections = []
                else:
                    # String or other simple type
                    net_name = str(net_key)
                    connections = []
                
                logger.debug(f"Processing net {net_name} with {len(connections)} connections")
                
                # For now, skip wire creation since we need proper connection data
                # TODO: Implement proper connection mapping from circuit-synth to kicad-sch-api
                
            except Exception as e:
                logger.error(f"Failed to process net {net_key}: {e}")
                # Continue with other nets
    
    def _create_net_wires(self, components: List[Any], net: Net) -> None:
        """Create wire connections for a net."""
        # For now, create simple point-to-point connections
        # TODO: Implement intelligent wire routing
        
        if len(components) < 2:
            return
        
        # Connect first component to all others (star topology)
        first_comp = components[0]
        first_pos = first_comp.position
        
        for other_comp in components[1:]:
            other_pos = other_comp.position
            
            # Create wire between components
            wire = self.schematic.add_wire(
                start_point=(first_pos.x, first_pos.y),
                end_point=(other_pos.x, other_pos.y)
            )
            logger.debug(f"Created wire in net {net.name}")
    
    def _get_lib_id(self, component: Component) -> str:
        """Get KiCad library ID for component."""
        # Use the actual symbol from the component first
        if hasattr(component, 'symbol') and component.symbol:
            lib_id = component.symbol
            logger.debug(f"Using component symbol: {component.ref} -> {lib_id}")
            return lib_id
        
        # Fallback to type mapping if no symbol
        type_mapping = {
            'resistor': 'Device:R',
            'capacitor': 'Device:C',
            'inductor': 'Device:L',
            'diode': 'Device:D',
            'led': 'Device:LED',
            'transistor': 'Device:Q_NPN_BEC',
            'mosfet': 'Device:Q_NMOS_GSD',
            'ic': 'Device:U',  # Generic IC
        }
        
        comp_type = getattr(component, 'type', 'ic').lower()
        lib_id = type_mapping.get(comp_type, 'Device:U')
        
        logger.debug(f"Using type mapping: {component.ref} type '{comp_type}' -> {lib_id}")
        return lib_id
    
    def _get_position(self, component: Component) -> Tuple[float, float]:
        """Get component position for placement."""
        # Use existing position if available
        if hasattr(component, 'position') and component.position:
            pos = component.position
            if hasattr(pos, 'x') and hasattr(pos, 'y'):
                return (float(pos.x), float(pos.y))
            elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
                return (float(pos[0]), float(pos[1]))
        
        # Default to origin - placement will be handled separately
        return (100.0, 100.0)
    
    def _set_component_properties(self, kicad_component: Any, circuit_component: Component) -> None:
        """Set component properties from circuit-synth component."""
        # Set standard properties
        if hasattr(circuit_component, 'footprint') and circuit_component.footprint:
            kicad_component.footprint = circuit_component.footprint
        
        # Set custom properties
        if hasattr(circuit_component, 'properties'):
            for key, value in circuit_component.properties.items():
                kicad_component.set_property(key, str(value))
        
        # Set manufacturing properties if available
        for prop in ['MPN', 'Manufacturer', 'Datasheet', 'Description']:
            if hasattr(circuit_component, prop.lower()):
                value = getattr(circuit_component, prop.lower())
                if value:
                    kicad_component.set_property(prop, str(value))
    
    def _set_title_block(self, circuit: Circuit) -> None:
        """Set schematic title block information."""
        title_block = self.schematic.title_block
        
        # Set basic information
        title_block['title'] = getattr(circuit, 'name', self.project_name)
        
        if hasattr(circuit, 'description'):
            title_block['comment1'] = circuit.description
        
        # Add generation timestamp
        import datetime
        title_block['date'] = datetime.datetime.now().strftime("%Y-%m-%d")
        title_block['comment4'] = "Generated by circuit-synth with kicad-sch-api"
    
    def _create_project_file(self, project_path: Path) -> None:
        """Create a basic KiCad project file."""
        project_content = f'''{{
  "board": {{
    "3dviewports": [],
    "design_rules": {{
      "rules": {{
        "solder_mask_clearance": 0.0,
        "solder_mask_min_width": 0.0
      }}
    }},
    "layer_presets": [],
    "viewports": []
  }},
  "boards": [],
  "cvpcb": {{
    "equivalence_files": []
  }},
  "libraries": {{
    "pinned_footprint_libs": [],
    "pinned_symbol_libs": []
  }},
  "meta": {{
    "filename": "{self.project_name}.kicad_pro",
    "version": 1
  }},
  "net_settings": {{
    "classes": [
      {{
        "bus_width": 12,
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.2,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Default",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "track_width": 0.25,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6
      }}
    ],
    "meta": {{
      "version": 3
    }}
  }},
  "pcbnew": {{
    "last_paths": {{
      "gencad": "",
      "idf": "",
      "netlist": "",
      "specctra_dsn": "",
      "step": "",
      "vrml": ""
    }},
    "page_layout_descr_file": ""
  }},
  "schematic": {{
    "annotate_start_num": 0,
    "drawing": {{
      "dashed_lines_dash_length_ratio": 12.0,
      "dashed_lines_gap_length_ratio": 3.0,
      "default_line_thickness": 6.0,
      "default_text_size": 50.0,
      "field_names": [],
      "intersheets_ref_own_page": false,
      "intersheets_ref_prefix": "",
      "intersheets_ref_short": false,
      "intersheets_ref_show": false,
      "intersheets_ref_suffix": "",
      "junction_size_choice": 3,
      "label_size_ratio": 0.375,
      "pin_symbol_size": 25.0,
      "text_offset_ratio": 0.15
    }},
    "legacy_lib_dir": "",
    "legacy_lib_list": [],
    "meta": {{
      "version": 1
    }},
    "net_format_name": "",
    "page_layout_descr_file": "",
    "plot_directory": "",
    "spice_current_sheet_as_root": false,
    "spice_external_command": "spice \\"%I\\"",
    "spice_model_current_sheet_as_root": true,
    "spice_save_all_currents": false,
    "spice_save_all_voltages": false,
    "subpart_first_id": 65,
    "subpart_id_separator": 0
  }},
  "sheets": [
    [
      "e13de29e-9398-4197-9b9d-b109b3ca07a6",
      ""
    ]
  ],
  "text_variables": {{}}
}}'''
        
        with open(project_path, 'w') as f:
            f.write(project_content)
    
    def _add_positioned_component(self, comp_data: Dict) -> None:
        """Add a component with pre-calculated position from legacy system."""
        try:
            # Extract component information
            lib_id = comp_data.get('symbol', comp_data.get('lib_id', 'Device:U'))
            reference = comp_data.get('ref', comp_data.get('reference', 'U'))
            value = comp_data.get('value', '')
            position = comp_data.get('position', (100.0, 100.0))
            footprint = comp_data.get('footprint', None)
            
            # Ensure position is a tuple of floats
            if isinstance(position, dict):
                pos = (float(position.get('x', 100)), float(position.get('y', 100)))
            elif isinstance(position, (list, tuple)) and len(position) >= 2:
                pos = (float(position[0]), float(position[1]))
            else:
                pos = (100.0, 100.0)
            
            # Add component with kicad-sch-api
            kicad_component = self.schematic.components.add(
                lib_id=lib_id,
                reference=reference,
                value=value,
                position=pos,
                footprint=footprint
            )
            
            # Set additional properties
            if 'properties' in comp_data:
                for key, val in comp_data['properties'].items():
                    kicad_component.set_property(key, str(val))
            
            # Track mapping
            self._component_map[reference] = kicad_component
            
            logger.debug(f"Added positioned component {reference} at {pos}")
            
        except Exception as e:
            logger.error(f"Failed to add positioned component {comp_data.get('ref', 'unknown')}: {e}")
            raise
    
    def _add_net_data(self, net_data: Dict) -> None:
        """Add net data from legacy system (labels only, no wires)."""
        try:
            # Legacy system handles hierarchical labels, not wires
            # This is a placeholder for future net data integration
            net_name = net_data.get('name', 'unknown')
            logger.debug(f"Processing net data for {net_name}")
            
        except Exception as e:
            logger.error(f"Failed to process net data: {e}")
    
    def _set_title_block_from_data(self, title_info: Dict) -> None:
        """Set title block from legacy system data."""
        title_block = self.schematic.title_block
        
        if 'title' in title_info:
            title_block['title'] = title_info['title']
        if 'description' in title_info:
            title_block['comment1'] = title_info['description']
        if 'date' in title_info:
            title_block['date'] = title_info['date']
        else:
            import datetime
            title_block['date'] = datetime.datetime.now().strftime("%Y-%m-%d")
            
        title_block['comment4'] = "Generated by circuit-synth with kicad-sch-api"


def generate_kicad_schematic_modern(
    circuit: Circuit,
    output_dir: str = ".",
    project_name: str = "circuit"
) -> str:
    """
    Generate KiCad schematic using modern kicad-sch-api.
    
    Args:
        circuit: Circuit object to convert
        output_dir: Directory for output files
        project_name: Base name for generated files
    
    Returns:
        str: Path to generated .kicad_sch file
    
    Raises:
        ImportError: If kicad-sch-api is not available
        RuntimeError: If generation fails
    """
    if not KiCadConfig.use_modern_sch_api():
        raise RuntimeError(
            "Modern schematic API is disabled. "
            "Enable with: export USE_MODERN_SCH_API=true"
        )
    
    validation_error = validate_modern_api_requirements()
    if validation_error:
        raise RuntimeError(validation_error)
    
    generator = ModernKiCadGenerator(output_dir, project_name)
    return generator.generate_schematic(circuit)


# Maintain backward compatibility function name
def generate_kicad_schematic(
    circuit: Circuit,
    output_dir: str = ".",
    project_name: str = "circuit",
    use_modern: Optional[bool] = None
) -> str:
    """
    Generate KiCad schematic using FORCED modern API only.
    
    Args:
        circuit: Circuit object to convert
        output_dir: Directory for output files  
        project_name: Base name for generated files
        use_modern: Override for modern API usage (None = auto-detect)
    
    Returns:
        str: Path to generated .kicad_sch file
    """
    logger.info("Using modern kicad-sch-api generator")
    
    # Check API availability
    if not KICAD_SCH_API_AVAILABLE:
        raise RuntimeError(
            "kicad-sch-api is required but not available. "
            "Install with: pip install kicad-sch-api>=0.1.1"
        )
    
    generator = ModernKiCadGenerator(output_dir, project_name)
    return generator.generate_schematic(circuit)