"""1 GOhm stubs on connected-but-unmodeled macromodel pins (Stage 22.4, bug #16).

A behavioral macromodel (LDO / switcher) drives only its resolved terminals; a
real part's OTHER connected pins (NR/SS/BYP/COMP/EN...) stay in the netlist as
plain nodes. If such a node's net is cap-only (the usual decoupling), it has no
DC path and ngspice's op-point fails (``singular matrix: check node ...``). The
converter now emits a 1 GOhm resistor from each such node to ground -- nA-level
leakage that gives the node a DC path without perturbing behavior.

Netlist-shape only (no ngspice); the live op-point convergence is in
``tests/e2e/test_ldo_macromodel.py``.
"""

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import PYSPICE_AVAILABLE, SpiceConverter

needs_pyspice = pytest.mark.skipif(
    not PYSPICE_AVAILABLE, reason="PySpice not available"
)

LDO_SYM = "Regulator_Linear:TPS7A4701xRGW"  # pins: 15=IN 1=OUT 7=GND 14=NR 13=EN 20=OUT


def _stub_lines(netlist: str, ref: str):
    pfx = f"r{ref}_stub".lower()
    return [ln for ln in netlist.splitlines() if ln.strip().lower().startswith(pfx)]


@needs_pyspice
def test_ldo_nr_pin_gets_one_stub():
    """An LDO NR pin on a cap-only net gets exactly one 1G stub to ground;
    IN/OUT/GND get none."""

    @circuit(name="ldo_nr")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="32.5")
        u1 = Component(symbol=LDO_SYM, ref="U1", **{"Sim.Params": "vout=5"})
        cnr = Component(symbol="Device:C", ref="C1", value="10n")
        rl = Component(symbol="Device:R", ref="RL", value="1k")
        vin, out, gnd, nr = Net("VIN"), Net("OUT"), Net("GND"), Net("LDO_NR")
        v1[1] += vin
        v1[2] += gnd
        u1[15] += vin  # IN
        u1[1] += out  # OUT
        u1[7] += gnd  # GND
        u1[14] += nr  # NR (cap-only net)
        cnr[1] += nr
        cnr[2] += gnd
        rl[1] += out
        rl[2] += gnd

    netlist = str(SpiceConverter(_c()).convert())
    stubs = _stub_lines(netlist, "U1")
    assert len(stubs) == 1, netlist
    parts = stubs[0].split()
    # R<ref>_stubN <node> <gnd=0> 1e9
    assert parts[1].upper() == "LDO_NR", stubs
    assert parts[2] == "0", stubs
    assert parts[3] in ("1e9", "1e+09", "1E9", "1000000000.0"), stubs
    # No stub on the modeled nets.
    low = netlist.lower()
    for modeled in ("vin", "out"):
        assert f"ru1_stub" not in low or not any(
            p.split()[1].lower() == modeled for p in stubs
        )


@needs_pyspice
def test_ldo_extra_pins_tied_to_out_produce_no_stub():
    """Extra pins tapping the OUT node (anyOUT-tap shape) dedupe to zero stubs."""

    @circuit(name="ldo_outtap")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="32.5")
        u1 = Component(symbol=LDO_SYM, ref="U1", **{"Sim.Params": "vout=5"})
        rl = Component(symbol="Device:R", ref="RL", value="1k")
        vin, out, gnd = Net("VIN"), Net("OUT"), Net("GND")
        v1[1] += vin
        v1[2] += gnd
        u1[15] += vin  # IN
        u1[1] += out  # OUT
        u1[7] += gnd  # GND
        u1[20] += out  # second OUT pad -> OUT node (modeled)
        u1[13] += out  # EN tapped to OUT -> OUT node (modeled)
        rl[1] += out
        rl[2] += gnd

    netlist = str(SpiceConverter(_c()).convert())
    assert _stub_lines(netlist, "U1") == [], netlist


@needs_pyspice
def test_switcher_extra_pin_gets_one_stub():
    """A boost switcher with an extra connected pin (EN) gets one stub; none on
    SW/VIN/GND/FB."""

    @circuit(name="boost_en")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        u1 = Component(
            symbol="Regulator_Switching:TPS62130",
            ref="U1",
            **{"Sim.Device": "BOOST", "Sim.Params": "fsw=500k vout=12"},
        )
        l1 = Component(symbol="Device:L", ref="L1", value="10u")
        ren = Component(symbol="Device:R", ref="R1", value="100k")
        vin, sw, gnd, en = Net("VIN"), Net("SW"), Net("GND"), Net("EN_NET")
        v1[1] += vin
        v1[2] += gnd
        l1[1] += vin  # boost inductor VIN -> SW (gives SW a second connection)
        l1[2] += sw
        u1[10] += vin  # VIN
        u1[1] += sw  # SW
        u1[6] += gnd  # GND
        u1[13] += en  # EN (extra, unmodeled)
        ren[1] += en
        ren[2] += gnd

    netlist = str(SpiceConverter(_c()).convert())
    stubs = _stub_lines(netlist, "U1")
    assert len(stubs) == 1, netlist
    parts = stubs[0].split()
    assert parts[1].upper() == "EN_NET", stubs
    assert parts[2] == "0", stubs
