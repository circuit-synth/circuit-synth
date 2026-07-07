"""Acceptance: ngspice compat mode makes vendor PSpice libs run (Stage 20.2).

The fixture ``pstest.lib`` uses PSpice idioms (``PARAMS:``, ``VALUE={IF(...)}``)
that ngspice's default dialect rejects. With ``compat="psa"`` the shared ngspice
instance is put in PSpice mode before load, the subckt parses, and its ``GAIN``
parameter (passed through ``Sim.Params``) evaluates: VIN=1 V, GAIN=3 -> V(OUT)=3 V.

The negative case (no compat -> parse failure) runs in a **subprocess** because a
failed PSpice-syntax load poisons the per-process singleton ngspice instance and
would break unrelated tests sharing this pytest process.

Skips cleanly when PySpice or a loadable ngspice is unavailable.
"""

import os
import subprocess
import sys
import textwrap

import pytest

from circuit_synth import Component, Net, circuit


FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "spice",
    "pstest.lib",
)


def _ngspice_available() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice or a loadable ngspice is not available",
)


@circuit(name="vendor_compat")
def _vendor_circuit():
    """A PSpice-syntax subckt driven by a 1 V DC source, GAIN passed via Sim.Params."""
    v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
    x1 = Component(
        symbol="Device:R",
        ref="R1",
        **{"Sim.Library": FIXTURE, "Sim.Name": "PSTEST", "Sim.Params": "GAIN=3"},
    )
    rl = Component(symbol="Device:R", ref="RL", value="1k")
    vin = Net("VIN")
    out = Net("OUT")
    gnd = Net("GND")
    v1[1] += vin
    v1[2] += gnd
    x1[1] += vin  # IN
    x1[2] += out  # OUT
    rl[1] += out
    rl[2] += gnd


def test_pspice_lib_runs_with_compat_psa():
    """compat='psa' -> the PSpice subckt parses and GAIN=3 evaluates: V(OUT)=3 V."""
    result = _vendor_circuit().simulate(compat="psa").operating_point()
    assert result.get_voltage("OUT") == pytest.approx(3.0, abs=0.01)


def test_pspice_lib_fails_without_compat_in_subprocess():
    """No compat -> the PSpice syntax is rejected by ngspice's default dialect.

    Run in a subprocess: a failed load leaves the singleton ngspice instance
    unusable, so this must not share the pytest process with other sims.
    """
    script = textwrap.dedent(
        f"""
        import circuit_synth.simulation.simulator  # noqa: F401 (DLL discovery)
        from circuit_synth import Component, Net, circuit

        @circuit(name="vc")
        def c():
            v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
            x1 = Component(symbol="Device:R", ref="R1", **{{
                "Sim.Library": {FIXTURE!r},
                "Sim.Name": "PSTEST",
                "Sim.Params": "GAIN=3",
            }})
            rl = Component(symbol="Device:R", ref="RL", value="1k")
            vin, out, gnd = Net("VIN"), Net("OUT"), Net("GND")
            v1[1] += vin; v1[2] += gnd
            x1[1] += vin; x1[2] += out
            rl[1] += out; rl[2] += gnd

        # No compat -> default ngspice dialect -> PSpice IF() must be rejected.
        c().simulate().operating_point()
        print("UNEXPECTED_SUCCESS")
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=180,
    )
    combined = (proc.stdout + proc.stderr).lower()
    assert proc.returncode != 0, f"expected failure, got success:\n{combined}"
    assert "unexpected_success" not in combined, combined
    # The characteristic default-dialect rejection of the PSpice IF() function.
    assert "if" in combined or "ngspice" in combined or "error" in combined, combined
