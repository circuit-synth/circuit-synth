"""Local, MPN-keyed SPICE model store (Stage 9.4).

Bridges "a real orderable part" to "its SPICE model" *without* pretending any
distributor serves SPICE files. The store is a plain directory the user (or a
future explicit tool) drops vendor ``.lib``/``.sub`` files into, keyed by MPN:

    ~/.circuit_synth/spice_models/
        models/<MPN>.lib          # user- or tool-dropped vendor model files
        index.json                # {mpn: {manufacturer, datasheet_url, model_path, ...}}

The SPICE converter consults it *above* the datasheet-fit tier: a device whose
MPN/value matches a stored file is attached exactly as if ``Sim.Library`` named
that file (tier ``vendor_lib``, source ``local_store``).

``resolve_mpn`` optionally enriches ``index.json`` with DigiKey metadata
(manufacturer, datasheet URL, parameters) *and points the user at where to
download the vendor model* -- it never scrapes or auto-downloads vendor sites.
Everything degrades gracefully with no credentials and no network: without a
stored file the converter simply falls back to the datasheet-fit/generic tiers.
"""

import json
import logging
import os
import shutil
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Environment override for the store root (used by tests and power users).
STORE_ENV_VAR = "CIRCUIT_SYNTH_SPICE_MODEL_STORE"

# Recognized SPICE model file extensions, in preference order.
_MODEL_EXTS = (".lib", ".sub", ".spi", ".cir", ".mod")

# Where each manufacturer publishes official SPICE models -- surfaced to the user
# by resolve_mpn so they can fetch the real model themselves (we never scrape).
VENDOR_MODEL_SOURCES = {
    "Texas Instruments": "https://www.ti.com/design-resources/design-tools-simulation/models-simulators/overview.html",
    "Analog Devices": "https://www.analog.com/en/resources/simulation-models.html",
    "STMicroelectronics": "https://www.st.com/",
    "onsemi": "https://www.onsemi.com/design/tools-software/webdesigner+/downloadable-tools-and-models",
    "ON Semiconductor": "https://www.onsemi.com/design/tools-software/webdesigner+/downloadable-tools-and-models",
    "Infineon": "https://www.infineon.com/cms/en/design-support/finder-selection-tools/product-finder/simulation-model/",
    "Infineon Technologies": "https://www.infineon.com/cms/en/design-support/finder-selection-tools/product-finder/simulation-model/",
    "Diodes Incorporated": "https://www.diodes.com/design/tools/spice-models/",
    "Nexperia": "https://www.nexperia.com/support/models-simulations/spice-models.html",
    "Vishay": "https://www.vishay.com/en/how/design-support-tools/spice-models/",
}


class SpiceModelStore:
    """A directory of MPN-keyed SPICE model files plus a JSON metadata index."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(
            os.path.expanduser("~"), ".circuit_synth", "spice_models"
        )

    @property
    def models_dir(self) -> str:
        return os.path.join(self.base_dir, "models")

    @property
    def index_path(self) -> str:
        return os.path.join(self.base_dir, "index.json")

    # -- index ------------------------------------------------------------- #

    def load_index(self) -> Dict[str, dict]:
        try:
            with open(self.index_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_index(self, index: Dict[str, dict]) -> None:
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as fh:
            json.dump(index, fh, indent=2, sort_keys=True)

    # -- lookup ------------------------------------------------------------ #

    def lookup(self, mpn) -> Optional[str]:
        """Absolute path to the stored model file for ``mpn``, or None.

        Tries ``models/<MPN>.<ext>`` for each known extension, then any
        ``model_path`` recorded in the index. Case-sensitive on the filename;
        callers pass the MPN as written.
        """
        if not mpn:
            return None
        name = str(mpn)
        for ext in _MODEL_EXTS:
            cand = os.path.join(self.models_dir, f"{name}{ext}")
            if os.path.exists(cand):
                return os.path.abspath(cand)
        entry = self.load_index().get(name)
        if entry:
            path = entry.get("model_path")
            if path and os.path.exists(path):
                return os.path.abspath(path)
        return None

    # -- population -------------------------------------------------------- #

    def add_model(self, mpn, model_path: str, **metadata) -> str:
        """Copy an existing model file into the store under ``mpn`` and index it.

        Returns the stored path. Extra kwargs (manufacturer, datasheet_url, ...)
        are recorded in the index entry.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(model_path)
        os.makedirs(self.models_dir, exist_ok=True)
        ext = os.path.splitext(model_path)[1] or ".lib"
        dest = os.path.join(self.models_dir, f"{mpn}{ext}")
        shutil.copyfile(model_path, dest)
        self.record_metadata(mpn, model_path=os.path.abspath(dest), **metadata)
        logger.info(f"Added SPICE model for {mpn} -> {dest}")
        return os.path.abspath(dest)

    def record_metadata(self, mpn, **metadata) -> None:
        """Merge metadata into the index entry for ``mpn`` (no file required)."""
        index = self.load_index()
        entry = index.get(str(mpn), {})
        entry.update({k: v for k, v in metadata.items() if v is not None})
        index[str(mpn)] = entry
        self.save_index(index)


def get_model_store(base_dir: Optional[str] = None) -> SpiceModelStore:
    """Default store, honoring the ``CIRCUIT_SYNTH_SPICE_MODEL_STORE`` override."""
    return SpiceModelStore(base_dir or os.environ.get(STORE_ENV_VAR))


def vendor_source_url(manufacturer: Optional[str]) -> Optional[str]:
    """Official SPICE-model download page for a manufacturer, if known."""
    if not manufacturer:
        return None
    key = str(manufacturer).strip()
    if key in VENDOR_MODEL_SOURCES:
        return VENDOR_MODEL_SOURCES[key]
    low = key.lower()
    for name, url in VENDOR_MODEL_SOURCES.items():
        if name.lower() in low or low in name.lower():
            return url
    return None


def resolve_mpn(mpn, store: Optional[SpiceModelStore] = None) -> Optional[dict]:
    """Enrich the store index with DigiKey metadata for ``mpn`` (best effort).

    Optional and offline-safe: requires DigiKey credentials + network. On success
    records ``{manufacturer, datasheet_url, parameters}`` into ``index.json`` and
    logs where to download the vendor's official SPICE model (we never fetch it
    automatically). Returns the metadata dict, or None if enrichment was
    unavailable. Never raises.
    """
    store = store or get_model_store()
    try:
        from ..manufacturing.digikey.component_search import DigiKeyComponentSearch

        results = DigiKeyComponentSearch().search_components(keyword=str(mpn))
    except Exception as exc:  # missing creds, no network, import error, ...
        logger.info(f"DigiKey metadata enrichment unavailable for {mpn}: {exc}")
        return None

    match = None
    for comp in results or []:
        if str(getattr(comp, "manufacturer_part_number", "")).strip() == str(mpn):
            match = comp
            break
    if match is None and results:
        match = results[0]
    if match is None:
        logger.info(f"No DigiKey match for {mpn}")
        return None

    meta = {
        "manufacturer": getattr(match, "manufacturer", None),
        "datasheet_url": getattr(match, "datasheet_url", None),
        "parameters": getattr(match, "parameters", None),
    }
    store.record_metadata(mpn, **meta)
    url = vendor_source_url(meta.get("manufacturer"))
    if url:
        logger.info(
            f"{mpn}: download the official SPICE model from {meta['manufacturer']} "
            f"at {url}, then drop it in {store.models_dir}/{mpn}.lib"
        )
    return meta
