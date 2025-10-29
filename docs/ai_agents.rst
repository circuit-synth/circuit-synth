AI Agents System
================

Circuit-Synth includes a comprehensive AI agent system designed to assist with circuit design, component selection, and development workflows.

Overview
--------

The agent system consists of specialized agents located in ``.claude/agents/`` that provide expert assistance for specific tasks:

- **Circuit Design**: Intelligent circuit architecture and component selection
- **Manufacturing**: JLCPCB parts sourcing and DFM validation
- **Simulation**: SPICE simulation setup and analysis
- **Development**: Code review, testing, and project management

Agent Categories
----------------

Circuit Design Agents
~~~~~~~~~~~~~~~~~~~~~

**circuit-architect**
  Master circuit design coordinator that orchestrates the entire design process from requirements to final implementation.

**circuit-generation-agent**
  Specialized in generating complete circuit-synth Python code from natural language descriptions.

**interactive-circuit-designer**
  Professional interactive circuit design agent for collaborative engineering partnership throughout the complete design lifecycle.

**circuit-project-creator**
  Master orchestrator for complete circuit project generation from natural language prompts.

Manufacturing & Sourcing
~~~~~~~~~~~~~~~~~~~~~~~~~

**component-guru**
  Component sourcing and manufacturing optimization specialist with real-time supplier data.

**jlc-parts-finder**
  Specialized agent for finding manufacturable components by searching JLCPCB availability and verifying KiCad symbol compatibility.

**dfm-agent**
  Design for Manufacturing (DFM) analysis and optimization specialist using real supplier data.

MCU Selection
~~~~~~~~~~~~~

**stm32-mcu-finder**
  STM32 microcontroller selection specialist with pin mapping expertise and peripheral requirement matching.

Simulation & Validation
~~~~~~~~~~~~~~~~~~~~~~~~

**simulation-expert**
  SPICE simulation and circuit validation specialist for testing designs before manufacturing.

**circuit-validation-agent**
  Circuit validation specialist that tests generated code execution and catches errors early.

**test-plan-creator**
  Circuit test plan generation and validation specialist for comprehensive testing procedures.

Development Tools
~~~~~~~~~~~~~~~~~

**contributor**
  Circuit-synth contributor onboarding and development assistant.

**first-setup-agent**
  Circuit-synth environment setup and configuration assistant for new users.

**circuit-syntax-fixer**
  Circuit syntax specialist that fixes code errors while preserving design intent.

Using Agents
------------

Agents are invoked through Claude Code's task system. Each agent has specific capabilities and tools optimized for its domain.

Basic Usage
~~~~~~~~~~~

Agents can be called directly when working in Claude Code:

.. code-block:: text

   User: "Find an STM32 with 3 SPI interfaces available on JLCPCB"

   Claude invokes stm32-mcu-finder agent which:
   1. Searches modm-devices database for STM32s with 3+ SPI
   2. Checks JLCPCB availability
   3. Provides options with pricing and stock levels

Agent Capabilities
------------------

Each agent has access to specific tools and knowledge:

- **Web Search**: Real-time component pricing and availability
- **File Operations**: Read/write circuit files and schematics
- **Code Execution**: Generate and test circuit code
- **Database Access**: Component libraries and datasheets
- **API Integration**: JLCPCB, DigiKey, and other supplier APIs

Examples
--------

Component Sourcing Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # User request: "Find a 3.3V LDO regulator on JLCPCB"

   # Agent (component-guru) response:
   {
       "part": "AMS1117-3.3",
       "jlcpcb_part": "C6186",
       "price_100": "$0.05",
       "stock": "In Stock",
       "symbol": "Regulator_Linear:AMS1117-3.3",
       "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
   }

Circuit Generation Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # User request: "Create a 5V to 3.3V power supply"

   # Agent (circuit-generation-agent) generates:
   from circuit_synth import *

   @circuit(name="power_supply_3v3")
   def power_supply_3v3():
       """5V to 3.3V linear regulator"""

       vin_5v = Net('VIN_5V')
       vout_3v3 = Net('VOUT_3V3')
       gnd = Net('GND')

       vreg = Component(
           symbol="Regulator_Linear:AMS1117-3.3",
           ref="U",
           footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
       )

       # ... rest of circuit

Agent Architecture
------------------

Agents use a markdown-based configuration system:

.. code-block:: markdown

   ---
   name: agent-name
   description: Agent purpose and capabilities
   tools: ["WebSearch", "Read", "Write", "Bash"]
   model: claude-sonnet-4-5
   ---

   # Agent Instructions

   Detailed instructions for the agent's behavior and expertise.

Best Practices
--------------

When to Use Agents
~~~~~~~~~~~~~~~~~~

- **Component Selection**: Use component-guru or jlc-parts-finder
- **MCU Selection**: Use stm32-mcu-finder for STM32 chips
- **Circuit Generation**: Use circuit-generation-agent for complete designs
- **Validation**: Use circuit-validation-agent before manufacturing
- **DFM Analysis**: Use dfm-agent for manufacturability checks

Agent Workflow Tips
~~~~~~~~~~~~~~~~~~~

1. **Be Specific**: Provide detailed requirements (voltage, current, package type)
2. **Include Constraints**: Specify JLCPCB availability, price targets, stock requirements
3. **Verify Results**: Always review agent suggestions before manufacturing
4. **Iterate**: Agents can refine designs based on feedback

Limitations
-----------

- Agents rely on current database information (may be outdated)
- Component availability changes rapidly
- Always verify critical specifications in datasheets
- Test designs before manufacturing

Contributing
------------

To add or modify agents, see the agent development guide in the repository.

Agent files are located in:
- ``.claude/agents/`` - Agent definitions and instructions
- ``src/circuit_synth/ai_integration/`` - Agent implementation code

See Also
--------

- :doc:`CONTRIBUTING` - Contributing to circuit-synth
- :doc:`quickstart` - Getting started guide
- GitHub Repository: https://github.com/circuit-synth/circuit-synth
