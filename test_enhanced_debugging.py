#!/usr/bin/env python3
"""
Test the enhanced debugging agent with comprehensive knowledge base
"""

from circuit_synth.debugging import CircuitDebugger, DebugSession
from circuit_synth.ai_integration.agents.debugging_agent import CircuitDebuggingAgent
import json
from pathlib import Path


def test_knowledge_base_debugging():
    """Test debugging with comprehensive knowledge base"""
    
    print("🔍 Testing Enhanced Circuit Debugging with Knowledge Base")
    print("=" * 60)
    
    # Initialize debugger (will auto-load knowledge base)
    debugger = CircuitDebugger()
    
    # Start a debugging session
    session = debugger.start_session("STM32F4_Board", "2.0")
    
    print("\n📋 Test Case 1: Capacitor Failure")
    print("-" * 40)
    
    # Add symptoms that match capacitor failure modes
    session.add_symptom("Short circuit on power rail")
    session.add_symptom("Excessive leakage current")
    session.add_symptom("Board overheating")
    
    # Analyze with knowledge base
    issues = debugger.analyze_symptoms(session)
    
    print(f"Found {len(issues)} potential issues:")
    for i, issue in enumerate(issues[:3], 1):  # Show top 3
        print(f"\n{i}. {issue.title}")
        print(f"   Category: {issue.category.value}")
        print(f"   Severity: {issue.severity.value}")
        print(f"   Confidence: {issue.confidence:.0%}")
        print(f"   Probable Causes: {', '.join(issue.probable_causes[:2])}")
        print(f"   Test Suggestions: {', '.join(issue.test_suggestions[:2])}")
    
    print("\n\n📋 Test Case 2: I2C Communication Failure")
    print("-" * 40)
    
    # New session for I2C issues
    session2 = debugger.start_session("ESP32_Sensor_Board", "1.0")
    
    session2.add_symptom("I2C no ACK from sensor")
    session2.add_symptom("SDA stuck low")
    session2.add_measurement("SDA_voltage", 0.3, "V", "Measured when idle")
    session2.add_measurement("SCL_voltage", 3.3, "V", "Normal high level")
    
    issues2 = debugger.analyze_symptoms(session2)
    
    print(f"Found {len(issues2)} potential issues:")
    for i, issue in enumerate(issues2[:3], 1):
        print(f"\n{i}. {issue.title}")
        print(f"   Category: {issue.category.value}")
        print(f"   Severity: {issue.severity.value}")
        print(f"   Test Suggestions:")
        for j, test in enumerate(issue.test_suggestions[:3], 1):
            print(f"      {j}. {test}")
    
    print("\n\n📋 Test Case 3: USB Enumeration Failure")
    print("-" * 40)
    
    session3 = debugger.start_session("USB_Device", "1.1")
    
    session3.add_symptom("USB device not detected")
    session3.add_symptom("Enumeration fails")
    
    issues3 = debugger.analyze_symptoms(session3)
    
    print(f"Found {len(issues3)} potential issues:")
    for i, issue in enumerate(issues3[:3], 1):
        print(f"\n{i}. {issue.title}")
        print(f"   Solutions:")
        for j, solution in enumerate(issue.solutions[:3], 1):
            print(f"      {j}. {solution}")
    
    print("\n\n📋 Test Case 4: Power Supply Not Working")
    print("-" * 40)
    
    session4 = debugger.start_session("Power_Board", "1.0")
    
    session4.add_symptom("Board not turning on")
    session4.add_symptom("No voltage on output")
    
    issues4 = debugger.analyze_symptoms(session4)
    
    print(f"Found {len(issues4)} potential issues:")
    for i, issue in enumerate(issues4[:2], 1):
        print(f"\n{i}. {issue.title}")
        print(f"   Description: {issue.description}")
        if "systematic" in issue.title.lower():
            print(f"   Systematic Approach:")
            for j, test in enumerate(issue.test_suggestions[:5], 1):
                print(f"      {test}")


def test_ai_agent():
    """Test the AI debugging agent"""
    
    print("\n\n🤖 Testing AI Debugging Agent")
    print("=" * 60)
    
    agent = CircuitDebuggingAgent()
    
    # Test component failure lookup
    failures = agent._find_relevant_failures("short circuit")
    print(f"\nFound {len(failures)} component failures related to 'short circuit':")
    for failure in failures[:3]:
        print(f"  - {failure['component_type']}: {failure['failure_mode']}")
    
    # Test problem lookup
    problems = agent._find_relevant_problems("no ack")
    print(f"\nFound {len(problems)} common problems related to 'no ack':")
    for problem in problems[:3]:
        print(f"  - {problem['category']}/{problem['issue']}: {problem.get('description', 'N/A')}")
    
    # Test debugging techniques
    techniques = agent._get_debugging_techniques("i2c no ack")
    print(f"\nFound {len(techniques)} debugging techniques for 'i2c no ack':")
    for i, technique in enumerate(techniques[:5], 1):
        print(f"  {i}. {technique}")
    
    # Test test plan generation
    print("\n\n📝 Generating Test Plan")
    print("-" * 40)
    
    symptoms = ["Power not turning on", "No LED activity"]
    measurements = {"Input_Voltage": {"value": 5.0, "unit": "V"}}
    
    test_plan = agent.generate_test_plan(symptoms, measurements)
    
    print("Test Plan:")
    for step in test_plan[:5]:
        if "equipment_required" in step:
            print(f"\nRequired Equipment: {', '.join(step['equipment_required'])}")
            print(f"Preparation: {step['preparation']}")
        else:
            print(f"\nStep {step['step']}: {step['test']}")
            print(f"  Equipment: {step['equipment']}")
            print(f"  Procedure: {step['procedure']}")
            print(f"  Expected: {step['expected']}")


def verify_knowledge_base_loaded():
    """Verify that knowledge base files are loaded correctly"""
    
    print("\n\n✅ Verifying Knowledge Base Loading")
    print("=" * 60)
    
    kb_path = Path(__file__).parent / "debugging_knowledge_base"
    
    files = [
        "component_failure_modes.json",
        "debugging_techniques.json",
        "common_problems_solutions.json",
        "test_equipment_guide.json"
    ]
    
    for filename in files:
        file_path = kb_path / filename
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
                # Count items in the knowledge base
                if "component_failure_modes" in data:
                    component_count = len(data["component_failure_modes"])
                    print(f"✓ {filename}: {component_count} component types loaded")
                elif "debugging_techniques" in data:
                    tech_count = len(data["debugging_techniques"])
                    print(f"✓ {filename}: {tech_count} technique categories loaded")
                elif "common_pcb_problems" in data:
                    prob_count = sum(len(v) if isinstance(v, dict) else 0 
                                   for v in data["common_pcb_problems"].values())
                    print(f"✓ {filename}: {prob_count} problem types loaded")
                elif "test_equipment_guide" in data:
                    equip_count = len(data["test_equipment_guide"])
                    print(f"✓ {filename}: {equip_count} equipment categories loaded")
        else:
            print(f"✗ {filename}: NOT FOUND")


if __name__ == "__main__":
    # Verify knowledge base is loaded
    verify_knowledge_base_loaded()
    
    # Test the enhanced debugging
    test_knowledge_base_debugging()
    
    # Test the AI agent
    test_ai_agent()
    
    print("\n\n✨ Enhanced debugging test complete!")
    print("The debugging agent now incorporates:")
    print("  • Component failure modes database")
    print("  • Common PCB problems and solutions")
    print("  • Professional debugging techniques")
    print("  • Test equipment usage guides")
    print("  • KiCad-to-Python conversion capability")
    print("  • Web search guidance for additional insights")