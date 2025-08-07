#!/usr/bin/env python3
"""
Generate PDF report from debugging session
"""

import json
from pathlib import Path

# Check if reportlab is available
try:
    from circuit_synth.debugging.report_generator import DebugReportGenerator
    
    # Load the session data
    session_file = Path("debug_session_report.json")
    if session_file.exists():
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        print("📄 Generating PDF report...")
        
        # Generate PDF
        generator = DebugReportGenerator(session_data)
        output_file = generator.generate_pdf("PCB_Debug_Report.pdf")
        
        print(f"✅ PDF report generated: {output_file}")
        print(f"   File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
    else:
        print("❌ Session file not found. Run test_debugging_demo.py first.")
        
except ImportError as e:
    print("⚠️  reportlab not installed. Installing now...")
    import subprocess
    import sys
    
    # Try to install reportlab
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        print("✅ reportlab installed successfully. Please run this script again.")
    except subprocess.CalledProcessError:
        print("❌ Failed to install reportlab. Please install manually with:")
        print("   pip install reportlab")
        print("   or")
        print("   uv pip install reportlab")