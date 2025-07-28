"""
LLM-based schematic component placement using ADK infrastructure.

This agent uses Google ADK to intelligently place schematic components based on:
- Component bounding boxes and dimensions
- Pin locations and orientations
- Net connections between components
- Electrical design best practices
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from google.adk import Runner

# ADK imports
from google.adk.agents import Agent, LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.sessions import InMemorySessionService, Session
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types
from pydantic import BaseModel, Field

# Local imports
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

from .collision_detection import BBox
from .connection_aware_collision_manager import ConnectionAwareCollisionManager
from .symbol_geometry import SymbolBoundingBoxCalculator

logger = logging.getLogger(__name__)


@dataclass
class ComponentPlacement:
    """Represents placement of a single component."""

    ref: str
    x: float
    y: float
    rotation: int = 0  # 0, 90, 180, or 270 degrees


# Pydantic models for ADK output schema
class PlacementOutput(BaseModel):
    """Single component placement output."""

    ref: str = Field(description="Component reference designator")
    x: float = Field(description="X coordinate in millimeters")
    y: float = Field(description="Y coordinate in millimeters")
    rotation: int = Field(
        default=0, description="Rotation in degrees (0, 90, 180, or 270)"
    )


class SchematicPlacementResponse(BaseModel):
    """Response from the LLM placement agent."""

    placements: List[PlacementOutput] = Field(
        description="List of component placements"
    )


class LLMPlacementDataPrep:
    """Prepares component data for LLM placement"""

    def __init__(self):
        self.bbox_calc = SymbolBoundingBoxCalculator()

    def extract_component_data(self, circuit, sheet_size=(297, 210)) -> Dict[str, Any]:
        """
        Extract component and connection data for LLM.

        Returns:
            Dict with components, connections, and sheet info
        """
        components = []
        connections = []
        net_map = {}  # Track which components connect to which nets

        # Extract components
        for comp in circuit.components:
            try:
                # Get symbol data
                symbol_data = SymbolLibCache.get_symbol_data(comp.lib_id)

                # Calculate bounding box
                bbox = self.bbox_calc.calculate_bounding_box(symbol_data)
                # bbox is a tuple (min_x, min_y, max_x, max_y)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                # Get pin information
                pins = []
                for pin in comp.pins:
                    pin_info = {
                        "name": pin.name,
                        "number": pin.number,
                        "type": getattr(pin, "electrical_type", "passive"),
                        "x": pin.position.x if pin.position else 0,
                        "y": pin.position.y if pin.position else 0,
                    }
                    pins.append(pin_info)

                    # Track net connections
                    if hasattr(comp, "_pin_nets") and pin.name in comp._pin_nets:
                        net_name = comp._pin_nets[pin.name]
                        if net_name not in net_map:
                            net_map[net_name] = []
                        net_map[net_name].append(
                            {"ref": comp.reference, "pin": pin.name}
                        )

                comp_data = {
                    "ref": comp.reference,
                    "symbol": comp.lib_id,
                    "value": getattr(comp, "value", ""),
                    "width": width,
                    "height": height,
                    "pins": pins,
                    "type": self._classify_component(comp.lib_id),
                }
                components.append(comp_data)

            except Exception as e:
                logger.warning(f"Failed to extract data for {comp.reference}: {e}")
                # Provide minimal data
                comp_data = {
                    "ref": comp.reference,
                    "symbol": comp.lib_id,
                    "value": getattr(comp, "value", ""),
                    "width": 25.4,  # Default 1 inch
                    "height": 12.7,  # Default 0.5 inch
                    "pins": [],
                    "type": "unknown",
                }
                components.append(comp_data)

        # Extract connections from net map
        for net_name, net_connections in net_map.items():
            if len(net_connections) > 1:  # Only include nets with multiple connections
                connections.append({"net": net_name, "connections": net_connections})

        return {
            "sheet_size": {"width": sheet_size[0], "height": sheet_size[1]},
            "components": components,
            "connections": connections,
        }

    def _classify_component(self, symbol: str) -> str:
        """Classify component type from symbol name"""
        symbol_lower = symbol.lower()

        if "mcu" in symbol_lower or "arduino" in symbol_lower:
            return "microcontroller"
        elif "regulator" in symbol_lower or "lm78" in symbol_lower:
            return "voltage_regulator"
        elif "connector" in symbol_lower or "usb" in symbol_lower:
            return "connector"
        elif "led" in symbol_lower:
            return "led"
        elif symbol.startswith("Device:R"):
            return "resistor"
        elif symbol.startswith("Device:C"):
            return "capacitor"
        elif "switch" in symbol_lower or "button" in symbol_lower:
            return "switch"
        elif "sensor" in symbol_lower:
            return "sensor"
        else:
            return "generic"


def create_schematic_placement_agent(model="gemini-1.5-flash"):
    """Create the schematic placement agent"""

    instruction = """You are an expert electronics engineer specializing in schematic layout.
Your task is to place electronic components on a schematic sheet for optimal readability and organization.

PLACEMENT RULES:
1. Signal Flow: Arrange components left-to-right following signal flow (inputs→processing→outputs)
2. Power Distribution: Place voltage regulators and power components at the top
3. Connectors: Place input connectors on the left edge, output connectors on the right edge
4. Grouping: Keep functionally related components together
5. Spacing: Maintain at least 10mm between components to allow for wiring
6. Microcontrollers: Place centrally as they often connect to many other components
7. Decoupling Capacitors: Place very close (within 20mm) to their associated ICs
8. LEDs/Indicators: Place at bottom or edges for visibility
9. Test Points: Place at edges for easy access

COORDINATE SYSTEM:
- Origin (0,0) is at top-left
- X increases to the right
- Y increases downward
- Units are in millimeters
- Rotation: 0=normal, 90=rotated right, 180=upside down, 270=rotated left

INPUT FORMAT:
You'll receive:
- Sheet dimensions (width x height in mm)
- Component list with dimensions and pin information
- Net connections showing how components connect

OUTPUT FORMAT:
Return a JSON object with a "placements" array. Each placement must have:
- ref: component reference (e.g., "U1", "R1")
- x: X coordinate of component center
- y: Y coordinate of component center  
- rotation: 0, 90, 180, or 270 degrees

EXAMPLE PLACEMENT STRATEGY:
For a typical Arduino project:
1. USB connector (J1) at (20, 50) - left edge for input
2. Voltage regulator (U2) at (100, 30) - top area for power
3. Arduino (U1) at (150, 100) - central hub
4. LED (D1) at (250, 180) - bottom for visibility
5. Capacitors near their ICs

Remember to check component dimensions to avoid overlaps!
"""

    return Agent(
        name="schematic_placement",
        model=model,
        description="Places schematic components intelligently based on connections and best practices",
        instruction=instruction,
        output_schema=SchematicPlacementResponse,
    )


# Global agent instance (created lazily)
_schematic_placement_agent = None


def get_schematic_placement_agent():
    """Get or create the schematic placement agent."""
    global _schematic_placement_agent
    if _schematic_placement_agent is None:
        _schematic_placement_agent = create_schematic_placement_agent()
    return _schematic_placement_agent


async def place_components_with_llm(
    circuit, sheet_size=(297, 210), model=None
) -> List[ComponentPlacement]:
    """
    Use LLM to place schematic components intelligently.

    Args:
        circuit: Circuit object with components and nets
        sheet_size: (width, height) in mm
        model: Optional model name override

    Returns:
        List of ComponentPlacement objects
    """
    # Use custom model if provided
    if model:
        agent = create_schematic_placement_agent(model)
    else:
        agent = get_schematic_placement_agent()

    # Prepare component data
    data_prep = LLMPlacementDataPrep()
    circuit_data = data_prep.extract_component_data(circuit, sheet_size)

    # Create prompt
    prompt = f"""Place these electronic components on a {sheet_size[0]}x{sheet_size[1]}mm schematic sheet.

COMPONENTS:
{json.dumps(circuit_data['components'], indent=2)}

CONNECTIONS:
{json.dumps(circuit_data['connections'], indent=2)}

Provide optimal placement following schematic design best practices."""

    # Get placement from LLM
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    runner = Runner(
        app_name="schematic_placement",
        agent=agent,
        artifact_service=artifact_service,
        session_service=session_service,
    )

    # Create a session
    session = await session_service.create_session(
        app_name="schematic_placement", user_id="system"
    )

    # Create content
    content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])

    # Run the agent and collect response
    response_text = ""
    async for event in runner.run_async(
        user_id="system", session_id=session.id, new_message=content
    ):
        if event.content.parts and event.content.parts[0].text:
            response_text += event.content.parts[0].text

    # Parse response - try to extract JSON from the response text
    placements = []
    try:
        # Try to find JSON in the response
        import re

        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            response_data = json.loads(json_match.group())
            if "placements" in response_data:
                for p in response_data["placements"]:
                    placements.append(
                        ComponentPlacement(
                            ref=p["ref"],
                            x=float(p["x"]),
                            y=float(p["y"]),
                            rotation=int(p.get("rotation", 0)),
                        )
                    )
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {e}")
        logger.debug(f"Response text: {response_text}")

    return placements


class LLMPlacementManager:
    """Manages LLM placement with collision detection and fallback"""

    def __init__(self, sheet_size=(297, 210)):
        self.sheet_size = sheet_size
        self.collision_manager = ConnectionAwareCollisionManager(sheet_size)

    async def apply_llm_placement(self, circuit, components, model=None):
        """
        Apply LLM placement to components with collision detection.

        Args:
            circuit: Circuit object
            components: List of components to place
            model: Optional model override

        Returns:
            Success boolean
        """
        try:
            # Get LLM placements
            placements = await place_components_with_llm(
                circuit, self.sheet_size, model
            )

            if not placements:
                logger.warning("LLM returned no placements")
                return False

            # Create placement map
            placement_map = {p.ref: p for p in placements}

            # Apply placements with collision detection
            placed_count = 0
            for comp in components:
                if comp.reference in placement_map:
                    p = placement_map[comp.reference]

                    # Get component dimensions
                    bbox = comp.get_bounding_box()
                    if bbox:
                        width = bbox.x2 - bbox.x1
                        height = bbox.y2 - bbox.y1
                    else:
                        width = 20.0
                        height = 20.0

                    # Check if LLM position is collision-free
                    test_bbox = BBox(
                        p.x - width / 2 - 0.5,
                        p.y - height / 2 - 0.5,
                        p.x + width / 2 + 0.5,
                        p.y + height / 2 + 0.5,
                    )

                    # Try to add the bbox - if it succeeds, there's no collision
                    if self.collision_manager.detector.add_bbox(test_bbox):
                        # Position is free, place component
                        comp.position.x = p.x
                        comp.position.y = p.y
                        if p.rotation:
                            comp.rotation = p.rotation
                        placed_count += 1
                        logger.info(
                            f"Placed {comp.reference} at LLM position ({p.x}, {p.y}) rotation={p.rotation}"
                        )
                    else:
                        # Position has collision, find nearby free position
                        logger.info(
                            f"LLM position for {comp.reference} has collision, finding alternative"
                        )
                        # Use the collision manager's place_symbol method to find a free position
                        new_pos = self.collision_manager.place_symbol(width, height)

                        comp.position.x = new_pos[0]
                        comp.position.y = new_pos[1]
                        if p.rotation:
                            comp.rotation = p.rotation
                        placed_count += 1
                        logger.info(
                            f"Placed {comp.reference} at adjusted position {new_pos}"
                        )

            logger.info(
                f"LLM placement: {placed_count}/{len(components)} components placed"
            )
            return placed_count == len(components)

        except Exception as e:
            logger.error(f"LLM placement failed: {e}")
            return False
