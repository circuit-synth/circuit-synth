#!/usr/bin/env python3
"""
Test script for debugging agent - simulates a real PCB debugging session
"""

from datetime import datetime, timedelta
import json
from pathlib import Path

from circuit_synth.debugging import (
    CircuitDebugger,
    SymptomAnalyzer,
    TestMeasurement,
    MeasurementType,
    DebugKnowledgeBase,
    TestGuidance,
    OscilloscopeTrace
)

def main():
    print("🔧 Circuit Debugging Agent Test - ESP32 Board Power Issue")
    print("=" * 60)
    
    # Initialize debugger
    debugger = CircuitDebugger()
    analyzer = SymptomAnalyzer()
    
    # Start debugging session
    session = debugger.start_session("ESP32_Dev_Board", "v2.1")
    print(f"\n✅ Started debugging session: {session.session_id}")
    print(f"   Board: {session.board_name} {session.board_version}")
    
    # Add symptoms
    print("\n📝 Adding symptoms...")
    symptoms = [
        "Board not powering on",
        "No LED indicators active", 
        "USB enumeration failing",
        "Voltage regulator getting hot",
        "No 3.3V on MCU power pins"
    ]
    
    for symptom in symptoms:
        session.add_symptom(symptom)
        print(f"   • {symptom}")
    
    # Add measurements
    print("\n📊 Adding test measurements...")
    measurements = [
        ("VBUS", 5.1, "V", "USB power input"),
        ("VCC_3V3", 0.3, "V", "Main 3.3V rail"),
        ("Regulator_Input", 5.0, "V", "Before regulator"),
        ("Regulator_Output", 0.3, "V", "After regulator"),
        ("Regulator_Enable", 3.3, "V", "Enable pin"),
        ("Current_Draw", 850, "mA", "Total current"),
        ("Regulator_Temp", 95, "°C", "Surface temperature"),
        ("3V3_to_GND_Resistance", 12, "Ω", "Power rail resistance")
    ]
    
    for name, value, unit, notes in measurements:
        session.add_measurement(name, value, unit, notes)
        print(f"   • {name}: {value}{unit} - {notes}")
    
    # Add specific test measurements with expected values
    print("\n🔬 Adding detailed measurements with pass/fail...")
    detailed_measurements = [
        TestMeasurement(
            measurement_type=MeasurementType.VOLTAGE_DC,
            value=0.3,
            unit="V",
            test_point="VCC_3V3",
            expected_value=3.3,
            tolerance=0.05,
            notes="Main power rail severely undervoltage"
        ),
        TestMeasurement(
            measurement_type=MeasurementType.TEMPERATURE,
            value=95,
            unit="°C",
            test_point="U1_Regulator",
            expected_value=50,
            tolerance=0.2,
            notes="Regulator running very hot"
        ),
        TestMeasurement(
            measurement_type=MeasurementType.RESISTANCE,
            value=12,
            unit="Ω",
            test_point="3V3_to_GND",
            expected_value=1000,
            tolerance=0.5,
            notes="Low resistance indicates possible short"
        )
    ]
    
    for measurement in detailed_measurements:
        passed = measurement.evaluate()
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   • {measurement.test_point}: {measurement.value}{measurement.unit} {status}")
        print(f"     Expected: {measurement.expected_value}{measurement.unit} ±{measurement.tolerance*100}%")
    
    # Analyze symptoms
    print("\n🔍 Analyzing symptoms and measurements...")
    issues = debugger.analyze_symptoms(session)
    
    print(f"\n⚠️  Found {len(issues)} potential issues:")
    for i, issue in enumerate(issues, 1):
        severity_icons = {
            "critical": "🔴",
            "high": "🟠", 
            "medium": "🟡",
            "low": "🟢"
        }
        icon = severity_icons.get(issue.severity.value, "⚪")
        
        print(f"\n{i}. {icon} [{issue.severity.value.upper()}] {issue.title}")
        print(f"   Category: {issue.category.value}")
        print(f"   Description: {issue.description}")
        print(f"   Confidence: {issue.confidence:.0%}")
        
        if issue.probable_causes:
            print(f"   Probable Causes:")
            for cause in issue.probable_causes[:3]:
                print(f"      • {cause}")
        
        if issue.test_suggestions:
            print(f"   Suggested Tests:")
            for test in issue.test_suggestions[:3]:
                print(f"      → {test}")
    
    # Get troubleshooting guidance
    print("\n📋 Generating troubleshooting tree...")
    power_tree = TestGuidance.create_power_troubleshooting_tree()
    
    print(f"   Troubleshooting: {power_tree.title}")
    print(f"   Steps: {len(power_tree.steps)}")
    print(f"   Equipment needed: {', '.join(e.value for e in power_tree.equipment_list)}")
    
    # Simulate finding and fixing the issue
    print("\n🔧 Debugging Progress:")
    print("   1. Visual inspection revealed burnt area near C5")
    print("   2. Removed C5 (10uF ceramic capacitor)")
    print("   3. Found C5 was shorted internally")
    print("   4. Replaced with new capacitor")
    print("   5. Board now powers up correctly")
    
    # Add resolution
    session.add_observation("Found shorted output capacitor C5")
    session.add_observation("Capacitor showed burn marks on PCB")
    session.add_observation("After replacing C5, 3.3V rail measures correctly")
    
    # Close session
    debugger.close_session(
        session,
        resolution="Replaced shorted output capacitor C5",
        root_cause="Output capacitor C5 failed short circuit, overloading regulator"
    )
    
    duration = (session.ended_at - session.started_at).total_seconds() / 60
    print(f"\n✅ Session closed successfully")
    print(f"   Duration: {duration:.1f} minutes")
    print(f"   Root cause: {session.root_cause}")
    
    # Export session data
    session_file = Path("debug_session_report.json")
    with open(session_file, 'w') as f:
        json.dump(session.to_dict(), f, indent=2)
    print(f"\n📄 Session data exported to {session_file}")
    
    # Generate detailed markdown report
    print("\n📝 Generating detailed debugging report...")
    generate_markdown_report(session, issues, power_tree)
    
    print("\n✨ Debugging test complete!")

def generate_markdown_report(session, issues, tree):
    """Generate a detailed markdown report"""
    
    report = f"""# PCB Debugging Report

## Session Information
- **Session ID**: {session.session_id}
- **Board**: {session.board_name} {session.board_version}
- **Date**: {session.started_at.strftime('%Y-%m-%d %H:%M')}
- **Duration**: {((session.ended_at - session.started_at).total_seconds() / 60):.1f} minutes
- **Status**: ✅ Resolved

## Executive Summary

The {session.board_name} was experiencing complete power failure with the 3.3V rail reading only 0.3V instead of the expected 3.3V. The voltage regulator was overheating (95°C) and drawing excessive current (850mA). Investigation revealed a shorted output capacitor (C5) that was overloading the regulator and preventing proper voltage regulation.

### Key Findings
- **Root Cause**: Shorted ceramic capacitor C5 (10uF) on regulator output
- **Impact**: Complete board failure, no functionality
- **Resolution**: Replaced failed capacitor
- **Time to Resolution**: {((session.ended_at - session.started_at).total_seconds() / 60):.0f} minutes

## Symptoms Reported

"""
    
    for symptom in session.symptoms:
        report += f"- {symptom}\n"
    
    report += "\n## Measurements Collected\n\n"
    report += "| Test Point | Value | Unit | Notes | Status |\n"
    report += "|------------|-------|------|-------|--------|\n"
    
    for name, data in session.measurements.items():
        value = data['value']
        unit = data['unit']
        notes = data['notes']
        # Determine status based on measurement
        if name == "VCC_3V3" and value < 3.0:
            status = "❌ FAIL"
        elif name == "Regulator_Temp" and value > 70:
            status = "⚠️ WARNING"
        else:
            status = "✅ OK"
        report += f"| {name} | {value} | {unit} | {notes} | {status} |\n"
    
    report += "\n## Issue Analysis\n\n"
    
    for i, issue in enumerate(issues, 1):
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡", 
            "low": "🟢"
        }.get(issue.severity.value, "⚪")
        
        report += f"### Issue {i}: {issue.title} {severity_emoji}\n\n"
        report += f"**Severity**: {issue.severity.value.upper()}\n"
        report += f"**Category**: {issue.category.value}\n"
        report += f"**Confidence**: {issue.confidence:.0%}\n\n"
        report += f"{issue.description}\n\n"
        
        if issue.probable_causes:
            report += "**Probable Causes:**\n"
            for cause in issue.probable_causes:
                report += f"- {cause}\n"
            report += "\n"
        
        if issue.test_suggestions:
            report += "**Recommended Tests:**\n"
            for test in issue.test_suggestions:
                report += f"- {test}\n"
            report += "\n"
        
        if issue.solutions:
            report += "**Potential Solutions:**\n"
            for solution in issue.solutions[:3]:
                report += f"- {solution}\n"
            report += "\n"
    
    report += "## Troubleshooting Steps Performed\n\n"
    report += "1. **Initial Power Check**\n"
    report += "   - Verified USB input voltage: 5.1V ✅\n"
    report += "   - Checked fuse continuity: OK ✅\n\n"
    
    report += "2. **Voltage Regulator Analysis**\n"
    report += "   - Input voltage present: 5.0V ✅\n"
    report += "   - Output voltage low: 0.3V ❌\n"
    report += "   - Enable pin active: 3.3V ✅\n"
    report += "   - Temperature excessive: 95°C ❌\n\n"
    
    report += "3. **Load Testing**\n"
    report += "   - Measured 3V3 to GND resistance: 12Ω ❌\n"
    report += "   - Normal expected: >1kΩ\n"
    report += "   - Indicates short circuit condition\n\n"
    
    report += "4. **Component Inspection**\n"
    report += "   - Visual inspection revealed burn marks near C5\n"
    report += "   - Removed C5 for testing\n"
    report += "   - Confirmed C5 internally shorted\n\n"
    
    report += "5. **Repair and Verification**\n"
    report += "   - Replaced C5 with new 10uF ceramic capacitor\n"
    report += "   - 3.3V rail now measures 3.28V ✅\n"
    report += "   - Regulator temperature normal: 45°C ✅\n"
    report += "   - Board boots successfully ✅\n\n"
    
    report += "## Root Cause Analysis\n\n"
    report += f"**Root Cause**: {session.root_cause}\n\n"
    report += "**Failure Mechanism**: The ceramic capacitor C5 developed an internal short circuit, "
    report += "likely due to mechanical stress or voltage spike. This created a direct short from the "
    report += "3.3V rail to ground, causing the voltage regulator to enter current limit mode and overheat.\n\n"
    
    report += "## Recommendations\n\n"
    report += "### Immediate Actions\n"
    report += "- ✅ Replace failed capacitor C5 (completed)\n"
    report += "- ✅ Verify all voltage rails before powering MCU\n"
    report += "- ✅ Check for any secondary damage from overheating\n\n"
    
    report += "### Preventive Measures\n"
    report += "- Consider using multiple smaller capacitors instead of single large ceramic\n"
    report += "- Add overcurrent protection or PTC fuse on 3.3V rail\n"
    report += "- Implement soft-start circuit to reduce inrush current\n"
    report += "- Use capacitors with higher voltage rating (10V minimum for 3.3V rail)\n"
    report += "- Add thermal protection/shutdown to voltage regulator\n\n"
    
    report += "## Test Equipment Used\n\n"
    for equipment in tree.equipment_list:
        report += f"- {equipment.value.replace('_', ' ').title()}\n"
    
    report += "\n## Lessons Learned\n\n"
    report += "1. **Ceramic Capacitor Failure**: Large ceramic capacitors (>10uF) are susceptible to "
    report += "mechanical stress cracking which can cause internal shorts\n\n"
    
    report += "2. **Thermal Indicators**: Excessive heat from voltage regulators is often the first "
    report += "indicator of downstream short circuits\n\n"
    
    report += "3. **Systematic Approach**: Following systematic troubleshooting procedures quickly "
    report += "isolated the issue to the output side of the regulator\n\n"
    
    report += "## Appendix: Troubleshooting Tree\n\n"
    report += tree.to_mermaid()
    report += "\n\n---\n"
    report += f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    report += "*Generated with Circuit-Synth Debugging Agent v1.0*\n"
    
    # Save report
    report_file = Path("debug_report.md")
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"   ✅ Markdown report saved to {report_file}")
    
    return report

if __name__ == "__main__":
    main()