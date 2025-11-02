# Test 01: Basic Netlist Generation

Tests basic netlist generation with simple RC circuit.

```bash
pytest test_*.py -v
```

Validates:
- Netlist file created
- Components present (R1, R2, C1)
- Values preserved (10k, 4.7k, 100nF)
- Nets present (VCC, GND, SIGNAL)
