# Dead Code Analysis Command

## Usage
```
/dead-code-analysis [target-script]
```

## Description
Performs comprehensive dead code analysis by:
1. Adding debug logging to every function in the codebase
2. Running a target script to capture which functions are actually called
3. Comparing instrumented vs called functions to identify dead code
4. Generating a detailed markdown report with cleanup recommendations

## Parameters
- `target-script` (optional): Path to script to run for function call analysis. Defaults to `main.py` if found in current directory.

## Output Files
- `function_calls.log`: Raw debug output from script execution
- `unique_function_calls.txt`: List of unique functions that were called
- `Dead_Code_Analysis_Report.md`: Comprehensive analysis report
- `*.backup`: Backup files for all instrumented source files

## Examples
```bash
# Analyze dead code using main.py
/dead-code-analysis

# Analyze using a specific test script
/dead-code-analysis test_suite.py

# Analyze using a custom script path
/dead-code-analysis examples/test_all_circuits.py
```

## Implementation
The command performs the following automated steps:

### 1. Function Instrumentation
- Scans all Python files in `src/circuit_synth/`
- Adds `logging.debug(f"CALLED: {function_name} in {file_path}")` to the start of every function
- Creates backup files (`.backup`) before modification
- Adds necessary import statements if missing
- Preserves existing function logic and formatting

### 2. Script Execution
- Runs the target script with debug logging enabled
- Captures all function calls to `function_calls.log`
- Handles large log files efficiently

### 3. Analysis & Reporting
- Extracts unique function calls from execution log
- Compares against all instrumented functions
- Groups suspected dead code by module/directory
- Generates comprehensive markdown report with:
  - Executive summary with statistics
  - Dead code grouped by impact
  - Removal recommendations
  - Safety considerations

## Expected Results
Based on previous analysis, expect to find:
- **~90%** of functions are potentially unused
- **270+** complete modules with no called functions
- Major dead code categories:
  - Duplicate PCB implementations
  - Unused interface layers
  - Over-engineered abstractions
  - Legacy/experimental code

## Safety Notes
- Creates backup files before modifying source code
- Only adds logging statements, doesn't change logic
- Can be run multiple times safely
- Backups can be restored if needed:
  ```bash
  # Restore all backups
  find . -name "*.backup" | while read backup; do
    original="${backup%.backup}"
    mv "$backup" "$original"
  done
  ```

## Cleanup Workflow
After analysis:
1. Review the generated report
2. Start with highest-impact dead modules (most functions, zero usage)
3. Search git history for any external references
4. Remove dead code in phases with testing
5. Re-run analysis to track progress

## Command Implementation
This command is implemented via:
- **Main script**: `scripts/dead-code-analysis.py` - Python implementation with AST parsing
- **Shell wrapper**: `scripts/dead-code-analysis.sh` - Simple command-line interface

### Manual Usage
```bash
# From repository root
python scripts/dead-code-analysis.py [target-script]

# Or use the shell wrapper
./scripts/dead-code-analysis.sh [target-script]

# Restore backups if needed
python scripts/dead-code-analysis.py --restore-backups
```

The implementation preserves all existing functionality while adding comprehensive function call tracking for dead code identification.