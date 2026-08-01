#!/usr/bin/env python3
"""
JLCPCB component import for circuit-synth.

Turns a JLCPCB/LCSC catalog entry into a ready-to-use ``circuit_synth.Component``.
The importer resolves the KiCad symbol, footprint, value and reference prefix for
a part and attaches the sourcing metadata (LCSC part number, manufacturer part
number, manufacturer, stock level and basic/extended status) as component
properties so it is carried through to the netlist and BOM.

Typical use::

    from circuit_synth.manufacturing.jlcpcb import import_jlc_component

    r1 = import_jlc_component("C25804")
    # Component(symbol="Device:R", value="10K",
    #           footprint="Resistor_SMD:R_0603_1608Metric", LCSC="C25804", ...)

The lookup path depends on the JLCPCB search layer, which may be unavailable or
rate limited. Lookup failures raise :class:`JlcLookupError`; the non raising
helper :func:`lookup_lcsc_part` returns ``None`` instead so callers can fall back
to a locally specified component.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

from ...core.component import Component
from .fast_search import FastJLCSearch, FastSearchResult, get_fast_searcher
from .smart_component_finder import SmartComponentFinder

logger = logging.getLogger(__name__)

# LCSC part numbers are the letter C followed by digits, for example "C25804".
LCSC_PART_PATTERN = re.compile(r"^C\d+$")

# Number of search results inspected when resolving a single part number.
_LOOKUP_RESULT_LIMIT = 10


class JlcImportError(Exception):
    """Base error for JLCPCB component import failures."""


class JlcPartNotFoundError(JlcImportError):
    """Raised when no catalog entry matches the requested LCSC part number."""


class JlcLookupError(JlcImportError):
    """Raised when the JLCPCB search layer could not be queried."""


class SymbolResolutionError(JlcImportError):
    """Raised when no KiCad symbol could be determined for a part."""


def normalize_lcsc_part(lcsc_part: str) -> str:
    """
    Normalize an LCSC part number to its canonical form.

    Args:
        lcsc_part: LCSC part number, for example "c25804" or " C25804 ".

    Returns:
        The part number in canonical upper case form, for example "C25804".

    Raises:
        JlcImportError: If the value is not a valid LCSC part number.
    """
    if not isinstance(lcsc_part, str):
        raise JlcImportError(
            f"LCSC part number must be a string, got {type(lcsc_part)}"
        )

    normalized = lcsc_part.strip().upper()
    if not LCSC_PART_PATTERN.match(normalized):
        raise JlcImportError(
            f"Invalid LCSC part number '{lcsc_part}', expected format C<digits>"
        )

    return normalized


@dataclass
class JlcPartSpec:
    """
    Resolved description of a JLCPCB part ready to be turned into a Component.

    Attributes:
        lcsc_part: LCSC part number, for example "C25804".
        manufacturer_part: Manufacturer part number.
        manufacturer: Manufacturer name.
        description: Catalog description of the part.
        package: JLCPCB package name, for example "0603" or "SOIC-8".
        stock: Reported stock quantity.
        basic_part: True for JLCPCB basic parts, False for extended parts.
        price: Price string as reported by JLCPCB, empty when unknown.
        symbol: Resolved KiCad symbol, None when no mapping was found.
        footprint: Resolved KiCad footprint, None when no mapping was found.
        value: Component value for passives, None when not applicable.
        ref_prefix: Reference designator prefix, for example "R" or "U".
        symbol_verified: True when the symbol comes from a verified mapping.
        footprint_verified: True when the footprint comes from a verified mapping.
    """

    lcsc_part: str
    manufacturer_part: str = ""
    manufacturer: str = ""
    description: str = ""
    package: str = ""
    stock: int = 0
    basic_part: bool = False
    price: str = ""
    symbol: Optional[str] = None
    footprint: Optional[str] = None
    value: Optional[str] = None
    ref_prefix: str = "U"
    symbol_verified: bool = False
    footprint_verified: bool = False

    def to_properties(self) -> Dict[str, str]:
        """
        Build the component properties describing the JLCPCB sourcing data.

        Returns:
            Mapping of property name to value. Properties without data are
            omitted so no empty fields end up in the netlist.
        """
        properties: Dict[str, str] = {"LCSC": self.lcsc_part}

        if self.manufacturer_part:
            properties["MPN"] = self.manufacturer_part
        if self.manufacturer:
            properties["Manufacturer"] = self.manufacturer
        if self.package:
            properties["JLCPCB_Package"] = self.package
        if self.price:
            properties["JLCPCB_Price"] = self.price

        properties["JLCPCB_Stock"] = str(self.stock)
        properties["JLCPCB_Part_Type"] = "Basic" if self.basic_part else "Extended"

        return properties

    def to_circuit_synth_code(self, ref: Optional[str] = None) -> str:
        """
        Render the part as a circuit-synth Component definition.

        Args:
            ref: Reference designator or prefix. Defaults to the resolved prefix.

        Returns:
            Python source for a Component definition.

        Raises:
            SymbolResolutionError: If no KiCad symbol has been resolved.
        """
        if not self.symbol:
            raise SymbolResolutionError(
                f"No KiCad symbol resolved for {self.lcsc_part}; "
                "pass an explicit symbol to generate code"
            )

        lines = [f'    symbol="{self.symbol}",', f'    ref="{ref or self.ref_prefix}",']
        if self.value:
            lines.append(f'    value="{self.value}",')
        if self.footprint:
            lines.append(f'    footprint="{self.footprint}",')
        for name, value in self.to_properties().items():
            lines.append(f'    {name}="{value}",')

        body = "\n".join(lines)
        return f"Component(\n{body}\n)"


class JlcComponentImporter:
    """
    Convert JLCPCB catalog entries into circuit-synth components.

    The importer combines the JLCPCB search layer (part lookup) with the KiCad
    symbol and footprint mappings of :class:`SmartComponentFinder`.
    """

    def __init__(
        self,
        searcher: Optional[FastJLCSearch] = None,
        finder: Optional[SmartComponentFinder] = None,
    ) -> None:
        """
        Initialize the importer.

        Args:
            searcher: Search backend used to look up LCSC part numbers.
                Defaults to the shared fast searcher.
            finder: Provider of the KiCad symbol and footprint mappings.
                Defaults to a new SmartComponentFinder.
        """
        self._searcher = searcher if searcher is not None else get_fast_searcher()
        self._finder = finder if finder is not None else SmartComponentFinder()

    def resolve_part(self, lcsc_part: str) -> JlcPartSpec:
        """
        Look up an LCSC part number and resolve it to a part specification.

        Args:
            lcsc_part: LCSC part number, for example "C25804".

        Returns:
            The resolved part specification.

        Raises:
            JlcImportError: If the part number is not a valid LCSC part number.
            JlcLookupError: If the search backend could not be queried.
            JlcPartNotFoundError: If no catalog entry matches the part number.
        """
        normalized = normalize_lcsc_part(lcsc_part)

        try:
            results = self._searcher.search(
                normalized, max_results=_LOOKUP_RESULT_LIMIT
            )
        except Exception as error:
            logger.error(f"JLCPCB lookup failed for {normalized}: {error}")
            raise JlcLookupError(
                f"Could not query JLCPCB for {normalized}: {error}"
            ) from error

        match = self._select_exact_match(results, normalized)
        if match is None:
            raise JlcPartNotFoundError(
                f"No JLCPCB catalog entry found for {normalized}"
            )

        logger.info(f"Resolved JLCPCB part {normalized} to {match.manufacturer_part}")
        return self.spec_from_search_result(match)

    def spec_from_search_result(self, result: FastSearchResult) -> JlcPartSpec:
        """
        Build a part specification from a search result.

        Args:
            result: Search result produced by the JLCPCB search layer.

        Returns:
            The resolved part specification.
        """
        return self.spec_from_catalog_entry(
            {
                "lcsc_part": result.part_number,
                "part_number": result.manufacturer_part,
                "description": result.description,
                "package": result.package,
                "stock": result.stock,
                "price": f"${result.price:.4f}" if result.price else "",
                "library_type": "Basic" if result.basic_part else "Extended",
            }
        )

    def spec_from_catalog_entry(self, entry: Mapping[str, Any]) -> JlcPartSpec:
        """
        Build a part specification from a raw JLCPCB catalog dictionary.

        Args:
            entry: Catalog entry as returned by the JLCPCB scraper. Recognized
                keys are ``lcsc_part``, ``part_number``, ``manufacturer``,
                ``description``, ``package``, ``stock``, ``price`` and
                ``library_type``.

        Returns:
            The resolved part specification.
        """
        lookup: Dict[str, Any] = {
            "part_number": entry.get("part_number", ""),
            "description": entry.get("description", ""),
            "package": entry.get("package", ""),
        }

        symbol_info = self._finder.find_kicad_symbol(lookup)
        footprint_info = self._finder.find_kicad_footprint(lookup)
        symbol = symbol_info["symbol"] if symbol_info else None

        value: Optional[str] = None
        if symbol and self._finder.is_passive_component(symbol):
            value = self._finder.extract_component_value(lookup)

        spec = JlcPartSpec(
            lcsc_part=str(entry.get("lcsc_part", "")),
            manufacturer_part=str(entry.get("part_number", "")),
            manufacturer=str(entry.get("manufacturer", "")),
            description=str(entry.get("description", "")),
            package=str(entry.get("package", "")),
            stock=int(entry.get("stock", 0) or 0),
            basic_part="basic" in str(entry.get("library_type", "")).lower(),
            price=str(entry.get("price", "") or ""),
            symbol=symbol,
            footprint=footprint_info["footprint"] if footprint_info else None,
            value=value,
            ref_prefix=(
                self._finder.reference_designator_for(symbol) if symbol else "U"
            ),
            symbol_verified=bool(symbol_info and symbol_info.get("verified")),
            footprint_verified=bool(footprint_info and footprint_info.get("verified")),
        )

        if spec.symbol is None:
            logger.warning(
                f"No KiCad symbol mapping for {spec.lcsc_part} "
                f"({spec.manufacturer_part or 'unknown part'})"
            )

        return spec

    def build_component(
        self,
        spec: JlcPartSpec,
        ref: Optional[str] = None,
        symbol: Optional[str] = None,
        footprint: Optional[str] = None,
        value: Optional[str] = None,
        **properties: Any,
    ) -> Component:
        """
        Create a circuit-synth Component from a part specification.

        Args:
            spec: Resolved part specification.
            ref: Reference designator or prefix. Defaults to the resolved prefix.
            symbol: KiCad symbol override.
            footprint: KiCad footprint override.
            value: Component value override.
            **properties: Additional component properties. They take precedence
                over the JLCPCB sourcing properties of the same name.

        Returns:
            A Component with the JLCPCB sourcing metadata attached.

        Raises:
            SymbolResolutionError: If no symbol was resolved and none was given.
        """
        resolved_symbol = symbol or spec.symbol
        if not resolved_symbol:
            raise SymbolResolutionError(
                f"No KiCad symbol resolved for {spec.lcsc_part}; "
                "pass symbol= to create the component explicitly"
            )

        resolved_footprint = footprint or spec.footprint
        if not resolved_footprint:
            logger.warning(
                f"No KiCad footprint resolved for {spec.lcsc_part} "
                f"(package '{spec.package}'), component created without footprint"
            )

        component_properties: Dict[str, Any] = dict(spec.to_properties())
        component_properties.update(properties)

        component = Component(
            symbol=resolved_symbol,
            ref=ref or spec.ref_prefix,
            value=value or spec.value,
            footprint=resolved_footprint,
            description=spec.description or None,
            **component_properties,
        )

        logger.debug(
            f"Created component for {spec.lcsc_part} using symbol {resolved_symbol}"
        )
        return component

    def import_component(
        self,
        lcsc_part: str,
        ref: Optional[str] = None,
        symbol: Optional[str] = None,
        footprint: Optional[str] = None,
        value: Optional[str] = None,
        **properties: Any,
    ) -> Component:
        """
        Look up an LCSC part number and create the matching Component.

        Args:
            lcsc_part: LCSC part number, for example "C25804".
            ref: Reference designator or prefix.
            symbol: KiCad symbol override.
            footprint: KiCad footprint override.
            value: Component value override.
            **properties: Additional component properties.

        Returns:
            A Component with the JLCPCB sourcing metadata attached.

        Raises:
            JlcImportError: If the part could not be resolved or created.
        """
        spec = self.resolve_part(lcsc_part)
        return self.build_component(
            spec,
            ref=ref,
            symbol=symbol,
            footprint=footprint,
            value=value,
            **properties,
        )

    @staticmethod
    def _select_exact_match(
        results: List[FastSearchResult], lcsc_part: str
    ) -> Optional[FastSearchResult]:
        """
        Select the result matching an LCSC part number exactly.

        Args:
            results: Search results to inspect.
            lcsc_part: Normalized LCSC part number.

        Returns:
            The matching result, or None when no result matches.
        """
        for result in results:
            if result.part_number.strip().upper() == lcsc_part:
                return result
        return None


_default_importer: Optional[JlcComponentImporter] = None


def get_component_importer() -> JlcComponentImporter:
    """
    Get the shared component importer instance.

    Returns:
        The process wide JlcComponentImporter, created on first use.
    """
    global _default_importer
    if _default_importer is None:
        _default_importer = JlcComponentImporter()
    return _default_importer


def import_jlc_component(
    lcsc_part: str,
    ref: Optional[str] = None,
    symbol: Optional[str] = None,
    footprint: Optional[str] = None,
    value: Optional[str] = None,
    importer: Optional[JlcComponentImporter] = None,
    **properties: Any,
) -> Component:
    """
    Import a JLCPCB part as a circuit-synth Component.

    Args:
        lcsc_part: LCSC part number, for example "C25804".
        ref: Reference designator or prefix.
        symbol: KiCad symbol override.
        footprint: KiCad footprint override.
        value: Component value override.
        importer: Importer to use, defaults to the shared importer.
        **properties: Additional component properties.

    Returns:
        A Component with the JLCPCB sourcing metadata attached.

    Raises:
        JlcImportError: If the part could not be resolved or created.
    """
    active_importer = importer if importer is not None else get_component_importer()
    return active_importer.import_component(
        lcsc_part,
        ref=ref,
        symbol=symbol,
        footprint=footprint,
        value=value,
        **properties,
    )


def component_from_search_result(
    result: FastSearchResult,
    ref: Optional[str] = None,
    symbol: Optional[str] = None,
    footprint: Optional[str] = None,
    value: Optional[str] = None,
    importer: Optional[JlcComponentImporter] = None,
    **properties: Any,
) -> Component:
    """
    Create a Component from an existing JLCPCB search result.

    No additional lookup is performed, so this works with results that were
    obtained earlier or read from the search cache.

    Args:
        result: Search result produced by the JLCPCB search layer.
        ref: Reference designator or prefix.
        symbol: KiCad symbol override.
        footprint: KiCad footprint override.
        value: Component value override.
        importer: Importer to use, defaults to the shared importer.
        **properties: Additional component properties.

    Returns:
        A Component with the JLCPCB sourcing metadata attached.

    Raises:
        SymbolResolutionError: If no symbol was resolved and none was given.
    """
    active_importer = importer if importer is not None else get_component_importer()
    spec = active_importer.spec_from_search_result(result)
    return active_importer.build_component(
        spec,
        ref=ref,
        symbol=symbol,
        footprint=footprint,
        value=value,
        **properties,
    )


def lookup_lcsc_part(
    lcsc_part: str, importer: Optional[JlcComponentImporter] = None
) -> Optional[JlcPartSpec]:
    """
    Look up an LCSC part number without raising on failure.

    Args:
        lcsc_part: LCSC part number, for example "C25804".
        importer: Importer to use, defaults to the shared importer.

    Returns:
        The resolved part specification, or None when the part could not be
        resolved because it does not exist or the lookup was unavailable.
    """
    active_importer = importer if importer is not None else get_component_importer()
    try:
        return active_importer.resolve_part(lcsc_part)
    except JlcImportError as error:
        logger.warning(
            f"JLCPCB lookup for {lcsc_part} returned no usable data: {error}"
        )
        return None
