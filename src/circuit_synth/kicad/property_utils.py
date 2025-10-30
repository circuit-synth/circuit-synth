"""
Utilities for handling custom component properties.

Provides type conversion between Python and KiCad property formats:
- Python types → KiCad strings (for generation)
- KiCad strings → Python types (for synchronization)
- Property extraction and filtering
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# System property prefix to avoid conflicts with user properties
SYSTEM_PROPERTY_PREFIX = "_circuit_synth_"

# KiCad symbol metadata properties (handled by symbol definition, not user properties)
KICAD_SYMBOL_METADATA = {"ki_keywords", "ki_fp_filters", "ki_description"}

# Standard component fields (not custom properties)
STANDARD_COMPONENT_FIELDS = {
    "ref",
    "symbol",
    "value",
    "footprint",
    "datasheet",
    "description",
    "pins",
    "_extra_fields",
    "properties",
    "uuid",
    "reference",  # KiCad API field
    "lib_id",  # KiCad API field
}


def convert_value_for_kicad(value: Any) -> str:
    """
    Convert Python value to KiCad property string.

    KiCad properties are always strings. This handles type conversion
    for all Python types.

    Args:
        value: Python value of any type

    Returns:
        String representation suitable for KiCad properties

    Examples:
        >>> convert_value_for_kicad(True)
        'true'
        >>> convert_value_for_kicad([1, 2, 3])
        '1, 2, 3'
        >>> convert_value_for_kicad({"a": 1})
        '{"a": 1}'
    """
    if isinstance(value, bool):
        return "true" if value else "false"

    elif isinstance(value, (list, tuple)):
        # Convert lists to comma-separated strings
        return ", ".join(str(v) for v in value)

    elif isinstance(value, dict):
        # Convert dicts to JSON strings (for complex data)
        return json.dumps(value, ensure_ascii=False)

    elif value is None:
        return ""

    else:
        return str(value)


def convert_value_from_kicad(value: str) -> Any:
    """
    Convert KiCad property string back to Python type.

    Attempts to infer the original Python type from the string.

    Args:
        value: String value from KiCad property

    Returns:
        Python value with inferred type

    Examples:
        >>> convert_value_from_kicad("true")
        True
        >>> convert_value_from_kicad("1, 2, 3")
        [1, 2, 3]  # Could also be string "1, 2, 3" - ambiguous
        >>> convert_value_from_kicad('{"a": 1}')
        {'a': 1}
    """
    if not isinstance(value, str):
        return value

    # Handle boolean strings
    if value in ("true", "True", "TRUE"):
        return True
    elif value in ("false", "False", "FALSE"):
        return False

    # Handle empty strings
    if value.strip() == "":
        return None

    # Try to parse as number
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass

    # Try to parse as JSON (for lists/dicts)
    if value.startswith(("{", "[")):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    # Try to parse as comma-separated list
    # Only if it looks like a list (has commas) and not a regular value
    if ", " in value and not value.startswith('"'):
        try:
            # Try to parse each element
            parts = [part.strip() for part in value.split(",")]
            # Check if all parts look like list elements (not a sentence)
            if len(parts) >= 2 and all(len(part) < 50 for part in parts):
                return parts
        except Exception:
            pass

    # Return as string (safest fallback)
    return value


def extract_component_properties(
    comp_dict: dict, default_hierarchy_path: str = "/"
) -> dict:
    """
    Extract all properties from component dict for SchematicSymbol.

    Separates system properties (prefixed) from user properties (custom fields).

    Args:
        comp_dict: Component data from JSON
        default_hierarchy_path: Default hierarchy path if not specified

    Returns:
        Dict with both system and user properties, properly namespaced

    Example:
        >>> comp_dict = {
        ...     "ref": "R1",
        ...     "symbol": "Device:R",
        ...     "value": "10k",
        ...     "_extra_fields": {"DNP": True, "MPN": "RC0603"}
        ... }
        >>> props = extract_component_properties(comp_dict)
        >>> props["_circuit_synth_hierarchy_path"]
        '/'
        >>> props["DNP"]
        'true'
        >>> props["MPN"]
        'RC0603'
    """
    properties = {}

    # System properties (internal metadata) - ALWAYS prefixed
    properties[f"{SYSTEM_PROPERTY_PREFIX}hierarchy_path"] = default_hierarchy_path

    # Extract user properties from _extra_fields
    extra_fields = comp_dict.get("_extra_fields", {})
    for key, value in extra_fields.items():
        # Skip KiCad symbol metadata (already handled by symbol definition)
        if key in KICAD_SYMBOL_METADATA:
            logger.debug(
                f"Skipping KiCad metadata property: {key} (handled by symbol definition)"
            )
            continue

        # Add user property with type conversion
        properties[key] = convert_value_for_kicad(value)
        logger.debug(
            f"Added user property from _extra_fields: {key} = {properties[key]}"
        )

    # Fallback: check top-level fields (for backward compatibility)
    for key, value in comp_dict.items():
        if key not in STANDARD_COMPONENT_FIELDS and key not in properties:
            properties[key] = convert_value_for_kicad(value)
            logger.debug(
                f"Added user property from top-level: {key} = {properties[key]}"
            )

    logger.debug(
        f"Extracted {len(properties)} total properties ({len([k for k in properties if not k.startswith(SYSTEM_PROPERTY_PREFIX)])} user, {len([k for k in properties if k.startswith(SYSTEM_PROPERTY_PREFIX)])} system)"
    )

    return properties


def extract_user_properties_from_kicad(kicad_symbol) -> dict:
    """
    Extract user properties from KiCad SchematicSymbol.

    Filters out system properties and converts types back to Python.

    Args:
        kicad_symbol: SchematicSymbol from kicad-sch-api

    Returns:
        Dict of user properties suitable for Component._extra_fields

    Example:
        >>> # Assuming kicad_symbol.properties = {
        >>> #     "_circuit_synth_hierarchy_path": "/",
        >>> #     "DNP": "true",
        >>> #     "MPN": "RC0603"
        >>> # }
        >>> props = extract_user_properties_from_kicad(kicad_symbol)
        >>> props["DNP"]
        True  # Converted from string "true"
        >>> props["MPN"]
        'RC0603'
        >>> "_circuit_synth_hierarchy_path" in props
        False  # System property filtered out
    """
    user_props = {}

    if not hasattr(kicad_symbol, "properties"):
        logger.warning(f"Symbol {kicad_symbol} has no properties attribute")
        return user_props

    for key, value in kicad_symbol.properties.items():
        # Skip system properties (internal circuit-synth metadata)
        if key.startswith(SYSTEM_PROPERTY_PREFIX):
            logger.debug(f"Skipping system property: {key}")
            continue

        # Skip standard KiCad properties (already handled by standard fields)
        if key in {"Reference", "Value", "Footprint", "Datasheet", "Description"}:
            logger.debug(f"Skipping standard KiCad property: {key}")
            continue

        # Convert back to Python types
        user_props[key] = convert_value_from_kicad(value)
        logger.debug(f"Extracted user property: {key} = {user_props[key]}")

    # Handle DNP special case - check built-in flag
    if hasattr(kicad_symbol, "dnp") and kicad_symbol.dnp:
        user_props["DNP"] = True
        logger.debug("Extracted DNP from built-in flag")

    logger.debug(f"Extracted {len(user_props)} user properties from KiCad")

    return user_props


def extract_dnp_value(comp_dict: dict) -> bool:
    """
    Extract DNP value from component dict.

    Checks both _extra_fields and top-level for DNP property.
    Handles various boolean representations.

    Args:
        comp_dict: Component data dict

    Returns:
        Boolean DNP value (default: False)

    Example:
        >>> extract_dnp_value({"DNP": True})
        True
        >>> extract_dnp_value({"DNP": "true"})
        True
        >>> extract_dnp_value({"_extra_fields": {"DNP": True}})
        True
        >>> extract_dnp_value({})
        False
    """
    # Check _extra_fields first
    extra_fields = comp_dict.get("_extra_fields", {})
    if "DNP" in extra_fields:
        dnp_value = extra_fields["DNP"]
    elif "DNP" in comp_dict:
        dnp_value = comp_dict["DNP"]
    else:
        return False

    # Convert to boolean
    if isinstance(dnp_value, bool):
        return dnp_value
    elif isinstance(dnp_value, str):
        return dnp_value.lower() in ("true", "yes", "1")
    elif isinstance(dnp_value, (int, float)):
        return bool(dnp_value)
    else:
        return False


def is_user_property(key: str) -> bool:
    """
    Check if a property key is a user property (not system).

    Args:
        key: Property key name

    Returns:
        True if user property, False if system property

    Example:
        >>> is_user_property("DNP")
        True
        >>> is_user_property("_circuit_synth_hierarchy_path")
        False
    """
    return not key.startswith(SYSTEM_PROPERTY_PREFIX)


def filter_user_properties(properties: dict) -> dict:
    """
    Filter properties dict to only user properties.

    Args:
        properties: Dict with mixed system and user properties

    Returns:
        Dict with only user properties

    Example:
        >>> props = {
        ...     "_circuit_synth_hierarchy_path": "/",
        ...     "DNP": "true",
        ...     "MPN": "RC0603"
        ... }
        >>> user_props = filter_user_properties(props)
        >>> list(user_props.keys())
        ['DNP', 'MPN']
    """
    return {k: v for k, v in properties.items() if is_user_property(k)}
