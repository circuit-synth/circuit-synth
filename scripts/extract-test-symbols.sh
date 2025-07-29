#!/bin/bash
# Extract specific symbols from local KiCad installation for testing

set -e

echo "🔍 Extracting KiCad symbols for testing..."

# Find KiCad symbol directory
KICAD_SYMBOLS=""
if [ -n "$KICAD_SYMBOL_DIR" ]; then
    KICAD_SYMBOLS="$KICAD_SYMBOL_DIR"
elif [ -d "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols" ]; then
    KICAD_SYMBOLS="/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
elif [ -d "/usr/share/kicad/symbols" ]; then
    KICAD_SYMBOLS="/usr/share/kicad/symbols"
elif [ -d "/usr/local/share/kicad/symbols" ]; then
    KICAD_SYMBOLS="/usr/local/share/kicad/symbols"
else
    echo "❌ Could not find KiCad symbols directory"
    exit 1
fi

echo "📂 Found KiCad symbols at: $KICAD_SYMBOLS"

# Create output directory
OUTPUT_DIR="tests/test_data/symbols"
mkdir -p "$OUTPUT_DIR"

# Function to extract a specific symbol from a library file
extract_symbol() {
    local library_file="$1"
    local symbol_name="$2"
    local output_file="$3"
    
    if [ ! -f "$library_file" ]; then
        echo "⚠️  Library file not found: $library_file"
        return 1
    fi
    
    echo "📋 Extracting $symbol_name from $(basename "$library_file")..."
    
    # Use a simpler approach: find the symbol and extract its complete definition
    python3 -c "
import sys
import re

symbol_name = '$symbol_name'
library_file = '$library_file'
output_file = '$output_file.tmp'

with open(library_file, 'r') as f:
    content = f.read()

# Find the symbol definition with proper parenthesis matching
def find_symbol_definition(content, symbol_name):
    lines = content.split('\n')
    symbol_lines = []
    paren_count = 0
    in_symbol = False
    
    for line in lines:
        if f'(symbol \"{symbol_name}\"' in line:
            in_symbol = True
            paren_count = 0
            symbol_lines = []
        
        if in_symbol:
            symbol_lines.append(line)
            # Count parentheses
            paren_count += line.count('(') - line.count(')')
            
            # If we've closed all parentheses, we're done
            if paren_count <= 0 and len(symbol_lines) > 1:
                return '\n'.join(symbol_lines)
    
    return None

symbol_text = find_symbol_definition(content, symbol_name)

if symbol_text:
    # Write minimal library with just this symbol
    with open(output_file, 'w') as f:
        f.write('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n')
        f.write('  ' + symbol_text + '\n')
        f.write(')\n')
    print(f'✅ Extracted {symbol_name}')
else:
    print(f'❌ Symbol {symbol_name} not found')
    sys.exit(1)
"
    
    # Move the temp file to final location
    if [ -f "$output_file.tmp" ]; then
        mv "$output_file.tmp" "$output_file"
        return 0
    else
        return 1
    fi
}

# Function to create a multi-symbol library file
create_library() {
    local output_file="$1"
    shift
    local temp_files=("$@")
    
    echo "📚 Creating library: $(basename "$output_file")"
    
    # Use Python to combine multiple symbol files into one library
    python3 -c "
import sys
import re

output_file = '$output_file'
temp_files = [f for f in '''$*'''.split() if f]

with open(output_file, 'w') as outf:
    outf.write('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n')
    
    for temp_file in temp_files:
        try:
            with open(temp_file, 'r') as inf:
                content = inf.read()
                # Extract just the symbol definition
                symbol_match = re.search(r'(\(symbol\s+.*?^\))', content, re.MULTILINE | re.DOTALL)
                if symbol_match:
                    outf.write('  ' + symbol_match.group(1) + '\n')
        except FileNotFoundError:
            print(f'Warning: {temp_file} not found')
    
    outf.write(')\n')
print(f'Created {output_file}')
"
    
    # Clean up temp files
    for temp_file in "${temp_files[@]}"; do
        rm -f "$temp_file"
    done
}

# Extract symbols we need for tests
echo "🎯 Extracting required symbols..."

# Device library symbols
extract_symbol "$KICAD_SYMBOLS/Device.kicad_sym" "R" "/tmp/device_r.sym"
extract_symbol "$KICAD_SYMBOLS/Device.kicad_sym" "C" "/tmp/device_c.sym"
extract_symbol "$KICAD_SYMBOLS/Device.kicad_sym" "R_Network12_Split" "/tmp/device_rnet.sym"

create_library "$OUTPUT_DIR/Device.kicad_sym" "/tmp/device_r.sym" "/tmp/device_c.sym" "/tmp/device_rnet.sym"

# Power library symbols  
extract_symbol "$KICAD_SYMBOLS/power.kicad_sym" "GND" "/tmp/power_gnd.sym"
extract_symbol "$KICAD_SYMBOLS/power.kicad_sym" "+3V3" "/tmp/power_3v3.sym"

create_library "$OUTPUT_DIR/power.kicad_sym" "/tmp/power_gnd.sym" "/tmp/power_3v3.sym"

# Regulator library symbols
extract_symbol "$KICAD_SYMBOLS/Regulator_Linear.kicad_sym" "AMS1117-3.3" "/tmp/reg_ams.sym"
extract_symbol "$KICAD_SYMBOLS/Regulator_Linear.kicad_sym" "AP1117-15" "/tmp/reg_ap.sym"

create_library "$OUTPUT_DIR/Regulator_Linear.kicad_sym" "/tmp/reg_ams.sym" "/tmp/reg_ap.sym"

echo "✅ Symbol extraction complete!"
echo "📊 Created $(find "$OUTPUT_DIR" -name "*.kicad_sym" | wc -l) symbol libraries"
echo "📋 Files created:"
ls -la "$OUTPUT_DIR"/*.kicad_sym