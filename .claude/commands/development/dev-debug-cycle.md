---
allowed-tools: Bash(uv*), Bash(python*), Read, Write, Edit, MultiEdit, Diff, Grep, Glob
description: Systematic debugging with tight feedback loops for circuit-synth issues
---

# Debug Cycle Command

**Purpose:** Systematic debugging command that creates a tight feedback loop for troubleshooting circuit-synth issues by following a disciplined cycle of: test → compare → enhance logging → fix → repeat.

## Usage
```bash
/dev-debug-cycle [test_script] [reference_path] [compare_target]
```

## Arguments
- `test_script` - Path to the test script that reproduces the issue (default: ask user)
- `reference_path` - Path to known-good reference files/output (default: ask user)  
- `compare_target` - What to compare (files/logs/data) (default: ask user)

## User Setup Requirements

Before running this command, provide:

1. **Test Script**: A minimal test script that reproduces the issue
   - Should be focused on the specific problem
   - Should generate output that's easy to compare
   - Example: Single component creation, simple circuit generation

2. **Reference Output**: Known-good reference files/output to compare against
   - Should match the expected output of the test script
   - Should be in a format that's easy to diff/compare
   - Example: Working KiCad files, expected log output, expected data structures

3. **Success Criteria**: Clear definition of what "fixed" means
   - Specific files that should match
   - Expected behavior or output
   - Validation checks to perform

## Implementation

### Phase 1: Setup and Validation
```bash
echo "🔧 DEBUG CYCLE - Systematic Issue Resolution"
echo "==========================================="

# Get user input if not provided
if [[ -z "$1" ]]; then
    echo "❓ Please provide:"
    echo "  1. Test script path:"
    read -r test_script
    echo "  2. Reference output path:"
    read -r reference_path
    echo "  3. What to compare (files/logs/output):"
    read -r compare_target
else
    test_script="$1"
    reference_path="$2"
    compare_target="$3"
fi

# Validate inputs
echo "📋 Validating setup..."
if [[ ! -f "$test_script" ]]; then
    echo "❌ Test script not found: $test_script"
    exit 1
fi

if [[ ! -e "$reference_path" ]]; then
    echo "❌ Reference path not found: $reference_path"
    exit 1
fi

echo "✅ Setup validated"
echo "  Test script: $test_script"
echo "  Reference: $reference_path"  
echo "  Compare: $compare_target"
echo ""
```

### Phase 2: Debug Cycle Implementation

The debug cycle will be implemented by Claude through these steps:

#### Cycle Step 1: Run Test
- Execute the test script using `uv run python "$test_script"`
- Capture output and generated files
- Note any errors or unexpected behavior
- Report execution status

#### Cycle Step 2: Compare Output
- Compare generated output to reference using `diff` or file comparison
- Identify specific discrepancies in files, logs, or data structures
- Document differences clearly with line numbers and content
- Categorize differences (critical, cosmetic, missing)

#### Cycle Step 3: Analyze Differences
- Trace differences back to root causes in the codebase
- Identify which code modules are responsible for discrepancies
- Determine if the issue is in data flow, formatting, or logic
- Plan targeted fixes based on analysis

#### Cycle Step 4: Enhance Logging
- Add debug logging at key decision points
- Comment out existing logs that aren't relevant to this issue
- Focus logging on the specific data flow causing problems
- Ensure logging shows data transformations clearly

#### Cycle Step 5: Implement Fixes
- Make targeted code changes based on analysis
- Implement fixes for root causes, not just symptoms
- Ensure changes don't break other functionality
- Update related code if needed for consistency

#### Cycle Step 6: Verify and Iterate
- Re-run the test script to verify fixes
- Compare output again to check if differences are resolved
- If issues remain, start next cycle with enhanced understanding
- Continue until output matches reference or user confirms resolution

### Phase 3: Success Validation
```bash
echo "🎯 Final Validation"
echo "=================="

# Run final test
echo "🧪 Running final test..."
uv run python "$test_script" || {
    echo "❌ Final test failed"
    exit 1
}

# Compare to reference
echo "📊 Comparing to reference..."
if [[ "$compare_target" == "files" ]]; then
    # File comparison logic
    if diff -r generated_output/ "$reference_path" >/dev/null 2>&1; then
        echo "✅ Generated files match reference"
    else
        echo "⚠️  Some differences remain:"
        diff -r generated_output/ "$reference_path" | head -20
    fi
elif [[ "$compare_target" == "logs" ]]; then
    # Log comparison logic
    echo "📝 Log comparison (manual review required)"
elif [[ "$compare_target" == "output" ]]; then
    # Output comparison logic
    echo "📤 Output comparison completed"
fi

echo ""
echo "🎉 Debug cycle completed"
echo "User should verify the issue is resolved"
```

## Expected Workflow

1. **User provides setup**: Test script, reference, and success criteria
2. **Claude runs cycle**: Test → Compare → Analyze → Log → Fix → Repeat
3. **Progress tracking**: Each cycle reports findings and changes made
4. **Convergence**: Cycles continue until output matches reference
5. **Validation**: Final test confirms issue resolution

## Example Usage

```bash
# Full debug cycle with arguments
/dev-debug-cycle test_resistor.py reference_output/ files

# Interactive mode (Claude asks for inputs)
/dev-debug-cycle

# With specific comparison target
/dev-debug-cycle my_test.py good_output/ logs
```

## Integration with Development

This command works with:
- **Bug reproduction**: Minimal test cases that isolate issues
- **Regression testing**: Compare against known-good outputs  
- **Code quality**: Systematic approach to fixing complex issues
- **Documentation**: Auto-generates debugging traces for future reference

## Success Criteria

**Cycle Success:**
- Generated output matches reference output exactly
- Test script runs without errors
- All specified validation checks pass
- User confirms the original issue is resolved

**Process Success:**
- Systematic approach prevents missing edge cases
- Each cycle makes measurable progress
- Root causes are identified and fixed (not just symptoms)
- Solutions are robust and don't introduce new issues

---

**This systematic debug cycle ensures thorough issue resolution through disciplined iterative improvement.**