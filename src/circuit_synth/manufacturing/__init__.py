"""
Manufacturing integrations for Circuit-Synth.

This module provides integrations with various PCB manufacturers and component suppliers:
- jlcpcb/: JLCPCB manufacturing and assembly services
- digikey/: DigiKey component sourcing
- unified_search: Multi-source component search
- pcbway/: PCBWay manufacturing services (future)
- oshpark/: OSH Park manufacturing services (future)
"""

from .unified_search import UnifiedComponentSearch, find_parts

__all__ = ["UnifiedComponentSearch", "find_parts"]
