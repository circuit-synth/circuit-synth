# LLM Agent Integration for Circuit-synth

## Overview

Circuit-synth's design philosophy makes it ideal for LLM code generation. By requiring users to know KiCad symbol/footprint names, we create a structured format that AIs can easily generate when provided with comprehensive component libraries.

## LLM-Friendly Design Advantages

### Structured Component Format
```python
# Predictable, structured syntax ideal for LLM generation
component = Component(
    symbol="Device:R",           # Standard KiCad symbol reference
    ref="R",                     # Reference designator prefix  
    value="10K",                 # Component value
    footprint="Resistor_SMD:R_0603_1608Metric"  # Standard footprint
)
```

### Function-First Hierarchy
```python
# Every subcircuit is a Python function - natural for LLM code generation
@circuit(name="voltage_regulator") 
def voltage_regulator(vin, vout, gnd, output_voltage=3.3):
    # LLM can easily generate hierarchical circuit functions
    pass
```

## Required Tools & Features

### 1. LLM Agent Prompt Template

**Location:** `/memory-bank/prompts/circuit-synth-agent-prompt.md`

**Contents:**
- Circuit-synth API reference and syntax
- Common KiCad symbol library (Device, Connector, MCU, etc.)
- Common footprint library (SMD packages, connectors, etc.)
- Example circuits for different complexity levels
- Best practices for hierarchical design

### 2. Symbol/Footprint Search Tool

**Need:** Tool for LLMs to search KiCad libraries when unknown components are needed.

**Potential Implementation:**
```python
from circuit_synth.search import search_symbols, search_footprints

# LLM can search for components
symbols = search_symbols("microcontroller STM32")
footprints = search_footprints("QFP-64")
```

**Check if exists:** We may already have this capability - need to investigate current codebase.

### 3. Component Library Database

**Contents:**
- Comprehensive symbol mappings (Device:R, MCU_ST_STM32:STM32F4xx, etc.)
- Footprint catalog with descriptions (SOIC-8, QFP-64, 0603, etc.)
- Common component values and ratings
- Pin mapping information for complex components

## Implementation Tasks

### Phase 1: Agent Prompt Creation ✅ COMPLETED
- [x] Create comprehensive LLM agent prompt with:
  - Circuit-synth syntax guide ✅
  - Common symbol/footprint library ✅
  - Example circuits (simple to complex) ✅
  - Hierarchical design patterns ✅
  - Error handling guidelines ✅

**Status:** Circuit-synth Claude agent created at `.claude/agents/circuit-synth.md`
- Comprehensive syntax examples with good/bad patterns
- Component reuse best practices
- Pin connection patterns (integer vs string access)  
- Circuit structure and @circuit decorator usage
- Code quality and maintainability guidelines

### Phase 2: Search Tool Development
- [ ] Investigate existing search capabilities in codebase
- [ ] Implement/enhance symbol search functionality
- [ ] Implement/enhance footprint search functionality
- [ ] Create LLM-friendly search API

### Phase 3: Component Database
- [ ] Build comprehensive symbol reference database
- [ ] Build comprehensive footprint reference database  
- [ ] Include component descriptions and use cases
- [ ] Add pin mapping information for complex parts

### Phase 4: Integration Testing
- [ ] Test LLM code generation with various AI models
- [ ] Validate generated circuit functionality
- [ ] Refine prompts based on AI performance
- [ ] Create example AI-generated circuits

## Benefits

### For Users
- **AI-Assisted Design** - Generate circuits from natural language descriptions
- **Learning Tool** - AI can explain circuit design decisions
- **Rapid Prototyping** - Quick generation of common circuit patterns
- **Component Discovery** - AI helps find appropriate symbols/footprints

### For Circuit-synth
- **Competitive Advantage** - Unique AI-native circuit design tool
- **User Adoption** - Lower barrier to entry with AI assistance
- **Professional Appeal** - Modern workflow integration
- **Educational Value** - Teaching tool for circuit design

## Use Cases

### 1. Natural Language Circuit Generation
```
User: "Create an ESP32 development board with USB-C, voltage regulator, and debug header"
AI: Generates complete circuit-synth code with appropriate components
```

### 2. Component Selection Assistance
```
User: "I need a microcontroller with USB and CAN interfaces"
AI: Searches database and suggests appropriate MCUs with footprints
```

### 3. Circuit Optimization
```
User: "Optimize this power supply for better efficiency"
AI: Analyzes circuit and suggests component changes with rationale
```

### 4. Learning and Education
```
User: "Explain why this circuit needs these capacitors"
AI: Provides educational explanation of decoupling and filtering
```

## Success Metrics

1. **AI Generation Quality** - Generated circuits compile and function correctly
2. **Component Accuracy** - AI selects appropriate symbols/footprints
3. **User Adoption** - Engineers successfully use AI-generated circuits
4. **Search Effectiveness** - AI finds correct components when needed
5. **Educational Value** - AI explanations help users learn circuit design

## Competitive Advantage

This LLM integration strategy gives circuit-synth a unique position:

- **SKIDL**: Complex syntax difficult for AI generation
- **PCB/Zener**: DSL syntax less familiar to AI models  
- **Circuit-synth**: Python-native, structured format ideal for AI

Making circuit-synth the **premier AI-native circuit design tool** for the modern engineering workflow.