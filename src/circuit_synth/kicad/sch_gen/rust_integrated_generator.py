#!/usr/bin/env python3
"""
Rust-Integrated Schematic Generator

This module replaces the Python schematic generation with Rust backend while
maintaining compatibility with the existing API.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Import the original generator for fallback and other functionality
from .main_generator import SchematicGenerator as OriginalSchematicGenerator
from .circuit_loader import load_circuit_hierarchy
from ..rust_adapter import RustSchematicAdapter

logger = logging.getLogger(__name__)


class RustIntegratedSchematicGenerator(OriginalSchematicGenerator):
    """
    Schematic generator that uses Rust backend for S-expression generation.
    
    This class extends the original SchematicGenerator but replaces the
    schematic writing portion with Rust for better performance.
    """
    
    def __init__(self, output_dir: str, project_name: str, use_rust: bool = True):
        """
        Initialize the generator.
        
        Args:
            output_dir: Output directory for the project
            project_name: Name of the KiCad project
            use_rust: Whether to use Rust backend (default: True)
        """
        super().__init__(output_dir, project_name)
        self.use_rust = use_rust
        logger.info(f"🚀 RustIntegratedSchematicGenerator initialized")
        logger.info(f"  Rust backend: {'ENABLED ✅' if use_rust else 'DISABLED ❌'}")
        
    def generate_schematic_with_rust(self, circuit, output_path: str) -> None:
        """
        Generate schematic using Rust backend.
        
        Args:
            circuit: Circuit object to generate schematic for
            output_path: Path to write the .kicad_sch file
        """
        logger.info(f"🦀 Generating schematic with Rust backend...")
        
        # Create Rust adapter
        adapter = RustSchematicAdapter(circuit)
        
        # Generate schematic
        adapter.generate_schematic(output_path)
        
        logger.info(f"✅ Rust schematic generation complete: {output_path}")
        
    def generate_project(
        self,
        json_file: str,
        force_regenerate: bool = False,
        generate_pcb: bool = True,
        placement_algorithm: str = "connection_centric",
        schematic_placement: str = "connection_aware",
        draw_bounding_boxes: bool = False,
        **pcb_kwargs,
    ):
        """
        Generate KiCad project with optional Rust backend.
        
        This method overrides the parent to add Rust backend support.
        """
        logger.info(f"📋 Starting project generation...")
        logger.info(f"  Project: {self.project_name}")
        logger.info(f"  Rust backend: {'ENABLED' if self.use_rust else 'DISABLED'}")
        
        if self.use_rust:
            try:
                # Load circuit from JSON
                logger.info(f"  Loading circuit from: {json_file}")
                with open(json_file, 'r') as f:
                    circuit_data = json.load(f)
                    
                # Create project directory
                self.project_dir.mkdir(parents=True, exist_ok=True)
                
                # Load circuit hierarchy (for compatibility with existing code)
                circuit_dict, sub_dict = load_circuit_hierarchy(json_file)
                
                # For now, we'll generate the main circuit only
                # TODO: Handle hierarchical circuits
                main_circuit_name = circuit_data.get('name', 'main')
                
                # Convert to Python Circuit object format
                # This is a simplified conversion - full implementation would handle all cases
                from circuit_synth import Circuit, Component, Net
                
                circuit = Circuit(main_circuit_name)
                
                # Add components
                if 'components' in circuit_data:
                    for comp_ref, comp_data in circuit_data['components'].items():
                        comp = Component(
                            symbol=comp_data.get('symbol', ''),
                            ref=comp_ref.rstrip('0123456789'),  # Remove numbers
                            value=comp_data.get('value', '')
                        )
                        circuit.add_component(comp)
                        
                # Add nets
                if 'nets' in circuit_data:
                    for net_name, net_data in circuit_data['nets'].items():
                        net = Net(net_name)
                        if 'nodes' in net_data:
                            for node in net_data['nodes']:
                                comp_ref = node.get('component', '')
                                pin_num = node.get('pin', {}).get('number', '')
                                if comp_ref and pin_num:
                                    net.connect(comp_ref, pin_num)
                        circuit.add_net(net)
                
                # Generate schematic using Rust
                schematic_path = self.project_dir / f"{self.project_name}.kicad_sch"
                self.generate_schematic_with_rust(circuit, str(schematic_path))
                
                # Generate project file
                self._generate_project_file()
                
                # Generate PCB if requested
                if generate_pcb:
                    logger.info("  Generating PCB...")
                    # Use parent's PCB generation
                    super()._generate_pcb(
                        json_file,
                        placement_algorithm=placement_algorithm,
                        draw_bounding_boxes=draw_bounding_boxes,
                        **pcb_kwargs
                    )
                    
                logger.info(f"✅ Project generation complete: {self.project_dir}")
                
            except Exception as e:
                logger.error(f"❌ Rust backend failed: {e}")
                logger.info("  Falling back to Python implementation...")
                self.use_rust = False
                return super().generate_project(
                    json_file,
                    force_regenerate=force_regenerate,
                    generate_pcb=generate_pcb,
                    placement_algorithm=placement_algorithm,
                    schematic_placement=schematic_placement,
                    draw_bounding_boxes=draw_bounding_boxes,
                    **pcb_kwargs
                )
        else:
            # Use original Python implementation
            return super().generate_project(
                json_file,
                force_regenerate=force_regenerate,
                generate_pcb=generate_pcb,
                placement_algorithm=placement_algorithm,
                schematic_placement=schematic_placement,
                draw_bounding_boxes=draw_bounding_boxes,
                **pcb_kwargs
            )
            
    def _generate_project_file(self):
        """Generate the .kicad_pro project file."""
        import datetime
        
        project_file = {
            "meta": {
                "filename": f"{self.project_name}.kicad_pro",
                "version": 1
            },
            "project": {
                "name": self.project_name,
                "created": datetime.datetime.now().isoformat(),
                "updated": datetime.datetime.now().isoformat()
            }
        }
        
        project_path = self.project_dir / f"{self.project_name}.kicad_pro"
        with open(project_path, 'w') as f:
            json.dump(project_file, f, indent=2)
            
        logger.info(f"  Generated project file: {project_path}")


# Make this the default when imported
SchematicGenerator = RustIntegratedSchematicGenerator