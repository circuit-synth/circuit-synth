# Test Failure Breakdown

## By Category

- Unit Tests: 11
- Integration Tests: 38
- E2E Tests: 8
- Bidirectional Tests: 29
- PCB Generation Tests: 18
- KiCad-to-Python Tests: 16
- Bidirectional Automated Tests: 33
- Errors: 10

## Unit Test Failures (Detailed)

FAILED tests/unit/kicad/test_library_sourcing.py::TestLibraryOrchestrator::test_search_with_cache
FAILED tests/unit/kicad/test_library_sourcing.py::TestLibraryOrchestrator::test_fallback_search
FAILED tests/unit/test_core_circuit.py::TestCircuit::test_to_dict - Assertion...
FAILED tests/unit/test_power_symbol_generation.py::TestPowerSymbolGeneration::test_gnd_generates_power_symbol
FAILED tests/unit/test_power_symbol_generation.py::TestPowerSymbolGeneration::test_vcc_generates_power_symbol
FAILED tests/unit/test_power_symbol_generation.py::TestPowerSymbolGeneration::test_multiple_power_nets
FAILED tests/unit/test_power_symbol_generation.py::TestPowerSymbolGeneration::test_regular_nets_still_use_hierarchical_labels
FAILED tests/unit/test_power_symbol_generation.py::TestNetJSONSerialization::test_power_net_serialization
FAILED tests/unit/test_power_symbol_generation.py::TestPowerSymbolReferences::test_power_symbol_unique_references
FAILED tests/unit/test_python_code_generator_edge_cases.py::TestPythonCodeGeneratorEdgeCases::test_circuit_with_no_nets
FAILED tests/unit/test_python_code_generator_edge_cases.py::TestPythonCodeGeneratorEdgeCases::test_component_reference_sanitization
