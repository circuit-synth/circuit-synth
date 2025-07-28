"""
Hierarchy navigation for KiCad schematics.

This module provides tools for navigating and analyzing hierarchical
schematic designs.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..core.s_expression import SExpressionParser
from ..core.types import Schematic, Sheet, SheetPin
from .sheet_manager import SheetManager

logger = logging.getLogger(__name__)


@dataclass
class HierarchyNode:
    """Node in the hierarchy tree."""

    sheet_name: str
    sheet_uuid: str
    sheet_filename: str
    parent_uuid: Optional[str] = None
    children: List["HierarchyNode"] = field(default_factory=list)
    depth: int = 0
    instance_path: List[str] = field(default_factory=list)

    def add_child(self, child: "HierarchyNode"):
        """Add a child node."""
        child.parent_uuid = self.sheet_uuid
        child.depth = self.depth + 1
        child.instance_path = self.instance_path + [self.sheet_uuid]
        self.children.append(child)

    def get_full_path(self) -> str:
        """Get the full hierarchical path."""
        if not self.instance_path:
            return self.sheet_name
        return "/".join(self.instance_path) + "/" + self.sheet_name

    def find_node(self, sheet_uuid: str) -> Optional["HierarchyNode"]:
        """Find a node by UUID in this subtree."""
        if self.sheet_uuid == sheet_uuid:
            return self

        for child in self.children:
            found = child.find_node(sheet_uuid)
            if found:
                return found

        return None


@dataclass
class HierarchyAnalysis:
    """Analysis results for a hierarchical design."""

    total_sheets: int
    max_depth: int
    circular_references: List[List[str]]
    duplicate_instances: Dict[str, int]  # filename -> count
    missing_files: List[str]
    net_scope_conflicts: List[Tuple[str, List[str]]]  # net_name -> [sheet_paths]


class HierarchyNavigator:
    """
    Navigate and analyze hierarchical schematic designs.

    This class provides tools to:
    - Build hierarchy trees
    - Find sheets and navigate paths
    - Validate hierarchy structure
    - Analyze net scoping
    """

    def __init__(self, root_schematic: Schematic, project_path: Path):
        """
        Initialize hierarchy navigator.

        Args:
            root_schematic: The root schematic
            project_path: Path to the project directory
        """
        self.root_schematic = root_schematic
        self.project_path = project_path
        self._parser = SExpressionParser()
        self._schematic_cache: Dict[str, Schematic] = {}
        self._hierarchy_tree: Optional[HierarchyNode] = None

    def get_hierarchy_tree(self) -> HierarchyNode:
        """
        Build and return the complete hierarchy tree.

        Returns:
            Root node of the hierarchy tree
        """
        if self._hierarchy_tree:
            return self._hierarchy_tree

        # Create root node
        root_node = HierarchyNode(
            sheet_name="Root", sheet_uuid="root", sheet_filename="root.kicad_sch"
        )

        # Build tree recursively
        self._build_hierarchy_recursive(self.root_schematic, root_node)

        self._hierarchy_tree = root_node
        return root_node

    def _build_hierarchy_recursive(
        self,
        schematic: Schematic,
        parent_node: HierarchyNode,
        visited: Optional[Set[str]] = None,
    ):
        """Build hierarchy tree recursively."""
        if visited is None:
            visited = set()

        # Process each sheet in the schematic
        for sheet in schematic.sheets:
            # Check for circular reference
            if sheet.uuid in visited:
                logger.warning(f"Circular reference detected: {sheet.name}")
                continue

            visited.add(sheet.uuid)

            # Create node for this sheet
            sheet_node = HierarchyNode(
                sheet_name=sheet.name,
                sheet_uuid=sheet.uuid,
                sheet_filename=sheet.filename,
            )

            parent_node.add_child(sheet_node)

            # Load sheet contents
            sheet_schematic = self._load_sheet_schematic(sheet.filename)
            if sheet_schematic:
                # Recursively process child sheets
                self._build_hierarchy_recursive(
                    sheet_schematic, sheet_node, visited.copy()
                )

    def _load_sheet_schematic(self, filename: str) -> Optional[Schematic]:
        """Load a sheet schematic from file."""
        if filename in self._schematic_cache:
            return self._schematic_cache[filename]

        filepath = self.project_path / filename
        if not filepath.exists():
            logger.warning(f"Sheet file not found: {filepath}")
            return None

        try:
            schematic = self._parser.parse_file(filepath)
            self._schematic_cache[filename] = schematic
            return schematic
        except Exception as e:
            logger.error(f"Error loading sheet {filename}: {e}")
            return None

    def find_sheet_by_name(self, name: str) -> Optional[Sheet]:
        """
        Find a sheet by name anywhere in the hierarchy.

        Args:
            name: Sheet name to find

        Returns:
            Sheet object if found
        """
        # Search in root
        for sheet in self.root_schematic.sheets:
            if sheet.name == name:
                return sheet

        # Search in cached schematics
        for schematic in self._schematic_cache.values():
            for sheet in schematic.sheets:
                if sheet.name == name:
                    return sheet

        return None

    def get_sheet_path(self, sheet_uuid: str) -> List[str]:
        """
        Get the hierarchical path to a sheet.

        Args:
            sheet_uuid: UUID of the sheet

        Returns:
            List of sheet names from root to target
        """
        tree = self.get_hierarchy_tree()
        node = tree.find_node(sheet_uuid)

        if not node:
            return []

        # Build path from instance_path
        path = []
        for uuid in node.instance_path:
            parent_node = tree.find_node(uuid)
            if parent_node:
                path.append(parent_node.sheet_name)

        path.append(node.sheet_name)
        return path

    def get_all_sheets_recursive(self) -> List[Sheet]:
        """Get all sheets in the hierarchy."""
        all_sheets = []

        # Add root sheets
        all_sheets.extend(self.root_schematic.sheets)

        # Add sheets from all cached schematics
        for schematic in self._schematic_cache.values():
            all_sheets.extend(schematic.sheets)

        return all_sheets

    def validate_hierarchy(self) -> List[str]:
        """
        Validate the hierarchy structure.

        Returns:
            List of validation issues
        """
        issues = []

        # Build complete hierarchy
        tree = self.get_hierarchy_tree()

        # Check for missing files
        self._check_missing_files(tree, issues)

        # Check for circular references
        circular_refs = self.find_circular_references()
        for cycle in circular_refs:
            issues.append(f"Circular reference: {' -> '.join(cycle)}")

        # Check for duplicate sheet names at same level
        self._check_duplicate_names(tree, issues)

        # Check sheet pin consistency
        self._check_sheet_pins(tree, issues)

        return issues

    def _check_missing_files(self, node: HierarchyNode, issues: List[str]):
        """Check for missing sheet files."""
        if node.sheet_filename != "root.kicad_sch":
            filepath = self.project_path / node.sheet_filename
            if not filepath.exists():
                issues.append(f"Missing sheet file: {node.sheet_filename}")

        for child in node.children:
            self._check_missing_files(child, issues)

    def _check_duplicate_names(self, node: HierarchyNode, issues: List[str]):
        """Check for duplicate sheet names at the same level."""
        child_names = {}
        for child in node.children:
            if child.sheet_name in child_names:
                issues.append(
                    f"Duplicate sheet name '{child.sheet_name}' "
                    f"in {node.sheet_name}"
                )
            child_names[child.sheet_name] = True

            # Recursive check
            self._check_duplicate_names(child, issues)

    def _check_sheet_pins(self, node: HierarchyNode, issues: List[str]):
        """Check sheet pin consistency."""
        # Load the sheet that contains this node
        if node.parent_uuid:
            parent_schematic = self._get_schematic_containing_sheet(node.sheet_uuid)
            if parent_schematic:
                # Find the sheet symbol
                sheet = None
                for s in parent_schematic.sheets:
                    if s.uuid == node.sheet_uuid:
                        sheet = s
                        break

                if sheet:
                    # Load the sheet contents
                    sheet_schematic = self._load_sheet_schematic(sheet.filename)
                    if sheet_schematic:
                        # Check that hierarchical labels match sheet pins
                        self._validate_sheet_connections(sheet, sheet_schematic, issues)

        # Recursive check
        for child in node.children:
            self._check_sheet_pins(child, issues)

    def _get_schematic_containing_sheet(self, sheet_uuid: str) -> Optional[Schematic]:
        """Find the schematic that contains a sheet."""
        # Check root
        for sheet in self.root_schematic.sheets:
            if sheet.uuid == sheet_uuid:
                return self.root_schematic

        # Check cached schematics
        for schematic in self._schematic_cache.values():
            for sheet in schematic.sheets:
                if sheet.uuid == sheet_uuid:
                    return schematic

        return None

    def _validate_sheet_connections(
        self, sheet: Sheet, sheet_contents: Schematic, issues: List[str]
    ):
        """Validate connections between sheet pins and hierarchical labels."""
        # Get sheet pin names
        pin_names = {pin.name for pin in sheet.pins}

        # Get hierarchical label names
        hier_labels = set()
        for label in sheet_contents.labels:
            if label.label_type.value == "hierarchical_label":
                hier_labels.add(label.text)

        # Check for mismatches
        pins_without_labels = pin_names - hier_labels
        labels_without_pins = hier_labels - pin_names

        if pins_without_labels:
            issues.append(
                f"Sheet '{sheet.name}' has pins without hierarchical labels: "
                f"{', '.join(pins_without_labels)}"
            )

        if labels_without_pins:
            issues.append(
                f"Sheet '{sheet.name}' has hierarchical labels without pins: "
                f"{', '.join(labels_without_pins)}"
            )

    def find_circular_references(self) -> List[List[str]]:
        """Find all circular references in the hierarchy."""
        circular_refs = []

        def dfs(filename: str, path: List[str], visited: Set[str]):
            if filename in path:
                # Found circular reference
                cycle_start = path.index(filename)
                cycle = path[cycle_start:] + [filename]
                circular_refs.append(cycle)
                return

            if filename in visited:
                return

            visited.add(filename)
            path.append(filename)

            # Load schematic
            schematic = self._load_sheet_schematic(filename)
            if schematic:
                for sheet in schematic.sheets:
                    dfs(sheet.filename, path[:], visited)

        # Start from root
        visited = set()
        for sheet in self.root_schematic.sheets:
            dfs(sheet.filename, [], visited)

        return circular_refs

    def get_net_scope(self, net_name: str, sheet_uuid: str) -> str:
        """
        Determine the scope of a net in a specific sheet.

        Args:
            net_name: Name of the net
            sheet_uuid: UUID of the sheet

        Returns:
            Scope: "local", "global", or "hierarchical"
        """
        # Find the sheet
        tree = self.get_hierarchy_tree()
        node = tree.find_node(sheet_uuid)

        if not node:
            return "local"

        # Load sheet contents
        schematic = self._load_sheet_schematic(node.sheet_filename)
        if not schematic:
            return "local"

        # Check labels
        for label in schematic.labels:
            if label.text == net_name:
                if label.label_type.value == "global_label":
                    return "global"
                elif label.label_type.value == "hierarchical_label":
                    return "hierarchical"

        return "local"

    def analyze_hierarchy(self) -> HierarchyAnalysis:
        """Perform comprehensive hierarchy analysis."""
        tree = self.get_hierarchy_tree()

        # Count sheets and find max depth
        total_sheets = 0
        max_depth = 0

        def count_recursive(node: HierarchyNode):
            nonlocal total_sheets, max_depth
            total_sheets += 1
            max_depth = max(max_depth, node.depth)
            for child in node.children:
                count_recursive(child)

        count_recursive(tree)

        # Find circular references
        circular_refs = self.find_circular_references()

        # Count duplicate instances
        instance_counts = {}

        def count_instances(node: HierarchyNode):
            if node.sheet_filename != "root.kicad_sch":
                instance_counts[node.sheet_filename] = (
                    instance_counts.get(node.sheet_filename, 0) + 1
                )
            for child in node.children:
                count_instances(child)

        count_instances(tree)

        duplicate_instances = {
            filename: count for filename, count in instance_counts.items() if count > 1
        }

        # Find missing files
        missing_files = []

        def check_files(node: HierarchyNode):
            if node.sheet_filename != "root.kicad_sch":
                filepath = self.project_path / node.sheet_filename
                if not filepath.exists():
                    missing_files.append(node.sheet_filename)
            for child in node.children:
                check_files(child)

        check_files(tree)

        # Analyze net scope conflicts (simplified)
        net_scope_conflicts = []

        return HierarchyAnalysis(
            total_sheets=total_sheets,
            max_depth=max_depth,
            circular_references=circular_refs,
            duplicate_instances=duplicate_instances,
            missing_files=missing_files,
            net_scope_conflicts=net_scope_conflicts,
        )

    def get_instance_count(self, sheet_filename: str) -> int:
        """Get the number of instances of a sheet file."""
        count = 0

        def count_recursive(node: HierarchyNode):
            nonlocal count
            if node.sheet_filename == sheet_filename:
                count += 1
            for child in node.children:
                count_recursive(child)

        tree = self.get_hierarchy_tree()
        count_recursive(tree)

        return count
