#!/usr/bin/env python3
"""
Demonstration of All SPICE Simulation Output Formats

This example shows all the different ways to export and visualize
simulation results:
- CSV data export
- JSON data export  
- PDF report generation
- Interactive HTML plots
- SPICE netlist export
- Professional plots (Bode, time-domain)
"""

from pathlib import Path
from circuit_synth import Circuit, Component, Net
from circuit_synth.simulation import (
    CircuitSimulator,
    SimulationVisualizer,
    TransientAnalysis,
    ACAnalysis,
)


def create_rc_filter():
    """Create a simple RC low-pass filter for demonstration."""
    
    circuit = Circuit("RC Low-Pass Filter")
    
    # Create nets
    vin = Net("VIN")
    vout = Net("VOUT")
    gnd = Net("GND")
    
    # Input voltage source (1V AC for frequency response)
    v_source = Component(
        symbol="Device:V",
        ref="V1",
        value="AC 1",  # 1V AC source
    )
    v_source[1] += vin
    v_source[2] += gnd
    
    # RC filter components
    # Cutoff frequency = 1/(2*pi*R*C) = 1/(2*pi*1k*1uF) ≈ 159 Hz
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
    )
    r1[1] += vin
    r1[2] += vout
    
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="1uF",
    )
    c1[1] += vout
    c1[2] += gnd
    
    # Output load
    r_load = Component(
        symbol="Device:R",
        ref="R2",
        value="10k",
    )
    r_load[1] += vout
    r_load[2] += gnd
    
    circuit.add_components([v_source, r1, c1, r_load])
    
    return circuit


def demonstrate_all_outputs():
    """Demonstrate all available output formats."""
    
    print("=" * 70)
    print("SPICE SIMULATION OUTPUT FORMATS DEMONSTRATION")
    print("=" * 70)
    
    # Create output directory
    output_dir = Path("simulation_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Create the circuit
    circuit = create_rc_filter()
    print(f"\n✓ Created RC filter circuit")
    print(f"  Expected cutoff frequency: ~159 Hz")
    
    # NOTE: The actual simulation would require PySpice to be installed
    # This demonstration shows the API and what outputs would be generated
    
    print("\n" + "=" * 70)
    print("AVAILABLE OUTPUT FORMATS")
    print("=" * 70)
    
    # Simulate what would happen with real PySpice
    print("\nIf PySpice were installed, the following would be generated:")
    
    try:
        # This would work with PySpice installed
        sim = CircuitSimulator(circuit)
        
        # Run AC analysis
        ac_result = sim.ac_analysis(
            start_freq=1,      # 1 Hz
            stop_freq=100000,  # 100 kHz
            points=100
        )
        
        # Create visualizer
        viz = SimulationVisualizer(ac_result)
        
        print("\n1. CSV DATA EXPORT")
        print("-" * 40)
        csv_path = output_dir / "rc_filter_results.csv"
        ac_result.export_csv(str(csv_path))
        print(f"   ✓ Exported to: {csv_path}")
        print("   Format: Spreadsheet-compatible data")
        print("   Contents: Node voltages vs frequency")
        
        print("\n2. JSON DATA EXPORT")
        print("-" * 40)
        json_path = output_dir / "rc_filter_results.json"
        ac_result.export_json(str(json_path))
        print(f"   ✓ Exported to: {json_path}")
        print("   Format: Structured JSON with metadata")
        print("   Use case: Programmatic analysis, web apps")
        
        print("\n3. PDF REPORT GENERATION")
        print("-" * 40)
        pdf_path = output_dir / "rc_filter_report.pdf"
        ac_result.generate_report(
            str(pdf_path),
            circuit_name="RC Low-Pass Filter",
            include_plots=True,
            include_data=True
        )
        print(f"   ✓ Generated report: {pdf_path}")
        print("   Contents:")
        print("     - Title page with metadata")
        print("     - Bode plots (magnitude & phase)")
        print("     - Data summary tables")
        print("     - Test bench configuration")
        
        print("\n4. INTERACTIVE HTML PLOT")
        print("-" * 40)
        html_path = output_dir / "rc_filter_interactive.html"
        ac_result.plot_interactive(
            nodes=["VIN", "VOUT"],
            output_path=str(html_path)
        )
        print(f"   ✓ Created interactive plot: {html_path}")
        print("   Features:")
        print("     - Zoom and pan")
        print("     - Hover for values")
        print("     - Toggle traces")
        print("     - Export as PNG")
        
        print("\n5. SPICE NETLIST EXPORT")
        print("-" * 40)
        netlist_path = output_dir / "rc_filter.cir"
        viz.export_spice_netlist(str(netlist_path))
        print(f"   ✓ Exported netlist: {netlist_path}")
        print("   Format: Standard SPICE netlist")
        print("   Use case: Import into other SPICE tools")
        
        print("\n6. MATPLOTLIB PLOTS")
        print("-" * 40)
        # Bode plot
        bode_path = output_dir / "rc_filter_bode.png"
        viz.plot_bode(
            "VIN", "VOUT",
            save_path=str(bode_path),
            show=False
        )
        print(f"   ✓ Saved Bode plot: {bode_path}")
        
    except ImportError:
        print("\n⚠️  PySpice not installed - showing API demonstration only")
        print("\nTo enable actual simulation, install PySpice:")
        print("  pip install PySpice")
        print("\nWithout PySpice, the following outputs WOULD be generated:")
        
        # Show what would be created
        print("\n1. CSV DATA EXPORT")
        print("-" * 40)
        print("   File: simulation_outputs/rc_filter_results.csv")
        print("   Example content:")
        print("   Point, V(VIN), V(VOUT)")
        print("   0, 1.000, 0.995")
        print("   1, 1.000, 0.987")
        print("   ...")
        
        print("\n2. JSON DATA EXPORT")
        print("-" * 40)
        print("   File: simulation_outputs/rc_filter_results.json")
        print("   Example structure:")
        print("""   {
     "timestamp": "2024-01-01T12:00:00",
     "analysis_type": "ac",
     "nodes": {
       "VIN": [1.0, 1.0, ...],
       "VOUT": [0.995, 0.987, ...]
     }
   }""")
        
        print("\n3. PDF REPORT")
        print("-" * 40)
        print("   File: simulation_outputs/rc_filter_report.pdf")
        print("   Multi-page PDF with:")
        print("   - Professional formatting")
        print("   - Embedded plots")
        print("   - Data tables")
        print("   - Circuit parameters")
        
        print("\n4. INTERACTIVE HTML")
        print("-" * 40)
        print("   File: simulation_outputs/rc_filter_interactive.html")
        print("   Plotly-based interactive visualization")
        print("   Opens in web browser")
        
        print("\n5. SPICE NETLIST")
        print("-" * 40)
        print("   File: simulation_outputs/rc_filter.cir")
        print("   Example content:")
        print("   * RC Low-Pass Filter")
        print("   V1 VIN GND AC 1")
        print("   R1 VIN VOUT 1k")
        print("   C1 VOUT GND 1uF")
        print("   R2 VOUT GND 10k")
        print("   .AC DEC 100 1 100k")
        print("   .END")
        
        print("\n6. MATPLOTLIB PLOTS")
        print("-" * 40)
        print("   Files: simulation_outputs/*.png")
        print("   High-resolution plots for reports/papers")
        print("   - Bode plots (magnitude & phase)")
        print("   - Time-domain responses")
        print("   - DC sweep curves")
    
    print("\n" + "=" * 70)
    print("OUTPUT FORMAT COMPARISON")
    print("=" * 70)
    
    comparison = """
    Format      | Use Case                  | Advantages
    ------------|---------------------------|---------------------------
    CSV         | Excel, data analysis      | Universal, spreadsheet-ready
    JSON        | Programming, web apps     | Structured, metadata included
    PDF Report  | Documentation, sharing    | Professional, self-contained
    HTML Plot   | Interactive exploration   | Zoom, pan, hover details
    PNG/SVG     | Papers, presentations     | High-quality static images
    SPICE       | Tool interoperability     | Standard format, portable
    """
    print(comparison)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nThe enhanced SPICE simulation system provides:")
    print("✓ Multiple export formats for different use cases")
    print("✓ Professional visualization capabilities")
    print("✓ Automated report generation")
    print("✓ Interactive analysis tools")
    print("✓ Industry-standard output formats")


if __name__ == "__main__":
    demonstrate_all_outputs()
    
    print("\n✨ Output formats demonstration complete!")
    print("\nWith PySpice installed, all these outputs would be generated")
    print("in the 'simulation_outputs' directory.")