# Comprehensive Bidirectional Sync Test Scenarios

This document catalogs ALL test scenarios needed for production-ready bidirectional
sync between Python and KiCad. Based on real-world usage analysis.

**Status Key:**
- ✅ Implemented & Passing
- ⚠️ Implemented but Issues
- ❌ Implemented & Failing
- 📋 Planned (not implemented)
- 🔮 Future consideration

---

## Category 1: Basic Operations

### Component CRUD
- ✅ **02_generate:** Create component in Python → KiCad
- ✅ **03_import:** Import component from KiCad → Python
- ✅ **04_properties:** Component properties (ref, value, footprint) preserved
- ✅ **06_add_component:** Add component to existing circuit
- ✅ **07_delete_component:** Remove component from circuit
- ✅ **08_modify_value:** Change component value
- 📋 **Modify footprint:** Change component footprint (0603 → 0805)
- 📋 **Replace component:** Swap component type (R → C)
- 📋 **Duplicate component:** Copy component with new reference
- 📋 **Batch modify:** Change all resistors 0603 → 0805

### Round-Trip Cycles
- ✅ **05_roundtrip:** Simple Python → KiCad → Python
- ❌ **09_manual_position_preservation:** Manual KiCad edits survive Python regen
- ❌ **14_incremental_growth:** Multiple round-trips accumulate correctly
- 📋 **38_multiple_cycles:** 10+ round-trips without degradation
- 📋 **39_incremental_changes:** Modify different aspects each cycle

---

## Category 2: Position & Layout

### Position Setting
- ⚠️ **12_set_position:** Set explicit position in Python
- ❌ **15_move_component:** Move component to new position
- 📋 **16_rotation_preservation:** Rotation (0°, 90°, 180°, 270°)
- 📋 **Position units:** Verify mm/mils/inches consistency

### Position Preservation (CRITICAL)
- ❌ **09_manual_position_preservation:** Manual layout work survives
- 📋 **Position on regenerate:** Adding component doesn't move existing ones
- 📋 **Grid alignment:** Positions snap to KiCad grid correctly
- 📋 **Relative positioning:** Position relative to another component

---

## Category 3: Nets & Connections

### Basic Connections
- ✅ **17_create_net:** Create simple net between two components
- ✅ **22_delete_net:** Remove connection
- ✅ **10_add_to_existing_net:** Add third component to existing net
- ✅ **11_power_rails:** GND and VCC power distribution
- 📋 **18_named_nets:** Named signal nets (MISO, MOSI, SCK)
- 📋 **19_multipoint_net:** 5+ components on same net

### Connection Operations
- 📋 **20_add_connection:** Add pin to existing net
- 📋 **21_remove_connection:** Remove pin from net
- 📋 **23_rename_net:** Rename NET1 → SENSOR_DATA
- 📋 **24_split_net:** Disconnect, creating two separate nets
- 📋 **25_merge_nets:** Connect two separate nets together

### Advanced Connections
- 📋 **Bus connections:** 8-bit bus (D0-D7)
- 📋 **No-connect pins:** Mark unused IC pins as NC
- 📋 **Net name collisions:** Handle duplicate net names
- 📋 **Global labels:** Cross-sheet connections
- 📋 **Junction dots:** Explicit wire junctions

---

## Category 4: Component References & Naming

### Reference Management
- ❌ **13_component_rename:** R1 → R_PULLUP consistency
- 📋 **Auto-annotation:** Let KiCad assign references
- 📋 **Reference conflicts:** Duplicate ref handling
- 📋 **Descriptive names:** R_PULL_UP vs generic R1
- 📋 **Reference ranges:** R100-R199 for specific section

### Special Characters
- 📋 **Unicode names:** µController, Ω, etc.
- 📋 **Spaces in names:** "Pull Up Resistor"
- 📋 **Special chars:** Dashes, underscores, dots

---

## Category 5: Hierarchical Design

### Subcircuits
- 📋 **26_create_subcircuit:** Create hierarchical sheet
- 📋 **27_delete_subcircuit:** Remove hierarchical sheet
- 📋 **28_move_to_subcircuit:** Move component into subcircuit
- 📋 **29_move_from_subcircuit:** Move component out of subcircuit
- 📋 **30_subcircuit_connections:** Hierarchical pins
- 📋 **31_nested_subcircuits:** Subcircuit within subcircuit
- 📋 **32_rename_subcircuit:** Rename hierarchical sheet

### Subcircuit Instances
- 📋 **Multiple instances:** 4 copies of same subcircuit
- 📋 **Instance modification:** Different values per instance
- 📋 **Instance connections:** Wire up multiple instances

---

## Category 6: Multi-Sheet Schematics

### Multiple Pages
- 📋 **58_multi_sheet:** Circuit spread across multiple sheets
- 📋 **Sheet 1-3:** Power, MCU, Sensors on separate sheets
- 📋 **21_global_labels:** Cross-sheet signal connections
- 📋 **Sheet navigation:** Move between sheets in Python
- 📋 **Sheet properties:** Title blocks, revision info

---

## Category 7: Annotations & Documentation

### Text & Labels
- 📋 **33_text_preserved:** Text boxes survive round-trip
- 📋 **34_component_notes:** Component-specific notes
- 📋 **35_sheet_properties:** Title, revision, author
- 📋 **17_review_notes:** Design review comments
- 📋 **37_python_comments:** Python comments → KiCad notes

### Design Information
- 📋 **Version tracking:** Circuit version numbers
- 📋 **Change history:** What changed in each revision
- 📋 **Author information:** Who created what
- 📋 **Design intent:** Why certain choices were made

---

## Category 8: Component Libraries

### Footprints
- 📋 **07_footprint_change:** Change component footprint
- 📋 **Footprint batch:** Change all 0603 → 0805
- 📋 **Footprint missing:** Handle missing footprint
- 📋 **Custom footprint:** User-defined footprint

### Parts & Symbols
- 📋 **08_substitution:** Replace LM358 with TL072
- 📋 **09_generic_to_specific:** Generic R → Specific part number
- 📋 **Part metadata:** Manufacturer, part number, supplier
- 📋 **Symbol variants:** Different symbol representations

---

## Category 9: Error Handling & Edge Cases

### Empty/Partial States
- 📋 **41_empty_circuit:** Zero components
- ✅ **42_single_component_no_connections:** R1 alone
- 📋 **43_no_footprint:** Component without footprint
- 📋 **44_duplicate_refs:** Two components with R1
- 📋 **45_invalid_net_names:** Special characters in net names

### Syntax & Validation
- 📋 **24_partial_circuit:** Circuit with syntax error
- 📋 **25_incomplete:** Component with missing required fields
- 📋 **26_corrupt_file:** Manually edited KiCad file (corrupted)
- 📋 **Validation errors:** Clear error messages

---

## Category 10: Performance & Scale

### Large Circuits
- 📋 **46_large_circuit:** 500+ components
- 📋 **47_very_large:** 1000+ components, 2000+ nets
- 📋 **48_incremental_update:** Change 1 of 500 components
- 📋 **Performance acceptable:** < 5 seconds for 500 components

### Optimization
- 📋 **Differential updates:** Only update changed parts
- 📋 **Caching:** Cache component information
- 📋 **Memory usage:** Handle large circuits efficiently

---

## Category 11: Collaboration Workflows

### Team Scenarios
- 📋 **29_two_people:** Person A (Python) + Person B (KiCad)
- 📋 **30_handoff:** EE → Layout → EE handoff
- 📋 **Merge conflicts:** Resolve concurrent edits
- 📋 **19_version_control:** Git-friendly workflow

### Design Variants
- 📋 **31_design_variants:** Base + WiFi variant + BT variant
- 📋 **32_design_iterations:** v1.0, v1.1, v1.2 evolution
- 📋 **Component sourcing:** Substitute out-of-stock parts

---

## Category 12: PCB Integration

### PCB Workflow
- 📋 **22_schematic_pcb:** Schematic changes → PCB update
- 📋 **23_back_annotation:** PCB gate swap → Schematic
- 📋 **PCB annotations:** Preserve PCB-specific data
- 📋 **55_netlist:** Netlist generation and consistency

---

## Category 13: Special KiCad Features

### KiCad-Specific
- 📋 **49_power_symbols:** Power symbols (VCC, GND icons)
- 📋 **50_no_connect:** No-connect flags on pins
- 📋 **51_bus_connections:** KiCad bus notation
- 📋 **52_hierarchical_labels:** Sheet input/output pins
- 📋 **53_junction_dots:** Wire junction indicators
- 📋 **54_wire_styles:** Bus vs normal wire styles

---

## Category 14: Real Production Workflows

### Design Process
- 📋 **Breadboard → Prototype:** Iterative development
- 📋 **Design review cycle:** Review → Fix → Review
- 📋 **Copy-paste patterns:** Reuse circuit blocks
- 📋 **Bottom-up design:** Build subcircuits first
- 📋 **Top-down design:** Start with architecture

### Manufacturing
- 📋 **33_component_sourcing:** Handle part availability
- 📋 **BOM generation:** Bill of materials
- 📋 **DFM checks:** Design for manufacturing
- 📋 **Pick and place:** PCB assembly data

---

## Category 15: Testing & Simulation

### Verification
- 📋 **34_simulation:** SPICE simulation setup preserved
- 📋 **35_drc:** Design rule check results
- 📋 **Test points:** Test point annotations
- 📋 **Signal integrity:** Transmission line analysis

---

## Summary Statistics

**Total Scenarios Identified:** 100+

**Implemented:**
- ✅ Passing: 9 tests
- ⚠️ Issues: 4 tests
- ❌ Failing: 3 tests
- **Total: 16 tests**

**Planned (High Priority):** 20+ scenarios
**Future Consideration:** 60+ scenarios

---

## Implementation Priority

### Phase 1.6: Fix Critical Issues (IMMEDIATE)
1. Fix manual position preservation (test 09)
2. Fix import-modify-regenerate cycle (tests 13, 14)
3. Investigate position units (test 12, 15)

### Phase 2: Core Workflows (NEXT)
4. Footprint changes (batch modify)
5. Component substitution
6. Multiple round-trips stability
7. Named signal nets
8. No-connect handling

### Phase 3: Advanced Features
9. Hierarchical subcircuits
10. Multi-sheet schematics
11. Bus connections
12. Large circuit performance

### Phase 4: Production Polish
13. Team collaboration scenarios
14. Design variants
15. Version control integration
16. Manufacturing outputs

---

## Test Coverage Goals

**Phase 1 Target:** 20 tests (basic operations) - ✅ 16/20 done
**Phase 2 Target:** 40 tests (workflows + advanced)
**Phase 3 Target:** 60 tests (production scenarios)
**Phase 4 Target:** 80+ tests (comprehensive)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-26
**Maintainer:** circuit-synth development team
