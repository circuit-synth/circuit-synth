"""
Circuit Diff Analysis for Memory-Bank System

Intelligent analysis of circuit changes between commits using circuit-synth.
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# NOTE: KiCad parsing temporarily simplified for initial release
# from circuit_synth.kicad.netlist_importer import CircuitSynthParser


logger = logging.getLogger(__name__)


@dataclass
class ComponentChange:
    """Represents a change to a component."""

    reference: str
    change_type: str  # 'added', 'removed', 'modified'
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    details: List[str] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []


@dataclass
class NetChange:
    """Represents a change to a net connection."""

    net_name: str
    change_type: str  # 'added', 'removed', 'modified'
    old_connections: List[str] = None
    new_connections: List[str] = None
    details: List[str] = None

    def __post_init__(self):
        if self.old_connections is None:
            self.old_connections = []
        if self.new_connections is None:
            self.new_connections = []
        if self.details is None:
            self.details = []


@dataclass
class CircuitDiff:
    """Complete diff analysis between two circuit states."""

    commit_hash: str
    commit_message: str
    timestamp: str
    component_changes: List[ComponentChange]
    net_changes: List[NetChange]
    summary: Dict[str, Any]

    def has_significant_changes(self) -> bool:
        """Check if this diff contains significant changes worth documenting."""
        return (
            len(self.component_changes) > 0
            or len(self.net_changes) > 0
            or any(
                keyword in self.commit_message.lower()
                for keyword in ["add", "remove", "change", "fix", "update", "modify"]
            )
        )


class CircuitDiffAnalyzer:
    """Analyzes circuit changes between different versions."""

    def __init__(self, board_path: str):
        """Initialize analyzer for specific board."""
        self.board_path = Path(board_path)
        self.memory_bank_path = self.board_path / "memory-bank"
        self.cache_path = self.memory_bank_path / "cache"
        self.cache_path.mkdir(exist_ok=True)

    def analyze_commit_changes(self, commit_hash: str) -> CircuitDiff:
        """Analyze circuit changes in a specific commit."""
        try:
            commit_message = self._get_commit_message(commit_hash)
            timestamp = datetime.now().isoformat()

            # Get changed files in this commit
            changed_files = self._get_changed_files(commit_hash)

            component_changes = []
            net_changes = []

            # Look for KiCad schematic files
            kicad_files = [f for f in changed_files if f.endswith(".kicad_sch")]

            if kicad_files:
                # Analyze KiCad schematic changes
                for kicad_file in kicad_files:
                    try:
                        changes = self._analyze_kicad_file_changes(
                            kicad_file, commit_hash
                        )
                        component_changes.extend(changes.get("components", []))
                        net_changes.extend(changes.get("nets", []))
                    except Exception as e:
                        logger.warning(f"Failed to analyze {kicad_file}: {e}")

            # Look for circuit-synth Python files
            python_files = [
                f for f in changed_files if f.endswith(".py") and "circuit" in f.lower()
            ]

            if python_files:
                # Analyze Python circuit changes (if we can parse them)
                for py_file in python_files:
                    try:
                        changes = self._analyze_python_file_changes(
                            py_file, commit_hash
                        )
                        component_changes.extend(changes.get("components", []))
                        net_changes.extend(changes.get("nets", []))
                    except Exception as e:
                        logger.debug(f"Could not analyze Python file {py_file}: {e}")

            # Create summary
            summary = {
                "total_component_changes": len(component_changes),
                "total_net_changes": len(net_changes),
                "files_analyzed": len(kicad_files) + len(python_files),
                "kicad_files": kicad_files,
                "python_files": python_files,
                "change_types": {},
            }

            # Count change types
            for change in component_changes:
                change_type = change.change_type
                summary["change_types"][f"component_{change_type}"] = (
                    summary["change_types"].get(f"component_{change_type}", 0) + 1
                )

            for change in net_changes:
                change_type = change.change_type
                summary["change_types"][f"net_{change_type}"] = (
                    summary["change_types"].get(f"net_{change_type}", 0) + 1
                )

            return CircuitDiff(
                commit_hash=commit_hash,
                commit_message=commit_message,
                timestamp=timestamp,
                component_changes=component_changes,
                net_changes=net_changes,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"Failed to analyze commit {commit_hash}: {e}")
            # Return minimal diff on error
            return CircuitDiff(
                commit_hash=commit_hash,
                commit_message=self._get_commit_message(commit_hash),
                timestamp=datetime.now().isoformat(),
                component_changes=[],
                net_changes=[],
                summary={"error": str(e)},
            )

    def _analyze_kicad_file_changes(
        self, kicad_file: str, commit_hash: str
    ) -> Dict[str, List]:
        """Analyze changes in a KiCad schematic file."""
        component_changes = []
        net_changes = []

        try:
            # Get current version of file
            current_content = self._get_file_content(kicad_file)
            if not current_content:
                return {"components": component_changes, "nets": net_changes}

            # Get previous version of file
            previous_content = self._get_file_content(kicad_file, f"{commit_hash}~1")

            # Save to temporary files for analysis
            current_file = self.cache_path / f"current_{commit_hash[:7]}.kicad_sch"
            previous_file = self.cache_path / f"previous_{commit_hash[:7]}.kicad_sch"

            with open(current_file, "w") as f:
                f.write(current_content)

            if previous_content:
                with open(previous_file, "w") as f:
                    f.write(previous_content)

                # For now, use simple text-based analysis
                # TODO: Integrate full KiCad parsing in future version
                try:
                    component_changes.extend(
                        self._simple_diff_analysis(
                            previous_content, current_content, "component"
                        )
                    )
                    net_changes.extend(
                        self._simple_diff_analysis(
                            previous_content, current_content, "net"
                        )
                    )
                except Exception as e:
                    logger.debug(f"Simple diff analysis failed: {e}")
            else:
                # New file - analyze as additions
                try:
                    component_changes.extend(
                        self._simple_diff_analysis("", current_content, "component")
                    )
                except Exception as e:
                    logger.debug(f"Could not analyze new file: {e}")

            # Clean up temporary files
            for temp_file in [current_file, previous_file]:
                if temp_file.exists():
                    temp_file.unlink()

        except Exception as e:
            logger.debug(f"Error analyzing KiCad file changes: {e}")

        return {"components": component_changes, "nets": net_changes}

    def _analyze_python_file_changes(
        self, python_file: str, commit_hash: str
    ) -> Dict[str, List]:
        """Analyze changes in a Python circuit file."""
        component_changes = []
        net_changes = []

        try:
            # Get file contents
            current_content = self._get_file_content(python_file)
            previous_content = self._get_file_content(python_file, f"{commit_hash}~1")

            if current_content and previous_content:
                # Simple analysis based on Component() patterns
                component_changes.extend(
                    self._analyze_python_components(previous_content, current_content)
                )

                # Simple analysis based on Net() patterns
                net_changes.extend(
                    self._analyze_python_nets(previous_content, current_content)
                )

        except Exception as e:
            logger.debug(f"Error analyzing Python file changes: {e}")

        return {"components": component_changes, "nets": net_changes}

    def _compare_circuits(
        self, old_circuit, new_circuit
    ) -> Tuple[List[ComponentChange], List[NetChange]]:
        """Compare two circuit objects and identify changes.

        NOTE: This method is reserved for future full KiCad parsing integration.
        Currently using simplified text-based analysis.
        """
        # TODO: Implement full circuit object comparison when KiCad parsing is integrated
        logger.debug(
            "Circuit object comparison not yet implemented - using text analysis"
        )
        return [], []

    def _simple_diff_analysis(
        self, old_content: str, new_content: str, analysis_type: str
    ) -> List:
        """Simple text-based diff analysis as fallback."""
        changes = []

        try:
            import re

            if analysis_type == "component":
                # Look for component patterns in KiCad files
                # Pattern for symbol instances: (symbol (lib_id "Library:Symbol") (at x y rotation) ...)
                symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+[\d.\s-]+\).*?\(property\s+"Reference"\s+"([^"]+)"'

                old_matches = set(re.findall(symbol_pattern, old_content, re.DOTALL))
                new_matches = set(re.findall(symbol_pattern, new_content, re.DOTALL))

                added_components = new_matches - old_matches
                removed_components = old_matches - new_matches

                for symbol, ref in added_components:
                    changes.append(
                        ComponentChange(
                            reference=ref,
                            change_type="added",
                            new_value={"symbol": symbol},
                            details=[f"Added component: {symbol}"],
                        )
                    )

                for symbol, ref in removed_components:
                    changes.append(
                        ComponentChange(
                            reference=ref,
                            change_type="removed",
                            old_value={"symbol": symbol},
                            details=[f"Removed component: {symbol}"],
                        )
                    )

                # Check for value changes
                value_pattern = r'\(property\s+"Value"\s+"([^"]+)"\s+.*?\(property\s+"Reference"\s+"([^"]+)"'
                old_values = dict(re.findall(value_pattern, old_content, re.DOTALL))
                new_values = dict(re.findall(value_pattern, new_content, re.DOTALL))

                for ref in old_values:
                    if ref in new_values and old_values[ref] != new_values[ref]:
                        changes.append(
                            ComponentChange(
                                reference=ref,
                                change_type="modified",
                                old_value={"value": old_values[ref]},
                                new_value={"value": new_values[ref]},
                                details=[
                                    f"Value changed: {old_values[ref]} → {new_values[ref]}"
                                ],
                            )
                        )

            elif analysis_type == "net":
                # Look for net patterns - simplified for KiCad schematics
                # This is basic - full net analysis would require deeper parsing
                wire_pattern = r"\(wire\s+.*?\)"

                old_wires = len(re.findall(wire_pattern, old_content))
                new_wires = len(re.findall(wire_pattern, new_content))

                if new_wires > old_wires:
                    changes.append(
                        NetChange(
                            net_name="Unknown",
                            change_type="added",
                            details=[f"Added {new_wires - old_wires} wire(s)"],
                        )
                    )
                elif old_wires > new_wires:
                    changes.append(
                        NetChange(
                            net_name="Unknown",
                            change_type="removed",
                            details=[f"Removed {old_wires - new_wires} wire(s)"],
                        )
                    )

        except Exception as e:
            logger.debug(f"Simple diff analysis failed: {e}")

        return changes

    def _analyze_python_components(
        self, old_content: str, new_content: str
    ) -> List[ComponentChange]:
        """Analyze component changes in Python files."""
        changes = []

        try:
            import re

            # Find Component() patterns
            comp_pattern = (
                r'Component\(\s*symbol=["\'](.*?)["\'].*?ref=["\'](.*?)["\'].*?\)'
            )

            old_components = set(re.findall(comp_pattern, old_content))
            new_components = set(re.findall(comp_pattern, new_content))

            added = new_components - old_components
            removed = old_components - new_components

            for symbol, ref in added:
                changes.append(
                    ComponentChange(
                        reference=ref,
                        change_type="added",
                        new_value={"symbol": symbol},
                        details=[f"Added Python component: {symbol}"],
                    )
                )

            for symbol, ref in removed:
                changes.append(
                    ComponentChange(
                        reference=ref,
                        change_type="removed",
                        old_value={"symbol": symbol},
                        details=[f"Removed Python component: {symbol}"],
                    )
                )

        except Exception as e:
            logger.debug(f"Python component analysis failed: {e}")

        return changes

    def _analyze_python_nets(
        self, old_content: str, new_content: str
    ) -> List[NetChange]:
        """Analyze net changes in Python files."""
        changes = []

        try:
            import re

            # Find Net() patterns
            net_pattern = r'Net\(["\']([^"\']+)["\']\)'

            old_nets = set(re.findall(net_pattern, old_content))
            new_nets = set(re.findall(net_pattern, new_content))

            added = new_nets - old_nets
            removed = old_nets - new_nets

            for net_name in added:
                changes.append(
                    NetChange(
                        net_name=net_name,
                        change_type="added",
                        details=[f"Added Python net: {net_name}"],
                    )
                )

            for net_name in removed:
                changes.append(
                    NetChange(
                        net_name=net_name,
                        change_type="removed",
                        details=[f"Removed Python net: {net_name}"],
                    )
                )

        except Exception as e:
            logger.debug(f"Python net analysis failed: {e}")

        return changes

    def _get_commit_message(self, commit_hash: str) -> str:
        """Get commit message for given hash."""
        try:
            result = subprocess.run(
                ["git", "log", "--format=%B", "-n", "1", commit_hash],
                capture_output=True,
                text=True,
                cwd=self.board_path,
            )
            return result.stdout.strip()
        except Exception:
            return "Unknown commit message"

    def _get_changed_files(self, commit_hash: str) -> List[str]:
        """Get list of files changed in commit."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{commit_hash}~1", commit_hash],
                capture_output=True,
                text=True,
                cwd=self.board_path,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except Exception:
            return []

    def _get_file_content(
        self, file_path: str, commit_ref: str = "HEAD"
    ) -> Optional[str]:
        """Get file content at specific commit."""
        try:
            result = subprocess.run(
                ["git", "show", f"{commit_ref}:{file_path}"],
                capture_output=True,
                text=True,
                cwd=self.board_path,
            )
            return result.stdout if result.returncode == 0 else None
        except Exception:
            return None

    def cache_circuit_state(self, commit_hash: str, circuit_data: Dict[str, Any]):
        """Cache circuit state for future comparisons."""
        try:
            cache_file = self.cache_path / f"circuit_{commit_hash[:7]}.json"
            with open(cache_file, "w") as f:
                json.dump(circuit_data, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to cache circuit state: {e}")

    def get_cached_circuit_state(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached circuit state."""
        try:
            cache_file = self.cache_path / f"circuit_{commit_hash[:7]}.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load cached circuit state: {e}")
        return None


def format_diff_for_memory_bank(diff: CircuitDiff) -> str:
    """Format circuit diff for inclusion in memory-bank files."""
    lines = []

    # Header
    lines.append(
        f"## {datetime.now().strftime('%Y-%m-%d')}: {diff.commit_message[:60]}{'...' if len(diff.commit_message) > 60 else ''}"
    )
    lines.append(f"**Commit**: {diff.commit_hash[:7]}")
    lines.append(f"**Timestamp**: {diff.timestamp}")
    lines.append("")

    # Component changes
    if diff.component_changes:
        lines.append("**Component Changes**:")
        for change in diff.component_changes:
            if change.change_type == "added":
                symbol = (
                    change.new_value.get("symbol", "Unknown")
                    if change.new_value
                    else "Unknown"
                )
                lines.append(f"- ➕ {change.reference}: Added {symbol}")
            elif change.change_type == "removed":
                symbol = (
                    change.old_value.get("symbol", "Unknown")
                    if change.old_value
                    else "Unknown"
                )
                lines.append(f"- ➖ {change.reference}: Removed {symbol}")
            elif change.change_type == "modified":
                lines.append(f"- 🔄 {change.reference}: Modified")
                for detail in change.details:
                    lines.append(f"  - {detail}")
        lines.append("")

    # Net changes
    if diff.net_changes:
        lines.append("**Net Changes**:")
        for change in diff.net_changes:
            if change.change_type == "added":
                lines.append(f"- ➕ Added net: {change.net_name}")
            elif change.change_type == "removed":
                lines.append(f"- ➖ Removed net: {change.net_name}")
            elif change.change_type == "modified":
                lines.append(f"- 🔄 Modified net: {change.net_name}")
                for detail in change.details:
                    lines.append(f"  - {detail}")
        lines.append("")

    # Summary
    summary = diff.summary
    if (
        summary.get("total_component_changes", 0) > 0
        or summary.get("total_net_changes", 0) > 0
    ):
        lines.append("**Summary**:")
        lines.append(
            f"- Components: {summary.get('total_component_changes', 0)} changes"
        )
        lines.append(f"- Nets: {summary.get('total_net_changes', 0)} changes")
        if summary.get("kicad_files"):
            lines.append(f"- KiCad files: {', '.join(summary['kicad_files'])}")
        if summary.get("python_files"):
            lines.append(f"- Python files: {', '.join(summary['python_files'])}")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)
