"""Bulk operations for schematic components."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..core.types import Point
from ..core.types import SchematicSymbol as Component


@dataclass
class Position:
    x: float
    y: float
    angle: float


@dataclass
class Property:
    key: str
    value: str
    id: int
    at: Position


from .search_engine import SearchCriterion as SearchCriteria
from .search_engine import SearchEngine


class OperationType(Enum):
    """Types of bulk operations."""

    UPDATE_PROPERTY = "update_property"
    MOVE = "move"
    DELETE = "delete"
    DUPLICATE = "duplicate"
    REPLACE_SYMBOL = "replace_symbol"
    UPDATE_VALUE = "update_value"
    UPDATE_FOOTPRINT = "update_footprint"
    ADD_PROPERTY = "add_property"
    REMOVE_PROPERTY = "remove_property"


@dataclass
class BulkOperation:
    """Represents a bulk operation to perform."""

    operation_type: OperationType
    parameters: Dict[str, Any]
    filter_func: Optional[Callable[[Component], bool]] = None

    def applies_to(self, component: Component) -> bool:
        """Check if operation applies to component."""
        if self.filter_func:
            return self.filter_func(component)
        return True


@dataclass
class OperationResult:
    """Result of a bulk operation."""

    success: bool
    affected_components: List[str]  # UUIDs
    errors: List[str]
    warnings: List[str]

    @property
    def affected_count(self) -> int:
        """Number of affected components."""
        return len(self.affected_components)


class BulkOperations:
    """Performs bulk operations on schematic components."""

    def __init__(self, components: List[Component]):
        """Initialize with components."""
        self.components = {comp.uuid: comp for comp in components}
        # Create a temporary schematic for SearchEngine
        from ..core.types import Schematic

        temp_schematic = Schematic()
        temp_schematic.components = components
        self.search_engine = SearchEngine(temp_schematic)
        self._operation_history: List[Tuple[BulkOperation, OperationResult]] = []

    def execute_operation(
        self,
        operation: BulkOperation,
        target_components: Optional[List[Component]] = None,
    ) -> OperationResult:
        """Execute a bulk operation on components."""
        # Determine target components
        if target_components is None:
            targets = [c for c in self.components.values() if operation.applies_to(c)]
        else:
            targets = [c for c in target_components if operation.applies_to(c)]

        # Execute operation based on type
        if operation.operation_type == OperationType.UPDATE_PROPERTY:
            result = self._update_property(targets, operation.parameters)
        elif operation.operation_type == OperationType.MOVE:
            result = self._move_components(targets, operation.parameters)
        elif operation.operation_type == OperationType.DELETE:
            result = self._delete_components(targets)
        elif operation.operation_type == OperationType.DUPLICATE:
            result = self._duplicate_components(targets, operation.parameters)
        elif operation.operation_type == OperationType.REPLACE_SYMBOL:
            result = self._replace_symbol(targets, operation.parameters)
        elif operation.operation_type == OperationType.UPDATE_VALUE:
            result = self._update_value(targets, operation.parameters)
        elif operation.operation_type == OperationType.UPDATE_FOOTPRINT:
            result = self._update_footprint(targets, operation.parameters)
        elif operation.operation_type == OperationType.ADD_PROPERTY:
            result = self._add_property(targets, operation.parameters)
        elif operation.operation_type == OperationType.REMOVE_PROPERTY:
            result = self._remove_property(targets, operation.parameters)
        else:
            result = OperationResult(
                success=False,
                affected_components=[],
                errors=[f"Unknown operation type: {operation.operation_type}"],
                warnings=[],
            )

        # Record operation
        self._operation_history.append((operation, result))
        return result

    def _update_property(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Update property on components."""
        property_name = params.get("property_name")
        new_value = params.get("new_value")

        if not property_name:
            return OperationResult(
                success=False,
                affected_components=[],
                errors=["Property name not specified"],
                warnings=[],
            )

        affected = []
        errors = []

        for comp in components:
            try:
                # Find property
                prop = next(
                    (p for p in comp.properties if p.key == property_name), None
                )
                if prop:
                    prop.value = str(new_value)
                    affected.append(comp.uuid)
                else:
                    # Add property if it doesn't exist
                    comp.properties.append(
                        Property(
                            key=property_name,
                            value=str(new_value),
                            id=len(comp.properties),
                            at=comp.at,
                        )
                    )
                    affected.append(comp.uuid)
            except Exception as e:
                errors.append(f"Error updating {comp.reference}: {str(e)}")

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=[],
        )

    def _move_components(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Move components by offset."""
        offset_x = params.get("offset_x", 0)
        offset_y = params.get("offset_y", 0)

        affected = []
        errors = []

        for comp in components:
            try:
                # Handle both 'at' and 'position' attributes for compatibility
                if hasattr(comp, "at"):
                    comp.at.x += offset_x
                    comp.at.y += offset_y
                elif hasattr(comp, "position"):
                    comp.position.x += offset_x
                    comp.position.y += offset_y
                else:
                    raise AttributeError(
                        f"Component {comp.reference} has neither 'at' nor 'position' attribute"
                    )

                # Also move properties if they have position info
                if hasattr(comp, "properties"):
                    if isinstance(comp.properties, dict):
                        # Properties stored as dict - skip position update
                        pass
                    else:
                        # Properties stored as list with position info
                        for prop in comp.properties:
                            if hasattr(prop, "at") and prop.at:
                                prop.at.x += offset_x
                                prop.at.y += offset_y

                affected.append(comp.uuid)
            except Exception as e:
                errors.append(f"Error moving {comp.reference}: {str(e)}")

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=[],
        )

    def _delete_components(self, components: List[Component]) -> OperationResult:
        """Delete components."""
        affected = []
        errors = []
        warnings = []

        for comp in components:
            try:
                # Check for connections
                if hasattr(comp, "pins") and comp.pins:
                    connected_pins = [
                        p for p in comp.pins if hasattr(p, "net") and p.net
                    ]
                    if connected_pins:
                        warnings.append(
                            f"{comp.reference} has {len(connected_pins)} connected pins"
                        )

                # Remove from collection
                if comp.uuid in self.components:
                    del self.components[comp.uuid]
                    affected.append(comp.uuid)
            except Exception as e:
                errors.append(f"Error deleting {comp.reference}: {str(e)}")

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=warnings,
        )

    def _duplicate_components(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Duplicate components with offset."""
        offset_x = params.get("offset_x", 25.4)  # Default 1 inch
        offset_y = params.get("offset_y", 0)
        suffix = params.get("suffix", "_copy")

        affected = []
        errors = []
        new_components = []

        for comp in components:
            try:
                # Create copy
                import copy

                new_comp = copy.deepcopy(comp)

                # Generate new UUID
                import uuid

                new_comp.uuid = str(uuid.uuid4())

                # Update reference
                new_comp.reference = f"{comp.reference}{suffix}"

                # Update position
                new_comp.at.x += offset_x
                new_comp.at.y += offset_y

                # Update property positions
                for prop in new_comp.properties:
                    if prop.at:
                        prop.at.x += offset_x
                        prop.at.y += offset_y

                # Add to collection
                self.components[new_comp.uuid] = new_comp
                new_components.append(new_comp)
                affected.append(new_comp.uuid)

            except Exception as e:
                errors.append(f"Error duplicating {comp.reference}: {str(e)}")

        # Update search engine
        if new_components:
            all_components = list(self.components.values())
            from ..core.types import Schematic

            temp_schematic = Schematic()
            temp_schematic.components = all_components
            self.search_engine = SearchEngine(temp_schematic)

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=[],
        )

    def _replace_symbol(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Replace symbol library reference."""
        new_lib_id = params.get("new_lib_id")

        if not new_lib_id:
            return OperationResult(
                success=False,
                affected_components=[],
                errors=["New library ID not specified"],
                warnings=[],
            )

        affected = []
        errors = []
        warnings = []

        for comp in components:
            try:
                old_lib_id = comp.lib_id
                comp.lib_id = new_lib_id
                affected.append(comp.uuid)

                # Check if pin count might differ
                if ":" in old_lib_id and ":" in new_lib_id:
                    old_symbol = old_lib_id.split(":")[1]
                    new_symbol = new_lib_id.split(":")[1]
                    if old_symbol != new_symbol:
                        warnings.append(
                            f"{comp.reference}: Symbol changed from {old_symbol} to {new_symbol}"
                        )

            except Exception as e:
                errors.append(f"Error replacing symbol for {comp.reference}: {str(e)}")

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=warnings,
        )

    def _update_value(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Update component values."""
        new_value = params.get("new_value")
        pattern = params.get("pattern")  # Optional regex pattern for replacement

        if not new_value and not pattern:
            return OperationResult(
                success=False,
                affected_components=[],
                errors=["New value or pattern not specified"],
                warnings=[],
            )

        affected = []
        errors = []

        for comp in components:
            try:
                if pattern:
                    # Use regex replacement
                    new_val = re.sub(pattern, new_value, comp.value)
                    comp.value = new_val
                else:
                    # Direct replacement
                    comp.value = new_value

                # Update value property
                value_prop = next(
                    (p for p in comp.properties if p.key == "Value"), None
                )
                if value_prop:
                    value_prop.value = comp.value

                affected.append(comp.uuid)

            except Exception as e:
                errors.append(f"Error updating value for {comp.reference}: {str(e)}")

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=[],
        )

    def _update_footprint(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Update component footprints."""
        new_footprint = params.get("new_footprint")

        if not new_footprint:
            return OperationResult(
                success=False,
                affected_components=[],
                errors=["New footprint not specified"],
                warnings=[],
            )

        affected = []
        errors = []
        warnings = []

        for comp in components:
            try:
                # Update footprint property
                footprint_prop = next(
                    (p for p in comp.properties if p.key == "Footprint"), None
                )
                if footprint_prop:
                    old_footprint = footprint_prop.value
                    footprint_prop.value = new_footprint
                    if old_footprint and old_footprint != new_footprint:
                        warnings.append(
                            f"{comp.reference}: Changed from {old_footprint} to {new_footprint}"
                        )
                else:
                    # Add footprint property
                    comp.properties.append(
                        Property(
                            key="Footprint",
                            value=new_footprint,
                            id=len(comp.properties),
                            at=comp.at,
                        )
                    )

                affected.append(comp.uuid)

            except Exception as e:
                errors.append(
                    f"Error updating footprint for {comp.reference}: {str(e)}"
                )

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=warnings,
        )

    def _add_property(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Add property to components."""
        property_key = params.get("key")
        property_value = params.get("value", "")

        if not property_key:
            return OperationResult(
                success=False,
                affected_components=[],
                errors=["Property key not specified"],
                warnings=[],
            )

        affected = []
        errors = []
        warnings = []

        for comp in components:
            try:
                # Check if property already exists
                existing = next(
                    (p for p in comp.properties if p.key == property_key), None
                )
                if existing:
                    warnings.append(
                        f"{comp.reference}: Property '{property_key}' already exists"
                    )
                    continue

                # Add property
                comp.properties.append(
                    Property(
                        key=property_key,
                        value=str(property_value),
                        id=len(comp.properties),
                        at=comp.at,
                    )
                )

                affected.append(comp.uuid)

            except Exception as e:
                errors.append(f"Error adding property to {comp.reference}: {str(e)}")

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=warnings,
        )

    def _remove_property(
        self, components: List[Component], params: Dict[str, Any]
    ) -> OperationResult:
        """Remove property from components."""
        property_key = params.get("key")

        if not property_key:
            return OperationResult(
                success=False,
                affected_components=[],
                errors=["Property key not specified"],
                warnings=[],
            )

        affected = []
        errors = []
        warnings = []

        # Protected properties that shouldn't be removed
        protected_keys = {"Reference", "Value", "Footprint"}

        if property_key in protected_keys:
            return OperationResult(
                success=False,
                affected_components=[],
                errors=[f"Cannot remove protected property '{property_key}'"],
                warnings=[],
            )

        for comp in components:
            try:
                # Find and remove property
                original_count = len(comp.properties)
                comp.properties = [p for p in comp.properties if p.key != property_key]

                if len(comp.properties) < original_count:
                    affected.append(comp.uuid)

                    # Re-index properties
                    for i, prop in enumerate(comp.properties):
                        prop.id = i
                else:
                    warnings.append(
                        f"{comp.reference}: Property '{property_key}' not found"
                    )

            except Exception as e:
                errors.append(
                    f"Error removing property from {comp.reference}: {str(e)}"
                )

        return OperationResult(
            success=len(errors) == 0,
            affected_components=affected,
            errors=errors,
            warnings=warnings,
        )

    def create_operation_batch(self) -> "OperationBatch":
        """Create a batch for multiple operations."""
        return OperationBatch(self)

    def get_operation_history(self) -> List[Tuple[BulkOperation, OperationResult]]:
        """Get operation history."""
        return self._operation_history.copy()


class OperationBatch:
    """Batch multiple operations together."""

    def __init__(self, bulk_ops: BulkOperations):
        """Initialize batch."""
        self.bulk_ops = bulk_ops
        self.operations: List[Tuple[BulkOperation, Optional[List[Component]]]] = []

    def add_operation(
        self,
        operation: BulkOperation,
        target_components: Optional[List[Component]] = None,
    ):
        """Add operation to batch."""
        self.operations.append((operation, target_components))
        return self

    def execute(self) -> List[OperationResult]:
        """Execute all operations in batch."""
        results = []

        for operation, targets in self.operations:
            result = self.bulk_ops.execute_operation(operation, targets)
            results.append(result)

            # Stop on error if requested
            if (
                not result.success
                and hasattr(operation, "stop_on_error")
                and operation.stop_on_error
            ):
                break

        return results


# Helper functions for common operations
def create_value_update_operation(
    new_value: str, filter_func: Optional[Callable[[Component], bool]] = None
) -> BulkOperation:
    """Create operation to update component values."""
    return BulkOperation(
        operation_type=OperationType.UPDATE_VALUE,
        parameters={"new_value": new_value},
        filter_func=filter_func,
    )


def create_move_operation(
    offset_x: float,
    offset_y: float,
    filter_func: Optional[Callable[[Component], bool]] = None,
) -> BulkOperation:
    """Create operation to move components."""
    return BulkOperation(
        operation_type=OperationType.MOVE,
        parameters={"offset_x": offset_x, "offset_y": offset_y},
        filter_func=filter_func,
    )


def create_footprint_update_operation(
    new_footprint: str, filter_func: Optional[Callable[[Component], bool]] = None
) -> BulkOperation:
    """Create operation to update footprints."""
    return BulkOperation(
        operation_type=OperationType.UPDATE_FOOTPRINT,
        parameters={"new_footprint": new_footprint},
        filter_func=filter_func,
    )
