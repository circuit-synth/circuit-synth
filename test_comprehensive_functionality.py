#!/usr/bin/env python3
"""
Comprehensive functionality test for accurate dead code analysis.
This script exercises ALL major circuit-synth functionality areas.
"""

# Import at module level
from circuit_synth import *

def test_basic_circuits():
    """Test basic circuit creation and all core functionality"""
    
    print("📋 Testing basic circuit creation...")
    
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
    
    test_circuit = resistor_divider()
    print("✅ Basic circuit created")
    
    # Test all output formats
    try:
        test_circuit.generate_kicad_project("test_resistor_div", generate_pcb=True)
        print("✅ KiCad project generation")
    except Exception as e:
        print(f"⚠️ KiCad project generation failed: {e}")
    
    try:
        test_circuit.generate_json_netlist("test_circuit.json")
        print("✅ JSON netlist generation")
    except Exception as e:
        print(f"⚠️ JSON netlist generation failed: {e}")
    
    try:
        test_circuit.generate_kicad_netlist("test_circuit.net")
        print("✅ KiCad netlist generation")
    except Exception as e:
        print(f"⚠️ KiCad netlist generation failed: {e}")
    
    return test_circuit

def test_manufacturing_integration():
    """Test all manufacturing and component search functionality"""
    print("🔍 Testing manufacturing integration...")
    
    # JLCPCB search
    try:
        from circuit_synth.manufacturing.jlcpcb.fast_search import search_jlc_components_web
        jlc_results = search_jlc_components_web("0.1uF 0603", max_results=5)
        print("✅ JLCPCB component search")
    except Exception as e:
        print(f"⚠️ JLCPCB search failed: {e}")
    
    # Unified component search
    try:
        from circuit_synth.manufacturing.unified_search import find_parts
        unified_results = find_parts("10k resistor", sources="all")
        print("✅ Unified component search")
    except Exception as e:
        print(f"⚠️ Unified search failed: {e}")
    
    # STM32 peripheral search
    try:
        from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query
        stm32_response = handle_stm32_peripheral_query("find stm32 with 2 spi and usb")
        print("✅ STM32 peripheral search")
    except Exception as e:
        print(f"⚠️ STM32 search failed: {e}")
    
    # DigiKey integration (if configured)
    try:
        from circuit_synth.manufacturing.digikey.component_search import search_components
        dk_results = search_components("LM358")
        print("✅ DigiKey component search")
    except Exception as e:
        print(f"⚠️ DigiKey search failed: {e}")

def test_quality_assurance():
    """Test FMEA, DFM, and all quality assurance tools"""
    print("🎯 Testing quality assurance tools...")
    
    test_circuit = test_basic_circuits()
    
    # FMEA analysis
    try:
        from circuit_synth.quality_assurance.fmea_analyzer import FMEAAnalyzer
        fmea = FMEAAnalyzer()
        fmea_report = fmea.analyze_circuit(circuit)
        print("✅ FMEA analysis")
    except Exception as e:
        print(f"⚠️ FMEA test failed: {e}")
    
    # DFM analysis  
    try:
        from circuit_synth.design_for_manufacturing.dfm_analyzer import DFMAnalyzer
        dfm = DFMAnalyzer()
        dfm_report = dfm.analyze_circuit(circuit)
        print("✅ DFM analysis")
    except Exception as e:
        print(f"⚠️ DFM test failed: {e}")

def test_all_cli_tools():
    """Test all CLI utilities and command-line tools"""
    print("🛠️ Testing CLI tools...")
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
            status = "✅" if result.returncode == 0 else "❌"
            print(f"{status} CLI test: {' '.join(cmd[-2:])}")
        except Exception as e:
            print(f"⚠️ CLI test failed: {cmd[-2:]} - {e}")

def test_pcb_algorithms():
    """Test all PCB placement and routing algorithms"""
    print("🏗️ Testing PCB algorithms...")
    
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
            print(f"✅ Placement algorithm: {algorithm}")
        except Exception as e:
            print(f"⚠️ Placement algorithm {algorithm} failed: {e}")

def test_kicad_integration():
    """Test KiCad symbol/footprint integration"""
    print("🔧 Testing KiCad integration...")
    
    try:
        from circuit_synth.kicad.symbol_lib_parser import KiCadSymbolLibraryParser
        parser = KiCadSymbolLibraryParser()
        print("✅ KiCad symbol parser")
    except Exception as e:
        print(f"⚠️ Symbol parser failed: {e}")
    
    try:
        from circuit_synth.kicad.kicad_symbol_cache import KiCadSymbolCache
        cache = KiCadSymbolCache()
        print("✅ KiCad symbol cache")
    except Exception as e:
        print(f"⚠️ Symbol cache failed: {e}")

def test_debugging_tools():
    """Test circuit debugging and analysis tools"""
    print("🐛 Testing debugging tools...")
    
    try:
        from circuit_synth.debugging.analyzer import CircuitAnalyzer
        analyzer = CircuitAnalyzer()
        print("✅ Circuit analyzer")
    except Exception as e:
        print(f"⚠️ Circuit analyzer failed: {e}")
    
    try:
        from circuit_synth.debugging.knowledge_base import DebuggingKnowledgeBase
        kb = DebuggingKnowledgeBase()
        print("✅ Debugging knowledge base")
    except Exception as e:
        print(f"⚠️ Knowledge base failed: {e}")

def test_simulation_tools():
    """Test simulation and analysis functionality"""
    print("⚡ Testing simulation tools...")
    
    try:
        from circuit_synth.simulation.converter import SPICEConverter
        converter = SPICEConverter()
        print("✅ SPICE converter")
    except Exception as e:
        print(f"⚠️ SPICE converter failed: {e}")
    
    try:
        from circuit_synth.simulation.analysis import CircuitAnalysis
        analysis = CircuitAnalysis()
        print("✅ Circuit analysis")
    except Exception as e:
        print(f"⚠️ Circuit analysis failed: {e}")

def test_io_functionality():
    """Test input/output and conversion functionality"""
    print("💾 Testing I/O functionality...")
    
    try:
        from circuit_synth.io.json_loader import load_circuit_from_json
        print("✅ JSON loader")
    except Exception as e:
        print(f"⚠️ JSON loader failed: {e}")

if __name__ == "__main__":
    print("🧪 Running comprehensive circuit-synth functionality tests...")
    print("=" * 60)
    
    test_basic_circuits()
    test_manufacturing_integration()
    test_quality_assurance()
    test_all_cli_tools()
    test_pcb_algorithms()
    test_kicad_integration()
    test_debugging_tools()
    test_simulation_tools()
    test_io_functionality()
    
    print("=" * 60)
    print("✅ Comprehensive test suite completed")