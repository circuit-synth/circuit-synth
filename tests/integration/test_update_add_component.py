"""
Regression: regenerating a project that gained a component must add it.

Previously the update path crashed on kicad-sch-api's SheetManager and the
components_dict lookup, and then removed the just-added component again as
"unmatched".
"""

from pathlib import Path

import kicad_sch_api as ksa

from circuit_synth import Component, Net, circuit


def _build_flat(n_caps: int):
    @circuit(name="flat")
    def flat():
        gnd = Net(name="gnd")
        vcc = Net(name="vcc")
        for _ in range(n_caps):
            c = Component(
                symbol="Device:C",
                ref="C",
                value="100nF",
                footprint="Capacitor_SMD:C_0402_1005Metric",
            )
            c["1"] += vcc
            c["2"] += gnd

    return flat()


def _generate(circ, project_dir: Path) -> None:
    result = circ.generate_kicad_project(
        str(project_dir), generate_pcb=False, update_source_refs=False
    )
    assert result["success"], result.get("error")


def test_regeneration_adds_new_component_to_flat_project(tmp_path: Path) -> None:
    project_dir = tmp_path / "flat"
    _generate(_build_flat(1), project_dir)
    _generate(_build_flat(2), project_dir)

    sch = ksa.Schematic.load(str(project_dir / "flat.kicad_sch"))
    refs = sorted(c.reference for c in sch.components if not c.reference.startswith("#"))
    assert refs == ["C1", "C2"]
