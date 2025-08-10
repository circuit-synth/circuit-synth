# Dead Code Analysis Command

## Usage
```
/dead-code-analysis [target-script]
```

## Description
Performs comprehensive dead code analysis by running ALL system functionality and observing which functions are actually called. This provides accurate utilization metrics by exercising:

1. **Core Circuit Generation** - Create multiple circuit types (resistor dividers, LED circuits, power supplies)
2. **KiCad Integration** - Generate schematics and PCBs with all placement algorithms
3. **Manufacturing Integration** - Test JLCPCB, DigiKey searches and caching
4. **Component Intelligence** - STM32 search, KiCad symbol lookup, footprint matching
5. **Quality Assurance** - FMEA analysis, DFM checks, comprehensive reporting
6. **CLI Tools** - All command-line utilities and debugging tools
7. **Import/Export** - JSON, netlist generation, bidirectional conversion
8. **PCB Tools** - Placement algorithms, routing, validation

## Parameters
- `target-script` (optional): Path to script to run for function call analysis. Defaults to comprehensive test suite.
- `--comprehensive`: Runs full system functionality test (default behavior)

## Output Files
- `function_calls.log`: Raw debug output from script execution
- `unique_function_calls.txt`: List of unique functions that were called
- `Dead_Code_Analysis_Report.md`: Comprehensive analysis report
- `*.backup`: Backup files for all instrumented source files

## Examples
```bash
# Analyze dead code using main.py
/dead-code-analysis

# Analyze using a specific test script
/dead-code-analysis test_suite.py

# Analyze using a custom script path
/dead-code-analysis examples/test_all_circuits.py
```

## Implementation
The command performs the following automated steps:

### 1. Function Instrumentation
- Scans all Python files in `src/circuit_synth/`
- Adds `logging.debug(f"CALLED: {function_name} in {file_path}")` to the start of every function
- Creates backup files (`.backup`) before modification
- Adds necessary import statements if missing
- Preserves existing function logic and formatting

### 2. Script Execution
- Runs the target script with debug logging enabled
- Captures all function calls to `function_calls.log`
- Handles large log files efficiently

### 3. Analysis & Reporting
- Extracts unique function calls from execution log
- Compares against all instrumented functions
- Groups suspected dead code by module/directory
- Generates comprehensive markdown report with:
  - Executive summary with statistics
  - Dead code grouped by impact
  - Removal recommendations
  - Safety considerations

## Expected Results
With comprehensive testing, expect realistic utilization rates:
- **Core circuit functionality**: 80-90% utilization
- **KiCad integration**: 60-70% utilization  
- **Manufacturing tools**: 40-60% utilization
- **CLI utilities**: 30-50% utilization
- **Dev/debug tools**: 10-30% utilization

Actual dead code categories likely include:
- Duplicate algorithm implementations (multiple placement/routing versions)
- Template and example code (not part of runtime)
- Unused development utilities and debugging helpers
- Legacy experimental features

## Interactive Regression Testing Guide
After analysis completes, the tool provides **interactive guidance** for regression testing:

1. **Cache Clearing**: Prompts to clear all caches for clean testing
2. **Core Tests**: Guides through critical circuit generation tests
3. **KiCad Verification**: Step-by-step KiCad integration testing
4. **Component Intelligence**: Optional component search testing
5. **Safety Decisions**: Advises whether it's safe to remove dead code

The guide ensures you **never break core functionality** by validating everything works before code removal.

## Safety Notes
- Creates backup files before modifying source code
- Only adds logging statements, doesn't change logic
- Can be run multiple times safely
- Backups can be restored if needed:
  ```bash
  # Restore all backups
  find . -name "*.backup" | while read backup; do
    original="${backup%.backup}"
    mv "$backup" "$original"
  done
  ```

## Cleanup Workflow
After analysis:
1. Review the generated report
2. Start with highest-impact dead modules (most functions, zero usage)
3. Search git history for any external references
4. Remove dead code in phases with testing
5. Re-run analysis to track progress

## Command Implementation
This command is implemented via:
- **Main script**: `scripts/dead-code-analysis.py` - Python implementation with AST parsing
- **Shell wrapper**: `scripts/dead-code-analysis.sh` - Simple command-line interface

### Manual Usage
```bash
# From repository root
python scripts/dead-code-analysis.py [target-script]

# Or use the shell wrapper
./scripts/dead-code-analysis.sh [target-script]

# Restore backups if needed
python scripts/dead-code-analysis.py --restore-backups
```

## Comprehensive Test Implementation

To get accurate results, the analysis creates and runs these comprehensive test scripts:

### Core Functionality Test Script
```python
# test_comprehensive_functionality.py
from circuit_synth import *

def test_basic_circuits():
    """Test basic circuit creation and all core functionality"""
    
    # Resistor divider circuit
    @circuit(name="resistor_divider")
    def resistor_divider():
        r1 = Component(symbol="Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r2 = Component(symbol="Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        
        vin = Net('VIN')
        vout = Net('VOUT') 
        gnd = Net('GND')
        
        r1[1] += vin
        r1[2] += vout
        r2[1] += vout
        r2[2] += gnd
    
    circuit = resistor_divider()
    
    # Test all output formats
    circuit.generate_kicad_project("test_resistor_div", generate_pcb=True)
    circuit.generate_json_netlist("test_circuit.json")
    circuit.generate_kicad_netlist("test_circuit.net")
    
    return circuit

def test_manufacturing_integration():
    """Test all manufacturing and component search functionality"""
    from circuit_synth.manufacturing.jlcpcb.fast_search import search_jlc_components_web
    from circuit_synth.manufacturing.unified_search import find_parts
    from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query
    
    # JLCPCB search
    jlc_results = search_jlc_components_web("0.1uF 0603", max_results=5)
    
    # Unified component search
    unified_results = find_parts("10k resistor", sources="all")
    
    # STM32 peripheral search
    stm32_response = handle_stm32_peripheral_query("find stm32 with 2 spi and usb")
    
    # DigiKey integration (if configured)
    try:
        from circuit_synth.manufacturing.digikey.component_search import search_components
        dk_results = search_components("LM358")
    except:
        pass

def test_quality_assurance():
    """Test FMEA, DFM, and all quality assurance tools"""
    from circuit_synth.quality_assurance.fmea_analyzer import FMEAAnalyzer
    from circuit_synth.design_for_manufacturing.dfm_analyzer import DFMAnalyzer
    
    circuit = test_basic_circuits()
    
    # FMEA analysis
    try:
        fmea = FMEAAnalyzer()
        fmea_report = fmea.analyze_circuit(circuit)
    except Exception as e:
        print(f"FMEA test failed: {e}")
    
    # DFM analysis  
    try:
        dfm = DFMAnalyzer()
        dfm_report = dfm.analyze_circuit(circuit)
    except Exception as e:
        print(f"DFM test failed: {e}")

def test_all_cli_tools():
    """Test all CLI utilities and command-line tools"""
    import subprocess
    
    cli_commands = [
        ["uv", "run", "python", "-m", "circuit_synth.tools.jlc_fast_search_cli", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.debug_cli", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.quality_assurance.fmea_cli", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.project_management.new_project", "--help"],
    ]
    
    for cmd in cli_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            print(f"CLI test: {' '.join(cmd)} - {'✅' if result.returncode == 0 else '❌'}")
        except Exception as e:
            print(f"CLI test failed: {cmd} - {e}")

def test_pcb_algorithms():
    """Test all PCB placement and routing algorithms"""
    from circuit_synth.pcb.placement.force_directed import ForceDirectedPlacer
    from circuit_synth.pcb.placement.hierarchical_placement import HierarchicalPlacer
    from circuit_synth.pcb.placement.spiral_placement import SpiralPlacer
    
    circuit = test_basic_circuits()
    
    # Test different placement algorithms
    placement_algorithms = [
        "force_directed",
        "hierarchical", 
        "spiral",
        "connection_centric"
    ]
    
    for algorithm in placement_algorithms:
        try:
            circuit.generate_kicad_project(f"test_{algorithm}", 
                                         placement_algorithm=algorithm,
                                         generate_pcb=True)
        except Exception as e:
            print(f"Placement algorithm {algorithm} failed: {e}")

if __name__ == "__main__":
    print("🧪 Running comprehensive circuit-synth functionality tests...")
    test_basic_circuits()
    test_manufacturing_integration()
    test_quality_assurance()
    test_all_cli_tools()
    test_pcb_algorithms()
    print("✅ Comprehensive test suite completed")
```

### Hierarchical Circuit Test
```python
# test_hierarchical_comprehensive.py  
from circuit_synth import *

@circuit(name="power_supply_comprehensive")
def power_supply():
    """Complete 5V to 3.3V regulator with protection"""
    vreg = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U", 
                    footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    cap_in = Component(symbol="Device:C", ref="C", value="10uF", 
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF", 
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    
    # Add more components to exercise more functionality
    led_power = Component(symbol="Device:LED", ref="D", 
                         footprint="LED_SMD:LED_0603_1608Metric")
    r_led = Component(symbol="Device:R", ref="R", value="1k",
                     footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Create nets
    vin = Net('VIN_5V')
    vout = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Connect regulator
    vreg["VI"] += vin
    vreg["VO"] += vout
    vreg["GND"] += gnd
    
    # Connect capacitors
    cap_in[1] += vin
    cap_in[2] += gnd
    cap_out[1] += vout
    cap_out[2] += gnd
    
    # Power indicator LED
    r_led[1] += vout
    r_led[2] += led_power["A"]
    led_power["K"] += gnd

@circuit(name="mcu_comprehensive")
def mcu_circuit():
    """MCU circuit with crystal and decoupling"""
    # Use STM32 or similar complex component
    mcu = Component(symbol="MCU_ST_STM32F4:STM32F407VETx", ref="U",
                   footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm")
    
    # Crystal circuit
    crystal = Component(symbol="Device:Crystal", ref="Y", value="8MHz",
                       footprint="Crystal:Crystal_SMD_HC49-SD_HandSoldering")
    c1 = Component(symbol="Device:C", ref="C", value="22pF",
                   footprint="Capacitor_SMD:C_0603_1608Metric") 
    c2 = Component(symbol="Device:C", ref="C", value="22pF",
                   footprint="Capacitor_SMD:C_0603_1608Metric")
    
    # Decoupling capacitors
    bypass_caps = []
    for i in range(4):
        cap = Component(symbol="Device:C", ref="C", value="0.1uF",
                       footprint="Capacitor_SMD:C_0603_1608Metric")
        bypass_caps.append(cap)
    
    # Nets
    vcc = Net('VCC_3V3')
    gnd = Net('GND')
    osc_in = Net('OSC_IN')
    osc_out = Net('OSC_OUT')
    
    # Connect crystal
    crystal[1] += osc_in
    crystal[2] += osc_out
    c1[1] += osc_in
    c1[2] += gnd
    c2[1] += osc_out
    c2[2] += gnd
    
    # Connect MCU (simplified - just power/ground/crystal)
    mcu["VDD_1"] += vcc
    mcu["VDD_2"] += vcc
    mcu["VSS_1"] += gnd
    mcu["VSS_2"] += gnd
    mcu["PH0"] += osc_in
    mcu["PH1"] += osc_out
    
    # Connect decoupling capacitors
    for cap in bypass_caps:
        cap[1] += vcc
        cap[2] += gnd

@circuit(name="complete_system")
def complete_system():
    """Complete system integrating all subcircuits"""
    # Create shared nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    vin_5v = Net('VIN_5V')
    
    # Instantiate subcircuits
    power = power_supply()
    mcu = mcu_circuit()
    
    # Test hierarchical generation with all options
    return locals()

if __name__ == "__main__":
    print("🏗️ Testing hierarchical circuit generation...")
    system = complete_system()
    
    # Test multiple output formats and options
    system.generate_kicad_project("comprehensive_hierarchical", 
                                 placement_algorithm="hierarchical",
                                 generate_pcb=True)
    system.generate_json_netlist("hierarchical.json")
    
    print("✅ Hierarchical circuit test completed")
```

## Execution Strategy

1. **Create comprehensive test scripts** that exercise ALL major functionality
2. **Instrument all functions** with debug logging
3. **Run each test script** sequentially to capture function usage
4. **Aggregate results** from all test runs 
5. **Generate intelligent report** with realistic dead code identification

This approach will provide accurate utilization metrics by actually running the full system rather than relying on single simple test cases.

## IMPORTANT: Use Example Project for Analysis

**CRITICAL INSTRUCTION**: Always test using `/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth` with all functionalities.

- **DO NOT** create custom test scripts  
- **DO NOT** make your own logic
- **USE** the existing working example project that exercises real functionality
- **RUN** dead code analysis from within the example project directory  
- **TEST** all the actual circuit generation, KiCad integration, and manufacturing features

The example project contains:
- `main.py` - Complete ESP32-C6 development board
- `usb.py` - USB-C interface with protection  
- `power_supply.py` - 5V to 3.3V regulation
- `esp32c6.py` - ESP32-C6 MCU with support circuits
- `led_blinker.py` - Status LED with current limiting
- `debug_header.py` - Programming/debug interface

This exercises the real system functionality that users actually use, providing accurate dead code analysis results.

## Enhanced Test Coverage Strategy

The current analysis shows **10.8% utilization** - we need to add comprehensive test coverage to get accurate results for ALL functionality areas.

### Current Coverage Gaps (Need Testing)

1. **Manufacturing Integration (0% tested)**:
   - JLCPCB component search
   - DigiKey API integration  
   - Unified component search
   - Caching systems

2. **Quality Assurance (0% tested)**:
   - FMEA analysis
   - DFM analysis
   - Comprehensive reporting

3. **Simulation Tools (0% tested)**:
   - SPICE conversion
   - Circuit analysis
   - Testbench generation

4. **AI Integration (0% tested)**:
   - STM32 search helpers
   - Memory bank systems
   - Claude agents

5. **CLI Tools (0% tested)**:
   - Debug CLI
   - Component search CLI
   - Project management tools

6. **Advanced PCB Features (5% tested)**:
   - Force-directed placement
   - Spiral placement
   - Routing integration

### Enhanced Test Script Template

Add this comprehensive test to the example project:

```python
#!/usr/bin/env python3
"""
COMPREHENSIVE dead code analysis test - exercises ALL system functionality
"""

import sys
import os
sys.path.insert(0, '/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth')
os.chdir('/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth')

# Core circuit functionality (WORKING)
from usb import usb_port
from power_supply import power_supply
from esp32c6 import esp32c6
from circuit_synth import *

def test_manufacturing_integration():
    """Test ALL manufacturing and component search"""
    print("🔍 Testing manufacturing integration...")
    
    # JLCPCB search
    try:
        from circuit_synth.manufacturing.jlcpcb.fast_search import search_jlc_components_web
        results = search_jlc_components_web("0.1uF 0603", max_results=3)
        print(f"✅ JLCPCB search: Found {len(results)} components")
        
        from circuit_synth.manufacturing.jlcpcb.smart_component_finder import SmartComponentFinder
        finder = SmartComponentFinder()
        smart_results = finder.find_component("10k resistor")
        print(f"✅ Smart JLCPCB finder: {len(smart_results) if smart_results else 0} components")
        
    except Exception as e:
        print(f"⚠️ JLCPCB integration failed: {e}")
    
    # DigiKey integration
    try:
        from circuit_synth.manufacturing.digikey.component_search import search_components
        from circuit_synth.manufacturing.digikey.api_client import DigikeyApiClient
        
        client = DigikeyApiClient()
        dk_results = search_components("LM358")
        print(f"✅ DigiKey search: Found components")
        
    except Exception as e:
        print(f"⚠️ DigiKey integration failed: {e}")
    
    # Unified search
    try:
        from circuit_synth.manufacturing.unified_search import find_parts
        unified_results = find_parts("capacitor 0.1uF", sources="all")
        print(f"✅ Unified search: Found results from multiple sources")
        
    except Exception as e:
        print(f"⚠️ Unified search failed: {e}")

def test_quality_assurance_comprehensive():
    """Test ALL quality assurance and analysis tools"""
    print("🎯 Testing quality assurance systems...")
    
    # Create test circuit
    @circuit(name="test_qa_circuit")
    def qa_test_circuit():
        mcu = Component(symbol="MCU_ST_STM32F1:STM32F103C8Tx", ref="U",
                       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm")
        vreg = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U",
                        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
        cap = Component(symbol="Device:C", ref="C", value="0.1uF",
                       footprint="Capacitor_SMD:C_0603_1608Metric")
        
        vcc = Net('VCC_3V3')
        gnd = Net('GND')
        
        mcu["VDD"] += vcc
        mcu["VSS"] += gnd
        vreg["VO"] += vcc
        vreg["GND"] += gnd
        cap[1] += vcc
        cap[2] += gnd
    
    test_circuit = qa_test_circuit()
    
    # FMEA Analysis
    try:
        from circuit_synth.quality_assurance.fmea_analyzer import FMEAAnalyzer
        from circuit_synth.quality_assurance.enhanced_fmea_analyzer import EnhancedFMEAAnalyzer
        from circuit_synth.quality_assurance.comprehensive_fmea_report_generator import ComprehensiveFMEAReportGenerator
        
        fmea = FMEAAnalyzer()
        fmea_result = fmea.analyze_circuit(test_circuit)
        print("✅ Basic FMEA analysis completed")
        
        enhanced_fmea = EnhancedFMEAAnalyzer()
        enhanced_result = enhanced_fmea.analyze_circuit(test_circuit)
        print("✅ Enhanced FMEA analysis completed")
        
        report_gen = ComprehensiveFMEAReportGenerator()
        comprehensive_report = report_gen.generate_report(test_circuit)
        print("✅ Comprehensive FMEA report generated")
        
    except Exception as e:
        print(f"⚠️ FMEA analysis failed: {e}")
    
    # DFM Analysis
    try:
        from circuit_synth.design_for_manufacturing.dfm_analyzer import DFMAnalyzer
        from circuit_synth.design_for_manufacturing.comprehensive_dfm_report_generator import ComprehensiveDFMReportGenerator
        from circuit_synth.design_for_manufacturing.kicad_dfm_analyzer import KiCadDFMAnalyzer
        
        dfm = DFMAnalyzer()
        dfm_result = dfm.analyze_circuit(test_circuit)
        print("✅ Basic DFM analysis completed")
        
        dfm_report = ComprehensiveDFMReportGenerator()
        comprehensive_dfm = dfm_report.generate_report(test_circuit)
        print("✅ Comprehensive DFM report generated")
        
        kicad_dfm = KiCAdDFMAnalyzer()
        kicad_dfm_result = kicad_dfm.analyze_circuit(test_circuit)
        print("✅ KiCad DFM analysis completed")
        
    except Exception as e:
        print(f"⚠️ DFM analysis failed: {e}")

def test_simulation_comprehensive():
    """Test ALL simulation and analysis functionality"""
    print("⚡ Testing simulation systems...")
    
    # Create simple test circuit for simulation
    @circuit(name="simulation_test")
    def sim_test_circuit():
        r1 = Component(symbol="Device:R", ref="R", value="1k",
                      footprint="Resistor_SMD:R_0603_1608Metric")
        r2 = Component(symbol="Device:R", ref="R", value="2k", 
                      footprint="Resistor_SMD:R_0603_1608Metric")
        
        vin = Net('VIN')
        vout = Net('VOUT')
        gnd = Net('GND')
        
        r1[1] += vin
        r1[2] += vout
        r2[1] += vout
        r2[2] += gnd
    
    sim_circuit = sim_test_circuit()
    
    try:
        from circuit_synth.simulation.converter import SPICEConverter
        from circuit_synth.simulation.analysis import CircuitAnalysis
        from circuit_synth.simulation.simulator import CircuitSimulator
        from circuit_synth.simulation.testbench import TestbenchGenerator
        from circuit_synth.simulation.visualization import SimulationVisualizer
        
        # SPICE conversion
        spice_conv = SPICEConverter()
        spice_netlist = spice_conv.convert_circuit(sim_circuit)
        print("✅ SPICE conversion completed")
        
        # Circuit analysis
        analyzer = CircuitAnalysis()
        analysis_result = analyzer.analyze_circuit(sim_circuit)
        print("✅ Circuit analysis completed")
        
        # Simulation
        simulator = CircuitSimulator()
        sim_result = simulator.simulate_circuit(sim_circuit)
        print("✅ Circuit simulation completed")
        
        # Testbench generation
        testbench = TestbenchGenerator()
        tb_result = testbench.generate_testbench(sim_circuit)
        print("✅ Testbench generation completed")
        
        # Visualization
        visualizer = SimulationVisualizer()
        vis_result = visualizer.visualize_results(sim_result)
        print("✅ Simulation visualization completed")
        
    except Exception as e:
        print(f"⚠️ Simulation systems failed: {e}")

def test_ai_integration_comprehensive():
    """Test ALL AI integration features"""
    print("🧠 Testing AI integration...")
    
    try:
        # STM32 search
        from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query
        from circuit_synth.ai_integration.component_info.microcontrollers.modm_device_search import search_stm32
        
        stm32_result = handle_stm32_peripheral_query("stm32 with 2 spi and 1 i2c")
        print("✅ STM32 search helper completed")
        
        modm_result = search_stm32("stm32f4", peripherals=["spi", "i2c"])
        print("✅ MODM device search completed")
        
    except Exception as e:
        print(f"⚠️ STM32 integration failed: {e}")
    
    try:
        # Memory bank
        from circuit_synth.ai_integration.memory_bank.core import MemoryBankCore
        from circuit_synth.ai_integration.memory_bank.context import ContextManager
        from circuit_synth.ai_integration.memory_bank.git_integration import GitIntegration
        
        memory_core = MemoryBankCore()
        context_mgr = ContextManager()
        git_integ = GitIntegration()
        print("✅ Memory bank systems loaded")
        
    except Exception as e:
        print(f"⚠️ Memory bank failed: {e}")

def test_cli_tools_comprehensive():
    """Test ALL CLI tools and utilities"""
    print("🛠️ Testing CLI systems...")
    
    import subprocess
    
    cli_commands = [
        ["uv", "run", "python", "-m", "circuit_synth.tools.jlc_fast_search_cli", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.debug_cli", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.quality_assurance.fmea_cli", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.project_management.new_project", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.project_management.init_pcb", "--help"],
        ["uv", "run", "python", "-m", "circuit_synth.tools.utilities.circuit_creator_cli", "--help"],
    ]
    
    for cmd in cli_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=15)
            tool_name = cmd[-2].split('.')[-1]
            print(f"{'✅' if result.returncode == 0 else '❌'} CLI tool: {tool_name}")
        except Exception as e:
            print(f"⚠️ CLI tool failed: {cmd[-2]} - {e}")

def test_advanced_pcb_comprehensive():
    """Test ALL PCB placement algorithms and routing"""
    print("🏗️ Testing advanced PCB features...")
    
    # Create test circuit
    @circuit(name="pcb_test") 
    def pcb_test_circuit():
        components = []
        for i in range(6):  # More components to test placement
            comp = Component(symbol="Device:R", ref="R", value=f"{i+1}k",
                           footprint="Resistor_SMD:R_0603_1608Metric")
            components.append(comp)
        
        # Create interconnected network
        nets = [Net(f'NET_{i}') for i in range(4)]
        
        # Connect components in a network
        components[0][1] += nets[0]
        components[0][2] += nets[1]
        components[1][1] += nets[1] 
        components[1][2] += nets[2]
        components[2][1] += nets[2]
        components[2][2] += nets[3]
        
        for comp in components[3:]:
            comp[1] += nets[0]  # Common connection
            comp[2] += nets[3]  # Ground
    
    pcb_circuit = pcb_test_circuit()
    
    # Test all placement algorithms
    placement_algorithms = [
        "force_directed",
        "hierarchical",
        "spiral", 
        "connection_centric",
        "connectivity_driven",
        "spiral_hierarchical"
    ]
    
    for algorithm in placement_algorithms:
        try:
            pcb_circuit.generate_kicad_project(f"pcb_test_{algorithm}",
                                             placement_algorithm=algorithm,
                                             generate_pcb=True)
            print(f"✅ PCB placement: {algorithm}")
        except Exception as e:
            print(f"⚠️ PCB placement {algorithm} failed: {e}")
    
    # Test routing
    try:
        from circuit_synth.pcb.routing.freerouting_runner import FreeRoutingRunner
        from circuit_synth.pcb.routing.dsn_exporter import DSNExporter
        from circuit_synth.pcb.routing.ses_importer import SESImporter
        
        router = FreeRoutingRunner()
        dsn_exp = DSNExporter()
        ses_imp = SESImporter()
        print("✅ Routing systems loaded")
        
    except Exception as e:
        print(f"⚠️ Routing systems failed: {e}")

def test_debugging_systems():
    """Test ALL debugging and analysis tools"""
    print("🐛 Testing debugging systems...")
    
    try:
        from circuit_synth.debugging.analyzer import CircuitAnalyzer
        from circuit_synth.debugging.knowledge_base import DebuggingKnowledgeBase
        from circuit_synth.debugging.report_generator import DebugReportGenerator
        from circuit_synth.debugging.test_guidance import TestGuidanceEngine
        
        analyzer = CircuitAnalyzer()
        kb = DebuggingKnowledgeBase()
        reporter = DebugReportGenerator()
        guidance = TestGuidanceEngine()
        print("✅ All debugging systems loaded")
        
    except Exception as e:
        print(f"⚠️ Debugging systems failed: {e}")

if __name__ == "__main__":
    print("🚀 Running COMPREHENSIVE circuit-synth functionality test...")
    print("=" * 80)
    
    # Core functionality (already working)
    print("📋 Core circuit functionality already tested...")
    
    # New comprehensive tests
    test_manufacturing_integration()
    test_quality_assurance_comprehensive() 
    test_simulation_comprehensive()
    test_ai_integration_comprehensive()
    test_cli_tools_comprehensive()
    test_advanced_pcb_comprehensive()
    test_debugging_systems()
    
    print("=" * 80)
    print("🎉 COMPREHENSIVE test suite completed!")
```

### Updated Analysis Strategy

1. **Run current analysis** (10.8% baseline)
2. **Add comprehensive test script** with ALL functionality areas
3. **Re-run analysis** to get true coverage percentages
4. **Compare results** to identify genuinely unused vs. untested code
5. **Iterate until we achieve 40-60% realistic utilization**

### Target Coverage Goals

- **Core Circuit**: 90%+ (currently working)
- **KiCad Integration**: 70%+ (currently working)
- **Manufacturing**: 60%+ (needs testing)
- **Quality Assurance**: 40%+ (needs testing)
- **Simulation**: 30%+ (needs testing)
- **AI Integration**: 20%+ (needs testing)
- **CLI Tools**: 50%+ (needs testing)

Only after achieving comprehensive test coverage can we confidently identify truly dead code vs. simply untested code.