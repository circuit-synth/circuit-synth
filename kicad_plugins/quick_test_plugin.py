#!/usr/bin/env python3
"""
Quick Test Plugin for KiCad BOM Integration

This simple plugin helps test if the BOM integration is working
and ensures the GUI appears properly.
"""

import sys
import argparse
from pathlib import Path

def main():
    """Main test function with visible GUI."""
    parser = argparse.ArgumentParser(description='Quick KiCad Plugin Test')
    parser.add_argument('netlist_file', help='Path to the netlist XML file from KiCad')
    parser.add_argument('output_file', help='Output file path')
    
    args = parser.parse_args()
    
    print("🚀 Quick Test Plugin Starting...")
    print(f"📄 Netlist: {args.netlist_file}")
    print(f"📝 Output: {args.output_file}")
    
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # Create a simple test window
        root = tk.Tk()
        root.title("🧪 KiCad Plugin Test - SUCCESS!")
        root.geometry("400x200")
        
        # Force window to front
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        
        # Add content
        label = tk.Label(
            root, 
            text="✅ Plugin Integration Working!\n\nThis confirms:\n• KiCad can run Python plugins\n• GUI windows can be created\n• All permissions are correct",
            font=('Arial', 12),
            justify='center'
        )
        label.pack(expand=True)
        
        # Button to close
        def close_window():
            root.destroy()
            
        button = tk.Button(root, text="Close", command=close_window, font=('Arial', 12))
        button.pack(pady=10)
        
        # Write output file to satisfy KiCad
        try:
            Path(args.output_file).write_text("KiCad Plugin Test Successful\nGUI window opened correctly\n")
        except:
            pass
        
        print("✅ GUI window created - check if it's visible!")
        
        # Run the GUI
        root.mainloop()
        
    except ImportError:
        print("❌ tkinter not available")
        # Write text output instead
        try:
            Path(args.output_file).write_text("Plugin test ran but GUI not available\n")
        except:
            pass
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            Path(args.output_file).write_text(f"Plugin test failed: {e}\n")  
        except:
            pass

if __name__ == "__main__":
    main()