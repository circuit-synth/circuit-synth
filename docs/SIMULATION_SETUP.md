# Circuit-Synth SPICE Simulation Setup Guide

This guide walks you through setting up SPICE simulation capabilities in circuit-synth using PySpice and ngspice.

## Overview

Circuit-synth now supports SPICE simulation integration, allowing you to:
- Convert circuit-synth designs to SPICE netlists
- Run DC, AC, and transient analysis 
- Validate circuit behavior before PCB fabrication
- Optimize component values through simulation

## Prerequisites

### 1. Install ngspice (SPICE Simulator Engine)

**macOS (using Homebrew):**
```bash
brew install ngspice
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ngspice ngspice-doc
```

**Windows:**
1. Download ngspice from: http://ngspice.sourceforge.net/download.html
2. Install to `C:\ngspice` or similar location
3. Add to PATH environment variable

### 2. Install Circuit-Synth (PySpice included by default)

**Using pip:**
```bash
pip install circuit-synth
```

**Using uv:**
```bash
uv add circuit-synth
```

**Development installation:**
```bash
uv pip install -e .
```

## Verification

### Test ngspice Installation
```bash
# Check ngspice is installed
ngspice --version

# Find ngspice library location (macOS)
find /opt/homebrew /usr/local -name "*ngspice*" 2>/dev/null | grep lib

# Find ngspice library location (Linux)
find /usr -name "*ngspice*" 2>/dev/null | grep lib
```

### Test PySpice Installation
```python
import PySpice
from PySpice.Unit import *
from PySpice.Spice.Netlist import Circuit

print(f"✅ PySpice {PySpice.__version__} installed successfully")
```

### Test Circuit-Synth Simulation
```python
from circuit_synth import Circuit, Component, Net, circuit

@circuit
def test_circuit():
    r1 = Component("Device:R", ref="R", value="1k")
    vin = Net('VIN')
    gnd = Net('GND')
    r1[1] += vin
    r1[2] += gnd

# Create and test simulator
c = test_circuit()
try:
    sim = c.simulator()
    print("✅ Circuit-synth simulation ready!")
except Exception as e:
    print(f"❌ Simulation setup issue: {e}")
```

## Platform-Specific Configuration

### macOS Configuration
Circuit-synth automatically detects homebrew ngspice installations at:
- `/opt/homebrew/lib/libngspice.dylib` (Apple Silicon)
- `/usr/local/lib/libngspice.dylib` (Intel Mac)

### Linux Configuration
If PySpice can't find ngspice, set the library path manually:
```python
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
NgSpiceShared.LIBRARY_PATH = '/usr/lib/x86_64-linux-gnu/libngspice.so'
```

### Windows Configuration
Set the ngspice path in your code:
```python
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
NgSpiceShared.LIBRARY_PATH = r'C:\ngspice\bin_dll\ngspice.dll'
```

## Troubleshooting

### Common Issues

**"cannot load library 'libngspice'"**
- Verify ngspice is installed: `which ngspice`
- Check library exists: `ls /opt/homebrew/lib/libngspice*`
- Set LIBRARY_PATH manually (see platform sections above)

**"Unsupported Ngspice version"**
- This is a warning, not an error - simulation still works
- PySpice may not recognize newer ngspice versions

**"Warning: can't find the initialization file spinit"**
- This is normal - ngspice will use defaults
- Optional: Create spinit file for custom ngspice configuration

**Circuit conversion errors**
- Ensure all components have valid SPICE models
- Check that nets are properly connected
- Verify component values are SPICE-compatible (e.g., "10k" not "10K")

### Getting Help

1. **Check the examples**: `examples/simulation/`
2. **PySpice documentation**: https://pyspice.fabrice-salvaire.fr/
3. **ngspice manual**: http://ngspice.sourceforge.net/docs.html
4. **Circuit-synth issues**: Create an issue on GitHub

## Performance Notes

- **First simulation**: May take 2-3 seconds to initialize ngspice
- **Subsequent simulations**: ~100ms for simple circuits
- **Complex circuits**: Scale with number of nodes and components
- **Memory usage**: Moderate (~10-50MB per simulation)

## Security Considerations

- PySpice loads native libraries - ensure clean ngspice installation
- Simulation files are temporary and cleaned up automatically

## Next Steps

Once setup is complete:
1. Try the basic examples in `examples/simulation/`
2. Use the `/simulate` slash command with Claude
3. Explore the `Circuit.simulator()` API
4. Build your own simulation workflows

Happy simulating! 🔌⚡