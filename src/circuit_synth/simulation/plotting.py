"""Headless PNG plot saving for simulation results.

Unlike :mod:`circuit_synth.simulation.visualization` (which drives
``matplotlib.pyplot`` with an interactive backend and ``show=True`` defaults),
this module uses matplotlib's object-oriented Agg backend directly -- no global
pyplot state, no display, never blocks. That makes it safe to call from an
automated design loop / CI on a headless machine.

Each function takes a :class:`~circuit_synth.simulation.simulator.SimulationResult`
and an output path, writes a PNG, and returns the written :class:`pathlib.Path`.
If matplotlib is unavailable they log an error and return ``None`` (mirroring the
soft-fail contract of ``visualization.py``) rather than raising.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)

try:
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - matplotlib is a core dependency
    MATPLOTLIB_AVAILABLE = False


def _new_figure(figsize=(8, 5), dpi=150):
    """A fresh Agg-backed Figure with no pyplot involvement (headless-safe)."""
    fig = Figure(figsize=figsize, dpi=dpi)
    FigureCanvasAgg(fig)  # attaching the Agg canvas is what enables savefig()
    return fig


def _prepare(path: Union[str, Path]) -> Optional[Path]:
    """Return a Path with parents created, or None if matplotlib is missing."""
    if not MATPLOTLIB_AVAILABLE:
        logger.error("matplotlib required for plot saving; skipping %s", path)
        return None
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_bode_plot(
    result,
    path: Union[str, Path],
    node: str,
    input_magnitude: float = 1.0,
) -> Optional[Path]:
    """Save a Bode plot (magnitude dB + phase deg vs log frequency) for ``node``.

    If the result exposes a -3 dB cutoff, mark and annotate it on the magnitude
    axis. Requires an AC-analysis result.
    """
    path = _prepare(path)
    if path is None:
        return None

    freq, mag_db, phase_deg = result.bode(node, input_magnitude)

    fig = _new_figure(figsize=(8, 6))
    ax_mag = fig.add_subplot(2, 1, 1)
    ax_phase = fig.add_subplot(2, 1, 2, sharex=ax_mag)

    ax_mag.semilogx(freq, mag_db, color="C0")
    ax_mag.set_ylabel("Magnitude (dB)")
    ax_mag.set_title(f"Bode -- V({node})")
    ax_mag.grid(True, which="both", ls=":", alpha=0.6)

    try:
        fc = result.cutoff_frequency(node, input_magnitude=input_magnitude)
    except Exception:  # cutoff is best-effort annotation, never fatal
        fc = None
    if fc is not None:
        ax_mag.axvline(fc, color="C3", ls="--", lw=1)
        ax_mag.annotate(
            f"fc ~= {fc:,.0f} Hz",
            xy=(fc, ax_mag.get_ylim()[0]),
            xytext=(5, 5),
            textcoords="offset points",
            color="C3",
            fontsize=9,
        )

    ax_phase.semilogx(freq, phase_deg, color="C1")
    ax_phase.set_ylabel("Phase (deg)")
    ax_phase.set_xlabel("Frequency (Hz)")
    ax_phase.grid(True, which="both", ls=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(path)
    logger.info("Saved Bode plot to %s", path)
    return path


def save_transient_plot(
    result,
    path: Union[str, Path],
    nodes: Union[str, List[str]],
) -> Optional[Path]:
    """Save a transient waveform plot (voltage vs time) for one or more nodes.

    Uses the transient time axis when available; otherwise plots against sample
    index and labels the axis honestly.
    """
    path = _prepare(path)
    if path is None:
        return None

    if isinstance(nodes, str):
        nodes = [nodes]

    try:
        t = result.time_array()
        xlabel = "Time (s)"
    except Exception:
        t = None
        xlabel = "Sample index"

    fig = _new_figure()
    ax = fig.add_subplot(1, 1, 1)
    for node in nodes:
        v = result.get_voltage(node)
        if not isinstance(v, list):
            # A scalar (e.g. an OP result mistakenly passed here): draw a line.
            ax.axhline(v, label=f"V({node}) = {v:.3f} V")
            continue
        x = t if (t is not None and len(t) == len(v)) else range(len(v))
        if t is not None and len(t) != len(v):
            xlabel = "Sample index"  # length mismatch -> honest fallback
        ax.plot(x, v, label=f"V({node})")

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Transient response")
    ax.grid(True, ls=":", alpha=0.6)
    ax.legend()

    fig.tight_layout()
    fig.savefig(path)
    logger.info("Saved transient plot to %s", path)
    return path


def save_dc_transfer_plot(
    result,
    path: Union[str, Path],
    node: str,
    sweep_label: str = "Vsweep",
) -> Optional[Path]:
    """Save a DC-transfer plot: output ``node`` voltage vs the swept source.

    Uses the DC sweep axis when available; otherwise plots against sample index.
    Requires a ``dc_analysis`` result.
    """
    path = _prepare(path)
    if path is None:
        return None

    v = result.get_voltage(node)
    if not isinstance(v, list):
        v = [v]

    try:
        x = result.sweep_array()
        xlabel = sweep_label
        if len(x) != len(v):
            x = list(range(len(v)))
            xlabel = "Sample index"
    except Exception:
        x = list(range(len(v)))
        xlabel = "Sample index"

    fig = _new_figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(x, v, color="C0")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f"V({node})")
    ax.set_title(f"DC transfer -- V({node}) vs {sweep_label}")
    ax.grid(True, ls=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(path)
    logger.info("Saved DC-transfer plot to %s", path)
    return path
