"""End-to-end test for the three-phase BLDC motor driver example.

This is the acceptance case for hierarchical blocks: an MCU block, three
instances of a single-phase driver block that each take high and low side
drive signals and output one motor phase, and a power block that outputs the
3.3V logic rail and the 30V motor rail.

The structural checks read the generated .kicad_sch files. The connectivity
checks run KiCad itself, so they are skipped when kicad-cli is missing.

The example uses symbols from the full KiCad library (connectors, an STM32, a
gate driver, MOSFETs). The test suite otherwise points KICAD_SYMBOL_DIR at a
small fixture library, so this module locates a real KiCad symbol directory
and skips if there is not one.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

REQUIRED_LIBRARIES = (
    "Connector_Generic",
    "Device",
    "Driver_FET",
    "MCU_ST_STM32F1",
    "Regulator_Switching",
    "Transistor_FET",
    "power",
)

SYMBOL_DIR_CANDIDATES = (
    Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols"),
    Path.home() / r"AppData\Local\Programs\KiCad\10.0\share\kicad\symbols",
    Path("/usr/share/kicad/symbols"),
    Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"),
)

KICAD_CLI = shutil.which("kicad-cli") or next(
    (
        str(path)
        for path in (
            Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"),
            Path.home() / r"AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe",
            Path("/usr/bin/kicad-cli"),
            Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
        )
        if path.exists()
    ),
    None,
)

requires_kicad_cli = pytest.mark.skipif(
    KICAD_CLI is None, reason="kicad-cli is not installed"
)

# A node entry in a KiCad-exported netlist.
KICAD_NODE = re.compile(r'\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)')


def find_symbol_directory() -> Path:
    """Locate a KiCad symbol directory holding every library the example needs.

    Returns:
        The directory containing the KiCad symbol libraries.

    Raises:
        pytest.skip.Exception: If no complete symbol directory is installed.
    """
    candidates = list(SYMBOL_DIR_CANDIDATES)
    for entry in os.environ.get("KICAD_SYMBOL_DIR", "").split(os.pathsep):
        if entry:
            candidates.insert(0, Path(entry))

    for directory in candidates:
        if all(
            (directory / f"{library}.kicad_sym").exists()
            for library in REQUIRED_LIBRARIES
        ):
            return directory

    pytest.skip("No complete KiCad symbol library installed")


def sheet_names(schematic: Path) -> List[str]:
    """Read the names of the sheet symbols placed on a schematic.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        The sheet names in file order.
    """
    return re.findall(
        r'\(property "Sheetname" "([^"]+)"', schematic.read_text(encoding="utf-8")
    )


def hierarchical_labels(schematic: Path) -> List[Tuple[str, str]]:
    """Read the hierarchical labels from a schematic.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        A list of ``(label_text, shape)`` tuples in file order.
    """
    return re.findall(
        r'\(hierarchical_label "([^"]+)"\s*\(shape (\w+)\)',
        schematic.read_text(encoding="utf-8"),
    )


def sheet_pins(schematic: Path) -> List[Tuple[str, str]]:
    """Read the sheet pins from a schematic.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        A list of ``(pin_name, pin_type)`` tuples in file order.
    """
    return re.findall(r'\(pin "([^"]+)" (\w+)\n', schematic.read_text(encoding="utf-8"))


def component_references(schematic: Path) -> set:
    """Read the placed component references from a schematic.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        The reference designators found on placed symbols.
    """
    return set(
        re.findall(
            r'\(property "Reference" "([A-Z]+\d+)"',
            schematic.read_text(encoding="utf-8"),
        )
    )


def kicad_nets(project_root: Path, output_dir: Path) -> Dict[str, List[str]]:
    """Export a netlist with KiCad and return its nets.

    Args:
        project_root: The root .kicad_sch of the project.
        output_dir: Directory the netlist is written to.

    Returns:
        A mapping of net name to sorted ``"REF.PIN"`` node identifiers.
    """
    netlist = output_dir / "exported.net"
    subprocess.run(
        [
            KICAD_CLI,
            "sch",
            "export",
            "netlist",
            "--format",
            "kicadsexpr",
            "-o",
            str(netlist),
            str(project_root),
        ],
        check=True,
        capture_output=True,
        timeout=600,
    )

    nets: Dict[str, List[str]] = {}
    text = netlist.read_text(encoding="utf-8")
    for match in re.finditer(
        r'\(net\s*\(code "\d+"\)\s*\(name "([^"]*)"\)(.*?)\n\t\t\)', text, re.S
    ):
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', match.group(2))
        nets[match.group(1)] = sorted(f"{ref}.{pin}" for ref, pin in nodes)
    return nets


class _Union:
    """Minimal union-find used to build the intended pin partition."""

    def __init__(self) -> None:
        self._parent: Dict[object, object] = {}

    def find(self, key: object) -> object:
        """Return the representative of the set holding ``key``."""
        self._parent.setdefault(key, key)
        while self._parent[key] != key:
            self._parent[key] = self._parent[self._parent[key]]
            key = self._parent[key]
        return key

    def join(self, first: object, second: object) -> None:
        """Merge the sets holding two keys."""
        left, right = self.find(first), self.find(second)
        if left != right:
            self._parent[left] = right


def intended_partition(circuit_json: Path) -> Dict[str, frozenset]:
    """Build the connectivity the Python circuit described.

    The JSON is walked as a hierarchy, so two instances of one block keep their
    internal nets apart. A net crosses a sheet boundary exactly where a
    hierarchical port says it does, which is the only place the two sides are
    joined.

    Args:
        circuit_json: The generated circuit JSON.

    Returns:
        A mapping of ``"REF.PIN"`` to the frozen set of pins sharing its net.
    """
    union = _Union()
    tokens = set()

    def walk(node: dict, path: str) -> None:
        for net_name, info in (node.get("nets") or {}).items():
            entries = info.get("nodes", info) if isinstance(info, dict) else info
            # A rail drawn with power symbols connects by name across the whole
            # design, so it belongs to one set no matter which sheet it is on.
            is_power = isinstance(info, dict) and info.get("power_symbol")
            key = ("power", net_name) if is_power else (path, net_name)
            for entry in entries:
                token = f"{entry['component']}.{entry['pin']['number']}"
                tokens.add(token)
                union.join(token, key)

        for index, child in enumerate(node.get("subcircuits") or []):
            child_path = f"{path}/{child.get('name', '?')}#{index}"
            for port in child.get("ports") or []:
                union.join((child_path, port["net"]), (path, port["net"]))
            walk(child, child_path)

    walk(json.loads(circuit_json.read_text(encoding="utf-8")), "")

    groups: Dict[object, set] = {}
    for token in tokens:
        groups.setdefault(union.find(token), set()).add(token)
    # Power symbols and PWR_FLAGs exist only on the KiCad side.
    cleaned = [
        {token for token in group if not token.startswith("#")}
        for group in groups.values()
    ]
    return {
        token: frozenset(group) for group in cleaned for token in group if group
    }


def kicad_partition(project_root: Path, output_dir: Path) -> Dict[str, frozenset]:
    """Build the connectivity KiCad reads back from the generated project.

    Args:
        project_root: The root .kicad_sch of the project.
        output_dir: Directory the netlist is written to.

    Returns:
        A mapping of ``"REF.PIN"`` to the frozen set of pins sharing its net.
    """
    partition: Dict[str, frozenset] = {}
    for nodes in _exported_nets(project_root, output_dir):
        pins = frozenset(node for node in nodes if not node.startswith("#"))
        for token in pins:
            partition[token] = pins
    return partition


def _exported_nets(project_root: Path, output_dir: Path) -> List[set]:
    """Export a netlist with KiCad and return each net's pin tokens."""
    netlist = output_dir / "partition.net"
    subprocess.run(
        [KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr",
         "-o", str(netlist), str(project_root)],
        check=True, capture_output=True, timeout=900,
    )
    text = netlist.read_text(encoding="utf-8")
    section = text[text.index("(nets"):]

    nets = []
    for start in (m.start() for m in re.finditer(r"\(net\s", section)):
        depth = 0
        block = ""
        for index in range(start, len(section)):
            if section[index] == "(":
                depth += 1
            elif section[index] == ")":
                depth -= 1
                if depth == 0:
                    block = section[start:index + 1]
                    break
        name = re.search(r'\(name\s+"([^"]*)"\)', block)
        if name and name.group(1).startswith("unconnected"):
            continue
        nodes = {f"{r}.{p}" for r, p in KICAD_NODE.findall(block)}
        if nodes:
            nets.append(nodes)
    return nets


def kicad_erc_violations(project_root: Path, output_dir: Path) -> List[str]:
    """Run KiCad ERC and return the violation type of each reported error.

    Args:
        project_root: The root .kicad_sch of the project.
        output_dir: Directory the report is written to.

    Returns:
        The bracketed violation names, one per reported error.
    """
    report = output_dir / "erc.rpt"
    subprocess.run(
        [
            KICAD_CLI,
            "sch",
            "erc",
            "--severity-error",
            "-o",
            str(report),
            str(project_root),
        ],
        check=False,
        capture_output=True,
        timeout=600,
    )
    return re.findall(r"^\[(\w+)\]", report.read_text(encoding="utf-8"), re.M)


GENERATOR_SCRIPT = """
import sys
from circuit_synth.data.templates.example_circuits.bldc_motor_driver import (
    bldc_motor_driver,
)

bldc_motor_driver().generate_kicad_project(
    sys.argv[1], force_regenerate=True, generate_pcb=False
)
"""


@pytest.fixture(scope="module")
def project(tmp_path_factory) -> Path:
    """Generate the BLDC motor driver example once for this module.

    The project is built in a subprocess. The rest of the suite points
    KICAD_SYMBOL_DIR at a small fixture library, and circuit-synth caches
    symbol lookups per process, so generating in-process here would reuse
    those lookups and leave the example's symbols without pin data.

    Args:
        tmp_path_factory: pytest's temporary directory factory.

    Returns:
        The directory holding the generated KiCad project.
    """
    symbol_dir = find_symbol_directory()
    directory = tmp_path_factory.mktemp("bldc")
    path = directory / "bldc_motor_driver"

    environment = dict(os.environ)
    environment["KICAD_SYMBOL_DIR"] = str(symbol_dir)
    environment["CIRCUIT_SYNTH_CACHE_DIR"] = str(directory / "symbol_cache")

    result = subprocess.run(
        [sys.executable, "-c", GENERATOR_SCRIPT, str(path)],
        cwd=str(directory),
        env=environment,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    assert (
        result.returncode == 0
    ), f"generating the example failed:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}"
    return path


ROOT_SCHEMATIC = "BLDC_Motor_Driver.kicad_sch"
DRIVER_SHEETS = (
    "PhaseDriver.kicad_sch",
    "PhaseDriver2.kicad_sch",
    "PhaseDriver3.kicad_sch",
)


class TestGeneratedStructure:
    """The hierarchy written to disk."""

    def test_every_block_gets_a_schematic(self, project):
        """Power, MCU and each of the three phase drivers get their own sheet."""
        for name in (
            ROOT_SCHEMATIC,
            "Power.kicad_sch",
            "MCU.kicad_sch",
            *DRIVER_SHEETS,
        ):
            assert (project / name).exists(), f"missing {name}"

    def test_root_instantiates_five_blocks(self, project):
        """The root schematic places one sheet symbol per block."""
        assert sheet_names(project / ROOT_SCHEMATIC) == [
            "Power",
            "MCU",
            "PhaseDriver",
            "PhaseDriver2",
            "PhaseDriver3",
        ]

    def test_power_block_outputs_both_rails(self, project):
        """The power block exports the 30V and 3.3V rails as outputs."""
        labels = set(hierarchical_labels(project / "Power.kicad_sch"))
        assert ("V30", "output") in labels
        assert ("V3V3", "output") in labels

    def test_mcu_block_outputs_six_gate_signals(self, project):
        """The MCU block takes 3.3V in and drives three high/low signal pairs."""
        labels = set(hierarchical_labels(project / "MCU.kicad_sch"))
        assert ("V3V3", "input") in labels
        for signal in ("AH", "AL", "BH", "BL", "CH", "CL"):
            assert (signal, "output") in labels, f"{signal} is not an output"

    @pytest.mark.parametrize("sheet", DRIVER_SHEETS)
    def test_phase_driver_takes_hi_lo_and_outputs_a_phase(self, project, sheet):
        """Every driver instance has the same declared interface."""
        assert set(hierarchical_labels(project / sheet)) == {
            ("HI", "input"),
            ("LI", "input"),
            ("PHASE", "output"),
            ("VM", "input"),
            ("VDRV", "input"),
        }

    def test_root_sheet_pins_match_the_block_interfaces(self, project):
        """The sheet symbols carry the declared pins of every block."""
        pins = sheet_pins(project / ROOT_SCHEMATIC)
        driver_pins = [
            ("HI", "input"),
            ("LI", "input"),
            ("VM", "input"),
            ("VDRV", "input"),
            ("PHASE", "output"),
        ]
        assert (
            pins
            == [
                ("V30", "output"),
                ("V3V3", "output"),
                ("V3V3", "input"),
                ("AH", "output"),
                ("AL", "output"),
                ("BH", "output"),
                ("BL", "output"),
                ("CH", "output"),
                ("CL", "output"),
            ]
            + driver_pins * 3
        )

    def test_driver_instances_hold_distinct_components(self, project):
        """The three instances do not share component references."""
        references = [component_references(project / sheet) for sheet in DRIVER_SHEETS]
        for refs, sheet in zip(references, DRIVER_SHEETS):
            assert refs, f"{sheet} has no components"
        assert not references[0] & references[1]
        assert not references[0] & references[2]
        assert not references[1] & references[2]

    def test_root_has_no_hierarchical_labels(self, project):
        """The root sheet has no parent, so it must not export anything."""
        assert hierarchical_labels(project / ROOT_SCHEMATIC) == []


@requires_kicad_cli
class TestKicadConnectivity:
    """What KiCad makes of the generated project."""

    def test_gate_signals_reach_the_drivers(self, project, tmp_path):
        """Each of the six drive signals runs from the MCU into one driver."""
        nets = kicad_nets(project / ROOT_SCHEMATIC, tmp_path)
        for signal in ("AH", "AL", "BH", "BL", "CH", "CL"):
            nodes = nets.get(f"/{signal}")
            assert nodes is not None, f"/{signal} is missing from the netlist"
            assert len(nodes) == 2, f"/{signal} = {nodes}"

    def test_each_phase_reaches_the_motor_connector(self, project, tmp_path):
        """Every phase output reaches its half bridge and the motor connector."""
        nets = kicad_nets(project / ROOT_SCHEMATIC, tmp_path)
        for phase in ("PHASE_A", "PHASE_B", "PHASE_C"):
            nodes = nets.get(f"/{phase}")
            assert nodes is not None, f"/{phase} is missing from the netlist"
            assert len(nodes) == 5, f"/{phase} = {nodes}"
        # The three phases are separate nets.
        assert nets["/PHASE_A"] != nets["/PHASE_B"] != nets["/PHASE_C"]

    def test_power_rails_are_shared_between_blocks(self, project, tmp_path):
        """The 30V and 3.3V rails reach the blocks that consume them."""
        nets = kicad_nets(project / ROOT_SCHEMATIC, tmp_path)
        assert len(nets["/V30"]) >= 4, nets["/V30"]
        assert len(nets["/V3V3"]) >= 10, nets["/V3V3"]
        assert len(nets["GND"]) >= 20, nets["GND"]

    def test_instance_internals_stay_separate(self, project, tmp_path):
        """Nets internal to a driver belong to that instance alone."""
        nets = kicad_nets(project / ROOT_SCHEMATIC, tmp_path)
        boots = [
            nets["/PhaseDriver/BOOT"],
            nets["/PhaseDriver2/BOOT"],
            nets["/PhaseDriver3/BOOT"],
        ]
        assert all(len(nodes) == 3 for nodes in boots), boots
        assert boots[0] != boots[1] != boots[2]

    def test_wiring_does_not_change_the_netlist(self, project, tmp_path):
        """What KiCad reads back matches the circuit described in Python.

        This is the guarantee behind drawing wires rather than labelling every
        pin: the router may place a wire wherever it likes, but the resulting
        connectivity has to be identical, pin for pin, to what the Python
        circuit declared. A wire that strayed onto a neighbouring pin would
        show up here as a short.
        """
        expected = intended_partition(project / "BLDC_Motor_Driver.json")
        actual = kicad_partition(project / ROOT_SCHEMATIC, tmp_path)

        problems = []
        for token, group in sorted(expected.items()):
            found = actual.get(token)
            if found is None:
                problems.append(f"{token} is missing from the netlist")
            elif found != group:
                problems.append(
                    f"{token}: shorted to {sorted(found - group)}"
                    if found - group
                    else f"{token}: no longer joined to {sorted(group - found)}"
                )

        assert not problems, "\n".join(problems[:10])

    def test_signal_nets_are_drawn_as_wires(self, project):
        """The sheets carry real wires, not only labels at every pin."""
        total = 0
        for sheet in (*DRIVER_SHEETS, "Power.kicad_sch", "MCU.kicad_sch"):
            total += len(
                re.findall(r"\(wire\s*\(pts", (project / sheet).read_text(encoding="utf-8"))
            )
        assert total > 20, f"expected the blocks to be wired, found {total} segments"

    def test_ground_is_always_a_power_symbol(self, project):
        """Ground renders as a power symbol and never as a label."""
        for sheet in (*DRIVER_SHEETS, "Power.kicad_sch", "MCU.kicad_sch"):
            text = (project / sheet).read_text(encoding="utf-8")
            assert '(lib_id "power:GND")' in text, f"{sheet} has no ground symbol"
            assert '(label "GND"' not in text, f"{sheet} labels ground instead"
            assert '(hierarchical_label "GND"' not in text, (
                f"{sheet} exports ground as a port instead of drawing a symbol"
            )

    def test_erc_reports_no_hierarchy_errors(self, project, tmp_path):
        """ERC finds no mismatched, dangling or undriven hierarchical items.

        Unused MCU GPIO pins are still reported as unconnected; that is a
        property of the example, not of the hierarchy.
        """
        violations = set(kicad_erc_violations(project / ROOT_SCHEMATIC, tmp_path))
        assert "hier_label_mismatch" not in violations
        assert "label_dangling" not in violations
        assert "power_pin_not_driven" not in violations
