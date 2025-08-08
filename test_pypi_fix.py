#!/usr/bin/env python3
"""
Test script to verify PyPI fix works without Rust modules
"""

import sys
import os

# Simulate PyPI environment by temporarily hiding Rust modules  
import shutil
rust_modules_path = os.path.join(os.path.dirname(__file__), "rust_modules")
backup_path = rust_modules_path + "_backup"

try:
    # Temporarily move rust_modules to simulate PyPI environment
    if os.path.exists(rust_modules_path):
        print("🔄 Temporarily hiding Rust modules to simulate PyPI environment...")
        shutil.move(rust_modules_path, backup_path)
    
    print("🧪 Testing circuit-synth without Rust modules...")
    
    # Test imports
    from circuit_synth import Circuit, Component, Net, circuit
    print("✅ Core imports successful")
    
    # Test circuit creation with decorator
    @circuit('test_circuit')
    def test_basic_circuit():
        """Test basic circuit functionality"""
        
        # Test net and component creation
        VCC = Net('VCC')
        GND = Net('GND')
        print("✅ Net creation successful")
        
        vreg = Component(
            symbol='Regulator_Linear:AMS1117-3.3',
            ref='U', 
            footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2'
        )
        print("✅ Component creation successful")
        
        # Test connections
        vreg['VI'] += VCC
        vreg['GND'] += GND
        print("✅ Component connections successful")
        
        return locals()
        
    # Execute the circuit function
    result = test_basic_circuit()
    print("✅ Circuit function execution successful")
    
    print("🎉 All basic functionality works without Rust modules!")
    print("💡 PyPI fix successful - fallback to Python backend working")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Restore rust_modules
    if os.path.exists(backup_path):
        print("🔄 Restoring Rust modules...")
        shutil.move(backup_path, rust_modules_path)