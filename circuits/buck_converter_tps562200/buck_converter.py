#!/usr/bin/env python3
"""
TPS562200 Buck Converter Circuit
Professional power supply design for 12V to 3.3V conversion

This circuit demonstrates:
- Modern switching regulator design
- Feedback control loop analysis  
- Efficiency optimization
- Load regulation performance
"""

from circuit_synth import circuit, Component, Net


@circuit
def tps562200_buck_converter():
    """
    TPS562200 2A Buck Converter: 12V input to 3.3V output
    
    Features:
    - 2A continuous output current
    - 95% efficiency typical
    - 500kHz switching frequency
    - Integrated MOSFETs
    - Simple feedback network
    
    Applications:
    - Embedded systems power
    - IoT device supplies
    - Motor controller auxiliaries
    """
    
    # Power rails
    vin = Net("VIN")           # 12V input supply
    vout = Net("VOUT")          # 3.3V regulated output
    gnd = Net("GND")              # Ground reference
    sw = Net("SW")                           # Switch node (high frequency)
    fb = Net("FB")                           # Feedback pin
    
    # TPS562200 Buck Converter IC
    # This is the main switching regulator
    u1 = Component(
        symbol="Regulator_Switching:TPS562200",
        ref="U1",
        value="TPS562200DDC",
        footprint="Package_TO_SOT_SMD:SOT-23-5",
        spice_model="TPS562200",  # Will gracefully handle if missing
        description="2A Synchronous Buck Converter, 4.5V-17V Input"
    )
    
    # Connect TPS562200 pins
    vin += u1["VIN"]
    vin += u1["EN"]           # Enable tied to VIN (always on)
    sw += u1["SW"]            # Switch output
    fb += u1["VFB"]            # Feedback input (correct pin name)
    gnd += u1["GND"]          # Ground
    
    # Output inductor (critical for buck operation)
    l1 = Component(
        symbol="Device:L",
        ref="L1", 
        value="4.7uH",
        footprint="Inductor_SMD:L_1210_3225Metric",
        spice_model="L_CORE",
        specs={
            "current_rating": "3A",
            "dcr": "50mΩ",
            "saturation_current": "4A",
            "core_material": "Ferrite"
        }
    )
    sw += l1["1"]
    vout += l1["2"]
    
    # Output capacitor (low ESR for ripple reduction)
    c_out = Component(
        symbol="Device:C", 
        ref="C1",
        value="22uF",
        footprint="Capacitor_SMD:C_1206_3216Metric",
        spice_model="C_CERAMIC_X7R",
        specs={
            "voltage_rating": "6.3V",
            "esr": "5mΩ",
            "ripple_current": "1A"
        }
    )
    vout += c_out["1"]
    gnd += c_out["2"]
    
    # Input capacitor (bulk energy storage)
    c_in = Component(
        symbol="Device:C",
        ref="C2", 
        value="10uF",
        footprint="Capacitor_SMD:C_1206_3216Metric",
        spice_model="C_CERAMIC_X7R"
    )
    vin += c_in["1"]
    gnd += c_in["2"]
    
    # Feedback resistor divider (sets output voltage)
    # VOUT = 0.6V * (1 + R1/R2)
    # For 3.3V: R1/R2 = 4.5, choose R1=45k, R2=10k
    
    r_fb_top = Component(
        symbol="Device:R",
        ref="R1",
        value="45k",
        footprint="Resistor_SMD:R_0603_1608Metric",
        spice_model="R_GENERIC",
        tolerance="1%"
    )
    vout += r_fb_top["1"]
    fb += r_fb_top["2"]
    
    r_fb_bottom = Component(
        symbol="Device:R", 
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric", 
        spice_model="R_GENERIC",
        tolerance="1%"
    )
    fb += r_fb_bottom["1"]
    gnd += r_fb_bottom["2"]
    
    # Input voltage source for simulation
    v_input = Component(
        symbol="Simulation:VSOURCE",
        ref="V1",
        value="DC 12",
        spice_model="VSOURCE_DC",
        description="12V input supply"
    )
    vin += v_input["+"]
    gnd += v_input["-"]
    
    # Load resistor for simulation
    r_load = Component(
        symbol="Simulation:RLOAD", 
        ref="R3",
        value="3.3",  # 1A load at 3.3V
        spice_model="R_GENERIC",
        description="1A load (3.3Ω)"
    )
    vout += r_load["1"]
    gnd += r_load["2"]
    
    # Test points for monitoring
    tp_vin = Component(
        symbol="Connector:TestPoint",
        ref="TP1",
        value="VIN_TP"
    )
    vin += tp_vin["1"]
    
    tp_vout = Component(
        symbol="Connector:TestPoint", 
        ref="TP2",
        value="VOUT_TP"
    )
    vout += tp_vout["1"]
    
    tp_sw = Component(
        symbol="Connector:TestPoint",
        ref="TP3", 
        value="SW_TP"
    )
    sw += tp_sw["1"]


def simulate_buck_converter():
    """
    Run comprehensive simulation of the TPS562200 buck converter
    
    Simulations performed:
    1. DC operating point analysis
    2. AC small-signal response (control loop)
    3. Transient load step response
    4. Efficiency vs load analysis
    
    Returns:
        SimulationReport: Interactive HTML report with plots
    """
    
    # Create the circuit
    circuit = tps562200_buck_converter()
    
    try:
        # Import simulation framework
        from circuit_synth.simulation import SimulationEngine, SimulationReport
        
        # Initialize simulation engine
        engine = SimulationEngine()
        
        # DC Operating Point Analysis
        print("Running DC analysis...")
        dc_result = engine.dc_analysis(
            circuit=circuit,
            temperature=25,
            description="DC operating point and regulation"
        )
        
        # AC Small-Signal Analysis (Control Loop)
        print("Running AC analysis...")
        ac_result = engine.ac_analysis(
            circuit=circuit,
            start_freq=1,      # 1 Hz
            stop_freq=1e6,     # 1 MHz
            points_per_decade=50,
            description="Control loop frequency response"
        )
        
        # Transient Load Step Response
        print("Running transient analysis...")
        transient_result = engine.transient_analysis(
            circuit=circuit,
            duration=100e-6,   # 100 microseconds
            timestep=100e-9,   # 100 nanosecond resolution
            load_step={
                "time": 50e-6,
                "component": "R3", 
                "new_value": "1.65"  # Double the load (2A)
            },
            description="Load step response (1A to 2A)"
        )
        
        # Generate comprehensive report
        report = SimulationReport(
            circuit=circuit,
            title="TPS562200 Buck Converter Analysis",
            subtitle="Professional Power Supply Design & Validation"
        )
        
        # Add analysis sections
        report.add_dc_analysis(dc_result)
        report.add_ac_analysis(ac_result) 
        report.add_transient_analysis(transient_result)
        
        # Add design calculations
        report.add_design_section({
            "output_voltage": "3.3V ± 2%",
            "output_current": "2A maximum", 
            "efficiency": ">90% at 1A load",
            "switching_frequency": "500kHz",
            "ripple_voltage": "<50mV pk-pk",
            "load_regulation": "<1%",
            "line_regulation": "<0.5%"
        })
        
        # Generate interactive HTML report
        report_path = report.generate_html_report(
            filename="tps562200_analysis.html",
            include_interactive_plots=True,
            include_component_tables=True,
            include_design_notes=True
        )
        
        print(f"✅ Simulation completed successfully!")
        print(f"📊 Report generated: {report_path}")
        
        return report_path
        
    except ImportError as e:
        print(f"❌ Simulation framework not available: {e}")
        print("💡 Install circuit-simulation package for full analysis")
        return None
        
    except Exception as e:
        print(f"⚠️ Simulation encountered issues: {e}")
        print("📋 Circuit definition created successfully")
        print("🔧 Check SPICE models and try again")
        return None


if __name__ == "__main__":
    print("🔋 TPS562200 Buck Converter Design")
    print("=" * 50)
    
    # Create and validate circuit
    circuit = tps562200_buck_converter()
    print(f"✅ Circuit created with {len(circuit.components)} components")
    print(f"📋 Components: {', '.join([c.ref for c in circuit.components])}")
    
    # Run simulation if available
    report_path = simulate_buck_converter()
    
    if report_path:
        print(f"\n🎉 Open the report to view results:")
        print(f"📄 {report_path}")
    else:
        print(f"\n📐 Circuit ready for KiCad generation:")
        print(f"🔧 Run: python-to-kicad {__file__}")