# Bidirectional Update Test Cases

## Test Project: Simple Voltage Divider
- Two resistors (R1, R2) with value "330"
- Three nets: +5V, Vout, GND
- Simple series connection: +5V → R1 → R2 → GND

## Core Test Cases

### 1. Basic Update Scenarios

#### Test 1.1: Add Component (Python → KiCad)
- **Initial**: R1, R2 in circuit
- **Change**: Add capacitor C1 in Python
- **Expected**: C1 appears in KiCad without disrupting R1, R2 positions
- **Verify**: Existing component positions preserved

#### Test 1.2: Remove Component (Python → KiCad)
- **Initial**: R1, R2, C1 in circuit
- **Change**: Remove C1 from Python
- **Expected**: C1 removed from KiCad, R1, R2 unchanged
- **Verify**: No orphaned nets or connections

#### Test 1.3: Update Component Value (Python → KiCad)
- **Initial**: R1 = "330"
- **Change**: R1 = "1k" in Python
- **Expected**: R1 value updates, position preserved
- **Verify**: Reference designator and position unchanged

#### Test 1.4: Change Component Footprint (Python → KiCad)
- **Initial**: R1 footprint = "R_0805_2012Metric"
- **Change**: R1 footprint = "R_0603_1608Metric"
- **Expected**: Footprint updates, schematic position preserved
- **Verify**: Component symbol and connections intact

### 2. Net Connection Tests

#### Test 2.1: Add Net Connection
- **Initial**: R1 connected to +5V and Vout
- **Change**: Add connection from Vout to new test point
- **Expected**: New connection appears without disrupting existing wires
- **Verify**: Wire routing preserved where possible

#### Test 2.2: Remove Net Connection
- **Initial**: Multiple components on Vout net
- **Change**: Disconnect one component from Vout
- **Expected**: Connection removed, other connections preserved
- **Verify**: Net still exists if other connections remain

#### Test 2.3: Rename Net
- **Initial**: Net named "Vout"
- **Change**: Rename to "SIGNAL_OUT"
- **Expected**: Net label updates throughout schematic
- **Verify**: All connections maintained

### 3. Round-Trip Tests

#### Test 3.1: Python → KiCad → Python
- **Initial**: Original Python circuit
- **Process**: Export to KiCad, then import back to Python
- **Expected**: Functionally identical Python code
- **Verify**: Components, nets, connections all match

#### Test 3.2: KiCad → Python → KiCad
- **Initial**: Manually edited KiCad schematic
- **Process**: Import to Python, then export back to KiCad
- **Expected**: Component positions preserved
- **Verify**: Manual edits (positions, labels) maintained

### 4. Manual Edit Preservation

#### Test 4.1: Preserve Component Positions
- **Initial**: Components manually arranged in KiCad
- **Change**: Update values/footprints from Python
- **Expected**: Positions remain exactly as placed
- **Verify**: X,Y coordinates unchanged

#### Test 4.2: Preserve Wire Routing
- **Initial**: Manually routed wires in KiCad
- **Change**: Update component properties from Python
- **Expected**: Wire paths unchanged
- **Verify**: Junction points and bends preserved

#### Test 4.3: Preserve Text Annotations
- **Initial**: Manual text labels and notes in KiCad
- **Change**: Update circuit from Python
- **Expected**: All text annotations remain
- **Verify**: Position and content unchanged

## Edge Cases and Failure Modes

### Component Matching Edge Cases

#### Edge 1: Reference Designator Changes
- **Scenario**: R1 becomes R5 after renumbering
- **Challenge**: Match component across updates
- **Solution**: Use symbol+value+footprint as canonical ID
- **Test**: Verify position preserved despite ref change

#### Edge 2: Duplicate Components
- **Scenario**: Two identical resistors (same symbol, value, footprint)
- **Challenge**: Which one to update?
- **Solution**: Use position + properties for matching
- **Test**: Both components handled correctly

#### Edge 3: Symbol Library Changes
- **Scenario**: "Device:R" → "Resistor:R_US"
- **Challenge**: Component no longer matches
- **Solution**: Fuzzy matching on symbol basename
- **Test**: Component still recognized and updated

### Placement Edge Cases

#### Edge 4: No Space for New Components
- **Scenario**: Schematic page is full
- **Challenge**: Where to place new components?
- **Solution**: Extend schematic bounds or create new sheet
- **Test**: Components don't overlap existing work

#### Edge 5: Component Collision
- **Scenario**: New component would overlap existing one
- **Challenge**: Find alternative placement
- **Solution**: Grid search for open space
- **Test**: No overlapping components

### Net Edge Cases

#### Edge 6: Orphaned Nets
- **Scenario**: All components removed from a net
- **Challenge**: Should net be deleted?
- **Solution**: Remove net if no connections remain
- **Test**: No dangling net labels

#### Edge 7: Net Merge/Split
- **Scenario**: Two nets merged or one net split
- **Challenge**: Preserve wire routing
- **Solution**: Keep existing wire segments where valid
- **Test**: Minimal visual disruption

### Special Symbol Edge Cases

#### Edge 8: Power Symbol vs Net Label
- **Scenario**: User replaces net labels with power symbols in KiCad
- **Challenge**: Python doesn't have power symbol concept
- **Solution**: Treat power symbols as named nets in Python
- **Test**: Round-trip preserves functionality

#### Edge 9: Net Name Change
- **Scenario**: User renames net in Python code (e.g., "Vout" → "SIGNAL_OUT")
- **Challenge**: Should preserve wire routing but update net labels
- **Solution**: Update net names throughout schematic, preserve physical routing
- **Implementation**: Map old net name to new net name, update labels only

### File Format Edge Cases

#### Edge 10: KiCad Version Mismatch
- **Scenario**: Python generates v9, user has v8
- **Challenge**: Format compatibility
- **Solution**: Target minimum KiCad version
- **Test**: Files open in target version

#### Edge 11: Corrupted Sync Metadata
- **Scenario**: .circuit_synth_sync.json is invalid
- **Challenge**: Can't match components
- **Solution**: Fallback to best-effort matching
- **Test**: Graceful degradation

### Performance Edge Cases

#### Edge 12: Large Circuits (1000+ components)
- **Scenario**: Complex board with many components
- **Challenge**: Matching and placement performance
- **Solution**: Optimize with spatial indexing
- **Test**: Sync completes in reasonable time

## User Modification Preservation Requirements

### What MUST Be Preserved in KiCad
When Python circuit logic hasn't changed (canonical circuit is same):
1. **Component Positions** - Never move components unless Python explicitly changes them
2. **Wire Routing** - All user-drawn wires, junctions, and connections
3. **Text Annotations** - Any user-added labels, notes, or documentation
4. **Power Symbols** - User's choice of power symbol vs net label
5. **Graphical Elements** - Lines, boxes, images added by user
6. **Sheet Organization** - User's hierarchical sheet arrangement
7. **Component Orientation** - Rotation angles of components
8. **Reference Designators** - If user manually changed them

## Specific Test Scenarios for simple_voltage_divider

### Scenario 1: Add Bypass Capacitor
```python
# Modify main.py to add C1 across R2
capacitor = Component(symbol="Device:C", ref="C", value="100nF",
                    footprint="Capacitor_SMD:C_0603_1608Metric")
capacitor[1] += resistor2[1]  # Connect to junction
capacitor[2] += gnd           # Connect to ground
```
- Verify: C1 placed without overlapping R1 or R2

### Scenario 2: Change Resistor Values
```python
# Change R1 from 330 to 1k, R2 from 330 to 2k2
resistor1 = Component(symbol="Device:R", ref="R", value="1k", ...)
resistor2 = Component(symbol="Device:R", ref="R2", value="2k2", ...)
```
- Verify: Values update, positions unchanged

### Scenario 3: Add Test Points
```python
# Add test points to Vin and Vout
tp_vin = Component(symbol="TestPoint:TestPoint", ref="TP", ...)
tp_vout = Component(symbol="TestPoint:TestPoint", ref="TP", ...)
```
- Verify: Test points placed in available space

### Scenario 4: Convert to Hierarchical
```python
# Wrap divider in subcircuit
@subcircuit
def voltage_divider_module():
    # Original divider code
    pass

# Use in main circuit
divider1 = voltage_divider_module()
divider2 = voltage_divider_module()
```
- Verify: Hierarchy preserved in round-trip

## Test Execution Plan

### Phase 1: Unit Tests
- Test component matching logic
- Test position preservation
- Test placement algorithms

### Phase 2: Integration Tests
- Test with simple_voltage_divider
- Test round-trip conversion
- Test manual edit preservation

### Phase 3: Stress Tests
- Large circuits (100+ components)
- Complex hierarchies
- Performance benchmarks

### Phase 4: User Acceptance
- Real project testing
- Workflow validation
- Documentation updates