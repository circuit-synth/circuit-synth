#!/usr/bin/env python3
"""
Script to add logging statements to all functions in circuit-synth for dead code analysis.

This script automatically adds a logging statement to the beginning of every function
to track which functions are called during execution.
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Set


class FunctionLoggingTransformer(ast.NodeTransformer):
    """AST transformer to add logging statements to function definitions."""
    
    def __init__(self):
        self.modified = False
        self.functions_found = []
    
    def visit_FunctionDef(self, node):
        """Add logging statement to function definitions."""
        # Skip if already has logging
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Call) and
            isinstance(node.body[0].value.func, ast.Attribute) and
            getattr(node.body[0].value.func.attr, '', '') == 'info'):
            return node
            
        # Create logging statement
        log_stmt = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='__dead_code_logger', ctx=ast.Load()),
                    attr='info',
                    ctx=ast.Load()
                ),
                args=[ast.Constant(value=f"FUNCTION_CALLED: {node.name}")],
                keywords=[]
            )
        )
        
        # Insert at beginning of function body
        node.body.insert(0, log_stmt)
        self.modified = True
        self.functions_found.append(node.name)
        
        # Continue processing nested functions
        self.generic_visit(node)
        return node
    
    def visit_AsyncFunctionDef(self, node):
        """Add logging statement to async function definitions."""
        return self.visit_FunctionDef(node)


def add_logging_import(content: str) -> str:
    """Add the logging import at the top of the file if not present."""
    lines = content.split('\n')
    
    # Check if already has the logging setup
    if any('__dead_code_logger' in line for line in lines):
        return content
    
    # Find where to insert the import (after existing imports or docstring)
    insert_idx = 0
    in_docstring = False
    docstring_quotes = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Handle docstrings
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            docstring_quotes = stripped[:3]
            if stripped.count(docstring_quotes) == 1:  # Opening quote only
                in_docstring = True
            continue
        elif in_docstring and docstring_quotes in stripped:
            in_docstring = False
            insert_idx = i + 1
            continue
        elif in_docstring:
            continue
            
        # Skip comments and empty lines at top
        if not stripped or stripped.startswith('#'):
            continue
            
        # If this is an import line, keep looking
        if stripped.startswith(('import ', 'from ')):
            insert_idx = i + 1
            continue
            
        # Found first non-import line
        break
    
    # Add the logging setup
    logging_setup = [
        "# Dead code analysis logging",
        "import logging as __logging_module",
        "__dead_code_logger = __logging_module.getLogger('dead_code_analysis')",
        ""
    ]
    
    lines[insert_idx:insert_idx] = logging_setup
    return '\n'.join(lines)


def process_python_file(file_path: Path) -> tuple[bool, List[str]]:
    """Process a single Python file to add logging statements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the file
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return False, []
        
        # Transform the AST
        transformer = FunctionLoggingTransformer()
        new_tree = transformer.visit(tree)
        
        if not transformer.modified:
            return False, []
        
        # Convert back to code
        import astor
        new_content = astor.to_source(new_tree)
        
        # Add logging import
        new_content = add_logging_import(new_content)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Modified {file_path} - added logging to {len(transformer.functions_found)} functions")
        return True, transformer.functions_found
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, []


def main():
    """Main function to process all Python files in circuit-synth."""
    # Define the source directory
    source_dir = Path("src/circuit_synth")
    
    if not source_dir.exists():
        print(f"Source directory {source_dir} not found!")
        return
    
    # Find all Python files
    python_files = []
    for file_path in source_dir.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" in str(file_path) or "test_" in file_path.name:
            continue
        python_files.append(file_path)
    
    print(f"Found {len(python_files)} Python files to process")
    
    # Process each file
    total_functions = 0
    modified_files = 0
    
    for file_path in python_files:
        modified, functions = process_python_file(file_path)
        if modified:
            modified_files += 1
            total_functions += len(functions)
    
    print(f"\n✅ Complete!")
    print(f"Modified {modified_files} files")
    print(f"Added logging to {total_functions} functions")
    print(f"\nNow run: cd example_project/circuit-synth && python main.py > ../../function_usage.log 2>&1")


if __name__ == "__main__":
    main()