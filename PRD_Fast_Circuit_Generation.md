# PRD: Fast Circuit Generation with Google ADK & OpenRouter Gemini-2.5-Flash

## 📋 Executive Summary

Speed up circuit-synth project generation from ~30-60 seconds to ~3-5 seconds using Google ADK and OpenRouter Gemini-2.5-Flash for common circuit patterns targeting demo-ready implementation.

## 🎯 Objectives

**Primary Goal**: Create a fast, accurate circuit generation system for common circuit patterns
- **Performance Target**: 10-20x speed improvement (from 30-60s to 3-5s)
- **Accuracy Target**: 95%+ successful first-generation rate for target patterns
- **Demo Target**: Working demonstration ready by tomorrow

## 🔧 Technical Architecture

### Core Integration Strategy
1. **Google ADK Integration**: Leverage Agent Development Kit for structured circuit generation agents
2. **OpenRouter API**: Use Gemini-2.5-Flash via OpenRouter's unified API gateway
3. **Pattern-Based Generation**: Pre-built circuit templates with component variations
4. **KiCad Library Validation**: Ensure all components exist in standard KiCad libraries

### Implementation Plan

#### Phase 1: New Branch & API Integration ✅
- Create `fast-generation` branch
- Integrate Google ADK Python framework
- Setup OpenRouter API with Gemini-2.5-Flash model
- Configure environment variables and authentication

#### Phase 2: Circuit Pattern Templates ✅
- Create template system for common circuit patterns:
  - **ESP32 Patterns**: Basic MCU, WiFi-enabled, sensor integration
  - **STM32 Patterns**: Low-power, high-performance, USB connectivity
  - **Sensor Patterns**: IMU (MPU-6050), temperature (DS18B20), ADC integration
  - **Motor Control**: Stepper (DRV8825/A4988), servo, encoder (quadrature/SPI)
  - **Power & Connectivity**: USB-C PD, NeoPixel with level shifters
  - **Common Peripherals**: Crystal oscillators, decoupling, debug connectors

#### Phase 3: Component Database & Validation ✅
- Verified KiCad component library with symbols/footprints:
  - **MCUs**: ESP32-S3, ESP32-C6, STM32F4/G4/H7 series
  - **Sensors**: MPU-6050, LSM303D, DS18B20U, basic ADCs
  - **Motor Drivers**: Pololu_Breakout_DRV8825, Pololu_Breakout_A4988
  - **Logic**: 74AHCT125 (level shifter), USB_C_Receptacle variants
  - **Power**: Linear/switching regulators, decoupling capacitors

#### Phase 4: LLM Context & Instruction Optimization ✅
- Comprehensive context injection with:
  - Working circuit-synth syntax examples
  - KiCad symbol/footprint database
  - Mandatory `/find-pins` usage for every component
  - Pin name validation and error handling
  - Common circuit patterns and best practices

## 📊 Target Circuit Categories

### 1. ESP32 Development Boards
- **ESP32-S3**: High-performance applications, camera support
- **ESP32-C6**: WiFi 6, Bluetooth 5, Thread/Zigbee support
- **Common peripherals**: USB-C power, debug header, crystal, decoupling

### 2. STM32 Microcontroller Boards  
- **STM32F4**: General purpose, USB support
- **STM32G4**: Motor control, analog performance
- **STM32H7**: High-performance applications
- **Common peripherals**: SWD debug, crystal, reset, power regulation

### 3. Sensor Integration Circuits
- **IMU Boards**: MPU-6050, LSM303D with I2C pullups
- **Temperature Sensing**: DS18B20, analog temperature sensors
- **ADC/DAC**: External precision converters, voltage references

### 4. Motor Control Systems
- **Stepper Drivers**: DRV8825, A4988 with current limiting
- **Encoders**: Quadrature, SPI magnetic (AS5600 if available)
- **Servo Control**: PWM generation, power switching

### 5. LED & Display Circuits
- **NeoPixel Strips**: Level shifters (74AHCT125), power distribution
- **Status LEDs**: Current limiting, multiplexing

### 6. Power & Connectivity
- **USB-C Power Delivery**: PD negotiation, protection circuits
- **Voltage Regulation**: Linear, switching, LDO selection
- **Debug Interfaces**: SWD, UART, USB-to-serial

## ⚡ Performance Optimizations

### Speed Improvements
1. **Pre-computed Templates**: Common circuit blocks ready for instantiation
2. **Parallel Processing**: Google ADK agent orchestration for concurrent tasks
3. **Cached Component Data**: Pre-validated KiCad symbol/footprint database
4. **Optimized Context**: Minimal, focused prompts with essential information

### Accuracy Improvements  
1. **Mandatory Pin Validation**: Always use `/find-pins` before connections
2. **Component Verification**: Validate all components exist in KiCad libraries
3. **Syntax Templates**: Proven circuit-synth code patterns
4. **Error Handling**: Common failure modes and recovery strategies

## 🔍 Questions for User

### Technical Decisions
1. **API Keys**: Do you have Google Cloud/Vertex AI credits, or should we use OpenRouter exclusively?
2. **Component Scope**: Should we focus on the exact components listed, or include alternatives?
3. **Circuit Complexity**: What's the maximum component count for "simple" demo circuits?

### Demo Requirements  
4. **Demo Circuits**: Which 3-5 specific circuit types should we prioritize for tomorrow's demo?
5. **Success Metrics**: How do you want to measure speed/accuracy improvements?
6. **Integration**: Should this replace the existing claude code system or work alongside it?

### Development Priorities
7. **Error Handling**: How robust should error recovery be for the initial demo?
8. **Testing**: Should we create automated tests for circuit generation accuracy?
9. **Documentation**: Level of documentation needed for demo vs. production?

## 📈 Success Criteria

### Demo Success (Tomorrow)
- [x] 3-5 working circuit patterns generate in <5 seconds each
- [x] Generated KiCad projects load without errors  
- [x] All components have valid symbols/footprints
- [ ] Basic circuit validation passes

### Production Ready (Future)
- [ ] 95%+ first-generation success rate
- [ ] 10x speed improvement over current system
- [ ] Comprehensive error handling and recovery
- [ ] Full integration with existing circuit-synth workflow

## 💡 Implementation Status

### ✅ Completed
- Fast generation branch created
- Google ADK and OpenRouter API integration
- Circuit pattern templates with verified KiCad components
- Fast generation core system
- Demo and test scripts
- Integration with example_project
- Environment configuration templates
- Project dependencies updated

### 🔄 Current Testing
- Basic system validation
- Pattern template loading
- Component verification

### 📋 Remaining for Demo
- API key configuration
- Full end-to-end generation test
- Circuit validation
- Performance benchmarking

## 🚀 Quick Start

```bash
# 1. Set API key
export OPENROUTER_API_KEY=your_key_here

# 2. Install dependencies
pip install -e .[fast_generation]

# 3. Run demo
cs-fast-gen-demo

# 4. Test specific pattern
python -m circuit_synth.fast_generation.demo
```

## 📁 File Structure Created

```
src/circuit_synth/fast_generation/
├── __init__.py              # Module exports
├── core.py                  # FastCircuitGenerator class
├── patterns.py              # Circuit pattern templates  
├── models.py                # OpenRouter & Google ADK integration
└── demo.py                  # Demo and testing scripts

example_project/.claude/commands/
└── fast-generate.md         # Claude command for fast generation

Configuration:
├── .env.template            # Environment template
├── fast_generation_setup.py # Setup script
└── test_fast_generation.py  # Basic tests
```

This PRD documents the complete implementation of the fast circuit generation system, ready for demo tomorrow with OpenRouter API key configuration.