# Dead Code Analysis Report

## Executive Summary

- **Total Functions Analyzed**: 2,179
- **Functions Actually Called**: 6
- **Potentially Dead Functions**: 2,173
- **Code Utilization**: 0.3%

⚠️  **2,173 functions (99.7%) appear to be unused**

## Analysis Details

This analysis was performed by:
1. Instrumenting all Python functions with debug logging
2. Running the target script to capture function calls
3. Comparing instrumented vs called functions

## Files Analyzed

- `__init__.py`: 1 functions instrumented
- `ai_integration/agents/debugging_agent.py`: 12 functions instrumented
- `ai_integration/claude/__init__.py`: 4 functions instrumented
- `ai_integration/claude/agent_registry.py`: 8 functions instrumented
- `ai_integration/claude/agents/circuit_creator_agent.py`: 19 functions instrumented
- `ai_integration/claude/agents/circuit_design_agents.py`: 2 functions instrumented
- `ai_integration/claude/agents/contributor_agent.py`: 10 functions instrumented
- `ai_integration/claude/agents/test_plan_agent.py`: 18 functions instrumented
- `ai_integration/claude/circuit_design_rules.py`: 7 functions instrumented
- `ai_integration/claude/commands.py`: 3 functions instrumented
- `ai_integration/claude/enhanced_circuit_agent.py`: 2 functions instrumented
- `ai_integration/claude/hooks.py`: 4 functions instrumented
- `ai_integration/component_info/microcontrollers/modm_device_search.py`: 16 functions instrumented
- `ai_integration/memory_bank/circuit_diff.py`: 13 functions instrumented
- `ai_integration/memory_bank/cli.py`: 2 functions instrumented
- `ai_integration/memory_bank/commands.py`: 8 functions instrumented
- `ai_integration/memory_bank/context.py`: 10 functions instrumented
- `ai_integration/memory_bank/core.py`: 20 functions instrumented
- `ai_integration/memory_bank/git_integration.py`: 7 functions instrumented
- `ai_integration/memory_bank/templates.py`: 3 functions instrumented
- `ai_integration/plugins/ai_design_bridge.py`: 13 functions instrumented
- `ai_integration/stm32_search_helper.py`: 4 functions instrumented
- `ai_integration/validation/real_time_check.py`: 6 functions instrumented
- `ai_integration/validation/simple_validator.py`: 8 functions instrumented
- `component_placement/force_directed_layout.py`: 6 functions instrumented
- `component_placement/geometry.py`: 8 functions instrumented
- `component_placement/placement.py`: 5 functions instrumented
- `component_placement/wire_routing.py`: 2 functions instrumented
- `core/_logger.py`: 5 functions instrumented
- `core/annotations.py`: 8 functions instrumented
- `core/circuit.py`: 27 functions instrumented
- `core/component.py`: 6 functions instrumented
- `core/decorators.py`: 6 functions instrumented
- `core/dependency_injection.py`: 25 functions instrumented
- `core/enhanced_netlist_exporter.py`: 5 functions instrumented
- `core/json_encoder.py`: 1 functions instrumented
- `core/kicad_validator.py`: 9 functions instrumented
- `core/logging_minimal.py`: 8 functions instrumented
- `core/net.py`: 1 functions instrumented
- `core/netlist_exporter.py`: 12 functions instrumented
- `core/performance_profiler.py`: 13 functions instrumented
- `core/pin.py`: 9 functions instrumented
- `core/reference_manager.py`: 9 functions instrumented
- `core/symbol_cache.py`: 20 functions instrumented
- `data/templates/example_project/circuit-synth/debug_header.py`: 1 functions instrumented
- `data/templates/example_project/circuit-synth/esp32c6.py`: 1 functions instrumented
- `data/templates/example_project/circuit-synth/led_blinker.py`: 1 functions instrumented
- `data/templates/example_project/circuit-synth/main.py`: 1 functions instrumented
- `data/templates/example_project/circuit-synth/power_supply.py`: 1 functions instrumented
- `data/templates/example_project/circuit-synth/usb.py`: 1 functions instrumented
- `data/templates/project/main.py`: 1 functions instrumented
- `data/tools/ci-setup/setup_ci_symbols.py`: 4 functions instrumented
- `data/tools/update_examples_with_stock.py`: 9 functions instrumented
- `debugging/analyzer.py`: 16 functions instrumented
- `debugging/knowledge_base.py`: 10 functions instrumented
- `debugging/report_generator.py`: 10 functions instrumented
- `debugging/symptoms.py`: 6 functions instrumented
- `debugging/test_guidance.py`: 7 functions instrumented
- `design_for_manufacturing/comprehensive_dfm_report_generator.py`: 24 functions instrumented
- `design_for_manufacturing/dfm_analyzer.py`: 22 functions instrumented
- `design_for_manufacturing/dfm_analyzer_digikey.py`: 11 functions instrumented
- `design_for_manufacturing/json_dfm_analyzer.py`: 9 functions instrumented
- `design_for_manufacturing/kicad_dfm_analyzer.py`: 19 functions instrumented
- `io/json_loader.py`: 2 functions instrumented
- `kicad/canonical.py`: 21 functions instrumented
- `kicad/core/clean_formatter.py`: 23 functions instrumented
- `kicad/core/s_expression.py`: 25 functions instrumented
- `kicad/core/symbol_cache.py`: 28 functions instrumented
- `kicad/core/types.py`: 22 functions instrumented
- `kicad/formatter_test_harness.py`: 16 functions instrumented
- `kicad/kicad_symbol_cache.py`: 22 functions instrumented
- `kicad/kicad_symbol_parser.py`: 12 functions instrumented
- `kicad/logging_integration.py`: 17 functions instrumented
- `kicad/net_name_generator.py`: 7 functions instrumented
- `kicad/net_tracker.py`: 5 functions instrumented
- `kicad/netlist_exporter.py`: 26 functions instrumented
- `kicad/netlist_service.py`: 7 functions instrumented
- `kicad/pcb_gen/pcb_generator.py`: 9 functions instrumented
- `kicad/project_notes.py`: 10 functions instrumented
- `kicad/sch_gen/api_integration_plan.py`: 6 functions instrumented
- `kicad/sch_gen/circuit_loader.py`: 6 functions instrumented
- `kicad/sch_gen/collision_detection.py`: 4 functions instrumented
- `kicad/sch_gen/collision_manager.py`: 4 functions instrumented
- `kicad/sch_gen/connection_analyzer.py`: 11 functions instrumented
- `kicad/sch_gen/connection_aware_collision_manager.py`: 7 functions instrumented
- `kicad/sch_gen/connection_aware_collision_manager_v2.py`: 6 functions instrumented
- `kicad/sch_gen/data_structures.py`: 2 functions instrumented
- `kicad/sch_gen/debug_performance.py`: 9 functions instrumented
- `kicad/sch_gen/hierarchical_aware_placement.py`: 4 functions instrumented
- `kicad/sch_gen/hierarchy_manager.py`: 1 functions instrumented
- `kicad/sch_gen/integrated_placement.py`: 6 functions instrumented
- `kicad/sch_gen/integrated_reference_manager.py`: 9 functions instrumented
- `kicad/sch_gen/kicad_formatter.py`: 6 functions instrumented
- `kicad/sch_gen/main_generator.py`: 34 functions instrumented
- `kicad/sch_gen/schematic_writer.py`: 23 functions instrumented
- `kicad/sch_gen/shape_drawer.py`: 4 functions instrumented
- `kicad/sch_gen/symbol_geometry.py`: 4 functions instrumented
- `kicad/schematic/bulk_operations.py`: 18 functions instrumented
- `kicad/schematic/component_manager.py`: 17 functions instrumented
- `kicad/schematic/connection_tracer.py`: 16 functions instrumented
- `kicad/schematic/connection_updater.py`: 13 functions instrumented
- `kicad/schematic/connection_utils.py`: 10 functions instrumented
- `kicad/schematic/design_rule_checker.py`: 22 functions instrumented
- `kicad/schematic/geometry_utils.py`: 7 functions instrumented
- `kicad/schematic/hierarchical_synchronizer.py`: 10 functions instrumented
- `kicad/schematic/hierarchy_navigator.py`: 24 functions instrumented
- `kicad/schematic/instance_utils.py`: 2 functions instrumented
- `kicad/schematic/junction_manager.py`: 11 functions instrumented
- `kicad/schematic/label_manager.py`: 13 functions instrumented
- `kicad/schematic/label_utils.py`: 8 functions instrumented
- `kicad/schematic/net_discovery.py`: 15 functions instrumented
- `kicad/schematic/net_matcher.py`: 3 functions instrumented
- `kicad/schematic/placement.py`: 21 functions instrumented
- `kicad/schematic/project_generator.py`: 12 functions instrumented
- `kicad/schematic/schematic_transform.py`: 31 functions instrumented
- `kicad/schematic/search_engine.py`: 25 functions instrumented
- `kicad/schematic/sheet_manager.py`: 20 functions instrumented
- `kicad/schematic/sheet_placement.py`: 5 functions instrumented
- `kicad/schematic/sheet_utils.py`: 13 functions instrumented
- `kicad/schematic/symbol_geometry.py`: 5 functions instrumented
- `kicad/schematic/sync_adapter.py`: 4 functions instrumented
- `kicad/schematic/sync_strategies.py`: 4 functions instrumented
- `kicad/schematic/synchronizer.py`: 15 functions instrumented
- `kicad/schematic/text_manager.py`: 11 functions instrumented
- `kicad/schematic/wire_manager.py`: 14 functions instrumented
- `kicad/schematic/wire_router.py`: 10 functions instrumented
- `kicad/sheet_hierarchy_manager.py`: 20 functions instrumented
- `kicad/symbol_lib_parser.py`: 21 functions instrumented
- `kicad/symbol_lib_parser_manager.py`: 2 functions instrumented
- `manufacturing/digikey/api_client.py`: 12 functions instrumented
- `manufacturing/digikey/cache.py`: 12 functions instrumented
- `manufacturing/digikey/component_search.py`: 8 functions instrumented
- `manufacturing/digikey/config_manager.py`: 8 functions instrumented
- `manufacturing/digikey/test_connection.py`: 2 functions instrumented
- `manufacturing/jlcpcb/cache.py`: 9 functions instrumented
- `manufacturing/jlcpcb/fast_search.py`: 17 functions instrumented
- `manufacturing/jlcpcb/jlc_parts_lookup.py`: 8 functions instrumented
- `manufacturing/jlcpcb/jlc_web_scraper.py`: 11 functions instrumented
- `manufacturing/jlcpcb/smart_component_finder.py`: 19 functions instrumented
- `manufacturing/unified_search.py`: 9 functions instrumented
- `pcb/footprint_library.py`: 16 functions instrumented
- `pcb/kicad_cli.py`: 10 functions instrumented
- `pcb/pcb_board.py`: 65 functions instrumented
- `pcb/pcb_formatter.py`: 3 functions instrumented
- `pcb/pcb_parser.py`: 35 functions instrumented
- `pcb/placement/__init__.py`: 1 functions instrumented
- `pcb/placement/advanced_placement.py`: 1 functions instrumented
- `pcb/placement/base.py`: 13 functions instrumented
- `pcb/placement/bbox.py`: 11 functions instrumented
- `pcb/placement/connection_centric.py`: 9 functions instrumented
- `pcb/placement/connectivity_driven.py`: 13 functions instrumented
- `pcb/placement/courtyard_collision.py`: 19 functions instrumented
- `pcb/placement/courtyard_collision_improved.py`: 20 functions instrumented
- `pcb/placement/force_directed.py`: 12 functions instrumented
- `pcb/placement/force_directed_placement.py`: 2 functions instrumented
- `pcb/placement/force_directed_placement_fixed.py`: 19 functions instrumented
- `pcb/placement/grouping.py`: 9 functions instrumented
- `pcb/placement/hierarchical_placement.py`: 15 functions instrumented
- `pcb/placement/hierarchical_placement_v2.py`: 15 functions instrumented
- `pcb/placement/spiral_hierarchical_placement.py`: 8 functions instrumented
- `pcb/placement/spiral_placement.py`: 2 functions instrumented
- `pcb/placement/spiral_placement_v2.py`: 5 functions instrumented
- `pcb/placement/utils.py`: 2 functions instrumented
- `pcb/ratsnest_generator.py`: 10 functions instrumented
- `pcb/routing/dsn_exporter.py`: 15 functions instrumented
- `pcb/routing/freerouting_docker.py`: 3 functions instrumented
- `pcb/routing/freerouting_runner.py`: 9 functions instrumented
- `pcb/routing/install_freerouting.py`: 8 functions instrumented
- `pcb/routing/ses_importer.py`: 14 functions instrumented
- `pcb/simple_ratsnest.py`: 1 functions instrumented
- `pcb/types.py`: 3 functions instrumented
- `pcb/validation.py`: 19 functions instrumented
- `quality_assurance/circuit_parser.py`: 9 functions instrumented
- `quality_assurance/comprehensive_fmea_report_generator.py`: 26 functions instrumented
- `quality_assurance/enhanced_fmea_analyzer.py`: 14 functions instrumented
- `quality_assurance/fmea_analyzer.py`: 13 functions instrumented
- `quality_assurance/fmea_report_generator.py`: 11 functions instrumented
- `simulation/analysis.py`: 8 functions instrumented
- `simulation/converter.py`: 17 functions instrumented
- `simulation/manufacturer_models.py`: 8 functions instrumented
- `simulation/models.py`: 8 functions instrumented
- `simulation/simulator.py`: 12 functions instrumented
- `simulation/testbench.py`: 12 functions instrumented
- `simulation/visualization.py`: 12 functions instrumented
- `tools/debug_cli.py`: 11 functions instrumented
- `tools/development/pcb_tracker_basic.py`: 5 functions instrumented
- `tools/development/setup_claude.py`: 8 functions instrumented
- `tools/development/setup_kicad_plugins.py`: 7 functions instrumented
- `tools/jlc_fast_search_cli.py`: 7 functions instrumented
- `tools/kicad_integration/kicad_to_python_sync.py`: 4 functions instrumented
- `tools/kicad_integration/preload_symbols.py`: 4 functions instrumented
- `tools/kicad_integration/preparse_kicad_symbols.py`: 11 functions instrumented
- `tools/kicad_integration/python_to_kicad_sync.py`: 10 functions instrumented
- `tools/project_management/init_existing_project.py`: 19 functions instrumented
- `tools/project_management/init_pcb.py`: 8 functions instrumented
- `tools/project_management/new_pcb.py`: 1 functions instrumented
- `tools/project_management/new_project.py`: 7 functions instrumented
- `tools/quality_assurance/fmea_cli.py`: 1 functions instrumented
- `tools/utilities/ai_design_manager.py`: 5 functions instrumented
- `tools/utilities/circuit_creator_cli.py`: 6 functions instrumented
- `tools/utilities/kicad_netlist_parser.py`: 3 functions instrumented
- `tools/utilities/kicad_parser.py`: 14 functions instrumented
- `tools/utilities/llm_code_updater.py`: 11 functions instrumented
- `tools/utilities/models.py`: 3 functions instrumented
- `tools/utilities/python_code_generator.py`: 23 functions instrumented

## Called Functions

The following functions were called during execution:

- _decorator in circuit_synth/core/decorators.py
- circuit in circuit_synth/core/decorators.py
- decorator in circuit_synth/core/performance_profiler.py
- get_container in circuit_synth/core/dependency_injection.py
- get_current_circuit in circuit_synth/core/decorators.py
- wrapper in circuit_synth/core/performance_profiler.py

## Recommendations

1. **Review functions not called** during this analysis
2. **Consider additional test scenarios** to ensure comprehensive coverage
3. **Search codebase** for dynamic calls or reflection usage
4. **Check git history** for external usage before removing code
5. **Remove dead code gradually** with proper testing

## Notes

- This analysis is based on a single execution path
- Some functions may be used in other contexts not covered by the test
- Consider running multiple test scenarios for comprehensive analysis
- Review functions used only in error handling or edge cases