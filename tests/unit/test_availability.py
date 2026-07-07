"""Honest availability facade (Stage 10.3).

Fully mocked -- no network, no credentials required. Verifies the facade:
- skips sources with no credentials (never fabricates stock),
- normalizes real DigiKey/JLC rows into PartAvailability,
- never returns the JLC web-scraper demo data,
- handles a mix of one-up / one-down source.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from circuit_synth.manufacturing.availability import (
    AvailabilityReport,
    PartAvailability,
    check_availability,
)


def _digikey_component(mpn, stock, price, ds="http://d.example/ds.pdf"):
    return SimpleNamespace(
        manufacturer_part_number=mpn,
        quantity_available=stock,
        unit_price=price,
        datasheet_url=ds,
    )


def test_no_digikey_creds_skips_digikey(monkeypatch):
    """DigiKey with no creds -> honest skip, zero fabricated results."""
    with patch(
        "circuit_synth.manufacturing.digikey.DigiKeyComponentSearch",
        side_effect=ValueError("DigiKey API credentials not configured"),
    ):
        report = check_availability("2N7000", sources=("digikey",))

    assert isinstance(report, AvailabilityReport)
    assert report.results == []
    assert report.skipped["digikey"] == "no credentials"
    assert not report  # __bool__ is False when empty


def test_digikey_hit_normalized():
    """A mocked DigiKey result becomes a normalized PartAvailability."""
    fake_search = MagicMock()
    fake_search.search_components.return_value = [
        _digikey_component("2N7000", 50000, 0.12),
        _digikey_component("2N7002", 3, 0.05),  # below min_stock filter below
    ]
    with patch(
        "circuit_synth.manufacturing.digikey.DigiKeyComponentSearch",
        return_value=fake_search,
    ):
        report = check_availability("2N7000", sources=("digikey",), min_stock=100)

    dk = [r for r in report.results if r.source == "digikey"]
    assert len(dk) == 1  # the stock=3 row filtered out
    row = dk[0]
    assert isinstance(row, PartAvailability)
    assert row.mpn == "2N7000"
    assert row.stock == 50000
    assert row.unit_price == pytest.approx(0.12)
    assert row.datasheet_url == "http://d.example/ds.pdf"


def test_jlc_official_api_when_keyed(monkeypatch):
    """With JLC creds set, the facade calls the credentialed API (source jlcpcb)."""
    monkeypatch.setenv("JLCPCB_KEY", "k")
    monkeypatch.setenv("JLCPCB_SECRET", "s")

    fake_iface = MagicMock()
    fake_iface.search_components.return_value = [
        {
            "manufacturer_part": "2N7000",
            "lcsc_part": "C8492",
            "stock": 12000,
            "price": "$0.03@100pcs",
            "datasheet": "http://jlc.example/2n7000.pdf",
        }
    ]
    with patch(
        "circuit_synth.manufacturing.jlcpcb.jlc_parts_lookup.JlcPartsInterface",
        return_value=fake_iface,
    ):
        report = check_availability("2N7000", sources=("jlcpcb",))

    jlc = [r for r in report.results if r.source == "jlcpcb"]
    assert len(jlc) == 1
    assert jlc[0].mpn == "2N7000"
    assert jlc[0].stock == 12000
    assert jlc[0].unit_price == pytest.approx(0.03)  # parsed from "$0.03@100pcs"
    assert jlc[0].lcsc == "C8492"
    # Demo-data marker must never appear in real results.
    assert all(getattr(r, "demo_data", None) is None for r in report.results)


def test_jlc_keyless_used_without_creds(monkeypatch):
    """No JLC creds -> keyless tscircuit mirror, tagged source jlcpcb:jlcsearch."""
    monkeypatch.delenv("JLCPCB_KEY", raising=False)
    monkeypatch.delenv("JLCPCB_SECRET", raising=False)

    with patch(
        "circuit_synth.manufacturing.jlcpcb.jlcsearch.search_jlcsearch",
        return_value=[
            {"mpn": "2N7000", "lcsc": "C9114", "stock": 4695, "price": 0.0321,
             "package": "TO-92", "basic": False, "description": ""},
            {"mpn": "2N7000", "lcsc": "C232838", "stock": 5, "price": 0.19,
             "package": "TO-92-3L", "basic": False, "description": ""},
        ],
    ) as mock_search:
        report = check_availability("2N7000", sources=("jlcpcb",), min_stock=100)

    mock_search.assert_called_once()  # keyless path really used
    jlc = [r for r in report.results if r.source == "jlcpcb:jlcsearch"]
    assert len(jlc) == 1  # the stock=5 row dropped by min_stock
    assert jlc[0].mpn == "2N7000"
    assert jlc[0].stock == 4695
    assert jlc[0].lcsc == "C9114"
    assert jlc[0].unit_price == pytest.approx(0.0321)
    assert "jlcpcb" not in report.skipped  # a successful query is not a skip


def test_jlc_keyless_network_error_is_a_skip(monkeypatch):
    """Keyless mirror network failure -> honest skip, not a raise."""
    monkeypatch.delenv("JLCPCB_KEY", raising=False)
    monkeypatch.delenv("JLCPCB_SECRET", raising=False)

    with patch(
        "circuit_synth.manufacturing.jlcpcb.jlcsearch.search_jlcsearch",
        side_effect=RuntimeError("connection timed out"),
    ):
        report = check_availability("2N7000", sources=("jlcpcb",))

    assert report.results == []
    assert "jlcsearch" in report.skipped["jlcpcb"]
    assert "connection timed out" in report.skipped["jlcpcb"]


def test_mixed_one_up_one_down(monkeypatch):
    """DigiKey up, JLC keyless mirror down (network error): one result, JLC skipped."""
    monkeypatch.delenv("JLCPCB_KEY", raising=False)
    monkeypatch.delenv("JLCPCB_SECRET", raising=False)

    fake_search = MagicMock()
    fake_search.search_components.return_value = [
        _digikey_component("LM358", 8000, 0.15)
    ]
    with patch(
        "circuit_synth.manufacturing.digikey.DigiKeyComponentSearch",
        return_value=fake_search,
    ), patch(
        "circuit_synth.manufacturing.jlcpcb.jlcsearch.search_jlcsearch",
        side_effect=RuntimeError("mirror unreachable"),
    ):
        report = check_availability("LM358")

    assert len(report.results) == 1
    assert report.results[0].source == "digikey"
    assert "jlcsearch" in report.skipped["jlcpcb"]


def test_network_error_is_a_skip_not_a_raise(monkeypatch):
    """A supplier query exception becomes a skip reason, never propagates."""
    monkeypatch.delenv("JLCPCB_KEY", raising=False)
    monkeypatch.delenv("JLCPCB_SECRET", raising=False)

    fake_search = MagicMock()
    fake_search.search_components.side_effect = RuntimeError("connection reset")
    with patch(
        "circuit_synth.manufacturing.digikey.DigiKeyComponentSearch",
        return_value=fake_search,
    ):
        report = check_availability("2N7000", sources=("digikey",))

    assert report.results == []
    assert "query error" in report.skipped["digikey"]
    assert "connection reset" in report.skipped["digikey"]


def test_unknown_source_skipped(monkeypatch):
    monkeypatch.delenv("JLCPCB_KEY", raising=False)
    monkeypatch.delenv("JLCPCB_SECRET", raising=False)
    report = check_availability("2N7000", sources=("mouser",))
    assert report.skipped["mouser"] == "unknown source"


def test_jlcsearch_client_parses_response():
    """The keyless client normalizes the tscircuit JSON shape (mocked HTTP)."""
    from circuit_synth.manufacturing.jlcpcb.jlcsearch import search_jlcsearch

    payload = {
        "components": [
            {"lcsc": 9114, "mfr": "2N7000", "package": "TO-92",
             "is_basic": False, "stock": 4695, "price": 0.032142857,
             "description": ""},
        ]
    }
    fake_resp = MagicMock()
    fake_resp.json.return_value = payload
    fake_resp.raise_for_status.return_value = None
    with patch("requests.get", return_value=fake_resp) as mock_get:
        rows = search_jlcsearch("2N7000", max_results=5)

    # Query is URL-encoded into the endpoint.
    assert "q=2N7000" in mock_get.call_args[0][0]
    assert len(rows) == 1
    r = rows[0]
    assert r["mpn"] == "2N7000"
    assert r["lcsc"] == "C9114"  # C-prefixed
    assert r["stock"] == 4695
    assert r["price"] == pytest.approx(0.032142857)
    assert r["basic"] is False
