# Circuit-Synth Architecture Overview

## 🏗️ High-Level Architecture

Circuit-synth is designed as a **Python-first EE design tool** with **Rust acceleration** for performance-critical operations. The architecture emphasizes simplicity, modularity, and seamless integration with existing EE workflows.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Circuit-Synth Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│  Python API Layer (User Interface)                             │
│  ├─ Circuit Definition (@circuit decorator)                    │
│  ├─ Component Library (symbols, footprints, JLCPCB)          │
│  └─ Simple Python Syntax (nets, components, connections)      │
├─────────────────────────────────────────────────────────────────┤
│  Core Engine (Python + Rust Acceleration)                     │
│  ├─ Circuit Graph Management                                   │
│  ├─ Net Analysis & Validation                                  │
│  ├─ Reference Management                                       │
│  └─ Component Placement Algorithms                             │
├─────────────────────────────────────────────────────────────────┤
│  KiCad Integration Layer                                        │
│  ├─ Schematic Generation (hierarchical sheets)                │
│  ├─ PCB Generation (component placement)                      │
│  ├─ Netlist Export/Import (.net files)                       │
│  └─ Bi-directional Sync (canonical matching)                 │
├─────────────────────────────────────────────────────────────────┤
│  Manufacturing Integration                                      │
│  ├─ JLCPCB (availability, pricing, constraints)              │
│  ├─ Component Search (STM32, modm-devices)                   │
│  └─ Future: Digi-Key, PCBWay, OSH Park                       │
├─────────────────────────────────────────────────────────────────┤
│  AI Agent Infrastructure                                        │
│  ├─ Claude Code Agents (circuit design, review)              │
│  ├─ Component Search Agents                                   │
│  ├─ Development Helper Agents                                 │
│  └─ Extensible Agent Framework                                │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure (Scalable Organization)

### Core Python Package
```
src/circuit_synth/
├── core/                    # Core circuit logic
│   ├── circuit.py          # Circuit class, @circuit decorator
│   ├── component.py        # Component definitions
│   ├── net.py              # Net management
│   ├── reference_manager.py # R1, C1, U1 assignment
│   └── rust_integration.py # Rust acceleration layer
├── component_info/          # Component-specific integrations
│   ├── microcontrollers/   # STM32, ESP32, PIC, AVR families
│   ├── analog/             # Op-amps, ADCs, sensors
│   ├── power/              # Regulators, power management
│   ├── rf/                 # RF/wireless components
│   └── [future families]   # Extensible component categories
├── manufacturing/           # Manufacturing integrations
│   ├── jlcpcb/            # JLCPCB API, constraints
│   ├── [future]/          # Digi-Key, PCBWay, OSH Park
├── kicad/                  # KiCad integration
│   ├── sch_gen/           # Schematic generation
│   ├── pcb_gen/           # PCB generation  
│   └── sch_sync/          # Bi-directional sync
└── tools/                  # CLI tools and utilities
```

### Rust Acceleration Modules
```
rust_modules/
├── rust_core_circuit_engine/    # Core circuit operations
├── rust_kicad_integration/      # KiCad file generation
├── rust_netlist_processor/      # Netlist processing
├── rust_force_directed_placement/ # Component placement
├── rust_symbol_cache/           # Symbol search/caching
└── [future modules]/           # Extensible Rust components
```

## 🔄 Data Flow Architecture

### 1. Circuit Definition (Python API)
```python
@circuit(name="Power_Supply")
def usb_to_3v3():
    """USB-C to 3.3V regulation"""
    # Simple Python syntax
    vbus = Net('VBUS')
    regulator = Component("Regulator_Linear:AMS1117-3.3", ref="U")
    regulator["VI"] += vbus  # Clear connections
```

### 2. Core Processing (Python + Rust)
- **Circuit Graph**: Component relationships, net connectivity
- **Validation**: Design rule checks, electrical validation
- **Reference Assignment**: R1, C1, U1 generation (globally unique)
- **Placement**: Force-directed algorithms for optimal layout

### 3. KiCad Generation (Rust Accelerated)
- **Hierarchical Schematics**: Professional sheet organization
- **S-Expression Generation**: Fast, optimized KiCad file format
- **Component Placement**: Intelligent positioning algorithms
- **Netlist Export**: Industry-standard .net files

### 4. Manufacturing Integration
- **Component Verification**: Real-time availability checking
- **Constraint Validation**: Manufacturing capability verification
- **Cost Optimization**: Component selection for budget targets

## 🤖 AI Agent Integration Architecture

### Agent Categories
1. **Circuit Design Agents**: Help users create circuits
2. **Component Search Agents**: Find components with manufacturing data
3. **Code Review Agents**: Ensure code quality and conventions
4. **Development Helper Agents**: Assist contributors

### Agent Infrastructure
```python
# Agent registration system
from circuit_synth.claude_integration import register_agent

@register_agent("circuit-architect")
class CircuitArchitectAgent:
    """Master circuit design coordinator"""
    
    def capabilities(self):
        return [
            "circuit_design",
            "component_selection", 
            "kicad_generation",
            "manufacturing_integration"
        ]
```

## 🚀 Performance Architecture

### Python + Rust Hybrid Approach

**Python**: User interface, API design, flexibility
- Circuit definition and validation
- Agent integration and orchestration
- Development tooling and testing

**Rust**: Performance-critical operations  
- KiCad file generation (S-expression processing)
- Component placement algorithms
- Large-scale netlist processing
- Symbol search and caching

### Performance Fallback System
```python
# Graceful degradation when Rust unavailable
try:
    import rust_kicad_integration
    use_rust_acceleration = True
except ImportError:
    use_rust_acceleration = False
    # Use Python implementation with performance warning
```

## 🔄 Bi-directional Sync Architecture

### Canonical Matching System
```
┌─────────────────┐    Sync    ┌──────────────────┐
│   Python Code   │ ◄────────► │   KiCad Project  │
│                 │            │                  │
│ Circuit(...)    │            │ .kicad_sch       │
│ Component(...)  │            │ .kicad_pcb       │
│ Net(...)        │            │ .net             │
└─────────────────┘            └──────────────────┘
        ▲                               ▲
        │                               │
        └─────── Canonical Match ───────┘
           (handles user modifications)
```

**Canonical Matching** handles:
- User-modified reference designators (R1 → R_PULL_UP)
- Changed component values (1kΩ → 2.2kΩ)  
- Moved component positions
- Added/removed components

## 🧪 Test-Driven Development Architecture

### Testing Pyramid
```
        ┌─────────────────┐
        │  Integration    │  ← Full workflow tests
        │     Tests       │
        ├─────────────────┤
        │  Functional     │  ← Feature-specific tests
        │     Tests       │
        ├─────────────────┤
        │  Unit Tests     │  ← Individual component tests
        └─────────────────┘
```

### TDD Workflow Integration
```bash
# Automated testing infrastructure
./scripts/run_all_tests.sh           # All tests
./scripts/run_all_tests.sh --python-only  # Skip Rust compilation
./scripts/test_rust_modules.sh       # Rust-specific tests
```

## 🔌 Extensibility Architecture  

### Component Family Extension
```python
# Adding new component family
src/circuit_synth/component_info/sensors/
├── __init__.py
├── temperature_sensors.py
├── pressure_sensors.py
└── imu_sensors.py
```

### Manufacturing Integration Extension
```python
# Adding new manufacturer
src/circuit_synth/manufacturing/digikey/
├── __init__.py
├── api_client.py
├── part_search.py
└── pricing_integration.py
```

### Agent Extension
```python
# Adding specialized agent
@register_agent("power-supply-expert")
class PowerSupplyAgent:
    """Specialized in power supply design"""
    # Implementation...
```

## 🎯 Design Principles

### 1. **Simplicity First**
- Very simple Python syntax
- No complex DSL or meta-programming
- Clear, readable generated KiCad files

### 2. **Professional Integration**
- Fits existing EE workflows
- Industry-standard file formats
- Manufacturing-ready outputs

### 3. **AI-Agent Friendly**
- Extensive documentation for LLMs
- Clear APIs and patterns
- Comprehensive examples

### 4. **Performance When Needed**
- Python for flexibility
- Rust for speed-critical operations
- Graceful fallback system

### 5. **Test-Driven Everything**
- Every feature has comprehensive tests
- TDD workflow integration
- Continuous integration validation

---

This architecture enables circuit-synth to be both **simple for users** and **powerful for complex workflows**, while remaining **highly extensible** for future development.