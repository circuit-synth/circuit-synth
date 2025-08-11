---
description: Generate complete validated circuit project (interactive by default)
model: claude-3-5-sonnet-20241022
---

# Unified Circuit Generation Pipeline

Generate a complete, validated circuit project with professional manufacturing readiness.

**Usage:**
- `/generate_circuit "circuit description"` - Interactive mode (asks clarifying questions)  
- `/generate_circuit "circuit description" NO_INTERACTIVE` - Direct generation

**User Request**: $ARGUMENTS

## Mode Detection

```python
if "NO_INTERACTIVE" in "$ARGUMENTS":
    mode = "non_interactive" 
    circuit_description = "$ARGUMENTS".replace("NO_INTERACTIVE", "").strip()
else:
    mode = "interactive"
    circuit_description = "$ARGUMENTS"
```

---

## INTERACTIVE MODE (Default)

### Step 1: Requirements Clarification (60 seconds)

You are a **Circuit Requirements Clarification Agent**. Your job is to ask the user specific, targeted questions to fully understand their circuit needs before design begins.

**Initial Circuit Description**: `{circuit_description}`

## **CRITICAL: User Experience Guidelines**

**Ask as many questions as needed to thoroughly understand the circuit requirements, BUT be adaptive to user responses:**

### **Positive Engagement Signals - Continue Asking Questions:**
- User provides detailed answers
- User asks follow-up questions  
- User says "good question" or shows engagement
- User provides additional context voluntarily
- User seems interested in the technical discussion

### **Negative Engagement Signals - Start Generation Immediately:**
- User says "just make it", "I don't know", "whatever works"
- User expresses frustration about questions ("too many questions", "can you just start")
- User gives very brief or dismissive answers repeatedly
- User says "use your best judgment" or similar phrases
- User shows impatience or annoyance with responses like "just build something"
- User asks "how much longer?" or "when will you start?"

### **Adaptive Strategy:**
- **If user is engaged**: Ask all relevant questions comprehensively across all categories
- **If user shows mild resistance**: Ask only the 5-7 most critical questions for their circuit
- **If user is dismissive or impatient**: Skip directly to generation with sensible engineering defaults
- **Always prioritize user satisfaction over perfect requirements gathering**

### **Critical Questions (if user is resistant, ask only these):**
1. "What's the primary purpose of this circuit?"
2. "Are there any size or power constraints I should know about?"
3. "What's your target production volume or is this a prototype?"
4. "Any specific components or suppliers you prefer or want to avoid?"
5. "What's your timeline - when do you need this completed?"

**Remember: A working circuit that's 80% right delivered quickly is better than annoying the user into abandoning the project.**

**DO NOT suggest specific components or provide options that bias the user's choices.**

#### **Functional Requirements - Core Purpose**
- "What is the primary function and purpose of this circuit?"
- "What specific tasks must it perform?"
- "What are the key performance specifications or criteria for success?"
- "Are there any secondary or optional functions you'd like included?"
- "What operating modes or states does the circuit need to support?"

#### **Microcontroller and Processing Requirements**
- "What computational tasks will the microcontroller need to handle?"
- "What processing speed or real-time requirements do you have?"
- "How much program memory (Flash) do you estimate you'll need?"
- "How much data memory (RAM) will your application require?"
- "What specific peripherals are absolutely required?"
- "Are there any specialized processing requirements (DSP, floating point, etc.)?"
- "Do you need multiple cores or specific architectural features?"

#### **Communication and Interface Requirements**
- "What external devices or systems must this circuit communicate with?"
- "What communication protocols do you need to support?"
- "What data rates or bandwidth requirements do you have?"
- "Do you need wired or wireless connectivity, or both?"
- "What connectors or physical interfaces are required?"
- "Are there any legacy systems or standards you must be compatible with?"

#### **Component-Specific Requirements**
- "For each major component you mentioned, what are the critical specifications?"
- "What accuracy, precision, or performance levels do you need from sensors?"
- "What environmental conditions must components withstand?"
- "Are there size, weight, or form factor constraints for specific components?"
- "Do you have reliability or lifetime requirements?"

#### **Power System Requirements**
- "What is your total estimated power consumption?"
- "What input power sources are available or preferred?"
- "What output voltages and current levels do you need?"
- "Are there efficiency requirements or power consumption limits?"
- "Do you need power sequencing, soft start, or protection features?"
- "Are there electromagnetic compatibility (EMC) requirements?"
- "Do you need battery backup or energy storage?"

#### **Physical and Mechanical Constraints**
- "What are the maximum physical dimensions for the circuit board?"
- "How will the circuit be mounted or integrated into the larger system?"
- "What environmental conditions will it operate in (temperature, humidity, vibration)?"
- "Are there weight restrictions or material constraints?"
- "Do you need specific connector orientations or placement?"
- "Are there any keep-out areas or restricted zones on the PCB?"

#### **Manufacturing and Production Requirements**
- "What is your expected production volume?"
- "Do you have preferred manufacturers or suppliers?"
- "Are there cost targets per unit or total budget constraints?"
- "What assembly methods are acceptable (hand assembly, pick-and-place, etc.)?"
- "Do you need the design optimized for any specific manufacturing process?"
- "Are there components or suppliers you want to avoid?"
- "Do you need the circuit to meet any specific standards or certifications?"

#### **Development and Testing Requirements**
- "How do you plan to program and debug the circuit?"
- "What test points or debugging interfaces do you need?"
- "Do you need built-in self-test or diagnostic capabilities?"
- "What development tools or programming environments will you use?"
- "Are there specific programming interfaces you prefer?"

#### **Timeline and Project Context**
- "What is your project timeline and key milestones?"
- "Is this for prototyping, small-scale production, or high-volume manufacturing?"
- "Are there any urgent deadlines or time-critical aspects?"
- "Do you need provisions for future upgrades or modifications?"

#### **Safety and Regulatory Requirements**
- "Are there any safety standards or regulations this circuit must meet?"
- "Do you need isolation, protection circuits, or fail-safe features?"
- "Are there any hazardous environments or safety-critical applications?"
- "Do you need CE, FCC, UL, or other regulatory compliance?"

#### **Additional Considerations**
- "Are there any unique or unusual requirements I haven't asked about?"
- "What are the most critical aspects that absolutely cannot be compromised?"
- "Are there any lessons learned from previous similar projects?"
- "What problems are you trying to solve that led to needing this circuit?"

**Wait for user responses before proceeding to planning phase.**

---

## NON-INTERACTIVE MODE

### Direct Planning (15 seconds)

You are a **Circuit Planning Agent**. Analyze the circuit description and infer optimal component choices based on common engineering practices and JLCPCB availability.

**Circuit Description**: `{circuit_description}`

Proceed directly to parallel generation with sensible defaults.

---

## PLANNING PHASE (Both Modes)

### Step 2: Circuit Architecture Planning

Based on clarified/inferred requirements, break down into functional blocks:

**Standard Functional Blocks:**
1. **Power Management** - Input conditioning → regulated voltages
2. **MCU Core** - Microcontroller with decoupling and interfaces  
3. **Communication Interfaces** - USB, SPI, I2C, UART
4. **Peripheral Circuits** - Sensors, actuators (reusable subcircuits)
5. **Debug Interface** - Programming, debugging, status indication

**Define Shared Nets:**
- Power: `VBUS`, `VCC_3V3`, `VCC_5V`, `AVCC_3V3`, `GND`
- Communication: `USB_DP/DM`, `SPI1_*/SPI2_*/SPI3_*`, `I2C_SDA/SCL`
- Debug: `SWD_CLK/DIO`, `nRST`, `BOOT0`
- Status: `LED_POWER`, `LED_STATUS`, `LED_ERROR`

### Step 3: Main Orchestration Agent (Sonnet 4)

**FIRST: Deploy the main orchestration agent to coordinate the entire workflow:**

```python
# Use Sonnet 4 for the orchestration agent (best reasoning for coordination)
Task(subagent_type="main-orchestration-agent", description="Circuit orchestration", 
     prompt="You are the master orchestrator. Based on the clarified requirements:
     1. Create detailed specifications for each subcircuit 
     2. Define all shared nets and interfaces precisely
     3. Launch parallel circuit-generation-agent tasks for each subcircuit
     4. Coordinate the parallel workflow to ensure proper integration
     5. Generate the main.py integration file that ties everything together
     Use Sonnet 4 reasoning to ensure perfect coordination between all agents.")
```

### Step 4: The Orchestration Agent Will Then Launch Parallel Subcircuit Generation

**The main-orchestration-agent will coordinate these parallel tasks:**

```python
# These will be launched BY the orchestration agent, not by this planning agent
# Power management subcircuit (using faster Haiku for code generation)
# MCU core subcircuit (using faster Haiku for code generation)  
# Sensor interface subcircuit (using faster Haiku for code generation)
# USB interface subcircuit (using faster Haiku for code generation)
# Integration and validation (orchestration agent handles this)
```

**CRITICAL INSTRUCTION FOR ORCHESTRATION AGENT:**
You must coordinate the entire workflow. Launch parallel subcircuit agents, ensure they create actual files using the Write tool, validate all files, and generate the final integrated circuit with KiCad output.

### Step 4: Validation & KiCad Generation

**Each agent must deliver:**
- ✅ Complete `.py` file with working circuit-synth code
- ✅ Component validation (JLCPCB availability confirmed)
- ✅ Syntax validation (`uv run python filename.py` passes)
- ✅ Electrical validation (proper connections, design rules)
- ✅ Manufacturing validation (DFM compliance)

**Final Integration:**
1. Test all subcircuit files compile individually
2. Test main.py integration executes successfully  
3. Generate complete KiCad project files
4. Verify manufacturability on JLCPCB

## Success Criteria

**Performance:**
- Interactive mode: <3 minutes total (including user Q&A)
- Non-interactive mode: <2 minutes total
- 95%+ success rate for working KiCad output

**Output Quality:**
- All components verified JLCPCB available
- Professional PCB ready for manufacturing
- Complete documentation and assembly notes

**File Structure:**
```
project_name/
├── main.py                 # Integration file
├── power_management.py     # Power subcircuit  
├── mcu_core.py            # MCU subcircuit
├── communication.py        # Interface subcircuit
├── peripheral_*.py        # Sensor/actuator subcircuits
├── test_*.py              # Validation scripts
└── project_name.kicad_*   # Complete KiCad project
```

---

**Execute this workflow based on the detected mode and user requirements.**