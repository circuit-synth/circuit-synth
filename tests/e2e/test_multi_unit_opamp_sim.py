"""E2E: a dual op-amp with BOTH units wired simulates per-unit (bug #A closed).

The run-4 DAQ filter chain -- Sallen-Key LPF (1 MHz) + MFB HPF (100 Hz) -- placed
on ONE dual ``ADA4807-2ACP`` (unit A = LPF, unit B = HPF). Before Stage 23.3 the
dual collapsed to a single VCVS, leaving the HPF section undriven (singular
matrix). This asserts both sections now simulate: VLP -3 dB ~= 995 kHz, VHP -3 dB
~= 102 Hz (the same numbers the two-singles workaround produced in
``kicadprojects/SiPM_TIA_Filter/circuit-synth/sim_filter_chain.py``).

Skips cleanly when ngspice is unavailable.
"""

import pytest

from circuit_synth import Component, Net, circuit


def _ngspice_loads() -> bool:
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        Component(symbol="Amplifier_Operational:ADA4807-2ACP", ref="U1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_loads(), reason="ngspice or ADA4807-2ACP symbol unavailable"
)


@circuit(name="Dual_Filter_Chain")
def _dual_filter_chain():
    """VSIN -> SK LPF (unit A) -> VLP --split--> MFB HPF (unit B) -> VHP.

    ADA4807-2ACP: unit A OUT=1 -IN=2 +IN=3; unit B +IN=7 -IN=8 OUT=9.
    """
    v1 = Component(symbol="Simulation_SPICE:VSIN", ref="V1", value="1V")
    u2 = Component(symbol="Amplifier_Operational:ADA4807-2ACP", ref="U2")

    r1a = Component(symbol="Device:R", ref="R1A", value="1.13k")
    r2a = Component(symbol="Device:R", ref="R2A", value="1.13k")
    c1a = Component(symbol="Device:C", ref="C1A", value="200p")
    c2a = Component(symbol="Device:C", ref="C2A", value="100p")

    c1h = Component(symbol="Device:C", ref="C1H", value="10n")
    c3h = Component(symbol="Device:C", ref="C3H", value="10n")
    c4h = Component(symbol="Device:C", ref="C4H", value="10n")
    r2h = Component(symbol="Device:R", ref="R2H", value="75k")
    r5h = Component(symbol="Device:R", ref="R5H", value="332k")

    vtia, vlp, vhp = Net("VTIA"), Net("VLP"), Net("VHP")
    nx, pa, nn, vg, gnd = Net("NX"), Net("PA"), Net("NN"), Net("VG"), Net("GND")

    v1[1] += vtia
    v1[2] += gnd

    # Sallen-Key LPF on unit A
    r1a[1] += vtia
    r1a[2] += nx
    r2a[1] += nx
    r2a[2] += pa
    c1a[1] += nx
    c1a[2] += vlp
    c2a[1] += pa
    c2a[2] += gnd
    u2[3] += pa  # +IN (A)
    u2[2] += vlp  # -IN (A), unity feedback
    u2[1] += vlp  # OUT (A)

    # MFB HPF on unit B
    c1h[1] += vlp
    c1h[2] += nn
    r2h[1] += nn
    r2h[2] += gnd
    c3h[1] += nn
    c3h[2] += vg
    c4h[1] += nn
    c4h[2] += vhp
    r5h[1] += vg
    r5h[2] += vhp
    u2[8] += vg  # -IN (B)
    u2[7] += gnd  # +IN (B)
    u2[9] += vhp  # OUT (B)


def test_dual_opamp_filter_chain_simulates_both_sections():
    from circuit_synth.simulation.converter import SpiceConverter

    c = _dual_filter_chain()

    # Netlist: both units emitted as distinct VCVS sources.
    netlist = str(SpiceConverter(c).convert())
    assert any(ln.startswith("EU2 ") for ln in netlist.splitlines()), netlist
    assert any(ln.startswith("EU2u2 ") for ln in netlist.splitlines()), netlist

    # AC: both filter outputs are present (no singular matrix) with the expected
    # corners (same as the two-singles workaround, +/-5%).
    result = c.simulate().ac_analysis(10, 1e7, points=200)
    vlp_fc = result.cutoff_frequency("VLP")  # LPF -3 dB corner
    vhp_fc = result.cutoff_frequency("VHP")  # HPF (first crossing low->high)
    assert vlp_fc == pytest.approx(995e3, rel=0.05), f"VLP cutoff {vlp_fc}"
    assert vhp_fc == pytest.approx(102.0, rel=0.05), f"VHP cutoff {vhp_fc}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
