from typing import Dict, List, Optional, Set

from ._logger import context_logger
from .exception import ValidationError


class ReferenceManager:
    """
    Manages component references within a circuit hierarchy.
    Each circuit has its own ReferenceManager instance.
    """

    def __init__(self, initial_counters: Optional[dict[str, int]] = None):
        self._used_references: Set[str] = set()
        self._parent: Optional["ReferenceManager"] = None
        self._prefix_counters: dict[str, int] = (
            initial_counters.copy() if initial_counters else {}
        )
        self._children: List["ReferenceManager"] = []
        self._unnamed_net_counter: int = 1  # Counter for globally unique N$ names

    def set_parent(self, parent: Optional["ReferenceManager"]) -> None:
        """Set the parent reference manager and register with parent."""
        self._parent = parent
        if parent:
            parent._children.append(self)

    def get_root_manager(self) -> "ReferenceManager":
        """Get the root manager in the hierarchy."""
        current = self
        while current._parent is not None:
            current = current._parent
        return current

    def get_all_used_references(self) -> Set[str]:
        """Get all references used in this subtree."""
        refs = set(self._used_references)
        for child in self._children:
            refs.update(child.get_all_used_references())
        return refs

    def validate_reference(self, ref: str) -> bool:
        """
        Check if reference is available across entire hierarchy.
        """
        root = self.get_root_manager()
        all_refs = root.get_all_used_references()
        return ref not in all_refs

    def register_reference(self, ref: str) -> None:
        """Register a new reference if it's unique in the hierarchy."""
        if not self.validate_reference(ref):
            raise ValidationError(
                f"Reference {ref} already in use in circuit hierarchy"
            )

        self._used_references.add(ref)
        context_logger.debug(
            "Registered reference", component="REFERENCE_MANAGER", reference=ref
        )

    def set_initial_counters(self, counters: Dict[str, int]) -> None:
        """Set initial counters for reference generation."""
        for prefix, start_num in counters.items():
            if (
                prefix not in self._prefix_counters
                or self._prefix_counters[prefix] < start_num
            ):
                self._prefix_counters[prefix] = start_num
                context_logger.debug(
                    "Set initial counter for prefix",
                    component="REFERENCE_MANAGER",
                    prefix=prefix,
                    start_num=start_num,
                )

    def generate_next_reference(self, prefix: str) -> str:
        """Generate next available reference for a prefix."""
        # Always use the root manager for generating references
        root = self.get_root_manager()

        # If we're not the root, delegate to root
        if root is not self:
            return root.generate_next_reference(prefix)

        # We are the root, generate the reference
        if prefix not in self._prefix_counters:
            self._prefix_counters[prefix] = 1

        while True:
            candidate = f"{prefix}{self._prefix_counters[prefix]}"
            self._prefix_counters[prefix] += 1

            if self.validate_reference(candidate):
                self.register_reference(candidate)
                return candidate

    def generate_next_unnamed_net_name(self) -> str:
        """Generates the next globally unique name for unnamed nets (e.g., N$1)."""
        root = self.get_root_manager()
        # Ensure the counter is incremented on the root manager
        name = f"N${root._unnamed_net_counter}"
        root._unnamed_net_counter += 1
        context_logger.debug(
            "Generated unnamed net name", component="REFERENCE_MANAGER", net_name=name
        )
        return name

    def clear(self) -> None:
        """
        Clear all registered references and counters.
        Also break parent/child relationships.
        """
        # Clear local state
        self._used_references.clear()
        self._prefix_counters.clear()

        # Detach from parent
        if self._parent:
            if self in self._parent._children:
                self._parent._children.remove(self)
            self._parent = None

        # Detach children
        for child in self._children:
            child._parent = None
        self._children.clear()
