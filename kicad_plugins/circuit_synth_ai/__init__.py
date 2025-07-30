"""
Circuit-Synth AI Plugin for KiCad

A custom KiCad plugin that provides AI-powered circuit design assistance
integrated with the circuit-synth framework.

This plugin supports both KiCad 8.x (legacy) and KiCad 9.x (IPC API) formats.
"""

try:
    # Try to import pcbnew (available in KiCad's Python environment)
    import pcbnew
    from .plugin_action import CircuitSynthAI
    
    # Register the plugin using the legacy ActionPlugin system
    CircuitSynthAI().register()
    
except ImportError as e:
    # If pcbnew is not available, this might be running outside KiCad
    # or in KiCad 9's new IPC system
    import logging
    logging.getLogger(__name__).debug(f"pcbnew not available: {e}")
    
    # For KiCad 9 IPC API, the main.py file handles plugin execution
    pass

except Exception as e:
    import logging
    root = logging.getLogger()
    root.debug(f"Circuit-Synth AI Plugin error: {repr(e)}")