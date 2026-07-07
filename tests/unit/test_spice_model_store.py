"""Local MPN-keyed SPICE model store + optional DigiKey enrichment (Stage 9.4).

The store maps an MPN to a dropped-in vendor model file; the converter consults it
above the datasheet-fit tier so a stored file is attached like an implicit
Sim.Library (tier vendor_lib, source local_store). Everything is offline-safe:
without a stored file the converter falls back to datasheet-fit/generic, and the
DigiKey enrichment is best-effort and mocked here (no network in the suite).
"""

import os
from unittest import mock

import pytest

from circuit_synth import Component, Net, circuit
from circuit_synth.simulation.model_store import (
    SpiceModelStore,
    get_model_store,
    resolve_mpn,
    vendor_source_url,
)


def _symbols_available() -> bool:
    try:
        Component(symbol="Device:R", ref="R1", value="1k")
        return True
    except Exception:
        return False


def _pyspice_available() -> bool:
    try:
        from circuit_synth.simulation.converter import PYSPICE_AVAILABLE

        return PYSPICE_AVAILABLE
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _symbols_available(), reason="KiCad symbol libraries not available"
)
needs_pyspice = pytest.mark.skipif(
    not _pyspice_available(), reason="PySpice not available"
)

CUSTOM_DIODE = """* stored vendor diode
.model STOREDIODE D (IS=1e-14 RS=0.3 N=1.4 BV=60)
"""


def _seed_store(tmp_path, mpn, text=CUSTOM_DIODE):
    store = SpiceModelStore(base_dir=str(tmp_path / "spice_models"))
    os.makedirs(store.models_dir, exist_ok=True)
    with open(os.path.join(store.models_dir, f"{mpn}.lib"), "w", encoding="utf-8") as f:
        f.write(text)
    return store


# --------------------------------------------------------------------------- #
# Store basics                                                                 #
# --------------------------------------------------------------------------- #


def test_store_lookup_and_index_roundtrip(tmp_path):
    store = _seed_store(tmp_path, "1N4148X")
    path = store.lookup("1N4148X")
    assert path is not None and path.endswith("1N4148X.lib")
    assert store.lookup("NOTHERE") is None

    store.record_metadata(
        "1N4148X", manufacturer="Acme", datasheet_url="http://ex/ds.pdf"
    )
    idx = store.load_index()
    assert idx["1N4148X"]["manufacturer"] == "Acme"
    assert idx["1N4148X"]["datasheet_url"] == "http://ex/ds.pdf"


def test_get_model_store_honors_env(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CIRCUIT_SYNTH_SPICE_MODEL_STORE", str(tmp_path / "custom_store")
    )
    store = get_model_store()
    assert store.base_dir == str(tmp_path / "custom_store")


def test_vendor_source_url_known_and_unknown():
    assert vendor_source_url("Texas Instruments")
    assert vendor_source_url("onsemi")
    assert vendor_source_url("Nonexistent Vendor Ltd") is None


# --------------------------------------------------------------------------- #
# Converter integration                                                        #
# --------------------------------------------------------------------------- #


@needs_pyspice
def test_store_model_preferred_over_datasheet_fit(tmp_path, monkeypatch):
    """A stored file for the MPN is attached as vendor_lib, above datasheet-fit."""
    _seed_store(tmp_path, "1N4148")  # same name as a datasheet-fit library part
    monkeypatch.setenv(
        "CIRCUIT_SYNTH_SPICE_MODEL_STORE", str(tmp_path / "spice_models")
    )
    from circuit_synth.simulation.converter import SpiceConverter

    @circuit(name="StoreDiode")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        d1 = Component(symbol="Device:D", ref="D1", value="1N4148")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        out = Net("OUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        d1[2] += vin  # A (anode): keeps DD1 VIN OUT node order, schematic-correct
        d1[1] += out  # K (cathode)
        r1[1] += out
        r1[2] += gnd

    conv = SpiceConverter(cir())
    netlist = str(conv.convert())
    assert ".include" in netlist
    assert "DD1 VIN OUT STOREDIODE" in netlist
    prov = conv.model_provenance["D1"]
    assert prov.tier == "vendor_lib"
    assert prov.source == "local_store"


@needs_pyspice
def test_no_store_falls_back_to_datasheet_fit(tmp_path, monkeypatch):
    """With an empty store, a named part still resolves datasheet-fit (unchanged)."""
    monkeypatch.setenv(
        "CIRCUIT_SYNTH_SPICE_MODEL_STORE", str(tmp_path / "empty_store")
    )
    from circuit_synth.simulation.converter import SpiceConverter

    @circuit(name="NoStore")
    def cir():
        v1 = Component(symbol="Simulation_SPICE:VDC", ref="V1", value="5V")
        d1 = Component(symbol="Device:D", ref="D1", value="1N4148")
        r1 = Component(symbol="Device:R", ref="R1", value="1k")
        vin = Net("VIN")
        out = Net("OUT")
        gnd = Net("GND")
        v1[1] += vin
        v1[2] += gnd
        d1[2] += vin  # A (anode): keeps DD1 VIN OUT node order, schematic-correct
        d1[1] += out  # K (cathode)
        r1[1] += out
        r1[2] += gnd

    conv = SpiceConverter(cir())
    netlist = str(conv.convert())
    assert ".model 1N4148 D" in netlist
    assert conv.model_provenance["D1"].tier == "datasheet_fit"


# --------------------------------------------------------------------------- #
# DigiKey enrichment (mocked; never touches the network)                       #
# --------------------------------------------------------------------------- #


def test_resolve_mpn_records_metadata(tmp_path):
    store = SpiceModelStore(base_dir=str(tmp_path / "spice_models"))

    fake = mock.Mock()
    fake.manufacturer_part_number = "LM358"
    fake.manufacturer = "Texas Instruments"
    fake.datasheet_url = "https://www.ti.com/lit/ds/symlink/lm358.pdf"
    fake.parameters = {"Package": "SOIC-8"}

    with mock.patch(
        "circuit_synth.manufacturing.digikey.component_search.DigiKeyComponentSearch"
    ) as cls:
        cls.return_value.search_components.return_value = [fake]
        meta = resolve_mpn("LM358", store=store)

    assert meta["manufacturer"] == "Texas Instruments"
    idx = store.load_index()
    assert idx["LM358"]["datasheet_url"].endswith("lm358.pdf")


def test_resolve_mpn_offline_returns_none(tmp_path):
    store = SpiceModelStore(base_dir=str(tmp_path / "spice_models"))
    with mock.patch(
        "circuit_synth.manufacturing.digikey.component_search.DigiKeyComponentSearch",
        side_effect=RuntimeError("no credentials"),
    ):
        assert resolve_mpn("LM358", store=store) is None
    # No index written, nothing raised.
    assert store.load_index() == {}
