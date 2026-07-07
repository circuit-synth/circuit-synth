"""Footprint-existence check at schematic-generation time (Stage 22.9).

Run 3 shipped three guessed footprint ids (e.g. ``VQFN-20...EP2.55``,
``L_Bourns-SRN6045``, ``VSSOP-8_3.0x3.0``) that do not exist in KiCad 10's
libraries; generation never noticed and they only surfaced as
``footprint_link_issues`` warnings in a post-generation KiCad ERC.

This module warns (never fails) when a component's ``Lib:Name`` footprint id is
absent from the installed KiCad footprint libraries. If no footprint root can be
located (no KiCad install / a custom ``KICAD_SYMBOL_DIR`` we can't map), the check
degrades silently -- the same graceful behavior as the optional kicad-cli passes.

Footprint libraries live in ``<share>/kicad/footprints/<Lib>.pretty/<Name>.kicad_mod``,
a sibling of the ``symbols`` dir the symbol cache already resolves, so the roots
are derived from that same discovery.
"""

import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

logger = logging.getLogger(__name__)


def _footprint_root_dirs() -> List[Path]:
    """KiCad footprint root dirs (each holds ``<Lib>.pretty`` subdirs).

    Derived from the symbol cache's resolved symbol dirs by swapping the trailing
    ``symbols`` path component for ``footprints``. Roots that don't end in
    ``symbols`` can't be mapped and are skipped. Returns ``[]`` when nothing is
    found (e.g. no KiCad install) so the caller skips silently.
    """
    try:
        from ..kicad_symbol_cache import SymbolLibCache

        symbol_dirs = SymbolLibCache._parse_kicad_symbol_dirs()
    except Exception as e:  # pragma: no cover - defensive
        logger.debug(f"Footprint check: could not resolve symbol dirs: {e}")
        return []

    roots: List[Path] = []
    seen: Set[str] = set()
    for sd in symbol_dirs:
        if sd.name != "symbols":
            continue
        fp_root = sd.parent / "footprints"
        key = str(fp_root).lower()
        if key in seen:
            continue
        seen.add(key)
        if fp_root.is_dir():
            roots.append(fp_root)
    return roots


def _lib_footprints(
    lib: str, roots: List[Path], cache: Dict[str, Optional[Set[str]]]
) -> Optional[Set[str]]:
    """Set of footprint stems in ``<lib>.pretty`` across all roots (cached per-lib).

    Returns ``None`` when no ``<lib>.pretty`` dir exists in any root (library
    missing), else the set of ``*.kicad_mod`` stems. Cached so an N-part design
    scans each distinct library once, not once per part.
    """
    if lib in cache:
        return cache[lib]

    names: Optional[Set[str]] = None
    for root in roots:
        pretty = root / f"{lib}.pretty"
        if pretty.is_dir():
            if names is None:
                names = set()
            try:
                names.update(p.stem for p in pretty.glob("*.kicad_mod"))
            except OSError as e:  # pragma: no cover - defensive
                logger.debug(f"Footprint check: cannot list {pretty}: {e}")
    cache[lib] = names
    return names


def check_footprints(components: Iterable, roots: Optional[List[Path]] = None) -> int:
    """Warn for each component whose ``Lib:Name`` footprint id doesn't exist.

    Args:
        components: iterable of objects with ``.reference`` and ``.footprint``.
        roots: footprint root dirs (each holding ``<Lib>.pretty``). Defaults to
            the discovered KiCad roots; an empty list means "skip silently".

    Returns:
        Number of warnings emitted (0 also when the check is skipped).
    """
    if roots is None:
        roots = _footprint_root_dirs()
    if not roots:
        logger.debug("Footprint check skipped: no KiCad footprint libraries found")
        return 0

    cache: Dict[str, Optional[Set[str]]] = {}
    seen: Set[str] = set()
    warnings = 0
    for comp in components:
        fp = (getattr(comp, "footprint", "") or "").strip()
        if ":" not in fp:
            continue  # empty or not a Lib:Name id -> nothing to verify
        ref = getattr(comp, "reference", "?")
        dedupe_key = f"{ref}\0{fp}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        lib, name = fp.split(":", 1)
        names = _lib_footprints(lib, roots, cache)
        if names is None or name not in names:
            logger.warning(
                f"{ref}: footprint '{fp}' not found in KiCad libraries "
                f"(will show as footprint_link_issues in ERC)"
            )
            warnings += 1
    return warnings
