"""
Circuit-Synth AI Plugin for KiCad

A custom KiCad plugin that provides AI-powered circuit design assistance
integrated with the circuit-synth framework.
"""

try:
    from .plugin_action import CircuitSynthAI
    CircuitSynthAI().register()
except Exception as e:
    import logging
    root = logging.getLogger()
    root.debug(f"Circuit-Synth AI Plugin error: {repr(e)}")