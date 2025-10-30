#!/usr/bin/env python3
"""
Automated documentation alignment validator.

Usage:
    python tools/documentation/validate_docs.py

Returns:
    Exit code 0: All docs aligned
    Exit code 1: Alignment issues found
"""

import sys
from pathlib import Path
import re


class DocValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.root = Path(__file__).parent.parent.parent

    def check_installation_consistency(self):
        """Verify installation commands match across docs."""
        readme_path = self.root / "README.md"
        index_rst_path = self.root / "docs" / "index.rst"

        if not readme_path.exists():
            self.errors.append(f"README.md not found at {readme_path}")
            return

        readme = readme_path.read_text()

        # README must have both pip and uv
        has_pip_in_readme = "pip install circuit-synth" in readme
        has_uv_in_readme = "uv add circuit-synth" in readme

        if not (has_pip_in_readme and has_uv_in_readme):
            self.errors.append(
                "README.md missing complete installation instructions. "
                "Must include both 'pip install circuit-synth' AND 'uv add circuit-synth'"
            )

        # docs/index.rst should match
        if index_rst_path.exists():
            index_rst = index_rst_path.read_text()
            if has_pip_in_readme and "pip install circuit-synth" not in index_rst:
                self.warnings.append(
                    "docs/index.rst missing 'pip install circuit-synth' "
                    "(present in README.md)"
                )
            if has_uv_in_readme and "uv add circuit-synth" not in index_rst:
                self.warnings.append(
                    "docs/index.rst missing 'uv add circuit-synth' "
                    "(present in README.md)"
                )

    def check_bad_paths(self):
        """Check for known incorrect file paths."""
        readme_path = self.root / "README.md"
        if not readme_path.exists():
            return

        readme = readme_path.read_text()

        bad_paths = [
            ("example_project/circuit-synth/main.py",
             "Wrong path after cs-new-project. Should be just 'python main.py' after cd to project"),
            ("circuit-synth/circuit-synth/main.py",
             "Wrong nested path. Should be 'cd my_project' then 'python main.py'"),
        ]

        for bad_path, explanation in bad_paths:
            if bad_path in readme:
                line_num = None
                for i, line in enumerate(readme.split('\n'), 1):
                    if bad_path in line:
                        line_num = i
                        break
                self.errors.append(
                    f"README.md:{line_num} contains bad path '{bad_path}'. "
                    f"{explanation}"
                )

    def check_correct_workflow(self):
        """Verify correct workflow patterns are documented."""
        readme_path = self.root / "README.md"
        if not readme_path.exists():
            return

        readme = readme_path.read_text()

        # Check for correct cs-new-project workflow
        # Should be: cs-new-project PROJECT_NAME, then cd PROJECT_NAME, then python main.py
        correct_workflow_pattern = r"cs-new-project\s+\w+.*?cd\s+\w+.*?python\s+main\.py"

        if not re.search(correct_workflow_pattern, readme, re.DOTALL | re.MULTILINE):
            self.warnings.append(
                "README.md may be missing clear cs-new-project workflow: "
                "cs-new-project NAME → cd NAME → python main.py"
            )

    def check_pyproject_metadata(self):
        """Verify pyproject.toml has correct metadata."""
        pyproject_path = self.root / "pyproject.toml"
        if not pyproject_path.exists():
            self.errors.append("pyproject.toml not found!")
            return

        pyproject = pyproject_path.read_text()

        # Must use README.md as readme
        if 'readme = "README.md"' not in pyproject:
            self.errors.append(
                "pyproject.toml must have 'readme = \"README.md\"' "
                "to use README as PyPI long_description"
            )

        # Check required URLs
        required_urls = [
            ("Homepage", "https://github.com/circuit-synth/circuit-synth"),
            ("Documentation", "circuit-synth.readthedocs.io"),
            ("Repository", "https://github.com/circuit-synth/circuit-synth"),
            ("Issues", "https://github.com/circuit-synth/circuit-synth/issues"),
        ]

        for url_name, expected_pattern in required_urls:
            if url_name not in pyproject:
                self.warnings.append(
                    f"pyproject.toml missing [project.urls] entry: {url_name}"
                )
            elif expected_pattern not in pyproject:
                self.warnings.append(
                    f"pyproject.toml URL '{url_name}' may have wrong value "
                    f"(expected to contain: {expected_pattern})"
                )

    def check_code_examples_syntax(self):
        """Basic syntax check for Python code blocks in README."""
        readme_path = self.root / "README.md"
        if not readme_path.exists():
            return

        readme = readme_path.read_text()

        # Extract Python code blocks
        code_blocks = re.findall(r'```python\n(.*?)```', readme, re.DOTALL)

        for i, code_block in enumerate(code_blocks, 1):
            # Skip incomplete/example-only blocks
            if '...' in code_block or '# ...' in code_block:
                continue

            # Try to compile (syntax check only, don't execute)
            try:
                compile(code_block, f'<README.md code block {i}>', 'exec')
            except SyntaxError as e:
                self.warnings.append(
                    f"README.md code block {i} has syntax error: {e.msg} at line {e.lineno}"
                )

    def run_all_checks(self):
        """Run all validation checks."""
        print("🔍 Running documentation validation...")
        print()

        self.check_installation_consistency()
        self.check_bad_paths()
        self.check_correct_workflow()
        self.check_pyproject_metadata()
        self.check_code_examples_syntax()

        # Report results
        if self.errors:
            print("❌ ERRORS FOUND:")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ All documentation validation checks passed!")
            return 0
        elif self.errors:
            print(f"❌ Found {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
            print("Fix errors before release!")
            return 1
        else:
            print(f"⚠️  Found {len(self.warnings)} warning(s) (no blocking errors)")
            return 0


if __name__ == "__main__":
    validator = DocValidator()
    sys.exit(validator.run_all_checks())
