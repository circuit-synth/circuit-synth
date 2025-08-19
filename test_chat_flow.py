#!/usr/bin/env python3
"""
Test Chat Flow
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation.core import FastCircuitGenerator

async def test_direct_generation():
    """Test generating directly without the chat interface"""
    
    print("🧪 Testing Direct Professional Generation")
    print("=" * 50)
    
    generator = FastCircuitGenerator()
    
    # Generate ESP32 complete board directly
    output_dir = Path("direct_test_circuits")
    result = generator.generate_hierarchical_project(
        project_type="esp32_complete_board",
        output_dir=output_dir,
        project_name="ESP32_S3_IMU_NeoPixel_Direct"
    )
    
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"📁 Project: {result['project_path']}")
        
        # Check files
        project_path = Path(result["project_path"])
        if project_path.exists():
            files = list(project_path.glob("*.py"))
            print(f"\n🏗️  Generated {len(files)} files:")
            for f in sorted(files):
                print(f"   ├── {f.name}")
                
                # Check for professional features
                try:
                    content = f.read_text()
                    features = []
                    if "USBLC6-2P6" in content:
                        features.append("ESD protection")
                    if "AMS1117" in content:
                        features.append("5V→3.3V regulator")
                    if "5.1k" in content and "CC" in content:
                        features.append("CC resistors")
                    if "100nF" in content:
                        features.append("Decoupling caps")
                    
                    if features:
                        print(f"   │   Features: {', '.join(features)}")
                except:
                    pass
        
        print(f"\n🚀 Test project generation!")
        print(f"cd {result['project_path']}")
        print(f"python3 main.py")
        
        return True
    else:
        print(f"❌ Failed: {result.get('error')}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_generation())
    if success:
        print("\n✅ Direct generation works! The issue is in the chat logic.")
    else:
        print("\n❌ Direct generation failed.")