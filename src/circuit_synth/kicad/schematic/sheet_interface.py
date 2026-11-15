"""
Determine which nets of a child subcircuit are exposed as sheet pins.

Shared by fresh schematic generation and hierarchical synchronization so that
both produce the same sheet interface for a given circuit hierarchy.
"""

from typing import Any, Iterable, List

# NOTE: nets shared only between a grandchild and a non-sibling sheet are not
# detected; the interface is computed one hierarchy level at a time.


def _net_list(circ: Any) -> List[Any]:
    nets = circ.nets
    return list(nets.values() if isinstance(nets, dict) else nets)


def shared_net_names(
    child_circ: Any, parent_circ: Any, sibling_circs: Iterable[Any]
) -> List[str]:
    """
    Return the sorted names of child nets that connect to the parent sheet.

    Args:
        child_circ: Circuit placed in the child sheet
        parent_circ: Circuit owning the sheet symbol
        sibling_circs: Other child circuits of ``parent_circ``

    Returns:
        Sorted list of net names to expose as sheet pins.
    """
    # Nets are identified by name across the hierarchy (as in the flat
    # netlist), so a child net is external if the parent or any sibling uses it
    external = {n.name for n in _net_list(parent_circ)}
    for sib in sibling_circs:
        external.update(n.name for n in _net_list(sib))

    return sorted({n.name for n in _net_list(child_circ) if n.name in external})
