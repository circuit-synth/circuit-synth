# Circuit Generation Workflow - Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** 2025-08-10  
**Author:** Circuit-Synth Development Team  

## Executive Summary

This PRD defines a robust, transparent, and validated circuit generation workflow that transforms natural language prompts into complete, manufacturable circuit projects. The workflow emphasizes complete transparency through comprehensive logging, component validation, and automated testing.

## Problem Statement

The current circuit generation workflow has several critical issues:
- **No transparency**: No logging of agent decisions or design processes
- **Missing component validation**: Components not verified for JLCPCB/DigiKey availability or KiCad library presence
- **Invalid outputs**: Agents claim to generate files but only create useless placeholder files
- **No code validation**: Generated Python code not tested for execution
- **Incomplete designs**: Missing power management and supporting components in initial design
- **Wrong scope**: Generating PCB routing instead of focusing on circuit-synth code generation

## Success Criteria

**Primary Success Metric:** Generate working Python circuit-synth code that:
1. Executes without errors (`uv run main.py` passes)
2. Uses only components available in JLCPCB/DigiKey stock
3. Uses only KiCad library symbols/footprints that exist
4. Includes complete power management and supporting circuits
5. Creates proper project structure matching `/circuit-synth3/example_project/circuit-synth/`

**Secondary Metrics:**
- Complete transparency through timestamped logs
- 3-attempt validation with syntax fixing
- Modular subcircuit architecture
- Comprehensive component verification

## Detailed Requirements

### 1. Logging and Transparency System

**Requirement:** All agents must create timestamped markdown log files documenting every decision and action.

**Implementation Details:**
- **Log Location:** `logs/[timestamp]/[agent_name]_[session_id].md`
- **Log Format:** Markdown with structured sections
- **Log Content Must Include:**
  - Timestamp for each major action
  - Component search queries and results
  - Decision rationale for component selection
  - Availability checks and results
  - KiCad symbol/footprint verification
  - Code generation attempts
  - Validation results and error messages
  - Inter-agent communication and handoffs

**Example Log Structure:**
```markdown
# STM32-MCU-Finder Agent Log
**Session ID:** uuid-here  
**Start Time:** 2025-08-10T14:30:00Z  

## Component Search Request
**Query:** STM32 with 3 SPI peripherals  
**Requirements:** JLCPCB availability, LQFP package preferred  

## Search Results
### Candidate 1: STM32F407VET6
- **JLCPCB Part:** C116735  
- **Stock Status:** 5,847 units (✅ Available)  
- **Price:** $8.50 @ qty 10  
- **KiCad Symbol:** MCU_ST_STM32F4:STM32F407VETx (✅ Verified)  
- **SPI Peripherals:** SPI1, SPI2, SPI3 (✅ Meets requirement)  

## Decision
**Selected:** STM32F407VET6  
**Rationale:** Best balance of features, availability, and cost  
```

### 2. Component Validation Workflow

**Requirement:** Validate component availability and KiCad library presence after circuit design, with iterative refinement.

**Validation Process:**
1. **Initial Circuit Design:** Generate complete circuit with preferred components
2. **Component Verification:** Check each component for:
   - JLCPCB/DigiKey stock availability
   - KiCad symbol existence and exact naming
   - KiCad footprint existence and exact naming
   - Price within reasonable range
3. **Design Refinement:** If components fail validation:
   - Find suitable alternatives
   - Modify circuit design as needed
   - Re-validate until all components pass
   - Allow agent back-and-forth for optimization

**Component Search Integration:**
- Use existing STM32 search helper for microcontrollers
- Use JLCPCB integration for passive components
- Use DigiKey integration for specialty components
- Cache search results to avoid repeated API calls

### 3. Project Structure and Output Format

**Requirement:** Generate modular subcircuit files in organized project directory structure.

**Target Directory Structure:**
Based on `/Users/shanemattner/Desktop/circuit-synth3/example_project/circuit-synth/`:
```
[project_name]/
├── main.py                    # Main circuit orchestration file  
├── power_supply.py            # Voltage regulation, power management
├── mcu.py                     # Microcontroller and supporting circuits
├── spi_imu_1.py              # IMU on SPI1
├── spi_imu_2.py              # IMU on SPI2  
├── spi_imu_3.py              # IMU on SPI3
├── usb_connector.py          # USB-C connector with ESD protection
├── debug_header.py           # SWD debug connector
├── crystal.py                # Crystal oscillator circuit
├── reset_circuit.py          # Reset button and circuits
├── README.md                 # Project documentation
└── logs/                     # Agent execution logs
    └── [timestamp]/
        ├── orchestrator_[session].md
        ├── component_search_[session].md
        └── circuit_generator_[session].md
```

**File Generation Requirements:**
- **main.py:** Import all subcircuits, create hierarchical circuit, include @circuit decorator
- **Subcircuit files:** Self-contained circuits with proper imports, decorators, and return statements
- **README.md:** Project overview, BOM summary, setup instructions
- **No PCB routing files:** Focus purely on circuit-synth Python code generation

### 4. Code Validation and Syntax Fixing

**Requirement:** Validate generated code execution and fix syntax errors automatically.

**Validation Process:**
1. **Primary Validation:** Run `uv run main.py` in project directory
2. **Success Case:** Code executes without errors → workflow complete
3. **Failure Case:** Pass to circuit-syntax-fixer agent with error details
4. **Retry Limit:** Maximum 3 attempts at syntax fixing
5. **Final Failure:** Escalate to user with detailed error log

**Circuit-Syntax-Fixer Agent Requirements:**
- Receive full error traceback and generated code
- Fix syntax errors while preserving design intent
- Focus on common issues: import errors, missing decorators, net connection problems
- Log all fixes attempted and reasoning
- Return corrected code with explanation of changes

### 5. Agent Architecture and Workflow

**Requirement:** Orchestrated multi-agent workflow with clear responsibilities and handoffs.

**Agent Roles and Responsibilities:**

**1. Circuit-Project-Creator (Master Orchestrator)**
- Parse user requirements and create project plan
- Coordinate all other agents in proper sequence
- Create project directory structure
- Generate main.py orchestration file
- Monitor overall progress and handle escalations
- **Key Outputs:** Project structure, main.py, coordination logs

**2. Component-Search Agents**
- STM32-MCU-Finder: Microcontroller selection with peripheral verification
- Component-Guru: General component search and sourcing
- JLC-Parts-Finder: JLCPCB-specific component verification
- **Key Outputs:** Component specifications, availability confirmation, pricing

**3. Circuit-Generation-Agent**  
- Generate individual subcircuit Python files
- Ensure proper circuit-synth syntax and patterns
- Include all supporting components (power, decoupling, protection)
- Create proper net connections and component references
- **Key Outputs:** Subcircuit .py files, circuit documentation

**4. Circuit-Validation-Agent**
- Execute code validation (`uv run main.py`)
- Verify component symbol/footprint existence
- Check electrical connectivity and completeness
- **Key Outputs:** Validation reports, error identification

**5. Circuit-Syntax-Fixer**
- Fix syntax errors while preserving design intent
- Handle import errors, decorator problems, net connection issues
- **Key Outputs:** Corrected code, fix documentation

**Agent Coordination Protocol:**
1. **Orchestrator** creates project plan and directory
2. **Component-Search** agents find and verify all required components
3. **Circuit-Generation** creates all subcircuit files
4. **Orchestrator** generates main.py with proper imports
5. **Circuit-Validation** tests code execution
6. **Circuit-Syntax-Fixer** handles any errors (max 3 attempts)
7. **Orchestrator** finalizes project and creates README

### 6. Quality Assurance and Testing

**Validation Checkpoints:**
- [ ] All components verified in JLCPCB/DigiKey stock
- [ ] All KiCad symbols exist and are correctly named
- [ ] All KiCad footprints exist and are correctly named
- [ ] Python code executes without errors
- [ ] All nets properly connected
- [ ] Power management circuits included
- [ ] Supporting circuits (crystal, reset, debug) included
- [ ] Proper project structure created
- [ ] Comprehensive logs generated

**Automated Testing:**
- Code syntax validation via Python AST parsing
- Circuit connectivity verification
- Component availability API checks
- KiCad library symbol/footprint verification

## Technical Implementation Notes

### Logging System Implementation
```python
# Standard logging format for all agents
import logging
from datetime import datetime

def setup_agent_logging(agent_name, session_id):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = f"logs/{timestamp}"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f"{log_dir}/{agent_name}_{session_id}.md"
    
    # Configure markdown-formatted logging
    formatter = MarkdownFormatter()
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(f"{agent_name}_{session_id}")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    return logger
```

### Component Validation Integration
```python
# Component validation workflow
def validate_component(component_spec):
    validations = {
        'jlcpcb_stock': check_jlcpcb_availability(component_spec),
        'digikey_stock': check_digikey_availability(component_spec),
        'kicad_symbol': verify_kicad_symbol(component_spec.symbol),
        'kicad_footprint': verify_kicad_footprint(component_spec.footprint)
    }
    
    return all(validations.values()), validations
```

### Project Structure Generator
```python
def create_project_structure(project_name, components):
    base_path = Path(project_name)
    
    # Create flat directory structure (like example_project/circuit-synth/)
    directories = [
        base_path,  # Main project directory
        base_path / "logs"  # Logs subdirectory
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
```

## Risk Assessment and Mitigation

**High Risk:**
- **Component availability changes during generation:** *Mitigation - Cache checks and re-validate before final output*
- **KiCad library changes:** *Mitigation - Version pin KiCad libraries and verify symbols exist*
- **Agent coordination failures:** *Mitigation - Robust error handling and escalation procedures*

**Medium Risk:**
- **Performance with large component databases:** *Mitigation - Implement caching and parallel searches*
- **Complex circuit validation:** *Mitigation - Incremental validation at each step*

## Success Metrics and KPIs

**Primary KPIs:**
- **Code Execution Success Rate:** Target >95% of generated main.py files execute successfully
- **Component Validation Success:** Target >98% of components pass availability and KiCad checks
- **First-Attempt Success:** Target >80% of circuits work without syntax fixing iterations

**Secondary KPIs:**
- **Agent Coordination Efficiency:** Average workflow completion time <5 minutes
- **Log Completeness:** 100% of agent actions documented in logs
- **User Satisfaction:** Complete transparency and working outputs

## Implementation Timeline

**Phase 1 (Week 1):** Logging system and component validation infrastructure
**Phase 2 (Week 2):** Agent coordination and workflow orchestration
**Phase 3 (Week 3):** Code generation and syntax fixing integration
**Phase 4 (Week 4):** End-to-end testing and refinement

## Conclusion

This PRD defines a comprehensive circuit generation workflow that addresses all identified issues with the current system. The focus on transparency, validation, and modular architecture will ensure reliable, manufacturable circuit outputs that meet professional development standards.

The workflow transforms natural language prompts into production-ready circuit projects through systematic component validation, transparent logging, and automated quality assurance.