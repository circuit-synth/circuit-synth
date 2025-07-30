# Circuit-Synth YouTube Video - Blue Pill Clone Demo

**Target:** Create compelling YouTube video demonstrating circuit-synth library effectiveness
**Duration:** 15-20 minutes (optimal for technical content)
**Audience:** Hardware engineers, PCB designers, Python developers interested in EDA tools

## Video Concept

**Title Options:**
- "Building a Blue Pill STM32 Board with Python Code - Circuit-Synth Demo"
- "From Python to PCB: Creating an STM32 Development Board"
- "Circuit Design with Code: Making a Blue Pill Clone in Python"

**Hook (First 30 seconds):**
"What if you could design entire PCBs using just Python code? Today I'm recreating the popular Blue Pill STM32 development board using circuit-synth - a Python library that generates complete KiCad projects from code."

## Video Structure & Script

### 1. Introduction (1-2 minutes)
**Script Points:**
- Quick demo: Show final result first (working Blue Pill clone)
- Problem statement: Traditional PCB design vs. code-based approach
- What we'll build: Blue Pill clone with STM32F103C8T6
- What viewers will learn: Python-based circuit design workflow

**Visuals:**
- Blue Pill board reference
- Circuit-synth code preview
- Generated KiCad schematic/PCB

### 2. Circuit-Synth Overview (2-3 minutes)
**Script Points:**
- What is circuit-synth: Python library for circuit design
- Key advantages: Version control, hierarchical design, component reuse
- **AI-powered workflow:** Built-in code review agent and component discovery
- Comparison to traditional EDA tools
- Integration with KiCad ecosystem

**Visuals:**
- Library architecture diagram
- Code examples showing syntax
- **AI agent interface demonstration**
- KiCad integration workflow

### 3. Blue Pill Analysis (2-3 minutes)
**Script Points:**
- Why Blue Pill: Popular, well-documented dev board
- Circuit sections: Power supply, MCU core, programming interface, I/O
- Component breakdown: STM32F103C8T6, TX6211B regulator, crystals, etc.
- Design challenges we'll solve

**Visuals:**
- Blue Pill schematic walkthrough
- Component identification
- Circuit section highlighting

### 4. Implementation - Power Supply (3-4 minutes)
**Script Points:**
- Start with hierarchical design approach
- **Use `/find-symbol` and `/find-footprint` commands** to discover components
- Create power supply subcircuit
- USB connector and protection
- TX6211B voltage regulator circuit
- Demonstrate component reuse patterns
- **Show AI agent code review in real-time**

**Code Demo:**
```python
@circuit
def power_supply(usb_5v, vcc_3v3, gnd):
    """USB to 3.3V power supply using TX6211B regulator"""
    # Implementation here
```

**Visuals:**
- Live coding session with AI assistance
- Component discovery commands in action
- Generated schematic updates
- AI agent feedback and suggestions

### 5. Implementation - STM32 Core (3-4 minutes)
**Script Points:**
- STM32F103C8T6 microcontroller circuit
- Crystal oscillator design (8MHz HSE, 32kHz LSE)
- Decoupling capacitor patterns  
- Reset circuit implementation

**Code Demo:**
```python
@circuit
def stm32_core(vcc_3v3, gnd, reset, swd_pins):
    """STM32F103C8T6 core circuit with crystals and decoupling"""
    # Implementation here
```

**Visuals:**
- MCU pinout reference
- Crystal circuit patterns
- Schematic generation in real-time

### 6. Implementation - Programming Interface (2-3 minutes)
**Script Points:**
- SWD debug header connections
- USB programming interface (D+/D- lines)
- Boot configuration jumpers
- Address USB D+ resistor issue

**Code Demo:**
```python
@circuit  
def programming_interface(stm32_pins, usb_conn, swd_header):
    """SWD and USB programming interfaces"""
    # Implementation here
```

### 7. Implementation - I/O and Assembly (2-3 minutes)
**Script Points:**
- GPIO headers (40 pins total)
- User LED and reset button
- Circuit assembly and net connections
- Final schematic generation

**Code Demo:**
```python
@circuit
def blue_pill_clone():
    """Complete Blue Pill development board"""
    # Assemble all subcircuits
```

### 8. Results and KiCad Generation (1-2 minutes)
**Script Points:**
- Generate complete KiCad project
- Schematic review and validation
- PCB layout preview (if implemented)
- File output and project structure

**Visuals:**
- KiCad schematic walkthrough
- Generated project files
- PCB preview/ratsnest view

### 9. Wrap-up and Next Steps (1 minute)
**Script Points:**
- Recap what we accomplished
- Circuit-synth advantages demonstrated
- Future video topics (ESP32, Arduino clones)
- Call to action: Try circuit-synth, subscribe

## Technical Preparation Needed

### Circuit-Synth Library Modifications
**Likely Requirements:**
- [ ] STM32F103C8T6 symbol verification/creation
- [ ] TX6211B regulator symbol/footprint
- [ ] Crystal oscillator patterns
- [ ] USB connector improvements
- [ ] Header connector templates
- [ ] Decoupling capacitor patterns

### KiCad Symbol/Footprint Requirements
**Need to verify availability:**
- [ ] STM32F103C8T6 (LQFP-48)
- [ ] TX6211B (SOT23-5)
- [ ] 8MHz crystal (HC49 or similar)
- [ ] 32.768kHz crystal (cylindrical)
- [ ] USB Micro connector
- [ ] Pin headers (2.54mm spacing)

### Demo Environment Setup
- [ ] Screen recording setup (clean desktop, proper resolution)
- [ ] KiCad installation and library verification
- [ ] Circuit-synth development environment
- [ ] Code editor with syntax highlighting
- [ ] Examples and reference materials organized

## Video Production Notes

### Recording Quality
- **Resolution:** 1080p minimum, 4K preferred for code clarity
- **Audio:** Clear narration, avoid background noise
- **Code visibility:** Large fonts, high contrast themes

### Editing Considerations
- **Pace:** Allow time for viewers to follow code
- **Cuts:** Remove compilation waits, file saves
- **Graphics:** Add callouts for important code sections
- **Transitions:** Smooth between code and KiCad views

### Call-to-Action Strategy
- **Repository link:** Direct viewers to circuit-synth GitHub
- **Documentation:** Link to getting started guide
- **Community:** Discord/forum for questions
- **Future content:** Tease upcoming dev board series

## Success Metrics

### Video Performance
- **Views:** Target 10K+ views in first month
- **Engagement:** High watch time percentage
- **Comments:** Technical questions and discussions
- **Conversions:** GitHub stars, library downloads

### Library Adoption
- **GitHub activity:** Issues, PRs, stars
- **Community growth:** New users trying examples
- **Technical feedback:** Feature requests, bug reports

This comprehensive plan provides structure for creating a compelling technical demonstration that showcases circuit-synth capabilities while building a practical Blue Pill clone.