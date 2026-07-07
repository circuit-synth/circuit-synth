"""Compare two KiCad netlists for electrical equivalence (Stage 13, Phase C).

The SKiDL render and the circuit_synth generator produce *different-looking*
``.kicad_sch`` files (different placement, different auto-generated net names) but
should be *electrically identical*. This module compares two ``kicad-cli sch export
netlist`` outputs by the **partition of pins into nets** -- i.e. two pins are on the
same net in A iff they are on the same net in B -- rather than by net name (which is
allowed to differ). It also checks that each real component's ref/value/footprint
matches.

Power / no-connect pseudo-symbols (refs beginning with ``#``, e.g. ``#PWR01``) are
dropped by default: circuit_synth and SKiDL each synthesize their own power-symbol
instances, so comparing them by identity is meaningless -- what matters is that the
real component pins land in the same connectivity groups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Set, Tuple, Union

Pin = Tuple[str, str]  # (ref, pin)


# --------------------------------------------------------------------------- #
# Minimal s-expression parser (enough for KiCad netlists)
# --------------------------------------------------------------------------- #


def _tokenize(text: str) -> List[str]:
    tokens: List[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "()":
            tokens.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                    continue
                buf.append(text[j])
                j += 1
            tokens.append('"' + "".join(buf))  # tag string tokens with a leading quote
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


SExpr = Union[str, List["SExpr"]]


def _parse(tokens: List[str]) -> SExpr:
    """Parse the first complete s-expression; assumes a single root list."""
    pos = 0

    def parse_at(p: int) -> Tuple[SExpr, int]:
        tok = tokens[p]
        if tok == "(":
            lst: List[SExpr] = []
            p += 1
            while tokens[p] != ")":
                node, p = parse_at(p)
                lst.append(node)
            return lst, p + 1
        return tok, p + 1

    node, _ = parse_at(pos)
    return node


def _atom(x: SExpr) -> str:
    """Unwrap a token to its plain string value (dropping the string-tag)."""
    if isinstance(x, str):
        return x[1:] if x.startswith('"') else x
    return ""


def _find_all(node: SExpr, head: str) -> List[List[SExpr]]:
    """All direct-or-nested child lists whose first element is ``head``."""
    out: List[List[SExpr]] = []
    if isinstance(node, list):
        if node and _atom(node[0]) == head:
            out.append(node)
        for child in node:
            out.extend(_find_all(child, head))
    return out


def _field(node: List[SExpr], head: str) -> str:
    for child in node:
        if isinstance(child, list) and child and _atom(child[0]) == head:
            return _atom(child[1]) if len(child) > 1 else ""
    return ""


# --------------------------------------------------------------------------- #
# Netlist model
# --------------------------------------------------------------------------- #


@dataclass
class ParsedNetlist:
    # ref -> {"value": ..., "footprint": ...}
    components: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # list of nets, each a set of (ref, pin)
    nets: List[Set[Pin]] = field(default_factory=list)
    # net name -> set of (ref, pin) (names may be auto-generated / non-unique across
    # tools, so use ``nets``/``partition`` for equivalence and this only when the
    # human-facing net name matters, e.g. power detection / label matching)
    named_nets: Dict[str, Set[Pin]] = field(default_factory=dict)

    def partition(self, ignore_pseudo: bool = True) -> Set[FrozenSet[Pin]]:
        """The set of pin-groups (empty groups dropped)."""
        groups: Set[FrozenSet[Pin]] = set()
        for net in self.nets:
            pins = {
                (ref, pin)
                for (ref, pin) in net
                if not (ignore_pseudo and ref.startswith("#"))
            }
            if pins:
                groups.add(frozenset(pins))
        return groups

    def real_components(self, ignore_pseudo: bool = True) -> Dict[str, Dict[str, str]]:
        return {
            ref: v
            for ref, v in self.components.items()
            if not (ignore_pseudo and ref.startswith("#"))
        }


def parse_netlist(path: Union[str, Path]) -> ParsedNetlist:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    root = _parse(_tokenize(text))

    result = ParsedNetlist()

    for comp in _find_all(root, "comp"):
        ref = _field(comp, "ref")
        if not ref:
            continue
        result.components[ref] = {
            "value": _field(comp, "value"),
            "footprint": _field(comp, "footprint"),
        }

    for net in _find_all(root, "net"):
        pins: Set[Pin] = set()
        for node in _find_all(net, "node"):
            ref = _field(node, "ref")
            pin = _field(node, "pin")
            if ref and pin:
                pins.add((ref, pin))
        result.nets.append(pins)
        name = _field(net, "name")
        if name:
            result.named_nets[name] = pins

    return result


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #


@dataclass
class NetlistComparison:
    equivalent: bool
    messages: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.equivalent


def compare_netlists(
    netlist_a: Union[str, Path],
    netlist_b: Union[str, Path],
    *,
    ignore_pseudo: bool = True,
    check_footprint: bool = True,
) -> NetlistComparison:
    """Compare two netlist files by pin-partition + per-ref value/footprint.

    Net *names* are ignored; only the grouping of real-component pins into nets is
    compared. Returns a :class:`NetlistComparison` that is truthy iff equivalent and
    carries human-readable diffs.
    """
    a = parse_netlist(netlist_a)
    b = parse_netlist(netlist_b)
    msgs: List[str] = []

    # 1) Component set + attributes.
    ca = a.real_components(ignore_pseudo)
    cb = b.real_components(ignore_pseudo)
    only_a = set(ca) - set(cb)
    only_b = set(cb) - set(ca)
    if only_a:
        msgs.append(f"components only in A: {sorted(only_a)}")
    if only_b:
        msgs.append(f"components only in B: {sorted(only_b)}")
    for ref in sorted(set(ca) & set(cb)):
        if ca[ref]["value"] != cb[ref]["value"]:
            msgs.append(
                f"{ref} value differs: A={ca[ref]['value']!r} B={cb[ref]['value']!r}"
            )
        if check_footprint and ca[ref]["footprint"] != cb[ref]["footprint"]:
            msgs.append(
                f"{ref} footprint differs: "
                f"A={ca[ref]['footprint']!r} B={cb[ref]['footprint']!r}"
            )

    # 2) Connectivity partition.
    pa = a.partition(ignore_pseudo)
    pb = b.partition(ignore_pseudo)
    if pa != pb:
        for grp in sorted(pa - pb, key=lambda g: sorted(g)):
            msgs.append(f"net group only in A: {sorted(grp)}")
        for grp in sorted(pb - pa, key=lambda g: sorted(g)):
            msgs.append(f"net group only in B: {sorted(grp)}")

    return NetlistComparison(equivalent=not msgs, messages=msgs)
