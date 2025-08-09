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

def test_core_functionality():
    """Test core circuit functionality - this already works"""
    print("📋 Testing core circuit functionality...")
    
    # Create main circuit like in main.py
    @circuit(name="ESP32_C6_Dev_Board_Comprehensive")
    def main_circuit():
        vbus = Net('VBUS')
        vcc_3v3 = Net('VCC_3V3')
        gnd = Net('GND')
        usb_dp = Net('USB_DP')
        usb_dm = Net('USB_DM')

        usb_port_circuit = usb_port(vbus, gnd, usb_dp, usb_dm)
        power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
        esp32_circuit = esp32c6(vcc_3v3, gnd, usb_dp, usb_dm)
    
    main_board = main_circuit()
    
    # Test all generation methods
    main_board.generate_kicad_netlist("comprehensive_test.net")
    main_board.generate_json_netlist("comprehensive_test.json")
    main_board.generate_kicad_project("comprehensive_test_core", generate_pcb=True)
    
    print("✅ Core functionality working")

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
        
        from circuit_synth.manufacturing.jlcpcb.jlc_parts_lookup import JLCPartsLookup
        lookup = JLCPartsLookup()
        lookup_results = lookup.search_parts("capacitor")
        print("✅ JLC parts lookup completed")
        
    except Exception as e:
        print(f"⚠️ JLCPCB integration failed: {e}")
    
    # DigiKey integration
    try:
        from circuit_synth.manufacturing.digikey.component_search import search_components
        from circuit_synth.manufacturing.digikey.api_client import DigikeyApiClient
        from circuit_synth.manufacturing.digikey.cache import DigikeyCache
        
        client = DigikeyApiClient()
        cache = DigikeyCache()
        dk_results = search_components("LM358")
        print(f"✅ DigiKey search completed")
        
    except Exception as e:
        print(f"⚠️ DigiKey integration failed: {e}")
    
    # Unified search
    try:
        from circuit_synth.manufacturing.unified_search import find_parts
        unified_results = find_parts("capacitor 0.1uF", sources="all")
        print(f"✅ Unified search completed")
        
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
    
    qa_circuit = qa_test_circuit()
    
    # FMEA Analysis
    try:
        from circuit_synth.quality_assurance.fmea_analyzer import FMEAAnalyzer
        from circuit_synth.quality_assurance.enhanced_fmea_analyzer import EnhancedFMEAAnalyzer
        from circuit_synth.quality_assurance.comprehensive_fmea_report_generator import ComprehensiveFMEAReportGenerator
        from circuit_synth.quality_assurance.circuit_parser import CircuitParser
        
        fmea = FMEAAnalyzer()
        fmea_result = fmea.analyze_circuit(qa_circuit)
        print("✅ Basic FMEA analysis completed")
        
        enhanced_fmea = EnhancedFMEAAnalyzer()
        enhanced_result = enhanced_fmea.analyze_circuit(qa_circuit)
        print("✅ Enhanced FMEA analysis completed")
        
        report_gen = ComprehensiveFMEAReportGenerator()
        comprehensive_report = report_gen.generate_report(qa_circuit)
        print("✅ Comprehensive FMEA report generated")
        
        parser = CircuitParser()
        parsed_circuit = parser.parse_circuit(qa_circuit)
        print("✅ Circuit parser completed")
        
    except Exception as e:
        print(f"⚠️ FMEA analysis failed: {e}")
    
    # DFM Analysis
    try:
        from circuit_synth.design_for_manufacturing.dfm_analyzer import DFMAnalyzer
        from circuit_synth.design_for_manufacturing.comprehensive_dfm_report_generator import ComprehensiveDFMReportGenerator
        from circuit_synth.design_for_manufacturing.kicad_dfm_analyzer import KiCadDFMAnalyzer
        from circuit_synth.design_for_manufacturing.json_dfm_analyzer import JSONDFMAnalyzer
        
        dfm = DFMAnalyzer()
        dfm_result = dfm.analyze_circuit(test_circuit)
        print("✅ Basic DFM analysis completed")
        
        dfm_report = ComprehensiveDFMReportGenerator()
        comprehensive_dfm = dfm_report.generate_report(test_circuit)
        print("✅ Comprehensive DFM report generated")
        
        kicad_dfm = KiCadDFMAnalyzer()
        kicad_dfm_result = kicad_dfm.analyze_circuit(test_circuit)
        print("✅ KiCad DFM analysis completed")
        
        json_dfm = JSONDFMAnalyzer()
        json_dfm_result = json_dfm.analyze_circuit(test_circuit)
        print("✅ JSON DFM analysis completed")
        
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
        from circuit_synth.simulation.models import ComponentModels
        from circuit_synth.simulation.manufacturer_models import ManufacturerModels
        
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
        
        # Models
        models = ComponentModels()
        mfg_models = ManufacturerModels()
        print("✅ Simulation models loaded")
        
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
        from circuit_synth.ai_integration.memory_bank.circuit_diff import CircuitDiff
        from circuit_synth.ai_integration.memory_bank.templates import TemplateManager
        
        memory_core = MemoryBankCore()
        context_mgr = ContextManager()
        git_integ = GitIntegration()
        diff_tool = CircuitDiff()
        templates = TemplateManager()
        print("✅ Memory bank systems loaded")
        
    except Exception as e:
        print(f"⚠️ Memory bank failed: {e}")
    
    try:
        # Validation systems
        from circuit_synth.ai_integration.validation.simple_validator import SimpleValidator
        from circuit_synth.ai_integration.validation.real_time_check import RealTimeChecker
        
        validator = SimpleValidator()
        rt_checker = RealTimeChecker()
        print("✅ AI validation systems loaded")
        
    except Exception as e:
        print(f"⚠️ AI validation failed: {e}")

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
        ["uv", "run", "python", "-m", "circuit_synth.tools.utilities.python_code_generator", "--help"],
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
        from circuit_synth.pcb.routing.install_freerouting import install_freerouting
        
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
        from circuit_synth.debugging.symptoms import SymptomAnalyzer
        
        analyzer = CircuitAnalyzer()
        kb = DebuggingKnowledgeBase()
        reporter = DebugReportGenerator()
        guidance = TestGuidanceEngine()
        symptoms = SymptomAnalyzer()
        print("✅ All debugging systems loaded")
        
    except Exception as e:
        print(f"⚠️ Debugging systems failed: {e}")

def test_io_systems():
    """Test input/output and conversion functionality"""
    print("💾 Testing I/O systems...")
    
    try:
        from circuit_synth.io.json_loader import load_circuit_from_json, JSONCircuitLoader
        
        loader = JSONCircuitLoader()
        print("✅ JSON I/O systems loaded")
        
    except Exception as e:
        print(f"⚠️ I/O systems failed: {e}")

if __name__ == "__main__":
    print("🚀 Running COMPREHENSIVE circuit-synth functionality test...")
    print("=" * 80)
    
    # Test all functionality areas
    test_core_functionality()
    test_manufacturing_integration()
    test_quality_assurance_comprehensive() 
    test_simulation_comprehensive()
    test_ai_integration_comprehensive()
    test_cli_tools_comprehensive()
    test_advanced_pcb_comprehensive()
    test_debugging_systems()
    test_io_systems()
    
    print("=" * 80)
    print("🎉 COMPREHENSIVE test suite completed!")