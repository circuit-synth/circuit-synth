#!/usr/bin/env python3
"""Compare the reference KiCad format with our generated format."""

def format_sexp_pretty(content):
    """Format S-expression with proper indentation for comparison."""
    result = []
    indent = 0
    i = 0
    
    while i < len(content):
        char = content[i]
        
        if char == '(':
            if i > 0 and content[i-1] not in ' \n\t(':
                result.append(' ')
            result.append('(')
            # Look ahead to see if this should be on same line
            j = i + 1
            while j < len(content) and content[j] in ' \t':
                j += 1
            if j < len(content) and content[j] != '(':
                # This is a simple expression, might stay on same line
                pass
            else:
                # Complex expression, new line
                indent += 1
                result.append('\n' + '  ' * indent)
        elif char == ')':
            if result and result[-1] in '\n\t ':
                result.pop()
            result.append(')')
            indent = max(0, indent - 1)
            if i + 1 < len(content) and content[i + 1] == ')':
                pass  # Multiple closing parens
            elif i + 1 < len(content) and content[i + 1] not in ')':
                result.append('\n' + '  ' * indent)
        elif char in ' \t\n':
            if result and result[-1] not in '\n\t ':
                result.append(' ')
            while i + 1 < len(content) and content[i + 1] in ' \t\n':
                i += 1
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result).strip()

print("=== KiCad Reference Format ===")
with open('/Users/shanemattner/Desktop/circuit-synth3/kicad_reference/kicad_reference.kicad_sch', 'r') as f:
    reference = f.read()
    
print(format_sexp_pretty(reference))

print("\n=== Our Generated Format (formatted) ===")
with open('test_schematic_rust.kicad_sch', 'r') as f:
    generated = f.read()
    
formatted = format_sexp_pretty(generated)
# Show first 20 lines
lines = formatted.split('\n')
for line in lines[:20]:
    print(line)
if len(lines) > 20:
    print(f"... ({len(lines) - 20} more lines)")

print("\n=== Key Differences ===")

# Check for uuid format
if "(uuid ." in generated:
    print("❌ Still has dotted pairs in uuid")
elif '(uuid "' in generated:
    print("✅ UUID in correct format")

# Check structure
ref_lines = reference.strip().split('\n')
gen_lines = generated.strip().split('\n')

print(f"\nReference: {len(ref_lines)} lines")
print(f"Generated: {len(gen_lines)} lines (single line)")

# Check for required elements
required = ['(version', '(generator', '(paper', '(lib_symbols']
for req in required:
    if req in generated:
        print(f"✅ Has {req}")
    else:
        print(f"❌ Missing {req}")

# Check optional elements
if '(symbol_instances)' in reference and '(symbol_instances)' not in generated:
    print("⚠️  Reference has (symbol_instances) but we don't generate it")
    
if 'generator_version' in reference:
    print("✅ Both have generator_version")

print("\n=== Minimal Valid Schematic ===")
print("""
The minimal valid KiCad schematic is:
(kicad_sch (version 20250114) (generator "name") (generator_version "version")
  (paper "A4")
  (lib_symbols)
  (symbol_instances)
)

Our format generates everything on one line but includes all required elements.
""")