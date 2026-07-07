"""ngspice compat mode + subckt-param passthrough (Stage 20.2).

Two capabilities that make typical vendor model files consumable:

1. **Compat mode** -- PSpice/LTspice-flavored `.lib` files parse only when ngspice
   is told to relax its dialect (``set ngbehavior=psa``). The user opts in with
   ``circuit.simulate(compat="psa")`` or a schematic ``Sim.Compat="psa"`` property.
   Because ``NgSpiceShared`` is a per-process singleton, the mode is set on the
   shared instance before circuit load and *unset* on the next default-mode run.

2. **X-line params** -- a ``Sim.Library`` subckt taking parameters receives them
   from ``Sim.Params`` (``X<ref> ... <SUBCKT> gain=3``).

Netlist/plumbing level only (no ngspice); the live parse is in
``tests/e2e/test_vendor_compat.py``.
"""

import os

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.converter import SpiceConverter, SimulationValidationError


FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "spice",
    "pstest.lib",
)


def _pyspice_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        return bool(PYSPICE_AVAILABLE)
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _pyspice_available(), reason="PySpice not available"
)


@pytest.fixture(autouse=True)
def _restore_ngbehavior_flag():
    """Isolate the process-global ngbehavior-set flag between tests."""
    from circuit_synth.simulation.simulator import CircuitSimulator

    saved = getattr(CircuitSimulator, "_ngbehavior_set", False)
    yield
    CircuitSimulator._ngbehavior_set = saved


# --------------------------------------------------------------------------- #
# compat arg validation                                                       #
# --------------------------------------------------------------------------- #


@circuit(name="divider")
def _divider():
    v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    r2 = Component(symbol="Device:R", ref="R2", value="1k")
    vin = Net("VIN")
    out = Net("OUT")
    gnd = Net("GND")
    v1[1] += vin
    v1[2] += gnd
    r1[1] += vin
    r1[2] += out
    r2[1] += out
    r2[2] += gnd


def test_bogus_compat_raises_valueerror():
    from circuit_synth.simulation.simulator import CircuitSimulator

    with pytest.raises(ValueError) as exc:
        CircuitSimulator(_divider(), compat="bogus")
    assert "compat" in str(exc.value).lower()


@pytest.mark.parametrize("mode", ["ps", "lt", "psa", "a", "all", "ki"])
def test_valid_compat_accepted(mode):
    from circuit_synth.simulation.simulator import CircuitSimulator

    sim = CircuitSimulator(_divider(), compat=mode)
    assert sim._compat == mode


# --------------------------------------------------------------------------- #
# compat plumbing: set before load, unset on next default-mode run            #
# --------------------------------------------------------------------------- #


class _FakeShared:
    def __init__(self):
        self.cmds = []

    def exec_command(self, cmd):
        self.cmds.append(cmd)


def _patch_shared_and_simulator(monkeypatch, sim):
    """Record ngbehavior commands and the simulator() kwargs without real ngspice."""
    from circuit_synth.simulation import simulator as sim_mod

    shared = _FakeShared()
    monkeypatch.setattr(
        sim_mod.NgSpiceShared, "new_instance", staticmethod(lambda: shared)
    )
    captured = {}

    def fake_simulator(**kwargs):
        captured.update(kwargs)

        class _S:
            def options(self, **_o):
                pass

        return _S()

    monkeypatch.setattr(sim.spice_circuit, "simulator", fake_simulator)
    return shared, captured


def test_compat_sets_ngbehavior_before_build(monkeypatch):
    from circuit_synth.simulation.simulator import CircuitSimulator

    sim = CircuitSimulator(_divider(), compat="psa")
    shared, captured = _patch_shared_and_simulator(monkeypatch, sim)
    sim._make_simulator(25)
    assert "set ngbehavior=psa" in shared.cmds
    assert captured.get("simulator") == "ngspice-shared"
    assert captured.get("ngspice_shared") is shared
    assert CircuitSimulator._ngbehavior_set is True


def test_default_mode_unsets_after_compat_run(monkeypatch):
    from circuit_synth.simulation.simulator import CircuitSimulator

    CircuitSimulator._ngbehavior_set = True  # a previous compat run left it set
    sim = CircuitSimulator(_divider())  # compat=None
    shared, captured = _patch_shared_and_simulator(monkeypatch, sim)
    sim._make_simulator(25)
    assert "unset ngbehavior" in shared.cmds
    assert CircuitSimulator._ngbehavior_set is False


def test_default_mode_no_shared_instance_when_clean(monkeypatch):
    """No compat, no pending reset -> the legacy simulator() call, untouched."""
    from circuit_synth.simulation.simulator import CircuitSimulator
    from circuit_synth.simulation import simulator as sim_mod

    CircuitSimulator._ngbehavior_set = False
    sim = CircuitSimulator(_divider())

    def _boom():
        raise AssertionError("new_instance must not be called on the clean path")

    monkeypatch.setattr(sim_mod.NgSpiceShared, "new_instance", staticmethod(_boom))
    captured = {}

    def fake_simulator(**kwargs):
        captured.update(kwargs)

        class _S:
            def options(self, **_o):
                pass

        return _S()

    monkeypatch.setattr(sim.spice_circuit, "simulator", fake_simulator)
    sim._make_simulator(25)
    assert "ngspice_shared" not in captured and "simulator" not in captured


# --------------------------------------------------------------------------- #
# Sim.Compat schematic property -> converter.compat_hint                      #
# --------------------------------------------------------------------------- #


def _divider_with_compat(*compats):
    """Divider whose R1/R2 carry the given Sim.Compat values (None = omit)."""

    @circuit(name="divider_compat")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5")
        r1kw = {"symbol": "Device:R", "ref": "R1", "value": "1k"}
        r2kw = {"symbol": "Device:R", "ref": "R2", "value": "1k"}
        if compats and compats[0] is not None:
            r1kw["Sim.Compat"] = compats[0]
        if len(compats) > 1 and compats[1] is not None:
            r2kw["Sim.Compat"] = compats[1]
        r1 = Component(**r1kw)
        r2 = Component(**r2kw)
        vin = Net("VIN")
        out = Net("OUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        r1[1] += vin
        r1[2] += out
        r2[1] += out
        r2[2] += gnd

    return _c()


def test_sim_compat_property_sets_hint():
    conv = SpiceConverter(_divider_with_compat("psa"))
    conv.convert()
    assert conv.compat_hint == "psa"


def test_sim_compat_hint_used_when_no_explicit_arg():
    from circuit_synth.simulation.simulator import CircuitSimulator

    sim = CircuitSimulator(_divider_with_compat("lt"))
    assert sim._compat == "lt"


def test_explicit_compat_overrides_hint():
    from circuit_synth.simulation.simulator import CircuitSimulator

    sim = CircuitSimulator(_divider_with_compat("lt"), compat="psa")
    assert sim._compat == "psa"


def test_conflicting_sim_compat_is_validation_error():
    with pytest.raises(SimulationValidationError) as exc:
        SpiceConverter(_divider_with_compat("psa", "lt")).convert()
    assert "Sim.Compat" in str(exc.value)


# --------------------------------------------------------------------------- #
# X-line subckt params from Sim.Params                                        #
# --------------------------------------------------------------------------- #


def _subckt_part_circuit(sim_params=None):
    @circuit(name="subckt_params")
    def _c():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="1")
        kw = {
            "symbol": "Device:R",
            "ref": "R1",
            "Sim.Library": FIXTURE,
            "Sim.Name": "PSTEST",
        }
        if sim_params:
            kw["Sim.Params"] = sim_params
        x1 = Component(**kw)
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

    return _c()


def test_subckt_params_emitted_on_x_line():
    netlist = str(SpiceConverter(_subckt_part_circuit("gain=3")).convert())
    xline = next(
        (ln for ln in netlist.splitlines() if ln.strip().startswith("X")), None
    )
    assert xline is not None, netlist
    assert "gain=3" in xline.lower(), xline
    assert "PSTEST" in xline, xline


def test_subckt_without_params_has_no_kwargs():
    netlist = str(SpiceConverter(_subckt_part_circuit()).convert())
    xline = next(
        (ln for ln in netlist.splitlines() if ln.strip().startswith("X")), None
    )
    assert xline is not None and "=" not in xline, xline
