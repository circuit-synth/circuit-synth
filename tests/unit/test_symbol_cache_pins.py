"""Symbol caches must build and round-trip kicad-sch-api SchematicPin objects."""

from pathlib import Path

import pytest

import circuit_synth.core.symbol_cache as core_cache
import circuit_synth.kicad.core.symbol_cache as kicad_cache

SYMBOLS = Path(__file__).resolve().parents[1] / "test_data" / "kicad_symbols"


@pytest.fixture(params=[core_cache, kicad_cache], ids=["core", "kicad.core"])
def cache(request, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KICAD_SYMBOL_DIR", str(SYMBOLS))
    return request.param.get_symbol_cache()


def test_get_symbol_has_pins(cache) -> None:
    symbol = cache.get_symbol("Device:R")

    assert symbol is not None
    assert sorted(p.number for p in symbol.pins) == ["1", "2"]


def test_serialize_round_trip_keeps_pin_data(cache) -> None:
    symbol = cache.get_symbol("Device:R")

    restored = cache._deserialize_symbol(cache._serialize_symbol(symbol))

    assert [(p.number, p.pin_type, p.rotation, p.position) for p in restored.pins] == [
        (p.number, p.pin_type, p.rotation, p.position) for p in symbol.pins
    ]
