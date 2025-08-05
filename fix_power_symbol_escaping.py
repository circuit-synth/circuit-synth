#!/usr/bin/env python3
"""
Fix for power symbol Description property escaping issue.
This script fixes the malformed preservation_test.kicad_sch file.
"""

import re
from pathlib import Path

def fix_description_escaping(file_path):
    """Fix unescaped quotes in Description properties."""
    path = Path(file_path)
    content = path.read_text()
    
    # Pattern to match Description properties with embedded quotes
    # This regex captures the Description property and fixes the inner quotes
    pattern = r'(property "Description" ")([^"]*)"([^"]*)" ([^"]*")'
    
    def replace_quotes(match):
        # Reconstruct with escaped inner quotes
        prefix = match.group(1)
        part1 = match.group(2)
        quoted = match.group(3)  # This is the part that was in quotes (e.g., GND)
        part2 = match.group(4)
        
        # Escape the inner quotes
        return f'{prefix}{part1}\\"{quoted}\\" {part2}'
    
    # Apply the fix
    fixed_content = re.sub(pattern, replace_quotes, content)
    
    # Write back
    path.write_text(fixed_content)
    print(f"Fixed {file_path}")
    
    # Show what was fixed
    if content != fixed_content:
        print("Fixed Description properties with unescaped quotes")
    else:
        print("No changes needed")

if __name__ == "__main__":
    fix_description_escaping("/Users/shanemattner/Desktop/circuit-synth/preservation_test/preservation_test.kicad_sch")