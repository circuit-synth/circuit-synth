# Manual Test Steps for Test Case 10

## Initial Setup
1. Run the circuit.py script to generate the initial KiCad project
2. Open the generated project in KiCad

## KiCad Modifications

### Step 1: Add Net Labels
1. Open the schematic editor
2. Add net labels (press 'L'):
   - Place label "VCC" on NET1
   - Place label "SENSOR_OUT" on NET2
   - Place label "BUFFER_OUT" on NET3
   - Place label "ADC_IN" on NET4

### Step 2: Add Global Labels
1. Add global label (Ctrl+L):
   - Place global label "VCC" on the power net
   - Place global label "ADC_IN" on NET4 (for inter-sheet connection)

### Step 3: Merge Redundant Nets
1. Notice that U1 pin 2 and pin 1 are connected (voltage follower)
2. Ensure they share the same net name "BUFFER_OUT"

### Step 4: Add Hierarchical Labels (Optional)
1. If testing hierarchical designs:
   - Add hierarchical label "SENSOR_INPUT" 
   - Add hierarchical label "ADC_OUTPUT"

### Step 5: Save and Export
1. Save the schematic
2. Run ERC to verify connections
3. Export using Circuit Synth tools

## Python Re-import
1. Run the import script to bring changes back to Python
2. Verify the generated Python code shows:
   - NET1 replaced with "VCC"
   - NET2 replaced with "SENSOR_OUT"
   - NET3 replaced with "BUFFER_OUT"
   - NET4 replaced with "ADC_IN"

## Validation Checklist
- [ ] All generic net names replaced with meaningful names
- [ ] Global labels properly recognized
- [ ] Net merging handled correctly
- [ ] All connections preserved
- [ ] No duplicate net definitions
- [ ] Hierarchical labels (if used) properly handled