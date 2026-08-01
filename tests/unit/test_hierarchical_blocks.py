"""Unit tests for hierarchical blocks with declared ports.

A hierarchical block is a subcircuit that declares a named, directional
interface. These tests cover the declaration API, its serialization, and the
KiCad output it produces: typed sheet pins on the parent's sheet symbol and
matching hierarchical labels in the child schematic.
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from circuit_synth import (
    Bidirectional,
    Component,
    Input,
    Net,
    Output,
    PassivePort,
    PortDirection,
    PowerIn,
    PowerOut,
    TriState,
    circuit,
)

KICAD_CLI = shutil.which("kicad-cli") or next(
    (
        str(path)
        for path in [
            Path(r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"),
            Path.home() / r"AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe",
            Path("/usr/bin/kicad-cli"),
            Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
        ]
        if path.exists()
    ),
    None,
)

requires_kicad_cli = pytest.mark.skipif(
    KICAD_CLI is None, reason="kicad-cli is not installed"
)


def sheet_pins(schematic: Path) -> List[Tuple[str, str]]:
    """Read the sheet pins from a schematic file.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        A list of ``(pin_name, pin_type)`` tuples in file order.
    """
    text = schematic.read_text(encoding="utf-8")
    return re.findall(r'\(pin "([^"]+)" (\w+)\n', text)


def hierarchical_labels(schematic: Path) -> List[Tuple[str, str]]:
    """Read the hierarchical labels from a schematic file.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        A list of ``(label_text, shape)`` tuples in file order.
    """
    text = schematic.read_text(encoding="utf-8")
    return re.findall(r'\(hierarchical_label "([^"]+)"\s*\(shape (\w+)\)', text)


def local_labels(schematic: Path) -> List[str]:
    """Read the local (sheet-scoped) labels from a schematic file.

    Args:
        schematic: Path to a .kicad_sch file.

    Returns:
        The label texts in file order.
    """
    text = schematic.read_text(encoding="utf-8")
    return re.findall(r'\n\t\(label "([^"]+)"', text)


def kicad_nets(project_root: Path, tmp_path: Path) -> Dict[str, List[str]]:
    """Export a netlist with KiCad and return its nets.

    Args:
        project_root: The root .kicad_sch of the project.
        tmp_path: Directory the netlist is written to.

    Returns:
        A mapping of net name to sorted ``"REF.PIN"`` node identifiers.
    """
    netlist = tmp_path / "exported.net"
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


def kicad_erc(project_root: Path, tmp_path: Path) -> List[str]:
    """Run KiCad ERC and return the violation type of each error.

    Args:
        project_root: The root .kicad_sch of the project.
        tmp_path: Directory the report is written to.

    Returns:
        The bracketed violation names, one per reported error.
    """
    report = tmp_path / "erc.rpt"
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


@pytest.fixture
def temp_dir():
    """Create a temporary directory for generated KiCad projects."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path, ignore_errors=True)


class TestPortDeclaration:
    """The declaration API on the @circuit decorator."""

    def test_annotations_declare_ports(self):
        """Annotated parameters become ports named after the parameter."""

        @circuit(name="Block")
        def block(HI: Input, LO: Input, OUT: Output, REF: Bidirectional):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += HI
            resistor[2] += OUT

        @circuit(name="Top")
        def top():
            block(Net("A"), Net("B"), Net("C"), Net("REF_NET"))

        child = top().subcircuits[0]
        assert [(p.name, p.direction) for p in child.ports] == [
            ("HI", PortDirection.INPUT),
            ("LO", PortDirection.INPUT),
            ("OUT", PortDirection.OUTPUT),
            ("REF", PortDirection.BIDIRECTIONAL),
        ]

    def test_ports_record_the_connected_net(self):
        """Each port records the net bound to it at the call site."""

        @circuit(name="Block")
        def block(IN: Input, OUT: Output):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += IN
            resistor[2] += OUT

        @circuit(name="Top")
        def top():
            block(Net("SIGNAL_IN"), Net("SIGNAL_OUT"))

        child = top().subcircuits[0]
        assert {p.name: p.net_name for p in child.ports} == {
            "IN": "SIGNAL_IN",
            "OUT": "SIGNAL_OUT",
        }

    def test_power_annotations_map_to_input_and_output(self):
        """PowerIn and PowerOut record as input and output.

        KiCad has no power shape for hierarchical labels, so power rails use
        the ordinary directions.
        """

        @circuit(name="Block")
        def block(VIN: PowerIn, VOUT: PowerOut, SIG: TriState, REF: PassivePort):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += VIN
            resistor[2] += VOUT

        @circuit(name="Top")
        def top():
            block(Net("V5"), Net("V3"), Net("BUS"), Net("AGND"))

        directions = {p.name: p.direction for p in top().subcircuits[0].ports}
        assert directions == {
            "VIN": PortDirection.INPUT,
            "VOUT": PortDirection.OUTPUT,
            "SIG": PortDirection.TRI_STATE,
            "REF": PortDirection.PASSIVE,
        }

    def test_ports_argument_declares_without_annotations(self):
        """The decorator's ports argument works on unannotated signatures."""

        @circuit(name="Block", ports={"a": "input", "b": "output"})
        def block(a, b):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += a
            resistor[2] += b

        @circuit(name="Top")
        def top():
            block(Net("A"), Net("B"))

        assert [(p.name, p.direction) for p in top().subcircuits[0].ports] == [
            ("a", PortDirection.INPUT),
            ("b", PortDirection.OUTPUT),
        ]

    def test_partial_declaration_exports_remaining_nets(self):
        """One declared port makes the rest of the Net interface passive ports."""

        @circuit(name="Block")
        def block(IN: Input, other, third):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += IN
            resistor[2] += other

        @circuit(name="Top")
        def top():
            block(Net("A"), Net("B"), Net("C"))

        assert [(p.name, p.direction) for p in top().subcircuits[0].ports] == [
            ("IN", PortDirection.INPUT),
            ("other", PortDirection.PASSIVE),
            ("third", PortDirection.PASSIVE),
        ]

    def test_power_rails_are_not_ports(self):
        """Ground and the supply rails stay off the block interface.

        They are drawn as KiCad power symbols, which connect by name across the
        whole design, so turning them into sheet pins as well would clutter
        every block with rails that need no routing.
        """

        @circuit(name="Block")
        def block(SIG: Input, OUT: Output, GND: Bidirectional, VCC: PowerIn):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += SIG
            resistor[2] += OUT

        @circuit(name="Top")
        def top():
            block(Net("A"), Net("B"), Net("GND"), Net("VCC"))

        names = [port.name for port in top().subcircuits[0].ports]
        assert names == ["SIG", "OUT"], f"power rails leaked into the ports: {names}"

    def test_undeclared_circuit_has_no_ports(self):
        """Circuits that declare nothing keep the previous behaviour."""

        @circuit(name="Block")
        def block(a, b):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += a
            resistor[2] += b

        @circuit(name="Top")
        def top():
            block(Net("A"), Net("B"))

        assert top().subcircuits[0].ports == []

    def test_ports_are_serialized(self):
        """Ports appear in the intermediate circuit JSON."""

        @circuit(name="Block")
        def block(IN: Input, OUT: Output):
            resistor = Component(symbol="Device:R", ref="R", value="1k")
            resistor[1] += IN
            resistor[2] += OUT

        @circuit(name="Top")
        def top():
            block(Net("A"), Net("B"))

        data = top().to_dict()
        assert data["subcircuits"][0]["ports"] == [
            {"name": "IN", "direction": "input", "net": "A"},
            {"name": "OUT", "direction": "output", "net": "B"},
        ]


class TestGeneratedSheetPins:
    """The KiCad output produced from declared ports."""

    @staticmethod
    def _two_level_project(temp_dir: Path) -> Path:
        @circuit(name="Divider")
        def divider(VIN: Input, VOUT: Output, RTN: Bidirectional):
            top_resistor = Component(
                symbol="Device:R",
                ref="R",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            bottom_resistor = Component(
                symbol="Device:R",
                ref="R",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            top_resistor[1] += VIN
            top_resistor[2] += VOUT
            bottom_resistor[1] += VOUT
            bottom_resistor[2] += RTN

        @circuit(name="Board")
        def board():
            divider(Net("SRC"), Net("VSENSE"), Net("RETURN"))

        project = temp_dir / "divider_project"
        board().generate_kicad_project(
            str(project), force_regenerate=True, generate_pcb=False
        )
        return project

    def test_parent_sheet_gets_typed_pins(self, temp_dir):
        """The sheet symbol carries one pin per port, with the port's direction."""
        project = self._two_level_project(temp_dir)
        assert sheet_pins(project / "Board.kicad_sch") == [
            ("VIN", "input"),
            ("VOUT", "output"),
            ("RTN", "bidirectional"),
        ]

    def test_child_labels_match_the_pins(self, temp_dir):
        """The child has a hierarchical label per port, with a matching shape."""
        project = self._two_level_project(temp_dir)
        labels = set(hierarchical_labels(project / "Divider.kicad_sch"))
        assert labels == {
            ("VIN", "input"),
            ("VOUT", "output"),
            ("RTN", "bidirectional"),
        }

    def test_pins_are_named_for_ports_not_nets(self, temp_dir):
        """Sheet pins use the block's port names, not the caller's net names."""
        project = self._two_level_project(temp_dir)
        child_labels = {
            name for name, _ in hierarchical_labels(project / "Divider.kicad_sch")
        }
        assert "VBUS" not in child_labels
        assert "VSENSE" not in child_labels

    def test_parent_labels_the_connected_nets(self, temp_dir):
        """The parent labels each sheet pin with the net it connects."""
        project = self._two_level_project(temp_dir)
        assert set(local_labels(project / "Board.kicad_sch")) == {
            "SRC",
            "VSENSE",
            "RETURN",
        }

    def test_internal_nets_stay_local(self, temp_dir):
        """A net that is not a port does not become a hierarchical label."""

        @circuit(name="Filter")
        def rc_filter(IN: Input, OUT: Output, RTN: Bidirectional):
            resistor = Component(
                symbol="Device:R",
                ref="R",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            first_cap = Component(
                symbol="Device:C",
                ref="C",
                value="100nF",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )
            second_cap = Component(
                symbol="Device:C",
                ref="C",
                value="100nF",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )
            middle = Net("MIDPOINT")
            resistor[1] += IN
            resistor[2] += middle
            first_cap[1] += middle
            first_cap[2] += RTN
            second_cap[1] += middle
            second_cap[2] += OUT

        @circuit(name="Board")
        def board():
            rc_filter(Net("A"), Net("B"), Net("RETURN"))

        project = temp_dir / "filter_project"
        board().generate_kicad_project(
            str(project), force_regenerate=True, generate_pcb=False
        )

        child = project / "Filter.kicad_sch"
        assert "MIDPOINT" not in {name for name, _ in hierarchical_labels(child)}
        assert "MIDPOINT" in local_labels(child)


class TestRepeatedInstances:
    """Instantiating one block several times."""

    @staticmethod
    def _three_instance_project(temp_dir: Path) -> Path:
        @circuit(name="Buffer")
        def buffer_block(IN: Input, OUT: Output, RTN: Bidirectional):
            resistor = Component(
                symbol="Device:R",
                ref="R",
                value="100R",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            cap = Component(
                symbol="Device:C",
                ref="C",
                value="1nF",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )
            resistor[1] += IN
            resistor[2] += OUT
            cap[1] += OUT
            cap[2] += RTN

        @circuit(name="Board")
        def board():
            gnd = Net("RETURN")
            buffer_block(Net("IN_A"), Net("OUT_A"), gnd)
            buffer_block(Net("IN_B"), Net("OUT_B"), gnd)
            buffer_block(Net("IN_C"), Net("OUT_C"), gnd)

        project = temp_dir / "repeat_project"
        board().generate_kicad_project(
            str(project), force_regenerate=True, generate_pcb=False
        )
        return project

    def test_each_instance_gets_its_own_sheet_file(self, temp_dir):
        """Three instances produce three schematics, not one shared file."""
        project = self._three_instance_project(temp_dir)
        assert (project / "Buffer.kicad_sch").exists()
        assert (project / "Buffer2.kicad_sch").exists()
        assert (project / "Buffer3.kicad_sch").exists()

    def test_each_instance_keeps_its_own_components(self, temp_dir):
        """Components are not lost when a block is instantiated repeatedly."""
        project = self._three_instance_project(temp_dir)
        references = set()
        for name in ("Buffer.kicad_sch", "Buffer2.kicad_sch", "Buffer3.kicad_sch"):
            text = (project / name).read_text(encoding="utf-8")
            found = set(re.findall(r'\(property "Reference" "([RC]\d+)"', text))
            assert len(found) == 2, f"{name} should hold two components, got {found}"
            references |= found
        assert len(references) == 6, "every instance needs distinct references"

    def test_instances_connect_to_different_nets(self, temp_dir):
        """The parent wires each instance to its own nets."""
        project = self._three_instance_project(temp_dir)
        labels = set(local_labels(project / "Board.kicad_sch"))
        assert {"IN_A", "IN_B", "IN_C", "OUT_A", "OUT_B", "OUT_C"} <= labels

    def test_all_instances_share_one_interface(self, temp_dir):
        """Every instance's sheet symbol has the same declared pins."""
        project = self._three_instance_project(temp_dir)
        pins = sheet_pins(project / "Board.kicad_sch")
        expected = [("IN", "input"), ("OUT", "output"), ("RTN", "bidirectional")]
        assert pins == expected * 3


class TestNesting:
    """Blocks nested more than one level deep."""

    def test_three_levels_of_blocks(self, temp_dir):
        """A block inside a block inside the root keeps its ports at each level."""

        @circuit(name="Leaf")
        def leaf(IN: Input, OUT: Output, RTN: Bidirectional):
            resistor = Component(
                symbol="Device:R",
                ref="R",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            cap = Component(
                symbol="Device:C",
                ref="C",
                value="100nF",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )
            resistor[1] += IN
            resistor[2] += OUT
            cap[1] += OUT
            cap[2] += RTN

        @circuit(name="Middle")
        def middle(IN: Input, OUT: Output, RTN: Bidirectional):
            stage = Net("STAGE")
            leaf(IN, stage, RTN)
            leaf(stage, OUT, RTN)

        @circuit(name="Board")
        def board():
            leaf_return = Net("RETURN")
            middle(Net("SRC"), Net("SINK"), leaf_return)

        project = temp_dir / "nested_project"
        board().generate_kicad_project(
            str(project), force_regenerate=True, generate_pcb=False
        )

        # Root -> Middle
        assert sheet_pins(project / "Board.kicad_sch") == [
            ("IN", "input"),
            ("OUT", "output"),
            ("RTN", "bidirectional"),
        ]
        # Middle -> two Leaf instances, and Middle exports its own ports
        assert (
            sheet_pins(project / "Middle.kicad_sch")
            == [
                ("IN", "input"),
                ("OUT", "output"),
                ("RTN", "bidirectional"),
            ]
            * 2
        )
        assert set(hierarchical_labels(project / "Middle.kicad_sch")) == {
            ("IN", "input"),
            ("OUT", "output"),
            ("RTN", "bidirectional"),
        }
        # The net between the two leaves stays inside Middle
        assert "STAGE" in local_labels(project / "Middle.kicad_sch")
        assert (project / "Leaf.kicad_sch").exists()
        assert (project / "Leaf2.kicad_sch").exists()
