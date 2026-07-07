"""Interop adapters that bridge circuit_synth to *external* EDA toolchains.

Currently this package hosts the optional SKiDL render backend (Stage 13): a way
to hand a circuit_synth :class:`~circuit_synth.core.circuit.Circuit` to SKiDL's
force-directed placer + maze router and get back a wire-routed ``.kicad_sch``.

Nothing here is imported at ``import circuit_synth`` time, and ``skidl`` is never a
hard dependency of circuit_synth -- the render runs in a separate interpreter via
subprocess (see :mod:`circuit_synth.interop.skidl_export`).
"""

from .skidl_export import export_skidl_script, render_with_skidl

__all__ = ["export_skidl_script", "render_with_skidl"]
