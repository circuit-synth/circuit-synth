"""
Super simple circuit validator for Claude Code integration.

This module provides lightweight validation that catches the most common
circuit code issues while integrating seamlessly with Claude Code agents.
"""

import ast
import logging
import os
import subprocess
import tempfile
from typing import List, Optional, Tuple

# Set up logging for debugging
logger = logging.getLogger(__name__)


def validate_and_improve_circuit(
    code: str, max_attempts: int = 2, timeout_seconds: int = 10
) -> Tuple[str, bool, str]:
    """
    Validate circuit code and return improved version.

    This function performs basic validation checks and can attempt automatic
    improvements. It's designed to catch the most common issues:
    - Syntax errors
    - Missing imports
    - Basic runtime failures

    Args:
        code: Circuit code to validate
        max_attempts: Maximum improvement attempts (default: 2)
        timeout_seconds: Execution timeout (default: 10)

    Returns:
        Tuple of (improved_code, is_valid, status_message)

    Example:
        >>> code = "from circuit_synth import Component\\nComponent('Device:R', 'R')"
        >>> improved, valid, status = validate_and_improve_circuit(code)
        >>> print(f"Valid: {valid}, Status: {status}")
    """

    logger.info(f"Starting validation with {max_attempts} max attempts")

    current_code = code
    original_code = code  # Keep original for comparison

    for attempt in range(max_attempts):
        logger.debug(f"Validation attempt {attempt + 1}")

        # Check for issues
        issues = _check_circuit_code(current_code, timeout_seconds)

        if not issues:
            success_msg = f"✅ Circuit code validated successfully"
            if attempt > 0:
                success_msg += f" (fixed in {attempt} attempts)"
            logger.info(success_msg)
            return current_code, True, success_msg

        logger.warning(f"Found {len(issues)} issues: {issues}")

        # For first attempt, try basic auto-fixes
        if attempt == 0:
            current_code = _apply_basic_fixes(current_code, issues)
        else:
            # For subsequent attempts, annotate issues for Claude
            issue_comments = "\n".join(f"# ISSUE: {issue}" for issue in issues)
            current_code = f"""# Circuit validation issues found:
{issue_comments}
# Original code:

{original_code}"""

    # Max attempts reached
    final_status = f"⚠️ Still has {len(issues)} issues after {max_attempts} attempts"
    logger.warning(final_status)
    return current_code, False, final_status


def _check_circuit_code(code: str, timeout_seconds: int = 10) -> List[str]:
    """
    Perform comprehensive but lightweight circuit code checking.

    Args:
        code: Code to check
        timeout_seconds: Execution timeout

    Returns:
        List of issue descriptions (empty if no issues)
    """
    issues = []

    # 1. Syntax validation using AST
    try:
        ast.parse(code)
        logger.debug("✓ Syntax check passed")
    except SyntaxError as e:
        syntax_issue = f"Syntax error at line {e.lineno}: {e.msg}"
        issues.append(syntax_issue)
        logger.error(f"Syntax error: {e}")
        return issues  # Can't continue with broken syntax

    # 2. Import validation
    import_issues = _check_imports(code)
    issues.extend(import_issues)

    # 3. Basic circuit structure validation
    structure_issues = _check_circuit_structure(code)
    issues.extend(structure_issues)

    # 4. Runtime validation (only if no critical issues)
    if not issues:
        runtime_issues = _check_runtime_execution(code, timeout_seconds)
        issues.extend(runtime_issues)

    return issues


def _check_imports(code: str) -> List[str]:
    """Check for essential circuit_synth imports."""
    issues = []

    # Check for essential circuit_synth import
    if "from circuit_synth import" not in code and "import circuit_synth" not in code:
        issues.append("Missing circuit_synth framework import")

    # Check for common component usage without import
    if "Component(" in code and "Component" not in _extract_imports(code):
        issues.append("Component class used but not imported")

    if "Net(" in code and "Net" not in _extract_imports(code):
        issues.append("Net class used but not imported")

    if "@circuit" in code and "circuit" not in _extract_imports(code):
        issues.append("@circuit decorator used but not imported")

    logger.debug(f"Import check found {len(issues)} issues")
    return issues


def _extract_imports(code: str) -> List[str]:
    """Extract imported names from code."""
    imports = []

    for line in code.split("\n"):
        line = line.strip()
        if line.startswith("from circuit_synth import"):
            # Extract everything after "import"
            import_part = line.split("import")[1].strip()
            # Handle comma-separated imports
            imports.extend(name.strip() for name in import_part.split(","))
        elif line.startswith("import circuit_synth"):
            imports.append("circuit_synth")

    return imports


def _check_circuit_structure(code: str) -> List[str]:
    """Check for basic circuit structure issues."""
    issues = []

    # Check for @circuit decorator usage
    if "@circuit" in code:
        # Ensure function definition follows
        lines = code.split("\n")
        for i, line in enumerate(lines):
            if "@circuit" in line:
                # Check if next non-empty line is a function definition
                for j in range(i + 1, len(lines)):
                    next_line = lines[j].strip()
                    if next_line:
                        if not next_line.startswith("def "):
                            issues.append(
                                "@circuit decorator not followed by function definition"
                            )
                        break

    # Check for basic component patterns
    if "Component(" in code:
        # Basic component syntax check (very lightweight)
        if code.count("Component(") != code.count('"'):
            # This is a heuristic - not perfect but catches common issues
            pass  # Skip for now to avoid false positives

    logger.debug(f"Structure check found {len(issues)} issues")
    return issues


def _check_runtime_execution(code: str, timeout_seconds: int) -> List[str]:
    """Test code execution in isolated environment."""
    issues = []

    # Create temporary file for execution
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        logger.debug(f"Executing code in {temp_file}")

        # Execute with timeout - try python3 first, then python
        python_cmd = "python3"  # Use python3 as default
        try:
            result = subprocess.run(
                [python_cmd, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except FileNotFoundError:
            # Fallback to python if python3 not found
            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

        if result.returncode != 0:
            # Extract meaningful error from stderr
            error_lines = result.stderr.strip().split("\n")
            # Get the last non-empty line (usually the actual error)
            meaningful_error = next(
                (line for line in reversed(error_lines) if line.strip()),
                "Unknown error",
            )
            issues.append(f"Runtime error: {meaningful_error}")

        logger.debug(f"Execution completed with return code {result.returncode}")

    except subprocess.TimeoutExpired:
        issues.append(f"Code execution timed out (>{timeout_seconds}s)")
        logger.warning(f"Execution timeout after {timeout_seconds}s")
    except Exception as e:
        issues.append(f"Execution failed: {str(e)}")
        logger.error(f"Execution exception: {e}")
    finally:
        # Clean up temporary file
        try:
            if "temp_file" in locals():
                os.unlink(temp_file)
        except Exception as e:
            logger.warning(f"Failed to clean up temp file: {e}")

    return issues


def _apply_basic_fixes(code: str, issues: List[str]) -> str:
    """Apply basic automatic fixes to common issues."""
    fixed_code = code

    # Fix missing circuit_synth import - add at the beginning
    if any("Missing circuit_synth framework import" in issue for issue in issues):
        if (
            "from circuit_synth import" not in fixed_code
            and "import circuit_synth" not in fixed_code
        ):
            fixed_code = (
                "from circuit_synth import Component, Net, circuit\n\n" + fixed_code
            )
            logger.debug("Applied fix: Added circuit_synth import")

    # Fix specific missing imports by ensuring they are in the import line
    imports_to_add = []
    if any("Component class used but not imported" in issue for issue in issues):
        imports_to_add.append("Component")
    if any("Net class used but not imported" in issue for issue in issues):
        imports_to_add.append("Net")
    if any("@circuit decorator used but not imported" in issue for issue in issues):
        imports_to_add.append("circuit")

    if imports_to_add:
        # Check if there's already a circuit_synth import line to extend
        lines = fixed_code.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("from circuit_synth import"):
                # Extend existing import
                existing_imports = line.split("import")[1].strip()
                # Avoid duplicates
                current_imports = [imp.strip() for imp in existing_imports.split(",")]
                for imp in imports_to_add:
                    if imp not in current_imports:
                        current_imports.append(imp)
                lines[i] = f"from circuit_synth import {', '.join(current_imports)}"
                fixed_code = "\n".join(lines)
                logger.debug(f"Applied fix: Extended imports with {imports_to_add}")
                break
        else:
            # No existing import found, add new one
            if imports_to_add:
                import_line = f"from circuit_synth import {', '.join(imports_to_add)}\n"
                fixed_code = import_line + "\n" + fixed_code
                logger.debug(
                    f"Applied fix: Added new import line with {imports_to_add}"
                )

    return fixed_code


# Context provision function
def get_circuit_design_context(circuit_type: str = "general") -> str:
    """
    Get comprehensive circuit design context for Claude Code.

    This function provides all the context Claude needs in a single call,
    avoiding multiple document reads and tool calls.

    Args:
        circuit_type: Type of circuit context needed
                     (general, power, microcontroller, analog, digital)

    Returns:
        Comprehensive context string with examples, patterns, and best practices

    Example:
        >>> context = get_circuit_design_context("esp32")
        >>> # Use context in Claude prompt for better generation
    """

    circuit_type = circuit_type.lower()
    logger.info(f"Generating context for circuit type: {circuit_type}")

    # Base context that applies to all circuits
    context = f"""# Circuit Design Context for {circuit_type.upper()}

## Essential Framework Usage
```python
from circuit_synth import Component, Net, circuit

@circuit
def my_circuit():
    # Define power nets first
    VCC_3V3 = Net("VCC_3V3")
    VCC_5V = Net("VCC_5V") 
    GND = Net("GND")
    
    # Create components
    component = Component("Library:SymbolName", "RefPrefix")
    
    # Make connections
    VCC_3V3 += component["VCC_PIN"]
    GND += component["GND_PIN"]
```

## Component Search Integration
- Use `/find-symbol <name>` to search KiCad symbols
- Use `/find-footprint <name>` to search KiCad footprints  
- Use `component-guru` agent for JLCPCB availability
- Use `stm32-mcu-finder` agent for STM32 peripherals

## Standard Power Supply Patterns
- **3.3V Linear Regulator**: AMS1117-3.3 with 10µF input, 22µF output caps
- **5V USB Power**: USB_C_Receptacle_USB2.0 with TVS diode protection
- **Decoupling**: 100nF ceramic caps near all ICs

## Common Net Names
- Power: VCC_3V3, VCC_5V, VCC_12V
- Ground: GND (always)
- USB: USB_DP, USB_DM, USB_VBUS
- Crystal: XTAL1, XTAL2

## Best Practices
1. Always define power nets first
2. Use descriptive component references (U1, R1, C1, etc.)
3. Group related connections together
4. Add decoupling capacitors for all ICs
5. Verify component availability with JLCPCB tools
"""

    # Add specific context based on circuit type
    if any(keyword in circuit_type for keyword in ["power", "regulator", "supply"]):
        context += """
## Power Supply Design Specifics
```python
# Linear regulator example
regulator = Component("Regulator_Linear:AMS1117-3.3", "U")
cap_in = Component("Device:C", "C", value="10uF")
cap_out = Component("Device:C", "C", value="22uF")

VCC_5V += regulator["VI"], cap_in[1]
VCC_3V3 += regulator["VO"], cap_out[1] 
GND += regulator["GND"], cap_in[2], cap_out[2]
```

### Power Design Guidelines
- Linear regulators: Use for low noise, <1A loads
- Switching regulators: Use for efficiency, >1A loads
- Always add input/output filtering capacitors
- Include power indicator LEDs
- Add fuse/polyfuse protection for safety
"""

    if any(
        keyword in circuit_type
        for keyword in ["stm32", "mcu", "microcontroller", "esp32"]
    ):
        context += """
## Microcontroller Design Specifics
```python
# STM32 example with crystal and decoupling
mcu = Component("MCU_ST_STM32F4:STM32F407VETx", "U")
crystal = Component("Device:Crystal", "Y", value="8MHz")
cap1 = Component("Device:C", "C", value="22pF")
cap2 = Component("Device:C", "C", value="22pF")

# Crystal connections
crystal[1] += mcu["OSC_IN"], cap1[1]
crystal[2] += mcu["OSC_OUT"], cap2[1]
GND += cap1[2], cap2[2]

# Power and decoupling
VCC_3V3 += mcu["VDD"]
GND += mcu["VSS"]
```

### MCU Design Guidelines  
- Crystal: Usually 8MHz or 25MHz for STM32
- Decoupling: 100nF ceramic cap per VDD pin
- Boot pins: Configure for normal operation
- Debug: Include SWD connector (SWDIO, SWCLK)
- Reset: Pull-up resistor + reset button
"""

    if any(keyword in circuit_type for keyword in ["usb", "connector", "interface"]):
        context += """
## USB Interface Design Specifics
```python
# USB-C connector with protection
usb_conn = Component("Connector:USB_C_Receptacle_USB2.0", "J")
tvs_diode = Component("Device:D_TVS", "D")
fuse = Component("Device:Polyfuse", "F", value="500mA")

# Power path with protection
fuse[1] += usb_conn["VBUS"]
VCC_5V += fuse[2]
tvs_diode[1] += VCC_5V
GND += usb_conn["GND"], tvs_diode[2]

# Data lines (if needed)
USB_DP += usb_conn["DP"]
USB_DM += usb_conn["DM"]
```

### USB Design Guidelines
- Always add TVS diode protection on VBUS
- Include polyfuse for overcurrent protection  
- Shield connection to GND through ferrite bead
- USB 2.0 data lines need 90Ω differential impedance
"""

    if any(keyword in circuit_type for keyword in ["analog", "amplifier", "sensor"]):
        context += """
## Analog Circuit Design Specifics
```python
# Op-amp circuit example
opamp = Component("Amplifier_Operational:LM358", "U")
r_feedback = Component("Device:R", "R", value="10k")
r_input = Component("Device:R", "R", value="1k")

# Non-inverting amplifier
signal_in += r_input[1]
r_input[2] += opamp["+"]
opamp["-"] += r_feedback[2]
r_feedback[1] += opamp["OUT"]
```

### Analog Design Guidelines
- Power supply decoupling critical for low noise
- Use precision resistors for gain setting
- Consider temperature effects and drift
- Add anti-aliasing filters for ADC inputs
- Ground plane important for noise reduction
"""

    # Add manufacturing and component availability info
    context += """
## Manufacturing Integration (JLCPCB)
- Check component availability with `component-guru` agent
- Prefer JLCPCB basic parts for cost efficiency
- Extended parts available but cost more
- Consider assembly constraints (component size, orientation)

## Component Search Commands
- `/find-symbol STM32F4` - Search for STM32F4 symbols
- `/find-footprint LQFP` - Search for LQFP footprints
- `/find-mcu 3 spi 2 uart` - Find STM32 with specific peripherals

## Debugging Tips
- Use `validate_and_improve_circuit()` for quick validation
- Check component availability before finalizing design
- Verify pin assignments match datasheet
- Test with simple circuits first, then add complexity
"""

    logger.debug(f"Generated {len(context)} character context")
    return context
