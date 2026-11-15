"""Unit tests for sheet pin interface computation."""

from types import SimpleNamespace
from typing import List

from circuit_synth.kicad.schematic.sheet_interface import shared_net_names


def _circ(*names: str, as_dict: bool = False) -> SimpleNamespace:
    nets: List[SimpleNamespace] = [SimpleNamespace(name=n) for n in names]
    return SimpleNamespace(nets={n.name: n for n in nets} if as_dict else nets)


def test_net_in_parent_is_shared() -> None:
    assert shared_net_names(_circ("gnd", "local"), _circ("gnd"), []) == ["gnd"]


def test_net_in_sibling_is_shared_when_parent_has_no_nets() -> None:
    child = _circ("mid", "local")
    assert shared_net_names(child, _circ(), [_circ("mid")]) == ["mid"]


def test_net_in_sibling_is_shared_when_parent_has_other_nets() -> None:
    child = _circ("gnd", "mid", "local")
    sibling = _circ("gnd", "mid")
    assert shared_net_names(child, _circ("gnd"), [sibling]) == ["gnd", "mid"]


def test_internal_only_nets_are_not_shared() -> None:
    assert shared_net_names(_circ("a", "b"), _circ("x"), [_circ("y")]) == []


def test_dict_nets_supported() -> None:
    child = _circ("gnd", "b", as_dict=True)
    assert shared_net_names(child, _circ("gnd", as_dict=True), []) == ["gnd"]
