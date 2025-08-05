#!/usr/bin/env python3
"""
Dead Code Analysis Script for Claude Commands

This script implements the /dead-code-analysis command functionality.
It instruments Python functions with debug logging, runs a target script,
and analyzes the results to identify dead code.
"""

import argparse
import ast
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple


class FunctionInstrumenter:
    """Instruments Python functions with debug logging statements."""
    
    def __init__(self, src_dir: Path):
        self.src_dir = src_dir
        self.instrumented_files = []
        self.total_functions = 0
        
    def instrument_all_files(self) -> Dict[str, int]:
        """Instrument all Python files in the source directory."""
        print(f"🔍 Scanning {self.src_dir} for Python files...")
        
        results = {}
        python_files = list(self.src_dir.rglob("*.py"))
        
        print(f"📁 Found {len(python_files)} Python files")
        
        for py_file in python_files:
            if py_file.name == "__pycache__":
                continue
                
            try:
                count = self._instrument_file(py_file)
                if count > 0:
                    results[str(py_file.relative_to(self.src_dir))] = count
                    self.total_functions += count
                    self.instrumented_files.append(py_file)
            except Exception as e:
                print(f"⚠️  Skipped {py_file}: {e}")
                
        print(f"✅ Instrumented {len(self.instrumented_files)} files with {self.total_functions} functions")
        return results
        
    def _instrument_file(self, file_path: Path) -> int:
        """Instrument a single Python file with debug logging."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse the AST to find function definitions
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return 0
            
        functions = self._find_functions(tree)
        if not functions:
            return 0
            
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Add logging import if needed
        lines = content.splitlines()
        if not any('import logging' in line for line in lines[:20]):
            # Find a good place to insert the import
            insert_line = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    # Skip docstrings
                    in_docstring = True
                    quote_type = '"""' if '"""' in line else "'''"
                    if line.count(quote_type) >= 2:
                        in_docstring = False
                    for j in range(i + 1, len(lines)):
                        if in_docstring and quote_type in lines[j]:
                            insert_line = j + 1
                            break
                    break
                elif line.strip() and not line.startswith('#'):
                    insert_line = i
                    break
                    
            lines.insert(insert_line, 'import logging')
            
        # Instrument functions
        instrumented_count = 0
        for func_name, line_num in reversed(functions):  # Reverse to maintain line numbers
            # Insert logging statement at the beginning of function
            func_line_idx = line_num - 1  # Convert to 0-based index
            
            # Find the function definition line and its indentation
            while func_line_idx < len(lines) and not lines[func_line_idx].strip().startswith('def '):
                func_line_idx += 1
                
            if func_line_idx >= len(lines):
                continue
                
            # Find the end of the function signature (handle multi-line signatures)
            signature_end = func_line_idx
            paren_count = 0
            in_signature = False
            
            for i in range(func_line_idx, len(lines)):
                line = lines[i]
                for char in line:
                    if char == '(':
                        paren_count += 1
                        in_signature = True
                    elif char == ')':
                        paren_count -= 1
                        if paren_count == 0 and in_signature:
                            signature_end = i
                            break
                if paren_count == 0 and in_signature:
                    break
                    
            # Look for the colon and first non-empty line after it
            colon_line = signature_end
            for i in range(signature_end, len(lines)):
                if ':' in lines[i]:
                    colon_line = i
                    break
                    
            # Find first non-empty line in function body
            body_start = colon_line + 1
            while body_start < len(lines) and not lines[body_start].strip():
                body_start += 1
                
            if body_start >= len(lines):
                continue
                
            # Skip if already instrumented
            if 'CALLED:' in lines[body_start]:
                continue
                
            # Get indentation of the function body
            indent = len(lines[body_start]) - len(lines[body_start].lstrip())
            
            # Create logging statement
            relative_path = file_path.relative_to(self.src_dir.parent)
            log_statement = f"{' ' * indent}logging.debug(f'CALLED: {func_name} in {relative_path}')"
            
            # Insert logging statement
            lines.insert(body_start, log_statement)
            instrumented_count += 1
            
        # Write instrumented file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
            
        return instrumented_count
        
    def _find_functions(self, tree: ast.AST) -> List[Tuple[str, int]]:
        """Find all function definitions in the AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip dunder methods for cleaner output
                if not (node.name.startswith('__') and node.name.endswith('__')):
                    functions.append((node.name, node.lineno))
                    
        return functions
        
    def restore_backups(self):
        """Restore all backup files."""
        print("🔄 Restoring backup files...")
        restored = 0
        
        for py_file in self.instrumented_files:
            backup_path = py_file.with_suffix(py_file.suffix + '.backup')
            if backup_path.exists():
                backup_path.rename(py_file)
                restored += 1
                
        print(f"✅ Restored {restored} files from backups")


class DeadCodeAnalyzer:
    """Analyzes function call logs to identify dead code."""
    
    def __init__(self, src_dir: Path):
        self.src_dir = src_dir
        
    def analyze_calls(self, log_file: Path, instrumented_functions: Dict[str, int]) -> Dict:
        """Analyze function calls and identify dead code."""
        print(f"📊 Analyzing function calls from {log_file}...")
        
        # Extract called functions from log
        called_functions = self._extract_called_functions(log_file)
        
        # Compare with instrumented functions
        all_functions = set()
        for file_path, count in instrumented_functions.items():
            # We'd need to re-parse to get exact function names, but for now
            # we'll use the simpler approach from the log analysis
            pass
            
        # Generate statistics
        total_instrumented = sum(instrumented_functions.values())
        total_called = len(called_functions)
        dead_functions = total_instrumented - total_called
        
        return {
            'total_instrumented': total_instrumented,
            'total_called': total_called,
            'dead_functions': dead_functions,
            'utilization': (total_called / total_instrumented) * 100 if total_instrumented > 0 else 0,
            'called_functions': called_functions,
            'instrumented_files': instrumented_functions
        }
        
    def _extract_called_functions(self, log_file: Path) -> Set[str]:
        """Extract unique called functions from the log file."""
        called_functions = set()
        
        if not log_file.exists():
            return called_functions
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'CALLED:' in line:
                        # Extract function name and file path
                        match = re.search(r'CALLED: (.+) in (.+)', line)
                        if match:
                            func_name = match.group(1)
                            file_path = match.group(2)
                            called_functions.add(f"{func_name} in {file_path}")
        except Exception as e:
            print(f"⚠️  Error reading log file: {e}")
            
        return called_functions
        
    def generate_report(self, analysis: Dict, output_file: Path):
        """Generate a comprehensive dead code analysis report."""
        print(f"📝 Generating report: {output_file}")
        
        report_lines = [
            "# Dead Code Analysis Report",
            "",
            "## Executive Summary",
            "",
            f"- **Total Functions Analyzed**: {analysis['total_instrumented']:,}",
            f"- **Functions Actually Called**: {analysis['total_called']:,}",
            f"- **Potentially Dead Functions**: {analysis['dead_functions']:,}",
            f"- **Code Utilization**: {analysis['utilization']:.1f}%",
            "",
            f"⚠️  **{analysis['dead_functions']:,} functions ({100-analysis['utilization']:.1f}%) appear to be unused**",
            "",
            "## Analysis Details",
            "",
            "This analysis was performed by:",
            "1. Instrumenting all Python functions with debug logging",
            "2. Running the target script to capture function calls",
            "3. Comparing instrumented vs called functions",
            "",
            "## Files Analyzed",
            "",
        ]
        
        # Add file statistics
        for file_path, count in sorted(analysis['instrumented_files'].items()):
            report_lines.append(f"- `{file_path}`: {count} functions instrumented")
            
        report_lines.extend([
            "",
            "## Called Functions",
            "",
            "The following functions were called during execution:",
            "",
        ])
        
        # Add called functions list
        for func_call in sorted(analysis['called_functions']):
            report_lines.append(f"- {func_call}")
            
        report_lines.extend([
            "",
            "## Recommendations",
            "",
            "1. **Review functions not called** during this analysis",
            "2. **Consider additional test scenarios** to ensure comprehensive coverage",
            "3. **Search codebase** for dynamic calls or reflection usage",
            "4. **Check git history** for external usage before removing code",
            "5. **Remove dead code gradually** with proper testing",
            "",
            "## Notes",
            "",
            "- This analysis is based on a single execution path",
            "- Some functions may be used in other contexts not covered by the test",
            "- Consider running multiple test scenarios for comprehensive analysis",
            "- Review functions used only in error handling or edge cases",
        ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
            
        print(f"✅ Report generated: {output_file}")


def main():
    """Main entry point for dead code analysis."""
    parser = argparse.ArgumentParser(description="Dead Code Analysis Tool")
    parser.add_argument(
        "target_script", 
        nargs='?', 
        default="main.py",
        help="Target script to run for analysis (default: main.py)"
    )
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=Path("src/circuit_synth"),
        help="Source directory to analyze (default: src/circuit_synth)"
    )
    parser.add_argument(
        "--restore-backups",
        action="store_true",
        help="Restore backup files and exit"
    )
    
    args = parser.parse_args()
    
    if not args.src_dir.exists():
        print(f"❌ Source directory not found: {args.src_dir}")
        sys.exit(1)
        
    instrumenter = FunctionInstrumenter(args.src_dir)
    
    if args.restore_backups:
        instrumenter.restore_backups()
        return
        
    try:
        # Step 1: Instrument all functions
        print("🔧 Step 1: Instrumenting functions...")
        instrumented_functions = instrumenter.instrument_all_files()
        
        if not instrumented_functions:
            print("❌ No functions found to instrument")
            return
            
        # Step 2: Run target script with logging
        print(f"🏃 Step 2: Running {args.target_script}...")
        log_file = Path("function_calls.log")
        
        env = os.environ.copy()
        env['PYTHONPATH'] = str(args.src_dir.parent)
        
        cmd = [
            sys.executable, "-c", 
            f"import logging; logging.basicConfig(level=logging.DEBUG, format='%(message)s'); exec(open('{args.target_script}').read())"
        ]
        
        with open(log_file, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=Path.cwd()
            )
            
        if result.returncode != 0:
            print(f"⚠️  Target script completed with exit code {result.returncode}")
        else:
            print("✅ Target script completed successfully")
            
        # Step 3: Analyze results
        print("📊 Step 3: Analyzing results...")
        analyzer = DeadCodeAnalyzer(args.src_dir)
        analysis = analyzer.analyze_calls(log_file, instrumented_functions)
        
        # Step 4: Generate report
        print("📝 Step 4: Generating report...")
        report_file = Path("Dead_Code_Analysis_Report.md")
        analyzer.generate_report(analysis, report_file)
        
        # Generate unique functions list for reference
        unique_file = Path("unique_function_calls.txt")
        with open(unique_file, 'w') as f:
            for func_call in sorted(analysis['called_functions']):
                f.write(f"{func_call}\n")
                
        print(f"✅ Analysis complete!")
        print(f"📊 Results: {analysis['total_called']}/{analysis['total_instrumented']} functions called ({analysis['utilization']:.1f}% utilization)")
        print(f"📁 Files: {report_file}, {unique_file}, {log_file}")
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise
    finally:
        # Always offer to restore backups
        if instrumenter.instrumented_files:
            try:
                response = input("\n🔄 Restore backup files? (y/N): ").strip().lower()
                if response in ('y', 'yes'):
                    instrumenter.restore_backups()
            except KeyboardInterrupt:
                print("\n⏭️  Skipping backup restoration")


if __name__ == "__main__":
    main()