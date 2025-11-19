"""
Bulk component replacement utilities.

Provides functions to replace/substitute components across circuits based on
property values, manufacturers, or other criteria.

Example:
    >>> import circuit_synth as cs
    >>>
    >>> circuit = cs.Circuit("MyDesign")
    >>> # ... add components with MPN properties ...
    >>>
    >>> # Replace all components with specific MPN
    >>> result = cs.replace_components(
    ...     circuit,
    ...     match={"MPN": "ASD123"},
    ...     update={"MPN": "FGS032", "Manufacturer": "NewCo"}
    ... )
    >>> print(f"Replaced {result.count} components")
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .circuit import Circuit


@dataclass
class ReplacementResult:
    """
    Results from bulk component replacement operation.

    Attributes:
        count: Number of components modified
        affected_components: List of component references that were modified
        warnings: List of warning messages
        errors: List of error messages
    """

    count: int
    affected_components: List[str]
    warnings: List[str]
    errors: List[str]

    def __str__(self) -> str:
        """Format result as string."""
        result = f"Replaced {self.count} components"
        if self.affected_components:
            result += f": {', '.join(self.affected_components)}"
        if self.warnings:
            result += f"\nWarnings: {len(self.warnings)}"
        if self.errors:
            result += f"\nErrors: {len(self.errors)}"
        return result


def replace_components(
    circuit: Circuit,
    match: Dict[str, str],
    update: Dict[str, str],
    dry_run: bool = False,
) -> ReplacementResult:
    """
    Replace property values for components matching criteria.

    Finds all components with properties matching the `match` criteria
    and updates their properties with values from `update`.

    Args:
        circuit: Circuit to modify
        match: Property criteria to match (e.g., {"MPN": "ASD123"})
        update: Properties to update (e.g., {"MPN": "FGS032", "Manufacturer": "NewCo"})
        dry_run: If True, don't actually modify, just return what would change

    Returns:
        ReplacementResult with count and list of affected components

    Example:
        >>> circuit = cs.Circuit("Test")
        >>> r1 = cs.Component("Device:R", ref="R", value="10k")
        >>> r1.MPN = "ASD123"
        >>> circuit.add_component(r1)
        >>> circuit.finalize_references()
        >>>
        >>> # Replace MPN
        >>> result = cs.replace_components(
        ...     circuit,
        ...     match={"MPN": "ASD123"},
        ...     update={"MPN": "FGS032"}
        ... )
        >>> print(result.count)  # 1
        >>> print(r1.MPN)  # "FGS032"
    """
    warnings = []
    errors = []
    affected = []
    count = 0

    # Iterate through all components
    for comp in circuit.components.values():
        # Check if component matches all criteria
        matches = True
        for prop_name, prop_value in match.items():
            # Check if component has this property
            if not hasattr(comp, prop_name):
                matches = False
                break

            # Check if value matches
            comp_value = getattr(comp, prop_name, None)
            if comp_value != prop_value:
                matches = False
                break

        # If component matches, update properties
        if matches:
            if not dry_run:
                for prop_name, new_value in update.items():
                    try:
                        setattr(comp, prop_name, new_value)
                    except Exception as e:
                        errors.append(
                            f"Failed to update {prop_name} on {comp.ref}: {str(e)}"
                        )

            affected.append(comp.ref)
            count += 1

    return ReplacementResult(
        count=count, affected_components=affected, warnings=warnings, errors=errors
    )


def replace_multiple(
    circuit: Circuit,
    replacements: List[Dict[str, any]],
    dry_run: bool = False,
) -> ReplacementResult:
    """
    Apply multiple replacement operations in sequence.

    Each replacement in the list should have 'match' and 'update' dicts.

    Args:
        circuit: Circuit to modify
        replacements: List of replacement specs, each with 'match' and 'update'
        dry_run: If True, don't actually modify

    Returns:
        Combined ReplacementResult from all operations

    Example:
        >>> replacements = [
        ...     {
        ...         "match": {"MPN": "ASD123"},
        ...         "update": {"MPN": "FGS032", "Manufacturer": "NewCo"}
        ...     },
        ...     {
        ...         "match": {"MPN": "OLD456"},
        ...         "update": {"MPN": "NEW789"}
        ...     }
        ... ]
        >>> result = cs.replace_multiple(circuit, replacements)
        >>> print(f"Total replaced: {result.count}")
    """
    total_count = 0
    all_affected = []
    all_warnings = []
    all_errors = []

    for replacement_spec in replacements:
        match = replacement_spec.get("match", {})
        update = replacement_spec.get("update", {})

        if not match or not update:
            all_warnings.append(
                f"Skipping invalid replacement spec: {replacement_spec}"
            )
            continue

        result = replace_components(circuit, match, update, dry_run=dry_run)

        total_count += result.count
        all_affected.extend(result.affected_components)
        all_warnings.extend(result.warnings)
        all_errors.extend(result.errors)

    return ReplacementResult(
        count=total_count,
        affected_components=all_affected,
        warnings=all_warnings,
        errors=all_errors,
    )


def find_replaceable_components(
    circuit: Circuit, match: Dict[str, str]
) -> List[str]:
    """
    Find components that match criteria without modifying them.

    Useful for previewing what would be affected by a replacement operation.

    Args:
        circuit: Circuit to search
        match: Property criteria to match

    Returns:
        List of component references that match criteria

    Example:
        >>> # Find all components with specific MPN
        >>> matches = cs.find_replaceable_components(
        ...     circuit,
        ...     match={"MPN": "ASD123"}
        ... )
        >>> print(f"Would affect: {matches}")
    """
    result = replace_components(circuit, match, update={}, dry_run=True)
    return result.affected_components
