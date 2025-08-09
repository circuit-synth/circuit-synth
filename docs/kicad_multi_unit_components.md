# Complex KiCad Multi-Unit Components

## What Are Multi-Unit Components?

Multi-unit components are single physical ICs that contain multiple functional blocks, each represented as a separate symbol unit in KiCad. This is common for:

### 1. **Quad Op-Amps (4 units + power)**
- **LM324** - 4 op-amp units (A, B, C, D) + 1 power unit
- **TL074** - 4 op-amp units + power
- **TL084** - 4 op-amp units + power
- **LM348** - 4 op-amp units + power

### 2. **Dual Op-Amps (2 units + power)**
- **LM358** - 2 op-amp units (A, B) + 1 power unit
- **TL072** - 2 op-amp units + power
- **TL082** - 2 op-amp units + power
- **NE5532** - 2 op-amp units + power

### 3. **Logic Gates (4-6 units + power)**
- **74HC00** - 4 NAND gates + power
- **74HC04** - 6 NOT gates + power
- **74HC08** - 4 AND gates + power
- **74HC32** - 4 OR gates + power
- **74HC86** - 4 XOR gates + power
- **CD4066** - 4 analog switches + power

### 4. **Comparators**
- **LM339** - 4 comparator units + power
- **LM393** - 2 comparator units + power

### 5. **Analog Switches/Multiplexers**
- **CD4066** - 4 analog switches + power
- **CD4051** - 8-channel mux (complex multi-unit)
- **CD4052** - Dual 4-channel mux
- **CD4053** - Triple 2-channel mux

## How Multi-Unit Components Work in KiCad

### Symbol Structure
```
LM324 (Physical IC Package)
├── Unit A (Op-Amp 1) - Pins: 1(OUT), 2(IN-), 3(IN+)
├── Unit B (Op-Amp 2) - Pins: 7(OUT), 6(IN-), 5(IN+)
├── Unit C (Op-Amp 3) - Pins: 8(OUT), 9(IN-), 10(IN+)
├── Unit D (Op-Amp 4) - Pins: 14(OUT), 13(IN-), 12(IN+)
└── Unit E (Power)    - Pins: 4(VCC), 11(VSS/GND)
```

### In S-Expressions
```lisp
(symbol (lib_id "Amplifier_Operational:LM324") 
  (at 100 50 0) 
  (unit 1)  ; Unit A
  (uuid "abc-123")
  ...)

(symbol (lib_id "Amplifier_Operational:LM324") 
  (at 150 50 0) 
  (unit 2)  ; Unit B
  (uuid "def-456")
  ...)

(symbol (lib_id "Amplifier_Operational:LM324") 
  (at 100 100 0) 
  (unit 3)  ; Unit C
  (uuid "ghi-789")
  ...)

(symbol (lib_id "Amplifier_Operational:LM324") 
  (at 150 100 0) 
  (unit 4)  ; Unit D
  (uuid "jkl-012")
  ...)

(symbol (lib_id "Amplifier_Operational:LM324") 
  (at 50 150 0) 
  (unit 5)  ; Power unit
  (uuid "mno-345")
  ...)
```

## Challenges for S-Expression Formatting

### 1. **Unit Numbering**
- Each unit needs correct `(unit N)` parameter
- Units share the same reference (e.g., all are "U1")
- Must track which units are used

### 2. **Instances Block**
```lisp
(instances
  (project "my_project"
    (path "/"
      (reference "U1")  ; Same reference for all units
      (unit 1)          ; But different unit numbers
    )
  )
)
```

### 3. **Power Unit Handling**
- Power unit (usually unit 5) is often auto-placed
- May have different symbol style (just power pins)
- Sometimes hidden by default

### 4. **Pin Mapping Complexity**
- Pin numbers are distributed across units
- Same physical pin appears only in one unit
- Pin-to-unit mapping must be correct

## Test Cases for Multi-Unit Components

### Test 1: Simple Dual Op-Amp (LM358)
```python
def test_lm358_dual_opamp():
    """Test formatting of dual op-amp with 2 units + power."""
    # Unit A: Pins 1(OUT), 2(IN-), 3(IN+)
    # Unit B: Pins 7(OUT), 6(IN-), 5(IN+)  
    # Power:  Pins 8(V+), 4(V-)
    pass
```

### Test 2: Complex Quad Op-Amp (LM324)
```python
def test_lm324_quad_opamp():
    """Test formatting of quad op-amp with 4 units + power."""
    # 4 op-amp units + 1 power unit = 5 total units
    pass
```

### Test 3: Logic Gates (74HC00)
```python
def test_74hc00_quad_nand():
    """Test formatting of quad NAND gate."""
    # 4 NAND gate units + 1 power unit
    # Different symbol shape than op-amps
    pass
```

### Test 4: Mixed Analog/Digital (CD4066)
```python
def test_cd4066_analog_switch():
    """Test formatting of quad analog switch."""
    # 4 switch units + 1 power unit
    # Has both analog and digital pins
    pass
```

## Special Formatting Considerations

### 1. **Unit-Specific Properties**
```lisp
(property "Reference" "U1A"  ; Unit A gets suffix
  (at 100 47.46 0)
  (unit 1)  ; Property specific to unit 1
  ...)
```

### 2. **Interleaved Units**
Different units of same component can be scattered across schematic:
```
Page 1: U1A (unit 1) - First op-amp
Page 2: U1B (unit 2) - Second op-amp  
Page 3: U1C (unit 3) - Third op-amp
Page 5: U1E (unit 5) - Power connections
```

### 3. **De Morgan Representations**
Some logic gates have alternate symbols:
```lisp
(symbol (lib_id "74xx:74HC00")
  (unit 1)
  (de_morgan 2)  ; Alternate symbol representation
  ...)
```

## How Circuit-Synth Should Handle Multi-Unit

### Current Approach (if any)
```python
# Does circuit-synth handle multi-unit components?
# How are units specified in Python code?
```

### Potential Python API
```python
# Option 1: Automatic unit assignment
lm324 = Component("Amplifier_Operational:LM324", ref="U")
# Automatically creates all 5 units?

# Option 2: Explicit unit specification  
lm324_a = Component("Amplifier_Operational:LM324", ref="U", unit=1)
lm324_b = Component("Amplifier_Operational:LM324", ref="U", unit=2)
lm324_power = Component("Amplifier_Operational:LM324", ref="U", unit=5)

# Option 3: Unit as property
lm324 = Component("Amplifier_Operational:LM324", ref="U")
lm324.unit[1]["OUT"] += net1  # Access unit 1
lm324.unit[2]["OUT"] += net2  # Access unit 2
```

## Testing Multi-Unit in Formatter

### Critical Test Cases

1. **All units of same component have same reference**
   - U1 for all units, not U1, U2, U3...

2. **Unit numbers preserved correctly**
   - (unit 1), (unit 2), etc. in right places

3. **Instances block handles units**
   ```lisp
   (instances
     (project "test"
       (path "/" 
         (reference "U1") (unit 1))
       (path "/" 
         (reference "U1") (unit 2))
       ; ... for each unit
   )
   ```

4. **Power unit formatting**
   - Often has different placement rules
   - May be auto-hidden

5. **Properties per unit**
   - Reference shows unit suffix (U1A, U1B)
   - Each unit can have different position

## Example: Complete LM358 in S-Expression

```lisp
; Unit A (Op-Amp 1)
(symbol (lib_id "Amplifier_Operational:LM358") (at 127 50.8 0) (unit 1)
  (in_bom yes) (on_board yes) (dnp no)
  (uuid "11111111-1111-1111-1111-111111111111")
  (property "Reference" "U1A" (at 127 45.72 0)
    (effects (font (size 1.27 1.27))))
  (property "Value" "LM358" (at 127 48.26 0)
    (effects (font (size 1.27 1.27))))
  (pin "1" (uuid "aaaa"))  ; OUT
  (pin "2" (uuid "bbbb"))  ; IN-
  (pin "3" (uuid "cccc"))  ; IN+
  (instances
    (project "my_circuit"
      (path "/"
        (reference "U1") (unit 1)))))

; Unit B (Op-Amp 2)
(symbol (lib_id "Amplifier_Operational:LM358") (at 165.1 50.8 0) (unit 2)
  (in_bom yes) (on_board yes) (dnp no)
  (uuid "22222222-2222-2222-2222-222222222222")
  (property "Reference" "U1B" (at 165.1 45.72 0)
    (effects (font (size 1.27 1.27))))
  (property "Value" "LM358" (at 165.1 48.26 0)
    (effects (font (size 1.27 1.27))))
  (pin "5" (uuid "dddd"))  ; IN+
  (pin "6" (uuid "eeee"))  ; IN-
  (pin "7" (uuid "ffff"))  ; OUT
  (instances
    (project "my_circuit"
      (path "/"
        (reference "U1") (unit 2)))))

; Unit 3 (Power)
(symbol (lib_id "Amplifier_Operational:LM358") (at 101.6 25.4 0) (unit 3)
  (in_bom yes) (on_board yes) (dnp no)
  (uuid "33333333-3333-3333-3333-333333333333")
  (property "Reference" "U1" (at 100.33 24.13 0)
    (effects (font (size 1.27 1.27)) (justify left)))
  (property "Value" "LM358" (at 100.33 26.67 0)
    (effects (font (size 1.27 1.27)) (justify left)))
  (pin "4" (uuid "gggg"))  ; V-/GND
  (pin "8" (uuid "hhhh"))  ; V+
  (instances
    (project "my_circuit"
      (path "/"
        (reference "U1") (unit 3)))))
```

## Summary

Multi-unit components like LM324, LM358, and 74HC series are the most complex KiCad components because:

1. **Single package, multiple symbols** - One IC becomes 3-6 schematic symbols
2. **Shared reference** - All units are "U1" but different unit numbers
3. **Distributed pins** - Each unit has different pin subsets
4. **Power unit** - Special handling for power pins
5. **Complex instances** - Must track unit numbers in instances blocks

These are excellent test cases for the S-expression formatter refactoring!