"""Unit tests for SchematicWriter._is_net_hierarchical root-awareness (Stage 22.3).

Bug #9: a net used by a sheet's own children was flagged hierarchical regardless
of whether the sheet was the ROOT. A hierarchical label in the root binds to a
non-existent parent sheet pin -> ERC error. The root must use LOCAL labels to
join its child sheet pins; only a non-root sheet re-exports upward.

These call the method on a bare writer (``__new__`` -- no KiCad API init needed)
with lightweight fake circuits, so they stay pure unit tests.
"""

from circuit_synth.kicad.sch_gen.schematic_writer import SchematicWriter


class _Net:
    def __init__(self, name, is_power=False):
        self.name = name
        self.is_power = is_power


class _Circ:
    def __init__(self, name, nets=(), children=()):
        self.name = name
        self.nets = list(nets)
        self.child_instances = [{"sub_name": c} for c in children]


def _writer(circuit, all_subcircuits):
    w = SchematicWriter.__new__(SchematicWriter)
    w.circuit = circuit
    w.all_subcircuits = all_subcircuits
    return w


def _two_level():
    """root(child) with a net V5 shared between root and child."""
    v5_root = _Net("V5")
    v5_child = _Net("V5")
    root = _Circ("root", nets=[v5_root], children=["child"])
    child = _Circ("child", nets=[v5_child])
    return root, child, {"root": root, "child": child}


def test_root_net_used_by_child_is_local():
    """ROOT writer: a net used by a child gets a LOCAL label (not hierarchical)."""
    root, child, subs = _two_level()
    w = _writer(root, subs)
    assert w._is_net_hierarchical(root.nets[0]) is False


def test_child_net_shared_with_parent_is_hierarchical():
    """CHILD writer: a net shared with the parent keeps its hierarchical label."""
    root, child, subs = _two_level()
    w = _writer(child, subs)
    assert w._is_net_hierarchical(child.nets[0]) is True


def test_find_parent_circuit_root_vs_child():
    root, child, subs = _two_level()
    assert _writer(root, subs)._find_parent_circuit() is None
    assert _writer(child, subs)._find_parent_circuit() is root


def test_power_net_never_hierarchical_even_in_child():
    """Power nets are global (power symbols); never hierarchical, either sheet."""
    root, child, subs = _two_level()
    gnd = _Net("GND", is_power=True)
    child.nets.append(gnd)
    root.nets.append(_Net("GND", is_power=True))
    assert _writer(child, subs)._is_net_hierarchical(gnd) is False


def test_root_internal_net_is_local():
    """A net used by no child (purely internal to the root) stays local."""
    root, child, subs = _two_level()
    internal = _Net("ROOT_ONLY")
    root.nets.append(internal)
    assert _writer(root, subs)._is_net_hierarchical(internal) is False
