# Generate Validated Circuit

Generate circuit code with automatic validation and quality assurance.

## Usage
```bash
/generate-validated-circuit <description> [type]
```

## Parameters
- `description`: Circuit description (required)
- `type`: Circuit type for context (optional: general, power, mcu, usb, analog)

## What It Does
1. **Context Gathering** - Gets relevant design patterns and best practices
2. **Intelligent Generation** - Creates circuit code using proven patterns
3. **Automatic Validation** - Checks syntax, imports, and basic execution
4. **Quality Improvement** - Applies fixes for common issues
5. **Status Reporting** - Provides clear validation results

## Examples
```bash
# General circuit
/generate-validated-circuit "ESP32 development board"

# Power supply circuit  
/generate-validated-circuit "3.3V regulator with USB-C input" power

# STM32 microcontroller
/generate-validated-circuit "STM32F4 with crystal and debug connector" mcu

# USB interface
/generate-validated-circuit "USB-C connector with protection" usb
```

## Output Format
- Generated circuit code with validation status
- Clear indication of any issues found
- Applied fixes and improvements noted
- Quality assurance summary

This ensures your circuit code compiles, runs, and follows best practices.