# Round-Trip Testing Strategy

## Test Status

| Category | Status | Location |
|----------|--------|----------|
| Format preservation | ✅ 6/6 pass | `submodules/kicad-sch-api/tests/reference_tests/` |
| Component matching | ✅ Exists | Need explicit round-trip tests |
| Position preservation | ❓ Untested | Need integration test |
| Wire preservation | ❓ Unknown | **Critical to verify** |
| Label preservation | ❓ Unknown | **Critical to verify** |
| Hierarchical updates | ✅ Code exists | Need integration test |

## Critical Tests Needed

### 1. Position Preservation Test
```python
def test_position_preservation():
    # Generate from Python
    circuit.generate_kicad_project("test_project")

    # Move component in KiCad simulation
    sch = ksa.Schematic.load("test_project/test_project.kicad_sch")
    r1 = sch.get_component("R1")
    original_pos = r1.position
    r1.position = (100, 200)  # Move it
    sch.save()

    # Re-generate (no changes)
    circuit.generate_kicad_project("test_project")

    # Verify position preserved
    sch_after = ksa.Schematic.load("test_project/test_project.kicad_sch")
    r1_after = sch_after.get_component("R1")
    assert r1_after.position == (100, 200)
```

### 2. Wire Preservation Test
```python
def test_wire_preservation():
    # Generate basic circuit
    circuit.generate_kicad_project("test_project")

    # Add manual wire
    sch = ksa.Schematic.load("test_project/test_project.kicad_sch")
    wire = sch.add_wire(start=(50, 50), end=(100, 50))
    wire_uuid = wire.uuid
    sch.save()

    # Re-generate (modify value)
    circuit.components["R1"].value = "22k"
    circuit.generate_kicad_project("test_project")

    # Verify wire still exists
    sch_after = ksa.Schematic.load("test_project/test_project.kicad_sch")
    assert wire_uuid in [w.uuid for w in sch_after.wires]
```

### 3. Label Preservation Test
```python
def test_label_preservation():
    # Generate circuit
    circuit.generate_kicad_project("test_project")

    # Add manual label
    sch = ksa.Schematic.load("test_project/test_project.kicad_sch")
    label = sch.add_label("TEST_SIGNAL", position=(75, 75))
    label_uuid = label.uuid
    sch.save()

    # Re-generate
    circuit.generate_kicad_project("test_project")

    # Verify label preserved
    sch_after = ksa.Schematic.load("test_project/test_project.kicad_sch")
    assert label_uuid in [l.uuid for l in sch_after.labels]
```

### 4. Complete Round-Trip Test
```python
def test_complete_roundtrip():
    """Test full workflow: generate → edit → modify → regenerate"""
    # 1. Generate initial circuit
    circuit = create_test_circuit()
    circuit.generate_kicad_project("test_project")

    # 2. Simulate user edits in KiCad
    sch = ksa.Schematic.load("test_project/test_project.kicad_sch")
    r1 = sch.get_component("R1")
    r1.position = (150, 150)  # Move
    sch.add_wire(start=(50, 50), end=(100, 50))  # Add wire
    sch.add_label("CUSTOM", position=(75, 75))  # Add label
    sch.save()

    # 3. Modify Python circuit
    circuit.components["R1"].value = "47k"  # Change value
    circuit.add_component(Component("Device:C", ref="C", value="10uF"))  # Add cap

    # 4. Re-generate
    circuit.generate_kicad_project("test_project")

    # 5. Verify everything
    sch_final = ksa.Schematic.load("test_project/test_project.kicad_sch")
    r1_final = sch_final.get_component("R1")

    assert r1_final.position == (150, 150), "Position preserved"
    assert r1_final.value == "47k", "Value updated"
    assert len(sch_final.wires) > 0, "Wires preserved"
    assert len(sch_final.labels) > 0, "Labels preserved"
    assert sch_final.get_component("C1") is not None, "New component added"
```

## Manual Test Checklist

**Phase 1: Basic Verification**
- [ ] Generate simple circuit (2 resistors)
- [ ] Open in KiCad, move R1
- [ ] Re-run Python (no changes)
- [ ] Verify R1 still in new position

**Phase 2: Wire Routing**
- [ ] Generate circuit
- [ ] Route wires manually in KiCad
- [ ] Re-run Python (change R1 value)
- [ ] Verify wires intact, value updated

**Phase 3: Annotations**
- [ ] Generate circuit
- [ ] Add text boxes and notes
- [ ] Re-run Python
- [ ] Verify annotations preserved

**Phase 4: Component Operations**
- [ ] Generate 5 resistors
- [ ] Change R1-R3 values in Python
- [ ] Remove R4 from Python
- [ ] Add R6 in Python
- [ ] Re-run
- [ ] Verify: R1-R3 updated, R4 removed, R5 unchanged, R6 added

**Phase 5: Hierarchical**
- [ ] Generate 3-sheet project
- [ ] Edit each sheet in KiCad
- [ ] Modify Python (add component to sheet 2)
- [ ] Re-run
- [ ] Verify all sheets correct

## Success Criteria

✅ **All tests pass**
✅ **No data loss in manual testing**
✅ **Update completes in <2s**
✅ **User reports confidence in preservation**

## Timeline

- Week 1 Day 1-2: Create automated tests
- Week 1 Day 3: Run manual verification
- Week 1 Day 4-5: Fix issues found
- Week 2 Day 1: Final testing
