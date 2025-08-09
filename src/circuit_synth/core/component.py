##############################
# File: src/circuit_synth/core/component.py
##############################

import keyword
import os
import re
import warnings
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Union

from ._logger import context_logger
from .decorators import get_current_circuit
from .exception import (
    CircuitSynthError,
    ComponentError,
    LibraryNotFound,
    ValidationError,
)
from .pin import Pin
from .simple_pin_access import PinGroup, SimplifiedPinAccess

# Import symbol cache
try:
    from ..kicad.kicad_symbol_cache import SymbolLibCache
except ImportError:
    # Symbol cache not available
    context_logger.error("No symbol cache available", component="COMPONENT")

    class SymbolLibCache:
        @staticmethod
        def get_symbol_data(symbol_id: str):
            return {}


@dataclass
class Component(SimplifiedPinAccess):
    """
    Represents an electronic component that references a KiCad symbol.

    If multiple pins share the same name (e.g. "GND"), __getitem__ returns a PinGroup,
    so something like:
        comp["GND"] += net
    will connect *all* GND pins to that net.

    Additional fields can be passed as keyword arguments and will be stored
    in _extra_fields for later access (e.g., mfg_part_num, tolerance, etc.).
    """

    symbol: str
    ref: Optional[str] = None
    value: Optional[str] = None
    footprint: Optional[str] = None
    datasheet: Optional[str] = None
    description: Optional[str] = None

    _extra_fields: Dict[str, Any] = field(default_factory=dict, repr=False)

    # Store pins by integer index
    _pins: Dict[str, Pin] = field(
        default_factory=dict, init=False, repr=False
    )  # Now keyed by pin number instead of index

    # For name-based lookup, store lists of pins by name
    _pin_names: Dict[str, List[Pin]] = field(
        default_factory=dict, init=False, repr=False
    )

    _is_prefix: bool = field(default=False, init=False, repr=False)
    _user_reference: str = field(default="", init=False, repr=False)

    ALLOWED_REASSIGN = {"value"}

    def __init__(
        self,
        symbol: str,
        ref: Optional[str] = None,
        value: Optional[str] = None,
        footprint: Optional[str] = None,
        datasheet: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize Component with support for arbitrary additional fields.

        Args:
            symbol: KiCad symbol reference (e.g., "Device:R")
            ref: Component reference (e.g., "R1")
            value: Component value (e.g., "10k")
            footprint: KiCad footprint reference
            datasheet: URL to component datasheet
            description: Component description
            **kwargs: Additional fields (e.g., mfg_part_num, tolerance, etc.)
        """
        # Initialize the fields that are normally handled by dataclass first
        self._extra_fields = {}
        self._pins = {}
        self._pin_names = {}
        self._is_prefix = False
        self._user_reference = ""

        # Set the standard dataclass fields (this will trigger __setattr__ for ref)
        self.symbol = symbol
        self.ref = ref
        self.value = value
        self.footprint = footprint
        self.datasheet = datasheet
        self.description = description

        # Store any additional keyword arguments in _extra_fields (validation happens later)
        for key, value in kwargs.items():
            self._extra_fields[key] = value

        # Call the original post_init logic
        self.__post_init__()

        # Now validate the extra fields after the object is fully initialized
        for key, value in kwargs.items():
            try:
                self._validate_property(key, value)
            except ValidationError as e:
                raise ValidationError(f"Invalid property '{key}': {e}")

    def __post_init__(self):
        self._validate_symbol(self.symbol)

        # Instead of using SharedParserManager + parse_symbol,
        # we load flattened data from the SymbolLibCache
        try:
            symbol_data = SymbolLibCache.get_symbol_data(self.symbol)  # e.g. "Device:C"
            context_logger.debug(
                "Loaded symbol data from cache",
                component="COMPONENT",
                symbol=self.symbol,
                has_pins="pins" in symbol_data,
                pin_count=(
                    len(symbol_data.get("pins", [])) if "pins" in symbol_data else 0
                ),
            )
        except FileNotFoundError as e:
            context_logger.error(
                "Library file not found for symbol",
                component="COMPONENT",
                symbol=self.symbol,
                error=str(e),
            )
            raise LibraryNotFound(f"Failed to load symbol '{self.symbol}': {e}")
        except KeyError as e:
            context_logger.error(
                "Symbol not found in library",
                component="COMPONENT",
                symbol=self.symbol,
                error=str(e),
            )
            raise LibraryNotFound(f"Symbol not found: '{self.symbol}': {e}")
        except Exception as e:
            # fallback for anything else
            context_logger.error(
                "Error while loading symbol from cache",
                component="COMPONENT",
                symbol=self.symbol,
                error=str(e),
            )
            raise LibraryNotFound(f"Failed to load symbol '{self.symbol}': {e}")

        # Store standard properties from symbol_data if not already set on component
        if self.description is None:
            self.description = symbol_data.get("description")
        if self.datasheet is None:
            self.datasheet = symbol_data.get("datasheet")
        # Store keywords and filters in _extra_fields for later use
        if "keywords" not in self._extra_fields and symbol_data.get("keywords"):
            self._extra_fields["ki_keywords"] = symbol_data.get("keywords")
        if "ki_fp_filters" not in self._extra_fields and symbol_data.get("fp_filters"):
            self._extra_fields["ki_fp_filters"] = symbol_data.get("fp_filters")

        # Clear any old pin data in case we re-init
        self._pins.clear()
        self._pin_names.clear()

        # Build pin objects from the symbol_data
        # symbol_data["pins"] is typically a list of dicts:
        # [ {"function": "passive", "name": "~", "number": "1", ...}, ... ]
        pins_loaded = 0
        for pin_info in symbol_data.get("pins", []):
            pin_num = pin_info.get("number", "")
            if not pin_num:  # Skip pins without numbers
                context_logger.warning(
                    "Skipping pin without number in symbol",
                    component="COMPONENT",
                    symbol=self.symbol,
                )
                continue

            new_pin = Pin(
                name=pin_info.get("name", "~"),
                num=pin_num,
                func=pin_info.get("function", "passive"),
                unit=1,
                x=pin_info.get("x", 0),
                y=pin_info.get("y", 0),
                length=pin_info.get("length", 2.54),
                orientation=pin_info.get("orientation", 0),
            )
            new_pin._component = self
            new_pin._component_pin_id = int(pin_num) if pin_num.isdigit() else 0

            # Store by pin number
            self._pins[pin_num] = new_pin
            pins_loaded += 1

            # Also store by pin name
            nm = new_pin.name
            if nm and nm not in ("~", ""):
                if nm not in self._pin_names:
                    self._pin_names[nm] = []
                self._pin_names[nm].append(new_pin)

        context_logger.debug(
            "Component pins loaded",
            component="COMPONENT",
            symbol=self.symbol,
            ref=self.ref,
            pins_loaded=pins_loaded,
            pin_numbers=list(self._pins.keys()),
            pin_names=list(self._pin_names.keys()),
        )

        # Handle case where no reference is provided
        if not self.ref:
            # No reference provided - this is allowed for template components
            self._user_reference = ""
            self._is_prefix = True
            return

        # Validate non-empty string references
        if not self.ref.strip():
            raise ValidationError("Reference must be a non-empty string")

        # Use the reference provided in constructor
        user_ref = self.ref.strip()
        # Only set _user_reference and _is_prefix if not already set by __setattr__
        if not hasattr(self, "_user_reference"):
            self._user_reference = user_ref

            # Check if final or prefix-only
            trailing_digits = re.search(r"\d+$", user_ref)
            self._is_prefix = not bool(trailing_digits)

            context_logger.debug(
                "Component detected reference",
                component="COMPONENT",
                symbol=self.symbol,
                reference_type="final" if not self._is_prefix else "prefix",
                reference=user_ref,
            )

        # See if there's an active circuit
        circuit = get_current_circuit()
        if circuit is None:
            # No active circuit - this is OK for template components
            context_logger.debug(
                "No active circuit for component - can be used as template",
                component="COMPONENT",
                reference=self.ref,
                symbol=self.symbol,
            )
            return

        # If we do have an active circuit, add the component
        circuit.add_component(self)

    def _validate_symbol(self, symbol: str):
        if not symbol or not isinstance(symbol, str):
            raise CircuitSynthError("Invalid symbol format: Must be non-empty string.")
        parts = symbol.split(":")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise CircuitSynthError(
                f"Invalid symbol format '{symbol}': Should be 'Library:Symbol'"
            )

    def __getattr__(self, name: str) -> Any:
        if name in self._extra_fields:
            return self._extra_fields[name]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_validate_property":
            super().__setattr__(name, value)
            return

        # Special handling for ref assignments
        if name == "ref":
            # Allow None values during initialization, but validate string references
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValidationError("Reference must be a non-empty string")

            # Store the user's reference (handle None values)
            if value is None:
                super().__setattr__("_user_reference", "")
                super().__setattr__(
                    "_is_prefix", True
                )  # Default to prefix when no reference
                super().__setattr__("ref", None)  # Update the dataclass field
                context_logger.debug(
                    "Component reference set to None", component="COMPONENT"
                )
            else:
                cleaned_value = value.strip()
                super().__setattr__("_user_reference", cleaned_value)

                # Check if it's a final reference (has trailing digits)
                trailing_digits = re.search(r"\d+$", cleaned_value)
                super().__setattr__("_is_prefix", not bool(trailing_digits))
                super().__setattr__("ref", cleaned_value)  # Update the dataclass field

                context_logger.debug(
                    "Component reference set",
                    component="COMPONENT",
                    reference=value,
                    reference_type="final" if not self._is_prefix else "prefix",
                )
            return  # Don't process as dataclass field after special handling

        # Dataclass fields
        if name in self.__dataclass_fields__:
            super().__setattr__(name, value)
            return

        # If it's a known attribute name, disallow changing except "value"
        if (name in dir(self)) and (name not in self.ALLOWED_REASSIGN):
            raise ValidationError("collides with existing attribute")

        # Validate new property name
        self._validate_property(name, value)
        if not hasattr(self, "_extra_fields"):
            super().__setattr__("_extra_fields", {})
        self._extra_fields[name] = value

    def _validate_property(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            raise ValidationError("leading underscore")
        if name and name[0].isdigit():
            raise ValidationError("start with a digit")
        if keyword.iskeyword(name):
            raise ValidationError("reserved keyword")
        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
            raise ValidationError("invalid characters")
        if isinstance(value, str) and not value.strip():
            raise ValidationError("cannot be empty")

    # Pin access methods are now inherited from SimplifiedPinAccess

    def __call__(self, *args, **kwargs):
        """
        Cloning a prefix-based ref is allowed, but final references are not.
        """
        if re.search(r"\d+$", self.ref or ""):
            raise ComponentError(
                "trailing digits in ref, can't clone from a final ref. "
                "Please supply a new prefix or final ref manually."
            )

        # If we're cloning a template component (no ref) inside a circuit context,
        # generate a default prefix based on the symbol
        ref_to_use = self.ref
        if not ref_to_use and get_current_circuit() is not None:
            # Generate a default prefix based on the component symbol
            symbol_parts = self.symbol.split(":")
            if len(symbol_parts) >= 2:
                # Use the symbol name as prefix (e.g., "Device:R" -> "R")
                default_prefix = symbol_parts[1]
                # Clean up the prefix to be a valid reference
                default_prefix = re.sub(r"[^A-Za-z0-9_]", "", default_prefix)
                if default_prefix and default_prefix[0].isalpha():
                    ref_to_use = default_prefix
                else:
                    ref_to_use = "U"  # Generic fallback
            else:
                ref_to_use = "U"  # Generic fallback

        new_c = type(self)(
            symbol=self.symbol,
            ref=ref_to_use,
            value=self.value,
            footprint=self.footprint,
            datasheet=self.datasheet,
            description=self.description,
        )
        for k, v in self._extra_fields.items():
            setattr(new_c, k, v)
        # The unified pin access is automatically initialized in __post_init__
        return new_c

    def __mul__(self, count: int):
        if count < 1:
            raise ComponentError("Multiplication count must be >= 1.")
        return tuple(self() for _ in range(count))

    def __iter__(self) -> Iterator[Pin]:
        return iter(self._pins.values())

    def __len__(self) -> int:
        return len(self._pins)

    def __str__(self) -> str:
        desc = self.value if self.value else self.symbol
        return f"{self.ref} ({desc})"

    def to_dict(self) -> Dict[str, Any]:
        # Prepare properties dict, including those stored in _extra_fields
        properties = {}
        if "ki_keywords" in self._extra_fields:
            properties["ki_keywords"] = self._extra_fields["ki_keywords"]
        if "ki_fp_filters" in self._extra_fields:
            properties["ki_fp_filters"] = self._extra_fields["ki_fp_filters"]
        # Add other relevant fields from _extra_fields if needed in the future

        data = {
            "symbol": self.symbol or "",
            "ref": self.ref or "",
            "value": self.value or "",
            "footprint": self.footprint or "",
            "datasheet": self.datasheet or "",  # Ensure empty string instead of None
            "description": self.description
            or "",  # Ensure empty string instead of None
            "properties": properties,  # Add standard properties dict
            "_extra_fields": dict(
                self._extra_fields
            ),  # Keep original for now if needed elsewhere
            "pins": [],
        }

        # Add all extra fields to the top level for easy access
        for key, value in self._extra_fields.items():
            if key not in data and key not in ["ki_keywords", "ki_fp_filters"]:
                data[key] = value

        # Sort pins by number for consistent output
        sorted_pins = sorted(
            self._pins.items(),
            key=lambda x: int(x[0]) if x[0].isdigit() else float("inf"),
        )
        for pin_num, pin_obj in sorted_pins:
            data["pins"].append(
                {
                    "pin_id": pin_num,  # Use pin number instead of index
                    "name": pin_obj.name,
                    "func": pin_obj.func,
                    "unit": pin_obj.unit,
                    "x": pin_obj.x,
                    "y": pin_obj.y,
                    "length": pin_obj.length,
                    "orientation": pin_obj.orientation,
                }
            )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Component":
        if "symbol" not in data:
            raise ValidationError("symbol field missing")
        if "ref" not in data:
            raise ValidationError("ref field missing")

        comp = cls(
            symbol=data["symbol"],
            ref=data["ref"],
            value=data.get("value"),
            footprint=data.get("footprint"),
            datasheet=data.get("datasheet"),
            description=data.get("description"),
        )

        known_top = {
            "symbol",
            "ref",
            "value",
            "footprint",
            "datasheet",
            "description",
            "pins",
            "_extra_fields",
        }
        for k, v in data.items():
            if k not in known_top:
                setattr(comp, k, v)

        for k, v in data.get("_extra_fields", {}).items():
            setattr(comp, k, v)

        comp._pins.clear()
        comp._pin_names.clear()
        for pinfo in data.get("pins", []):
            pin_num = pinfo.get("number", pinfo.get("num", ""))
            if not pin_num:  # Skip pins without numbers
                context_logger.warning(
                    "Skipping pin without number in component",
                    component="COMPONENT",
                    component_ref=comp.ref,
                )
                continue

            if pin_num in comp._pins:
                raise ComponentError(f"Duplicate pin number '{pin_num}' in from_dict")

            pin_obj = Pin(
                name=pinfo.get("name", "~"),
                num=pin_num,
                func=pinfo.get("func", "unspecified"),
                unit=pinfo.get("unit", 1),
                x=pinfo.get("x", 0),
                y=pinfo.get("y", 0),
                length=pinfo.get("length", 0),
                orientation=pinfo.get("orientation", 0),
            )
            pin_obj._component = comp
            pin_obj._component_pin_id = int(pin_num) if pin_num.isdigit() else 0

            # Store by pin number
            comp._pins[pin_num] = pin_obj

            # Also store by name if it has one
            pin_name = pinfo.get("name")
            if pin_name and pin_name not in ("~", ""):
                comp._pin_names.setdefault(pin_name, []).append(pin_obj)

            n = pin_obj.name
            if n and n not in ("~", ""):
                if n not in comp._pin_names:
                    comp._pin_names[n] = []
                comp._pin_names[n].append(pin_obj)

        return comp

    # NEW: Provide a helper to list all pins for debugging
    def print_pin_names(self) -> str:
        """
        Returns a formatted string of all pins, showing index, name, and number.
        Useful for debugging symbol pin naming mismatches.
        """
        lines = []
        lines.append(
            f"--- Pin listing for Component '{self.ref}' (symbol='{self.symbol}') ---"
        )
        for idx, pin in sorted(self._pins.items(), key=lambda x: x[0]):
            lines.append(f"  Pin index={idx}, name='{pin.name}', number='{pin.num}'")
        return "\n".join(lines)
