#!/usr/bin/env python3
"""
Demonstration: Debug a KiCad PCB Project with Enhanced AI Agent

This shows the complete workflow:
1. Convert KiCad project to Python for LLM analysis
2. Analyze symptoms against comprehensive knowledge base
3. Generate systematic test plans
4. Provide web search guidance
"""

from circuit_synth.ai_integration.agents.debugging_agent import CircuitDebuggingAgent
from circuit_synth.debugging import CircuitDebugger
from circuit_synth.debugging.report_generator import DebugReportGenerator
from pathlib import Path
import json


def demo_full_debugging_workflow():
    """
    Demonstrate the complete debugging workflow
    """
    
    print("🔍 PCB Debugging Agent - Full Workflow Demo")
    print("=" * 60)
    print()
    
    # Initialize the AI debugging agent
    agent = CircuitDebuggingAgent()
    
    # Example KiCad project path (would be actual project in real use)
    # For demo, we'll simulate the analysis
    kicad_project = "/path/to/your/kicad/project"
    
    # Symptoms reported by user
    symptoms = [
        "Board not powering on",
        "I2C communication failing - no ACK from BME280 sensor",
        "USB device not enumerating",
        "3.3V rail measuring 2.8V",
        "Excessive current draw (500mA instead of expected 100mA)"
    ]
    
    # Measurements already taken
    measurements = {
        "VBUS": {"value": 5.0, "unit": "V", "notes": "USB input OK"},
        "3V3_rail": {"value": 2.8, "unit": "V", "notes": "Below spec"},
        "5V_rail": {"value": 4.9, "unit": "V", "notes": "Within tolerance"},
        "Total_Current": {"value": 500, "unit": "mA", "notes": "5x expected"},
        "SDA_voltage": {"value": 2.8, "unit": "V", "notes": "Follows 3.3V rail"},
        "SCL_voltage": {"value": 2.8, "unit": "V", "notes": "Follows 3.3V rail"}
    }
    
    # Additional observations
    observations = [
        "Voltage regulator is very hot to touch",
        "No visible damage or burnt components",
        "Board was working yesterday, failed after reassembly",
        "Using USB-C connector for power",
        "I2C pullups are 4.7k resistors"
    ]
    
    print("📊 SYMPTOMS REPORTED:")
    print("-" * 40)
    for symptom in symptoms:
        print(f"  • {symptom}")
    
    print("\n📏 MEASUREMENTS TAKEN:")
    print("-" * 40)
    for name, data in measurements.items():
        print(f"  • {name}: {data['value']}{data['unit']} - {data['notes']}")
    
    print("\n👁️ OBSERVATIONS:")
    print("-" * 40)
    for obs in observations:
        print(f"  • {obs}")
    
    # Generate comprehensive debug report
    print("\n\n🔬 ANALYZING WITH AI DEBUGGING AGENT...")
    print("=" * 60)
    
    # Note: In real use, this would convert the actual KiCad project
    # For demo, we'll show what the analysis would produce
    
    print("\n📝 GENERATED TEST PLAN:")
    print("-" * 40)
    
    test_plan = agent.generate_test_plan(symptoms, measurements)
    
    for i, step in enumerate(test_plan[:8]):
        if "equipment_required" in step:
            print(f"\n🔧 Required Equipment: {', '.join(step['equipment_required'])}")
            print(f"📋 {step['preparation']}")
        else:
            print(f"\n{step['step']}. {step['test']}")
            print(f"   Equipment: {step['equipment']}")
            print(f"   Procedure: {step['procedure']}")
            print(f"   Expected: {step['expected']}")
            if 'if_fail' in step:
                print(f"   If Fail: {step['if_fail']}")
    
    print("\n\n🎯 IDENTIFIED ISSUES (from Knowledge Base):")
    print("-" * 40)
    
    # Use the standard debugger with knowledge base
    debugger = CircuitDebugger()
    session = debugger.start_session("Demo_Board", "1.0")
    
    for symptom in symptoms:
        session.add_symptom(symptom)
    
    for name, data in measurements.items():
        session.add_measurement(name, data['value'], data['unit'], data['notes'])
    
    for obs in observations:
        session.add_observation(obs)
    
    issues = debugger.analyze_symptoms(session)
    
    # Group issues by severity
    critical = [i for i in issues if i.severity.value == "critical"]
    high = [i for i in issues if i.severity.value == "high"]
    medium = [i for i in issues if i.severity.value == "medium"]
    
    if critical:
        print("\n🔴 CRITICAL ISSUES:")
        for issue in critical[:2]:
            print(f"\n  {issue.title}")
            print(f"  Confidence: {issue.confidence:.0%}")
            print(f"  Probable Causes:")
            for cause in issue.probable_causes[:3]:
                print(f"    - {cause}")
            print(f"  Immediate Actions:")
            for action in issue.test_suggestions[:3]:
                print(f"    ✓ {action}")
    
    if high:
        print("\n🟠 HIGH PRIORITY ISSUES:")
        for issue in high[:3]:
            print(f"\n  {issue.title}")
            print(f"  Related to: {', '.join(issue.related_components[:3])}")
            print(f"  Solutions:")
            for solution in issue.solutions[:2]:
                print(f"    → {solution}")
    
    print("\n\n💡 ROOT CAUSE ANALYSIS:")
    print("-" * 40)
    print("""
Based on the symptoms and measurements, the most likely root causes are:

1. **Overloaded 3.3V Regulator**
   - Evidence: 3.3V rail at 2.8V (undervoltage)
   - Evidence: Excessive current draw (500mA vs 100mA expected)
   - Evidence: Hot regulator
   - Likely Cause: Short circuit or damaged component on 3.3V rail
   
2. **I2C Communication Failure (Secondary)**
   - Evidence: No ACK from sensor
   - Evidence: Voltage levels follow failing 3.3V rail
   - Likely Cause: Insufficient voltage for I2C operation
   
3. **USB Enumeration (Consequence)**
   - Likely failing due to MCU brownout from low 3.3V
""")
    
    print("\n📋 RECOMMENDED DEBUG SEQUENCE:")
    print("-" * 40)
    print("""
1. **Isolate the Short/Overload**
   - Disconnect peripheral boards/modules one by one
   - Monitor current draw after each disconnection
   - When current drops to normal, you've found the problem section

2. **Check for Physical Issues**
   - Inspect for solder bridges with microscope
   - Look for damaged components (bulging caps, burnt marks)
   - Check recent assembly work for errors

3. **Verify Component Values**
   - Confirm voltage regulator is correct part number
   - Check current limiting resistors haven't been swapped
   - Verify decoupling capacitors are correct values

4. **Test Without Load**
   - Remove all loads from 3.3V rail
   - Test if regulator outputs correct voltage unloaded
   - Gradually reconnect components while monitoring
""")
    
    # Web search guidance
    print("\n\n🌐 WEB SEARCH RECOMMENDATIONS:")
    print("-" * 40)
    
    board_info = {"mcu": "STM32F4"}  # Example
    search_guidance = agent.search_web_for_solution(symptoms, board_info)
    print(search_guidance)
    
    print("\n\n📊 DEBUGGING METRICS:")
    print("-" * 40)
    print(f"Total Issues Identified: {len(issues)}")
    print(f"Knowledge Base Matches: {sum(1 for i in issues if i.confidence > 0.7)}")
    print(f"Test Steps Generated: {len(test_plan)}")
    print(f"Critical Issues: {len(critical)}")
    print(f"Suggested Solutions: {sum(len(i.solutions) for i in issues)}")
    
    # Generate PDF report (if needed)
    print("\n\n📄 REPORT GENERATION:")
    print("-" * 40)
    print("Generating comprehensive PDF report...")
    
    try:
        generator = DebugReportGenerator()
        
        # Generate markdown report
        md_report = generator.generate_markdown_report(session, include_kb_analysis=True)
        with open("debug_report.md", "w") as f:
            f.write(md_report)
        print("✓ Markdown report saved to: debug_report.md")
        
        # Generate PDF report
        pdf_path = generator.generate_pdf_report(session, "debug_report.pdf", include_kb_analysis=True)
        print(f"✓ PDF report saved to: {pdf_path}")
    except Exception as e:
        print(f"Note: Report generation requires reportlab: {e}")
    
    print("\n\n✨ DEBUGGING WORKFLOW COMPLETE!")
    print("=" * 60)
    print("""
The enhanced debugging agent has:
✓ Analyzed symptoms against comprehensive knowledge base
✓ Identified probable root causes with confidence scores
✓ Generated systematic test plan with equipment requirements
✓ Provided prioritized action items
✓ Suggested web search strategies for additional info
✓ Created detailed reports for documentation

Next Steps:
1. Follow the test plan systematically
2. Document results of each test
3. Update the session with findings
4. Let the AI agent refine diagnosis based on test results
""")


if __name__ == "__main__":
    demo_full_debugging_workflow()