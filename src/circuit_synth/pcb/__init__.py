"""
KiCad PCB API - PCB generation features have been removed.

PCB generation functionality is no longer included in the open source version.
Contact Circuit Synth for licensing information if you need PCB features.
"""


class PCBNotAvailableError(ImportError):
    """Raised when PCB features are accessed but not available."""

    pass


def _raise_not_available(*args, **kwargs):
    raise PCBNotAvailableError(
        "PCB generation features are not included in this version. "
        "Contact Circuit Synth for licensing information."
    )


# Stub classes that raise errors when used
class PCBBoard:
    def __init__(self, *args, **kwargs):
        _raise_not_available()


class PCBParser:
    def __init__(self, *args, **kwargs):
        _raise_not_available()


# Keep circuit-synth specific extensions that don't depend on kicad-pcb-api
from .kicad_cli import DRCResult, KiCadCLI, KiCadCLIError, get_kicad_cli

__all__ = [
    "PCBBoard",
    "PCBParser",
    "PCBNotAvailableError",
    "KiCadCLI",
    "get_kicad_cli",
    "DRCResult",
    "KiCadCLIError",
]
