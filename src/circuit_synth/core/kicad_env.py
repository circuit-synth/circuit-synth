"""KiCad environment variable lookup."""

import os

# KiCad installers (e.g. Nix, Flatpak) often set only the versioned variable
SYMBOL_DIR_ENV_VARS = (
    "KICAD_SYMBOL_DIR",
    "KICAD10_SYMBOL_DIR",
    "KICAD9_SYMBOL_DIR",
    "KICAD8_SYMBOL_DIR",
    "KICAD7_SYMBOL_DIR",
    "KICAD6_SYMBOL_DIR",
)


def kicad_symbol_dir_env() -> str:
    """
    Return the KiCad symbol directory setting from the environment.

    Checks ``KICAD_SYMBOL_DIR`` first, then versioned variables newest first.

    Returns:
        The first non-empty value (may contain multiple paths separated by
        ``os.pathsep``), or an empty string if none is set.
    """
    for var in SYMBOL_DIR_ENV_VARS:
        value = os.environ.get(var, "")
        if value:
            return value
    return ""
