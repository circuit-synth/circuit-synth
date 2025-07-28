"""
FILE: json_to_python_project.py

Generates a Python project from Circuit-Synth JSON, with:
  - LCA-based net ownership
  - Net name unification
  - Descendant-based net imports
  - Pin name fix: uses pin_obj.num (e.g. "A1") in generated code
  - Reference conflict prevention via scanning
"""

import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from ..core.circuit import Circuit
from ..core.component import Component
from ..core.exception import CircuitSynthError
from ..core.net import Net
from ..io.json_loader import load_circuit_from_dict, load_circuit_from_json_file

logger = logging.getLogger(__name__)


def circuit_synth_json_to_python_project(
    input_json: Union[str, Dict], output_dir: str
) -> Circuit:
    """
    Main entry point: convert hierarchical JSON into a Python code project.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1) First scan JSON for existing references BEFORE loading
    json_data = None
    if isinstance(input_json, str):
        with open(input_json, "r") as f:
            json_data = json.load(f)
    elif isinstance(input_json, dict):
        json_data = input_json
    else:
        raise TypeError("input_json must be a filename or dict.")

    highest_refs = _scan_json_references(json_data)

    # 2) Load circuit
    root_circuit = _phase1_load_circuit(input_json)

    # 3) Clear the reference manager after loading
    # This is needed because loading the JSON creates components with explicit refs
    # that get registered, but we don't want those registrations when generating Python
    _clear_all_reference_managers(root_circuit)

    # 4) Rename top-level => "root_circuit"
    circuit_name_map = {}
    used_sanitized = set()
    _phase2_rename_circuits(
        root_circuit, circuit_name_map, used_sanitized, is_top_level=True
    )
    root_circuit._circuit_name_map = circuit_name_map

    # 5) Set initial counters on the root circuit's reference manager
    # Add safety margin to avoid conflicts
    initial_counters = {}
    for prefix, highest in highest_refs.items():
        initial_counters[prefix] = highest + 100
    if initial_counters:
        root_circuit._reference_manager.set_initial_counters(initial_counters)
        logger.info("Set initial reference counters: %s", initial_counters)

    # 6) Repeated parts => common_parts.py
    common_map = _phase3_find_repeated_components(root_circuit)
    if common_map:
        _phase3_write_common_parts(common_map, out_path, highest_refs)

    # 6) LCA net ownership
    net_usage_map = _phase4_gather_net_usage(root_circuit)
    net_owner_map = _phase4_compute_net_owners_lca(root_circuit, net_usage_map)
    _phase4_assign_nets_to_circuits(root_circuit, net_owner_map)

    # 7) Net unification
    _phase5_unify_net_names(root_circuit)

    # 8) Imported nets for each circuit
    _phase6_compute_imported_nets_with_descendants(root_circuit, net_owner_map)

    # 9) Write circuit .py files (all circuits in circuits/ folder)
    circuit_to_filename = {}
    _phase7_write_all_circuits_organized(
        root_circuit, out_path, common_map, circuit_to_filename
    )

    # 10) Write main.py
    _phase8_generate_main_py(
        root_circuit, out_path, circuit_to_filename, highest_refs=highest_refs
    )

    return root_circuit


# -----------------------------------------------------------------------
# PHASE 1: Load
# -----------------------------------------------------------------------


def _phase1_load_circuit(input_json: Union[str, Dict]) -> Circuit:
    if isinstance(input_json, str):
        p = Path(input_json)
        if not p.is_file():
            raise FileNotFoundError(f"JSON file {p} not found.")
        logger.info("Loading circuit from JSON file: %s", p)
        return load_circuit_from_json_file(p)
    elif isinstance(input_json, dict):
        logger.info("Loading circuit from in-memory JSON data.")
        return load_circuit_from_dict(input_json)
    else:
        raise TypeError("input_json must be a filename or dict.")


# -----------------------------------------------------------------------
# PHASE 2: Rename circuits
# -----------------------------------------------------------------------


def _phase2_rename_circuits(
    c: Circuit, name_map: Dict[Circuit, str], used: Set[str], is_top_level: bool
):
    import re

    def sanitize(n: str) -> str:
        tmp = re.sub(r"[^0-9A-Za-z_]+", "_", n.strip())
        if not tmp:
            tmp = "circuit"
        if tmp[0].isdigit():
            tmp = "_" + tmp
        return tmp

    old_name = c.name.strip()
    if is_top_level:
        final = "root_circuit"
        logger.debug("Top-level circuit '%s' => '%s'", old_name, final)
    else:
        base = sanitize(old_name)
        final = base
        i = 2
        while final in used:
            final = f"{base}_{i}"
            i += 1

    used.add(final)
    name_map[c] = final
    c._sanitized_name = final

    for child in c._subcircuits:
        _phase2_rename_circuits(child, name_map, used, is_top_level=False)


# -----------------------------------------------------------------------
# NEW: Scan for explicit references
# -----------------------------------------------------------------------


def _scan_json_references(json_data: dict) -> Dict[str, int]:
    """Scan JSON data for highest explicit reference numbers"""
    highest_refs = defaultdict(int)

    def scan_data(data):
        if isinstance(data, dict):
            # Check for components
            components = data.get("components", {})
            for ref, comp_data in components.items():
                # Extract prefix and number from reference
                match = re.match(r"^([A-Z]+)(\d+)$", ref)
                if match:
                    prefix = match.group(1)
                    num = int(match.group(2))
                    highest_refs[prefix] = max(highest_refs[prefix], num)

            # Recurse into subcircuits
            subcircuits = data.get("subcircuits", [])
            for subcircuit in subcircuits:
                scan_data(subcircuit)

    scan_data(json_data)
    logger.info("Scanned JSON for explicit references: %s", dict(highest_refs))
    return dict(highest_refs)


# -----------------------------------------------------------------------
# Helper: Clear reference managers
# -----------------------------------------------------------------------


def _clear_all_reference_managers(root: Circuit):
    """Clear all reference managers in the circuit hierarchy"""

    def clear_circuit(c: Circuit):
        c._reference_manager.clear()
        for subcircuit in c._subcircuits:
            clear_circuit(subcircuit)

    clear_circuit(root)
    logger.info("Cleared all reference managers in circuit hierarchy")


# -----------------------------------------------------------------------
# PHASE 3: Repeated parts => common_parts.py
# -----------------------------------------------------------------------


def _phase3_find_repeated_components(root: Circuit) -> Dict[Tuple[str, str, str], str]:
    from collections import Counter

    all_keys = []

    def gather(c: Circuit):
        for comp in c._components.values():
            k = (comp.symbol, comp.value or "", comp.footprint or "")
            all_keys.append(k)
        for sc in c._subcircuits:
            gather(sc)

    gather(root)
    counts = Counter(all_keys)
    repeated = [k for k, cnt in counts.items() if cnt > 1]

    result = {}
    for sym, val, fpt in repeated:
        nm = _make_common_varname(sym, val, fpt)
        i = 2
        tmp = nm
        while tmp in result.values():
            tmp = f"{nm}_{i}"
            i += 1
        result[(sym, val, fpt)] = tmp
    return result


def _make_common_varname(sym: str, val: str, fpt: str) -> str:
    import re

    prefix = "X"
    low = sym.lower()
    if "device:r" in low:
        prefix = "R"
    elif "device:c" in low:
        prefix = "C"
    elif "diode:" in low or "led" in low:
        prefix = "D"
    elif "regulator_linear" in low or "esp" in low or "sensor_" in low:
        prefix = "U"

    def sanitize(x: str) -> str:
        t = re.sub(r"[^0-9A-Za-z_]+", "_", x.strip())
        if not t:
            t = "part"
        if t[0].isdigit():
            t = "_" + t
        return t

    vs = sanitize(val)
    fs = sanitize(fpt)
    return f"{prefix}__{vs}_{fs}".rstrip("_")


def _phase3_write_common_parts(
    d: Dict[Tuple[str, str, str], str], outp: Path, highest_refs: Dict[str, int]
):
    fp = outp / "common_parts.py"
    logger.info("Writing common_parts.py => %s", fp)

    # Add safety margin to highest references
    start_refs = {
        "C": highest_refs.get("C", 0) + 100,
        "R": highest_refs.get("R", 0) + 100,
        "L": highest_refs.get("L", 0) + 100,
        "D": highest_refs.get("D", 0) + 100,
        "Q": highest_refs.get("Q", 0) + 100,
        "U": highest_refs.get("U", 0) + 100,
        "J": highest_refs.get("J", 0) + 100,
        "TP": highest_refs.get("TP", 0) + 100,
        "NT": highest_refs.get("NT", 0) + 100,
        "X": highest_refs.get("X", 0) + 100,  # Add X prefix for MOSFETs
    }

    # Track counters for each prefix
    ref_counters = defaultdict(int)

    with open(fp, "w", encoding="utf-8") as f:
        f.write('"""Auto-generated common parts - factory functions."""\n')
        f.write("import logging\n")
        f.write("from circuit_synth import Component\n\n")
        f.write("logger = logging.getLogger(__name__)\n")
        f.write("logger.debug('Importing common_parts...')\n\n")
        f.write("# Reference starting points to avoid conflicts:\n")
        for prefix, start in start_refs.items():
            if start > 100:  # Only show if there are actual explicit refs
                f.write(f"# {prefix}: starting from {prefix}{start}\n")
        f.write("\n")

        for (sym, val, fpt), varnm in d.items():
            vs = f"'{val}'" if val else "None"
            fs = f"'{fpt}'" if fpt else "None"

            # Determine appropriate ref prefix based on symbol
            ref_prefix = "U"  # Default
            if "Capacitor" in sym or ":C" in sym or ":C_" in sym:
                ref_prefix = "C"
            elif "Resistor" in sym or ":R" in sym or ":R_" in sym:
                ref_prefix = "R"
            elif "Inductor" in sym or ":L" in sym or ":L_" in sym:
                ref_prefix = "L"
            elif "Diode" in sym or "LED" in sym or ":D" in sym:
                ref_prefix = "D"
            elif "Transistor" in sym or ":Q" in sym:
                ref_prefix = "Q"
            elif "Connector" in sym or "TestPoint" in sym:
                ref_prefix = "TP" if "TestPoint" in sym else "J"
            elif "NetTie" in sym:
                ref_prefix = "NT"
            elif "MOSFET" in sym.upper() or "FET" in sym.upper() or "IAUC60N04" in sym:
                # Handle MOSFETs - they should have X prefix
                ref_prefix = "X"

            # Get starting number for this prefix
            start_num = start_refs.get(ref_prefix, 100)

            f.write(f"def {varnm}():\n")
            f.write(f'    """Factory function for {sym}"""\n')
            f.write(f"    return Component(\n")
            f.write(f"        symbol='{sym}',\n")
            f.write(
                f"        ref='{ref_prefix}',  # prefix only - number assigned by circuit starting from {ref_prefix}{start_num}\n"
            )
            f.write(f"        value={vs},\n")
            f.write(f"        footprint={fs}\n")
            f.write("    )\n\n")


# -----------------------------------------------------------------------
# PHASE 4: LCA net ownership
# -----------------------------------------------------------------------


def _phase4_gather_net_usage(root: Circuit) -> Dict[str, Set[Circuit]]:
    usage = defaultdict(set)

    def walk(c: Circuit):
        for net_name in c._nets:
            usage[net_name].add(c)
        for sc in c._subcircuits:
            walk(sc)

    walk(root)
    return dict(usage)


def _phase4_compute_net_owners_lca(
    root: Circuit, usage: Dict[str, Set[Circuit]]
) -> Dict[str, Circuit]:
    ancestry = {}

    def get_ancestry(c: Circuit) -> List[Circuit]:
        if c in ancestry:
            return ancestry[c]
        path = []
        found = False

        def dfs(cur: Circuit, path_so_far: List[Circuit]):
            nonlocal found
            if cur is c:
                path.extend(path_so_far + [cur])
                found = True
                return
            for child in cur._subcircuits:
                if not found:
                    dfs(child, path_so_far + [cur])

        dfs(root, [])
        ancestry[c] = path
        return path

    def find_lca(circuits: List[Circuit]) -> Circuit:
        if not circuits:
            return root
        paths = [get_ancestry(x) for x in circuits]
        min_len = min(len(p) for p in paths)
        lca = root
        for i in range(min_len):
            candidate = paths[0][i]
            if all(i < len(p) and p[i] is candidate for p in paths):
                lca = candidate
            else:
                break
        return lca

    owners = {}
    for net, used_by in usage.items():
        if not used_by:
            owners[net] = root
        elif len(used_by) == 1:
            owners[net] = list(used_by)[0]
        else:
            lca = find_lca(list(used_by))
            owners[net] = lca
        logger.debug(
            "Net '%s' used by %s => owner: %s",
            net,
            [c.name for c in used_by],
            owners[net].name,
        )
    return owners


def _phase4_assign_nets_to_circuits(root: Circuit, net_owner_map: Dict[str, Circuit]):
    def initall(c: Circuit):
        c._owned_netnames = set()
        for sc in c._subcircuits:
            initall(sc)

    initall(root)

    for net, owner in net_owner_map.items():
        owner._owned_netnames.add(net)
        logger.debug("Assigning net '%s' to circuit '%s'", net, owner.name)


# -----------------------------------------------------------------------
# PHASE 5: unify net names
# -----------------------------------------------------------------------


def _phase5_unify_net_names(root: Circuit):
    net_obj_to_canon = {}

    def gather(c: Circuit):
        for n in c._owned_netnames:
            if n in c._nets:
                net_obj = c._nets[n]
                net_obj_to_canon[net_obj] = n
        for sc in c._subcircuits:
            gather(sc)

    gather(root)

    def rename(c: Circuit):
        new_map = {}
        for old_name, net_obj in list(c._nets.items()):
            canon = net_obj_to_canon.get(net_obj, old_name)
            net_obj.name = canon
            if canon not in new_map:
                new_map[canon] = net_obj
            if old_name != canon and old_name in c._nets:
                del c._nets[old_name]
        c._nets = new_map

        # rename pin net names
        for comp in c._components.values():
            for p in comp._pins.values():
                if p.net in net_obj_to_canon:
                    p.net.name = net_obj_to_canon[p.net]
        for sc in c._subcircuits:
            rename(sc)

    rename(root)


# -----------------------------------------------------------------------
# PHASE 6: Compute "imported_nets" with descendant usage
# -----------------------------------------------------------------------


def _phase6_compute_imported_nets_with_descendants(
    root: Circuit, net_owner_map: Dict[str, Circuit]
):
    """
    For each circuit c, figure out which nets c must import from its parent.
      - c uses or child uses net
      - net is owned by an ancestor of c
      - c is not top-level
    """

    def is_ancestor(a: Circuit, b: Circuit) -> bool:
        # climb from b up to root, see if we find a
        cur = b
        while cur is not None:
            if cur is a:
                return True
            cur = cur._parent
        return False

    def gather(c: Circuit) -> Set[str]:
        imports_from_children = set()
        for child in c._subcircuits:
            imports_from_children |= gather(child)

        if c._parent is None:
            c._imported_netnames = set()
            return set()

        # direct usage: c._nets that c doesn't own
        direct_usage = {n for n in c._nets if n not in c._owned_netnames}

        needed = direct_usage | imports_from_children
        final_imports = set()

        for net_name in needed:
            owner = net_owner_map[net_name]
            # c only imports if net is owned by an ancestor
            if owner is not c and is_ancestor(owner, c._parent):
                final_imports.add(net_name)

        c._imported_netnames = final_imports
        return final_imports

    gather(root)


# -----------------------------------------------------------------------
# PHASE 7: Write .py files
# -----------------------------------------------------------------------


def _phase7_write_all_circuits_organized(
    root: Circuit,
    out: Path,
    common_map: Dict[Tuple[str, str, str], str],
    circuit_to_file: Dict[Circuit, str],
):
    """
    Write all circuit files organized in circuits/ folder.
    """
    # Create circuits subdirectory
    circuits_dir = out / "circuits"
    circuits_dir.mkdir(exist_ok=True)

    # Create circuits/__init__.py
    init_file = circuits_dir / "__init__.py"
    with open(init_file, "w", encoding="utf-8") as f:
        f.write('"""Circuit modules"""\n')

    # Write all circuits in standard format
    _write_all_circuits_standard(root, circuits_dir, common_map, circuit_to_file)


def _write_all_circuits_standard(
    root: Circuit,
    circuits_dir: Path,
    common_map: Dict[Tuple[str, str, str], str],
    circuit_to_file: Dict[Circuit, str],
):
    """
    Write all circuits to circuits/ folder.
    """

    def rec(c: Circuit, parent: Optional[Circuit]):
        nm = c._sanitized_name
        fpy = circuits_dir / (nm + ".py")
        circuit_to_file[c] = f"circuits/{nm}.py"
        logger.info(
            "Writing circuit file: circuits/%s => circuit name: '%s'", fpy.name, c.name
        )
        code = _generate_circuit_py_for_circuits_folder(c, parent, common_map)
        with open(fpy, "w", encoding="utf-8") as fh:
            fh.write(code)

        for sc in c._subcircuits:
            rec(sc, c)

    rec(root, None)


def _generate_circuit_py_for_circuits_folder(
    c: Circuit, parent: Optional[Circuit], common_map: Dict[Tuple[str, str, str], str]
) -> str:
    """
    Generate Python code for a circuit in the circuits/ folder.
    Uses relative imports for common_parts.
    """
    lines = []
    lines.append(f'"""Auto-generated file for circuit: {c.name}"""')
    lines.append("import logging")
    lines.append("import os")
    lines.append("from pathlib import Path")
    lines.append("from circuit_synth import circuit, Net, Component")

    used_common = set()
    for comp in c._components.values():
        k = (comp.symbol, comp.value or "", comp.footprint or "")
        if k in common_map:
            used_common.add(common_map[k])
    if used_common:
        lines.append(f"from common_parts import {', '.join(sorted(used_common))}")
    lines.append("")
    lines.append("logger = logging.getLogger(__name__)")
    lines.append("")

    build_func = f"build_{c._sanitized_name}"
    imported = sorted(list(getattr(c, "_imported_netnames", set())))
    param_str = ", ".join(_sanitize_for_param(n) for n in imported)

    lines.append("@circuit")
    lines.append(f"def {build_func}({param_str}):")
    lines.append(
        f'    logger.info("Entering {build_func} with imported nets: %s", {imported})'
    )

    owned = sorted(list(getattr(c, "_owned_netnames", set())))
    if owned:
        lines.append("    # Define local (owned) nets:")
        for net_name in owned:
            lines.append(f"    {_sanitize_for_param(net_name)} = Net()")

    lines.append("")
    lines.append("    # Define components:")
    for comp in c._components.values():
        k = (comp.symbol, comp.value or "", comp.footprint or "")
        if k in common_map:
            common_name = common_map[k]
            lines.append(f"    {comp.ref} = {common_name}()")
        else:
            lines.append(f"    {comp.ref} = Component(")
            lines.append(f"        symbol='{comp.symbol}',")
            lines.append(f"        value='{comp.value}',")
            lines.append(f"        footprint='{comp.footprint}',")
            lines.append(f"        ref='{comp.ref}'")
            lines.append("    )")

    # Generate connections
    lines.append("")
    lines.append("    # Define connections:")
    for net in c._nets.values():
        net_var = _sanitize_for_param(net.name)
        for pin in net._pins:
            comp_ref = pin._component.ref
            pin_ref = pin.num
            lines.append(f"    {net_var} += {comp_ref}['{pin_ref}']")

    # Generate subcircuit calls
    if c._subcircuits:
        lines.append("")
        lines.append("    # Call subcircuits:")
        for i, child in enumerate(c._subcircuits):
            child_func = f"build_{child._sanitized_name}"
            child_imports = sorted(list(getattr(child, "_imported_netnames", set())))
            param_call = ", ".join(_sanitize_for_param(x) for x in child_imports)
            lines.append(f"    from .{child._sanitized_name} import {child_func}")
            lines.append(f"    {child_func}({param_call})")

    lines.append("")
    lines.append(f'    logger.info("Completed {build_func}")')
    lines.append("")

    return "\n".join(lines)


def _sanitize_for_param(n: str) -> str:
    import re

    t = re.sub(r"[^0-9A-Za-z_]+", "_", n.strip())
    if not t:
        t = "param"
    if t[0].isdigit():
        t = "_" + t
    return t


# -----------------------------------------------------------------------
# PHASE 8: main.py
# -----------------------------------------------------------------------


def _phase8_generate_main_py(
    root: Circuit,
    out_dir: Path,
    circuit_to_file: Dict[Circuit, str],
    main_fn="main.py",
    highest_refs: Dict[str, int] = None,
):
    topnm = root._sanitized_name  # e.g. "root_circuit"
    buildf = f"build_{topnm}"

    lines = []
    lines.append('"""Auto-generated main driver script."""')
    lines.append("import logging")
    lines.append("from pathlib import Path")
    lines.append("import os")
    lines.append("from circuit_synth import *")
    lines.append("from circuit_synth.core.reference_manager import ReferenceManager")
    lines.append("")
    lines.append("logger = logging.getLogger(__name__)")
    lines.append("logging.basicConfig(level=logging.INFO)")
    lines.append("")

    # Add setup for initial reference counters if needed
    if highest_refs:
        lines.append("# Setup initial reference counters to avoid conflicts")
        lines.append("_initial_counters = {")
        for prefix, highest in sorted(highest_refs.items()):
            start_num = highest + 100
            lines.append(f"    '{prefix}': {start_num},")
        lines.append("}")
        lines.append("")
        lines.append("# Monkey patch ReferenceManager to use initial counters")
        lines.append("_original_init = ReferenceManager.__init__")
        lines.append("def _patched_init(self, initial_counters=None):")
        lines.append("    _original_init(self, initial_counters)")
        lines.append("    if not initial_counters and not self._parent:")
        lines.append("        # This is a root manager, set initial counters")
        lines.append("        self.set_initial_counters(_initial_counters)")
        lines.append(
            "        logger.info('Set initial reference counters: %s', _initial_counters)"
        )
        lines.append("ReferenceManager.__init__ = _patched_init")
        lines.append("")

    lines.append(f"from circuits.{topnm} import {buildf}")
    lines.append("")
    lines.append("def main():")
    lines.append(f"    logger.info('Calling {buildf}() to build the top circuit.')")
    lines.append(f"    c = {buildf}()")
    lines.append("    return c")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append("    circuit = main()")
    lines.append("    ")
    lines.append("    # Generate text netlist")
    lines.append("    netlist_text = circuit.generate_text_netlist()")
    lines.append("    print(netlist_text)")
    lines.append("    ")
    lines.append("    # Generate JSON netlist")
    lines.append("    current_dir = Path(__file__).parent")
    lines.append('    out_json = current_dir / "my_circuit.json"')
    lines.append("    circuit.generate_json_netlist(str(out_json))")
    lines.append('    print(f"JSON netlist saved to {out_json}")')
    lines.append("")
    lines.append("    # Generate KiCad netlist")
    lines.append(f'    kicad_netlist_path = current_dir / "{topnm}.net"')
    lines.append("    circuit.generate_kicad_netlist(str(kicad_netlist_path))")
    lines.append('    print(f"KiCad netlist saved to {kicad_netlist_path}")')
    lines.append("    ")
    lines.append("    # Note: KiCad schematic generation requires additional modules")
    lines.append("    # that are not included in the open source package")
    lines.append("")

    fp = out_dir / main_fn
    with open(fp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("Wrote main.py => %s", fp)


def main():
    """CLI entry point for JSON to Python project generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Python project from Circuit-Synth JSON"
    )
    parser.add_argument("input_json", help="Input Circuit-Synth JSON file")
    parser.add_argument("output_dir", help="Output directory for Python project")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    try:
        circuit = circuit_synth_json_to_python_project(args.input_json, args.output_dir)
        print(f"✓ Successfully generated Python project in {args.output_dir}")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Full error traceback:")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
