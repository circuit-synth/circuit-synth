# Dead Code Analysis Report

## Executive Summary

- **Total Functions Analyzed**: 3,558
- **Functions Actually Called**: 160
- **Potentially Dead Functions**: 3,245
- **Potentially Dead Modules**: 270
- **Code Utilization**: 4.5%

⚠️  **3245 functions (91.2%) appear to be unused**

## 🚨 Potentially Dead Modules (High Priority)

These entire modules have no functions that were called during the test run. These are the best candidates for removal:

### `circuit_synth/kicad_api/pcb/pcb_board.py`
- **Functions**: 67
- **Functions list**: __init__, add_net, get_net_info, get_net_count, get_footprint, list_footprints, _create_empty_pcb, _get_default_layers, _get_default_setup, load, save, add_footprint, _add_default_pads, remove_footprint, move_footprint, update_footprint_value, get_net_by_name, get_board_outline, get_board_outline, set_board_outline, get_footprint_count, clear_footprints, get_board_info, get_ratsnest, get_connections, connect_pads, disconnect_pad, add_track, route_connection, route_ratsnest, get_tracks, remove_track, clear_tracks, add_via, set_board_outline_rect, set_board_outline_polygon, add_edge_cut_line, clear_edge_cuts, get_board_outline_bbox, _add_graphic_item, add_zone, get_zones, remove_zone, clear_zones, fill_zone, unfill_zone, auto_place_components, get_placement_bbox, footprints, add_footprint_object, run_drc, check_basic_rules, export_gerbers, export_drill, export_pick_and_place, search_footprints, get_footprint_info, add_footprint_from_library, _create_footprint_from_library_data, _parse_library_pad, _parse_library_line, _parse_library_arc, _parse_library_text, _parse_library_rect, list_available_libraries, refresh_footprint_cache, _parse_library_model

### `circuit_synth/pcb/pcb_board.py`
- **Functions**: 66
- **Functions list**: __init__, add_net, get_net_info, get_net_count, get_footprint, list_footprints, _create_empty_pcb, _get_default_layers, _get_default_setup, load, save, add_footprint, _add_default_pads, remove_footprint, move_footprint, update_footprint_value, get_net_by_name, get_board_outline, get_board_outline, set_board_outline, get_footprint_count, clear_footprints, get_board_info, get_ratsnest, get_connections, connect_pads, disconnect_pad, add_track, route_connection, route_ratsnest, get_tracks, remove_track, clear_tracks, add_via, set_board_outline_rect, set_board_outline_polygon, add_edge_cut_line, clear_edge_cuts, get_board_outline_bbox, _add_graphic_item, add_zone, get_zones, remove_zone, clear_zones, fill_zone, unfill_zone, auto_place_components, get_placement_bbox, footprints, add_footprint_object, run_drc, check_basic_rules, export_gerbers, export_drill, export_pick_and_place, search_footprints, get_footprint_info, add_footprint_from_library, _create_footprint_from_library_data, _parse_library_pad, _parse_library_line, _parse_library_arc, _parse_library_text, _parse_library_rect, list_available_libraries, refresh_footprint_cache

### `circuit_synth/interfaces/circuit_interface.py`
- **Functions**: 62
- **Functions list**: to_dict, to_dict, to_dict, add_component, remove_component, get_component, connect_to_net, add_net, get_symbol, from_dict, add_pin, get_component_type, get_footprint, get_property, set_property, get_name, get_name, get_name, set_name, set_name, set_name, get_components, remove_net, get_net, get_nets, connect, disconnect, disconnect, validate, validate, validate, validate, get_statistics, get_reference, set_reference, get_value, set_value, set_footprint, set_symbol, get_library, set_library, get_properties, get_pins, get_pins, get_pin, get_position, get_position, set_position, set_position, get_rotation, set_rotation, get_number, get_pin_type, set_pin_type, get_electrical_type, set_electrical_type, get_connected_net, is_connected, remove_pin, get_pin_count, is_connected_to, get_connected_components

### `circuit_synth/kicad/netlist_importer.py`
- **Functions**: 60
- **Functions list**: __init__, __init__, __init__, add_node, to_dict, to_dict, to_dict, to_dict, to_dict, to_dict, to_dict, to_dict, main, components, nets, parse_file, convert_netlist, from_kicad, add_pin, _clean_artifact_subcircuits, _is_human_readable_name, parse, _tokenize, _parse_expr, _find_section, design, sheets, libparts, parse_kicad_netlist, _parse_libparts, _determine_pin_type, _build_hierarchy_from_design, _extract_sheet_info, _process_sheet_hierarchies, _create_subcircuit_hierarchy, _register_component, _parse_components, _get_pin_details, _parse_nets, _extract_net_info, _extract_node_info, _get_component_sheet_path, _add_node_to_subcircuit, _build_net_mapping, _standardize_net_name, _get_local_net_name, _normalize_sheet_path, _find_or_create_subcircuit, _get_subcircuit_name_from_path, _get_parent_path, _extract_sheetpath, _parse_design_properties, _verify_and_log_hierarchy, detect_duplicate_circuits, _extract_schematic_source, _generate_component_signature, _generate_template_id, _generate_canonical_name, _collect_attached_subcircuits, _log_subcircuit_hierarchy

### `circuit_synth/kicad/unified_kicad_integration.py`
- **Functions**: 43
- **Functions list**: __init__, __init__, __init__, __init__, __init__, add_component, validate_schematic, generate_netlist, add_wire, get_symbol, list_libraries, list_libraries, create_unified_kicad_integration, create_unified_schematic_generator, create_unified_pcb_generator, create_unified_symbol_library, create_unified_footprint_library, generate_from_circuit_data, generate_from_circuit_data, initialize_project, add_net_connection, set_component_property, save_schematic, get_component_count, get_net_count, _add_components_from_circuit_data, _apply_placement_algorithm, list_symbols, get_footprint, list_footprints, generate_schematic, generate_pcb, validate_design, get_version, validate_installation, get_symbol_libraries, get_footprint_libraries, generate_project, create_schematic_generator, create_pcb_generator, get_symbol_library, get_footprint_library, cleanup

### `circuit_synth/kicad/sch_gen/main_generator.py`
- **Functions**: 42
- **Functions list**: __init__, __init__, __init__, __init__, __init__, collect_from_circuit, place_components, generate_from_circuit_data, generate_from_circuit_data, generate_schematic, generate_pcb, validate_design, get_version, validate_installation, get_symbol_libraries, get_footprint_libraries, generate_project, create_schematic_generator, create_pcb_generator, get_symbol_library, get_footprint_library, cleanup, search_footprints, get_footprint_info, get_symbol_info, get_schematic_generator, get_pcb_generator, get_capabilities, _collect_all_references, _check_existing_project, _update_existing_project, _add_bounding_boxes_to_existing_project, _log_sync_results, _generate_netlist, _determine_paper_size, _collision_place_all_circuits, _prepare_blank_project, _write_cover_sheet, _update_kicad_pro, generate_pcb_from_schematics, generate_from_schematic, search_symbols

### `circuit_synth/interfaces/kicad_interface.py`
- **Functions**: 37
- **Functions list**: add_component, validate_schematic, __post_init__, __post_init__, generate_netlist, add_wire, initialize_project, add_net_connection, set_component_property, save_schematic, get_component_count, get_net_count, get_version, validate_installation, get_symbol_libraries, get_footprint_libraries, create_schematic_generator, create_pcb_generator, set_board_outline, add_via, auto_place_components, run_drc, export_gerbers, get_footprint_info, validate_pcb, initialize_pcb, import_netlist, place_component, route_traces, save_pcb, get_component_placements, get_routing_statistics, search_symbol, get_symbol_info, validate_symbol, search_footprint, validate_footprint

### `circuit_synth/pcb/pcb_parser.py`
- **Functions**: 36
- **Functions list**: __init__, parse_file, parse_string, write_file, dumps, _is_sexp_list, _get_symbol_name, _find_element, _find_all_elements, _get_value, _parse_general, _parse_layers, _parse_net, _parse_footprint, _parse_property, _parse_pad, _parse_line, _parse_arc, _parse_rectangle, _parse_text, _parse_via, _parse_track, _pcb_to_sexp, _zone_to_sexp, _parse_zone, _gr_rect_to_sexp, _footprint_to_sexp, _property_to_sexp, _pad_to_sexp, _line_to_sexp, _arc_to_sexp, _text_to_sexp, _rect_to_sexp, _via_to_sexp, _track_to_sexp, _gr_line_to_sexp

### `circuit_synth/kicad_api/pcb/pcb_parser.py`
- **Functions**: 36
- **Functions list**: __init__, parse_file, parse_string, write_file, dumps, _is_sexp_list, _get_symbol_name, _find_element, _find_all_elements, _get_value, _parse_general, _parse_layers, _parse_net, _parse_footprint, _parse_property, _parse_pad, _parse_line, _parse_arc, _parse_rectangle, _parse_text, _parse_via, _parse_track, _pcb_to_sexp, _zone_to_sexp, _parse_zone, _gr_rect_to_sexp, _footprint_to_sexp, _property_to_sexp, _pad_to_sexp, _line_to_sexp, _arc_to_sexp, _text_to_sexp, _rect_to_sexp, _via_to_sexp, _track_to_sexp, _gr_line_to_sexp

### `circuit_synth/codegen/json_to_python_project.py`
- **Functions**: 34
- **Functions list**: dfs, main, circuit_synth_json_to_python_project, _phase1_load_circuit, _phase2_rename_circuits, _scan_json_references, _clear_all_reference_managers, _phase3_find_repeated_components, _make_common_varname, _phase3_write_common_parts, _phase4_gather_net_usage, _phase4_compute_net_owners_lca, _phase4_assign_nets_to_circuits, _phase5_unify_net_names, _phase6_compute_imported_nets_with_descendants, _phase7_write_all_circuits_organized, _write_all_circuits_standard, _generate_circuit_py_for_circuits_folder, _sanitize_for_param, _phase8_generate_main_py, sanitize, sanitize, scan_data, clear_circuit, gather, gather, gather, walk, get_ancestry, find_lca, initall, rename, is_ancestor, rec

### `circuit_synth/kicad_api/core/s_expression.py`
- **Functions**: 33
- **Functions list**: __init__, parse_file, parse_string, write_file, dumps, _format_sexp, to_schematic, from_schematic, _is_sexp_list, _get_symbol_name, _find_element, _find_all_elements, _get_value, _parse_title_block, _parse_symbol, _parse_wire, _parse_label, _parse_junction, _parse_sheet, _parse_sheet_pin, _symbol_to_sexp, _wire_to_sexp, _sheet_to_sexp, _generate_lib_symbols, _symbol_definition_to_sexp, _graphic_element_to_sexp, _label_to_sexp, _junction_to_sexp, _rectangle_to_sexp, _text_to_sexp, _textbox_to_sexp, _simple_text_to_sexp, _color_name_to_rgb

### `circuit_synth/schematic/schematic_transform.py`
- **Functions**: 32
- **Functions list**: __init__, apply, compose, identity, rotation, scale, translation, mirror_x, mirror_y, width, height, center, expand, contains_point, intersects, push_transform, pop_transform, get_current_transform, transform_position, transform_component, transform_wire, transform_junction, transform_text, transform_label, rotate_elements, mirror_elements, scale_elements, translate_elements, align_elements, distribute_elements, calculate_bounding_box, auto_arrange

### `circuit_synth/kicad_api/schematic/schematic_transform.py`
- **Functions**: 32
- **Functions list**: __init__, apply, compose, identity, rotation, scale, translation, mirror_x, mirror_y, width, height, center, expand, contains_point, intersects, push_transform, pop_transform, get_current_transform, transform_position, transform_component, transform_wire, transform_junction, transform_text, transform_label, rotate_elements, mirror_elements, scale_elements, translate_elements, align_elements, distribute_elements, calculate_bounding_box, auto_arrange

### `circuit_synth/core/s_expression.py`
- **Functions**: 29
- **Functions list**: __init__, parse_file, parse_string, write_file, dumps, _format_sexp, to_schematic, from_schematic, _is_sexp_list, _get_symbol_name, _find_element, _find_all_elements, _get_value, _parse_title_block, _parse_symbol, _parse_wire, _parse_label, _parse_junction, _parse_sheet, _parse_sheet_pin, _symbol_to_sexp, _wire_to_sexp, _sheet_to_sexp, _generate_lib_symbols, _symbol_definition_to_sexp, _graphic_element_to_sexp, _label_to_sexp, _junction_to_sexp, _rectangle_to_sexp

### `circuit_synth/core/dependency_injection.py`
- **Functions**: 28
- **Functions list**: __init__, __init__, configure_default_dependencies, get_service, inject, register, register, register_singleton, register_singleton, register_transient, register_transient, register_factory, register_factory, register_instance, register_instance, resolve, resolve, resolve, is_registered, is_registered, is_registered, _create_instance, get_registrations, clear, set_container, get_container, decorator, wrapper

### `circuit_synth/kicad_api/core/symbol_cache.py`
- **Functions**: 28
- **Functions list**: __init__, get_symbol_cache, bounding_box, add_library_path, get_symbol, get_symbol_by_name, get_reference_prefix, _load_default_libraries, _load_symbol, _save_cache, _serialize_symbol, _deserialize_symbol, _build_complete_index, _parse_kicad_symbol_dirs, _extract_symbol_names_fast, _find_library_file, _load_library, _compute_file_hash, _cache_filename, _convert_to_symbol_definition, get_all_symbols, list_libraries, _lazy_symbol_search, _find_symbol_file_by_name, _ripgrep_symbol_search, _python_grep_search, _load_symbol_from_file, extract_property_value

### `circuit_synth/schematic/search_engine.py`
- **Functions**: 27
- **Functions list**: __init__, __init__, add_criterion, total_count, is_empty, parse_value, _build_indices, search_components, _matches_query, _get_component_field, _matches_pattern, search_nets, search_by_value, search_by_footprint, find_components_in_area, find_unconnected_pins, find_power_nets, find_duplicate_references, trace_net, get_net_statistics, with_reference, with_value, with_footprint, with_property, combine_with_or, combine_with_and, build

### `circuit_synth/kicad_api/schematic/search_engine.py`
- **Functions**: 27
- **Functions list**: __init__, __init__, add_criterion, total_count, is_empty, parse_value, _build_indices, search_components, _matches_query, _get_component_field, _matches_pattern, search_nets, search_by_value, search_by_footprint, find_components_in_area, find_unconnected_pins, find_power_nets, find_duplicate_references, trace_net, get_net_statistics, with_reference, with_value, with_footprint, with_property, combine_with_or, combine_with_and, build

### `circuit_synth/kicad/canonical.py`
- **Functions**: 26
- **Functions list**: __init__, __init__, __str__, __repr__, __repr__, components, _parse_symbol, _parse_wire, _parse_label, from_kicad, _group_by_component, component_count, from_circuit, _process_subcircuit_recursive, _extract_symbols, _extract_properties, _is_power_symbol, _extract_net_connections, _extract_wires_and_labels, _get_pin_connections, get_component_type, get_component_nets, match, _group_components_by_type, _match_by_connectivity, _calculate_connectivity_score

### `circuit_synth/kicad/netlist_exporter.py`
- **Functions**: 26
- **Functions list**: generate_netlist, convert_json_to_netlist, sort_key, normalize_hierarchical_path, normalize_hierarchical_path, load_circuit_json, cleanup_whitespace, generate_design_section, _extract_sheets_from_circuit, generate_components_section, generate_libparts_section, generate_libpart_entry, generate_libraries_section, validate_net_data, generate_nets_section, determine_net_ownership, generate_component_entry, generate_net_entry, format_s_expr, format_node, to_kicad, process_circuit, process_components, _collect_components_recursive, process_net_nodes, scan_circuit

### `circuit_synth/schematic/hierarchy_navigator.py`
- **Functions**: 25
- **Functions list**: __init__, validate_hierarchy, dfs, add_child, get_full_path, find_node, get_hierarchy_tree, _build_hierarchy_recursive, _load_sheet_schematic, find_sheet_by_name, get_sheet_path, get_all_sheets_recursive, _check_missing_files, _check_duplicate_names, _check_sheet_pins, _get_schematic_containing_sheet, _validate_sheet_connections, find_circular_references, get_net_scope, analyze_hierarchy, get_instance_count, count_recursive, count_recursive, count_instances, check_files

### `circuit_synth/kicad_api/schematic/hierarchy_navigator.py`
- **Functions**: 25
- **Functions list**: __init__, validate_hierarchy, dfs, add_child, get_full_path, find_node, get_hierarchy_tree, _build_hierarchy_recursive, _load_sheet_schematic, find_sheet_by_name, get_sheet_path, get_all_sheets_recursive, _check_missing_files, _check_duplicate_names, _check_sheet_pins, _get_schematic_containing_sheet, _validate_sheet_connections, find_circular_references, get_net_scope, analyze_hierarchy, get_instance_count, count_recursive, count_recursive, count_instances, check_files

### `circuit_synth/core/types.py`
- **Functions**: 25
- **Functions list**: add_label, add_text, total_count, add_node, add_junction, width, height, center, contains_point, contains_point, intersects, add_component, remove_component, get_component, get_bounding_box, __post_init__, __iter__, __getitem__, to_tuple, uuid, get_endpoints, _point_on_segment, add_wire, add_rectangle, get_all_elements

### `circuit_synth/kicad_api/core/types.py`
- **Functions**: 25
- **Functions list**: add_label, add_text, total_count, add_node, add_junction, width, height, center, contains_point, contains_point, intersects, add_component, remove_component, get_component, get_bounding_box, __post_init__, __iter__, __getitem__, to_tuple, uuid, get_endpoints, _point_on_segment, add_wire, add_rectangle, get_all_elements

### `circuit_synth/schematic/design_rule_checker.py`
- **Functions**: 24
- **Functions list**: __init__, __str__, check_schematic, _add_violation, _check_unconnected_pins, _check_floating_nets, _check_power_pins, _check_duplicate_references, _check_missing_references, _check_reference_naming, _check_net_naming, _check_overlapping_components, _check_off_grid, _check_wire_length, _check_wire_junctions, _find_wire_intersection, _check_missing_values, _check_missing_footprints, _check_required_properties, _check_text_size, get_summary, get_violations_by_category, filter_violations, is_on_grid

### `circuit_synth/tools/python_code_generator.py`
- **Functions**: 24
- **Functions list**: __init__, _sanitize_variable_name, update_python_file, _generate_flat_code, _generate_component_code, _generate_project_call, _format_net_summary, generate_hierarchical_code, _generate_subcircuit_code, _generate_main_circuit_code, update_or_create_file, _get_ancestors, _get_depth, _find_lowest_common_ancestor, _determine_net_scope, _analyze_hierarchical_nets, _generate_multiple_files, _generate_standalone_subcircuit_file, _generate_subcircuit_code_with_params, _generate_main_file_with_imports, _identify_top_level_circuits, _get_child_interface_nets, _generate_hierarchical_circuit_recursive, _generate_main_circuit_code_with_params

### `circuit_synth/kicad/kicad_symbol_cache.py`
- **Functions**: 24
- **Functions list**: __init__, decorator, _build_complete_index, _parse_kicad_symbol_dirs, _extract_symbol_names_fast, _find_library_file, _load_library, _compute_file_hash, _cache_filename, get_all_symbols, quick_time, get_symbol_data, __new__, _get_cache_dir, get_symbol_data_by_name, find_symbol_library, get_all_libraries, _find_kicad_symbol_dirs, _is_cache_expired, _lazy_symbol_search, _find_symbol_file_by_name, _ripgrep_symbol_search, _python_grep_search, _load_symbol_from_file_direct

### `circuit_synth/kicad/sch_sync/synchronizer.py`
- **Functions**: 24
- **Functions list**: __init__, to_dict, sync_with_circuit, _extract_circuit_components, _schematic_has_components, synchronize, __post_init__, _collect_components_recursive, _find_sections, _get_component_updates, _load_kicad_schematic, _find_main_schematic, _find_sheet_uuid_for_schematic, _extract_kicad_components, _process_component_matches, _process_unmatched_components, _component_needs_update, _check_connection_changes, _export_kicad_netlist, _match_components_canonical, _extract_symbols_ordered, _extract_properties_from_symbol, _write_updated_schematic, extract_symbols_recursive

### `circuit_synth/kicad_api/schematic/design_rule_checker.py`
- **Functions**: 24
- **Functions list**: __init__, __str__, check_schematic, _add_violation, _check_unconnected_pins, _check_floating_nets, _check_power_pins, _check_duplicate_references, _check_missing_references, _check_reference_naming, _check_net_naming, _check_overlapping_components, _check_off_grid, _check_wire_length, _check_wire_junctions, _find_wire_intersection, _check_missing_values, _check_missing_footprints, _check_required_properties, _check_text_size, get_summary, get_violations_by_category, filter_violations, is_on_grid

### `circuit_synth/kicad_api/schematic/placement.py`
- **Functions**: 24
- **Functions list**: __init__, __init__, _snap_to_grid, right, bottom, overlaps, find_position, _estimate_component_size, _estimate_sheet_size, place_element, _find_next_available_position, _find_next_available_position_with_size, _find_grid_position, _find_edge_position, _find_center_position, _get_occupied_bounds, _check_within_bounds, arrange_components, _arrange_grid, _arrange_vertical, _arrange_horizontal, _arrange_circular, _arrange_force_directed_rust, _arrange_force_directed_python

### `circuit_synth/core/circuit.py`
- **Functions**: 23
- **Functions list**: __init__, to_dict, add_component, validate_reference, register_reference, add_subcircuit, finalize_references, _add_docstring_annotation, generate_text_netlist, generate_full_netlist, add_net, add_annotation, generate_json_netlist, to_flattened_list, generate_flattened_json_netlist, _generate_hierarchical_json_netlist, generate_kicad_netlist, generate_kicad_project, simulate, simulator, components, nets, collect_from_circuit

### `circuit_synth/kicad/symbol_lib_parser.py`
- **Functions**: 23
- **Functions list**: __init__, _find_library_file, __new__, to_simple_dict, to_simple_dict, to_simple_dict, from_simple_dict, from_simple_dict, from_simple_dict, merge_parent, _initialize, _parse_file, _parse_symbol_body, _parse_subsymbol, _parse_pin, _parse_graphic_element, _parse_property_elem, _resolve_all_extends, _resolve_extends_for_symbol, _get_unit_number, _get_key, _find_kicad_sym_file, parse_symbol

### `circuit_synth/kicad_api/pcb/courtyard_collision_improved.py`
- **Functions**: 23
- **Functions list**: __init__, __init__, expand, contains_point, intersects, get_bounding_box, check_collision, _calculate_signed_area, transform, get_courtyard_polygon, get_footprint_polygon, _calculate_footprint_bbox, __sub__, dot, perp_dot, get_edges, get_axes, project_onto_axis, detect_collisions, _bounding_boxes_overlap, _get_cached_polygon, _trace_polygon_from_lines, get_collision_vector

### `circuit_synth/kicad_api/pcb/force_directed_placement.py`
- **Functions**: 23
- **Functions list**: __init__, _build_connection_graph, __mul__, __add__, magnitude, place, _group_by_subcircuit, _initialize_group_positions, _optimize_subcircuit, _optimize_rotations, _update_group_properties, _count_inter_group_connections, _optimize_group_positions, _calculate_attraction, _calculate_repulsion, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_repulsion, _calculate_group_boundary_force, _enforce_minimum_spacing, _connectivity_aware_collision_resolution, normalize, _build_connectivity_from_board

### `circuit_synth/kicad_api/pcb/placement/courtyard_collision_improved.py`
- **Functions**: 23
- **Functions list**: __init__, __init__, expand, contains_point, intersects, get_bounding_box, check_collision, _calculate_signed_area, transform, get_courtyard_polygon, get_footprint_polygon, _calculate_footprint_bbox, __sub__, dot, perp_dot, get_edges, get_axes, project_onto_axis, detect_collisions, _bounding_boxes_overlap, _get_cached_polygon, _trace_polygon_from_lines, get_collision_vector

### `circuit_synth/kicad_api/pcb/placement/force_directed_placement.py`
- **Functions**: 23
- **Functions list**: __init__, _build_connection_graph, __mul__, __add__, magnitude, place, _group_by_subcircuit, _initialize_group_positions, _optimize_subcircuit, _optimize_rotations, _update_group_properties, _count_inter_group_connections, _optimize_group_positions, _calculate_attraction, _calculate_repulsion, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_repulsion, _calculate_group_boundary_force, _enforce_minimum_spacing, _connectivity_aware_collision_resolution, normalize, _build_connectivity_from_board

### `circuit_synth/pcb/placement/courtyard_collision_improved.py`
- **Functions**: 23
- **Functions list**: __init__, __init__, expand, contains_point, intersects, get_bounding_box, check_collision, _calculate_signed_area, transform, get_courtyard_polygon, get_footprint_polygon, _calculate_footprint_bbox, __sub__, dot, perp_dot, get_edges, get_axes, project_onto_axis, detect_collisions, _bounding_boxes_overlap, _get_cached_polygon, _trace_polygon_from_lines, get_collision_vector

### `circuit_synth/pcb/placement/force_directed_placement.py`
- **Functions**: 23
- **Functions list**: __init__, _build_connection_graph, __mul__, __add__, magnitude, place, _group_by_subcircuit, _initialize_group_positions, _optimize_subcircuit, _optimize_rotations, _update_group_properties, _count_inter_group_connections, _optimize_group_positions, _calculate_attraction, _calculate_repulsion, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_repulsion, _calculate_group_boundary_force, _enforce_minimum_spacing, _connectivity_aware_collision_resolution, normalize, _build_connectivity_from_board

### `circuit_synth/schematic/placement.py`
- **Functions**: 22
- **Functions list**: __init__, __init__, _snap_to_grid, right, bottom, overlaps, find_position, _estimate_component_size, _estimate_sheet_size, place_element, _find_next_available_position, _find_next_available_position_with_size, _find_grid_position, _find_edge_position, _find_center_position, _get_occupied_bounds, _check_within_bounds, arrange_components, _arrange_grid, _arrange_vertical, _arrange_horizontal, _arrange_circular

### `circuit_synth/core/symbol_cache.py`
- **Functions**: 22
- **Functions list**: __init__, get_symbol_cache, bounding_box, add_library_path, get_symbol, get_symbol_by_name, get_reference_prefix, _load_default_libraries, _load_symbol, _save_cache, _serialize_symbol, _deserialize_symbol, _build_complete_index, _parse_kicad_symbol_dirs, _extract_symbol_names_fast, _find_library_file, _load_library, _compute_file_hash, _cache_filename, _convert_to_symbol_definition, get_all_symbols, list_libraries

### `circuit_synth/pcb/validation.py`
- **Functions**: 22
- **Functions list**: __init__, __str__, is_valid, print_summary, validate_pcb, error_count, warning_count, info_count, add_error, add_warning, add_info, validate_board, _validate_board_outline, _validate_component_placement, _validate_overlapping_footprints, _validate_net_connectivity, _validate_tracks, _validate_vias, _validate_zones, _validate_isolated_copper, _get_footprint_bbox, _bbox_spacing

### `circuit_synth/memory_bank/core.py`
- **Functions**: 22
- **Functions list**: __init__, __init__, create_project_structure, _create_project_level_files, _create_board_structure, add_board, remove_memory_bank, is_memory_bank_enabled, get_config, get_boards, update_from_commit, _get_commit_message, _analyze_commit_changes, _should_update_decisions, _should_update_timeline, _update_decisions_file, _update_timeline_file, _update_decisions_file_with_diff, _update_timeline_file_with_diff, _update_issues_file_with_diff, _should_update_timeline_from_diff, _should_update_issues_from_diff

### `circuit_synth/kicad/sch_gen/schematic_writer.py`
- **Functions**: 22
- **Functions list**: __init__, decorator, quick_time, _add_components, find_pin_by_identifier, validate_arc_geometry, write_schematic_file, generate_s_expr, _place_components, _add_pin_level_net_labels, _add_subcircuit_sheets, _add_component_bounding_boxes, _add_annotations, _add_textbox_annotation, _add_text_annotation, _add_table_annotation, _add_paper_size, _add_symbol_definitions, _create_symbol_definition, _add_sheet_instances, _add_symbol_instances_table, find_sheet_pins_in_expr

### `circuit_synth/kicad_api/pcb/force_directed_placement_fixed.py`
- **Functions**: 22
- **Functions list**: __init__, _build_connection_graph, __mul__, __add__, magnitude, place, _group_by_subcircuit, _initialize_group_positions, _optimize_subcircuit, _optimize_rotations, _update_group_properties, _count_inter_group_connections, _optimize_group_positions, _calculate_attraction, _calculate_repulsion, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_repulsion, _calculate_group_boundary_force, _enforce_minimum_spacing, _build_connectivity_from_graph, _connectivity_aware_collision_resolution

### `circuit_synth/kicad_api/pcb/validation.py`
- **Functions**: 22
- **Functions list**: __init__, __str__, is_valid, print_summary, validate_pcb, error_count, warning_count, info_count, add_error, add_warning, add_info, validate_board, _validate_board_outline, _validate_component_placement, _validate_overlapping_footprints, _validate_net_connectivity, _validate_tracks, _validate_vias, _validate_zones, _validate_isolated_copper, _get_footprint_bbox, _bbox_spacing

### `circuit_synth/kicad_api/pcb/placement/force_directed_placement_fixed.py`
- **Functions**: 22
- **Functions list**: __init__, _build_connection_graph, __mul__, __add__, magnitude, place, _group_by_subcircuit, _initialize_group_positions, _optimize_subcircuit, _optimize_rotations, _update_group_properties, _count_inter_group_connections, _optimize_group_positions, _calculate_attraction, _calculate_repulsion, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_repulsion, _calculate_group_boundary_force, _enforce_minimum_spacing, _build_connectivity_from_graph, _connectivity_aware_collision_resolution

### `circuit_synth/pcb/placement/force_directed_placement_fixed.py`
- **Functions**: 22
- **Functions list**: __init__, _build_connection_graph, __mul__, __add__, magnitude, place, _group_by_subcircuit, _initialize_group_positions, _optimize_subcircuit, _optimize_rotations, _update_group_properties, _count_inter_group_connections, _optimize_group_positions, _calculate_attraction, _calculate_repulsion, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_repulsion, _calculate_group_boundary_force, _enforce_minimum_spacing, _build_connectivity_from_graph, _connectivity_aware_collision_resolution

### `circuit_synth/schematic/sheet_manager.py`
- **Functions**: 21
- **Functions list**: __init__, _index_sheets, add_sheet, remove_sheet, update_sheet, add_sheet_pin, remove_sheet_pin, get_sheet_contents, create_sheet_from_components, get_sheet_by_name, get_sheet_hierarchy, validate_hierarchy, _validate_filename, _resolve_sheet_path, _calculate_pin_position, _get_pin_orientation, _recalculate_pin_positions, _calculate_sheet_size, _find_sheet_position, _find_circular_references, dfs

### `circuit_synth/schematic/bulk_operations.py`
- **Functions**: 21
- **Functions list**: __init__, __init__, create_value_update_operation, create_move_operation, create_footprint_update_operation, applies_to, affected_count, execute_operation, _update_property, _move_components, _delete_components, _duplicate_components, _replace_symbol, _update_value, _update_footprint, _add_property, _remove_property, create_operation_batch, get_operation_history, add_operation, execute

### `circuit_synth/kicad/sheet_hierarchy_manager.py`
- **Functions**: 21
- **Functions list**: __init__, validate_hierarchy, parse_sheet_hierarchy, _build_hierarchy, _validate_hierarchy, _build_path_map, get_sheet_order, get_sheet_paths, _validate_uuid, parse_sheet_data, normalize_path, get_sheet_by_path, get_sheet_by_uuid, get_parent_sheet, get_child_sheets, check_cycles, validate_node, collect_reachable, traverse, traverse, traverse

### `circuit_synth/manufacturing/jlcpcb/smart_component_finder.py`
- **Functions**: 21
- **Functions list**: __init__, find_component, find_components, find_components, print_component_recommendation, get_best_component, find_alternatives, _create_recommendation, _find_kicad_symbol, _find_kicad_footprint, _generate_circuit_synth_code, _calculate_score, _generate_recommendation_notes, _load_symbol_mappings, _load_footprint_mappings, _guess_symbol_from_description, _guess_footprint_from_package, _get_reference_designator, _is_passive_component, _extract_component_value, _extract_component_family

### `circuit_synth/kicad_api/schematic/sheet_manager.py`
- **Functions**: 21
- **Functions list**: __init__, _index_sheets, add_sheet, remove_sheet, update_sheet, add_sheet_pin, remove_sheet_pin, get_sheet_contents, create_sheet_from_components, get_sheet_by_name, get_sheet_hierarchy, validate_hierarchy, _validate_filename, _resolve_sheet_path, _calculate_pin_position, _get_pin_orientation, _recalculate_pin_positions, _calculate_sheet_size, _find_sheet_position, _find_circular_references, dfs

### `circuit_synth/kicad_api/schematic/bulk_operations.py`
- **Functions**: 21
- **Functions list**: __init__, __init__, create_value_update_operation, create_move_operation, create_footprint_update_operation, applies_to, affected_count, execute_operation, _update_property, _move_components, _delete_components, _duplicate_components, _replace_symbol, _update_value, _update_footprint, _add_property, _remove_property, create_operation_batch, get_operation_history, add_operation, execute

### `circuit_synth/kicad_api/pcb/courtyard_collision.py`
- **Functions**: 21
- **Functions list**: __init__, __init__, contains_point, get_bounding_box, check_collision, _calculate_signed_area, transform, get_courtyard_polygon, _lines_to_polygon, _circle_to_polygon, _arcs_to_polygon, get_footprint_polygon, _calculate_footprint_bbox, _bboxes_overlap, check_collision_with_placed, find_valid_position, _polygons_intersect, _project_polygon, _inflate_polygon, _normalize_vector, _is_inside_board

### `circuit_synth/kicad_api/pcb/placement/courtyard_collision.py`
- **Functions**: 21
- **Functions list**: __init__, __init__, contains_point, get_bounding_box, check_collision, _calculate_signed_area, transform, get_courtyard_polygon, _lines_to_polygon, _circle_to_polygon, _arcs_to_polygon, get_footprint_polygon, _calculate_footprint_bbox, _bboxes_overlap, check_collision_with_placed, find_valid_position, _polygons_intersect, _project_polygon, _inflate_polygon, _normalize_vector, _is_inside_board

### `circuit_synth/pcb/placement/courtyard_collision.py`
- **Functions**: 21
- **Functions list**: __init__, __init__, contains_point, get_bounding_box, check_collision, _calculate_signed_area, transform, get_courtyard_polygon, _lines_to_polygon, _circle_to_polygon, _arcs_to_polygon, get_footprint_polygon, _calculate_footprint_bbox, _bboxes_overlap, check_collision_with_placed, find_valid_position, _polygons_intersect, _project_polygon, _inflate_polygon, _normalize_vector, _is_inside_board

### `circuit_synth/schematic/connection_tracer.py`
- **Functions**: 20
- **Functions list**: __init__, __init__, trace_net, _points_equal, __hash__, __hash__, add_node, add_node, add_edge, add_edge, get_node_at, find_path, _build_connection_graph, _get_or_create_node, find_all_connections, get_net_endpoints, find_path_between_pins, find_floating_nets, find_short_circuits, analyze_connectivity

### `circuit_synth/kicad/logging_integration.py`
- **Functions**: 20
- **Functions list**: __init__, __init__, log_schematic_generation, log_schematic_generation, log_pcb_generation, log_pcb_generation, log_component_placement, log_component_placement, log_kicad_error, log_kicad_warning, operation_context, log_symbol_lookup, log_collision_detection, log_routing_progress, log_file_generation, log_validation_result, log_performance_bottleneck, _get_memory_usage, add_metric, log_progress

### `circuit_synth/kicad/sch_api/component_search.py`
- **Functions**: 20
- **Functions list**: __init__, _build_indices, get_statistics, find_by_reference, find_by_reference_pattern, find_by_value, find_by_property, find_by_footprint, find_by_lib_id, find_unconnected_components, find_by_criteria, find_by_custom_filter, group_by_type, group_by_value, group_by_lib_id, find_duplicates, find_in_area, find_nearest, _has_unconnected_pins, _get_reference_prefix

### `circuit_synth/kicad_api/schematic/connection_tracer.py`
- **Functions**: 20
- **Functions list**: __init__, __init__, trace_net, _points_equal, __hash__, __hash__, add_node, add_node, add_edge, add_edge, get_node_at, find_path, _build_connection_graph, _get_or_create_node, find_all_connections, get_net_endpoints, find_path_between_pins, find_floating_nets, find_short_circuits, analyze_connectivity

### `circuit_synth/kicad/sch_api/placement_engine.py`
- **Functions**: 19
- **Functions list**: __init__, snap_to_grid, expand, contains_point, intersects, find_next_position, check_collision, _update_state, _determine_strategy, _edge_placement, _grid_placement, _contextual_placement, _get_type_based_y_position, _find_nearest_free_position, _create_bounding_box, _get_component_prefix, _get_prefix_from_lib_id, _has_related_components, _find_related_components

### `circuit_synth/tools/init_existing_project.py`
- **Functions**: 19
- **Functions list**: main, find_kicad_project, validate_kicad_project, check_for_existing_circuit_synth, create_backup, setup_circuit_synth_in_place, copy_claude_setup, convert_kicad_to_circuit_synth, _collect_all_subcircuits_recursive, map_subcircuit_to_target_name, generate_hierarchical_circuit_synth_code, update_esp32_with_embedded_circuits, generate_subcircuit_code, generate_hierarchical_main_code, generate_circuit_synth_code, create_basic_template, create_project_files, _recursive_collect, sanitize_net_name

### `circuit_synth/core/defensive_logging.py`
- **Functions**: 18
- **Functions list**: __init__, get_defensive_logger, log_all_performance_summaries, rust_failure_rate, avg_rust_time, avg_python_time, performance_improvement, is_rust_available, log_operation_start, log_python_success, log_rust_success, log_rust_fallback, log_file_validation, get_performance_summary, log_performance_summary, defensive_operation, _calculate_size, _calculate_checksum

### `circuit_synth/pcb/footprint_library.py`
- **Functions**: 18
- **Functions list**: __init__, list_libraries, get_footprint, search_footprints, get_footprint_cache, footprint_type, is_smd, is_tht, is_mixed, _discover_system_libraries, _load_or_build_index, _build_index, _extract_basic_info, _save_index, get_footprint_data, _sexp_to_dict, refresh_cache, score

### `circuit_synth/kicad_api/pcb/footprint_library.py`
- **Functions**: 18
- **Functions list**: __init__, list_libraries, get_footprint, search_footprints, get_footprint_cache, footprint_type, is_smd, is_tht, is_mixed, _discover_system_libraries, _load_or_build_index, _build_index, _extract_basic_info, _save_index, get_footprint_data, _sexp_to_dict, refresh_cache, score

### `circuit_synth/schematic/net_discovery.py`
- **Functions**: 17
- **Functions list**: __init__, __init__, get_net_statistics, find_floating_nets, is_valid, get_member_name, discover_all_nets, _create_net_info, _is_power_net, _is_ground_net, _is_bus_net, merge_net_aliases, identify_bus_nets, analyze_net_connectivity, suggest_net_names, discover_hierarchical_nets, trace_hierarchical_net

### `circuit_synth/schematic/component_manager.py`
- **Functions**: 17
- **Functions list**: __init__, _generate_uuid, _snap_to_grid, _build_component_index, add_component, remove_component, update_component, find_component, list_components, find_components_by_value, find_components_by_library, move_component, clone_component, validate_schematic, _generate_reference, get_component, get_bounding_box

### `circuit_synth/memory_bank/circuit_diff.py`
- **Functions**: 17
- **Functions list**: __init__, __post_init__, __post_init__, _get_commit_message, format_diff_for_memory_bank, has_significant_changes, analyze_commit_changes, _analyze_kicad_file_changes, _analyze_python_file_changes, _compare_circuits, _simple_diff_analysis, _analyze_python_components, _analyze_python_nets, _get_changed_files, _get_file_content, cache_circuit_state, get_cached_circuit_state

### `circuit_synth/kicad_api/schematic/net_discovery.py`
- **Functions**: 17
- **Functions list**: __init__, __init__, get_net_statistics, find_floating_nets, is_valid, get_member_name, discover_all_nets, _create_net_info, _is_power_net, _is_ground_net, _is_bus_net, merge_net_aliases, identify_bus_nets, analyze_net_connectivity, suggest_net_names, discover_hierarchical_nets, trace_hierarchical_net

### `circuit_synth/kicad_api/schematic/component_manager.py`
- **Functions**: 17
- **Functions list**: __init__, _generate_uuid, _snap_to_grid, _build_component_index, add_component, remove_component, update_component, find_component, list_components, find_components_by_value, find_components_by_library, move_component, clone_component, validate_schematic, _generate_reference, get_component, get_bounding_box

### `circuit_synth/kicad_api/pcb/routing/dsn_exporter.py`
- **Functions**: 17
- **Functions list**: __init__, _calculate_footprint_bbox, export_pcb_to_dsn, export, _extract_board_outline, _extract_layers, _extract_components, _extract_nets, _get_pad_net, _rotate_point, _convert_pad_shape, _generate_dsn, _add_padstack_definitions, _add_footprint_definitions, _get_footprint_id, _sanitize_net_name, _get_kicad_version

### `circuit_synth/pcb/routing/dsn_exporter.py`
- **Functions**: 17
- **Functions list**: __init__, _calculate_footprint_bbox, export_pcb_to_dsn, export, _extract_board_outline, _extract_layers, _extract_components, _extract_nets, _get_pad_net, _rotate_point, _convert_pad_shape, _generate_dsn, _add_padstack_definitions, _add_footprint_definitions, _get_footprint_id, _sanitize_net_name, _get_kicad_version

### `circuit_synth/component_info/microcontrollers/modm_device_search.py`
- **Functions**: 17
- **Functions list**: __init__, search_stm32, search_by_peripherals, print_mcu_result, _find_modm_devices_path, _load_modm_devices, search_mcus, _evaluate_device, _extract_memory_size, _parse_memory_value, _extract_memory_from_identifier, _extract_pin_count, _extract_peripherals, _calculate_availability_score, _find_kicad_components, get_available_families, get_family_series

### `circuit_synth/kicad_api/pcb/hierarchical_placement_v2.py`
- **Functions**: 16
- **Functions list**: __init__, place_components, _is_within_board, place, _group_by_hierarchy, _group_groups, _pack_group, _find_best_placement_point, _place_at_board_edge, _get_area, _is_locked, _set_position, _get_position, _get_item_polygon, _get_spacing, _get_combined_bbox_footprints

### `circuit_synth/kicad_api/pcb/hierarchical_placement.py`
- **Functions**: 16
- **Functions list**: __init__, place_components, place, _group_by_hierarchy, _group_groups, _pack_group, _find_best_placement_point, _get_area, _is_locked, _get_spacing, _set_bottom_left, _get_bbox, _set_center, _touches, _get_combined_bbox, _bbox_within_board

### `circuit_synth/kicad_api/pcb/routing/ses_importer.py`
- **Functions**: 16
- **Functions list**: __init__, __init__, add_wire, parse, add_via, import_ses_to_pcb, _parse_session, _parse_resolution, _parse_routes, _parse_network_routes, _parse_vias, import_routing, _build_net_map, _remove_existing_routing, _import_wires, _import_vias

### `circuit_synth/kicad_api/pcb/placement/hierarchical_placement_v2.py`
- **Functions**: 16
- **Functions list**: __init__, place_components, _is_within_board, place, _group_by_hierarchy, _group_groups, _pack_group, _find_best_placement_point, _place_at_board_edge, _get_area, _is_locked, _set_position, _get_position, _get_item_polygon, _get_spacing, _get_combined_bbox_footprints

### `circuit_synth/kicad_api/pcb/placement/hierarchical_placement.py`
- **Functions**: 16
- **Functions list**: __init__, place_components, place, _group_by_hierarchy, _group_groups, _pack_group, _find_best_placement_point, _get_area, _is_locked, _get_spacing, _set_bottom_left, _get_bbox, _set_center, _touches, _get_combined_bbox, _bbox_within_board

### `circuit_synth/pcb/routing/ses_importer.py`
- **Functions**: 16
- **Functions list**: __init__, __init__, add_wire, parse, add_via, import_ses_to_pcb, _parse_session, _parse_resolution, _parse_routes, _parse_network_routes, _parse_vias, import_routing, _build_net_map, _remove_existing_routing, _import_wires, _import_vias

### `circuit_synth/pcb/placement/hierarchical_placement_v2.py`
- **Functions**: 16
- **Functions list**: __init__, place_components, _is_within_board, place, _group_by_hierarchy, _group_groups, _pack_group, _find_best_placement_point, _place_at_board_edge, _get_area, _is_locked, _set_position, _get_position, _get_item_polygon, _get_spacing, _get_combined_bbox_footprints

### `circuit_synth/pcb/placement/hierarchical_placement.py`
- **Functions**: 16
- **Functions list**: __init__, place_components, place, _group_by_hierarchy, _group_groups, _pack_group, _find_best_placement_point, _get_area, _is_locked, _get_spacing, _set_bottom_left, _get_bbox, _set_center, _touches, _get_combined_bbox, _bbox_within_board

### `circuit_synth/schematic/wire_manager.py`
- **Functions**: 15
- **Functions list**: __init__, _get_component_pins, _get_pin_position, add_connection, _build_wire_database, _build_pin_connections, _find_wires_at_point, _points_equal, find_wires_for_pin, remove_pin_connections, add_wire_between_points, route_wire, _manhattan_route, find_or_create_junction, get_net_at_point

### `circuit_synth/schematic/synchronizer.py`
- **Functions**: 15
- **Functions list**: __init__, to_dict, _load_schematic, _load_sheets_recursively, sync_with_circuit, _extract_circuit_components, _extract_pin_info, _match_components, _process_matches, _needs_update, _process_unmatched, _add_component, _determine_library_id, _save_schematic, get_all_components

### `circuit_synth/tools/kicad_parser.py`
- **Functions**: 15
- **Functions list**: __init__, _find_root_schematic, generate_netlist, parse_circuits, _analyze_hierarchical_structure, _build_hierarchical_tree, _parse_sheet_instances, _extract_sheet_blocks, _extract_sheet_instance_blocks, _parse_sheet_block, _parse_sheet_instance_block, _parse_circuits_from_schematics, _parse_schematic_file, _extract_symbol_blocks, _parse_component_block

### `circuit_synth/core/pin.py`
- **Functions**: 15
- **Functions list**: __init__, __str__, to_dict, __eq__, from_string, can_connect_to, x, y, length, orientation, connected, connect_to_net, __iadd__, __repr__, __json__

### `circuit_synth/core/performance_profiler.py`
- **Functions**: 15
- **Functions list**: __init__, get_summary, decorator, decorator, wrapper, wrapper, get_profiler, profile_operation, profile, profile, print_performance_summary, quick_time, time_operation, timing_decorator, print_summary

### `circuit_synth/core/enhanced_netlist_exporter.py`
- **Functions**: 15
- **Functions list**: __init__, to_dict, export_netlist_with_analytics, export_netlist_with_analytics, _export_with_rust_backend, _export_with_python_backend, _count_components, _count_nets, _should_use_rust_backend, _should_optimize, _get_memory_usage_mb, _get_cpu_usage, _update_generation_stats, _log_netlist_analytics, get_generation_statistics

### `circuit_synth/core/component.py`
- **Functions**: 15
- **Functions list**: __init__, __str__, to_dict, __post_init__, __iter__, _validate_symbol, __getattr__, __setattr__, _validate_property, __call__, __mul__, __len__, from_dict, print_pin_names, get_symbol_data

### `circuit_synth/core/netlist_exporter.py`
- **Functions**: 15
- **Functions list**: __init__, to_dict, generate_text_netlist, generate_full_netlist, generate_json_netlist, to_flattened_list, generate_flattened_json_netlist, generate_kicad_netlist, generate_kicad_project, create_defensive_logger, convert_python_to_rust_format, generate_kicad_netlist_defensive, convert_json_to_netlist, collect_nets, print_circuit

### `circuit_synth/plugins/ai_design_bridge.py`
- **Functions**: 15
- **Functions list**: __init__, get_ai_design_bridge, create_ai_assisted_circuit, _get_plugin_path, _get_kicad_plugin_directory, install_plugin, is_plugin_installed, get_plugin_status, generate_circuit_with_ai_assistance, _get_component_suggestions, _get_design_recommendations, _get_optimization_tips, _get_alternative_approaches, _generate_ai_guided_template, analyze_existing_circuit

### `circuit_synth/kicad/sch_api/component_manager.py`
- **Functions**: 15
- **Functions list**: __init__, get_all_components, add_component, remove_component, move_component, clone_component, validate_schematic, get_component, _validate_and_fetch_symbol, _create_component_instance, _set_component_properties, _create_pins, _get_symbol_size, _is_valid_property_name, update_component_property

### `circuit_synth/kicad/sch_editor/schematic_reader.py`
- **Functions**: 15
- **Functions list**: __init__, get_component, __post_init__, __iter__, _get_value, _parse_components, _parse_nets, read_file, _parse_lib_symbols, _parse_sheets, _parse_symbol_section, _parse_comp_section, _parse_hierarchical_labels, _get_libpart_pin_type, _find_sections

### `circuit_synth/kicad_api/schematic/wire_manager.py`
- **Functions**: 15
- **Functions list**: __init__, _get_component_pins, _get_pin_position, add_connection, _build_wire_database, _build_pin_connections, _find_wires_at_point, _points_equal, find_wires_for_pin, remove_pin_connections, add_wire_between_points, route_wire, _manhattan_route, find_or_create_junction, get_net_at_point

### `circuit_synth/kicad_api/schematic/synchronizer.py`
- **Functions**: 15
- **Functions list**: __init__, to_dict, _load_schematic, _load_sheets_recursively, sync_with_circuit, _extract_circuit_components, _extract_pin_info, _match_components, _process_matches, _needs_update, _process_unmatched, _add_component, _determine_library_id, _save_schematic, get_all_components

### `circuit_synth/schematic/label_manager.py`
- **Functions**: 14
- **Functions list**: __init__, _build_label_index, _generate_uuid, add_label, remove_label, update_label, find_labels_at_point, find_labels_by_text, auto_position_label, _find_wires_near_point, _is_horizontal_wire, get_label_by_uuid, get_labels_by_type, validate_hierarchical_labels

### `circuit_synth/schematic/connection_updater.py`
- **Functions**: 14
- **Functions list**: __init__, update_component_connections, _get_component_pins, _find_pin, _get_pin_position, _connect_pin_to_net, _find_or_create_net_point, _create_power_symbol, _create_net_label, _find_nearest_label, _needs_junction, update_net_connections, remove_floating_wires, optimize_wire_routing

### `circuit_synth/tools/python_to_kicad_sync.py`
- **Functions**: 14
- **Functions list**: __init__, __init__, main, sync, _create_backup, setup_logging, __post_init__, extract_circuit, _load_circuit_from_module, _load_circuit_from_execution, _validate_inputs, _apply_sync_changes, _generate_final_report, _save_report

### `circuit_synth/simulation/converter.py`
- **Functions**: 14
- **Functions list**: __init__, _add_component, convert, _map_nodes, _add_components, _add_resistor, _add_capacitor, _add_inductor, _add_diode, _add_opamp, _get_component_nodes, _convert_value_to_spice, _add_power_sources, _extract_voltage_from_net_name

### `circuit_synth/simulation/simulator.py`
- **Functions**: 14
- **Functions list**: __init__, __init__, list_components, get_voltage, get_current, list_nodes, list_nodes, plot, _convert_to_spice, operating_point, dc_analysis, ac_analysis, transient_analysis, get_netlist

### `circuit_synth/kicad_api/schematic/label_manager.py`
- **Functions**: 14
- **Functions list**: __init__, _build_label_index, _generate_uuid, add_label, remove_label, update_label, find_labels_at_point, find_labels_by_text, auto_position_label, _find_wires_near_point, _is_horizontal_wire, get_label_by_uuid, get_labels_by_type, validate_hierarchical_labels

### `circuit_synth/kicad_api/schematic/connection_updater.py`
- **Functions**: 14
- **Functions list**: __init__, update_component_connections, _get_component_pins, _find_pin, _get_pin_position, _connect_pin_to_net, _find_or_create_net_point, _create_power_symbol, _create_net_label, _find_nearest_label, _needs_junction, update_net_connections, remove_floating_wires, optimize_wire_routing

### `circuit_synth/kicad_api/pcb/connectivity_driven.py`
- **Functions**: 14
- **Functions list**: __init__, place, _build_connectivity_graph, _identify_critical_nets, _find_clusters, _calculate_placement_order, _find_best_position, _find_empty_spot, _find_closest_valid_position, _is_valid_position, _minimize_crossings, _count_crossings, _lines_intersect, ccw

### `circuit_synth/kicad_api/pcb/base.py`
- **Functions**: 14
- **Functions list**: __init__, place, bbox, set_bottom_left, area, is_locked, touches, reference, position, value, original_bbox, _calculate_bbox, hierarchical_path, move_to

### `circuit_synth/kicad_api/pcb/placement/connectivity_driven.py`
- **Functions**: 14
- **Functions list**: __init__, place, _build_connectivity_graph, _identify_critical_nets, _find_clusters, _calculate_placement_order, _find_best_position, _find_empty_spot, _find_closest_valid_position, _is_valid_position, _minimize_crossings, _count_crossings, _lines_intersect, ccw

### `circuit_synth/kicad_api/pcb/placement/base.py`
- **Functions**: 14
- **Functions list**: __init__, place, bbox, set_bottom_left, area, is_locked, touches, reference, position, value, original_bbox, _calculate_bbox, hierarchical_path, move_to

### `circuit_synth/pcb/placement/connectivity_driven.py`
- **Functions**: 14
- **Functions list**: __init__, place, _build_connectivity_graph, _identify_critical_nets, _find_clusters, _calculate_placement_order, _find_best_position, _find_empty_spot, _find_closest_valid_position, _is_valid_position, _minimize_crossings, _count_crossings, _lines_intersect, ccw

### `circuit_synth/pcb/placement/base.py`
- **Functions**: 14
- **Functions list**: __init__, place, bbox, set_bottom_left, area, is_locked, touches, reference, position, value, original_bbox, _calculate_bbox, hierarchical_path, move_to

### `circuit_synth/schematic/project_generator.py`
- **Functions**: 13
- **Functions list**: __init__, _generate_uuid, _generate_uuid, _get_pin_position, generate_from_circuit, _copy_blank_project_files, _generate_schematic, _generate_simple_design, _generate_hierarchical_design, _generate_root_with_unified_placement, _generate_top_sheet, _generate_sub_sheet, _get_library_id

### `circuit_synth/core/logging_minimal.py`
- **Functions**: 13
- **Functions list**: __init__, __init__, debug, info, warning, error, get_current_context, monitor_performance, performance_context, _format_kwargs, timer, __enter__, __exit__

### `circuit_synth/kicad/sch_api/reference_manager.py`
- **Functions**: 13
- **Functions list**: __init__, clear, get_statistics, _get_reference_prefix, add_existing_references, generate_reference, is_reference_available, release_reference, update_reference, get_next_reference, _split_reference, _is_valid_reference, _update_counter_from_reference

### `circuit_synth/kicad_api/schematic/project_generator.py`
- **Functions**: 13
- **Functions list**: __init__, _generate_uuid, _generate_uuid, _get_pin_position, generate_from_circuit, _copy_blank_project_files, _generate_schematic, _generate_simple_design, _generate_hierarchical_design, _generate_root_with_unified_placement, _generate_top_sheet, _generate_sub_sheet, _get_library_id

### `circuit_synth/kicad_api/pcb/force_directed.py`
- **Functions**: 13
- **Functions list**: __init__, add_connection, add_component, place, apply_force_directed_placement, reference, _run_placement, _calculate_center, _initialize_positions, _apply_spring_forces, _apply_repulsion_forces, _apply_gravity_forces, _update_positions

### `circuit_synth/kicad_api/pcb/placement/force_directed.py`
- **Functions**: 13
- **Functions list**: __init__, add_connection, add_component, place, apply_force_directed_placement, reference, _run_placement, _calculate_center, _initialize_positions, _apply_spring_forces, _apply_repulsion_forces, _apply_gravity_forces, _update_positions

### `circuit_synth/pcb/placement/force_directed.py`
- **Functions**: 13
- **Functions list**: __init__, add_connection, add_component, place, apply_force_directed_placement, reference, _run_placement, _calculate_center, _initialize_positions, _apply_spring_forces, _apply_repulsion_forces, _apply_gravity_forces, _update_positions

### `circuit_synth/schematic/sheet_utils.py`
- **Functions**: 13
- **Functions list**: calculate_sheet_size_from_content, suggest_pin_side, match_hierarchical_labels_to_pins, validate_sheet_filename, resolve_sheet_filepath, calculate_pin_spacing, group_pins_by_function, suggest_sheet_position, create_sheet_instance_name, _get_pin_side, estimate_sheet_complexity, generate_sheet_documentation, all_sides

### `circuit_synth/kicad_api/schematic/sheet_utils.py`
- **Functions**: 13
- **Functions list**: calculate_sheet_size_from_content, suggest_pin_side, match_hierarchical_labels_to_pins, validate_sheet_filename, resolve_sheet_filepath, calculate_pin_spacing, group_pins_by_function, suggest_sheet_position, create_sheet_instance_name, _get_pin_side, estimate_sheet_complexity, generate_sheet_documentation, all_sides

### `circuit_synth/schematic/text_manager.py`
- **Functions**: 12
- **Functions list**: __init__, _generate_uuid, _build_text_index, add_text, remove_text, update_text, find_text_at_point, find_text_by_content, align_texts, add_multiline_text, get_text_by_uuid, get_all_texts

### `circuit_synth/schematic/junction_manager.py`
- **Functions**: 12
- **Functions list**: __init__, _build_junction_index, update_junctions, _find_junction_points, _find_wire_crossings, _add_junction_at_position, _remove_junction_at_position, add_junction, remove_junction, get_junction_at, find_junctions_in_area, validate_junctions

### `circuit_synth/tools/llm_code_updater.py`
- **Functions**: 12
- **Functions list**: __init__, _sanitize_variable_name, _check_llm_availability, update_python_file, _llm_assisted_update, _prepare_llm_context, _fallback_update, _generate_hierarchical_code, _generate_subcircuit_function, _generate_main_circuit_function, _generate_flat_code, _generate_component_code

### `circuit_synth/pcb/kicad_cli.py`
- **Functions**: 12
- **Functions list**: __init__, __init__, get_version, run_drc, export_gerbers, export_drill, get_kicad_cli, total_issues, _find_kicad_cli, run_command, export_pos, export_svg

### `circuit_synth/manufacturing/jlcpcb/jlc_web_scraper.py`
- **Functions**: 12
- **Functions list**: __init__, search_components, search_jlc_components_web, get_component_availability_web, enhance_component_with_web_data, _parse_search_results, _extract_json_data, _parse_html_table, _parse_table_row, _extract_number, _get_demo_components, get_most_available_component

### `circuit_synth/kicad/sch_api/bulk_operations.py`
- **Functions**: 12
- **Functions list**: __init__, move_components, align_components, update_property_bulk, distribute_evenly, rotate_group, mirror_group, _calculate_group_bounds, _align_horizontal, _align_vertical, _align_grid, _rearrange_components

### `circuit_synth/kicad/sch_sync/schematic_updater.py`
- **Functions**: 12
- **Functions list**: __init__, _add_component, save_schematic, create_component_updates_from_sync_report, apply_updates, _modify_component, _remove_component, _create_schematic_symbol, _create_component_pins, _find_safe_placement, _align_to_grid, _add_hierarchical_labels

### `circuit_synth/kicad/sch_gen/circuit_loader.py`
- **Functions**: 12
- **Functions list**: __init__, __init__, __init__, add_component, __repr__, __repr__, __repr__, add_net, load_circuit_hierarchy, _parse_circuit, _circuits_match, assign_subcircuit_instance_labels

### `circuit_synth/kicad/sch_gen/connection_analyzer.py`
- **Functions**: 12
- **Functions list**: __init__, _is_power_net, get_connected_components, analyze_circuit, _identify_groups, get_connection_count, get_connection_strength, get_component_group, get_placement_order, calculate_wire_length, find, union

### `circuit_synth/kicad_api/schematic/text_manager.py`
- **Functions**: 12
- **Functions list**: __init__, _generate_uuid, _build_text_index, add_text, remove_text, update_text, find_text_at_point, find_text_by_content, align_texts, add_multiline_text, get_text_by_uuid, get_all_texts

### `circuit_synth/kicad_api/schematic/junction_manager.py`
- **Functions**: 12
- **Functions list**: __init__, _build_junction_index, update_junctions, _find_junction_points, _find_wire_crossings, _add_junction_at_position, _remove_junction_at_position, add_junction, remove_junction, get_junction_at, find_junctions_in_area, validate_junctions

### `circuit_synth/kicad_api/pcb/kicad_cli.py`
- **Functions**: 12
- **Functions list**: __init__, __init__, get_version, run_drc, export_gerbers, export_drill, get_kicad_cli, total_issues, _find_kicad_cli, run_command, export_pos, export_svg

### `circuit_synth/claude_integration/agents/contributor_agent.py`
- **Functions**: 12
- **Functions list**: __init__, get_capabilities, get_system_prompt, get_tools, execute_tool, _search_codebase, _lookup_documentation, _check_rust_module_status, _run_tests, _check_branch_status, _find_examples, get_metadata

### `circuit_synth/core/annotations.py`
- **Functions**: 12
- **Functions list**: add_text, to_dict, to_dict, to_dict, __post_init__, __post_init__, __post_init__, add_text_box, add_table, rectangle, circle, line

### `circuit_synth/kicad/kicad_symbol_parser.py`
- **Functions**: 12
- **Functions list**: decorator, quick_time, _parse_symbol_body, _parse_subsymbol, _parse_pin, _parse_graphic_element, parse_kicad_sym_file, _resolve_extends_in_library, _resolve_symbol_extends, _merge_parent_into_child, _flatten_symbol, _key

### `circuit_synth/schematic/wire_router.py`
- **Functions**: 11
- **Functions list**: __init__, route_direct, route_manhattan, route_diagonal, route_smart, route_bus, _snap_to_grid, _path_intersects_obstacles, _line_intersects_rect, optimize_path, _point_on_line

### `circuit_synth/core/rust_integration.py`
- **Functions**: 11
- **Functions list**: __init__, decorator, wrapper, rust_accelerated, get_acceleration_status, generate_component_sexp, create_symbol_cache, create_placement_engine, _detect_rust_modules, get_rust_function, has_rust_module

### `circuit_synth/core/kicad_validator.py`
- **Functions**: 11
- **Functions list**: __init__, main, validate_kicad_installation, require_kicad, require_kicad, get_kicad_paths, _get_kicad_paths, validate_kicad_cli, validate_kicad_libraries, validate_full_installation, _generate_installation_guide

### `circuit_synth/kicad/netlist_service.py`
- **Functions**: 11
- **Functions list**: __init__, __init__, __init__, __init__, generate_netlist, collect_from_circuit, create_netlist_service, load_circuit_data, _flatten_hierarchical_data, reconstruct_circuit, write_netlist

### `circuit_synth/kicad/project_notes.py`
- **Functions**: 11
- **Functions list**: __init__, _is_kicad_project, _get_project_name, ensure_notes_folder, _update_config, save_datasheet, get_datasheet_path, save_analysis_result, get_analysis_history, add_user_note, export_cache_summary

### `circuit_synth/pcb/ratsnest_generator.py`
- **Functions**: 11
- **Functions list**: __init__, _generate_uuid, generate_pcb_ratsnest, extract_pad_info, calculate_distance, generate_minimum_spanning_tree, generate_star_topology, generate_ratsnest, generate_kicad_ratsnest_elements, add_ratsnest_to_pcb, export_ratsnest_report

### `circuit_synth/memory_bank/context.py`
- **Functions**: 11
- **Functions list**: __init__, get_current_context, switch_board, get_current_board, get_current_memory_bank_path, list_available_boards, get_context_status, clear_context, _create_basic_claude_config, auto_detect_board, ensure_context

### `circuit_synth/manufacturing/jlcpcb/cache.py`
- **Functions**: 11
- **Functions list**: __init__, get_jlcpcb_cache, cached_jlcpcb_search, _get_cache_key, _get_cache_file, _is_cache_valid, get, set, clear_expired, clear_all, get_cache_info

### `circuit_synth/kicad_api/schematic/wire_router.py`
- **Functions**: 11
- **Functions list**: __init__, route_direct, route_manhattan, route_diagonal, route_smart, route_bus, _snap_to_grid, _path_intersects_obstacles, _line_intersects_rect, optimize_path, _point_on_line

### `circuit_synth/kicad_api/pcb/grouping.py`
- **Functions**: 11
- **Functions list**: __init__, group_by_hierarchy, group_groups, bbox, hierarchical_level, hierarchical_level, move, set_bottom_left, area, is_locked, touches

### `circuit_synth/kicad_api/pcb/placement/grouping.py`
- **Functions**: 11
- **Functions list**: __init__, group_by_hierarchy, group_groups, bbox, hierarchical_level, hierarchical_level, move, set_bottom_left, area, is_locked, touches

### `circuit_synth/pcb/placement/grouping.py`
- **Functions**: 11
- **Functions list**: __init__, group_by_hierarchy, group_groups, bbox, hierarchical_level, hierarchical_level, move, set_bottom_left, area, is_locked, touches

### `circuit_synth/kicad_api/pcb/bbox.py`
- **Functions**: 11
- **Functions list**: width, height, center, intersects, area, inflate, merge, top_left, bottom_right, bottom_left, from_points

### `circuit_synth/kicad_api/pcb/placement/bbox.py`
- **Functions**: 11
- **Functions list**: width, height, center, intersects, area, inflate, merge, top_left, bottom_right, bottom_left, from_points

### `circuit_synth/pcb/placement/bbox.py`
- **Functions**: 11
- **Functions list**: width, height, center, intersects, area, inflate, merge, top_left, bottom_right, bottom_left, from_points

### `circuit_synth/tools/preparse_kicad_symbols.py`
- **Functions**: 11
- **Functions list**: main, _get_default_kicad_symbol_path, extract_symbol_names, find_kicad_symbol_files, build_symbol_index, preparse_symbols, preparse_specific_libraries, show_cache_status, clear_cache, preparse_symbols_legacy, validate_symbol_paths

### `circuit_synth/core/reference_manager.py`
- **Functions**: 10
- **Functions list**: __init__, clear, validate_reference, register_reference, set_parent, get_root_manager, get_all_used_references, set_initial_counters, generate_next_reference, generate_next_unnamed_net_name

### `circuit_synth/component_placement/geometry.py`
- **Functions**: 10
- **Functions list**: __init__, get_bounding_box, create_geometry_handler, _get_default_dimensions, _get_default_dimensions, _get_default_dimensions, _setup_pin_locations, _setup_pin_locations, _setup_pin_locations, get_pin_location

### `circuit_synth/kicad/sch_api/sync_integration.py`
- **Functions**: 10
- **Functions list**: __init__, _apply_sync_changes, create_sync_integration, setup_from_project, sync_with_circuit_using_api, _add_component_from_sync, _modify_component_from_sync, _remove_component_from_sync, _find_schematic_file, demonstrate_api_features

### `circuit_synth/kicad/sch_editor/schematic_exporter.py`
- **Functions**: 10
- **Functions list**: __init__, __init__, export_file, _validate_schematic, write_hierarchical_label, write_component, write_net, write_sheet, _ensure_required_sections, _format_schematic

### `circuit_synth/kicad/sch_gen/integrated_reference_manager.py`
- **Functions**: 10
- **Functions list**: __init__, __init__, reset, integrate_into_schematic_writer_example, test_integrated_reference_generation, get_reference_for_component, get_reference_for_symbol, enable_reassignment_mode, should_reassign, get_next_reference_for_type

### `circuit_synth/kicad/sch_gen/data_structures.py`
- **Functions**: 10
- **Functions list**: __init__, __init__, __init__, __init__, add_component, __repr__, __repr__, __repr__, __repr__, add_net

### `circuit_synth/kicad_api/pcb/connection_centric.py`
- **Functions**: 10
- **Functions list**: __init__, _find_edge_position, _find_nearest_valid_position, place, _is_valid_position, _analyze_connections, _get_subcircuit, _group_by_subcircuit, _place_subcircuit, _find_optimal_position

### `circuit_synth/kicad_api/pcb/routing/freerouting_runner.py`
- **Functions**: 10
- **Functions list**: __init__, route_pcb, _find_freerouting_jar, _check_java, _parse_progress, _monitor_output, _process_line, route, stop, get_progress

### `circuit_synth/kicad_api/pcb/placement/connection_centric.py`
- **Functions**: 10
- **Functions list**: __init__, _find_edge_position, _find_nearest_valid_position, place, _is_valid_position, _analyze_connections, _get_subcircuit, _group_by_subcircuit, _place_subcircuit, _find_optimal_position

### `circuit_synth/pcb/routing/freerouting_runner.py`
- **Functions**: 10
- **Functions list**: __init__, route_pcb, _find_freerouting_jar, _check_java, _parse_progress, _monitor_output, _process_line, route, stop, get_progress

### `circuit_synth/pcb/placement/connection_centric.py`
- **Functions**: 10
- **Functions list**: __init__, _find_edge_position, _find_nearest_valid_position, place, _is_valid_position, _analyze_connections, _get_subcircuit, _group_by_subcircuit, _place_subcircuit, _find_optimal_position

### `circuit_synth/schematic/connection_utils.py`
- **Functions**: 10
- **Functions list**: snap_to_grid, points_equal, distance_between_points, apply_transformation, get_pin_position, find_pin_by_name, segment_intersection, point_on_segment, get_wire_segments, simplify_points

### `circuit_synth/kicad_api/schematic/connection_utils.py`
- **Functions**: 10
- **Functions list**: snap_to_grid, points_equal, distance_between_points, apply_transformation, get_pin_position, find_pin_by_name, segment_intersection, point_on_segment, get_wire_segments, simplify_points

### `circuit_synth/data/examples/example_kicad_project.py`
- **Functions**: 10
- **Functions list**: decorator, wrapper, timed_function, regulator, resistor_divider, usb_port, imu, debug_header, esp32, root

### `circuit_synth/claude_integration/agent_registry.py`
- **Functions**: 9
- **Functions list**: __init__, main, decorator, register_agent, get_registered_agents, create_agent_instance, get_circuit_agents, register_circuit_agents, to_markdown

### `circuit_synth/manufacturing/jlcpcb/jlc_parts_lookup.py`
- **Functions**: 9
- **Functions list**: __init__, search_components, recommend_jlc_component, get_component_alternatives, enhance_component_with_jlc_data, _calculate_manufacturability_score, _obtain_token, get_component_page, get_most_available_part

### `circuit_synth/kicad/pcb_gen/pcb_generator.py`
- **Functions**: 9
- **Functions list**: __init__, generate_pcb, _calculate_initial_board_size, _extract_components_from_schematics, _extract_connections_from_schematics, _extract_hierarchical_path, _update_project_file, _apply_netlist_to_pcb, _auto_route_pcb

### `circuit_synth/kicad_api/pcb/spiral_placement.py`
- **Functions**: 9
- **Functions list**: __init__, _build_connection_graph, place_components, _calculate_ideal_position, _find_nearest_valid_position, _is_position_valid, _get_inflated_bbox, _is_within_board, _boxes_overlap

### `circuit_synth/kicad_api/pcb/spiral_hierarchical_placement.py`
- **Functions**: 9
- **Functions list**: __init__, _calculate_ideal_position, place, _is_valid_position, _find_best_placement_point, _build_connection_map, _spiral_search, _get_reference, _set_bottom_left

### `circuit_synth/kicad_api/pcb/placement/spiral_placement.py`
- **Functions**: 9
- **Functions list**: __init__, _build_connection_graph, place_components, _calculate_ideal_position, _find_nearest_valid_position, _is_position_valid, _get_inflated_bbox, _is_within_board, _boxes_overlap

### `circuit_synth/kicad_api/pcb/placement/spiral_hierarchical_placement.py`
- **Functions**: 9
- **Functions list**: __init__, _calculate_ideal_position, place, _is_valid_position, _find_best_placement_point, _build_connection_map, _spiral_search, _get_reference, _set_bottom_left

### `circuit_synth/pcb/placement/spiral_placement.py`
- **Functions**: 9
- **Functions list**: __init__, _build_connection_graph, place_components, _calculate_ideal_position, _find_nearest_valid_position, _is_position_valid, _get_inflated_bbox, _is_within_board, _boxes_overlap

### `circuit_synth/pcb/placement/spiral_hierarchical_placement.py`
- **Functions**: 9
- **Functions list**: __init__, _calculate_ideal_position, place, _is_valid_position, _find_best_placement_point, _build_connection_map, _spiral_search, _get_reference, _set_bottom_left

### `circuit_synth/kicad/rust_accelerated_symbol_cache.py`
- **Functions**: 9
- **Functions list**: get_all_symbols, get_symbol_data, __new__, get_symbol_data_by_name, find_symbol_library, get_all_libraries, _initialize, is_rust_accelerated, get_performance_info

### `circuit_synth/component_placement/force_directed_layout.py`
- **Functions**: 8
- **Functions list**: __init__, scale, __add__, magnitude, _calculate_attractive_force, _calculate_repulsive_force, _apply_forces, layout

### `circuit_synth/kicad/net_name_generator.py`
- **Functions**: 8
- **Functions list**: __init__, generate_net_name, resolve_bus_names, _validate_bus_inputs, _normalize_bus_name, _extract_existing_index, _get_next_number, apply_power_net_rules

### `circuit_synth/memory_bank/git_integration.py`
- **Functions**: 8
- **Functions list**: __init__, update_memory_bank_from_commit, get_commit_info, is_git_repository, get_current_commit_hash, get_recent_commits, install_post_commit_hook, remove_post_commit_hook

### `circuit_synth/kicad/sch_gen/integrated_placement.py`
- **Functions**: 8
- **Functions list**: __init__, __init__, integrate_into_collision_manager, test_integrated_placement, place_components_with_strategy, _get_component_type, _get_component_id, _create_placed_component

### `circuit_synth/kicad/sch_gen/connection_aware_collision_manager.py`
- **Functions**: 8
- **Functions list**: __init__, analyze_connections, place_component_connection_aware, _calculate_ideal_position, _find_nearest_valid_position, _try_position, get_placement_metrics, reset_placement

### `circuit_synth/schematic/label_utils.py`
- **Functions**: 8
- **Functions list**: suggest_label_position, get_wire_direction_at_point, format_net_name, validate_hierarchical_label_name, group_labels_by_net, find_connected_labels, suggest_label_for_component_pin, calculate_text_bounds

### `circuit_synth/kicad_api/schematic/label_utils.py`
- **Functions**: 8
- **Functions list**: suggest_label_position, get_wire_direction_at_point, format_net_name, validate_hierarchical_label_name, group_labels_by_net, find_connected_labels, suggest_label_for_component_pin, calculate_text_bounds

### `circuit_synth/tools/init_pcb.py`
- **Functions**: 8
- **Functions list**: main, find_kicad_files, organize_kicad_files, create_circuit_synth_structure, _create_simple_template, create_memory_bank, create_claude_agent, create_readme

### `circuit_synth/tools/setup_claude.py`
- **Functions**: 8
- **Functions list**: main, get_package_data_dir, check_claude_availability, create_claude_config, copy_examples, copy_memory_bank, copy_claude_md, detect_environment

### `circuit_synth/memory_bank/commands.py`
- **Functions**: 8
- **Functions list**: get_current_context, add_board, remove_memory_bank, switch_board, list_boards, init_memory_bank, get_memory_bank_status, search_memory_bank

### `circuit_synth/simulation/analysis.py`
- **Functions**: 8
- **Functions list**: is_sweep, get_total_points, get_num_points, dc_operating_point, dc_sweep, ac_frequency_response, transient_step_response, transient_pulse_response

### `circuit_synth/validation/simple_validator.py`
- **Functions**: 8
- **Functions list**: validate_and_improve_circuit, _check_circuit_code, _check_imports, _extract_imports, _check_circuit_structure, _check_runtime_execution, _apply_basic_fixes, get_circuit_design_context

### `circuit_synth/schematic/sync_strategies.py`
- **Functions**: 7
- **Functions list**: __init__, __init__, __init__, match_components, match_components, match_components, match_components

### `circuit_synth/component_placement/placement.py`
- **Functions**: 7
- **Functions list**: __init__, analyze_connectivity, __post_init__, _check_collision, _find_non_colliding_position, _determine_component_rotation, place_components

### `circuit_synth/kicad/sch_editor/schematic_comparer.py`
- **Functions**: 7
- **Functions list**: __init__, compare_with_circuit, _compare_components, _compare_component_properties, _compare_nets, _compare_net_nodes, _compare_sheets

### `circuit_synth/kicad/sch_gen/collision_detection.py`
- **Functions**: 7
- **Functions list**: __init__, __init__, intersects, __repr__, clear, add_bbox, _add_sheet_boundaries

### `circuit_synth/kicad/sch_gen/connection_aware_collision_manager_v2.py`
- **Functions**: 7
- **Functions list**: __init__, analyze_connections, place_component_connection_aware, get_placement_metrics, _calculate_ideal_position_and_rotation, _calculate_ideal_rotation, _is_better_position

### `circuit_synth/kicad/sch_gen/api_integration_plan.py`
- **Functions**: 7
- **Functions list**: __init__, integrate_into_collision_manager, integrate_into_schematic_writer, integrate_models_for_type_safety, integrate_reference_generation, integrate_placement_strategies, integrate_bounding_box_calculation

### `circuit_synth/kicad/sch_gen/kicad_formatter.py`
- **Functions**: 7
- **Functions list**: __init__, get_parser, format, format_kicad_schematic, _is_inline_construct, _format_inline_construct, _format_standard_list

### `circuit_synth/kicad_api/schematic/sync_strategies.py`
- **Functions**: 7
- **Functions list**: __init__, __init__, __init__, match_components, match_components, match_components, match_components

### `circuit_synth/schematic/geometry_utils.py`
- **Functions**: 7
- **Functions list**: get_actual_pin_position, transform_pin_to_world, get_pin_end_position, calculate_label_position, calculate_label_orientation, create_dynamic_hierarchical_label, get_pins_at_position

### `circuit_synth/kicad_api/schematic/geometry_utils.py`
- **Functions**: 7
- **Functions list**: get_actual_pin_position, transform_pin_to_world, get_pin_end_position, calculate_label_position, calculate_label_orientation, create_dynamic_hierarchical_label, get_pins_at_position

### `circuit_synth/tools/new_pcb.py`
- **Functions**: 7
- **Functions list**: get_template_content, _copy_claude_directory, copy_example_project_structure, _create_fallback_structure, main, copy_file_with_customization, copy_directory_recursive

### `circuit_synth/kicad_api/pcb/routing/install_freerouting.py`
- **Functions**: 7
- **Functions list**: main, get_platform_info, check_java, get_download_url, download_file, install_freerouting, download_progress

### `circuit_synth/pcb/routing/install_freerouting.py`
- **Functions**: 7
- **Functions list**: main, get_platform_info, check_java, get_download_url, download_file, install_freerouting, download_progress

### `circuit_synth/schematic/sheet_placement.py`
- **Functions**: 6
- **Functions list**: __init__, create_sheet_symbols, calculate_sheet_size, get_next_position, place_sheet, calculate_pin_positions

### `circuit_synth/schematic/symbol_geometry.py`
- **Functions**: 6
- **Functions list**: __init__, get_symbol_bounds, _calculate_symbol_bounds, _update_bounds_from_graphic_element, _get_default_bounds, calculate_text_width

### `circuit_synth/core/_logger.py`
- **Functions**: 6
- **Functions list**: __init__, log_netlist_analytics, debug, info, warning, error

### `circuit_synth/kicad/net_tracker.py`
- **Functions**: 6
- **Functions list**: __init__, analyze_net_drivers, track_net_usage, _get_driver_priority, get_net_info, detect_power_nets

### `circuit_synth/kicad/sch_api/exceptions.py`
- **Functions**: 6
- **Functions list**: __init__, __init__, __init__, __init__, __init__, __init__

### `circuit_synth/kicad/sch_api/component_operations.py`
- **Functions**: 6
- **Functions list**: __init__, _estimate_component_size, remove_component, move_component, clone_component, _increment_reference

### `circuit_synth/kicad/sch_sync/component_matcher.py`
- **Functions**: 6
- **Functions list**: __init__, match_components, _get_component_reference, _get_component_value, _get_component_footprint, _calculate_match_confidence

### `circuit_synth/kicad_api/schematic/sheet_placement.py`
- **Functions**: 6
- **Functions list**: __init__, create_sheet_symbols, calculate_sheet_size, get_next_position, place_sheet, calculate_pin_positions

### `circuit_synth/kicad_api/schematic/symbol_geometry.py`
- **Functions**: 6
- **Functions list**: __init__, get_symbol_bounds, _calculate_symbol_bounds, _update_bounds_from_graphic_element, _get_default_bounds, calculate_text_width

### `circuit_synth/kicad_api/pcb/spiral_placement_v2.py`
- **Functions**: 6
- **Functions list**: __init__, _build_connection_graph, place_components, _calculate_ideal_position, _find_nearest_valid_position, get_placement_info

### `circuit_synth/kicad_api/pcb/placement/spiral_placement_v2.py`
- **Functions**: 6
- **Functions list**: __init__, _build_connection_graph, place_components, _calculate_ideal_position, _find_nearest_valid_position, get_placement_info

### `circuit_synth/pcb/placement/spiral_placement_v2.py`
- **Functions**: 6
- **Functions list**: __init__, _build_connection_graph, place_components, _calculate_ideal_position, _find_nearest_valid_position, get_placement_info

### `circuit_synth/tools/circuit_creator_cli.py`
- **Functions**: 6
- **Functions list**: main, create_circuit_interactive, create_circuit_from_file, list_circuits_cli, use_circuit_cli, create_example_requirements_file

### `circuit_synth/validation/real_time_check.py`
- **Functions**: 6
- **Functions list**: main, extract_components_from_file, validate_component_symbols, check_net_connectivity, validate_circuit_functions, validate_circuit_file

### `circuit_synth/core/decorators.py`
- **Functions**: 6
- **Functions list**: get_current_circuit, set_current_circuit, circuit, enable_comments, _decorator, _wrapper

### `circuit_synth/kicad_api_minimal.py`
- **Functions**: 5
- **Functions list**: __init__, __init__, __init__, __init__, __init__

### `circuit_synth/schematic/sync_adapter.py`
- **Functions**: 5
- **Functions list**: __init__, sync_with_circuit, _find_schematic, _schematic_has_components, synchronize

### `circuit_synth/tools/kicad_to_python_sync.py`
- **Functions**: 5
- **Functions list**: __init__, main, _resolve_kicad_project_path, sync, _create_backup

### `circuit_synth/core/simple_pin_access.py`
- **Functions**: 5
- **Functions list**: __init__, __iadd__, __repr__, __getitem__, __setitem__

### `circuit_synth/claude_integration/hooks.py`
- **Functions**: 5
- **Functions list**: __init__, to_dict, get_circuit_hooks, create_claude_settings, setup_circuit_hooks

### `circuit_synth/claude_integration/enhanced_circuit_agent.py`
- **Functions**: 5
- **Functions list**: __init__, generate_validated_circuit, _generate_simple_example, _create_response, quick_validate

### `circuit_synth/kicad/sch_editor/schematic_editor.py`
- **Functions**: 5
- **Functions list**: __init__, add_component, remove_component, save, schematic_data

### `circuit_synth/kicad/sch_gen/collision_manager.py`
- **Functions**: 5
- **Functions list**: __init__, snap_to_grid, clear, place_symbol, register_existing_symbol

### `circuit_synth/kicad/sch_gen/hierarchical_aware_placement.py`
- **Functions**: 5
- **Functions list**: __init__, allocate_sheet_region, _find_available_space, get_sheet_offset, get_sheet_bounds

### `circuit_synth/kicad_api/schematic/sync_adapter.py`
- **Functions**: 5
- **Functions list**: __init__, sync_with_circuit, _find_schematic, _schematic_has_components, synchronize

### `circuit_synth/tools/ai_design_manager.py`
- **Functions**: 5
- **Functions list**: main, cmd_status, cmd_install, cmd_generate, cmd_analyze

### `circuit_synth/data/examples/jlc_component_finder_demo.py`
- **Functions**: 5
- **Functions list**: main, demo_single_component, demo_multiple_components, demo_passive_components, demo_connector_search

### `circuit_synth/tools/pcb_tracker_basic.py`
- **Functions**: 5
- **Functions list**: cli, init, log, list, install_hooks

### `circuit_synth/schematic/net_matcher.py`
- **Functions**: 4
- **Functions list**: __init__, match_by_connections, _get_component_nets, _calculate_net_similarity

### `circuit_synth/tools/kicad_netlist_parser.py`
- **Functions**: 4
- **Functions list**: __init__, parse_netlist, _parse_components_from_netlist, _parse_nets_from_netlist

### `circuit_synth/core/net.py`
- **Functions**: 4
- **Functions list**: __init__, __iadd__, __repr__, pins

### `circuit_synth/pcb/pcb_formatter.py`
- **Functions**: 4
- **Functions list**: __init__, format, _format_list, format_pcb

### `circuit_synth/claude_integration/commands.py`
- **Functions**: 4
- **Functions list**: __init__, to_markdown, get_circuit_commands, register_circuit_commands

### `circuit_synth/kicad_api/schematic/net_matcher.py`
- **Functions**: 4
- **Functions list**: __init__, match_by_connections, _get_component_nets, _calculate_net_similarity

### `circuit_synth/kicad_api/pcb/pcb_formatter.py`
- **Functions**: 4
- **Functions list**: __init__, format, _format_list, format_pcb

### `circuit_synth/kicad_api/pcb/routing/freerouting_docker.py`
- **Functions**: 4
- **Functions list**: __init__, route, route_pcb_docker, _check_docker

### `circuit_synth/pcb/routing/freerouting_docker.py`
- **Functions**: 4
- **Functions list**: __init__, route, route_pcb_docker, _check_docker

### `circuit_synth/stm32_search_helper.py`
- **Functions**: 4
- **Functions list**: detect_stm32_peripheral_query, find_stm32_with_peripherals, _format_stm32_recommendation, handle_stm32_peripheral_query

### `circuit_synth/kicad/sch_gen/symbol_geometry.py`
- **Functions**: 4
- **Functions list**: calculate_bounding_box, get_symbol_dimensions, _get_shape_bounds, _get_pin_bounds

### `circuit_synth/tools/preload_symbols.py`
- **Functions**: 4
- **Functions list**: main, _get_default_kicad_symbol_path, extract_symbol_names, preload_all_symbols

### `circuit_synth/data/tools/ci-setup/setup_ci_symbols.py`
- **Functions**: 4
- **Functions list**: main, download_file, get_ci_symbols_dir, verify_symbols

### `circuit_synth/pcb/types.py`
- **Functions**: 4
- **Functions list**: __repr__, get_library_id, get_property, set_property

### `circuit_synth/kicad_api/pcb/types.py`
- **Functions**: 4
- **Functions list**: __repr__, get_library_id, get_property, set_property

### `circuit_synth/kicad/sch_gen/shape_drawer.py`
- **Functions**: 4
- **Functions list**: rectangle_s_expr, polyline_s_expr, circle_s_expr, arc_s_expr

### `circuit_synth/component_placement/wire_routing.py`
- **Functions**: 3
- **Functions list**: __init__, route_net, sort_key

### `circuit_synth/tools/models.py`
- **Functions**: 3
- **Functions list**: to_dict, to_dict, to_dict

### `circuit_synth/core/rust_components.py`
- **Functions**: 3
- **Functions list**: create_rust_resistor, create_rust_capacitor, get_rust_component_status

### `circuit_synth/memory_bank/templates.py`
- **Functions**: 3
- **Functions list**: generate_claude_md, get_template, get_all_templates

### `circuit_synth/kicad_api/pcb/utils.py`
- **Functions**: 3
- **Functions list**: calculate_placement_bbox, _estimate_footprint_bbox, optimize_component_rotation

### `circuit_synth/kicad_api/pcb/placement/utils.py`
- **Functions**: 3
- **Functions list**: calculate_placement_bbox, _estimate_footprint_bbox, optimize_component_rotation

### `circuit_synth/pcb/placement/utils.py`
- **Functions**: 3
- **Functions list**: calculate_placement_bbox, _estimate_footprint_bbox, optimize_component_rotation

### `circuit_synth/kicad/sch_gen/hierarchy_manager.py`
- **Functions**: 2
- **Functions list**: __init__, build_hierarchy

### `circuit_synth/kicad_api/schematic/instance_utils.py`
- **Functions**: 2
- **Functions list**: add_symbol_instance, get_project_hierarchy_path

### `circuit_synth/io/json_loader.py`
- **Functions**: 2
- **Functions list**: load_circuit_from_json_file, load_circuit_from_dict

### `circuit_synth/kicad/symbol_lib_parser_manager.py`
- **Functions**: 2
- **Functions list**: get_parser, reset

### `circuit_synth/memory_bank/cli.py`
- **Functions**: 2
- **Functions list**: init_cli, remove_cli

### `circuit_synth/data/examples/reference_designs/reference_desgin2/python_generated_reference_design.py`
- **Functions**: 2
- **Functions list**: resistor_divider, resistor_divider2

### `circuit_synth/schematic/instance_utils.py`
- **Functions**: 1
- **Functions list**: add_symbol_instance

### `circuit_synth/scripts/enable_rust.py`
- **Functions**: 1
- **Functions list**: main

### `circuit_synth/data/templates/project/main.py`
- **Functions**: 1
- **Functions list**: main

### `circuit_synth/core/json_encoder.py`
- **Functions**: 1
- **Functions list**: default

### `circuit_synth/data/examples/reference_designs/reference_desgin1/python_generated_reference_design.py`
- **Functions**: 1
- **Functions list**: resistor_divider

### `circuit_synth/data/templates/example_project/circuit-synth/usb.py`
- **Functions**: 1
- **Functions list**: usb_port

### `circuit_synth/data/templates/example_project/circuit-synth/debug_header.py`
- **Functions**: 1
- **Functions list**: debug_header

### `circuit_synth/data/examples/agent-training/03_complete_stm32_development_board.py`
- **Functions**: 1
- **Functions list**: complete_stm32_development_board

### `circuit_synth/data/examples/agent-training/02_combined_usb_power_esp32.py`
- **Functions**: 1
- **Functions list**: usb_powered_esp32

### `circuit_synth/data/examples/agent-training/power/01_basic_ldo_3v3.py`
- **Functions**: 1
- **Functions list**: basic_ldo_3v3

### `circuit_synth/data/examples/agent-training/microcontrollers/01_esp32_minimal.py`
- **Functions**: 1
- **Functions list**: esp32_minimal

### `circuit_synth/data/examples/agent-training/microcontrollers/02_stm32_with_crystal.py`
- **Functions**: 1
- **Functions list**: stm32_reference_design

### `circuit_synth/data/examples/agent-training/interfaces/01_basic_usb_c.py`
- **Functions**: 1
- **Functions list**: basic_usb_c_power

### `circuit_synth/data/templates/example_project/circuit-synth/power_supply.py`
- **Functions**: 1
- **Functions list**: power_supply

### `circuit_synth/data/templates/example_project/circuit-synth/led_blinker.py`
- **Functions**: 1
- **Functions list**: led_blinker

### `circuit_synth/data/templates/example_project/circuit-synth/esp32c6.py`
- **Functions**: 1
- **Functions list**: esp32c6

### `circuit_synth/data/templates/example_project/circuit-synth/main.py`
- **Functions**: 1
- **Functions list**: main_circuit

## 📋 Dead Functions by Module

Functions that exist but were never called during the test run:

### `circuit_synth/`

#### `kicad_api_minimal.py`
**Dead functions (5)**: __init__, __init__, __init__, __init__, __init__

#### `stm32_search_helper.py`
**Dead functions (4)**: _format_stm32_recommendation, detect_stm32_peripheral_query, find_stm32_with_peripherals, handle_stm32_peripheral_query

### `circuit_synth/claude_integration/`

#### `agent_registry.py`
**Dead functions (8)**: __init__, create_agent_instance, get_circuit_agents, get_registered_agents, main, register_agent, register_circuit_agents, to_markdown

#### `enhanced_circuit_agent.py`
**Dead functions (5)**: __init__, _create_response, _generate_simple_example, generate_validated_circuit, quick_validate

#### `hooks.py`
**Dead functions (4)**: __init__, create_claude_settings, get_circuit_hooks, setup_circuit_hooks

#### `commands.py`
**Dead functions (4)**: __init__, get_circuit_commands, register_circuit_commands, to_markdown

### `circuit_synth/claude_integration/agents/`

#### `contributor_agent.py`
**Dead functions (12)**: __init__, _check_branch_status, _check_rust_module_status, _find_examples, _lookup_documentation, _run_tests, _search_codebase, execute_tool, get_capabilities, get_metadata, get_system_prompt, get_tools

### `circuit_synth/codegen/`

#### `json_to_python_project.py`
**Dead functions (34)**: _clear_all_reference_managers, _generate_circuit_py_for_circuits_folder, _make_common_varname, _phase1_load_circuit, _phase2_rename_circuits, _phase3_find_repeated_components, _phase3_write_common_parts, _phase4_assign_nets_to_circuits, _phase4_compute_net_owners_lca, _phase4_gather_net_usage, _phase5_unify_net_names, _phase6_compute_imported_nets_with_descendants, _phase7_write_all_circuits_organized, _phase8_generate_main_py, _sanitize_for_param, _scan_json_references, _write_all_circuits_standard, circuit_synth_json_to_python_project, clear_circuit, dfs, find_lca, gather, gather, gather, get_ancestry, initall, is_ancestor, main, rec, rename, sanitize, sanitize, scan_data, walk

### `circuit_synth/component_info/microcontrollers/`

#### `modm_device_search.py`
**Dead functions (17)**: __init__, _calculate_availability_score, _evaluate_device, _extract_memory_from_identifier, _extract_memory_size, _extract_peripherals, _extract_pin_count, _find_kicad_components, _find_modm_devices_path, _load_modm_devices, _parse_memory_value, get_available_families, get_family_series, print_mcu_result, search_by_peripherals, search_mcus, search_stm32

### `circuit_synth/component_placement/`

#### `geometry.py`
**Dead functions (10)**: __init__, _get_default_dimensions, _get_default_dimensions, _get_default_dimensions, _setup_pin_locations, _setup_pin_locations, _setup_pin_locations, create_geometry_handler, get_bounding_box, get_pin_location

#### `force_directed_layout.py`
**Dead functions (8)**: __add__, __init__, _apply_forces, _calculate_attractive_force, _calculate_repulsive_force, layout, magnitude, scale

#### `placement.py`
**Dead functions (7)**: __init__, __post_init__, _check_collision, _determine_component_rotation, _find_non_colliding_position, analyze_connectivity, place_components

#### `wire_routing.py`
**Dead functions (3)**: __init__, route_net, sort_key

### `circuit_synth/core/`

#### `dependency_injection.py`
**Dead functions (25)**: __init__, __init__, _create_instance, clear, configure_default_dependencies, get_registrations, get_service, inject, is_registered, is_registered, is_registered, register, register, register_factory, register_factory, register_instance, register_instance, register_singleton, register_singleton, register_transient, register_transient, resolve, resolve, resolve, set_container

#### `types.py`
**Dead functions (21)**: __getitem__, __iter__, __post_init__, _point_on_segment, add_junction, add_node, add_rectangle, add_wire, center, contains_point, contains_point, get_all_elements, get_bounding_box, get_component, get_endpoints, height, remove_component, to_tuple, total_count, uuid, width

#### `defensive_logging.py`
**Dead functions (18)**: __init__, _calculate_checksum, _calculate_size, avg_python_time, avg_rust_time, defensive_operation, get_defensive_logger, get_performance_summary, is_rust_available, log_all_performance_summaries, log_file_validation, log_operation_start, log_performance_summary, log_python_success, log_rust_fallback, log_rust_success, performance_improvement, rust_failure_rate

#### `s_expression.py`
**Dead functions (17)**: __init__, _find_all_elements, _find_element, _get_symbol_name, _is_sexp_list, _junction_to_sexp, _parse_junction, _parse_label, _parse_sheet, _parse_sheet_pin, _parse_symbol, _parse_title_block, _parse_wire, _rectangle_to_sexp, _wire_to_sexp, parse_file, to_schematic

#### `symbol_cache.py`
**Dead functions (14)**: __init__, _build_complete_index, _deserialize_symbol, _extract_symbol_names_fast, _find_library_file, _load_symbol, _save_cache, _serialize_symbol, add_library_path, bounding_box, get_all_symbols, get_reference_prefix, get_symbol_by_name, list_libraries

#### `enhanced_netlist_exporter.py`
**Dead functions (14)**: __init__, _count_components, _count_nets, _export_with_python_backend, _export_with_rust_backend, _get_cpu_usage, _get_memory_usage_mb, _log_netlist_analytics, _should_optimize, _should_use_rust_backend, _update_generation_stats, export_netlist_with_analytics, export_netlist_with_analytics, get_generation_statistics

#### `component.py`
**Dead functions (12)**: __call__, __getattr__, __init__, __iter__, __len__, __mul__, __post_init__, __setattr__, __str__, _validate_property, from_dict, print_pin_names

#### `kicad_validator.py`
**Dead functions (11)**: __init__, _generate_installation_guide, _get_kicad_paths, get_kicad_paths, main, require_kicad, require_kicad, validate_full_installation, validate_kicad_cli, validate_kicad_installation, validate_kicad_libraries

#### `circuit.py`
**Dead functions (10)**: __init__, _generate_hierarchical_json_netlist, components, generate_flattened_json_netlist, generate_full_netlist, generate_text_netlist, nets, simulate, simulator, to_flattened_list

#### `performance_profiler.py`
**Dead functions (10)**: __init__, get_profiler, get_summary, print_performance_summary, print_summary, profile, profile, profile_operation, time_operation, timing_decorator

#### `logging_minimal.py`
**Dead functions (10)**: __enter__, __exit__, __init__, __init__, _format_kwargs, get_current_context, monitor_performance, performance_context, timer, warning

#### `netlist_exporter.py`
**Dead functions (9)**: __init__, collect_nets, convert_json_to_netlist, generate_flattened_json_netlist, generate_full_netlist, generate_kicad_netlist_defensive, generate_text_netlist, print_circuit, to_flattened_list

#### `annotations.py`
**Dead functions (8)**: __post_init__, __post_init__, __post_init__, add_table, add_text_box, circle, line, rectangle

#### `pin.py`
**Dead functions (7)**: __eq__, __iadd__, __init__, __json__, __repr__, __str__, connected

#### `rust_integration.py`
**Dead functions (7)**: __init__, create_placement_engine, create_symbol_cache, generate_component_sexp, get_rust_function, has_rust_module, rust_accelerated

#### `simple_pin_access.py`
**Dead functions (5)**: __getitem__, __iadd__, __init__, __repr__, __setitem__

#### `net.py`
**Dead functions (4)**: __iadd__, __init__, __repr__, pins

#### `_logger.py`
**Dead functions (3)**: __init__, log_netlist_analytics, warning

#### `reference_manager.py`
**Dead functions (3)**: __init__, clear, set_initial_counters

#### `rust_components.py`
**Dead functions (3)**: create_rust_capacitor, create_rust_resistor, get_rust_component_status

#### `decorators.py`
**Dead functions (1)**: enable_comments

### `circuit_synth/data/examples/`

#### `example_kicad_project.py`
**Dead functions (8)**: debug_header, esp32, imu, regulator, resistor_divider, root, timed_function, usb_port

#### `jlc_component_finder_demo.py`
**Dead functions (5)**: demo_connector_search, demo_multiple_components, demo_passive_components, demo_single_component, main

### `circuit_synth/data/examples/agent-training/`

#### `03_complete_stm32_development_board.py`
**Dead functions (1)**: complete_stm32_development_board

#### `02_combined_usb_power_esp32.py`
**Dead functions (1)**: usb_powered_esp32

### `circuit_synth/data/examples/agent-training/interfaces/`

#### `01_basic_usb_c.py`
**Dead functions (1)**: basic_usb_c_power

### `circuit_synth/data/examples/agent-training/microcontrollers/`

#### `01_esp32_minimal.py`
**Dead functions (1)**: esp32_minimal

#### `02_stm32_with_crystal.py`
**Dead functions (1)**: stm32_reference_design

### `circuit_synth/data/examples/agent-training/power/`

#### `01_basic_ldo_3v3.py`
**Dead functions (1)**: basic_ldo_3v3

### `circuit_synth/data/examples/reference_designs/reference_desgin1/`

#### `python_generated_reference_design.py`
**Dead functions (1)**: resistor_divider

### `circuit_synth/data/examples/reference_designs/reference_desgin2/`

#### `python_generated_reference_design.py`
**Dead functions (2)**: resistor_divider, resistor_divider2

### `circuit_synth/data/templates/example_project/circuit-synth/`

#### `usb.py`
**Dead functions (1)**: usb_port

#### `debug_header.py`
**Dead functions (1)**: debug_header

#### `power_supply.py`
**Dead functions (1)**: power_supply

#### `led_blinker.py`
**Dead functions (1)**: led_blinker

#### `esp32c6.py`
**Dead functions (1)**: esp32c6

#### `main.py`
**Dead functions (1)**: main_circuit

### `circuit_synth/data/templates/project/`

#### `main.py`
**Dead functions (1)**: main

### `circuit_synth/data/tools/ci-setup/`

#### `setup_ci_symbols.py`
**Dead functions (4)**: download_file, get_ci_symbols_dir, main, verify_symbols

### `circuit_synth/interfaces/`

#### `circuit_interface.py`
**Dead functions (55)**: add_pin, connect, disconnect, disconnect, from_dict, get_component, get_component_type, get_components, get_connected_components, get_connected_net, get_electrical_type, get_footprint, get_library, get_name, get_name, get_name, get_net, get_nets, get_number, get_pin, get_pin_count, get_pin_type, get_pins, get_pins, get_position, get_position, get_properties, get_property, get_reference, get_rotation, get_statistics, get_value, is_connected, is_connected_to, remove_component, remove_net, remove_pin, set_electrical_type, set_footprint, set_library, set_name, set_name, set_name, set_pin_type, set_position, set_position, set_property, set_reference, set_rotation, set_symbol, set_value, validate, validate, validate, validate

#### `kicad_interface.py`
**Dead functions (35)**: __post_init__, __post_init__, add_net_connection, add_via, add_wire, auto_place_components, create_pcb_generator, create_schematic_generator, export_gerbers, get_component_count, get_component_placements, get_footprint_info, get_footprint_libraries, get_net_count, get_routing_statistics, get_symbol_info, get_symbol_libraries, get_version, import_netlist, initialize_pcb, initialize_project, place_component, route_traces, run_drc, save_pcb, save_schematic, search_footprint, search_symbol, set_board_outline, set_component_property, validate_footprint, validate_installation, validate_pcb, validate_schematic, validate_symbol

### `circuit_synth/io/`

#### `json_loader.py`
**Dead functions (2)**: load_circuit_from_dict, load_circuit_from_json_file

### `circuit_synth/kicad/`

#### `netlist_importer.py`
**Dead functions (50)**: __init__, __init__, __init__, _add_node_to_subcircuit, _build_hierarchy_from_design, _build_net_mapping, _clean_artifact_subcircuits, _collect_attached_subcircuits, _create_subcircuit_hierarchy, _determine_pin_type, _extract_net_info, _extract_node_info, _extract_schematic_source, _extract_sheet_info, _extract_sheetpath, _find_or_create_subcircuit, _find_section, _generate_canonical_name, _generate_component_signature, _generate_template_id, _get_component_sheet_path, _get_local_net_name, _get_parent_path, _get_pin_details, _get_subcircuit_name_from_path, _is_human_readable_name, _log_subcircuit_hierarchy, _normalize_sheet_path, _parse_design_properties, _parse_expr, _parse_libparts, _process_sheet_hierarchies, _register_component, _standardize_net_name, _tokenize, _verify_and_log_hierarchy, add_node, add_pin, components, convert_netlist, design, detect_duplicate_circuits, from_kicad, libparts, main, nets, parse, parse_file, parse_kicad_netlist, sheets

#### `unified_kicad_integration.py`
**Dead functions (39)**: __init__, __init__, __init__, __init__, __init__, _add_components_from_circuit_data, _apply_placement_algorithm, add_net_connection, add_wire, cleanup, create_pcb_generator, create_schematic_generator, create_unified_footprint_library, create_unified_kicad_integration, create_unified_pcb_generator, create_unified_schematic_generator, create_unified_symbol_library, generate_from_circuit_data, generate_from_circuit_data, generate_pcb, generate_schematic, get_component_count, get_footprint, get_footprint_libraries, get_footprint_library, get_net_count, get_symbol_libraries, get_symbol_library, get_version, initialize_project, list_footprints, list_libraries, list_libraries, list_symbols, save_schematic, set_component_property, validate_design, validate_installation, validate_schematic

#### `netlist_exporter.py`
**Dead functions (25)**: _collect_components_recursive, _extract_sheets_from_circuit, cleanup_whitespace, convert_json_to_netlist, determine_net_ownership, format_node, format_s_expr, generate_component_entry, generate_components_section, generate_design_section, generate_libpart_entry, generate_libparts_section, generate_libraries_section, generate_net_entry, generate_nets_section, load_circuit_json, normalize_hierarchical_path, normalize_hierarchical_path, process_circuit, process_components, process_net_nodes, scan_circuit, sort_key, to_kicad, validate_net_data

#### `canonical.py`
**Dead functions (24)**: __init__, __init__, __repr__, __repr__, __str__, _calculate_connectivity_score, _extract_net_connections, _extract_properties, _extract_symbols, _extract_wires_and_labels, _get_pin_connections, _group_components_by_type, _is_power_symbol, _match_by_connectivity, _parse_label, _parse_symbol, _parse_wire, _process_subcircuit_recursive, component_count, components, from_kicad, get_component_nets, get_component_type, match

#### `sheet_hierarchy_manager.py`
**Dead functions (21)**: __init__, _build_hierarchy, _build_path_map, _validate_hierarchy, _validate_uuid, check_cycles, collect_reachable, get_child_sheets, get_parent_sheet, get_sheet_by_path, get_sheet_by_uuid, get_sheet_order, get_sheet_paths, normalize_path, parse_sheet_data, parse_sheet_hierarchy, traverse, traverse, traverse, validate_hierarchy, validate_node

#### `logging_integration.py`
**Dead functions (20)**: __init__, __init__, _get_memory_usage, add_metric, log_collision_detection, log_component_placement, log_component_placement, log_file_generation, log_kicad_error, log_kicad_warning, log_pcb_generation, log_pcb_generation, log_performance_bottleneck, log_progress, log_routing_progress, log_schematic_generation, log_schematic_generation, log_symbol_lookup, log_validation_result, operation_context

#### `symbol_lib_parser.py`
**Dead functions (18)**: __init__, __new__, _find_kicad_sym_file, _find_library_file, _get_key, _get_unit_number, _parse_file, _parse_property_elem, _resolve_all_extends, _resolve_extends_for_symbol, from_simple_dict, from_simple_dict, from_simple_dict, merge_parent, parse_symbol, to_simple_dict, to_simple_dict, to_simple_dict

#### `kicad_symbol_cache.py`
**Dead functions (13)**: __init__, __new__, _build_complete_index, _extract_symbol_names_fast, _find_kicad_symbol_dirs, _find_library_file, _is_cache_expired, _python_grep_search, _ripgrep_symbol_search, find_symbol_library, get_all_libraries, get_all_symbols, get_symbol_data_by_name

#### `project_notes.py`
**Dead functions (11)**: __init__, _get_project_name, _is_kicad_project, _update_config, add_user_note, ensure_notes_folder, export_cache_summary, get_analysis_history, get_datasheet_path, save_analysis_result, save_datasheet

#### `net_name_generator.py`
**Dead functions (8)**: __init__, _extract_existing_index, _get_next_number, _normalize_bus_name, _validate_bus_inputs, apply_power_net_rules, generate_net_name, resolve_bus_names

#### `rust_accelerated_symbol_cache.py`
**Dead functions (7)**: __new__, find_symbol_library, get_all_libraries, get_all_symbols, get_performance_info, get_symbol_data_by_name, is_rust_accelerated

#### `net_tracker.py`
**Dead functions (6)**: __init__, _get_driver_priority, analyze_net_drivers, detect_power_nets, get_net_info, track_net_usage

#### `netlist_service.py`
**Dead functions (5)**: __init__, __init__, __init__, __init__, create_netlist_service

#### `symbol_lib_parser_manager.py`
**Dead functions (2)**: get_parser, reset

### `circuit_synth/kicad/pcb_gen/`

#### `pcb_generator.py`
**Dead functions (9)**: __init__, _apply_netlist_to_pcb, _auto_route_pcb, _calculate_initial_board_size, _extract_components_from_schematics, _extract_connections_from_schematics, _extract_hierarchical_path, _update_project_file, generate_pcb

### `circuit_synth/kicad/sch_api/`

#### `component_search.py`
**Dead functions (20)**: __init__, _build_indices, _get_reference_prefix, _has_unconnected_pins, find_by_criteria, find_by_custom_filter, find_by_footprint, find_by_lib_id, find_by_property, find_by_reference, find_by_reference_pattern, find_by_value, find_duplicates, find_in_area, find_nearest, find_unconnected_components, get_statistics, group_by_lib_id, group_by_type, group_by_value

#### `placement_engine.py`
**Dead functions (17)**: __init__, _contextual_placement, _create_bounding_box, _determine_strategy, _edge_placement, _find_nearest_free_position, _find_related_components, _get_component_prefix, _get_prefix_from_lib_id, _get_type_based_y_position, _grid_placement, _has_related_components, _update_state, check_collision, contains_point, expand, find_next_position

#### `component_manager.py`
**Dead functions (14)**: __init__, _create_component_instance, _create_pins, _get_symbol_size, _is_valid_property_name, _set_component_properties, _validate_and_fetch_symbol, clone_component, get_all_components, get_component, move_component, remove_component, update_component_property, validate_schematic

#### `bulk_operations.py`
**Dead functions (12)**: __init__, _align_grid, _align_horizontal, _align_vertical, _calculate_group_bounds, _rearrange_components, align_components, distribute_evenly, mirror_group, move_components, rotate_group, update_property_bulk

#### `reference_manager.py`
**Dead functions (11)**: __init__, _get_reference_prefix, _is_valid_reference, _update_counter_from_reference, clear, generate_reference, get_next_reference, get_statistics, is_reference_available, release_reference, update_reference

#### `sync_integration.py`
**Dead functions (10)**: __init__, _add_component_from_sync, _apply_sync_changes, _find_schematic_file, _modify_component_from_sync, _remove_component_from_sync, create_sync_integration, demonstrate_api_features, setup_from_project, sync_with_circuit_using_api

#### `exceptions.py`
**Dead functions (6)**: __init__, __init__, __init__, __init__, __init__, __init__

#### `component_operations.py`
**Dead functions (6)**: __init__, _estimate_component_size, _increment_reference, clone_component, move_component, remove_component

### `circuit_synth/kicad/sch_editor/`

#### `schematic_exporter.py`
**Dead functions (10)**: __init__, __init__, _ensure_required_sections, _format_schematic, _validate_schematic, export_file, write_component, write_hierarchical_label, write_net, write_sheet

#### `schematic_comparer.py`
**Dead functions (7)**: __init__, _compare_component_properties, _compare_components, _compare_net_nodes, _compare_nets, _compare_sheets, compare_with_circuit

#### `schematic_reader.py`
**Dead functions (6)**: __init__, __iter__, __post_init__, _get_libpart_pin_type, _parse_comp_section, get_component

#### `schematic_editor.py`
**Dead functions (4)**: __init__, remove_component, save, schematic_data

### `circuit_synth/kicad/sch_gen/`

#### `main_generator.py`
**Dead functions (34)**: __init__, __init__, __init__, __init__, __init__, _add_bounding_boxes_to_existing_project, _generate_netlist, _log_sync_results, _update_existing_project, _write_cover_sheet, cleanup, create_pcb_generator, create_schematic_generator, generate_from_circuit_data, generate_from_circuit_data, generate_from_schematic, generate_pcb, generate_pcb_from_schematics, generate_schematic, get_capabilities, get_footprint_info, get_footprint_libraries, get_footprint_library, get_pcb_generator, get_schematic_generator, get_symbol_info, get_symbol_libraries, get_symbol_library, get_version, place_components, search_footprints, search_symbols, validate_design, validate_installation

#### `connection_analyzer.py`
**Dead functions (12)**: __init__, _identify_groups, _is_power_net, analyze_circuit, calculate_wire_length, find, get_component_group, get_connected_components, get_connection_count, get_connection_strength, get_placement_order, union

#### `integrated_reference_manager.py`
**Dead functions (8)**: __init__, __init__, enable_reassignment_mode, get_next_reference_for_type, get_reference_for_component, integrate_into_schematic_writer_example, reset, test_integrated_reference_generation

#### `integrated_placement.py`
**Dead functions (8)**: __init__, __init__, _create_placed_component, _get_component_id, _get_component_type, integrate_into_collision_manager, place_components_with_strategy, test_integrated_placement

#### `connection_aware_collision_manager.py`
**Dead functions (8)**: __init__, _calculate_ideal_position, _find_nearest_valid_position, _try_position, analyze_connections, get_placement_metrics, place_component_connection_aware, reset_placement

#### `data_structures.py`
**Dead functions (8)**: __init__, __init__, __init__, __init__, __repr__, __repr__, __repr__, __repr__

#### `schematic_writer.py`
**Dead functions (7)**: __init__, _add_component_bounding_boxes, _add_paper_size, _add_sheet_instances, _add_symbol_instances_table, _add_table_annotation, _add_text_annotation

#### `circuit_loader.py`
**Dead functions (7)**: __init__, __init__, __init__, __repr__, __repr__, __repr__, _circuits_match

#### `connection_aware_collision_manager_v2.py`
**Dead functions (7)**: __init__, _calculate_ideal_position_and_rotation, _calculate_ideal_rotation, _is_better_position, analyze_connections, get_placement_metrics, place_component_connection_aware

#### `api_integration_plan.py`
**Dead functions (7)**: __init__, integrate_bounding_box_calculation, integrate_into_collision_manager, integrate_into_schematic_writer, integrate_models_for_type_safety, integrate_placement_strategies, integrate_reference_generation

#### `kicad_formatter.py`
**Dead functions (7)**: __init__, _format_inline_construct, _format_standard_list, _is_inline_construct, format, format_kicad_schematic, get_parser

#### `hierarchical_aware_placement.py`
**Dead functions (5)**: __init__, _find_available_space, allocate_sheet_region, get_sheet_bounds, get_sheet_offset

#### `collision_detection.py`
**Dead functions (4)**: __init__, __init__, __repr__, clear

#### `collision_manager.py`
**Dead functions (3)**: __init__, clear, register_existing_symbol

#### `hierarchy_manager.py`
**Dead functions (2)**: __init__, build_hierarchy

### `circuit_synth/kicad/sch_sync/`

#### `synchronizer.py`
**Dead functions (22)**: __init__, __post_init__, _check_connection_changes, _collect_components_recursive, _component_needs_update, _export_kicad_netlist, _extract_circuit_components, _extract_kicad_components, _extract_properties_from_symbol, _extract_symbols_ordered, _find_main_schematic, _find_sheet_uuid_for_schematic, _get_component_updates, _load_kicad_schematic, _match_components_canonical, _process_component_matches, _process_unmatched_components, _schematic_has_components, _write_updated_schematic, extract_symbols_recursive, sync_with_circuit, synchronize

#### `schematic_updater.py`
**Dead functions (12)**: __init__, _add_component, _add_hierarchical_labels, _align_to_grid, _create_component_pins, _create_schematic_symbol, _find_safe_placement, _modify_component, _remove_component, apply_updates, create_component_updates_from_sync_report, save_schematic

#### `component_matcher.py`
**Dead functions (6)**: __init__, _calculate_match_confidence, _get_component_footprint, _get_component_reference, _get_component_value, match_components

### `circuit_synth/kicad_api/core/`

#### `types.py`
**Dead functions (21)**: __getitem__, __iter__, __post_init__, _point_on_segment, add_junction, add_node, add_rectangle, add_wire, center, contains_point, contains_point, get_all_elements, get_bounding_box, get_component, get_endpoints, height, remove_component, to_tuple, total_count, uuid, width

#### `s_expression.py`
**Dead functions (18)**: __init__, _find_all_elements, _find_element, _get_symbol_name, _is_sexp_list, _junction_to_sexp, _parse_junction, _parse_label, _parse_sheet, _parse_sheet_pin, _parse_symbol, _parse_title_block, _parse_wire, _rectangle_to_sexp, _simple_text_to_sexp, _wire_to_sexp, parse_file, to_schematic

#### `symbol_cache.py`
**Dead functions (16)**: __init__, _build_complete_index, _deserialize_symbol, _extract_symbol_names_fast, _find_library_file, _load_symbol, _python_grep_search, _ripgrep_symbol_search, _save_cache, _serialize_symbol, add_library_path, bounding_box, get_all_symbols, get_reference_prefix, get_symbol_by_name, list_libraries

### `circuit_synth/kicad_api/pcb/`

#### `pcb_board.py`
**Dead functions (66)**: __init__, _add_default_pads, _add_graphic_item, _create_empty_pcb, _create_footprint_from_library_data, _get_default_layers, _get_default_setup, _parse_library_arc, _parse_library_line, _parse_library_model, _parse_library_pad, _parse_library_rect, _parse_library_text, add_edge_cut_line, add_footprint, add_footprint_from_library, add_footprint_object, add_track, add_via, add_zone, auto_place_components, check_basic_rules, clear_edge_cuts, clear_footprints, clear_tracks, clear_zones, connect_pads, disconnect_pad, export_drill, export_gerbers, export_pick_and_place, fill_zone, footprints, get_board_info, get_board_outline, get_board_outline, get_board_outline_bbox, get_connections, get_footprint, get_footprint_count, get_footprint_info, get_net_by_name, get_net_count, get_net_info, get_placement_bbox, get_ratsnest, get_tracks, get_zones, list_available_libraries, list_footprints, load, move_footprint, refresh_footprint_cache, remove_footprint, remove_track, remove_zone, route_connection, route_ratsnest, run_drc, save, search_footprints, set_board_outline, set_board_outline_polygon, set_board_outline_rect, unfill_zone, update_footprint_value

#### `pcb_parser.py`
**Dead functions (31)**: __init__, _arc_to_sexp, _find_all_elements, _find_element, _footprint_to_sexp, _get_symbol_name, _gr_line_to_sexp, _gr_rect_to_sexp, _is_sexp_list, _line_to_sexp, _pad_to_sexp, _parse_arc, _parse_footprint, _parse_general, _parse_layers, _parse_line, _parse_net, _parse_pad, _parse_property, _parse_rectangle, _parse_text, _parse_track, _parse_via, _parse_zone, _pcb_to_sexp, _property_to_sexp, _rect_to_sexp, _track_to_sexp, _via_to_sexp, _zone_to_sexp, parse_file

#### `force_directed_placement.py`
**Dead functions (23)**: __add__, __init__, __mul__, _build_connection_graph, _build_connectivity_from_board, _calculate_attraction, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_boundary_force, _calculate_group_repulsion, _calculate_repulsion, _connectivity_aware_collision_resolution, _count_inter_group_connections, _enforce_minimum_spacing, _group_by_subcircuit, _initialize_group_positions, _optimize_group_positions, _optimize_rotations, _optimize_subcircuit, _update_group_properties, magnitude, normalize, place

#### `force_directed_placement_fixed.py`
**Dead functions (22)**: __add__, __init__, __mul__, _build_connection_graph, _build_connectivity_from_graph, _calculate_attraction, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_boundary_force, _calculate_group_repulsion, _calculate_repulsion, _connectivity_aware_collision_resolution, _count_inter_group_connections, _enforce_minimum_spacing, _group_by_subcircuit, _initialize_group_positions, _optimize_group_positions, _optimize_rotations, _optimize_subcircuit, _update_group_properties, magnitude, place

#### `courtyard_collision_improved.py`
**Dead functions (22)**: __init__, __init__, __sub__, _bounding_boxes_overlap, _calculate_footprint_bbox, _calculate_signed_area, _get_cached_polygon, _trace_polygon_from_lines, check_collision, contains_point, detect_collisions, dot, expand, get_axes, get_bounding_box, get_collision_vector, get_courtyard_polygon, get_edges, get_footprint_polygon, perp_dot, project_onto_axis, transform

#### `validation.py`
**Dead functions (22)**: __init__, __str__, _bbox_spacing, _get_footprint_bbox, _validate_board_outline, _validate_component_placement, _validate_isolated_copper, _validate_net_connectivity, _validate_overlapping_footprints, _validate_tracks, _validate_vias, _validate_zones, add_error, add_info, add_warning, error_count, info_count, is_valid, print_summary, validate_board, validate_pcb, warning_count

#### `courtyard_collision.py`
**Dead functions (21)**: __init__, __init__, _arcs_to_polygon, _bboxes_overlap, _calculate_footprint_bbox, _calculate_signed_area, _circle_to_polygon, _inflate_polygon, _is_inside_board, _lines_to_polygon, _normalize_vector, _polygons_intersect, _project_polygon, check_collision, check_collision_with_placed, contains_point, find_valid_position, get_bounding_box, get_courtyard_polygon, get_footprint_polygon, transform

#### `footprint_library.py`
**Dead functions (18)**: __init__, _build_index, _discover_system_libraries, _extract_basic_info, _load_or_build_index, _save_index, _sexp_to_dict, footprint_type, get_footprint, get_footprint_cache, get_footprint_data, is_mixed, is_smd, is_tht, list_libraries, refresh_cache, score, search_footprints

#### `hierarchical_placement_v2.py`
**Dead functions (16)**: __init__, _find_best_placement_point, _get_area, _get_combined_bbox_footprints, _get_item_polygon, _get_position, _get_spacing, _group_by_hierarchy, _group_groups, _is_locked, _is_within_board, _pack_group, _place_at_board_edge, _set_position, place, place_components

#### `hierarchical_placement.py`
**Dead functions (16)**: __init__, _bbox_within_board, _find_best_placement_point, _get_area, _get_bbox, _get_combined_bbox, _get_spacing, _group_by_hierarchy, _group_groups, _is_locked, _pack_group, _set_bottom_left, _set_center, _touches, place, place_components

#### `connectivity_driven.py`
**Dead functions (14)**: __init__, _build_connectivity_graph, _calculate_placement_order, _count_crossings, _find_best_position, _find_closest_valid_position, _find_clusters, _find_empty_spot, _identify_critical_nets, _is_valid_position, _lines_intersect, _minimize_crossings, ccw, place

#### `base.py`
**Dead functions (14)**: __init__, _calculate_bbox, area, bbox, hierarchical_path, is_locked, move_to, original_bbox, place, position, reference, set_bottom_left, touches, value

#### `force_directed.py`
**Dead functions (12)**: __init__, _apply_gravity_forces, _apply_repulsion_forces, _apply_spring_forces, _calculate_center, _initialize_positions, _run_placement, _update_positions, add_connection, apply_force_directed_placement, place, reference

#### `kicad_cli.py`
**Dead functions (12)**: __init__, __init__, _find_kicad_cli, export_drill, export_gerbers, export_pos, export_svg, get_kicad_cli, get_version, run_command, run_drc, total_issues

#### `grouping.py`
**Dead functions (11)**: __init__, area, bbox, group_by_hierarchy, group_groups, hierarchical_level, hierarchical_level, is_locked, move, set_bottom_left, touches

#### `connection_centric.py`
**Dead functions (10)**: __init__, _analyze_connections, _find_edge_position, _find_nearest_valid_position, _find_optimal_position, _get_subcircuit, _group_by_subcircuit, _is_valid_position, _place_subcircuit, place

#### `bbox.py`
**Dead functions (10)**: area, bottom_left, bottom_right, center, from_points, height, inflate, merge, top_left, width

#### `spiral_placement.py`
**Dead functions (9)**: __init__, _boxes_overlap, _build_connection_graph, _calculate_ideal_position, _find_nearest_valid_position, _get_inflated_bbox, _is_position_valid, _is_within_board, place_components

#### `spiral_hierarchical_placement.py`
**Dead functions (9)**: __init__, _build_connection_map, _calculate_ideal_position, _find_best_placement_point, _get_reference, _is_valid_position, _set_bottom_left, _spiral_search, place

#### `spiral_placement_v2.py`
**Dead functions (6)**: __init__, _build_connection_graph, _calculate_ideal_position, _find_nearest_valid_position, get_placement_info, place_components

#### `pcb_formatter.py`
**Dead functions (4)**: __init__, _format_list, format, format_pcb

#### `types.py`
**Dead functions (4)**: __repr__, get_library_id, get_property, set_property

#### `utils.py`
**Dead functions (3)**: _estimate_footprint_bbox, calculate_placement_bbox, optimize_component_rotation

### `circuit_synth/kicad_api/pcb/placement/`

#### `force_directed_placement.py`
**Dead functions (23)**: __add__, __init__, __mul__, _build_connection_graph, _build_connectivity_from_board, _calculate_attraction, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_boundary_force, _calculate_group_repulsion, _calculate_repulsion, _connectivity_aware_collision_resolution, _count_inter_group_connections, _enforce_minimum_spacing, _group_by_subcircuit, _initialize_group_positions, _optimize_group_positions, _optimize_rotations, _optimize_subcircuit, _update_group_properties, magnitude, normalize, place

#### `force_directed_placement_fixed.py`
**Dead functions (22)**: __add__, __init__, __mul__, _build_connection_graph, _build_connectivity_from_graph, _calculate_attraction, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_boundary_force, _calculate_group_repulsion, _calculate_repulsion, _connectivity_aware_collision_resolution, _count_inter_group_connections, _enforce_minimum_spacing, _group_by_subcircuit, _initialize_group_positions, _optimize_group_positions, _optimize_rotations, _optimize_subcircuit, _update_group_properties, magnitude, place

#### `courtyard_collision_improved.py`
**Dead functions (22)**: __init__, __init__, __sub__, _bounding_boxes_overlap, _calculate_footprint_bbox, _calculate_signed_area, _get_cached_polygon, _trace_polygon_from_lines, check_collision, contains_point, detect_collisions, dot, expand, get_axes, get_bounding_box, get_collision_vector, get_courtyard_polygon, get_edges, get_footprint_polygon, perp_dot, project_onto_axis, transform

#### `courtyard_collision.py`
**Dead functions (21)**: __init__, __init__, _arcs_to_polygon, _bboxes_overlap, _calculate_footprint_bbox, _calculate_signed_area, _circle_to_polygon, _inflate_polygon, _is_inside_board, _lines_to_polygon, _normalize_vector, _polygons_intersect, _project_polygon, check_collision, check_collision_with_placed, contains_point, find_valid_position, get_bounding_box, get_courtyard_polygon, get_footprint_polygon, transform

#### `hierarchical_placement_v2.py`
**Dead functions (16)**: __init__, _find_best_placement_point, _get_area, _get_combined_bbox_footprints, _get_item_polygon, _get_position, _get_spacing, _group_by_hierarchy, _group_groups, _is_locked, _is_within_board, _pack_group, _place_at_board_edge, _set_position, place, place_components

#### `hierarchical_placement.py`
**Dead functions (16)**: __init__, _bbox_within_board, _find_best_placement_point, _get_area, _get_bbox, _get_combined_bbox, _get_spacing, _group_by_hierarchy, _group_groups, _is_locked, _pack_group, _set_bottom_left, _set_center, _touches, place, place_components

#### `connectivity_driven.py`
**Dead functions (14)**: __init__, _build_connectivity_graph, _calculate_placement_order, _count_crossings, _find_best_position, _find_closest_valid_position, _find_clusters, _find_empty_spot, _identify_critical_nets, _is_valid_position, _lines_intersect, _minimize_crossings, ccw, place

#### `base.py`
**Dead functions (14)**: __init__, _calculate_bbox, area, bbox, hierarchical_path, is_locked, move_to, original_bbox, place, position, reference, set_bottom_left, touches, value

#### `force_directed.py`
**Dead functions (12)**: __init__, _apply_gravity_forces, _apply_repulsion_forces, _apply_spring_forces, _calculate_center, _initialize_positions, _run_placement, _update_positions, add_connection, apply_force_directed_placement, place, reference

#### `grouping.py`
**Dead functions (11)**: __init__, area, bbox, group_by_hierarchy, group_groups, hierarchical_level, hierarchical_level, is_locked, move, set_bottom_left, touches

#### `connection_centric.py`
**Dead functions (10)**: __init__, _analyze_connections, _find_edge_position, _find_nearest_valid_position, _find_optimal_position, _get_subcircuit, _group_by_subcircuit, _is_valid_position, _place_subcircuit, place

#### `bbox.py`
**Dead functions (10)**: area, bottom_left, bottom_right, center, from_points, height, inflate, merge, top_left, width

#### `spiral_placement.py`
**Dead functions (9)**: __init__, _boxes_overlap, _build_connection_graph, _calculate_ideal_position, _find_nearest_valid_position, _get_inflated_bbox, _is_position_valid, _is_within_board, place_components

#### `spiral_hierarchical_placement.py`
**Dead functions (9)**: __init__, _build_connection_map, _calculate_ideal_position, _find_best_placement_point, _get_reference, _is_valid_position, _set_bottom_left, _spiral_search, place

#### `spiral_placement_v2.py`
**Dead functions (6)**: __init__, _build_connection_graph, _calculate_ideal_position, _find_nearest_valid_position, get_placement_info, place_components

#### `utils.py`
**Dead functions (3)**: _estimate_footprint_bbox, calculate_placement_bbox, optimize_component_rotation

### `circuit_synth/kicad_api/pcb/routing/`

#### `dsn_exporter.py`
**Dead functions (17)**: __init__, _add_footprint_definitions, _add_padstack_definitions, _calculate_footprint_bbox, _convert_pad_shape, _extract_board_outline, _extract_components, _extract_layers, _extract_nets, _generate_dsn, _get_footprint_id, _get_kicad_version, _get_pad_net, _rotate_point, _sanitize_net_name, export, export_pcb_to_dsn

#### `ses_importer.py`
**Dead functions (16)**: __init__, __init__, _build_net_map, _import_vias, _import_wires, _parse_network_routes, _parse_resolution, _parse_routes, _parse_session, _parse_vias, _remove_existing_routing, add_via, add_wire, import_routing, import_ses_to_pcb, parse

#### `freerouting_runner.py`
**Dead functions (10)**: __init__, _check_java, _find_freerouting_jar, _monitor_output, _parse_progress, _process_line, get_progress, route, route_pcb, stop

#### `install_freerouting.py`
**Dead functions (7)**: check_java, download_file, download_progress, get_download_url, get_platform_info, install_freerouting, main

#### `freerouting_docker.py`
**Dead functions (4)**: __init__, _check_docker, route, route_pcb_docker

### `circuit_synth/kicad_api/schematic/`

#### `schematic_transform.py`
**Dead functions (30)**: __init__, align_elements, apply, auto_arrange, center, compose, contains_point, distribute_elements, expand, get_current_transform, height, identity, mirror_elements, mirror_x, mirror_y, pop_transform, push_transform, rotate_elements, rotation, scale, scale_elements, transform_component, transform_junction, transform_label, transform_position, transform_text, transform_wire, translate_elements, translation, width

#### `search_engine.py`
**Dead functions (27)**: __init__, __init__, _build_indices, _get_component_field, _matches_pattern, _matches_query, add_criterion, build, combine_with_and, combine_with_or, find_components_in_area, find_duplicate_references, find_power_nets, find_unconnected_pins, get_net_statistics, is_empty, parse_value, search_by_footprint, search_by_value, search_components, search_nets, total_count, trace_net, with_footprint, with_property, with_reference, with_value

#### `hierarchy_navigator.py`
**Dead functions (25)**: __init__, _build_hierarchy_recursive, _check_duplicate_names, _check_missing_files, _check_sheet_pins, _get_schematic_containing_sheet, _load_sheet_schematic, _validate_sheet_connections, add_child, analyze_hierarchy, check_files, count_instances, count_recursive, count_recursive, dfs, find_circular_references, find_node, find_sheet_by_name, get_all_sheets_recursive, get_full_path, get_hierarchy_tree, get_instance_count, get_net_scope, get_sheet_path, validate_hierarchy

#### `design_rule_checker.py`
**Dead functions (24)**: __init__, __str__, _add_violation, _check_duplicate_references, _check_floating_nets, _check_missing_footprints, _check_missing_references, _check_missing_values, _check_net_naming, _check_off_grid, _check_overlapping_components, _check_power_pins, _check_reference_naming, _check_required_properties, _check_text_size, _check_unconnected_pins, _check_wire_junctions, _check_wire_length, _find_wire_intersection, check_schematic, filter_violations, get_summary, get_violations_by_category, is_on_grid

#### `placement.py`
**Dead functions (23)**: __init__, __init__, _arrange_circular, _arrange_force_directed_python, _arrange_force_directed_rust, _arrange_grid, _arrange_horizontal, _arrange_vertical, _check_within_bounds, _estimate_component_size, _estimate_sheet_size, _find_center_position, _find_edge_position, _find_grid_position, _find_next_available_position, _find_next_available_position_with_size, _get_occupied_bounds, arrange_components, bottom, find_position, overlaps, place_element, right

#### `sheet_manager.py`
**Dead functions (21)**: __init__, _calculate_pin_position, _calculate_sheet_size, _find_circular_references, _find_sheet_position, _get_pin_orientation, _index_sheets, _recalculate_pin_positions, _resolve_sheet_path, _validate_filename, add_sheet, add_sheet_pin, create_sheet_from_components, dfs, get_sheet_by_name, get_sheet_contents, get_sheet_hierarchy, remove_sheet, remove_sheet_pin, update_sheet, validate_hierarchy

#### `bulk_operations.py`
**Dead functions (21)**: __init__, __init__, _add_property, _delete_components, _duplicate_components, _move_components, _remove_property, _replace_symbol, _update_footprint, _update_property, _update_value, add_operation, affected_count, applies_to, create_footprint_update_operation, create_move_operation, create_operation_batch, create_value_update_operation, execute, execute_operation, get_operation_history

#### `connection_tracer.py`
**Dead functions (20)**: __hash__, __hash__, __init__, __init__, _build_connection_graph, _get_or_create_node, _points_equal, add_edge, add_edge, add_node, add_node, analyze_connectivity, find_all_connections, find_floating_nets, find_path, find_path_between_pins, find_short_circuits, get_net_endpoints, get_node_at, trace_net

#### `net_discovery.py`
**Dead functions (17)**: __init__, __init__, _create_net_info, _is_bus_net, _is_ground_net, _is_power_net, analyze_net_connectivity, discover_all_nets, discover_hierarchical_nets, find_floating_nets, get_member_name, get_net_statistics, identify_bus_nets, is_valid, merge_net_aliases, suggest_net_names, trace_hierarchical_net

#### `wire_manager.py`
**Dead functions (15)**: __init__, _build_pin_connections, _build_wire_database, _find_wires_at_point, _get_component_pins, _get_pin_position, _manhattan_route, _points_equal, add_connection, add_wire_between_points, find_or_create_junction, find_wires_for_pin, get_net_at_point, remove_pin_connections, route_wire

#### `connection_updater.py`
**Dead functions (14)**: __init__, _connect_pin_to_net, _create_net_label, _create_power_symbol, _find_nearest_label, _find_or_create_net_point, _find_pin, _get_component_pins, _get_pin_position, _needs_junction, optimize_wire_routing, remove_floating_wires, update_component_connections, update_net_connections

#### `synchronizer.py`
**Dead functions (14)**: __init__, _add_component, _determine_library_id, _extract_circuit_components, _extract_pin_info, _load_schematic, _load_sheets_recursively, _match_components, _needs_update, _process_matches, _process_unmatched, _save_schematic, get_all_components, sync_with_circuit

#### `sheet_utils.py`
**Dead functions (13)**: _get_pin_side, all_sides, calculate_pin_spacing, calculate_sheet_size_from_content, create_sheet_instance_name, estimate_sheet_complexity, generate_sheet_documentation, group_pins_by_function, match_hierarchical_labels_to_pins, resolve_sheet_filepath, suggest_pin_side, suggest_sheet_position, validate_sheet_filename

#### `label_manager.py`
**Dead functions (12)**: __init__, _build_label_index, _find_wires_near_point, _is_horizontal_wire, auto_position_label, find_labels_at_point, find_labels_by_text, get_label_by_uuid, get_labels_by_type, remove_label, update_label, validate_hierarchical_labels

#### `junction_manager.py`
**Dead functions (12)**: __init__, _add_junction_at_position, _build_junction_index, _find_junction_points, _find_wire_crossings, _remove_junction_at_position, add_junction, find_junctions_in_area, get_junction_at, remove_junction, update_junctions, validate_junctions

#### `component_manager.py`
**Dead functions (12)**: __init__, _generate_reference, clone_component, find_components_by_library, find_components_by_value, get_bounding_box, get_component, list_components, move_component, remove_component, update_component, validate_schematic

#### `project_generator.py`
**Dead functions (11)**: __init__, _copy_blank_project_files, _generate_hierarchical_design, _generate_root_with_unified_placement, _generate_schematic, _generate_simple_design, _generate_sub_sheet, _generate_top_sheet, _get_library_id, _get_pin_position, generate_from_circuit

#### `text_manager.py`
**Dead functions (10)**: __init__, _build_text_index, add_multiline_text, align_texts, find_text_at_point, find_text_by_content, get_all_texts, get_text_by_uuid, remove_text, update_text

#### `wire_router.py`
**Dead functions (10)**: __init__, _line_intersects_rect, _path_intersects_obstacles, _point_on_line, optimize_path, route_bus, route_diagonal, route_direct, route_manhattan, route_smart

#### `connection_utils.py`
**Dead functions (9)**: apply_transformation, distance_between_points, find_pin_by_name, get_pin_position, get_wire_segments, point_on_segment, points_equal, segment_intersection, simplify_points

#### `label_utils.py`
**Dead functions (8)**: calculate_text_bounds, find_connected_labels, format_net_name, get_wire_direction_at_point, group_labels_by_net, suggest_label_for_component_pin, suggest_label_position, validate_hierarchical_label_name

#### `sync_strategies.py`
**Dead functions (7)**: __init__, __init__, __init__, match_components, match_components, match_components, match_components

#### `geometry_utils.py`
**Dead functions (7)**: calculate_label_orientation, calculate_label_position, create_dynamic_hierarchical_label, get_actual_pin_position, get_pin_end_position, get_pins_at_position, transform_pin_to_world

#### `sheet_placement.py`
**Dead functions (6)**: __init__, calculate_pin_positions, calculate_sheet_size, create_sheet_symbols, get_next_position, place_sheet

#### `symbol_geometry.py`
**Dead functions (6)**: __init__, _calculate_symbol_bounds, _get_default_bounds, _update_bounds_from_graphic_element, calculate_text_width, get_symbol_bounds

#### `sync_adapter.py`
**Dead functions (5)**: __init__, _find_schematic, _schematic_has_components, sync_with_circuit, synchronize

#### `net_matcher.py`
**Dead functions (4)**: __init__, _calculate_net_similarity, _get_component_nets, match_by_connections

#### `instance_utils.py`
**Dead functions (1)**: get_project_hierarchy_path

### `circuit_synth/manufacturing/jlcpcb/`

#### `smart_component_finder.py`
**Dead functions (20)**: __init__, _calculate_score, _create_recommendation, _extract_component_family, _extract_component_value, _find_kicad_footprint, _find_kicad_symbol, _generate_circuit_synth_code, _generate_recommendation_notes, _get_reference_designator, _guess_footprint_from_package, _guess_symbol_from_description, _is_passive_component, _load_footprint_mappings, _load_symbol_mappings, find_alternatives, find_components, find_components, get_best_component, print_component_recommendation

#### `jlc_web_scraper.py`
**Dead functions (12)**: __init__, _extract_json_data, _extract_number, _get_demo_components, _parse_html_table, _parse_search_results, _parse_table_row, enhance_component_with_web_data, get_component_availability_web, get_most_available_component, search_components, search_jlc_components_web

#### `cache.py`
**Dead functions (11)**: __init__, _get_cache_file, _get_cache_key, _is_cache_valid, cached_jlcpcb_search, clear_all, clear_expired, get, get_cache_info, get_jlcpcb_cache, set

#### `jlc_parts_lookup.py`
**Dead functions (9)**: __init__, _calculate_manufacturability_score, _obtain_token, enhance_component_with_jlc_data, get_component_alternatives, get_component_page, get_most_available_part, recommend_jlc_component, search_components

### `circuit_synth/memory_bank/`

#### `core.py`
**Dead functions (22)**: __init__, __init__, _analyze_commit_changes, _create_board_structure, _create_project_level_files, _get_commit_message, _should_update_decisions, _should_update_issues_from_diff, _should_update_timeline, _should_update_timeline_from_diff, _update_decisions_file, _update_decisions_file_with_diff, _update_issues_file_with_diff, _update_timeline_file, _update_timeline_file_with_diff, add_board, create_project_structure, get_boards, get_config, is_memory_bank_enabled, remove_memory_bank, update_from_commit

#### `circuit_diff.py`
**Dead functions (17)**: __init__, __post_init__, __post_init__, _analyze_kicad_file_changes, _analyze_python_components, _analyze_python_file_changes, _analyze_python_nets, _compare_circuits, _get_changed_files, _get_commit_message, _get_file_content, _simple_diff_analysis, analyze_commit_changes, cache_circuit_state, format_diff_for_memory_bank, get_cached_circuit_state, has_significant_changes

#### `context.py`
**Dead functions (11)**: __init__, _create_basic_claude_config, auto_detect_board, clear_context, ensure_context, get_context_status, get_current_board, get_current_context, get_current_memory_bank_path, list_available_boards, switch_board

#### `git_integration.py`
**Dead functions (8)**: __init__, get_commit_info, get_current_commit_hash, get_recent_commits, install_post_commit_hook, is_git_repository, remove_post_commit_hook, update_memory_bank_from_commit

#### `commands.py`
**Dead functions (8)**: add_board, get_current_context, get_memory_bank_status, init_memory_bank, list_boards, remove_memory_bank, search_memory_bank, switch_board

#### `templates.py`
**Dead functions (3)**: generate_claude_md, get_all_templates, get_template

#### `cli.py`
**Dead functions (2)**: init_cli, remove_cli

### `circuit_synth/pcb/`

#### `pcb_board.py`
**Dead functions (65)**: __init__, _add_default_pads, _add_graphic_item, _create_empty_pcb, _create_footprint_from_library_data, _get_default_layers, _get_default_setup, _parse_library_arc, _parse_library_line, _parse_library_pad, _parse_library_rect, _parse_library_text, add_edge_cut_line, add_footprint, add_footprint_from_library, add_footprint_object, add_track, add_via, add_zone, auto_place_components, check_basic_rules, clear_edge_cuts, clear_footprints, clear_tracks, clear_zones, connect_pads, disconnect_pad, export_drill, export_gerbers, export_pick_and_place, fill_zone, footprints, get_board_info, get_board_outline, get_board_outline, get_board_outline_bbox, get_connections, get_footprint, get_footprint_count, get_footprint_info, get_net_by_name, get_net_count, get_net_info, get_placement_bbox, get_ratsnest, get_tracks, get_zones, list_available_libraries, list_footprints, load, move_footprint, refresh_footprint_cache, remove_footprint, remove_track, remove_zone, route_connection, route_ratsnest, run_drc, save, search_footprints, set_board_outline, set_board_outline_polygon, set_board_outline_rect, unfill_zone, update_footprint_value

#### `pcb_parser.py`
**Dead functions (31)**: __init__, _arc_to_sexp, _find_all_elements, _find_element, _footprint_to_sexp, _get_symbol_name, _gr_line_to_sexp, _gr_rect_to_sexp, _is_sexp_list, _line_to_sexp, _pad_to_sexp, _parse_arc, _parse_footprint, _parse_general, _parse_layers, _parse_line, _parse_net, _parse_pad, _parse_property, _parse_rectangle, _parse_text, _parse_track, _parse_via, _parse_zone, _pcb_to_sexp, _property_to_sexp, _rect_to_sexp, _track_to_sexp, _via_to_sexp, _zone_to_sexp, parse_file

#### `validation.py`
**Dead functions (22)**: __init__, __str__, _bbox_spacing, _get_footprint_bbox, _validate_board_outline, _validate_component_placement, _validate_isolated_copper, _validate_net_connectivity, _validate_overlapping_footprints, _validate_tracks, _validate_vias, _validate_zones, add_error, add_info, add_warning, error_count, info_count, is_valid, print_summary, validate_board, validate_pcb, warning_count

#### `footprint_library.py`
**Dead functions (18)**: __init__, _build_index, _discover_system_libraries, _extract_basic_info, _load_or_build_index, _save_index, _sexp_to_dict, footprint_type, get_footprint, get_footprint_cache, get_footprint_data, is_mixed, is_smd, is_tht, list_libraries, refresh_cache, score, search_footprints

#### `kicad_cli.py`
**Dead functions (12)**: __init__, __init__, _find_kicad_cli, export_drill, export_gerbers, export_pos, export_svg, get_kicad_cli, get_version, run_command, run_drc, total_issues

#### `ratsnest_generator.py`
**Dead functions (10)**: __init__, add_ratsnest_to_pcb, calculate_distance, export_ratsnest_report, extract_pad_info, generate_kicad_ratsnest_elements, generate_minimum_spanning_tree, generate_pcb_ratsnest, generate_ratsnest, generate_star_topology

#### `pcb_formatter.py`
**Dead functions (4)**: __init__, _format_list, format, format_pcb

#### `types.py`
**Dead functions (4)**: __repr__, get_library_id, get_property, set_property

### `circuit_synth/pcb/placement/`

#### `force_directed_placement.py`
**Dead functions (23)**: __add__, __init__, __mul__, _build_connection_graph, _build_connectivity_from_board, _calculate_attraction, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_boundary_force, _calculate_group_repulsion, _calculate_repulsion, _connectivity_aware_collision_resolution, _count_inter_group_connections, _enforce_minimum_spacing, _group_by_subcircuit, _initialize_group_positions, _optimize_group_positions, _optimize_rotations, _optimize_subcircuit, _update_group_properties, magnitude, normalize, place

#### `force_directed_placement_fixed.py`
**Dead functions (22)**: __add__, __init__, __mul__, _build_connection_graph, _build_connectivity_from_graph, _calculate_attraction, _calculate_boundary_force, _calculate_group_attraction, _calculate_group_boundary_force, _calculate_group_repulsion, _calculate_repulsion, _connectivity_aware_collision_resolution, _count_inter_group_connections, _enforce_minimum_spacing, _group_by_subcircuit, _initialize_group_positions, _optimize_group_positions, _optimize_rotations, _optimize_subcircuit, _update_group_properties, magnitude, place

#### `courtyard_collision_improved.py`
**Dead functions (22)**: __init__, __init__, __sub__, _bounding_boxes_overlap, _calculate_footprint_bbox, _calculate_signed_area, _get_cached_polygon, _trace_polygon_from_lines, check_collision, contains_point, detect_collisions, dot, expand, get_axes, get_bounding_box, get_collision_vector, get_courtyard_polygon, get_edges, get_footprint_polygon, perp_dot, project_onto_axis, transform

#### `courtyard_collision.py`
**Dead functions (21)**: __init__, __init__, _arcs_to_polygon, _bboxes_overlap, _calculate_footprint_bbox, _calculate_signed_area, _circle_to_polygon, _inflate_polygon, _is_inside_board, _lines_to_polygon, _normalize_vector, _polygons_intersect, _project_polygon, check_collision, check_collision_with_placed, contains_point, find_valid_position, get_bounding_box, get_courtyard_polygon, get_footprint_polygon, transform

#### `hierarchical_placement_v2.py`
**Dead functions (16)**: __init__, _find_best_placement_point, _get_area, _get_combined_bbox_footprints, _get_item_polygon, _get_position, _get_spacing, _group_by_hierarchy, _group_groups, _is_locked, _is_within_board, _pack_group, _place_at_board_edge, _set_position, place, place_components

#### `hierarchical_placement.py`
**Dead functions (16)**: __init__, _bbox_within_board, _find_best_placement_point, _get_area, _get_bbox, _get_combined_bbox, _get_spacing, _group_by_hierarchy, _group_groups, _is_locked, _pack_group, _set_bottom_left, _set_center, _touches, place, place_components

#### `connectivity_driven.py`
**Dead functions (14)**: __init__, _build_connectivity_graph, _calculate_placement_order, _count_crossings, _find_best_position, _find_closest_valid_position, _find_clusters, _find_empty_spot, _identify_critical_nets, _is_valid_position, _lines_intersect, _minimize_crossings, ccw, place

#### `base.py`
**Dead functions (14)**: __init__, _calculate_bbox, area, bbox, hierarchical_path, is_locked, move_to, original_bbox, place, position, reference, set_bottom_left, touches, value

#### `force_directed.py`
**Dead functions (12)**: __init__, _apply_gravity_forces, _apply_repulsion_forces, _apply_spring_forces, _calculate_center, _initialize_positions, _run_placement, _update_positions, add_connection, apply_force_directed_placement, place, reference

#### `grouping.py`
**Dead functions (11)**: __init__, area, bbox, group_by_hierarchy, group_groups, hierarchical_level, hierarchical_level, is_locked, move, set_bottom_left, touches

#### `connection_centric.py`
**Dead functions (10)**: __init__, _analyze_connections, _find_edge_position, _find_nearest_valid_position, _find_optimal_position, _get_subcircuit, _group_by_subcircuit, _is_valid_position, _place_subcircuit, place

#### `bbox.py`
**Dead functions (10)**: area, bottom_left, bottom_right, center, from_points, height, inflate, merge, top_left, width

#### `spiral_placement.py`
**Dead functions (9)**: __init__, _boxes_overlap, _build_connection_graph, _calculate_ideal_position, _find_nearest_valid_position, _get_inflated_bbox, _is_position_valid, _is_within_board, place_components

#### `spiral_hierarchical_placement.py`
**Dead functions (9)**: __init__, _build_connection_map, _calculate_ideal_position, _find_best_placement_point, _get_reference, _is_valid_position, _set_bottom_left, _spiral_search, place

#### `spiral_placement_v2.py`
**Dead functions (6)**: __init__, _build_connection_graph, _calculate_ideal_position, _find_nearest_valid_position, get_placement_info, place_components

#### `utils.py`
**Dead functions (3)**: _estimate_footprint_bbox, calculate_placement_bbox, optimize_component_rotation

### `circuit_synth/pcb/routing/`

#### `dsn_exporter.py`
**Dead functions (17)**: __init__, _add_footprint_definitions, _add_padstack_definitions, _calculate_footprint_bbox, _convert_pad_shape, _extract_board_outline, _extract_components, _extract_layers, _extract_nets, _generate_dsn, _get_footprint_id, _get_kicad_version, _get_pad_net, _rotate_point, _sanitize_net_name, export, export_pcb_to_dsn

#### `ses_importer.py`
**Dead functions (16)**: __init__, __init__, _build_net_map, _import_vias, _import_wires, _parse_network_routes, _parse_resolution, _parse_routes, _parse_session, _parse_vias, _remove_existing_routing, add_via, add_wire, import_routing, import_ses_to_pcb, parse

#### `freerouting_runner.py`
**Dead functions (10)**: __init__, _check_java, _find_freerouting_jar, _monitor_output, _parse_progress, _process_line, get_progress, route, route_pcb, stop

#### `install_freerouting.py`
**Dead functions (7)**: check_java, download_file, download_progress, get_download_url, get_platform_info, install_freerouting, main

#### `freerouting_docker.py`
**Dead functions (4)**: __init__, _check_docker, route, route_pcb_docker

### `circuit_synth/plugins/`

#### `ai_design_bridge.py`
**Dead functions (15)**: __init__, _generate_ai_guided_template, _get_alternative_approaches, _get_component_suggestions, _get_design_recommendations, _get_kicad_plugin_directory, _get_optimization_tips, _get_plugin_path, analyze_existing_circuit, create_ai_assisted_circuit, generate_circuit_with_ai_assistance, get_ai_design_bridge, get_plugin_status, install_plugin, is_plugin_installed

### `circuit_synth/schematic/`

#### `schematic_transform.py`
**Dead functions (30)**: __init__, align_elements, apply, auto_arrange, center, compose, contains_point, distribute_elements, expand, get_current_transform, height, identity, mirror_elements, mirror_x, mirror_y, pop_transform, push_transform, rotate_elements, rotation, scale, scale_elements, transform_component, transform_junction, transform_label, transform_position, transform_text, transform_wire, translate_elements, translation, width

#### `search_engine.py`
**Dead functions (27)**: __init__, __init__, _build_indices, _get_component_field, _matches_pattern, _matches_query, add_criterion, build, combine_with_and, combine_with_or, find_components_in_area, find_duplicate_references, find_power_nets, find_unconnected_pins, get_net_statistics, is_empty, parse_value, search_by_footprint, search_by_value, search_components, search_nets, total_count, trace_net, with_footprint, with_property, with_reference, with_value

#### `hierarchy_navigator.py`
**Dead functions (25)**: __init__, _build_hierarchy_recursive, _check_duplicate_names, _check_missing_files, _check_sheet_pins, _get_schematic_containing_sheet, _load_sheet_schematic, _validate_sheet_connections, add_child, analyze_hierarchy, check_files, count_instances, count_recursive, count_recursive, dfs, find_circular_references, find_node, find_sheet_by_name, get_all_sheets_recursive, get_full_path, get_hierarchy_tree, get_instance_count, get_net_scope, get_sheet_path, validate_hierarchy

#### `design_rule_checker.py`
**Dead functions (24)**: __init__, __str__, _add_violation, _check_duplicate_references, _check_floating_nets, _check_missing_footprints, _check_missing_references, _check_missing_values, _check_net_naming, _check_off_grid, _check_overlapping_components, _check_power_pins, _check_reference_naming, _check_required_properties, _check_text_size, _check_unconnected_pins, _check_wire_junctions, _check_wire_length, _find_wire_intersection, check_schematic, filter_violations, get_summary, get_violations_by_category, is_on_grid

#### `sheet_manager.py`
**Dead functions (21)**: __init__, _calculate_pin_position, _calculate_sheet_size, _find_circular_references, _find_sheet_position, _get_pin_orientation, _index_sheets, _recalculate_pin_positions, _resolve_sheet_path, _validate_filename, add_sheet, add_sheet_pin, create_sheet_from_components, dfs, get_sheet_by_name, get_sheet_contents, get_sheet_hierarchy, remove_sheet, remove_sheet_pin, update_sheet, validate_hierarchy

#### `placement.py`
**Dead functions (21)**: __init__, __init__, _arrange_circular, _arrange_grid, _arrange_horizontal, _arrange_vertical, _check_within_bounds, _estimate_component_size, _estimate_sheet_size, _find_center_position, _find_edge_position, _find_grid_position, _find_next_available_position, _find_next_available_position_with_size, _get_occupied_bounds, arrange_components, bottom, find_position, overlaps, place_element, right

#### `bulk_operations.py`
**Dead functions (21)**: __init__, __init__, _add_property, _delete_components, _duplicate_components, _move_components, _remove_property, _replace_symbol, _update_footprint, _update_property, _update_value, add_operation, affected_count, applies_to, create_footprint_update_operation, create_move_operation, create_operation_batch, create_value_update_operation, execute, execute_operation, get_operation_history

#### `connection_tracer.py`
**Dead functions (20)**: __hash__, __hash__, __init__, __init__, _build_connection_graph, _get_or_create_node, _points_equal, add_edge, add_edge, add_node, add_node, analyze_connectivity, find_all_connections, find_floating_nets, find_path, find_path_between_pins, find_short_circuits, get_net_endpoints, get_node_at, trace_net

#### `net_discovery.py`
**Dead functions (17)**: __init__, __init__, _create_net_info, _is_bus_net, _is_ground_net, _is_power_net, analyze_net_connectivity, discover_all_nets, discover_hierarchical_nets, find_floating_nets, get_member_name, get_net_statistics, identify_bus_nets, is_valid, merge_net_aliases, suggest_net_names, trace_hierarchical_net

#### `wire_manager.py`
**Dead functions (15)**: __init__, _build_pin_connections, _build_wire_database, _find_wires_at_point, _get_component_pins, _get_pin_position, _manhattan_route, _points_equal, add_connection, add_wire_between_points, find_or_create_junction, find_wires_for_pin, get_net_at_point, remove_pin_connections, route_wire

#### `connection_updater.py`
**Dead functions (14)**: __init__, _connect_pin_to_net, _create_net_label, _create_power_symbol, _find_nearest_label, _find_or_create_net_point, _find_pin, _get_component_pins, _get_pin_position, _needs_junction, optimize_wire_routing, remove_floating_wires, update_component_connections, update_net_connections

#### `synchronizer.py`
**Dead functions (14)**: __init__, _add_component, _determine_library_id, _extract_circuit_components, _extract_pin_info, _load_schematic, _load_sheets_recursively, _match_components, _needs_update, _process_matches, _process_unmatched, _save_schematic, get_all_components, sync_with_circuit

#### `sheet_utils.py`
**Dead functions (13)**: _get_pin_side, all_sides, calculate_pin_spacing, calculate_sheet_size_from_content, create_sheet_instance_name, estimate_sheet_complexity, generate_sheet_documentation, group_pins_by_function, match_hierarchical_labels_to_pins, resolve_sheet_filepath, suggest_pin_side, suggest_sheet_position, validate_sheet_filename

#### `label_manager.py`
**Dead functions (12)**: __init__, _build_label_index, _find_wires_near_point, _is_horizontal_wire, auto_position_label, find_labels_at_point, find_labels_by_text, get_label_by_uuid, get_labels_by_type, remove_label, update_label, validate_hierarchical_labels

#### `junction_manager.py`
**Dead functions (12)**: __init__, _add_junction_at_position, _build_junction_index, _find_junction_points, _find_wire_crossings, _remove_junction_at_position, add_junction, find_junctions_in_area, get_junction_at, remove_junction, update_junctions, validate_junctions

#### `component_manager.py`
**Dead functions (12)**: __init__, _generate_reference, clone_component, find_components_by_library, find_components_by_value, get_bounding_box, get_component, list_components, move_component, remove_component, update_component, validate_schematic

#### `project_generator.py`
**Dead functions (11)**: __init__, _copy_blank_project_files, _generate_hierarchical_design, _generate_root_with_unified_placement, _generate_schematic, _generate_simple_design, _generate_sub_sheet, _generate_top_sheet, _get_library_id, _get_pin_position, generate_from_circuit

#### `text_manager.py`
**Dead functions (10)**: __init__, _build_text_index, add_multiline_text, align_texts, find_text_at_point, find_text_by_content, get_all_texts, get_text_by_uuid, remove_text, update_text

#### `wire_router.py`
**Dead functions (10)**: __init__, _line_intersects_rect, _path_intersects_obstacles, _point_on_line, optimize_path, route_bus, route_diagonal, route_direct, route_manhattan, route_smart

#### `connection_utils.py`
**Dead functions (9)**: apply_transformation, distance_between_points, find_pin_by_name, get_pin_position, get_wire_segments, point_on_segment, points_equal, segment_intersection, simplify_points

#### `label_utils.py`
**Dead functions (8)**: calculate_text_bounds, find_connected_labels, format_net_name, get_wire_direction_at_point, group_labels_by_net, suggest_label_for_component_pin, suggest_label_position, validate_hierarchical_label_name

#### `sync_strategies.py`
**Dead functions (7)**: __init__, __init__, __init__, match_components, match_components, match_components, match_components

#### `geometry_utils.py`
**Dead functions (7)**: calculate_label_orientation, calculate_label_position, create_dynamic_hierarchical_label, get_actual_pin_position, get_pin_end_position, get_pins_at_position, transform_pin_to_world

#### `sheet_placement.py`
**Dead functions (6)**: __init__, calculate_pin_positions, calculate_sheet_size, create_sheet_symbols, get_next_position, place_sheet

#### `symbol_geometry.py`
**Dead functions (6)**: __init__, _calculate_symbol_bounds, _get_default_bounds, _update_bounds_from_graphic_element, calculate_text_width, get_symbol_bounds

#### `sync_adapter.py`
**Dead functions (5)**: __init__, _find_schematic, _schematic_has_components, sync_with_circuit, synchronize

#### `net_matcher.py`
**Dead functions (4)**: __init__, _calculate_net_similarity, _get_component_nets, match_by_connections

### `circuit_synth/scripts/`

#### `enable_rust.py`
**Dead functions (1)**: main

### `circuit_synth/simulation/`

#### `simulator.py`
**Dead functions (14)**: __init__, __init__, _convert_to_spice, ac_analysis, dc_analysis, get_current, get_netlist, get_voltage, list_components, list_nodes, list_nodes, operating_point, plot, transient_analysis

#### `converter.py`
**Dead functions (13)**: __init__, _add_capacitor, _add_component, _add_diode, _add_inductor, _add_opamp, _add_power_sources, _add_resistor, _convert_value_to_spice, _extract_voltage_from_net_name, _get_component_nodes, _map_nodes, convert

#### `analysis.py`
**Dead functions (8)**: ac_frequency_response, dc_operating_point, dc_sweep, get_num_points, get_total_points, is_sweep, transient_pulse_response, transient_step_response

### `circuit_synth/tools/`

#### `python_code_generator.py`
**Dead functions (24)**: __init__, _analyze_hierarchical_nets, _determine_net_scope, _find_lowest_common_ancestor, _format_net_summary, _generate_component_code, _generate_flat_code, _generate_hierarchical_circuit_recursive, _generate_main_circuit_code, _generate_main_circuit_code_with_params, _generate_main_file_with_imports, _generate_multiple_files, _generate_project_call, _generate_standalone_subcircuit_file, _generate_subcircuit_code, _generate_subcircuit_code_with_params, _get_ancestors, _get_child_interface_nets, _get_depth, _identify_top_level_circuits, _sanitize_variable_name, generate_hierarchical_code, update_or_create_file, update_python_file

#### `init_existing_project.py`
**Dead functions (19)**: _collect_all_subcircuits_recursive, _recursive_collect, check_for_existing_circuit_synth, convert_kicad_to_circuit_synth, copy_claude_setup, create_backup, create_basic_template, create_project_files, find_kicad_project, generate_circuit_synth_code, generate_hierarchical_circuit_synth_code, generate_hierarchical_main_code, generate_subcircuit_code, main, map_subcircuit_to_target_name, sanitize_net_name, setup_circuit_synth_in_place, update_esp32_with_embedded_circuits, validate_kicad_project

#### `python_to_kicad_sync.py`
**Dead functions (14)**: __init__, __init__, __post_init__, _apply_sync_changes, _create_backup, _generate_final_report, _load_circuit_from_execution, _load_circuit_from_module, _save_report, _validate_inputs, extract_circuit, main, setup_logging, sync

#### `kicad_parser.py`
**Dead functions (14)**: __init__, _analyze_hierarchical_structure, _build_hierarchical_tree, _extract_sheet_blocks, _extract_sheet_instance_blocks, _extract_symbol_blocks, _find_root_schematic, _parse_circuits_from_schematics, _parse_component_block, _parse_schematic_file, _parse_sheet_block, _parse_sheet_instance_block, _parse_sheet_instances, parse_circuits

#### `llm_code_updater.py`
**Dead functions (12)**: __init__, _check_llm_availability, _fallback_update, _generate_component_code, _generate_flat_code, _generate_hierarchical_code, _generate_main_circuit_function, _generate_subcircuit_function, _llm_assisted_update, _prepare_llm_context, _sanitize_variable_name, update_python_file

#### `preparse_kicad_symbols.py`
**Dead functions (11)**: _get_default_kicad_symbol_path, build_symbol_index, clear_cache, extract_symbol_names, find_kicad_symbol_files, main, preparse_specific_libraries, preparse_symbols, preparse_symbols_legacy, show_cache_status, validate_symbol_paths

#### `init_pcb.py`
**Dead functions (8)**: _create_simple_template, create_circuit_synth_structure, create_claude_agent, create_memory_bank, create_readme, find_kicad_files, main, organize_kicad_files

#### `setup_claude.py`
**Dead functions (8)**: check_claude_availability, copy_claude_md, copy_examples, copy_memory_bank, create_claude_config, detect_environment, get_package_data_dir, main

#### `new_pcb.py`
**Dead functions (7)**: _copy_claude_directory, _create_fallback_structure, copy_directory_recursive, copy_example_project_structure, copy_file_with_customization, get_template_content, main

#### `circuit_creator_cli.py`
**Dead functions (6)**: create_circuit_from_file, create_circuit_interactive, create_example_requirements_file, list_circuits_cli, main, use_circuit_cli

#### `kicad_to_python_sync.py`
**Dead functions (5)**: __init__, _create_backup, _resolve_kicad_project_path, main, sync

#### `ai_design_manager.py`
**Dead functions (5)**: cmd_analyze, cmd_generate, cmd_install, cmd_status, main

#### `pcb_tracker_basic.py`
**Dead functions (5)**: cli, init, install_hooks, list, log

#### `kicad_netlist_parser.py`
**Dead functions (4)**: __init__, _parse_components_from_netlist, _parse_nets_from_netlist, parse_netlist

#### `preload_symbols.py`
**Dead functions (4)**: _get_default_kicad_symbol_path, extract_symbol_names, main, preload_all_symbols

### `circuit_synth/validation/`

#### `simple_validator.py`
**Dead functions (8)**: _apply_basic_fixes, _check_circuit_code, _check_circuit_structure, _check_imports, _check_runtime_execution, _extract_imports, get_circuit_design_context, validate_and_improve_circuit

#### `real_time_check.py`
**Dead functions (6)**: check_net_connectivity, extract_components_from_file, main, validate_circuit_file, validate_circuit_functions, validate_component_symbols

## 📝 Analysis Notes

### Caveats and Considerations

1. **Test Coverage**: This analysis is based on a single test run. Functions might be used in:
   - Different execution paths
   - CLI tools and scripts
   - Error handling scenarios
   - Test suites
   - Debugging utilities

2. **Dynamic Calls**: Functions called dynamically (getattr, exec, etc.) won't be detected

3. **External APIs**: Some functions might be part of public APIs used by external code

4. **Development Tools**: Some functions might be used in development workflows

### Recommended Actions

1. **Start with dead modules** - These are safest to remove
2. **Review individual functions** - Check git history and documentation
3. **Add tests** - Before removing, ensure there are no hidden dependencies
4. **Gradual removal** - Remove in small batches and test thoroughly

### Next Steps

1. Review the potentially dead modules first (highest impact, lowest risk)
2. Search for external references to functions before removal
3. Consider adding deprecation warnings before final removal
4. Update this analysis after adding more comprehensive tests

