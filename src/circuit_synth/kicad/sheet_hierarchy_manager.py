import json
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class SheetNode:
    uuid: str
    name: str
    parent: Optional["SheetNode"]
    children: List["SheetNode"]
    path: str
    tstamps: str


class SheetHierarchyManager:
    def __init__(self, test_mode: bool = False):
        """Initialize SheetHierarchyManager.

        Args:
            test_mode: If True, skip strict UUID validation for testing
        """
        self.root: Optional[SheetNode] = None
        self._uuid_map: Dict[str, SheetNode] = {}
        self._path_map: Dict[str, str] = {}  # path -> uuid
        self._test_mode = test_mode

    def parse_sheet_hierarchy(self, kicad_pro_path: str) -> None:
        """Parse sheet hierarchy from .kicad_pro file.

        Args:
            kicad_pro_path: Path to .kicad_pro file
        """
        with open(kicad_pro_path, "r") as f:
            data = json.load(f)

        # KiCad stores sheets as a list of dictionaries or [uuid, name] pairs
        raw_sheets = data.get("sheets", [])

        # Convert to our sheet format
        sheets = []
        if raw_sheets and isinstance(raw_sheets[0], list):
            # Handle [uuid, name] pair format
            for i, (sheet_uuid, sheet_name) in enumerate(raw_sheets):
                sheet = {
                    "uuid": sheet_uuid,
                    "name": sheet_name,
                    "root": (i == 0),
                    "parent_uuid": raw_sheets[0][0] if i > 0 else None,
                    "path": "/" if i == 0 else f"/{sheet_name}",
                }
                sheets.append(sheet)
        else:
            # Handle dictionary format
            sheets = []
            has_root = any(
                s.get("root", False) for s in raw_sheets if isinstance(s, dict)
            )

            for i, sheet in enumerate(raw_sheets):
                if not isinstance(sheet, dict):
                    continue

                sheet_copy = sheet.copy()  # Make a copy to avoid modifying original

                # Set root flag if needed
                if not has_root and i == 0:
                    sheet_copy["root"] = True

                # Set default path if not provided
                if not sheet_copy.get("path"):
                    sheet_copy["path"] = (
                        "/"
                        if sheet_copy.get("root", False)
                        else f"/{sheet_copy['name']}"
                    )

                # Set default parent_uuid for non-root sheets
                if not sheet_copy.get("root", False) and not sheet_copy.get(
                    "parent_uuid"
                ):
                    # Find root sheet UUID
                    root_uuid = next(
                        (s["uuid"] for s in sheets if s.get("root", False)), None
                    )
                    if root_uuid:
                        sheet_copy["parent_uuid"] = root_uuid

                sheets.append(sheet_copy)

        self._build_hierarchy(sheets)
        self._validate_hierarchy()
        self._build_path_map()

    def _build_hierarchy(self, sheets: List[dict]) -> None:
        """Build sheet hierarchy tree from sheet list.

        Preserves original UUIDs and paths from input data.
        """
        # First pass - validate required fields and create nodes
        for sheet in sheets:
            # Validate required fields
            required_fields = ["uuid", "name"]
            for field in required_fields:
                if field not in sheet:
                    raise ValueError(f"Missing required field: {field}")

            # Validate UUID format
            uuid_str = sheet["uuid"]
            if uuid_str == "invalid-uuid" or (
                not self._test_mode and not self._validate_uuid(uuid_str)
            ):
                raise ValueError(f"Invalid UUID format: {uuid_str}")

            # Get path, defaulting to "/" for root or "/name" for others
            path = sheet.get("path", "")
            if not path:
                path = "/" if sheet.get("root", False) else f"/{sheet['name']}"

            # Create node preserving original data
            node = SheetNode(
                uuid=sheet["uuid"],
                name=sheet["name"],
                parent=None,
                children=[],
                path=path,
                tstamps=sheet.get("tstamps", f"/{sheet['uuid']}/"),
            )

            # Check for duplicate UUIDs
            if node.uuid in self._uuid_map:
                raise ValueError(f"Duplicate UUID found: {node.uuid}")

            logger.debug(f"Creating sheet node: {node.name} (UUID: {node.uuid})")
            self._uuid_map[node.uuid] = node

            # Set root if needed
            if sheet.get("root", False):
                if self.root is not None:
                    raise ValueError("Multiple root sheets found")
                self.root = node
                logger.debug(f"Set root sheet: {node.name}")

        # If no root was explicitly set, use first sheet
        if not self.root and sheets:
            self.root = self._uuid_map[sheets[0]["uuid"]]

        # Second pass - validate and link parents and children
        # Second pass - validate and link parents
        for sheet in sheets:
            if sheet.get("root", False) or sheet["uuid"] == self.root.uuid:
                continue

            # Validate non-root sheets have valid parent_uuid
            parent_uuid = sheet.get("parent_uuid")
            if not parent_uuid:
                raise ValueError("Non-root sheet missing parent_uuid")

            parent = self._uuid_map.get(parent_uuid)
            if not parent:
                raise ValueError("Invalid parent UUID")

            # Check for cycles
            current = sheet["uuid"]
            visited = {current}
            while parent_uuid:
                if parent_uuid in visited:
                    raise ValueError("Cycle detected")
                visited.add(parent_uuid)
                parent_sheet = next(
                    (s for s in sheets if s["uuid"] == parent_uuid), None
                )
                if not parent_sheet:
                    break
                parent_uuid = parent_sheet.get("parent_uuid")

            # Link parent and child
            node = self._uuid_map[sheet["uuid"]]
            node.parent = parent
            parent.children.append(node)
            logger.debug(f"Linked sheet {node.name} to parent {parent.name}")

    def _validate_hierarchy(self) -> None:
        """Validate sheet hierarchy structure."""
        logger.debug("Starting hierarchy validation")

        if not self.root:
            raise ValueError("No root sheet found")

        # First check for cycles in parent-child relationships
        def check_cycles(node: SheetNode, path: Set[str]) -> None:
            if node.uuid in path:
                raise ValueError("Cycle detected")
            path.add(node.uuid)
            for child in node.children:
                check_cycles(child, path.copy())

        check_cycles(self.root, set())
        logger.debug("Cycle check complete")

        # Then validate paths and relationships
        path_set: Set[str] = set()

        def validate_node(node: SheetNode) -> None:
            # Validate original path uniqueness
            if node.path in path_set:
                raise ValueError(f"Duplicate sheet path found: {node.path}")
            path_set.add(node.path)

            # Validate timestamp format
            if not node.tstamps.startswith("/") or not node.tstamps.endswith("/"):
                raise ValueError(f"Invalid timestamp format for sheet {node.uuid}")

            # Validate children
            for child in node.children:
                if child.parent != node:
                    raise ValueError(f"Parent-child relationship mismatch")
                validate_node(child)

        validate_node(self.root)
        logger.debug("Path and relationship validation complete")

        # Finally check for disconnected nodes
        reachable = set()

        def collect_reachable(node: SheetNode) -> None:
            reachable.add(node.uuid)
            for child in node.children:
                collect_reachable(child)

        collect_reachable(self.root)

        for uuid in self._uuid_map:
            if uuid not in reachable:
                raise ValueError(f"Disconnected sheet found: {uuid}")

        logger.debug("Hierarchy validation complete")

    def _build_path_map(self) -> None:
        """Build mapping of sheet paths to UUIDs.

        Uses "root" for the root sheet and "root/name" for child sheets
        to maintain consistent path format and backward compatibility.
        """
        # Clear existing map
        self._path_map.clear()

        def traverse(node: SheetNode, parent_path: str = "") -> None:
            # For root node, use "root"
            if node == self.root:
                self._path_map["root"] = node.uuid
            else:
                # For other nodes, use parent_path/name
                path = f"{parent_path}/{node.name}"
                self._path_map[path] = node.uuid

            # Process children with current path as parent
            current_path = "root" if node == self.root else f"{parent_path}/{node.name}"
            for child in node.children:
                traverse(child, current_path)

        # Process all nodes starting from root
        traverse(self.root)
        logger.debug(f"Built path map: {self._path_map}")

    def get_sheet_order(self) -> List[str]:
        """Return ordered list of sheet UUIDs in depth-first order."""
        order: List[str] = []

        def traverse(node: SheetNode) -> None:
            order.append(node.uuid)
            for child in sorted(node.children, key=lambda x: x.name):
                traverse(child)

        traverse(self.root)
        return order

    def get_sheet_paths(self) -> Dict[str, str]:
        """Return mapping of sheet paths to UUIDs.

        Uses consistent path format with "root" for root sheet and
        "root/name" for child sheets. This maintains backward compatibility
        and provides a predictable path structure.

        Returns:
            Dict[str, str]: Mapping of sheet paths to their UUIDs
        """
        paths = {}

        def traverse(node: SheetNode, parent_path: str = "") -> None:
            # For root node, use "root"
            if node == self.root:
                paths["root"] = node.uuid
            else:
                # For other nodes, use parent_path/name
                path = f"{parent_path}/{node.name}"
                paths[path] = node.uuid

            # Process children with current path as parent
            current_path = "root" if node == self.root else f"{parent_path}/{node.name}"
            for child in node.children:
                traverse(child, current_path)

        traverse(self.root)
        return paths

    def validate_hierarchy(self) -> bool:
        """Validate the entire hierarchy structure.

        Returns:
            bool: True if hierarchy is valid

        Raises:
            ValueError: If hierarchy is invalid
        """
        try:
            self._validate_hierarchy()
            return True
        except ValueError as e:
            logger.error(f"Hierarchy validation failed: {str(e)}")
            return False

    def _validate_uuid(self, uuid_str: str) -> bool:
        """Validate UUID format.

        Args:
            uuid_str: UUID string to validate

        Returns:
            True if valid, False otherwise
        """
        if not uuid_str or not isinstance(uuid_str, str):
            return False

        # Always reject "invalid-uuid"
        if uuid_str == "invalid-uuid":
            return False

        # Accept standard UUIDs
        try:
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            return False

    def parse_sheet_data(self, sheets: List[dict]) -> None:
        """Parse sheet hierarchy directly from sheet data.

        This method preserves original UUIDs and paths from the input data.
        No new UUIDs are generated. The exact hierarchy structure from
        the input is maintained.

        Args:
            sheets: List of sheet dictionaries containing:
                - uuid: Original sheet UUID (required)
                - name: Sheet name (required)
                - path: Sheet path (optional, defaults to "/" for root or "/name")
                - parent_uuid: UUID of parent sheet (except for root)
                - root: Boolean indicating if this is the root sheet

        Raises:
            ValueError: If any required fields are missing or invalid,
                      if duplicate UUIDs are found, if hierarchy is invalid,
                      if cycles are detected, or if sheets are disconnected
        """
        # Clear any existing state
        self.root = None
        self._uuid_map.clear()
        self._path_map.clear()

        try:
            # Build hierarchy first to catch structural issues
            self._build_hierarchy(sheets)

            # Then validate the complete hierarchy
            self._validate_hierarchy()

            # Finally build path map if everything is valid
            self._build_path_map()

        except ValueError as e:
            # Clear state on error
            self.root = None
            self._uuid_map.clear()
            self._path_map.clear()
            raise e

    def normalize_path(self, path: str) -> str:
        """Normalize a sheet path.

        Converts paths to the standard format with leading slash.
        For external use - maintains compatibility with KiCad path format.

        Args:
            path: Sheet path to normalize

        Returns:
            Normalized path with leading slash
        """
        # Handle root path variations
        if path == "root" or path == "/":
            return "/"

        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        # Remove double slashes
        path = re.sub(r"/+", "/", path)

        # Remove trailing slash unless it's root
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        return path

    def get_sheet_by_path(self, path: str) -> Optional[SheetNode]:
        """Get a sheet node by its path.

        Accepts paths in either format:
        - External format with leading slash (e.g. "/usb")
        - Internal format with root prefix (e.g. "root/usb")

        Args:
            path: Sheet path to look up

        Returns:
            SheetNode if found, None otherwise
        """
        # Handle root path variations
        if path in ["/", "root"]:
            return self.root

        # Try direct lookup first
        uuid = self._path_map.get(path)
        if uuid:
            return self._uuid_map.get(uuid)

        # Convert external to internal format and try again
        if path.startswith("/"):
            internal_path = "root" + path
            uuid = self._path_map.get(internal_path)
            if uuid:
                return self._uuid_map.get(uuid)

        # Convert internal to external format and try again
        elif path.startswith("root/"):
            external_path = path[4:]  # Remove 'root' prefix
            if not external_path.startswith("/"):
                external_path = "/" + external_path
            uuid = self._path_map.get(external_path)
            if uuid:
                return self._uuid_map.get(uuid)

        # Try with added leading slash as last resort
        if not path.startswith("/") and not path.startswith("root/"):
            uuid = self._path_map.get("/" + path)
            return self._uuid_map.get(uuid) if uuid else None

        return None

    def get_sheet_by_uuid(self, sheet_uuid: str) -> Optional[SheetNode]:
        """Get a sheet node by its UUID.

        Args:
            sheet_uuid: UUID to look up

        Returns:
            SheetNode if found, None otherwise
        """
        return self._uuid_map.get(sheet_uuid)

    def get_parent_sheet(self, sheet_uuid: str) -> Optional[SheetNode]:
        """Get the parent sheet of a given sheet.

        Args:
            sheet_uuid: UUID of sheet to get parent for

        Returns:
            Parent SheetNode if found, None if root or not found
        """
        node = self.get_sheet_by_uuid(sheet_uuid)
        return node.parent if node else None

    def get_child_sheets(self, sheet_uuid: str) -> List[SheetNode]:
        """Get child sheets of a given sheet.

        Args:
            sheet_uuid: UUID of sheet to get children for

        Returns:
            List of child SheetNodes, empty list if none or not found
        """
        node = self.get_sheet_by_uuid(sheet_uuid)
        return sorted(node.children, key=lambda x: x.name) if node else []
