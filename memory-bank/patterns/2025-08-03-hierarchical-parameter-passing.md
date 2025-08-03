# Hierarchical Parameter Passing Pattern

## Pattern: Child Circuit Instantiation with Net Parameters

### Problem
Child circuits in hierarchical designs need shared nets (like `GND`, `VCC_3V3`) passed as parameters to maintain connectivity across hierarchy levels.

### Solution Pattern
```python
def parent_circuit():
    # Create shared nets at parent level
    gnd = Net('GND')
    vcc_3v3 = Net('VCC_3V3')
    debug_en = Net('DEBUG_EN')
    
    # Parent circuit components
    # ... component definitions ...
    
    # Instantiate child circuits with proper parameters
    debug_header_circuit = debug_header(gnd, vcc_3v3, debug_en, debug_io0, debug_rx, debug_tx)
    led_blinker_circuit = led_blinker(gnd, led_control)
    
    # Combine circuits
    return parent_circuit + debug_header_circuit + led_blinker_circuit
```

### Key Principles

1. **Net Creation Hierarchy**: Nets are created at the Lowest Common Ancestor (LCA) level where they're shared
2. **Parameter Order**: Follow consistent parameter ordering (power nets first, then signals)
3. **Type Safety**: All parameters must be Net objects, not strings
4. **Complete Parameter Lists**: All child circuit parameters must be provided (no defaults in hierarchical context)

### Example Implementation
```python
# ESP32_C6_MCU.py - Parent circuit with two children
def esp32_c6_mcu(gnd, vcc_3v3, usb_dm, usb_dp):
    # Create local nets for children
    debug_en = Net('DEBUG_EN')
    debug_io0 = Net('DEBUG_IO0') 
    debug_rx = Net('DEBUG_RX')
    debug_tx = Net('DEBUG_TX')
    led_control = Net('LED_CONTROL')
    
    # Parent components
    esp32 = Component(symbol="RF_Module:ESP32-C6-MINI-1", ref="U")
    # ... connect esp32 to nets ...
    
    # Child circuit instantiation with all required parameters
    debug_header_circuit = debug_header(gnd, vcc_3v3, debug_en, debug_io0, debug_rx, debug_tx)
    led_blinker_circuit = led_blinker(gnd, led_control)
    
    return circuit + debug_header_circuit + led_blinker_circuit
```

### Benefits
- **Explicit Connectivity**: Clear net sharing across hierarchy boundaries
- **Type Safety**: Compile-time detection of missing parameters
- **Maintainability**: Easy to trace net flow through hierarchy
- **Scalability**: Pattern works for arbitrary hierarchy depth