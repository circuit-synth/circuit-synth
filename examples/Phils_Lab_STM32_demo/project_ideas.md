# Circuit-Synth Development Board Demo Series - Project Ideas

**Date:** 2025-07-29
**Goal:** Demonstrate circuit-synth library effectiveness through popular dev board clones

## Core Concept: Multi-Manufacturer Dev Board Series

### Proposed Board Series
1. **STM32 Blue Pill Clone** (Starting with Phil's Lab tutorial)
   - STM32F103C8T6 microcontroller
   - Minimal development board
   - USB programming interface
   - Basic I/O and power management

2. **ESP32 DevKit Clone**
   - ESP32-WROOM-32 module
   - USB-to-serial programming
   - WiFi/Bluetooth capabilities
   - Standard pinout compatibility

3. **Arduino Uno R3 Clone**
   - ATmega328P microcontroller
   - USB-to-serial interface
   - Standard Arduino shield compatibility
   - Classic development platform

4. **NXP Development Kit Clone**
   - NXP microcontroller (TBD which family)
   - Debugging interface
   - Peripheral breakouts
   - Professional development features

## Circuit-Synth Demonstration Opportunities

### Library Strengths to Showcase
- **Component Reuse Patterns:** Common circuits (power supplies, programming interfaces) across different boards
- **Hierarchical Design:** Modular subcircuits that can be mixed and matched
- **Cross-Platform Compatibility:** Same Python patterns work for different MCU families
- **KiCad Integration:** Automatic schematic and PCB generation
- **Professional Workflow:** Version control, testing, documentation

### Technical Features to Highlight
- **Annotation System:** Automatic documentation from docstrings
- **Ratsnest Generation:** Visual connection planning for PCB layout
- **Docker Integration:** Containerized development environment
- **AI Agent Integration:** Claude Code assistance for circuit design

## Implementation Strategy

### Phase 1: STM32 Blue Pill (Current)
- Follow Phil's Lab tutorial approach
- Implement in circuit-synth Python
- Generate complete KiCad project
- Document process and patterns

### Phase 2: Pattern Extraction
- Identify common subcircuits across boards
- Create reusable component library
- Establish design patterns and conventions
- Build component database

### Phase 3: Additional Boards
- Implement ESP32, Arduino, NXP variants
- Demonstrate component reuse
- Show cross-platform design principles
- Build comprehensive example library

### Phase 4: Advanced Features
- Multi-board system designs
- Interface compatibility testing
- Performance comparisons
- Educational materials

## User Ideas and Brainstorming

### 2025-07-29 Session
- **Multi-manufacturer dev board series** - Great way to show circuit-synth versatility
- **Blue Pill clone starting point** - Popular, well-documented reference design
- **Component reuse demonstration** - Power supplies, programming interfaces shared across platforms
- **Professional development workflow** - Version control, automated generation, documentation
- **STM32-base project as reference** - Comprehensive documentation and specifications available
- **Real-world clone target** - Blue Pill is widely used, well-documented dev board
- **YouTube video production** - Create compelling demo video showing circuit-synth workflow
- **Live coding demonstration** - Show real-time circuit design and KiCad generation
- **Educational content strategy** - Build series of dev board clones for learning
- **AI agent integration** - Circuit-synth specialized agent already exists for code review and guidance
- **Slash command tools** - `/find-symbol` and `/find-footprint` commands for KiCad component discovery
- **Professional AI workflow** - Demonstrate AI-assisted circuit design for modern development

### AI Infrastructure Discovery (2025-07-29)
- **Existing circuit-synth agent** - Comprehensive code reviewer with best practices guidance
- **Component discovery tools** - `/find-symbol` and `/find-footprint` slash commands ready to use
- **Cross-platform support** - macOS/Linux KiCad library search capabilities
- **Live demonstration potential** - Can show AI-assisted design process in video
- **Professional workflow showcase** - Modern AI-assisted circuit development

### YouTube Video AI Enhancement Ideas
- **Real-time AI code review** - Show circuit-synth agent analyzing our Blue Pill code
- **Component discovery demo** - Use `/find-symbol STM32F103` and `/find-footprint LQFP` live
- **Best practices guidance** - Let AI agent guide hierarchical design decisions
- **Educational value** - Demonstrate how AI can teach proper circuit-synth patterns
- **Competitive advantage** - Show circuit-synth's unique AI-native workflow

### JLC Parts Integration Idea (2025-07-29)
- **Repository discovery** - https://github.com/yaqwsx/jlcparts provides JLC PCB parts database
- **Component recommendation potential** - Could suggest available/cost-effective parts to users
- **Manufacturing integration** - Bridge design-to-production workflow
- **AI enhancement opportunity** - Agent could recommend JLC-compatible components
- **Cost optimization** - Help users select parts that are in stock and affordable

### JLC Parts Data Structure Analysis
- **Available fields** - LCSC part number, categories, manufacturer, package, stock, price, datasheet
- **API integration** - Python interface for programmatic component lookup
- **Parametric search** - Filter by package type, category, stock availability
- **Real-time data** - Current stock levels and pricing information
- **BOM optimization** - Could auto-suggest in-stock alternatives for components
- **Manufacturing readiness** - Verify all components available before PCB production
- **JLC parts lookup results** - Found STM32G030F6P6TR with highest stock (118,548 units)
- **Alternative option** - STM32G030C8T6 in LQFP-48 package (54,611 units available)
- **Integration proven** - JLC parts search capability demonstrated for circuit-synth enhancement
- **Integration opportunity** - Could copy JLC parts logic into circuit-synth for component recommendations
- **Two approaches discovered** - API-based (requires keys) vs pre-processed database (no keys needed)
- **yaqwsx approach** - Downloads XLS/database files, processes to JSON, uses IndexedDB locally
- **No API keys needed** - Frontend uses pre-downloaded component database stored locally
- **Third approach idea** - Use Puppeteer to scrape JLCPCB search results directly
- **Web scraping option** - Query https://jlcpcb.com/parts/componentSearch?searchTxt=stm32g0 programmatically
- **Real-time data** - Would get current stock/pricing without API keys
- **STM32G4 lookup test** - Found STM32G431CBT6 (LQFP-48) with highest stock: 83,737 units
- **Web scraping proven** - Successfully extracted real-time availability data

### Blue Pill Clone Advantages for Demo
- **Simple but complete design** - Good complexity level for demonstration
- **Well-documented reference** - STM32-base project provides detailed specs
- **Popular target** - Developers will recognize and relate to the design
- **Clear component list** - Known parts with specific values and packages
- **Multiple circuit sections** - Power, MCU, programming, I/O for hierarchical demo

---
*Continue adding ideas and concepts as they come up during development*