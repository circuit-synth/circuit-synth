#!/usr/bin/env python3
"""
Parse pytest results and create individual failure reports.

This script analyzes test results and creates a structured report with:
- Individual files for each failure type
- Categorization by test type (unit/integration/e2e)
- Severity classification
- Actionable recommendations
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, List, Set


@dataclass
class TestFailure:
    """Represents a single test failure"""
    test_name: str
    test_path: str
    test_category: str  # unit, integration, e2e, bidirectional, etc.
    failure_type: str  # FAILED, ERROR, XFAIL, SKIPPED
    error_type: str  # AssertionError, FileNotFoundError, etc.
    error_message: str
    full_output: str
    line_number: int = 0

    @property
    def severity(self) -> str:
        """Classify failure severity"""
        if self.failure_type == "ERROR":
            return "HIGH"
        elif self.failure_type == "FAILED":
            if "FileNotFoundError" in self.error_type:
                return "HIGH"
            elif "AttributeError" in self.error_type:
                return "HIGH"
            elif "TypeError" in self.error_type:
                return "HIGH"
            else:
                return "MEDIUM"
        elif self.failure_type == "XFAIL":
            return "LOW"
        elif self.failure_type == "SKIPPED":
            return "INFO"
        return "UNKNOWN"


class TestResultParser:
    """Parse pytest output and extract failure information"""

    def __init__(self, results_file: str):
        self.results_file = Path(results_file)
        self.failures: List[TestFailure] = []
        self.summary: Dict[str, int] = defaultdict(int)

    def parse(self):
        """Parse the test results file"""
        if not self.results_file.exists():
            print(f"Results file not found: {self.results_file}")
            return

        content = self.results_file.read_text()

        # Parse summary line
        summary_match = re.search(
            r'(\d+) failed,?\s*(\d+) passed,?\s*(\d+) skipped,?\s*(\d+) xfailed,?\s*(\d+) xpassed',
            content
        )
        if summary_match:
            self.summary = {
                'failed': int(summary_match.group(1)),
                'passed': int(summary_match.group(2)),
                'skipped': int(summary_match.group(3)),
                'xfailed': int(summary_match.group(4)),
                'xpassed': int(summary_match.group(5))
            }

        # Parse FAILED tests
        failed_pattern = r'FAILED (tests/[^\s]+) - (.+?)(?=\nFAILED|\nERROR|\nSKIPPED|\nXFAIL|\n=|$)'
        for match in re.finditer(failed_pattern, content, re.DOTALL):
            test_path = match.group(1)
            error_info = match.group(2).strip()

            # Extract error type and message
            error_match = re.match(r'(\w+Error|AssertionError): (.+)', error_info)
            if error_match:
                error_type = error_match.group(1)
                error_message = error_match.group(2)
            else:
                error_type = "Unknown"
                error_message = error_info[:200]

            failure = TestFailure(
                test_name=test_path.split('::')[-1] if '::' in test_path else test_path,
                test_path=test_path,
                test_category=self._categorize_test(test_path),
                failure_type="FAILED",
                error_type=error_type,
                error_message=error_message,
                full_output=error_info[:500]
            )
            self.failures.append(failure)

        # Parse ERROR tests
        error_pattern = r'ERROR (tests/[^\s]+) - (.+?)(?=\nFAILED|\nERROR|\nSKIPPED|\nXFAIL|\n=|$)'
        for match in re.finditer(error_pattern, content, re.DOTALL):
            test_path = match.group(1)
            error_info = match.group(2).strip()

            error_match = re.match(r'(\w+Error): (.+)', error_info)
            if error_match:
                error_type = error_match.group(1)
                error_message = error_match.group(2)
            else:
                error_type = "Unknown"
                error_message = error_info[:200]

            failure = TestFailure(
                test_name=test_path.split('::')[-1] if '::' in test_path else test_path,
                test_path=test_path,
                test_category=self._categorize_test(test_path),
                failure_type="ERROR",
                error_type=error_type,
                error_message=error_message,
                full_output=error_info[:500]
            )
            self.failures.append(failure)

    def _categorize_test(self, test_path: str) -> str:
        """Categorize test by directory"""
        if 'tests/unit/' in test_path:
            return 'unit'
        elif 'tests/integration/' in test_path:
            return 'integration'
        elif 'tests/e2e/' in test_path:
            return 'e2e'
        elif 'tests/bidirectional/' in test_path:
            return 'bidirectional'
        elif 'tests/pcb_generation/' in test_path:
            return 'pcb_generation'
        elif 'tests/kicad_to_python/' in test_path:
            return 'kicad_to_python'
        elif 'tests/test_bidirectional_automated/' in test_path:
            return 'bidirectional_automated'
        else:
            return 'other'

    def generate_reports(self, output_dir: Path):
        """Generate failure reports organized by category"""
        output_dir.mkdir(exist_ok=True)

        # Group failures by category
        by_category = defaultdict(list)
        by_error_type = defaultdict(list)
        by_severity = defaultdict(list)

        for failure in self.failures:
            by_category[failure.test_category].append(failure)
            by_error_type[failure.error_type].append(failure)
            by_severity[failure.severity].append(failure)

        # Generate summary report
        self._generate_summary(output_dir, by_category, by_error_type, by_severity)

        # Generate category reports
        for category, failures in by_category.items():
            self._generate_category_report(output_dir, category, failures)

        # Generate error type reports
        for error_type, failures in by_error_type.items():
            self._generate_error_type_report(output_dir, error_type, failures)

        # Generate individual failure files for unit tests
        unit_failures = by_category.get('unit', [])
        if unit_failures:
            self._generate_individual_reports(output_dir / 'unit_failures', unit_failures)

    def _generate_summary(self, output_dir, by_category, by_error_type, by_severity):
        """Generate overall summary report"""
        summary_path = output_dir / 'SUMMARY.md'

        with open(summary_path, 'w') as f:
            f.write("# Comprehensive Test Failure Analysis\n\n")
            f.write(f"**Total Tests:** {sum(self.summary.values())}\n\n")

            f.write("## Test Results Summary\n\n")
            for status, count in self.summary.items():
                f.write(f"- **{status.upper()}:** {count}\n")

            f.write("\n## Failures by Category\n\n")
            for category in sorted(by_category.keys()):
                count = len(by_category[category])
                f.write(f"- **{category}:** {count} failures\n")

            f.write("\n## Failures by Error Type\n\n")
            for error_type in sorted(by_error_type.keys(), key=lambda x: len(by_error_type[x]), reverse=True):
                count = len(by_error_type[error_type])
                f.write(f"- **{error_type}:** {count} occurrences\n")

            f.write("\n## Failures by Severity\n\n")
            for severity in ['HIGH', 'MEDIUM', 'LOW', 'INFO']:
                count = len(by_severity.get(severity, []))
                if count > 0:
                    f.write(f"- **{severity}:** {count} failures\n")

            f.write("\n## Priority Actions\n\n")
            f.write("### High Priority (API/Infrastructure Issues)\n\n")
            high_priority = by_severity.get('HIGH', [])
            for failure in high_priority[:10]:  # Top 10
                f.write(f"- `{failure.test_path}`\n")
                f.write(f"  - **Error:** {failure.error_type}: {failure.error_message[:100]}\n\n")

            f.write("\n### Unit Test Failures (Critical for CI/CD)\n\n")
            unit_failures = by_category.get('unit', [])
            f.write(f"**Total Unit Test Failures:** {len(unit_failures)}\n\n")
            f.write("Unit tests should have 100% pass rate for CI/CD.\n")
            f.write(f"See `unit_failures/` directory for detailed reports.\n\n")

    def _generate_category_report(self, output_dir, category, failures):
        """Generate report for a specific test category"""
        report_path = output_dir / f'{category}_failures.md'

        with open(report_path, 'w') as f:
            f.write(f"# {category.upper()} Test Failures\n\n")
            f.write(f"**Total Failures:** {len(failures)}\n\n")

            # Group by error type within category
            by_error = defaultdict(list)
            for failure in failures:
                by_error[failure.error_type].append(failure)

            for error_type, error_failures in sorted(by_error.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"## {error_type} ({len(error_failures)} occurrences)\n\n")
                for failure in error_failures:
                    f.write(f"### {failure.test_name}\n\n")
                    f.write(f"**Path:** `{failure.test_path}`\n\n")
                    f.write(f"**Severity:** {failure.severity}\n\n")
                    f.write(f"**Error:** {failure.error_message}\n\n")
                    f.write("```\n")
                    f.write(failure.full_output[:300])
                    f.write("\n```\n\n")
                    f.write("---\n\n")

    def _generate_error_type_report(self, output_dir, error_type, failures):
        """Generate report grouped by error type"""
        safe_name = error_type.replace(':', '_').replace(' ', '_')
        report_path = output_dir / f'error_{safe_name}.md'

        with open(report_path, 'w') as f:
            f.write(f"# {error_type} Failures\n\n")
            f.write(f"**Total Occurrences:** {len(failures)}\n\n")

            # Group by category
            by_cat = defaultdict(list)
            for failure in failures:
                by_cat[failure.test_category].append(failure)

            f.write("## Distribution by Category\n\n")
            for cat, cat_failures in sorted(by_cat.items()):
                f.write(f"- **{cat}:** {len(cat_failures)} tests\n")

            f.write("\n## All Failures\n\n")
            for failure in failures:
                f.write(f"- `{failure.test_path}`\n")
                f.write(f"  - {failure.error_message[:150]}\n\n")

    def _generate_individual_reports(self, output_dir, failures):
        """Generate individual report files for each failure"""
        output_dir.mkdir(exist_ok=True, parents=True)

        for i, failure in enumerate(failures, 1):
            safe_name = re.sub(r'[^\w\-_]', '_', failure.test_name)
            report_path = output_dir / f'{i:03d}_{safe_name}.md'

            with open(report_path, 'w') as f:
                f.write(f"# {failure.test_name}\n\n")
                f.write(f"**Category:** {failure.test_category}\n\n")
                f.write(f"**Path:** `{failure.test_path}`\n\n")
                f.write(f"**Severity:** {failure.severity}\n\n")
                f.write(f"**Error Type:** {failure.error_type}\n\n")
                f.write("## Error Message\n\n")
                f.write(f"```\n{failure.error_message}\n```\n\n")
                f.write("## Full Output\n\n")
                f.write(f"```\n{failure.full_output}\n```\n\n")
                f.write("## Recommended Actions\n\n")
                f.write(self._get_recommendations(failure))

    def _get_recommendations(self, failure: TestFailure) -> str:
        """Generate recommendations based on failure type"""
        if "FileNotFoundError" in failure.error_type:
            return """
- Check if test fixture is generating files correctly
- Verify path construction in test
- Check if cleanup is running prematurely
- Ensure test dependencies are met
"""
        elif "AttributeError" in failure.error_type:
            if "add_component" in failure.error_message:
                return """
- API change: kicad-sch-api may have changed
- Check kicad-sch-api version compatibility
- Update to use correct API method
- Check kicad-sch-api documentation
"""
            else:
                return """
- API mismatch detected
- Check object type expectations
- Verify API compatibility
- Update test to match current API
"""
        elif "TypeError" in failure.error_type:
            return """
- API signature changed
- Check method arguments
- Verify object instantiation
- Update to match current API
"""
        elif "AssertionError" in failure.error_type:
            return """
- Functional bug detected
- Verify expected behavior
- Check implementation
- May need code fix, not just test update
"""
        else:
            return """
- Investigate failure cause
- Check test assumptions
- Verify implementation
"""


def main():
    """Main entry point"""
    results_file = Path('test_results_full.txt')
    output_dir = Path('test_failure_reports')

    print("Parsing test results...")
    parser = TestResultParser(results_file)
    parser.parse()

    print(f"Found {len(parser.failures)} failures")
    print(f"\nGenerating reports in {output_dir}/...")

    parser.generate_reports(output_dir)

    print("\n✅ Reports generated successfully!")
    print(f"\nSummary: {output_dir}/SUMMARY.md")
    print(f"Category reports: {output_dir}/*_failures.md")
    print(f"Unit test details: {output_dir}/unit_failures/")


if __name__ == '__main__':
    main()
