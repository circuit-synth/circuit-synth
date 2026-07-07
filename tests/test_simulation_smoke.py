"""Smoke test: a resistor divider simulates to the expected operating point.

This exercises the full circuit-synth simulation path (Circuit.simulate() ->
SpiceConverter -> PySpice -> ngspice shared library) end to end. On Windows the
ngspice DLL bundled with KiCad is auto-configured by
``circuit_synth.simulation.simulator``; on macOS Homebrew's libngspice is used.

The test is skipped (not failed) when PySpice or a loadable ngspice library is
not available, so it is safe to run in CI environments without SPICE.
"""

import pytest

from circuit_synth import Component, Net, circuit


def _ngspice_available() -> bool:
    """True only if PySpice can actually load and start an ngspice instance.

    Importing the simulator module triggers the per-platform LIBRARY_PATH
    auto-configuration (e.g. KiCad's bundled ngspice.dll on Windows); creating
    an instance proves the shared library really loads on this machine.
    """
    try:
        from circuit_synth.simulation.simulator import PYSPICE_AVAILABLE

        if not PYSPICE_AVAILABLE:
            return False
        from PySpice.Spice.NgSpice.Shared import NgSpiceShared

        NgSpiceShared.new_instance()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _ngspice_available(),
    reason="PySpice or a loadable ngspice library is not available",
)


@circuit(name="Divider_Smoke")
def _divider():
    """5V -> 3.333V resistor divider: R1=1k (VIN->VOUT), R2=2k (VOUT->GND)."""
    r1 = Component(symbol="Device:R", ref="R1", value="1k")
    r2 = Component(symbol="Device:R", ref="R2", value="2k")
    vin_5v = Net("VIN_5V")
    vout_3v3 = Net("VOUT_3V3")
    gnd = Net("GND")
    r1[1] += vin_5v
    r1[2] += vout_3v3
    r2[1] += vout_3v3
    r2[2] += gnd


def test_divider_operating_point():
    """VOUT_3V3 settles at Vin * R2/(R1+R2) = 5 * 2/3 = 3.333 V."""
    c = _divider()

    sim = c.simulate()
    result = sim.operating_point()

    vout = result.get_voltage("VOUT_3V3")
    assert vout == pytest.approx(10 / 3, abs=0.01), f"VOUT_3V3={vout}, expected 3.333"

    vin = result.get_voltage("VIN_5V")
    assert vin == pytest.approx(5.0, abs=0.01), f"VIN_5V={vin}, expected 5.0"


def test_ngspice_init_banners_are_quiet():
    """The benign v46 / spinit init banners don't reach the logs (finding F2).

    Import-time fixes in ``simulation.simulator`` register KiCad's ngspice v46 as a
    known version (kills "Unsupported Ngspice version 46") and filter the harmless
    "can't find the initialization file spinit" line. Real sim-time warnings/errors
    are untouched -- only these two init banners are silenced.
    """
    import logging

    from PySpice.Spice.NgSpice.Shared import NgSpiceShared

    ngspice_logger = logging.getLogger("PySpice.Spice.NgSpice.Shared.NgSpiceShared")

    records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = _Capture()
    ngspice_logger.addHandler(handler)
    try:
        NgSpiceShared.new_instance()
    finally:
        ngspice_logger.removeHandler(handler)

    joined = "\n".join(records)
    assert "Unsupported Ngspice version" not in joined, joined
    assert "initialization file spinit" not in joined, joined
