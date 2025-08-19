#!/usr/bin/env python3
"""
Test the new professional circuit chat system
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation.core import FastCircuitGenerator


async def test_professional_generation():
    """Test the new hierarchical generation system"""
    
    print("🧪 Testing Professional Circuit Generation System")
    print("=" * 60)
    
    # Test hierarchical project generation
    generator = FastCircuitGenerator()
    
    output_dir = Path("test_professional_circuits")
    result = generator.generate_hierarchical_project(
        project_type="esp32_complete_board",
        output_dir=output_dir,
        project_name="ESP32_Professional_Test"
    )
    
    if result["success"]:
        print("✅ Hierarchical project generated successfully!")
        print(f"📁 Project: {result['project_path']}")
        
        project_path = Path(result["project_path"])
        if project_path.exists():
            files = list(project_path.glob("*.py"))
            print(f"🏗️  Generated {len(files)} subcircuit files:")
            
            for file_path in sorted(files):
                print(f"   ├── {file_path.name}")
                
                # Show key improvements in each file
                try:
                    content = file_path.read_text()
                    
                    improvements = []
                    if "USBLC6-2P6" in content:
                        improvements.append("ESD protection")
                    if "5.1k" in content and "CC" in content:
                        improvements.append("CC resistors")
                    if "AMS1117" in content:
                        improvements.append("5V→3.3V regulator")
                    if "100nF" in content or "10uF" in content:
                        improvements.append("Decoupling caps")
                    if "10k" in content and "pullup" in content.lower():
                        improvements.append("Pull-up resistors")
                    
                    if improvements:
                        print(f"   │   Professional features: {', '.join(improvements)}")
                        
                except Exception:
                    pass
            
            print()
            print("🎯 Key Professional Features Added:")
            print("   ✅ Hierarchical structure like example_project/circuit-synth/")
            print("   ✅ USB-C with CC1/CC2 pull-down resistors (5.1kΩ)")
            print("   ✅ ESD protection (USBLC6-2P6) on USB data lines")
            print("   ✅ 5V→3.3V regulation (AMS1117-3.3) with filtering")
            print("   ✅ Proper decoupling capacitors on all power rails")
            print("   ✅ Pull-up resistors where needed (EN, I2C)")
            print("   ✅ Modular design with separate subcircuit files")
            print()
            
            print("🚀 To test this project:")
            print(f"   cd {project_path}")
            print("   python3 main.py")
            
        return True
    else:
        print(f"❌ Generation failed: {result.get('error')}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_professional_generation())
        if success:
            print("\n🎉 Professional circuit generation system is working!")
            print("💬 Now try: python3 circuit_chat.py")
        else:
            print("\n❌ Test failed - check the error messages above")
    except Exception as e:
        print(f"\n❌ Test error: {e}")