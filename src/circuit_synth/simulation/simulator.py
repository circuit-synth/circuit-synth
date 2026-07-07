"""
Main CircuitSimulator class for circuit-synth SPICE integration.

This module provides the primary interface for running SPICE simulations
on circuit-synth designs.
"""

import logging
import os
import platform
import re
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

try:
    import PySpice
    from PySpice.Spice.Netlist import Circuit as SpiceCircuit
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    from PySpice.Unit import *

    PYSPICE_AVAILABLE = True

    # Auto-configure ngspice library path for macOS
    if platform.system() == "Darwin":  # macOS
        possible_paths = [
            "/opt/homebrew/lib/libngspice.dylib",  # Apple Silicon
            "/usr/local/lib/libngspice.dylib",  # Intel Mac
        ]
        for path in possible_paths:
            if os.path.exists(path):
                NgSpiceShared.LIBRARY_PATH = path
                logger.debug(f"Set ngspice library path: {path}")
                break

    # Auto-configure ngspice library path on Windows using KiCad's bundled DLL.
    # KiCad ships ngspice.dll (and its codemodels) under
    # <ProgramFiles>\KiCad\<version>\bin\ngspice.dll, so no separate ngspice
    # install is needed. Verified against KiCad 10.0 (ngspice 46).
    elif platform.system() == "Windows":
        import re as _re
        from pathlib import Path as _Path

        _roots = [
            _Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "KiCad",
            _Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
            / "KiCad",
        ]
        _versioned = []
        for _root in _roots:
            if _root.is_dir():
                for _child in _root.iterdir():
                    if _child.is_dir() and _re.fullmatch(r"\d+(?:\.\d+)*", _child.name):
                        _versioned.append(
                            (tuple(int(p) for p in _child.name.split(".")), _child)
                        )
        for _, _ver_dir in sorted(_versioned, reverse=True):
            _dll = _ver_dir / "bin" / "ngspice.dll"
            if _dll.exists():
                # Let ngspice.dll's own dependencies resolve from KiCad's bin dir.
                os.add_dll_directory(str(_dll.parent))
                NgSpiceShared.LIBRARY_PATH = str(_dll)
                # Point ngspice at its codemodels (analog.cm, etc.) if present so
                # AC/transient/behavioral sources work later; harmless if absent.
                _cm_dir = _ver_dir / "lib" / "ngspice"
                if _cm_dir.is_dir():
                    os.environ.setdefault("SPICE_LIB_DIR", str(_cm_dir))
                logger.debug(f"Set ngspice library path: {_dll}")
                break

    # Quiet the benign "Unsupported Ngspice version 46" banner (finding F2). PySpice
    # 1.5 whitelists ngspice only up to v34 in SimulationType.SIMULATION_TYPE, so
    # KiCad's bundled v46 raises a KeyError on every NgSpiceShared init and logs a
    # warning before harmlessly falling back to the last-known mapping (the node/type
    # conventions are unchanged, verified against KiCad 10). Register the newer
    # versions as aliases of that mapping so the KeyError -- and the warning -- never
    # fire. Runtime-only: mutates the in-memory dict, never patches PySpice on disk.
    try:
        from PySpice.Spice.NgSpice import SimulationType as _sim_type

        _sim_map = _sim_type.SIMULATION_TYPE
        _last_map = _sim_map.get("last")
        if _last_map is not None:
            for _v in range(_sim_type.LAST_VERSION + 1, 101):
                _sim_map.setdefault(_v, _last_map)
    except Exception as _e:  # a cosmetic tweak must never break simulation
        logger.debug(f"Could not pre-register newer ngspice versions: {_e}")

    # Drop only the benign init-time "can't find the initialization file spinit"
    # banner (finding F2). KiCad's ngspice ships no spinit and loads its codemodels
    # itself, so the message is harmless -- but it's printed to stderr on every init.
    # A narrow logging filter on PySpice's ngspice logger removes exactly that one
    # line while leaving every real (sim-time) ngspice warning/error intact.
    class _SpinitBannerFilter(logging.Filter):
        def filter(self, record):
            return "initialization file spinit" not in record.getMessage()

    logging.getLogger("PySpice.Spice.NgSpice.Shared.NgSpiceShared").addFilter(
        _SpinitBannerFilter()
    )

except ImportError as e:
    PYSPICE_AVAILABLE = False
    logger.warning(f"PySpice not available: {e}")


class SimulationResult:
    """Container for SPICE simulation results with analysis capabilities."""

    def __init__(self, analysis_result, analysis_type: str):
        self.analysis = analysis_result
        self.analysis_type = analysis_type
        self._voltages = {}
        self._currents = {}

        # Extract voltages and currents from analysis
        if hasattr(analysis_result, "nodes"):
            for node in analysis_result.nodes:
                if hasattr(analysis_result, node):
                    self._voltages[node] = analysis_result[node]

    def get_voltage(self, node: str) -> Union[float, List[float]]:
        """Get voltage at a specific node."""
        if node in self._voltages:
            voltage = self._voltages[node]
            # Handle scalar or array results
            if hasattr(voltage, "__len__") and len(voltage) == 1:
                return float(voltage[0])
            elif hasattr(voltage, "__len__"):
                return [float(v) for v in voltage]
            else:
                return float(voltage)
        else:
            # Try direct access
            try:
                voltage = self.analysis[node]
                if hasattr(voltage, "__len__") and len(voltage) == 1:
                    return float(voltage[0])
                elif hasattr(voltage, "__len__"):
                    return [float(v) for v in voltage]
                else:
                    return float(voltage)
            except:
                raise KeyError(f"Node '{node}' not found in simulation results")

    def get_current(self, component: str) -> Union[float, List[float]]:
        """Get current through a specific component."""
        # PySpice current notation: I(Vcomponent) for voltage sources
        current_name = f"I({component})"
        try:
            current = self.analysis[current_name]
            if hasattr(current, "__len__") and len(current) == 1:
                return float(current[0])
            elif hasattr(current, "__len__"):
                return [float(i) for i in current]
            else:
                return float(current)
        except:
            raise KeyError(f"Current for component '{component}' not found")

    def _frequency_array(self):
        """The AC sweep frequency axis as a real float ndarray.

        Raises if this result is not from an AC analysis (no frequency axis).
        """
        import numpy as np

        freq = getattr(self.analysis, "frequency", None)
        if freq is None:
            raise ValueError(
                "no frequency axis available (bode/cutoff need an AC analysis result)"
            )
        return np.real(np.asarray(freq)).astype(float)

    def _complex_node(self, node: str):
        """The complex node response (H(f)) as a complex ndarray."""
        import numpy as np

        try:
            data = self.analysis[node]
        except Exception:
            raise KeyError(f"Node '{node}' not found in AC analysis results")
        return np.asarray(data, dtype=complex)

    def time_array(self):
        """The transient time axis (seconds) as a real float ndarray.

        Raises if this result is not from a transient analysis.
        """
        import numpy as np

        t = getattr(self.analysis, "time", None)
        if t is None:
            raise ValueError(
                "no time axis available (transient plots need a transient result)"
            )
        return np.real(np.asarray(t)).astype(float)

    def sweep_array(self):
        """The DC-sweep axis (the swept source's values) as a real float ndarray.

        Raises if this result is not from a DC sweep analysis.
        """
        import numpy as np

        s = getattr(self.analysis, "sweep", None)
        if s is None:
            raise ValueError(
                "no sweep axis available (DC-transfer plots need a dc_analysis result)"
            )
        return np.real(np.asarray(s)).astype(float)

    def save_bode_plot(self, path, node: str, input_magnitude: float = 1.0):
        """Save a Bode plot (magnitude + phase) for ``node`` to ``path`` (PNG).

        Headless-safe; returns the written ``Path`` or ``None`` if matplotlib is
        unavailable. Delegates to :mod:`circuit_synth.simulation.plotting`.
        """
        from .plotting import save_bode_plot

        return save_bode_plot(self, path, node, input_magnitude=input_magnitude)

    def save_transient_plot(self, path, nodes):
        """Save a transient waveform plot of ``nodes`` to ``path`` (PNG).

        Headless-safe; returns the written ``Path`` or ``None`` if matplotlib is
        unavailable.
        """
        from .plotting import save_transient_plot

        return save_transient_plot(self, path, nodes)

    def save_dc_transfer_plot(self, path, node: str, sweep_label: str = "Vsweep"):
        """Save a DC-transfer plot (``node`` vs the swept source) to ``path`` (PNG).

        Headless-safe; returns the written ``Path`` or ``None`` if matplotlib is
        unavailable.
        """
        from .plotting import save_dc_transfer_plot

        return save_dc_transfer_plot(self, path, node, sweep_label=sweep_label)

    def bode(self, node: str, input_magnitude: float = 1.0):
        """Bode data for a node: ``(frequencies, magnitude_db, phase_deg)``.

        ``magnitude_db = 20*log10(|H|)`` where ``H = V(node) / input_magnitude``.
        With the default AC source magnitude of 1 V the node voltage *is* the
        transfer function, so ``input_magnitude`` can be left at 1.
        """
        import numpy as np

        freq = self._frequency_array()
        H = self._complex_node(node) / input_magnitude
        magnitude_db = 20 * np.log10(np.abs(H))
        phase_deg = np.angle(H, deg=True)
        return freq, magnitude_db, phase_deg

    def passband_gain_db(self, node: str, input_magnitude: float = 1.0) -> float:
        """Peak magnitude (dB) of the response -- the passband gain."""
        import numpy as np

        _, magnitude_db, _ = self.bode(node, input_magnitude)
        return float(np.max(magnitude_db))

    def cutoff_frequency(
        self, node: str, ref_db: float = -3.0, input_magnitude: float = 1.0
    ) -> Optional[float]:
        """Frequency where the response is ``ref_db`` below its passband peak.

        For a low-pass response this is the -3 dB corner. Returns the first
        frequency (scanning low->high) where the magnitude crosses
        ``passband_db + ref_db``, linearly interpolated in log-frequency between
        the two straddling samples. Returns ``None`` if the curve never crosses.
        """
        import numpy as np

        freq, magnitude_db, _ = self.bode(node, input_magnitude)
        target = float(np.max(magnitude_db)) + ref_db
        for i in range(1, len(freq)):
            a, b = magnitude_db[i - 1], magnitude_db[i]
            if a == b:
                continue
            # Straddle: target lies between consecutive samples.
            if (a - target) * (b - target) <= 0:
                fa, fb = np.log10(freq[i - 1]), np.log10(freq[i])
                t = (target - a) / (b - a)
                return float(10 ** (fa + t * (fb - fa)))
        return None

    # -- loop-stability helpers (Stage 20.5) ------------------------------ #

    def loop_gain(self, fb_a: str, fb_b: str):
        """Loop gain ``T(f)`` from a voltage-injection AC run: ``(freq, mag_db, phase_deg)``.

        The loop is broken by a ``Simulation_SPICE:VSIN`` (ac=1) inserted in series
        between the divider tap ``fb_a`` (the loop *output* / plant-side node) and the
        controller FB pin ``fb_b`` (the error-amp *input*), source polarity A->B. The
        return ratio is then ``T = -V(fb_a)/V(fb_b)`` (the divider-tap response over
        the pin excitation), which is high at DC and rolls off -- as a loop gain
        should. Phase is unwrapped (deg).

        Requires an averaged (``MODE=avg``) model -- the cycle-accurate model has no
        meaningful small-signal linearization. Validity: injection is accurate where
        the forward impedance greatly exceeds the backward impedance (true at a
        high-impedance FB pin); this is single-injection, not the general
        Middlebrook double-injection case.
        """
        import numpy as np

        freq = self._frequency_array()
        T = -self._complex_node(fb_a) / self._complex_node(fb_b)
        mag_db = 20 * np.log10(np.abs(T))
        phase_deg = np.unwrap(np.angle(T)) * 180.0 / np.pi
        return freq, mag_db, phase_deg

    def phase_margin(self, fb_a: str, fb_b: str) -> Optional[float]:
        """Phase margin (degrees) at the first 0 dB gain crossover, or ``None``.

        ``None`` when the loop gain never crosses 0 dB (report honestly rather than
        fabricate a margin). See :meth:`loop_gain` for the injection setup and the
        ``fb_a``/``fb_b`` (divider-tap / FB-pin) convention.
        """
        freq = self._frequency_array()
        T = -self._complex_node(fb_a) / self._complex_node(fb_b)
        return self._phase_margin_from(freq, T)

    def gain_margin(self, fb_a: str, fb_b: str) -> Optional[float]:
        """Gain margin (dB) at the first -180 deg phase crossing, or ``None``.

        Positive = the loop gain is that many dB below 0 dB where the phase hits
        -180 deg (stable). ``None`` when the phase never reaches -180 deg.
        """
        freq = self._frequency_array()
        T = -self._complex_node(fb_a) / self._complex_node(fb_b)
        return self._gain_margin_from(freq, T)

    @staticmethod
    def _phase_margin_from(freq, T) -> Optional[float]:
        """Phase margin from a complex loop-gain array ``T`` over ``freq`` (ascending).

        Finds the first downward 0 dB crossing, interpolates the (unwrapped) phase
        there, and returns ``180 + phase``. ``None`` if no downward crossing.
        """
        import numpy as np

        freq = np.asarray(freq, dtype=float)
        T = np.asarray(T, dtype=complex)
        mag_db = 20 * np.log10(np.abs(T))
        phase = np.unwrap(np.angle(T)) * 180.0 / np.pi
        for i in range(1, len(freq)):
            a, b = mag_db[i - 1], mag_db[i]
            if a >= 0.0 > b:  # crosses 0 dB going down
                t = (0.0 - a) / (b - a)
                ph = phase[i - 1] + t * (phase[i] - phase[i - 1])
                return float(180.0 + ph)
        return None

    @staticmethod
    def _gain_margin_from(freq, T) -> Optional[float]:
        """Gain margin (dB) from a complex loop-gain array; ``None`` if phase never
        crosses -180 deg. Interpolates the magnitude at the first -180 crossing and
        returns its negation (dB below 0)."""
        import numpy as np

        freq = np.asarray(freq, dtype=float)
        T = np.asarray(T, dtype=complex)
        mag_db = 20 * np.log10(np.abs(T))
        phase = np.unwrap(np.angle(T)) * 180.0 / np.pi
        for i in range(1, len(freq)):
            a, b = phase[i - 1], phase[i]
            if a > -180.0 >= b:  # crosses -180 deg going down
                t = (-180.0 - a) / (b - a)
                m = mag_db[i - 1] + t * (mag_db[i] - mag_db[i - 1])
                return float(-m)
        return None

    # -- transient measurement helpers (Stage 20.3) ----------------------- #

    def _node_series(self, node: str):
        """(time, value) real ndarrays for a transient node."""
        import numpy as np

        t = self.time_array()
        v = np.real(np.asarray(self.analysis[node])).astype(float)
        return t, v

    @staticmethod
    def _tail_mask(t, tail_frac: float):
        """Boolean mask selecting the last ``tail_frac`` of the time axis."""
        span = float(t[-1] - t[0])
        return t >= (t[-1] - tail_frac * span)

    def average(self, node: str, tail_frac: float = 0.2) -> float:
        """Mean of ``node`` over the last ``tail_frac`` of the run (steady state)."""
        import numpy as np

        t, v = self._node_series(node)
        return float(np.mean(v[self._tail_mask(t, tail_frac)]))

    def ripple_pp(self, node: str, tail_frac: float = 0.2) -> float:
        """Peak-to-peak ripple of ``node`` over the last ``tail_frac`` of the run.

        Note: use a fine transient step (e.g. <= 1/50 of the switching period) --
        a coarse step aliases the PWM edges and inflates the apparent ripple.
        """
        import numpy as np

        t, v = self._node_series(node)
        return float(np.ptp(v[self._tail_mask(t, tail_frac)]))

    def settling_time(
        self, node: str, final: Optional[float] = None, tol: float = 0.02
    ) -> Optional[float]:
        """First time after which ``node`` stays within +/-``tol``*final of ``final``.

        ``final`` defaults to the mean over the last 10% of the run. Returns None if
        the waveform never settles (still outside the band at the last sample).
        """
        import numpy as np

        t, v = self._node_series(node)
        if final is None:
            final = float(np.mean(v[self._tail_mask(t, 0.1)]))
        band = abs(tol * final) if final != 0 else abs(tol)
        outside = np.where(np.abs(v - final) > band)[0]
        if len(outside) == 0:
            return float(t[0])
        last = int(outside[-1])
        if last >= len(t) - 1:
            return None
        return float(t[last + 1])

    def branch_current(self, name: str):
        """Branch current through an element (e.g. an inductor ``'L1'``) as an ndarray.

        Pass the schematic ref (case-insensitive). ngspice exposes inductor and
        voltage-source branch currents; PySpice prepends the element letter to the
        ref, so ``L1`` becomes branch ``ll1`` and ``V1`` becomes ``vv1`` -- this
        resolves both forms. Raises KeyError if no matching branch exists.
        """
        import numpy as np

        branches = getattr(self.analysis, "branches", None) or {}
        low = name.lower()
        # Try the raw name, then the element-letter-prefixed form PySpice emits,
        # then any branch whose key ends with the ref (defensive).
        candidates = [low, "l" + low, "v" + low]
        key = next((c for c in candidates if c in branches), None)
        if key is None:
            key = next((k for k in branches if k.endswith(low)), None)
        if key is None:
            raise KeyError(
                f"no branch current for '{name}' (available: {sorted(branches)})"
            )
        return np.real(np.asarray(branches[key])).astype(float)

    def average_power(
        self, node: str, current_source: str, tail_frac: float = 0.2
    ) -> float:
        """Mean of ``V(node) * I(current_source)`` over the tail window.

        For efficiency: input power ~= ``average_power(vin_node, "Vsource")`` (sign
        per the source's current convention) and output power ~=
        ``average(vout)**2 / Rload``.
        """
        import numpy as np

        t = self.time_array()
        v = np.real(np.asarray(self.analysis[node])).astype(float)
        i = np.asarray(self.get_current(current_source), dtype=float)
        m = self._tail_mask(t, tail_frac)
        return float(np.mean(v[m] * i[m]))

    def list_nodes(self) -> List[str]:
        """List all available voltage nodes."""
        nodes = []
        if hasattr(self.analysis, "nodes"):
            nodes.extend(self.analysis.nodes)
        # Also check for direct access
        for attr in dir(self.analysis):
            if not attr.startswith("_") and attr not in ["nodes", "branches"]:
                try:
                    val = getattr(self.analysis, attr)
                    if hasattr(val, "__len__") or isinstance(val, (int, float)):
                        nodes.append(attr)
                except:
                    pass
        return list(set(nodes))

    def plot(self, *nodes, title: Optional[str] = None):
        """Plot voltage results (requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error("matplotlib required for plotting")
            return

        plt.figure(figsize=(10, 6))

        for node in nodes:
            try:
                voltage = self.get_voltage(node)
                if isinstance(voltage, list):
                    plt.plot(voltage, label=f"V({node})")
                else:
                    plt.axhline(y=voltage, label=f"V({node}) = {voltage:.3f}V")
            except KeyError as e:
                logger.warning(f"Could not plot {node}: {e}")

        plt.xlabel("Time/Frequency/Sweep")
        plt.ylabel("Voltage (V)")
        plt.title(title or f"{self.analysis_type.upper()} Analysis Results")
        plt.legend()
        plt.grid(True)
        plt.show()


class CircuitSimulator:
    """Main interface for SPICE simulation of circuit-synth designs."""

    # Accepted ngspice ``ngbehavior`` dialect selectors (compat modes). "psa" is
    # PSpice + whole-netlist, the mode most TI-style vendor .lib files need.
    _VALID_COMPAT = re.compile(r"^(ps|lt|ki|a|all|psa|lta|ltps|ltpsa)$")

    # Process-global: whether the singleton NgSpiceShared currently has a compat
    # ngbehavior set. NgSpiceShared.new_instance() returns one instance per
    # process, so a compat mode set for one simulation persists into later ones --
    # this flag lets the next default-mode run unset it (see _make_simulator).
    _ngbehavior_set = False

    def __init__(self, circuit_synth_circuit, compat=None):
        """Build a simulator for a circuit.

        ``compat`` selects an ngspice dialect (``ngbehavior``) so vendor
        PSpice/LTspice-flavored ``.lib`` files parse -- e.g. ``compat="psa"`` for a
        TI-style unencrypted PSpice model. Accepted: ps, lt, ki, a, all, psa, lta,
        ltps, ltpsa. When ``compat`` is None, a schematic ``Sim.Compat`` property
        (if any) is used instead; an explicit ``compat`` argument wins over it.
        """
        if not PYSPICE_AVAILABLE:
            raise ImportError(
                "PySpice not available. Install with: pip install PySpice\n"
                "Also ensure ngspice is installed on your system."
            )
        if compat is not None and not self._VALID_COMPAT.match(str(compat)):
            raise ValueError(
                f"invalid compat mode {compat!r}; expected one of "
                f"ps, lt, ki, a, all, psa, lta, ltps, ltpsa (e.g. 'psa' for a "
                f"TI-style PSpice vendor library)"
            )

        self.circuit_synth_circuit = circuit_synth_circuit
        self.spice_circuit = None
        # {ref: ResolvedModel} recording which model tier each active device got
        # (datasheet_fit / generic / vendor_lib). Populated during conversion.
        self.model_provenance = {}
        # The ngspice dialect a schematic requested via Sim.Compat, if any.
        self._compat_hint = None
        self._convert_to_spice()
        # Explicit arg wins; otherwise adopt the schematic's Sim.Compat hint. An
        # invalid hint (a typo in the schematic) is warned about and ignored rather
        # than crashing the whole design.
        self._compat = compat
        if self._compat is None and self._compat_hint:
            if self._VALID_COMPAT.match(str(self._compat_hint)):
                self._compat = str(self._compat_hint)
            else:
                logger.warning(
                    f"ignoring invalid Sim.Compat {self._compat_hint!r} "
                    f"(expected ps/lt/ki/a/all/psa/lta/ltps/ltpsa)"
                )

    def _convert_to_spice(self):
        """Convert circuit-synth circuit to PySpice format."""
        from .converter import SpiceConverter

        converter = SpiceConverter(self.circuit_synth_circuit)
        self.spice_circuit = converter.convert()
        self.model_provenance = converter.model_provenance
        self._compat_hint = getattr(converter, "compat_hint", None)

    def _make_simulator(self, temperature: float, options: Optional[Dict] = None):
        """Build a PySpice simulator with temperature and optional ngspice options.

        ``options`` maps ngspice ``.options`` names to values (e.g.
        ``{"reltol": 1e-3, "abstol": 1e-9, "gmin": 1e-12}``) for convergence /
        accuracy tuning; omit for ngspice defaults.
        """
        if not self.spice_circuit:
            raise RuntimeError("SPICE circuit not initialized")

        compat = getattr(self, "_compat", None)
        # Only touch the shared ngspice instance when a compat mode is active or a
        # previous compat run left ngbehavior set (which must be cleared for a
        # default-mode run, since the instance is a per-process singleton).
        # Otherwise use the legacy call unchanged, so default sims are unaffected.
        if compat or CircuitSimulator._ngbehavior_set:
            shared = NgSpiceShared.new_instance()
            if compat:
                shared.exec_command(f"set ngbehavior={compat}")
                CircuitSimulator._ngbehavior_set = True
                logger.debug(f"ngspice compat mode: set ngbehavior={compat}")
            else:
                shared.exec_command("unset ngbehavior")
                CircuitSimulator._ngbehavior_set = False
                logger.debug("ngspice compat mode: unset ngbehavior (default dialect)")
            simulator = self.spice_circuit.simulator(
                temperature=temperature,
                nominal_temperature=temperature,
                simulator="ngspice-shared",
                ngspice_shared=shared,
            )
        else:
            simulator = self.spice_circuit.simulator(
                temperature=temperature, nominal_temperature=temperature
            )
        if options:
            simulator.options(**options)
        return simulator

    def operating_point(
        self, temperature: float = 25, options: Optional[Dict] = None
    ) -> SimulationResult:
        """Run DC operating point analysis."""
        simulator = self._make_simulator(temperature, options)
        analysis = simulator.operating_point()

        return SimulationResult(analysis, "dc_op")

    def dc_analysis(
        self,
        source: str,
        start: float,
        stop: float,
        step: float,
        temperature: float = 25,
        options: Optional[Dict] = None,
    ) -> SimulationResult:
        """Run DC sweep analysis."""
        simulator = self._make_simulator(temperature, options)
        analysis = simulator.dc(**{source: slice(start, stop, step)})

        return SimulationResult(analysis, "dc_sweep")

    def ac_analysis(
        self,
        start_freq: float,
        stop_freq: float,
        points: int = 100,
        temperature: float = 25,
        options: Optional[Dict] = None,
    ) -> SimulationResult:
        """Run AC analysis."""
        # The cycle-accurate buck/boost model has no meaningful small-signal
        # linearization (a PWM comparator), so warn on .ac. The *averaged* model
        # (MODE=avg, provenance name "*_averaged") is built precisely for .ac loop
        # gain -- exclude it.
        switching = sorted(
            ref
            for ref, prov in self.model_provenance.items()
            if getattr(prov, "kind", None) in ("buck", "boost", "flyback")
            and "averaged" not in (getattr(prov, "name", "") or "")
        )
        if switching:
            logger.warning(
                f"AC analysis on switching macromodel(s) {', '.join(switching)} is "
                f"not meaningful: a PWM comparator has no small-signal linearization. "
                f"Use transient_analysis; loop-gain/phase-margin needs the averaged "
                f"model (Sim.Params MODE=avg)."
            )
        simulator = self._make_simulator(temperature, options)
        analysis = simulator.ac(
            start_frequency=start_freq @ u_Hz,
            stop_frequency=stop_freq @ u_Hz,
            number_of_points=points,
            variation="dec",
        )

        return SimulationResult(analysis, "ac")

    def transient_analysis(
        self,
        step_time: float,
        end_time: float,
        temperature: float = 25,
        options: Optional[Dict] = None,
        *,
        start_time: float = 0,
        max_time: Optional[float] = None,
        use_initial_condition: bool = False,
        initial_conditions: Optional[Dict[str, float]] = None,
    ) -> SimulationResult:
        """Run transient analysis.

        Times are in seconds. The keyword-only controls below are the standard
        ngspice ``.tran``/``.ic`` knobs that power-supply (soft-start, stiff
        vendor-model) simulations need; with none supplied the call is identical
        to the legacy two-argument form.

        Args:
            step_time: Suggested timestep (``tstep``).
            end_time: Stop time (``tstop``).
            temperature: Simulation temperature in Celsius.
            options: ngspice ``.options`` overrides (see ``_make_simulator``).
            start_time: Discard results before this time (``tstart``) -- smaller
                result arrays; the run still integrates from t=0.
            max_time: Cap the internal timestep (``tmax``) for accuracy on stiff
                circuits; ``None`` lets ngspice choose.
            use_initial_condition: Emit ``uic`` -- skip the DC operating point and
                start from device/``.ic`` initial conditions. Required when the op
                point does not converge (common with vendor switcher models).
            initial_conditions: ``{net_name: volts}`` emitted as ``.ic
                v(net)=volts``. Pass the circuit-synth **net name** (e.g. ``"VOUT"``,
                ``"OUT"``); it is used verbatim as the node name and ngspice matches
                it case-insensitively. For a soft-start from a discharged output use
                ``use_initial_condition=True, initial_conditions={"VOUT": 0}``.

        Note:
            ``.nodeset`` is not exposed (no PySpice API surface); use
            ``initial_conditions`` instead.
        """
        simulator = self._make_simulator(temperature, options)
        if initial_conditions:
            # PySpice's initial_condition(**kwargs) maps node_name -> value; the
            # net name is passed straight through as the ngspice node name.
            simulator.initial_condition(**dict(initial_conditions))
        # Build kwargs minimally so a controls-free call is byte-identical to the
        # legacy transient() (protects the default-path baseline).
        kwargs = dict(step_time=step_time @ u_s, end_time=end_time @ u_s)
        if start_time:
            kwargs["start_time"] = start_time @ u_s
        if max_time is not None:
            kwargs["max_time"] = max_time @ u_s
        if use_initial_condition:
            kwargs["use_initial_condition"] = True
        analysis = simulator.transient(**kwargs)

        return SimulationResult(analysis, "transient")

    def list_components(self) -> List[str]:
        """List all components in the SPICE circuit."""
        if not self.spice_circuit:
            return []

        components = []
        for element in self.spice_circuit.elements:
            components.append(str(element.name))
        return components

    def list_nodes(self) -> List[str]:
        """List all nodes in the SPICE circuit."""
        if not self.spice_circuit:
            return []

        nodes = []
        for node in self.spice_circuit.node_names:
            nodes.append(str(node))
        return nodes

    def get_netlist(self) -> str:
        """Get the SPICE netlist as string."""
        if not self.spice_circuit:
            return ""

        return str(self.spice_circuit)
