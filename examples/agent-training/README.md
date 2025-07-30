# Circuit-Synth Agent Training Examples

This directory contains carefully crafted examples for training specialized circuit design agents. Each example demonstrates best practices for specific circuit domains and provides context knowledge for intelligent code generation.

## Philosophy: Examples-First Training

Instead of hardcoded component libraries, agents learn from extensive examples of real circuit-synth code. This approach ensures:

- **Transparency**: All generated code is inspectable Python
- **Accuracy**: Examples are tested and verified to work with KiCad
- **Extensibility**: Easy to add new circuit types by adding examples
- **Learning**: Agents improve as example database grows

## Directory Structure

```
agent-training/
├── power/                    # Power management circuits
├── interfaces/               # Communication interfaces  
├── microcontrollers/         # MCU integration patterns
├── analog/                   # Analog signal processing
├── protection/               # ESD and overcurrent protection
└── [combined examples]       # Multi-domain system examples
```

## Example Format Standard

Each example follows strict conventions:

### File Header
```python
"""
CIRCUIT: Descriptive Circuit Name
PURPOSE: What the circuit accomplishes
COMPONENTS: Key components used
COMPLEXITY: Beginner|Intermediate|Advanced
DOMAIN: Circuit domain for agent specialization
"""
```

### Code Structure
- **Clean circuit-synth code only** - no test harnesses
- **Extensive comments** explaining design decisions
- **Component rationale** - why specific parts were chosen
- **Pin connections** with clear explanations
- **Design calculations** where relevant (power, current, etc.)

### Context Knowledge
Each domain includes `/context/` directory with:
- **Design principles** and best practices
- **Component selection guides** 
- **Layout and routing guidelines**
- **Common mistakes and how to avoid them**
- **Testing and validation procedures**

## Agent Specialization Domains

### Power Management (`power/`)
**Focus**: Voltage regulation, power conversion, supply filtering
**Examples**: LDO regulators, switching supplies, power distribution
**Context**: Thermal design, efficiency, regulation requirements

### Interface Design (`interfaces/`) 
**Focus**: Communication protocols, connectors, signal integrity
**Examples**: USB-C, UART, SPI, I2C, CAN interfaces
**Context**: Protection, termination, EMI/EMC considerations

### Microcontroller Integration (`microcontrollers/`)
**Focus**: MCU selection, peripheral assignment, system architecture  
**Examples**: ESP32, STM32, Arduino configurations
**Context**: Pinout optimization, boot sequences, programming interfaces

### Analog Circuits (`analog/`)
**Focus**: Signal conditioning, amplification, filtering
**Examples**: Op-amp circuits, ADC/DAC interfaces, sensor conditioning
**Context**: Noise analysis, precision design, calibration

### Protection Circuits (`protection/`)
**Focus**: ESD protection, overcurrent, overvoltage protection
**Examples**: TVS diodes, fuses, protection strategies
**Context**: Failure analysis, protection coordination, safety standards

## Usage by Agents

### Code Generation Workflow
1. **Pattern Recognition**: Agent identifies circuit requirements from user input
2. **Example Selection**: Searches relevant examples in appropriate domain
3. **Context Application**: Applies design principles from context knowledge
4. **Code Synthesis**: Generates new circuit-synth code following example patterns
5. **Integration**: Combines multiple domain patterns for complex systems

### Training Data Format
Agents are trained on:
- **Circuit Patterns**: Component selection and connection patterns
- **Design Context**: Understanding of why certain choices are made
- **KiCad Integration**: Knowledge of working symbol/footprint combinations
- **Progressive Complexity**: Learning path from basic to advanced designs

## Adding New Examples

### For New Circuit Types
1. Create example file following naming convention: `01_descriptive_name.py`
2. Include comprehensive header with circuit metadata
3. Add detailed comments explaining design decisions
4. Create corresponding context documentation
5. Test example generates valid KiCad project

### For New Domains
1. Create new domain directory under `agent-training/`
2. Add `context/` subdirectory with design guidelines
3. Create progressive examples (01_basic → 05_advanced)
4. Update this README with domain description

## Example Progression

### Beginner Level (01-02)
- Single-function circuits
- Basic component usage
- Standard configurations
- Clear, simple connections

### Intermediate Level (03-04) 
- Multi-function integration
- Component interaction
- Design trade-offs
- System-level thinking

### Advanced Level (05+)
- Complex system integration
- Performance optimization
- Edge case handling
- Production considerations

## Quality Standards

### Code Quality
- ✅ Clean, readable Python code
- ✅ Consistent naming conventions
- ✅ Comprehensive comments
- ✅ Working KiCad integration

### Design Quality
- ✅ Follows electronics best practices
- ✅ Includes proper decoupling and protection
- ✅ Considers real-world constraints
- ✅ Matches industry standards

### Documentation Quality
- ✅ Clear problem statement
- ✅ Design rationale explained
- ✅ Component selection justified
- ✅ Layout considerations included

This systematic approach enables agents to generate high-quality, production-ready circuit designs while maintaining full transparency and user control over the generated code.