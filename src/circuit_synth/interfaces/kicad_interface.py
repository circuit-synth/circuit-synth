"""
KiCad Integration Abstract Interfaces

Defines abstract interfaces for KiCad integration to eliminate circular dependencies
between the legacy kicad/ and modern kicad_api/ implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


@dataclass
class GenerationResult:
    """Result of circuit generation operation"""

    success: bool
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ComponentPlacement:
    """Component placement information"""

    reference: str
    x: float
    y: float
    rotation: float = 0.0
    layer: str = "F.Cu"
    locked: bool = False


@dataclass
class NetConnection:
    """Network connection information"""

    net_name: str
    component_ref: str
    pin_number: str
    pin_name: Optional[str] = None


@dataclass
class KiCadGenerationConfig:
    """Configuration for KiCad generation operations"""

    placement_algorithm: Optional[str] = None
    generate_pcb: Optional[bool] = None
    force_regenerate: Optional[bool] = None
    paper_size: Optional[str] = None
    auto_route: Optional[bool] = None
    component_spacing: Optional[float] = None
    group_spacing: Optional[float] = None
    board_size: Optional[Tuple[float, float]] = None
    custom_settings: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.custom_settings is None:
            self.custom_settings = {}


class IKiCadIntegration(ABC):
    """
    Abstract interface for KiCad integration.

    This interface provides a unified API for both legacy and modern KiCad implementations,
    allowing the system to switch between implementations without breaking dependencies.
    """

    @abstractmethod
    def get_version(self) -> str:
        """Get the version of the KiCad integration implementation"""
        pass

    @abstractmethod
    def validate_installation(self) -> bool:
        """Validate that KiCad is properly installed and accessible"""
        pass

    @abstractmethod
    def create_schematic_generator(self) -> "ISchematicGenerator":
        """Create a schematic generator instance"""
        pass

    @abstractmethod
    def create_pcb_generator(self) -> "IPCBGenerator":
        """Create a PCB generator instance"""
        pass

    @abstractmethod
    def get_symbol_libraries(self) -> List[str]:
        """Get list of available symbol libraries"""
        pass

    @abstractmethod
    def get_footprint_libraries(self) -> List[str]:
        """Get list of available footprint libraries"""
        pass


class ISchematicGenerator(ABC):
    """
    Abstract interface for schematic generation.

    Provides a unified API for generating KiCad schematics regardless of the
    underlying implementation (legacy or modern).
    """

    @abstractmethod
    def initialize_project(self, project_path: Path, project_name: str) -> bool:
        """Initialize a new KiCad project"""
        pass

    @abstractmethod
    def add_component(
        self,
        reference: str,
        symbol_name: str,
        library: str,
        position: Tuple[float, float],
        properties: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Add a component to the schematic"""
        pass

    @abstractmethod
    def add_wire(
        self,
        start_point: Tuple[float, float],
        end_point: Tuple[float, float],
        net_name: Optional[str] = None,
    ) -> bool:
        """Add a wire connection"""
        pass

    @abstractmethod
    def add_net_connection(self, connection: NetConnection) -> bool:
        """Add a network connection between components"""
        pass

    @abstractmethod
    def set_component_property(
        self, reference: str, property_name: str, property_value: str
    ) -> bool:
        """Set a property on a component"""
        pass

    @abstractmethod
    def validate_schematic(self) -> Tuple[bool, List[str]]:
        """Validate the schematic and return any errors"""
        pass

    @abstractmethod
    def generate_netlist(self, output_path: Path) -> GenerationResult:
        """Generate netlist from schematic"""
        pass

    @abstractmethod
    def save_schematic(self, output_path: Path) -> GenerationResult:
        """Save the schematic to file"""
        pass

    @abstractmethod
    def get_component_count(self) -> int:
        """Get the number of components in the schematic"""
        pass

    @abstractmethod
    def get_net_count(self) -> int:
        """Get the number of nets in the schematic"""
        pass


class IPCBGenerator(ABC):
    """
    Abstract interface for PCB generation.

    Provides a unified API for generating KiCad PCBs regardless of the
    underlying implementation (legacy or modern).
    """

    @abstractmethod
    def initialize_pcb(self, project_path: Path, netlist_path: Path) -> bool:
        """Initialize PCB from netlist"""
        pass

    @abstractmethod
    def import_netlist(self, netlist_path: Path) -> bool:
        """Import netlist into PCB"""
        pass

    @abstractmethod
    def place_component(self, placement: ComponentPlacement) -> bool:
        """Place a component on the PCB"""
        pass

    @abstractmethod
    def auto_place_components(
        self,
        algorithm: str = "force_directed",
        constraints: Optional[Dict[str, Any]] = None,
    ) -> GenerationResult:
        """Automatically place all components using specified algorithm"""
        pass

    @abstractmethod
    def route_traces(
        self, algorithm: str = "freerouting", settings: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """Route traces between components"""
        pass

    @abstractmethod
    def set_board_outline(
        self, width: float, height: float, origin: Tuple[float, float] = (0, 0)
    ) -> bool:
        """Set the board outline dimensions"""
        pass

    @abstractmethod
    def add_via(
        self,
        position: Tuple[float, float],
        drill_size: float,
        via_size: float,
        net_name: str,
    ) -> bool:
        """Add a via to the PCB"""
        pass

    @abstractmethod
    def validate_pcb(self) -> Tuple[bool, List[str]]:
        """Validate the PCB design and return any errors"""
        pass

    @abstractmethod
    def run_drc(self) -> Tuple[bool, List[str]]:
        """Run Design Rule Check and return results"""
        pass

    @abstractmethod
    def save_pcb(self, output_path: Path) -> GenerationResult:
        """Save the PCB to file"""
        pass

    @abstractmethod
    def export_gerbers(self, output_dir: Path) -> GenerationResult:
        """Export Gerber files for manufacturing"""
        pass

    @abstractmethod
    def get_component_placements(self) -> List[ComponentPlacement]:
        """Get current component placements"""
        pass

    @abstractmethod
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing completion statistics"""
        pass


class ISymbolLibrary(ABC):
    """Abstract interface for symbol library operations"""

    @abstractmethod
    def search_symbol(
        self, query: str, library: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Search for symbols matching query"""
        pass

    @abstractmethod
    def get_symbol_info(
        self, symbol_name: str, library: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a symbol"""
        pass

    @abstractmethod
    def validate_symbol(self, symbol_name: str, library: str) -> bool:
        """Validate that a symbol exists and is accessible"""
        pass


class IFootprintLibrary(ABC):
    """Abstract interface for footprint library operations"""

    @abstractmethod
    def search_footprint(
        self, query: str, library: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Search for footprints matching query"""
        pass

    @abstractmethod
    def get_footprint_info(
        self, footprint_name: str, library: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a footprint"""
        pass

    @abstractmethod
    def validate_footprint(self, footprint_name: str, library: str) -> bool:
        """Validate that a footprint exists and is accessible"""
        pass


# Factory function type for dependency injection
KiCadIntegrationFactory = Callable[[], IKiCadIntegration]
