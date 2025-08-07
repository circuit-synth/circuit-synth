#!/usr/bin/env python3
"""
Test script for comprehensive FMEA report generation
Tests the enhanced analyzer with the full knowledge base
"""

from src.circuit_synth.quality_assurance.enhanced_fmea_analyzer import EnhancedFMEAAnalyzer
from src.circuit_synth.quality_assurance.comprehensive_fmea_report_generator import ComprehensiveFMEAReportGenerator
from pathlib import Path
import os

def create_test_circuit():
    """Create a comprehensive test circuit with many components"""
    components = []
    
    # MCUs and ICs
    components.extend([
        {'ref': 'U1', 'symbol': 'MCU_ST:STM32F407VETx', 'footprint': 'LQFP-100', 'value': 'STM32F407VE'},
        {'ref': 'U2', 'symbol': 'Regulator_Linear:AMS1117-3.3', 'footprint': 'SOT-223', 'value': 'AMS1117-3.3'},
        {'ref': 'U3', 'symbol': 'Memory_Flash:W25Q128JVS', 'footprint': 'SOIC-8', 'value': 'W25Q128'},
        {'ref': 'U4', 'symbol': 'Interface_USB:FT232RL', 'footprint': 'SSOP-28', 'value': 'FT232RL'},
        {'ref': 'U5', 'symbol': 'Amplifier_Operational:LM358', 'footprint': 'SOIC-8', 'value': 'LM358'},
    ])
    
    # Connectors
    components.extend([
        {'ref': 'J1', 'symbol': 'Connector:USB_C_Receptacle', 'footprint': 'USB_C', 'value': 'USB-C'},
        {'ref': 'J2', 'symbol': 'Connector:Conn_01x10', 'footprint': 'Header_1x10', 'value': 'Debug'},
        {'ref': 'J3', 'symbol': 'Connector:Barrel_Jack', 'footprint': 'BarrelJack', 'value': 'Power'},
    ])
    
    # Capacitors (various types)
    for i in range(1, 21):
        if i <= 5:  # Electrolytics
            components.append({
                'ref': f'C{i}',
                'symbol': 'Device:CP',
                'footprint': 'CP_Radial_D8.0mm',
                'value': f'{i*10}uF'
            })
        else:  # Ceramic
            components.append({
                'ref': f'C{i}',
                'symbol': 'Device:C',
                'footprint': 'C_0603_1608Metric',
                'value': '0.1uF'
            })
    
    # Resistors
    for i in range(1, 16):
        components.append({
            'ref': f'R{i}',
            'symbol': 'Device:R',
            'footprint': 'R_0603_1608Metric',
            'value': f'{i}k'
        })
    
    # Inductors
    components.extend([
        {'ref': 'L1', 'symbol': 'Device:L', 'footprint': 'L_1210', 'value': '4.7uH'},
        {'ref': 'L2', 'symbol': 'Device:L_Ferrite', 'footprint': 'L_0805', 'value': 'BLM21'},
    ])
    
    # Diodes and transistors
    components.extend([
        {'ref': 'D1', 'symbol': 'Device:D_Schottky', 'footprint': 'D_SOD-123', 'value': '1N5819'},
        {'ref': 'D2', 'symbol': 'Device:LED', 'footprint': 'LED_0603', 'value': 'Red'},
        {'ref': 'Q1', 'symbol': 'Device:Q_NPN_BCE', 'footprint': 'SOT-23', 'value': '2N3904'},
        {'ref': 'Q2', 'symbol': 'Device:Q_PMOS_GSD', 'footprint': 'SOT-23', 'value': 'AO3401'},
    ])
    
    # Crystal
    components.append({
        'ref': 'Y1',
        'symbol': 'Device:Crystal',
        'footprint': 'Crystal_SMD_5032',
        'value': '8MHz'
    })
    
    return components

def main():
    print("=" * 60)
    print("COMPREHENSIVE FMEA REPORT GENERATION TEST")
    print("=" * 60)
    
    # Create test circuit
    components = create_test_circuit()
    print(f"\n📋 Created test circuit with {len(components)} components")
    
    # Initialize enhanced analyzer with knowledge base
    print("\n🔍 Initializing Enhanced FMEA Analyzer...")
    analyzer = EnhancedFMEAAnalyzer()
    
    # Define circuit context
    circuit_context = {
        'name': 'STM32F407 Development Board',
        'environment': 'industrial',  # More stringent than consumer
        'production_volume': 'high',   # Better detection
        'safety_critical': True,       # Higher severity
        'operating_temperature': '-20 to +85C',
        'expected_lifetime': '15 years',
        'compliance_requirements': ['IPC-A-610 Class 3', 'MIL-STD-883'],
    }
    
    # Analyze all components
    print(f"\n⚙️ Analyzing {len(components)} components with knowledge base...")
    all_failure_modes = []
    
    for component in components:
        # Get failure modes from enhanced analyzer
        failure_modes = analyzer.analyze_component(component, circuit_context)
        
        # Convert to dictionary format for report
        for fm in failure_modes:
            all_failure_modes.append({
                'component': fm.component,
                'failure_mode': fm.failure_mode,
                'cause': fm.cause,
                'effect': fm.effect,
                'severity': fm.severity,
                'occurrence': fm.occurrence,
                'detection': fm.detection,
                'rpn': fm.severity * fm.occurrence * fm.detection,
                'recommendation': fm.recommendation
            })
    
    print(f"  ✓ Identified {len(all_failure_modes)} failure modes")
    
    # Calculate statistics
    critical = sum(1 for fm in all_failure_modes if fm['rpn'] >= 300)
    high_risk = sum(1 for fm in all_failure_modes if 125 <= fm['rpn'] < 300)
    medium_risk = sum(1 for fm in all_failure_modes if 50 <= fm['rpn'] < 125)
    low_risk = sum(1 for fm in all_failure_modes if fm['rpn'] < 50)
    
    print(f"\n📊 Risk Distribution:")
    print(f"  - Critical (RPN ≥ 300): {critical}")
    print(f"  - High Risk (125-299): {high_risk}")
    print(f"  - Medium Risk (50-124): {medium_risk}")
    print(f"  - Low Risk (< 50): {low_risk}")
    
    # Prepare comprehensive analysis results
    analysis_results = {
        'project_name': 'STM32F407 Industrial Controller',
        'circuit_data': {
            'name': 'STM32F407 Development Board',
            'description': 'Industrial-grade development board with STM32F407 MCU for high-reliability applications',
            'component_count': len(components),
            'subsystem_count': 7,
            'design_version': '3.2',
            'compliance_standards': ['IPC-2221', 'IPC-A-610 Class 3', 'MIL-STD-883', 'RoHS', 'CE', 'FCC'],
            'operating_environment': 'Industrial/Harsh',
            'expected_lifetime': '15 years',
            'production_volume': '50,000 units/year',
            'subsystems': [
                {
                    'name': 'Power Management',
                    'description': 'Multi-rail power supply with protection and monitoring',
                    'components': ['U2', 'L1', 'C1-C5', 'D1'],
                    'criticality': 'Critical'
                },
                {
                    'name': 'STM32F407 Core',
                    'description': 'ARM Cortex-M4 MCU with FPU, 168MHz, 512KB Flash',
                    'components': ['U1', 'Y1', 'C6-C10', 'R1-R5'],
                    'criticality': 'Critical'
                },
                {
                    'name': 'USB Interface',
                    'description': 'USB-C with FTDI bridge for programming and communication',
                    'components': ['J1', 'U4', 'R6-R8'],
                    'criticality': 'High'
                },
                {
                    'name': 'External Memory',
                    'description': '128Mbit QSPI Flash for data logging',
                    'components': ['U3', 'C11-C12'],
                    'criticality': 'High'
                },
                {
                    'name': 'Analog Frontend',
                    'description': 'Operational amplifiers for sensor conditioning',
                    'components': ['U5', 'R9-R12', 'C13-C15'],
                    'criticality': 'Medium'
                },
                {
                    'name': 'Debug Interface',
                    'description': 'SWD/JTAG programming and debug header',
                    'components': ['J2', 'R13-R15'],
                    'criticality': 'Low'
                },
                {
                    'name': 'Status Indicators',
                    'description': 'Power and status LEDs',
                    'components': ['D2', 'Q1-Q2'],
                    'criticality': 'Low'
                }
            ]
        },
        'failure_modes': all_failure_modes,
        'circuit_context': circuit_context,
        'components': components
    }
    
    # Generate comprehensive report
    print("\n📝 Generating comprehensive FMEA report...")
    generator = ComprehensiveFMEAReportGenerator(
        project_name='STM32F407 Industrial Controller',
        author='Circuit-Synth Enhanced FMEA System v2.0'
    )
    
    output_path = generator.generate_comprehensive_report(
        analysis_results=analysis_results,
        output_path='STM32F407_Comprehensive_FMEA_Report.pdf'
    )
    
    # Check results
    if os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024
        size_mb = size_kb / 1024
        pages_estimate = size_kb / 3  # Rough estimate
        
        print(f"\n✅ COMPREHENSIVE REPORT GENERATED SUCCESSFULLY")
        print(f"📄 File: {output_path}")
        print(f"📊 Size: {size_kb:.1f} KB ({size_mb:.2f} MB)")
        print(f"📖 Estimated pages: ~{pages_estimate:.0f}")
        print(f"🔍 Total failure modes analyzed: {len(all_failure_modes)}")
        print(f"📚 Knowledge base categories used: {len(analyzer.knowledge_base)}")
        
        if pages_estimate >= 50:
            print("\n🎉 SUCCESS: Generated 50+ page comprehensive report!")
        elif pages_estimate >= 30:
            print("\n✅ Generated detailed report (30+ pages)")
        else:
            print("\n⚠️ Report is smaller than expected, may need more content")
            
        print(f"\n💡 To view the report, open: {output_path}")
    else:
        print("\n❌ Report generation failed")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()