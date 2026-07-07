"""Keyless JLCPCB availability via the tscircuit JLCSearch mirror.

The official JLC parts API needs credentials (``JLCPCB_KEY``/``JLCPCB_SECRET``);
the local web scraper has no live data (it only serves canned demo rows). This
module fills the gap with a **keyless** live source: the community-run
`tscircuit JLCSearch <https://github.com/tscircuit/jlcsearch>`_ service, which
indexes JLCPCB's daily parts data and exposes a plain JSON search endpoint.

    GET https://jlcsearch.tscircuit.com/api/search?q=<query>&limit=<n>
    -> {"components": [
         {"lcsc": 9114, "mfr": "2N7000", "package": "TO-92",
          "is_basic": false, "stock": 4695, "price": 0.0321, ...}, ...]}

Provenance caveat: this is a third-party mirror built from JLCPCB's *daily*
dumps, so stock/price may lag the official API by up to ~a day. Rows carry
``source="jlcpcb:jlcsearch"`` so the distinction is visible downstream. No key,
no scraping of demo data -- real numbers or an honest failure.
"""

import logging
from typing import Any, Dict, List
from urllib.parse import quote

logger = logging.getLogger(__name__)

JLCSEARCH_URL = "https://jlcsearch.tscircuit.com/api/search"


def search_jlcsearch(
    query: str, max_results: int = 5, timeout_s: float = 10.0
) -> List[Dict[str, Any]]:
    """Search JLCPCB availability via the keyless tscircuit JLCSearch API.

    Returns a list of normalized rows::

        {"mpn", "lcsc", "stock", "price", "package", "basic", "description"}

    where ``lcsc`` is the ``C``-prefixed LCSC part number and ``price`` is a
    float unit price (USD) or ``None``. Raises on network/HTTP/parse failure so
    the caller can record an honest skip; an empty match returns ``[]``.
    """
    import requests  # lazy: keeps import failures out of module load

    url = f"{JLCSEARCH_URL}?q={quote(query)}&limit={int(max_results)}"
    resp = requests.get(url, timeout=timeout_s)
    resp.raise_for_status()
    payload = resp.json()

    rows: List[Dict[str, Any]] = []
    for c in payload.get("components", [])[:max_results]:
        lcsc = c.get("lcsc")
        price = c.get("price")
        rows.append(
            {
                "mpn": c.get("mfr") or "",
                "lcsc": f"C{lcsc}" if lcsc is not None else None,
                "stock": int(c.get("stock", 0) or 0),
                "price": float(price) if isinstance(price, (int, float)) else None,
                "package": c.get("package"),
                "basic": bool(c.get("is_basic", False)),
                "description": c.get("description") or "",
            }
        )
    logger.info("jlcsearch: %d row(s) for %r", len(rows), query)
    return rows
