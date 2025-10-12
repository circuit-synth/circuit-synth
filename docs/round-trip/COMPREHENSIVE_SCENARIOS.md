# Comprehensive Round-Trip Test Scenarios
## Real-World Electronics Design Workflows

This document explores **all** practical scenarios where bi-directional updates between Python and KiCad are critical for professional electronics design.

---

## 1. Individual Designer Workflows

### 1.1 Prototyping & Rapid Iteration
**Scenario:** Designer testing multiple component value combinations

**Workflow:**
1. Generate voltage regulator in Python (3.3V output)
2. Test → realize need 5V instead
3. Update output voltage in Python code
4. Meanwhile, added test points in KiCad for oscilloscope
5. Re-generate → **Test points must be preserved**

**Tests Needed:**
- [ ] Value changes with test point preservation
- [ ] Multiple rapid regenerations (10+ cycles)
- [ ] Test point/probe marker preservation

### 1.2 PCB Layout Feedback Loop
**Scenario:** Schematic changes driven by PCB layout constraints

**Workflow:**
1. Generate initial schematic
2. Start PCB layout, realize connector on wrong side
3. In KiCad: Flip connector, add mounting holes, add board outline notes
4. In Python: Update other circuit functionality
5. Re-generate → **Mechanical additions must be preserved**

**Tests Needed:**
- [ ] Connector orientation changes preserved
- [ ] Mounting hole preservation
- [ ] Graphical board outline preserved
- [ ] Text annotations on schematic preserved

### 1.3 Multi-Page Schematic Organization
**Scenario:** Design grows too large for single page

**Workflow:**
1. Generate flat 100-component design (single page)
2. Manually split into sheets in KiCad (Power, MCU, Sensors, I/O)
3. Move components between sheets
4. Add hierarchical labels for inter-sheet connections
5. Update component values in Python
6. Re-generate → **Sheet structure must be preserved**

**Tests Needed:**
- [ ] Manual sheet creation preserved
- [ ] Component sheet assignments preserved
- [ ] Hierarchical labels preserved
- [ ] Sheet names preserved
- [ ] Sheet order preserved

### 1.4 Design Calculation Documentation
**Scenario:** Embedding design decisions in schematic

**Workflow:**
1. Generate power supply circuit
2. Add text boxes with calculations:
   - "Cout = 10μF (ESR < 50mΩ for stability)"
   - "Iout_max = 2A, thermal calc: Tj = 85°C"
   - "Formula: Vout = Vref * (1 + R2/R1)"
3. Update component values based on calculations
4. Re-generate → **All calculations must be preserved**

**Tests Needed:**
- [ ] Text box preservation
- [ ] Unicode characters (μ, Ω, °) preserved
- [ ] Multi-line text preserved
- [ ] Text formatting (bold, size) preserved
- [ ] Formula annotations preserved

---

## 2. Team Collaboration Workflows

### 2.1 Hardware/Software Engineer Split
**Scenario:** Different engineers working on same schematic

**Workflow:**
1. **HW Engineer:** Generates MCU base circuit in Python
2. **SW Engineer:** Opens KiCad, adds:
   - JTAG debug header
   - UART debug connector
   - Status LEDs
   - Reset button
3. **HW Engineer:** Updates MCU pin assignments in Python
4. Re-generate → **SW additions must be preserved**

**Tests Needed:**
- [ ] Manual component additions preserved
- [ ] Components not in Python preserved
- [ ] New net connections preserved
- [ ] Reference designators for manual parts preserved

### 2.2 Design Review & Annotation
**Scenario:** Reviewer adds feedback directly in schematic

**Workflow:**
1. Designer generates circuit
2. Reviewer opens in KiCad, adds:
   - Text boxes: "Q: Why 10k pull-up? Too high for fast I2C?"
   - Text boxes: "WARNING: R5 power rating insufficient"
   - Highlights problem areas with graphic boxes
   - Marks DNP flag on optional components
3. Designer fixes issues in Python
4. Re-generate → **Review comments preserved until designer addresses**

**Tests Needed:**
- [ ] Review comment text boxes preserved
- [ ] Graphic highlighting (rectangles, circles) preserved
- [ ] DNP flags preserved
- [ ] Multiple reviewers adding comments concurrently

### 2.3 Schematic Librarian / Standardization
**Scenario:** Company enforces standard symbols/footprints

**Workflow:**
1. Engineer generates circuit with generic Device:R symbols
2. Librarian updates to company-specific symbols
3. Librarian adds custom fields: MPN, Supplier, Cost
4. Engineer continues development in Python
5. Re-generate → **Symbol changes and custom fields preserved**

**Tests Needed:**
- [ ] Symbol substitution preserved (Device:R → CompanyLib:R_0603)
- [ ] Custom component fields preserved
- [ ] Field visibility settings preserved
- [ ] Symbol orientation changes preserved

### 2.4 Mechanical Integration
**Scenario:** Mechanical engineer adds constraints

**Workflow:**
1. Electrical engineer generates circuit
2. Mechanical engineer adds in KiCad:
   - Board outline (specific dimensions)
   - Mounting hole locations
   - Connector position constraints
   - Keep-out zones for enclosure bosses
3. Electrical engineer updates circuit
4. Re-generate → **Mechanical constraints preserved**

**Tests Needed:**
- [ ] Graphic lines/shapes preserved
- [ ] Mounting holes preserved
- [ ] Position constraints preserved
- [ ] Keep-out zone annotations preserved

---

## 3. Bi-Directional Sync (CRITICAL GAP!)

### 3.1 KiCad → Python Import
**Scenario:** Existing KiCad project needs Python management

**Workflow:**
1. Start with hand-drawn KiCad schematic
2. Import to Python → generate `.py` file
3. Verify Python code matches schematic
4. Continue development in Python
5. Export back to KiCad

**Tests Needed:**
- [ ] **Import KiCad schematic to Python code**
- [ ] Component extraction with correct references
- [ ] Net extraction with correct names
- [ ] Property extraction (value, footprint, custom fields)
- [ ] Hierarchy extraction (sheets, instances)
- [ ] Position import (for re-generation)

### 3.2 Round-Trip: Python → KiCad → Python
**Scenario:** Continuous bidirectional workflow

**Workflow:**
1. Generate circuit in Python
2. Add decoupling caps manually in KiCad
3. **Import KiCad changes back to Python** (sync)
4. Python now includes decoupling caps
5. Add another component in Python
6. Export to KiCad
7. Manual and generated components coexist

**Tests Needed:**
- [ ] **Python → KiCad → Python round-trip** (CRITICAL!)
- [ ] Manual KiCad additions sync to Python
- [ ] Python updates sync to KiCad
- [ ] Continuous back-and-forth updates
- [ ] No component duplication
- [ ] Reference designator conflict resolution

### 3.3 Incremental Sync
**Scenario:** Update only changed components

**Workflow:**
1. Large circuit (200+ components)
2. Update power supply section in Python
3. Sync only power supply → KiCad
4. Leave rest of circuit untouched
5. Update sensors in KiCad
6. Sync only sensors → Python

**Tests Needed:**
- [ ] Selective component sync (only changed)
- [ ] Unchanged components untouched
- [ ] Performance with large schematics
- [ ] Conflict detection (simultaneous edits)

### 3.4 Vendor Reference Design Integration
**Scenario:** Starting from vendor KiCad example

**Workflow:**
1. Download vendor reference design (KiCad format)
2. **Import to Python** for customization
3. Modify in Python (change MCU, add features)
4. Export back to KiCad for manufacturing
5. Share modified design

**Tests Needed:**
- [ ] Import arbitrary KiCad schematic
- [ ] Preserve vendor annotations
- [ ] Export with modifications
- [ ] Round-trip accuracy (no loss)

---

## 4. Hierarchical Design Scenarios

### 4.1 Flat → Hierarchical Refactoring
**Scenario:** Organizing complex design with sheets

**Workflow:**
1. Generate 150-component flat design
2. Manually create hierarchical sheets in KiCad:
   - Sheet: "Power Supply"
   - Sheet: "MCU & Peripherals"
   - Sheet: "Sensor Array"
   - Sheet: "Communication"
3. Move components to appropriate sheets
4. Create hierarchical labels for connections
5. Update Python code (still flat)
6. Re-generate → **Entire hierarchy must be preserved**

**Tests Needed:**
- [ ] Sheet structure preserved
- [ ] Component-to-sheet mapping preserved
- [ ] Hierarchical labels preserved
- [ ] Sheet instance paths preserved
- [ ] Sheet pins and connections preserved

### 4.2 Multi-Unit Component Distribution
**Scenario:** IC with multiple units across sheets

**Workflow:**
1. Generate circuit with quad op-amp
2. Manually distribute units in KiCad:
   - Unit A on "Audio" sheet
   - Unit B on "Filters" sheet
   - Unit C on "Comparators" sheet
   - Unit D unused (marked NC)
3. Add power pins on separate "Power" sheet
4. Update component values in Python
5. Re-generate → **Unit distribution must be preserved**

**Tests Needed:**
- [ ] Multi-unit component handling
- [ ] Unit distribution across sheets
- [ ] Power unit placement
- [ ] Unused unit marking (NC)

### 4.3 Repeated Sheet Instances
**Scenario:** Same subcircuit instantiated multiple times

**Workflow:**
1. Create sensor interface subcircuit in Python
2. Generate schematic
3. In KiCad: Create hierarchical sheet "Sensor_Interface"
4. Instantiate 4 times (4 sensors)
5. Each instance has unique reference designators
6. Update sensor interface in Python
7. Re-generate → **All instances update, unique refs preserved**

**Tests Needed:**
- [ ] Repeated sheet instance handling
- [ ] Instance-specific reference designators
- [ ] Synchronize changes across instances
- [ ] Instance-specific customizations

---

## 5. Component Property Management

### 5.1 Custom Fields & Metadata
**Scenario:** BOM management with custom fields

**Workflow:**
1. Generate circuit
2. Add custom fields in KiCad:
   - MPN (Manufacturer Part Number)
   - Supplier
   - Cost
   - Lead_Time
   - Alternative_Parts
3. Populate fields for BOM generation
4. Update circuit in Python
5. Re-generate → **All custom fields must be preserved**

**Tests Needed:**
- [ ] Custom field preservation
- [ ] Field values preserved
- [ ] Field visibility settings preserved
- [ ] Field positions preserved

### 5.2 DNP & Assembly Variants
**Scenario:** Multiple assembly configurations

**Workflow:**
1. Generate base circuit
2. Create variants in KiCad:
   - Variant "Basic": R10, R11 = DNP
   - Variant "Advanced": R10, R11 = populated
   - Variant "Prototype": Additional test points
3. Mark components with DNP flags
4. Update base circuit in Python
5. Re-generate → **DNP flags and variants preserved**

**Tests Needed:**
- [ ] DNP (Do Not Populate) flag preservation
- [ ] Assembly variant configurations
- [ ] Variant-specific component values
- [ ] BOM exclude flags (in_bom, on_board)

### 5.3 Component Substitution Tracking
**Scenario:** Tracking alternate parts for supply chain

**Workflow:**
1. Generate circuit with ideal components
2. In KiCad, add alternates due to availability:
   - R1: Original: RC0603FR-0710KL, Alt: ERJ-3EKF1002V
   - C1: Original: GRM188R71C104KA01D, Alt: CL10B104KB8NNNC
3. Add custom field "Alternates"
4. Update circuit values in Python
5. Re-generate → **Alternate part tracking preserved**

**Tests Needed:**
- [ ] Alternate part field preservation
- [ ] Multiple alternates per component
- [ ] Availability notes preserved

---

## 6. Net Management & Power Distribution

### 6.1 Power Net Renaming
**Scenario:** Specific power rail naming

**Workflow:**
1. Generate circuit with generic VCC, GND
2. Rename in KiCad to specific rails:
   - VCC → VDD_3V3
   - VCC_2 → VDD_IO_1V8
   - GND → GND (no change)
   - GND_2 → AGND (analog ground)
3. Update Python code
4. Re-generate → **Net names must be preserved**

**Tests Needed:**
- [ ] Net renaming preservation
- [ ] Power net name changes
- [ ] Multiple power domains
- [ ] Analog/digital ground separation

### 6.2 Net Classes & Routing Rules
**Scenario:** Defining PCB routing constraints in schematic

**Workflow:**
1. Generate circuit
2. Define net classes in KiCad:
   - Class "Power": VCC nets, min 0.5mm width
   - Class "Diff_Pair": USB D+/D-, 90Ω impedance
   - Class "Signal": Default
3. Assign nets to classes
4. Update circuit in Python
5. Re-generate → **Net classes preserved**

**Tests Needed:**
- [ ] Net class assignments preserved
- [ ] Net class parameters preserved
- [ ] Differential pair pairing preserved

### 6.3 Power Symbol Distribution
**Scenario:** Adding power symbols for clarity

**Workflow:**
1. Generate circuit
2. Add power symbols throughout in KiCad:
   - VCC symbols near each IC
   - GND symbols near decoupling caps
   - Power flags on supply inputs
3. Update circuit in Python
4. Re-generate → **All power symbols preserved**

**Tests Needed:**
- [ ] Power symbol (VCC/GND) preservation
- [ ] Power flag preservation
- [ ] Symbol positioning preserved

---

## 7. Annotation & Documentation

### 7.1 Design Notes & Calculations
**Scenario:** Embedding engineering rationale

**Workflow:**
1. Generate circuit
2. Add extensive notes in KiCad:
   - Text: "C1 = 10μF (ESR < 50mΩ for loop stability)"
   - Text: "R1/R2 voltage divider: Vout = 3.3V * (1 + R2/R1)"
   - Text: "Freq = 1/(2π * R * C) = 1.59kHz"
   - Text: "Power dissipation: P = I²R = 0.1W"
3. Update component values
4. Re-generate → **All notes preserved**

**Tests Needed:**
- [ ] Multi-line text preservation
- [ ] Mathematical symbols (π, ², ∞)
- [ ] Formula preservation
- [ ] Link to external documents

### 7.2 Assembly & Manufacturing Notes
**Scenario:** Instructions for technicians

**Workflow:**
1. Generate circuit
2. Add assembly notes:
   - "Install C1 last (polarity sensitive!)"
   - "R5 gets hot - use 1W rated part"
   - "J1 orientation: Pin 1 toward edge"
   - Arrows pointing to polarity marks
3. Update circuit
4. Re-generate → **Assembly notes preserved**

**Tests Needed:**
- [ ] Assembly instruction text boxes
- [ ] Polarity indicators (arrows, symbols)
- [ ] Warning/caution notes
- [ ] Assembly sequence numbers

### 7.3 Regulatory & Compliance
**Scenario:** Safety markings and certifications

**Workflow:**
1. Generate circuit
2. Add compliance markings:
   - "⚡ HIGH VOLTAGE - 240VAC"
   - "UL Listed"
   - "CE Certified"
   - Safety spacing requirements
3. Update circuit
4. Re-generate → **Compliance markings preserved**

**Tests Needed:**
- [ ] Warning symbols preserved
- [ ] Certification marks preserved
- [ ] Safety rating text preserved
- [ ] Regulatory notes preserved

---

## 8. Graphics & Visual Elements

### 8.1 Signal Flow Diagrams
**Scenario:** Visual documentation of signal path

**Workflow:**
1. Generate circuit
2. Add visual aids in KiCad:
   - Arrows showing signal direction
   - Block diagram overlay
   - Flow indicators
   - Functional grouping boxes
3. Update component values
4. Re-generate → **All graphics preserved**

**Tests Needed:**
- [ ] Graphic lines preserved
- [ ] Graphic rectangles preserved
- [ ] Graphic circles/arcs preserved
- [ ] Arrows/polylines preserved
- [ ] Line styles (dashed, dotted) preserved

### 8.2 Board Outline & Mechanical
**Scenario:** Schematic-level mechanical documentation

**Workflow:**
1. Generate circuit
2. Draw in KiCad:
   - Board outline with dimensions
   - Mounting hole locations
   - Connector position constraints
   - Height restriction zones
3. Update circuit
4. Re-generate → **Mechanical drawings preserved**

**Tests Needed:**
- [ ] Board outline graphics preserved
- [ ] Dimension lines preserved
- [ ] Mechanical constraint annotations preserved

---

## 9. Simulation & Analysis

### 9.1 SPICE Simulation Setup
**Scenario:** Circuit simulation configuration

**Workflow:**
1. Generate circuit
2. Add SPICE directives in KiCad:
   - .tran directive
   - Voltage sources for simulation
   - Current probes
   - Analysis commands
3. Run simulation, tune values
4. Update values in Python
5. Re-generate → **SPICE setup preserved**

**Tests Needed:**
- [ ] SPICE directive preservation
- [ ] Simulation sources preserved
- [ ] Probe placement preserved
- [ ] Analysis command preservation

### 9.2 Test Bench Components
**Scenario:** Separating production vs. test components

**Workflow:**
1. Generate production circuit
2. Add test fixtures in KiCad:
   - Signal generators (not in production)
   - Oscilloscope probes
   - Test load resistors (marked DNP for production)
3. Update production circuit
4. Re-generate → **Test fixtures preserved, marked non-production**

**Tests Needed:**
- [ ] Test component marking (DNP, Exclude from BOM)
- [ ] Test vs production component separation
- [ ] Test point preservation

---

## 10. Version Control & Collaboration

### 10.1 Git Merge Scenarios
**Scenario:** Concurrent edits need merging

**Workflow:**
1. **Branch A (Engineer 1):** Updates Python, regenerates
2. **Branch B (Engineer 2):** Adds components in KiCad
3. Both push to Git
4. Merge conflict in .kicad_sch file
5. Need resolution strategy

**Tests Needed:**
- [ ] **Conflict detection in round-trip**
- [ ] Merge conflict reporting
- [ ] Safe merge strategies
- [ ] Diff visualization for changes

### 10.2 Change Tracking & Auditing
**Scenario:** Understanding what changed

**Workflow:**
1. Generate circuit (version 1)
2. Multiple updates in KiCad
3. Re-generate from Python (version 2)
4. Need report: "What changed between v1 and v2?"

**Tests Needed:**
- [ ] Change detection (before/after diff)
- [ ] Change summary report
- [ ] "Which components were added/removed/modified?"
- [ ] "Which manual edits were preserved/lost?"

---

## 11. Performance & Scale

### 11.1 Large Schematic Performance
**Scenario:** Enterprise-scale designs

**Workflow:**
1. Generate 500+ component schematic
2. 20+ hierarchical sheets
3. Complex net connectivity
4. Update single component value
5. Re-generate → **Fast incremental update**

**Tests Needed:**
- [ ] Performance with 100+ components
- [ ] Performance with 500+ components
- [ ] Performance with 1000+ components
- [ ] Performance with 10+ sheets
- [ ] Incremental update speed

### 11.2 Rapid Iteration Performance
**Scenario:** Design iteration loop

**Workflow:**
1. Generate circuit
2. Test → update value
3. Re-generate
4. Test → update value
5. Repeat 50 times

**Tests Needed:**
- [ ] 10 consecutive regenerations < 5 seconds
- [ ] 50 consecutive regenerations < 30 seconds
- [ ] No memory leaks
- [ ] No corruption after many cycles

---

## 12. Edge Cases & Robustness

### 12.1 Unicode & International
**Scenario:** Non-ASCII characters

**Workflow:**
1. Component values: "10μF", "100Ω", "±5%"
2. Notes in Japanese, Chinese, Cyrillic
3. Designer names with accents: "José García"
4. Re-generate → **All unicode preserved**

**Tests Needed:**
- [ ] Greek symbols (μ, Ω, π, Σ)
- [ ] Math symbols (±, ≤, ≥, ≈)
- [ ] Superscripts/subscripts
- [ ] CJK characters
- [ ] Accented characters

### 12.2 Empty & Minimal Schematics
**Scenario:** Edge cases

**Workflow:**
1. Empty schematic (no components)
2. Single component schematic
3. Components with no connections
4. Re-generate → **Handle gracefully**

**Tests Needed:**
- [ ] Empty schematic generation
- [ ] Single component
- [ ] Disconnected components
- [ ] Missing references

### 12.3 Malformed Input Handling
**Scenario:** Corrupted or invalid data

**Workflow:**
1. Manually edit .kicad_sch with invalid S-expressions
2. Attempt to update
3. Should detect corruption

**Tests Needed:**
- [ ] Invalid S-expression detection
- [ ] Missing UUID handling
- [ ] Duplicate reference handling
- [ ] Circular reference detection

---

## 13. Real-World Complex Projects

### 13.1 Multi-Board System
**Scenario:** Complete product with multiple PCBs

**Workflow:**
1. System: Main board + sensor board + power board
2. Shared connectors between boards
3. Generate all boards in Python
4. Customize each board in KiCad
5. Update system-level changes in Python
6. Re-generate all → **Board-specific customizations preserved**

**Tests Needed:**
- [ ] Multiple projects sharing components
- [ ] Cross-board connector consistency
- [ ] Independent board customizations
- [ ] System-level update propagation

### 13.2 Product Family Variants
**Scenario:** Product line with shared base design

**Workflow:**
1. Base circuit in Python (common to all)
2. Variant 1: Add Bluetooth module
3. Variant 2: Add WiFi module
4. Variant 3: Basic (no wireless)
5. Update base circuit → **All variants update**

**Tests Needed:**
- [ ] Variant management
- [ ] Base circuit changes propagate
- [ ] Variant-specific additions preserved
- [ ] Shared component synchronization

---

## Priority Matrix

### P0 - Must Have (Blocking Release)
1. ✅ **Position preservation** - DONE
2. ✅ **Wire preservation** - DONE
3. ✅ **Label preservation** - DONE
4. ⚠️ **Value updates** - PARTIAL (failing in some tests)
5. ❌ **Footprint updates** - FAILING
6. ❌ **Component addition/removal** - FAILING
7. ❌ **Hierarchical sheet preservation** - NOT TESTED
8. ❌ **Text box preservation** - NOT TESTED

### P1 - Should Have (Next Release)
9. ❌ **KiCad → Python import** - MISSING FEATURE
10. ❌ **Custom field preservation** - NOT TESTED
11. ❌ **DNP flag preservation** - NOT TESTED
12. ❌ **Power symbol preservation** - FAILING
13. ❌ **Net name preservation** - NOT TESTED
14. ❌ **Component rotation** - FAILING
15. ❌ **Graphics preservation** - NOT TESTED

### P2 - Nice to Have (Future)
16. ❌ **SPICE directive preservation**
17. ❌ **Net class preservation**
18. ❌ **Multi-unit component distribution**
19. ❌ **Change tracking/diff**
20. ❌ **Conflict detection**

---

## Test Implementation Strategy

### Phase 1: Fix Existing Failures (Week 1)
- Fix value update propagation
- Fix footprint update propagation
- Fix component addition
- Get all basic tests passing

### Phase 2: Hierarchical Support (Week 2)
- Sheet structure preservation
- Component-to-sheet mapping
- Hierarchical labels
- Multi-page schematics

### Phase 3: Bi-Directional Sync (Week 3-4)
- **KiCad → Python import** (NEW FEATURE)
- Round-trip Python → KiCad → Python
- Incremental sync
- Conflict detection

### Phase 4: Annotations & Metadata (Week 5)
- Text box preservation
- Custom fields
- DNP flags
- Graphics preservation

### Phase 5: Advanced Features (Week 6+)
- Net management
- SPICE integration
- Performance optimization
- Variant management

---

## Conclusion

The current round-trip system covers ~20% of real-world scenarios. The **biggest gap** is bi-directional sync (KiCad → Python), which is critical for team workflows and legacy project integration.

**Immediate Next Steps:**
1. Fix failing basic tests (value/footprint updates)
2. Add hierarchical sheet tests
3. Implement **KiCad → Python import** (major feature)
4. Add text box/annotation preservation
5. Performance testing with large schematics
