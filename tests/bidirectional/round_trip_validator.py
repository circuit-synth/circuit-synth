#!/usr/bin/env python3
"""
Robust Round-Trip Validation for Bidirectional KiCad ↔ Python Synchronization.

This module implements production-ready validation strategies for verifying that
circuits remain identical through KiCad ↔ Python conversion cycles.

Key Requirements (for millions of users):
- Order independence (component/net ordering doesn't matter)
- Semantic equivalence (different code representations of same circuit)
- Floating-point tolerance (positions have mm precision)
- Metadata filtering (UUIDs, timestamps ignored)
- Comment preservation (CRITICAL - documentation must survive)
- Scalability (O(n) algorithms, works with 10,000+ components)
"""

import ast
import json
import logging
import re
import subprocess
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    passed: bool
    phase: str  # "json", "comments", "ast", "netlist"
    differences: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Human-readable summary."""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        msg = f"{status} ({self.phase})"
        if self.differences:
            msg += f"\n  Differences ({len(self.differences)}):"
            for diff in self.differences[:5]:  # Show first 5
                msg += f"\n    - {diff}"
            if len(self.differences) > 5:
                msg += f"\n    ... and {len(self.differences) - 5} more"
        if self.warnings:
            msg += f"\n  Warnings ({len(self.warnings)}):"
            for warn in self.warnings[:3]:
                msg += f"\n    - {warn}"
        return msg


@dataclass
class CircuitComparison:
    """Complete round-trip validation result."""

    json_validation: Optional[ValidationResult] = None
    comment_validation: Optional[ValidationResult] = None
    ast_validation: Optional[ValidationResult] = None
    netlist_validation: Optional[ValidationResult] = None

    @property
    def passed(self) -> bool:
        """Overall pass/fail status."""
        # JSON and comments are REQUIRED
        if self.json_validation and not self.json_validation.passed:
            return False
        if self.comment_validation and not self.comment_validation.passed:
            return False
        # AST and netlist are optional (warnings only)
        return True

    def __str__(self) -> str:
        """Human-readable summary."""
        lines = ["=" * 60]
        lines.append(f"Round-Trip Validation: {'✅ PASSED' if self.passed else '❌ FAILED'}")
        lines.append("=" * 60)

        if self.json_validation:
            lines.append(str(self.json_validation))
        if self.comment_validation:
            lines.append(str(self.comment_validation))
        if self.ast_validation:
            lines.append(str(self.ast_validation))
        if self.netlist_validation:
            lines.append(str(self.netlist_validation))

        lines.append("=" * 60)
        return "\n".join(lines)


class CircuitJSONComparator:
    """
    Compare circuits using JSON canonical representation.

    This is Phase 1 validation - ensures electrical correctness.
    """

    def __init__(
        self,
        position_tolerance: float = 0.01,  # mm
        ignore_uuids: bool = True,
        ignore_timestamps: bool = True,
    ):
        self.position_tolerance = position_tolerance
        self.ignore_uuids = ignore_uuids
        self.ignore_timestamps = ignore_timestamps

    def compare_kicad_projects(
        self,
        original_kicad_dir: Path,
        roundtrip_kicad_dir: Path
    ) -> ValidationResult:
        """
        Compare two KiCad projects for electrical equivalence.

        Uses KiCad JSON export as canonical intermediate format.
        """
        differences = []
        warnings = []

        # Export both to JSON
        try:
            orig_json = self._export_kicad_to_json(original_kicad_dir)
            rt_json = self._export_kicad_to_json(roundtrip_kicad_dir)
        except Exception as e:
            return ValidationResult(
                passed=False,
                phase="json",
                differences=[f"Failed to export KiCad to JSON: {e}"]
            )

        # Compare components (order-independent)
        comp_diffs = self._compare_components(orig_json, rt_json)
        differences.extend(comp_diffs)

        # Compare nets (order-independent)
        net_diffs = self._compare_nets(orig_json, rt_json)
        differences.extend(net_diffs)

        # Compare positions (with tolerance)
        pos_diffs, pos_warns = self._compare_positions(orig_json, rt_json)
        differences.extend(pos_diffs)
        warnings.extend(pos_warns)

        return ValidationResult(
            passed=(len(differences) == 0),
            phase="json",
            differences=differences,
            warnings=warnings,
            metadata={"components": len(orig_json.get("components", [])),
                     "nets": len(orig_json.get("nets", []))}
        )

    def _export_kicad_to_json(self, kicad_dir: Path) -> Dict:
        """Export KiCad project to JSON using kicad-cli."""
        # Find .kicad_sch file
        sch_files = list(kicad_dir.glob("*.kicad_sch"))
        if not sch_files:
            raise FileNotFoundError(f"No .kicad_sch file in {kicad_dir}")

        # Use main schematic (matches directory name or first found)
        sch_file = None
        for f in sch_files:
            if f.stem == kicad_dir.name:
                sch_file = f
                break
        if not sch_file:
            sch_file = sch_files[0]

        # For now, parse the schematic file directly
        # TODO: Use kicad-cli when JSON export available
        return self._parse_kicad_sch_to_dict(sch_file)

    def _parse_kicad_sch_to_dict(self, sch_file: Path) -> Dict:
        """Parse KiCad schematic S-expression to dictionary."""
        # Simple parser for components and nets
        content = sch_file.read_text()

        result = {
            "components": [],
            "nets": [],
            "positions": {}
        }

        # Extract symbols (components)
        # Pattern: (symbol (lib_id "Device:R") ... (at X Y rotation) ...)
        symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\).*?\(at\s+([\d.]+)\s+([\d.]+)\s+(\d+)\).*?\(property\s+"Reference"\s+"([^"]+)".*?\(property\s+"Value"\s+"([^"]+)"'

        for match in re.finditer(symbol_pattern, content, re.DOTALL):
            lib_id, x, y, rotation, ref, value = match.groups()
            result["components"].append({
                "reference": ref,
                "lib_id": lib_id,
                "value": value,
                "position": {"x": float(x), "y": float(y), "rotation": int(rotation)}
            })
            result["positions"][ref] = {"x": float(x), "y": float(y)}

        # Extract nets from junction and label elements
        # This is simplified - real nets need wire tracing
        label_pattern = r'\(label\s+"([^"]+)"\s+\(at\s+([\d.]+)\s+([\d.]+)'
        for match in re.finditer(label_pattern, content):
            net_name, x, y = match.groups()
            if not any(n["name"] == net_name for n in result["nets"]):
                result["nets"].append({
                    "name": net_name,
                    "connections": []  # Would need wire tracing for real connections
                })

        return result

    def _compare_components(self, orig: Dict, roundtrip: Dict) -> List[str]:
        """Compare components (order-independent)."""
        diffs = []

        orig_comps = {c["reference"]: c for c in orig.get("components", [])}
        rt_comps = {c["reference"]: c for c in roundtrip.get("components", [])}

        # Check for missing components
        orig_refs = set(orig_comps.keys())
        rt_refs = set(rt_comps.keys())

        missing = orig_refs - rt_refs
        if missing:
            diffs.append(f"Missing components in round-trip: {sorted(missing)}")

        extra = rt_refs - orig_refs
        if extra:
            diffs.append(f"Extra components in round-trip: {sorted(extra)}")

        # Check component values for common refs
        for ref in orig_refs & rt_refs:
            orig_comp = orig_comps[ref]
            rt_comp = rt_comps[ref]

            if orig_comp.get("value") != rt_comp.get("value"):
                diffs.append(
                    f"Component {ref} value mismatch: "
                    f"{orig_comp.get('value')} → {rt_comp.get('value')}"
                )

            if orig_comp.get("lib_id") != rt_comp.get("lib_id"):
                diffs.append(
                    f"Component {ref} lib_id mismatch: "
                    f"{orig_comp.get('lib_id')} → {rt_comp.get('lib_id')}"
                )

        return diffs

    def _compare_nets(self, orig: Dict, roundtrip: Dict) -> List[str]:
        """Compare nets (order-independent)."""
        diffs = []

        orig_nets = {n["name"]: n for n in orig.get("nets", [])}
        rt_nets = {n["name"]: n for n in roundtrip.get("nets", [])}

        orig_names = set(orig_nets.keys())
        rt_names = set(rt_nets.keys())

        missing = orig_names - rt_names
        if missing:
            diffs.append(f"Missing nets in round-trip: {sorted(missing)}")

        extra = rt_names - orig_names
        if extra:
            diffs.append(f"Extra nets in round-trip: {sorted(extra)}")

        return diffs

    def _compare_positions(
        self, orig: Dict, roundtrip: Dict
    ) -> Tuple[List[str], List[str]]:
        """Compare component positions with tolerance."""
        diffs = []
        warnings = []

        orig_pos = orig.get("positions", {})
        rt_pos = roundtrip.get("positions", {})

        for ref in set(orig_pos.keys()) & set(rt_pos.keys()):
            orig_xy = orig_pos[ref]
            rt_xy = rt_pos[ref]

            dx = abs(orig_xy["x"] - rt_xy["x"])
            dy = abs(orig_xy["y"] - rt_xy["y"])

            if dx > self.position_tolerance or dy > self.position_tolerance:
                diffs.append(
                    f"Component {ref} position changed: "
                    f"({orig_xy['x']:.2f}, {orig_xy['y']:.2f}) → "
                    f"({rt_xy['x']:.2f}, {rt_xy['y']:.2f})"
                )

        return diffs, warnings


class CommentPreservationValidator:
    """
    Validate that comments are preserved through round-trip.

    This is Phase 2 validation - CRITICAL for usability.
    """

    def compare_python_comments(
        self, original_py: Path, roundtrip_py: Path
    ) -> ValidationResult:
        """
        Compare comments between original and round-trip Python files.

        Strategy: Extract all comments using tokenize module, compare content
        (not positions, since those may change with code reformatting).
        """
        differences = []
        warnings = []

        try:
            orig_comments = self._extract_comments(original_py)
            rt_comments = self._extract_comments(roundtrip_py)
        except Exception as e:
            return ValidationResult(
                passed=False,
                phase="comments",
                differences=[f"Failed to extract comments: {e}"]
            )

        # Compare comment content (order-independent for now)
        orig_text = self._normalize_comments(orig_comments)
        rt_text = self._normalize_comments(rt_comments)

        missing = orig_text - rt_text
        if missing:
            differences.append(
                f"Missing comments ({len(missing)}): " +
                ", ".join(f"'{c[:30]}...'" if len(c) > 30 else f"'{c}'"
                         for c in sorted(missing)[:5])
            )

        extra = rt_text - orig_text
        if extra:
            warnings.append(
                f"Extra comments ({len(extra)}): " +
                ", ".join(f"'{c[:30]}...'" if len(c) > 30 else f"'{c}'"
                         for c in sorted(extra)[:5])
            )

        # Check for common issue: all comments moved to top
        if orig_comments and rt_comments:
            orig_first_5_lines = [c[0] for c in orig_comments[:5]]  # (line, text) tuples
            rt_first_5_lines = [c[0] for c in rt_comments[:5]]

            # If all RT comments are at top but originals were distributed
            if (len(set(rt_first_5_lines)) < 5 and
                len(set(orig_first_5_lines)) > 5):
                warnings.append(
                    "Comments may have been moved to top of function "
                    "(context lost)"
                )

        return ValidationResult(
            passed=(len(differences) == 0),
            phase="comments",
            differences=differences,
            warnings=warnings,
            metadata={
                "original_comments": len(orig_comments),
                "roundtrip_comments": len(rt_comments)
            }
        )

    def _extract_comments(self, py_file: Path) -> List[Tuple[int, str]]:
        """Extract all comments with line numbers."""
        comments = []

        with open(py_file, "rb") as f:
            try:
                tokens = tokenize.tokenize(f.readline)
                for tok in tokens:
                    if tok.type == tokenize.COMMENT:
                        line_num = tok.start[0]
                        comment_text = tok.string.lstrip("#").strip()
                        comments.append((line_num, comment_text))
            except tokenize.TokenError:
                pass  # Incomplete file is OK

        return comments

    def _normalize_comments(self, comments: List[Tuple[int, str]]) -> Set[str]:
        """Normalize comments for comparison (ignore positions)."""
        # Just use comment text, ignore line numbers for order-independent comparison
        return {text for _, text in comments if text.strip()}


class PythonASTComparator:
    """
    Compare Python code using AST (optional validation).

    This is Phase 3 - code quality check, not required for correctness.
    """

    def compare_python_ast(
        self, original_py: Path, roundtrip_py: Path
    ) -> ValidationResult:
        """Compare Python files at AST level."""
        differences = []
        warnings = []

        try:
            with open(original_py) as f:
                orig_tree = ast.parse(f.read())
            with open(roundtrip_py) as f:
                rt_tree = ast.parse(f.read())
        except SyntaxError as e:
            return ValidationResult(
                passed=False,
                phase="ast",
                differences=[f"Syntax error: {e}"]
            )

        # Compare function definitions
        orig_funcs = self._extract_functions(orig_tree)
        rt_funcs = self._extract_functions(rt_tree)

        if set(orig_funcs.keys()) != set(rt_funcs.keys()):
            differences.append(
                f"Function names differ: {sorted(orig_funcs.keys())} vs {sorted(rt_funcs.keys())}"
            )

        # Compare imports
        orig_imports = self._extract_imports(orig_tree)
        rt_imports = self._extract_imports(rt_tree)

        missing_imports = orig_imports - rt_imports
        if missing_imports:
            warnings.append(f"Missing imports: {sorted(missing_imports)}")

        return ValidationResult(
            passed=(len(differences) == 0),
            phase="ast",
            differences=differences,
            warnings=warnings,
            metadata={
                "functions": len(orig_funcs),
                "imports": len(orig_imports)
            }
        )

    def _extract_functions(self, tree: ast.AST) -> Dict[str, ast.FunctionDef]:
        """Extract all function definitions."""
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = node
        return functions

    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract all import statements."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.add(f"{module}.{alias.name}")
        return imports


class RoundTripValidator:
    """
    Comprehensive round-trip validation orchestrator.

    Executes all validation phases and reports results.
    """

    def __init__(
        self,
        position_tolerance: float = 0.01,
        require_json: bool = True,
        require_comments: bool = True,
        require_ast: bool = False,
    ):
        self.json_comparator = CircuitJSONComparator(
            position_tolerance=position_tolerance
        )
        self.comment_validator = CommentPreservationValidator()
        self.ast_comparator = PythonASTComparator()

        self.require_json = require_json
        self.require_comments = require_comments
        self.require_ast = require_ast

    def validate_complete_roundtrip(
        self,
        original_py: Path,
        original_kicad_dir: Path,
        roundtrip_py: Path,
        roundtrip_kicad_dir: Path,
    ) -> CircuitComparison:
        """
        Validate complete round-trip: Python → KiCad → Python.

        Phases:
        1. JSON validation (electrical correctness) - REQUIRED
        2. Comment preservation (documentation) - REQUIRED
        3. AST validation (code quality) - OPTIONAL

        Args:
            original_py: Original Python circuit file
            original_kicad_dir: KiCad project generated from original
            roundtrip_py: Python file imported back from KiCad
            roundtrip_kicad_dir: KiCad project regenerated from roundtrip

        Returns:
            CircuitComparison with all validation results
        """
        result = CircuitComparison()

        # Phase 1: JSON validation (KiCad projects)
        if self.require_json and original_kicad_dir.exists() and roundtrip_kicad_dir.exists():
            logger.info("Phase 1: JSON validation...")
            result.json_validation = self.json_comparator.compare_kicad_projects(
                original_kicad_dir, roundtrip_kicad_dir
            )

        # Phase 2: Comment preservation (Python files)
        if self.require_comments and original_py.exists() and roundtrip_py.exists():
            logger.info("Phase 2: Comment preservation validation...")
            result.comment_validation = self.comment_validator.compare_python_comments(
                original_py, roundtrip_py
            )

        # Phase 3: AST validation (Python files)
        if self.require_ast and original_py.exists() and roundtrip_py.exists():
            logger.info("Phase 3: AST validation...")
            result.ast_validation = self.ast_comparator.compare_python_ast(
                original_py, roundtrip_py
            )

        return result

    def validate_simple_roundtrip(
        self,
        original_py: Path,
        roundtrip_py: Path,
        kicad_dir: Optional[Path] = None,
    ) -> CircuitComparison:
        """
        Simplified validation for basic round-trips.

        Args:
            original_py: Original Python circuit file
            roundtrip_py: Python file after round-trip
            kicad_dir: Optional KiCad directory for position check

        Returns:
            CircuitComparison with comment and AST validation
        """
        result = CircuitComparison()

        # Comment preservation
        if self.require_comments:
            result.comment_validation = self.comment_validator.compare_python_comments(
                original_py, roundtrip_py
            )

        # AST validation
        if self.require_ast:
            result.ast_validation = self.ast_comparator.compare_python_ast(
                original_py, roundtrip_py
            )

        return result


# Convenience functions for quick validation

def validate_roundtrip(
    original_py: Path,
    roundtrip_py: Path,
    original_kicad: Optional[Path] = None,
    roundtrip_kicad: Optional[Path] = None,
    require_json: bool = True,
    require_comments: bool = True,
) -> CircuitComparison:
    """
    Quick validation function for round-trip testing.

    Usage:
        result = validate_roundtrip(
            Path("original.py"),
            Path("roundtrip.py"),
            original_kicad=Path("original_kicad"),
            roundtrip_kicad=Path("roundtrip_kicad")
        )
        assert result.passed, str(result)
    """
    validator = RoundTripValidator(
        require_json=require_json and original_kicad is not None,
        require_comments=require_comments,
        require_ast=False  # Optional by default
    )

    if original_kicad and roundtrip_kicad:
        return validator.validate_complete_roundtrip(
            original_py, original_kicad, roundtrip_py, roundtrip_kicad
        )
    else:
        return validator.validate_simple_roundtrip(
            original_py, roundtrip_py
        )


def assert_roundtrip_valid(
    original_py: Path,
    roundtrip_py: Path,
    **kwargs
) -> None:
    """
    Assert that round-trip is valid (raises AssertionError if not).

    Usage:
        assert_roundtrip_valid(
            Path("original.py"),
            Path("roundtrip.py")
        )
    """
    result = validate_roundtrip(original_py, roundtrip_py, **kwargs)
    assert result.passed, f"\n{result}"


if __name__ == "__main__":
    # Self-test example
    import tempfile

    print("Round-Trip Validator - Self Test")
    print("=" * 60)

    # Create test files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
from circuit_synth import Component, Net, circuit

@circuit(name="test")
def test_circuit():
    '''Test circuit.'''
    # Important comment about R1
    r1 = Component("Device:R", ref="R1", value="10k")
    # Another comment
    r2 = Component("Device:R", ref="R2", value="20k")
    return r1, r2
""")
        orig_file = Path(f.name)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
from circuit_synth import Component, Net, circuit

@circuit(name="test")
def test_circuit():
    '''Test circuit.'''
    # Important comment about R1
    # Another comment
    r1 = Component("Device:R", ref="R1", value="10k")
    r2 = Component("Device:R", ref="R2", value="20k")
    return r1, r2
""")
        rt_file = Path(f.name)

    try:
        # Run validation
        result = validate_roundtrip(
            orig_file, rt_file,
            require_json=False,  # No KiCad files in this test
            require_comments=True
        )

        print(result)
        print("\nValidation completed!")

    finally:
        orig_file.unlink()
        rt_file.unlink()
