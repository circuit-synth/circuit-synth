"""Honest component availability facade for the design loop.

One entry point -- :func:`check_availability` -- queries the credentialed
supplier APIs (DigiKey, JLCPCB) and returns *only real* results, with every
source that could not be queried recorded in a ``skipped`` map explaining why
(missing credentials, network error, ...). It never fabricates stock or prices
and never returns the JLC web scraper's demo data.

Design rules (mirroring simulation/model_store.resolve_mpn's honesty contract):
- Missing credentials is a *skip*, not an error and not fake data.
- Any network/auth failure is a *skip* with the error string, never a raise.
- Cached results are allowed; ``from_cache`` flags them when the underlying
  client makes that knowable (DigiKey/JLC currently do not expose it
  per-result, so it stays ``False`` -- we don't claim cache we can't confirm).
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


@dataclass
class PartAvailability:
    """A single real availability row from one supplier."""

    query: str
    source: str  # "digikey" | "jlcpcb" (official API) | "jlcpcb:jlcsearch" (keyless mirror)
    mpn: str
    stock: int
    unit_price: Optional[float]
    currency: str = "USD"
    from_cache: bool = False
    datasheet_url: Optional[str] = None
    lcsc: Optional[str] = None  # C-prefixed LCSC part number (JLC sources)


@dataclass
class AvailabilityReport:
    """Real results plus an honest account of every source that was skipped."""

    query: str
    results: List[PartAvailability] = field(default_factory=list)
    skipped: Dict[str, str] = field(default_factory=dict)  # source -> reason

    def __bool__(self) -> bool:
        return bool(self.results)


def _coerce_price(value) -> Optional[float]:
    """Best-effort float from a supplier price field; None if not numeric.

    JLC prices can be strings ("$1.20@100pcs") or price-break lists; we only
    keep a clean scalar, never a guessed number.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().lstrip("$")
        try:
            return float(cleaned.split("@")[0])
        except (ValueError, IndexError):
            return None
    return None


def _check_digikey(query: str, min_stock: int, max_results: int, report):
    """Query DigiKey; append real rows or record a skip reason."""
    try:
        from .digikey import DigiKeyComponentSearch
    except Exception as e:  # import-time failure -> honest skip
        report.skipped["digikey"] = f"unavailable: {e}"
        return

    try:
        search = DigiKeyComponentSearch(use_cache=True)
    except ValueError:
        # DigiKeyAPIClient raises ValueError specifically when credentials
        # are not configured.
        report.skipped["digikey"] = "no credentials"
        return
    except Exception as e:
        report.skipped["digikey"] = f"init error: {e}"
        return

    try:
        components = search.search_components(
            keyword=query, max_results=max_results, in_stock_only=False
        )
    except Exception as e:
        report.skipped["digikey"] = f"query error: {e}"
        return

    for c in components:
        if c.quantity_available < min_stock:
            continue
        report.results.append(
            PartAvailability(
                query=query,
                source="digikey",
                mpn=c.manufacturer_part_number,
                stock=int(c.quantity_available),
                unit_price=_coerce_price(c.unit_price),
                datasheet_url=c.datasheet_url,
            )
        )


def _check_jlcpcb(query: str, min_stock: int, max_results: int, report):
    """JLCPCB availability: official credentialed API if keyed, else keyless mirror.

    Never uses the demo web scraper. With ``JLCPCB_KEY``/``JLCPCB_SECRET`` set the
    official API is authoritative; otherwise the keyless tscircuit JLCSearch
    mirror provides real (daily) data so JLC is not skipped for want of keys.
    """
    if os.environ.get("JLCPCB_KEY") and os.environ.get("JLCPCB_SECRET"):
        _jlcpcb_official(query, min_stock, max_results, report)
    else:
        _jlcpcb_keyless(query, min_stock, max_results, report)


def _jlcpcb_official(query: str, min_stock: int, max_results: int, report):
    """Credentialed JLC parts API path (source ``jlcpcb``)."""
    try:
        from .jlcpcb.jlc_parts_lookup import JlcPartsInterface
    except Exception as e:
        report.skipped["jlcpcb"] = f"unavailable: {e}"
        return
    try:
        iface = JlcPartsInterface()
        rows = iface.search_components([query], max_results=max_results)
    except Exception as e:
        report.skipped["jlcpcb"] = f"query error: {e}"
        return
    for row in rows:
        stock = int(row.get("stock", 0) or 0)
        if stock < min_stock:
            continue
        report.results.append(
            PartAvailability(
                query=query,
                source="jlcpcb",
                mpn=row.get("manufacturer_part") or row.get("lcsc_part") or query,
                stock=stock,
                unit_price=_coerce_price(row.get("price")),
                datasheet_url=row.get("datasheet"),
                lcsc=row.get("lcsc_part"),
            )
        )


def _jlcpcb_keyless(query: str, min_stock: int, max_results: int, report):
    """Keyless tscircuit JLCSearch mirror (source ``jlcpcb:jlcsearch``)."""
    try:
        from .jlcpcb.jlcsearch import search_jlcsearch
    except Exception as e:
        report.skipped["jlcpcb"] = f"unavailable: {e}"
        return
    try:
        rows = search_jlcsearch(query, max_results=max_results)
    except Exception as e:
        report.skipped["jlcpcb"] = f"query error (jlcsearch): {e}"
        return
    for row in rows:
        stock = int(row.get("stock", 0) or 0)
        if stock < min_stock:
            continue
        report.results.append(
            PartAvailability(
                query=query,
                source="jlcpcb:jlcsearch",
                mpn=row.get("mpn") or row.get("lcsc") or query,
                stock=stock,
                unit_price=_coerce_price(row.get("price")),
                lcsc=row.get("lcsc"),
            )
        )


_CHECKERS = {"digikey": _check_digikey, "jlcpcb": _check_jlcpcb}


def check_availability(
    query: str,
    sources: Sequence[str] = ("digikey", "jlcpcb"),
    min_stock: int = 0,
    max_results: int = 5,
) -> AvailabilityReport:
    """Look up real availability for ``query`` across ``sources``.

    Returns an :class:`AvailabilityReport` whose ``results`` hold only real,
    credentialed data and whose ``skipped`` maps each un-queried source to a
    human-readable reason. Never raises for a missing credential or a network
    failure -- those become skips.

    Args:
        query: MPN or free-text part query (e.g. "2N7000", "10k 0603").
        sources: Which suppliers to try; unknown names are skipped.
        min_stock: Drop rows below this stock level.
        max_results: Max rows to request per source.
    """
    report = AvailabilityReport(query=query)
    for source in sources:
        checker = _CHECKERS.get(source)
        if checker is None:
            report.skipped[source] = "unknown source"
            continue
        checker(query, min_stock, max_results, report)
    logger.info(
        "check_availability(%r): %d result(s), skipped=%s",
        query,
        len(report.results),
        report.skipped,
    )
    return report
