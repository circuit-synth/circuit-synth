#!/usr/bin/env python3
"""Format the generated S-expression for better readability."""

def format_sexp(content, indent=0):
    """Format S-expression with proper indentation."""
    result = []
    current_indent = indent
    i = 0
    
    while i < len(content):
        char = content[i]
        
        if char == '(':
            # Start of new expression
            result.append('\n' + '\t' * current_indent + '(')
            current_indent += 1
            i += 1
            # Skip whitespace after opening paren
            while i < len(content) and content[i] in ' \t\n':
                i += 1
            i -= 1  # Back up one so we process next char normally
        elif char == ')':
            # End of expression
            current_indent -= 1
            result.append(')')
            # Check if there's another closing paren immediately after
            if i + 1 < len(content) and content[i + 1] == ')':
                pass  # Don't add newline
            else:
                pass  # Add newline will be handled by next open paren
        elif char in ' \t\n':
            # Whitespace - consolidate to single space
            if result and result[-1] not in '\n\t':
                result.append(' ')
            # Skip additional whitespace
            while i + 1 < len(content) and content[i + 1] in ' \t\n':
                i += 1
        else:
            # Regular character
            result.append(char)
        
        i += 1
    
    return ''.join(result)

# Read the generated file
with open('test_schematic_rust.kicad_sch', 'r') as f:
    content = f.read()

# Format it
formatted = format_sexp(content)

# Write formatted version
with open('test_schematic_rust_formatted.kicad_sch', 'w') as f:
    f.write(formatted)

print("Formatted file written to test_schematic_rust_formatted.kicad_sch")

# Show first 50 lines
lines = formatted.split('\n')
for i, line in enumerate(lines[:50], 1):
    print(f"{i:3}: {line}")