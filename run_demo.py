#!/usr/bin/env python3
"""
Circuit Demo Runner - Installs dependencies and runs the voltage divider demo
"""

import subprocess
import sys

def install_and_run():
    """Install required packages and run the demo"""
    
    print("🚀 Circuit-Synth Voltage Divider Demo")
    print("=" * 50)
    
    # Check if we need to install plotly
    try:
        import plotly
        print("✅ Plotly already installed")
    except ImportError:
        print("📦 Installing plotly...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'plotly'])
            print("✅ Plotly installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install plotly: {e}")
            print("Please run: pip install plotly")
            return False
    
    # Check numpy
    try:
        import numpy
        print("✅ NumPy available")
    except ImportError:
        print("📦 Installing numpy...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy'])
            print("✅ NumPy installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install numpy: {e}")
            return False
    
    print("\n🎯 Starting voltage divider demo...")
    print("-" * 50)
    
    # Run the actual demo
    try:
        import voltage_divider_demo
        return True
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = install_and_run()
    if success:
        print("\n🎉 Demo completed successfully!")
    else:
        print("\n❌ Demo failed - check error messages above")
        sys.exit(1)