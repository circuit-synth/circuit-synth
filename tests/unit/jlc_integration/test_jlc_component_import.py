"""
Tests for JLCPCB component import.

These tests never touch the network: the JLCPCB search layer is mocked so that
both the success paths and the failure/fallback paths are exercised
deterministically.
"""

import logging
import unittest
from typing import Any, Dict, List
from unittest.mock import patch

from circuit_synth.core.circuit import Circuit
from circuit_synth.core.decorators import get_current_circuit, set_current_circuit
from circuit_synth.manufacturing.jlcpcb.component_import import (
    JlcComponentImporter,
    JlcImportError,
    JlcLookupError,
    JlcPartNotFoundError,
    JlcPartSpec,
    SymbolResolutionError,
    component_from_search_result,
    get_component_importer,
    import_jlc_component,
    lookup_lcsc_part,
    normalize_lcsc_part,
)
from circuit_synth.manufacturing.jlcpcb.fast_search import FastSearchResult

RESISTOR_RESULT = FastSearchResult(
    part_number="C25804",
    manufacturer_part="RC0603FR-0710KL",
    description="10K Ohm Resistor, 1%, 1/10W",
    stock=956234,
    price=0.003,
    package="0603",
    basic_part=True,
    match_score=1.0,
)

OPAMP_RESULT = FastSearchResult(
    part_number="C7950",
    manufacturer_part="LM358DR",
    description="Dual Operational Amplifier",
    stock=89234,
    price=0.15,
    package="SOIC-8",
    basic_part=False,
    match_score=1.0,
)

SCRAPER_ROW: Dict[str, Any] = {
    "part_number": "AMS1117-3.3",
    "lcsc_part": "C6186",
    "manufacturer": "Advanced Monolithic Systems",
    "description": "3.3V Linear Voltage Regulator, 1A",
    "package": "SOT-223",
    "stock": 234567,
    "price": "$0.08@100pcs",
    "library_type": "Basic",
}


class _StubSearcher:
    """Minimal stand-in for FastJLCSearch that never performs I/O."""

    def __init__(
        self,
        results: List[FastSearchResult] = None,
        error: Exception = None,
    ) -> None:
        self.results = results or []
        self.error = error
        self.queries: List[str] = []

    def search(self, query: str, **kwargs: Any) -> List[FastSearchResult]:
        """Return the canned results or raise the canned error."""
        self.queries.append(query)
        if self.error is not None:
            raise self.error
        return list(self.results)


def _make_importer(
    results: List[FastSearchResult] = None, error: Exception = None
) -> JlcComponentImporter:
    """Build an importer backed by a stub searcher."""
    return JlcComponentImporter(searcher=_StubSearcher(results=results, error=error))


class TestNormalizeLcscPart(unittest.TestCase):
    """Validation and normalization of LCSC part numbers."""

    def test_uppercases_and_strips_whitespace(self):
        """Lower case input with surrounding whitespace is normalized."""
        self.assertEqual(normalize_lcsc_part("  c25804 "), "C25804")

    def test_accepts_canonical_form(self):
        """An already canonical part number is returned unchanged."""
        self.assertEqual(normalize_lcsc_part("C25804"), "C25804")

    def test_rejects_missing_prefix(self):
        """A part number without the C prefix is rejected."""
        with self.assertRaises(JlcImportError):
            normalize_lcsc_part("25804")

    def test_rejects_empty_value(self):
        """An empty string is rejected."""
        with self.assertRaises(JlcImportError):
            normalize_lcsc_part("   ")

    def test_rejects_non_numeric_suffix(self):
        """A part number with a non numeric suffix is rejected."""
        with self.assertRaises(JlcImportError):
            normalize_lcsc_part("C25804A")


class TestJlcPartSpec(unittest.TestCase):
    """Conversion of JLCPCB catalog data into a part specification."""

    def setUp(self):
        self.importer = _make_importer()

    def test_spec_from_search_result_resolves_symbol_and_footprint(self):
        """A passive search result maps to a KiCad symbol, footprint and value."""
        spec = self.importer.spec_from_search_result(RESISTOR_RESULT)

        self.assertEqual(spec.lcsc_part, "C25804")
        self.assertEqual(spec.manufacturer_part, "RC0603FR-0710KL")
        self.assertEqual(spec.symbol, "Device:R")
        self.assertEqual(spec.footprint, "Resistor_SMD:R_0603_1608Metric")
        self.assertEqual(spec.value, "10K")
        self.assertEqual(spec.ref_prefix, "R")
        self.assertTrue(spec.basic_part)
        self.assertEqual(spec.stock, 956234)

    def test_spec_from_search_result_for_integrated_circuit(self):
        """An IC search result maps to a U reference prefix and no value."""
        spec = self.importer.spec_from_search_result(OPAMP_RESULT)

        self.assertEqual(spec.symbol, "Amplifier_Operational:LM358")
        self.assertEqual(spec.footprint, "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm")
        self.assertEqual(spec.ref_prefix, "U")
        self.assertIsNone(spec.value)
        self.assertFalse(spec.basic_part)

    def test_spec_from_catalog_entry_reads_scraper_dictionary(self):
        """Raw scraper dictionaries are accepted as an input format."""
        spec = self.importer.spec_from_catalog_entry(SCRAPER_ROW)

        self.assertEqual(spec.lcsc_part, "C6186")
        self.assertEqual(spec.manufacturer_part, "AMS1117-3.3")
        self.assertEqual(spec.manufacturer, "Advanced Monolithic Systems")
        self.assertEqual(spec.symbol, "Regulator_Linear:AMS1117-3.3")
        self.assertEqual(spec.footprint, "Package_TO_SOT_SMD:SOT-223-3_TabPin2")
        self.assertTrue(spec.basic_part)
        self.assertEqual(spec.price, "$0.08@100pcs")

    def test_spec_without_mapping_leaves_symbol_unresolved(self):
        """An unmapped component yields a spec without symbol or footprint."""
        unknown = FastSearchResult(
            part_number="C999999",
            manufacturer_part="XYZ-1234",
            description="Unclassified part",
            stock=10,
            price=1.0,
            package="WeirdPackage",
            basic_part=False,
            match_score=0.1,
        )

        spec = self.importer.spec_from_search_result(unknown)

        self.assertIsNone(spec.symbol)
        self.assertIsNone(spec.footprint)

    def test_to_properties_includes_sourcing_metadata(self):
        """Sourcing metadata is exposed as component properties."""
        spec = self.importer.spec_from_search_result(RESISTOR_RESULT)
        properties = spec.to_properties()

        self.assertEqual(properties["LCSC"], "C25804")
        self.assertEqual(properties["MPN"], "RC0603FR-0710KL")
        self.assertEqual(properties["JLCPCB_Stock"], "956234")
        self.assertEqual(properties["JLCPCB_Part_Type"], "Basic")

    def test_to_properties_marks_extended_parts(self):
        """Extended parts are labelled as such in the properties."""
        spec = self.importer.spec_from_search_result(OPAMP_RESULT)

        self.assertEqual(spec.to_properties()["JLCPCB_Part_Type"], "Extended")

    def test_to_properties_omits_missing_fields(self):
        """Fields with no data are omitted rather than emitted empty."""
        spec = JlcPartSpec(lcsc_part="C1", symbol="Device:R")
        properties = spec.to_properties()

        self.assertNotIn("MPN", properties)
        self.assertNotIn("Manufacturer", properties)
        self.assertNotIn("JLCPCB_Price", properties)

    def test_to_circuit_synth_code_is_valid_python(self):
        """The generated snippet compiles and contains the resolved fields."""
        spec = self.importer.spec_from_search_result(RESISTOR_RESULT)
        code = spec.to_circuit_synth_code()

        compile(code, "<generated>", "exec")
        self.assertIn('symbol="Device:R"', code)
        self.assertIn('footprint="Resistor_SMD:R_0603_1608Metric"', code)
        self.assertIn('LCSC="C25804"', code)

    def test_to_circuit_synth_code_requires_symbol(self):
        """Code generation fails when the symbol could not be resolved."""
        spec = JlcPartSpec(lcsc_part="C1")

        with self.assertRaises(SymbolResolutionError):
            spec.to_circuit_synth_code()


class TestResolvePart(unittest.TestCase):
    """Lookup of an LCSC part number through the search layer."""

    def test_resolve_part_returns_matching_entry(self):
        """The result whose part number matches the query is selected."""
        importer = _make_importer([OPAMP_RESULT, RESISTOR_RESULT])

        spec = importer.resolve_part("c25804")

        self.assertEqual(spec.lcsc_part, "C25804")
        self.assertEqual(spec.symbol, "Device:R")

    def test_resolve_part_uses_normalized_query(self):
        """The searcher is queried with the normalized part number."""
        searcher = _StubSearcher([RESISTOR_RESULT])
        importer = JlcComponentImporter(searcher=searcher)

        importer.resolve_part(" c25804 ")

        self.assertEqual(searcher.queries, ["C25804"])

    def test_resolve_part_raises_when_no_results(self):
        """An empty result set raises JlcPartNotFoundError."""
        importer = _make_importer([])

        with self.assertRaises(JlcPartNotFoundError):
            importer.resolve_part("C25804")

    def test_resolve_part_raises_when_no_exact_match(self):
        """Results that do not match the requested part are rejected."""
        importer = _make_importer([OPAMP_RESULT])

        with self.assertRaises(JlcPartNotFoundError):
            importer.resolve_part("C25804")

    def test_resolve_part_wraps_search_failures(self):
        """Search layer exceptions are reported as JlcLookupError."""
        importer = _make_importer(error=ConnectionError("network unreachable"))

        with self.assertRaises(JlcLookupError):
            importer.resolve_part("C25804")

    def test_resolve_part_rejects_invalid_part_number(self):
        """Invalid part numbers fail before any search is attempted."""
        searcher = _StubSearcher([RESISTOR_RESULT])
        importer = JlcComponentImporter(searcher=searcher)

        with self.assertRaises(JlcImportError):
            importer.resolve_part("not-a-part")

        self.assertEqual(searcher.queries, [])


class TestLookupLcscPart(unittest.TestCase):
    """Non raising lookup helper."""

    def test_returns_spec_on_success(self):
        """A resolvable part returns its specification."""
        importer = _make_importer([RESISTOR_RESULT])

        spec = lookup_lcsc_part("C25804", importer=importer)

        self.assertIsNotNone(spec)
        self.assertEqual(spec.lcsc_part, "C25804")

    def test_returns_none_when_lookup_fails(self):
        """A failed lookup degrades to None instead of raising."""
        importer = _make_importer(error=ConnectionError("network unreachable"))

        self.assertIsNone(lookup_lcsc_part("C25804", importer=importer))

    def test_returns_none_for_invalid_part_number(self):
        """An invalid part number degrades to None."""
        importer = _make_importer([RESISTOR_RESULT])

        self.assertIsNone(lookup_lcsc_part("bogus", importer=importer))

    def test_logs_warning_when_lookup_fails(self):
        """A failed lookup is logged at warning level."""
        importer = _make_importer([])

        with self.assertLogs(
            "circuit_synth.manufacturing.jlcpcb.component_import", level=logging.WARNING
        ) as captured:
            lookup_lcsc_part("C25804", importer=importer)

        self.assertTrue(any("C25804" in message for message in captured.output))


class TestBuildComponent(unittest.TestCase):
    """Construction of circuit-synth components from JLCPCB data."""

    def setUp(self):
        self._previous_circuit = get_current_circuit()
        set_current_circuit(Circuit(name="JlcImportTest"))

    def tearDown(self):
        set_current_circuit(self._previous_circuit)

    def test_import_jlc_component_returns_usable_component(self):
        """A known LCSC part becomes a component with symbol, value and metadata."""
        importer = _make_importer([RESISTOR_RESULT])

        component = import_jlc_component("C25804", importer=importer)

        self.assertEqual(component.symbol, "Device:R")
        self.assertEqual(component.footprint, "Resistor_SMD:R_0603_1608Metric")
        self.assertEqual(component.value, "10K")
        self.assertEqual(component.LCSC, "C25804")
        self.assertEqual(component.MPN, "RC0603FR-0710KL")
        self.assertEqual(component.JLCPCB_Part_Type, "Basic")
        self.assertEqual(component.JLCPCB_Stock, "956234")
        self.assertEqual(len(component._pins), 2)

    def test_import_jlc_component_applies_overrides(self):
        """Caller supplied symbol, footprint, value and reference win."""
        importer = _make_importer([RESISTOR_RESULT])

        component = import_jlc_component(
            "C25804",
            ref="R42",
            symbol="Device:C",
            footprint="Capacitor_SMD:C_0603_1608Metric",
            value="100nF",
            importer=importer,
        )

        self.assertEqual(component.symbol, "Device:C")
        self.assertEqual(component.footprint, "Capacitor_SMD:C_0603_1608Metric")
        self.assertEqual(component.value, "100nF")
        self.assertEqual(component.ref, "R42")

    def test_import_jlc_component_accepts_extra_properties(self):
        """Additional properties are attached to the component."""
        importer = _make_importer([RESISTOR_RESULT])

        component = import_jlc_component("C25804", importer=importer, Tolerance="1%")

        self.assertEqual(component.Tolerance, "1%")

    def test_component_from_search_result_skips_lookup(self):
        """A search result can be converted without any further search."""
        searcher = _StubSearcher(error=AssertionError("search must not run"))
        importer = JlcComponentImporter(searcher=searcher)

        component = component_from_search_result(RESISTOR_RESULT, importer=importer)

        self.assertEqual(component.symbol, "Device:R")
        self.assertEqual(component.LCSC, "C25804")

    def test_build_component_requires_a_symbol(self):
        """A spec without a resolvable symbol raises SymbolResolutionError."""
        importer = _make_importer()
        spec = JlcPartSpec(lcsc_part="C999999", manufacturer_part="XYZ-1234")

        with self.assertRaises(SymbolResolutionError):
            importer.build_component(spec)

    def test_build_component_without_footprint_logs_warning(self):
        """A missing footprint is a warning, not a failure."""
        importer = _make_importer()
        spec = JlcPartSpec(lcsc_part="C25804", symbol="Device:R", ref_prefix="R")

        with self.assertLogs(
            "circuit_synth.manufacturing.jlcpcb.component_import", level=logging.WARNING
        ) as captured:
            component = importer.build_component(spec)

        self.assertIsNone(component.footprint)
        self.assertTrue(any("C25804" in message for message in captured.output))

    def test_build_component_uses_reference_prefix_by_default(self):
        """Without an explicit reference the mapped prefix is used."""
        importer = _make_importer([RESISTOR_RESULT])
        spec = importer.resolve_part("C25804")

        component = importer.build_component(spec)

        self.assertTrue(component.ref.startswith("R"))

    def test_import_jlc_component_propagates_not_found(self):
        """An unknown part propagates JlcPartNotFoundError to the caller."""
        importer = _make_importer([])

        with self.assertRaises(JlcPartNotFoundError):
            import_jlc_component("C25804", importer=importer)


class TestDefaultImporter(unittest.TestCase):
    """Module level importer accessor."""

    def test_get_component_importer_is_cached(self):
        """The default importer is created once and reused."""
        with patch(
            "circuit_synth.manufacturing.jlcpcb.component_import._default_importer",
            None,
        ):
            first = get_component_importer()
            second = get_component_importer()

        self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
