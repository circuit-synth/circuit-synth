# PRD: Circuit Generation from Single Prompt Workflow

**Version**: 1.0  
**Date**: 2025-01-27  
**Author**: Circuit-Synth Development Team

## Overview
Create a streamlined workflow where users can generate complete, working circuit-synth projects from a single natural language prompt (e.g., "make a circuit board with stm32 with 3 spi peripherals with 1 imu on each spi, add a usb-c").

## Problem Statement
Current circuit generation workflow has several issues:
- Takes too long (4+ minutes for simple circuits)
- Uses expensive Sonnet model for all agents
- Generates invalid circuit-synth code that fails to run
- No validation or error correction
- Missing essential slash commands
- No transparency in design decisions

## Success Criteria
- Complete workflow under 2 minutes
- Generated code runs successfully with `uv run main.py`
- Transparent design decisions visible to user
- All generated projects use hierarchical structure
- 95% success rate for common circuit requests

## Core Requirements

### 1. Agent Architecture
- **Single Orchestrator Agent**: `circuit-project-creator` (Haiku model)
- **Triggers when**: User requests circuit design from scratch
- **Workflow**: orchestrator → stm32-finder → circuit-generation → validation → syntax-fixer (if needed)

### 2. Project Structure Output
```
{project_name}/
├── main.py              # Top-level circuit orchestration
├── power_supply.py      # Power regulation subcircuit  
├── mcu.py              # Microcontroller subcircuit
├── peripherals/        # Peripheral subcircuits
│   ├── imu_spi1.py
│   ├── imu_spi2.py
│   └── imu_spi3.py
├── usb.py              # USB connectivity subcircuit
├── logs/               # Agent workflow logs
│   └── {timestamp}_workflow.json
├── design_decisions.md # Transparent design documentation
└── README.md           # Generated project documentation
```

### 3. Agent Specifications

#### A. `circuit-project-creator` (Orchestrator) - NEW
- **Model**: Haiku
- **Responsibilities**: 
  - Parse user prompt and extract requirements
  - Create project directory structure
  - Generate design_decisions.md in real-time
  - Coordinate all sub-agents with proper handoffs
  - Create comprehensive workflow logs
  - Present final results to user
- **Tools**: All (`["*"]`)
- **Triggers**: Natural language circuit design requests

#### B. `stm32-mcu-finder` - UPDATE
- **Model**: Haiku (change from current)
- **Responsibilities**: STM32 selection based on peripheral requirements
- **Current status**: Exists, needs model change to Haiku

#### C. `circuit-generation-agent` - UPDATE
- **Model**: Haiku (change from current Sonnet)
- **Responsibilities**: Generate circuit-synth Python code
- **Must generate**: Hierarchical structure with proper @circuit decorators
- **Current status**: Exists, needs model change to Haiku

#### D. `circuit-validation-agent` - NEW
- **Model**: Haiku
- **Responsibilities**: 
  - Run `uv run main.py` in generated project directory
  - Capture error messages and stack traces
  - Report validation results with context
  - No design changes, only validation
- **Tools**: Bash, Read

#### E. `circuit-syntax-fixer` - NEW
- **Model**: Haiku  
- **Responsibilities**: 
  - Fix syntax errors only (no design changes)
  - Handle: Net creation outside @circuit, missing imports, syntax errors
  - Max 3 attempts per project
  - Must preserve original design intent
- **Tools**: Read, Edit, MultiEdit, Bash

### 4. Missing Slash Commands (High Priority Implementation)

#### A. `/find-symbol <query>`
- **Purpose**: Search KiCad symbol libraries
- **Implementation**: Grep-based search across KiCad library paths
- **Output**: List of matching symbols with library paths
- **Template Location**: `.claude/commands/circuit-design/find-symbol.md`

#### B. `/find-footprint <query>`
- **Purpose**: Search KiCad footprint libraries
- **Implementation**: Grep-based search across KiCad footprint paths
- **Output**: List of matching footprints with library paths
- **Template Location**: `.claude/commands/circuit-design/find-footprint.md`

#### C. `/find-parts <query>`
- **Purpose**: Search JLCPCB/component databases
- **Implementation**: Integration with existing JLCPCB search functionality
- **Output**: Components with stock, pricing, and KiCad compatibility
- **Template Location**: `.claude/commands/manufacturing/find-parts.md`

#### D. `/find-mcu <requirements>`
- **Purpose**: STM32 search wrapper for common queries
- **Implementation**: Wrapper around stm32-mcu-finder agent
- **Output**: Recommended STM32 with reasoning
- **Template Location**: `.claude/commands/manufacturing/find-mcu.md`

### 5. Logging & Transparency

#### A. Real-time Design Documentation (`design_decisions.md`)
Generated in real-time during workflow, showing:
- **Component Selections**: MCU choice, peripheral selections, passives
- **Rationale**: Why each component was chosen vs alternatives
- **Pin Assignments**: GPIO mapping and reasoning
- **Power Supply Design**: Voltage levels, current calculations
- **Design Rule Compliance**: Which rules applied and how
- **Manufacturing Notes**: JLCPCB compatibility, stock levels
- **Alternative Components**: Backup options if primary unavailable

#### B. Workflow Logging (`logs/{timestamp}_workflow.json`)
```json
{
  "timestamp": "2025-01-27T10:30:00Z",
  "user_prompt": "make a circuit board with stm32 with 3 spi peripherals with 1 imu on each spi, add a usb-c",
  "project_name": "stm32_multi_imu_board",
  "agents_executed": [
    {
      "agent": "stm32-mcu-finder", 
      "start_time": "2025-01-27T10:30:15Z",
      "end_time": "2025-01-27T10:30:45Z",
      "duration_seconds": 30,
      "result": "STM32F407VET6 selected",
      "reasoning": "Has 3 SPI peripherals (SPI1, SPI2, SPI3), good JLCPCB stock (500+ units)",
      "alternatives_considered": ["STM32F411CEU6", "STM32F405RGT6"]
    },
    {
      "agent": "circuit-generation-agent",
      "start_time": "2025-01-27T10:30:45Z", 
      "end_time": "2025-01-27T10:31:30Z",
      "duration_seconds": 45,
      "result": "Generated 6 circuit files",
      "files_created": ["main.py", "mcu.py", "power_supply.py", "usb.py", "peripherals/imu_spi1.py", "peripherals/imu_spi2.py", "peripherals/imu_spi3.py"]
    }
  ],
  "validation_attempts": [
    {
      "attempt": 1,
      "status": "failure",
      "error": "CircuitSynthError: Cannot create Net('VCC_5V'): No active circuit found",
      "fix_applied": "Moved Net creation inside @circuit decorator"
    },
    {
      "attempt": 2, 
      "status": "success"
    }
  ],
  "total_duration_seconds": 120,
  "final_status": "success",
  "files_generated": 7,
  "kicad_project_generated": true
}
```

### 6. Validation & Error Correction Logic

#### A. Validation Process
1. **Execute Test**: Run `uv run main.py` in generated project directory
2. **Success Path**: If runs without errors, workflow complete
3. **Failure Path**: Capture full error message and stack trace

#### B. Error Correction Process
1. **Parse Error**: Identify error type (syntax, circuit-synth API, import, etc.)
2. **Context Preservation**: Maintain original design intent and component selections
3. **Targeted Fix**: Apply minimal changes to resolve specific error
4. **Re-validation**: Test fix with `uv run main.py`
5. **Iteration**: Repeat up to 3 times total
6. **Learning**: Log failures for future agent improvement

#### C. Common Error Patterns & Fixes
- **Net Creation Outside Circuit**: Move Net() calls inside @circuit functions
- **Missing Imports**: Add required circuit-synth imports
- **Invalid Pin References**: Fix component pin naming
- **Decorator Issues**: Ensure proper @circuit usage
- **Syntax Errors**: Fix Python syntax without changing circuit design

### 7. User Experience

#### A. Visible to User (Real-time Updates)
- Agent workflow progress ("🔍 Finding STM32 with 3 SPI interfaces...")
- Design decisions being made ("✅ Selected STM32F407VET6 - has SPI1, SPI2, SPI3")
- Component selections and rationale
- Final project structure and files created

#### B. Hidden from User (Background Processing)
- Validation attempts and failures
- Syntax error fixes and iterations
- Internal agent communication
- Low-level debugging information

#### C. Final Output
- **Project Directory**: Complete working circuit-synth project
- **Success Summary**: What was created and key specifications
- **Next Steps**: How to run the project and open in KiCad
- **Design Documentation**: Link to design_decisions.md for details

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create missing slash command templates
- [ ] Update existing agents to use Haiku model
- [ ] Test individual agent performance with Haiku

### Phase 2: New Agents (Week 2) 
- [ ] Implement `circuit-project-creator` orchestrator agent
- [ ] Create `circuit-validation-agent`
- [ ] Create `circuit-syntax-fixer` agent
- [ ] Build logging and transparency system

### Phase 3: Integration (Week 3)
- [ ] Connect all agents in workflow
- [ ] Implement real-time design documentation
- [ ] Add comprehensive error handling
- [ ] Test with original user prompt from logs

### Phase 4: Optimization (Week 4)
- [ ] Performance tuning and optimization  
- [ ] Edge case handling and robustness
- [ ] User experience improvements
- [ ] Documentation and examples

## Success Metrics
- **Performance**: <2 minute total workflow time
- **Reliability**: 95% success rate for common circuit types
- **Code Quality**: All generated projects run successfully
- **Transparency**: Design decisions clearly documented
- **User Satisfaction**: Positive feedback on workflow experience

## Risk Mitigation
- **Agent Failure**: Graceful degradation and error messaging
- **Component Availability**: Alternative component recommendation
- **Validation Loops**: Maximum 3 fix attempts to prevent infinite loops
- **User Expectations**: Clear communication of what the workflow produces

## Future Enhancements (Post-MVP)
- Support for non-STM32 microcontrollers (ESP32, etc.)
- Advanced circuit types (RF, high-speed digital, power electronics)
- Integration with PCB manufacturing quotes
- Automatic test code generation
- Version control integration for iterative design

---

**Approval Required From:**
- [ ] Product Owner
- [ ] Technical Lead  
- [ ] User Experience Lead

**Implementation Begins:** Upon approval
**Target Completion:** 4 weeks from approval date