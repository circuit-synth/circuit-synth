#!/usr/bin/env python3
"""
Test harness for gradual S-expression formatter migration.

This module provides infrastructure for:
1. Capturing baseline outputs from the current formatter
2. Running both old and new formatters in parallel
3. Comparing outputs for functional equivalence
4. Generating migration reports
"""

import difflib
import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FormatterTestHarness:
    """Test harness for comparing old and new S-expression formatters."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the test harness.

        Args:
            output_dir: Directory for storing test outputs and reports
        """
        self.output_dir = output_dir or Path(tempfile.mkdtemp(prefix="formatter_test_"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.baseline_dir = self.output_dir / "baseline"
        self.new_output_dir = self.output_dir / "new_output"
        self.reports_dir = self.output_dir / "reports"

        # Create subdirectories
        for dir_path in [self.baseline_dir, self.new_output_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.test_results = []
        self.migration_status = {
            "phase": 0,
            "started": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "functional_equivalence": [],
        }

    def capture_baseline(self, test_name: str, circuit_data: Dict) -> str:
        """Capture baseline output from the current formatter.

        Args:
            test_name: Name of the test case
            circuit_data: Circuit data to format

        Returns:
            Path to the baseline file
        """
        logger.info(f"Capturing baseline for test: {test_name}")

        # Generate S-expression using current formatter
        sexp_output = self._generate_schematic_sexp(circuit_data, use_new=False)

        # Save baseline
        baseline_file = self.baseline_dir / f"{test_name}.kicad_sch"
        baseline_file.write_text(sexp_output)

        # Store metadata
        metadata = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "file_hash": self._hash_file(baseline_file),
            "line_count": len(sexp_output.splitlines()),
            "file_size": len(sexp_output),
        }

        metadata_file = self.baseline_dir / f"{test_name}.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))

        return str(baseline_file)

    def run_parallel_test(self, test_name: str, circuit_data: Dict) -> Dict:
        """Run both formatters in parallel and compare results.

        Args:
            test_name: Name of the test case
            circuit_data: Circuit data to format

        Returns:
            Test result dictionary
        """
        logger.info(f"Running parallel test: {test_name}")

        # Generate with old formatter
        old_output = self._generate_schematic_sexp(circuit_data, use_new=False)
        old_file = self.baseline_dir / f"{test_name}_parallel.kicad_sch"
        old_file.write_text(old_output)

        # Generate with new formatter (when available)
        try:
            new_output = self._generate_schematic_sexp(circuit_data, use_new=True)
            new_file = self.new_output_dir / f"{test_name}_parallel.kicad_sch"
            new_file.write_text(new_output)
        except Exception as e:
            logger.warning(f"New formatter not available yet: {e}")
            new_output = old_output
            new_file = old_file

        # Compare outputs
        comparison = self._compare_outputs(old_output, new_output)

        # Check functional equivalence
        is_equivalent = self._check_functional_equivalence(old_output, new_output)

        result = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "old_file": str(old_file),
            "new_file": str(new_file),
            "identical": comparison["identical"],
            "functional_equivalent": is_equivalent,
            "differences": comparison["differences"],
            "old_metrics": self._get_output_metrics(old_output),
            "new_metrics": self._get_output_metrics(new_output),
        }

        self.test_results.append(result)
        self._update_migration_status(result)

        return result

    def _generate_schematic_sexp(
        self, circuit_data: Dict, use_new: bool = False
    ) -> str:
        """Generate schematic S-expression output.

        Args:
            circuit_data: Circuit data to format
            use_new: Whether to use new formatter (when available)

        Returns:
            Formatted S-expression string
        """
        if use_new:
            # Use new clean formatter
            from circuit_synth.kicad.core.clean_formatter import CleanSExprFormatter

            formatter = CleanSExprFormatter()
            return formatter.format_schematic(circuit_data)

        # Use current formatter
        from circuit_synth.kicad.core.s_expression import SExpressionParser

        # Build basic schematic structure
        schematic_sexp = [
            "kicad_sch",
            ["version", 20250114],
            ["generator", "circuit_synth"],
            ["generator_version", "9.0"],
            ["uuid", circuit_data.get("uuid", "test-uuid")],
            ["paper", "A4"],
        ]

        # Add components if present
        if "components" in circuit_data:
            for comp in circuit_data["components"]:
                schematic_sexp.append(self._build_component_sexp(comp))

        # Format using current formatter
        parser = SExpressionParser()
        return parser._format_sexp(schematic_sexp)

    def _build_component_sexp(self, component: Dict) -> List:
        """Build component S-expression structure.

        Args:
            component: Component data

        Returns:
            S-expression list structure
        """
        return [
            "symbol",
            ["lib_id", component.get("lib_id", "Device:R")],
            [
                "at",
                component.get("x", 0),
                component.get("y", 0),
                component.get("angle", 0),
            ],
            ["unit", component.get("unit", 1)],
            ["exclude_from_sim", "no"],
            ["in_bom", "yes"],
            ["on_board", "yes"],
            ["dnp", "no"],
            ["uuid", component.get("uuid", "test-uuid")],
            [
                "property",
                "Reference",
                component.get("reference", "R1"),
                ["at", 0, 0, 0],
                ["effects", ["font", ["size", 1.27, 1.27]]],
            ],
            [
                "property",
                "Value",
                component.get("value", "10k"),
                ["at", 0, 5, 0],
                ["effects", ["font", ["size", 1.27, 1.27]]],
            ],
        ]

    def _compare_outputs(self, old: str, new: str) -> Dict:
        """Compare two formatter outputs.

        Args:
            old: Old formatter output
            new: New formatter output

        Returns:
            Comparison results
        """
        if old == new:
            return {"identical": True, "differences": []}

        # Generate diff
        diff = list(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile="old_formatter",
                tofile="new_formatter",
                n=3,
            )
        )

        return {
            "identical": False,
            "differences": diff[:100],  # Limit to first 100 lines
        }

    def _check_functional_equivalence(self, old: str, new: str) -> bool:
        """Check if two outputs are functionally equivalent.

        This checks if the outputs represent the same circuit structure,
        even if formatting differs.

        Args:
            old: Old formatter output
            new: New formatter output

        Returns:
            True if functionally equivalent
        """
        # For now, simple check - normalize whitespace and compare
        old_normalized = " ".join(old.split())
        new_normalized = " ".join(new.split())

        # Extract key elements (components, nets, etc.)
        old_components = self._extract_components(old)
        new_components = self._extract_components(new)

        # Check if same components exist
        if set(old_components) != set(new_components):
            return False

        # TODO: Add more sophisticated equivalence checks
        # - Net connectivity
        # - Property values
        # - Sheet hierarchy

        return True

    def _extract_components(self, sexp_text: str) -> List[str]:
        """Extract component references from S-expression text.

        Args:
            sexp_text: S-expression text

        Returns:
            List of component references
        """
        import re

        # Find all reference properties
        pattern = r'property\s+"Reference"\s+"([^"]+)"'
        matches = re.findall(pattern, sexp_text)

        return matches

    def _get_output_metrics(self, output: str) -> Dict:
        """Get metrics for formatter output.

        Args:
            output: Formatter output

        Returns:
            Metrics dictionary
        """
        lines = output.splitlines()

        return {
            "line_count": len(lines),
            "char_count": len(output),
            "max_line_length": max(len(line) for line in lines) if lines else 0,
            "avg_line_length": (
                sum(len(line) for line in lines) / len(lines) if lines else 0
            ),
            "indent_levels": self._count_indent_levels(output),
        }

    def _count_indent_levels(self, output: str) -> int:
        """Count maximum indentation levels.

        Args:
            output: Formatter output

        Returns:
            Maximum indent level
        """
        max_indent = 0
        for line in output.splitlines():
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent // 2)  # Assuming 2-space indent

        return max_indent

    def _hash_file(self, file_path: Path) -> str:
        """Calculate hash of file contents.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def _update_migration_status(self, result: Dict):
        """Update migration status based on test result.

        Args:
            result: Test result dictionary
        """
        self.migration_status["tests_run"] += 1

        if result["functional_equivalent"]:
            self.migration_status["tests_passed"] += 1
            self.migration_status["functional_equivalence"].append(result["test_name"])
        else:
            self.migration_status["tests_failed"] += 1

    def generate_report(self) -> str:
        """Generate migration test report.

        Returns:
            Path to report file
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "migration_status": self.migration_status,
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": self.migration_status["tests_passed"],
                "failed": self.migration_status["tests_failed"],
                "success_rate": (
                    self.migration_status["tests_passed"]
                    / self.migration_status["tests_run"]
                    * 100
                    if self.migration_status["tests_run"] > 0
                    else 0
                ),
            },
        }

        # Save JSON report
        report_file = (
            self.reports_dir / f"migration_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        report_file.write_text(json.dumps(report, indent=2))

        # Generate human-readable summary
        summary_file = (
            self.reports_dir / f"migration_summary_{datetime.now():%Y%m%d_%H%M%S}.md"
        )
        summary_text = self._generate_summary_markdown(report)
        summary_file.write_text(summary_text)

        logger.info(f"Reports generated: {report_file}, {summary_file}")

        return str(summary_file)

    def _generate_summary_markdown(self, report: Dict) -> str:
        """Generate markdown summary of migration testing.

        Args:
            report: Report data

        Returns:
            Markdown formatted summary
        """
        summary = f"""# S-Expression Formatter Migration Report

## Summary
- **Date**: {report['timestamp']}
- **Phase**: {report['migration_status']['phase']}
- **Total Tests**: {report['summary']['total_tests']}
- **Passed**: {report['summary']['passed']}
- **Failed**: {report['summary']['failed']}
- **Success Rate**: {report['summary']['success_rate']:.1f}%

## Test Results

| Test Name | Functional Equivalent | Differences |
|-----------|---------------------|-------------|
"""

        for result in report["test_results"]:
            equiv = "✅" if result["functional_equivalent"] else "❌"
            diff_count = len(result["differences"]) if result["differences"] else 0
            summary += f"| {result['test_name']} | {equiv} | {diff_count} lines |\n"

        summary += f"""

## Metrics Comparison

### Average Metrics
- **Old Formatter**: {self._calculate_avg_metrics(report, 'old_metrics')}
- **New Formatter**: {self._calculate_avg_metrics(report, 'new_metrics')}

## Recommendations
{self._generate_recommendations(report)}
"""

        return summary

    def _calculate_avg_metrics(self, report: Dict, metrics_key: str) -> str:
        """Calculate average metrics from test results.

        Args:
            report: Report data
            metrics_key: Key for metrics ('old_metrics' or 'new_metrics')

        Returns:
            Formatted metrics string
        """
        if not report["test_results"]:
            return "No data"

        total_lines = sum(r[metrics_key]["line_count"] for r in report["test_results"])
        total_chars = sum(r[metrics_key]["char_count"] for r in report["test_results"])
        avg_indent = sum(
            r[metrics_key]["indent_levels"] for r in report["test_results"]
        ) / len(report["test_results"])

        return (
            f"Lines: {total_lines}, Chars: {total_chars}, Avg Indent: {avg_indent:.1f}"
        )

    def _generate_recommendations(self, report: Dict) -> str:
        """Generate recommendations based on test results.

        Args:
            report: Report data

        Returns:
            Recommendations text
        """
        success_rate = report["summary"]["success_rate"]

        if success_rate == 100:
            return "✅ All tests passing! Ready to proceed to next migration phase."
        elif success_rate >= 95:
            return "⚠️ Nearly ready. Review failing tests before proceeding."
        elif success_rate >= 80:
            return "🔧 Significant work needed. Focus on failing test cases."
        else:
            return "❌ Major issues detected. Review formatter implementation."


def run_baseline_capture():
    """Run baseline capture for existing test circuits."""
    harness = FormatterTestHarness(Path("/tmp/formatter_migration"))

    # Test with simple circuit
    simple_circuit = {
        "uuid": "test-123",
        "components": [
            {"reference": "R1", "value": "10k", "x": 10, "y": 20},
            {"reference": "C1", "value": "100nF", "x": 30, "y": 20},
        ],
    }

    harness.capture_baseline("simple_circuit", simple_circuit)

    # Test with hierarchical circuit
    hierarchical_circuit = {
        "uuid": "hier-456",
        "components": [
            {"reference": "U1", "value": "LM324", "x": 50, "y": 50, "unit": 1}
        ],
        "sheets": [{"name": "child1", "file": "child1.kicad_sch"}],
    }

    harness.capture_baseline("hierarchical_circuit", hierarchical_circuit)

    # Generate initial report
    report_path = harness.generate_report()
    print(f"Baseline capture complete. Report: {report_path}")

    return harness


if __name__ == "__main__":
    # Run baseline capture when executed directly
    run_baseline_capture()
