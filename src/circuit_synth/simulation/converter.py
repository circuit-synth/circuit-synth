"""
SpiceConverter: Converts circuit-synth designs to PySpice format.

This module handles the translation from circuit-synth components and nets
to SPICE netlists that can be simulated with PySpice/ngspice.
"""

import logging
import math
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResolvedModel:
    """Which model tier a device's SPICE ``.model`` was resolved from.

    Recorded per device so callers can see -- and log -- that a part simulated
    with datasheet-fit params, a textbook generic, or an external vendor model,
    rather than a generic being silently passed off as the real part.
    """

    ref: str
    kind: str  # diode | bjt | mosfet
    tier: str  # datasheet_fit | generic | vendor_lib | unresolved
    name: str  # the resolved model/base name
    overridden: bool = False  # True if Sim.Params overlaid a derived card
    source: str = ""  # provenance of a vendor_lib model: sim_library | local_store


try:
    from PySpice.Spice.Netlist import Circuit as SpiceCircuit
    from PySpice.Unit import *

    PYSPICE_AVAILABLE = True
except ImportError:
    PYSPICE_AVAILABLE = False


class SimulationValidationError(ValueError):
    """Raised when a circuit cannot be safely simulated.

    Carries the full list of problems (``.problems``) so the caller sees every
    issue at once, rather than discovering them one ngspice crash at a time. This
    replaces the old behaviour where unknown components were silently skipped,
    yielding a wrong-but-"successful" simulation.
    """

    def __init__(self, problems):
        self.problems = list(problems)
        body = "\n".join(f"  - {p}" for p in self.problems)
        super().__init__(f"circuit is not valid for simulation:\n{body}")


class SpiceConverter:
    """Converts circuit-synth circuits to PySpice format."""

    # Built-in generic SPICE model cards, keyed by model name. Each entry is
    # (ngspice device type, params dict). These back the ``Default*`` names the
    # device handlers assign, so any diode/BJT/MOSFET is simulatable out of the box
    # without a vendor model; a device's ``value=`` may also name one of these
    # built-ins directly. Only models a circuit actually uses are emitted (see
    # ``_emit_models``). Params are deliberately generic (textbook silicon values).
    GENERIC_MODELS = {
        "DefaultDiode": ("D", {"IS": 1e-14, "RS": 0.1, "N": 1.0, "CJO": 2e-12}),
        "DefaultSchottky": (
            "D",
            {"IS": 1e-6, "RS": 0.05, "N": 1.05, "CJO": 100e-12, "BV": 40, "IBV": 1e-3},
        ),
        "DefaultNPN": ("NPN", {"BF": 100, "IS": 1e-14, "VAF": 100}),
        "DefaultPNP": ("PNP", {"BF": 100, "IS": 1e-14, "VAF": 100}),
        "DefaultNMOS": ("NMOS", {"VTO": 1.0, "KP": 2e-5, "LAMBDA": 0.02}),
        "DefaultPMOS": ("PMOS", {"VTO": -1.0, "KP": 2e-5, "LAMBDA": 0.02}),
    }

    # Per-kind generic fallback: an unresolved model NAME carrying Sim.Params
    # degrades to this generic + the overrides (rather than a hard error), so an
    # unknown part can be param-fitted into a usable model (bug #11).
    _KIND_GENERIC = {
        "diode": "DefaultDiode",
        "bjt": "DefaultNPN",
        "mosfet": "DefaultNMOS",
    }

    # A bare device-type keyword in ``value`` selects the matching generic model,
    # so ``value="pnp"`` is treated as a type hint rather than a literal model name.
    _TYPE_KEYWORD_MODELS = {
        "npn": "DefaultNPN",
        "pnp": "DefaultPNP",
        "nmos": "DefaultNMOS",
        "pmos": "DefaultPMOS",
        "diode": "DefaultDiode",
    }

    def __init__(self, circuit_synth_circuit):
        self.circuit = circuit_synth_circuit
        self.spice_circuit = None
        self.voltage_sources = []
        self.node_map = {}
        # Nets driven by an explicit source component (Device:V, Simulation_SPICE:V*,
        # ...). _add_power_sources skips these so the net-name heuristic never adds a
        # second, conflicting supply on a net an explicit source already drives.
        self.driven_nets = set()
        # Model names referenced by diode/BJT/MOSFET devices; a matching .model card
        # is emitted for each that resolves to a built-in generic (see _emit_models).
        self.used_models = set()
        # Per-device model cards synthesized from Sim.Params overrides, keyed by a
        # derived name ({base}_{ref}) so two parts overriding the same base model
        # do not collide. Each value is (device_type, params). Emitted alongside
        # the built-in generics in _emit_models.
        self.derived_models = {}
        # Datasheet-fit model cards pulled from the built-in ModelLibrary and
        # actually referenced by a device, keyed by model name -> (device_type,
        # params). Emitted in _emit_models (GENERIC_MODELS covers only generics).
        self.library_models = {}
        # ref -> ResolvedModel: which tier each active device's model came from.
        self.model_provenance = {}
        # Absolute paths of external .lib/.sub files already `.include`d (dedup).
        self.included_libs = set()
        # First non-empty Sim.Compat across components (e.g. "psa" for a vendor
        # PSpice lib) -> the ngspice dialect the simulator should select. Resolved
        # in convert(); a disagreement between components is a validate() error.
        self.compat_hint = None
        # After _flatten on a hierarchical circuit: flat_ref -> (subcircuit_name,
        # original_ref) for any ref that had to be uniquified. Empty otherwise.
        # Keeps model provenance / error messages traceable back to the source.
        self.flattened_ref_map = {}

    class _FlatCircuit:
        """A read-only, flattened view of a hierarchical circuit.

        The converter only reads ``.components`` (dict ref->component),
        ``.nets`` (dict name->net) and ``.name`` off its circuit, so this thin
        view is all conversion/validation need after flattening.
        """

        def __init__(self, name, components, nets):
            self.name = name
            self.components = components
            self.nets = nets

    @staticmethod
    def _iter_values(container):
        """Values of a dict-or-iterable container (components/nets come as either)."""
        if hasattr(container, "values"):
            return list(container.values())
        if hasattr(container, "__iter__"):
            return list(container)
        return []

    def _flatten(self, circuit):
        """Merge a hierarchical circuit's components and nets into one view.

        Returns ``circuit`` unchanged when it has no subcircuits. Otherwise walks
        the subcircuit tree depth-first and returns a :class:`_FlatCircuit` with:

        - **components** merged into one dict. Refs are normally already unique
          across the hierarchy (the reference manager uniquifies at construction),
          but a genuine collision (two *distinct* components sharing a ref) is
          resolved by renaming the later one -- which propagates to its pins'
          string form (read live), so node extraction stays correct.
        - **nets** merged by name. A net shared across sheets is the *same object*
          (same name) so it merges cleanly; two *distinct* nets sharing a name
          would be conflated into one node, so that case is logged as a warning
          (a name-scoping limitation, not introduced by flattening).
        """
        if not getattr(circuit, "_subcircuits", None):
            return circuit  # already flat -- leave the existing path untouched

        components = {}
        nets = {}
        name_collisions = []
        self.flattened_ref_map = {}

        def visit(circ, path):
            for comp in self._iter_values(getattr(circ, "components", {})):
                ref = getattr(comp, "ref", None)
                if ref is None:
                    continue
                if ref in components and components[ref] is not comp:
                    new_ref = f"{ref}_{len(components)}"
                    while new_ref in components:
                        new_ref = f"{new_ref}_x"
                    self.flattened_ref_map[new_ref] = (circ.name, ref)
                    comp.ref = new_ref  # live -> updates str(pin) used for matching
                    ref = new_ref
                components[ref] = comp
            for net in self._iter_values(getattr(circ, "nets", {})):
                name = getattr(net, "name", str(net))
                existing = nets.get(name)
                if existing is None:
                    nets[name] = net
                elif existing is not net:
                    name_collisions.append(name)
            for sub in getattr(circ, "_subcircuits", []) or []:
                visit(sub, path + [getattr(sub, "name", "?")])

        visit(circuit, [getattr(circuit, "name", "Circuit")])

        if name_collisions:
            logger.warning(
                "Flattening hierarchy: distinct nets share name(s) %s and will "
                "be treated as one SPICE node -- rename them to disambiguate.",
                sorted(set(name_collisions)),
            )
        logger.info(
            "Flattened hierarchy for simulation: %d component(s), %d net(s)",
            len(components),
            len(nets),
        )
        return self._FlatCircuit(getattr(circuit, "name", "Circuit"), components, nets)

    def convert(self, strict: bool = True) -> "SpiceCircuit":
        """Convert circuit-synth circuit to PySpice circuit.

        Args:
            strict: When True (default), validate the circuit first and raise
                ``SimulationValidationError`` if anything would produce a
                wrong-but-"successful" simulation (unknown component, floating
                node, no source, under-connected op-amp). When False, fall back to
                the lenient path that warns and skips unknown components -- useful
                for exploratory conversion of partial circuits.
        """
        if not PYSPICE_AVAILABLE:
            raise ImportError("PySpice not available")

        # Hierarchical designs place their components/nets in subcircuits; the
        # converter iterates only self.circuit, so flatten first. No-op for a
        # flat circuit. (See _flatten for the identity/collision handling.)
        self.circuit = self._flatten(self.circuit)

        if strict:
            self.validate()

        # Resolve the requested ngspice dialect (Sim.Compat) for the simulator.
        self.compat_hint = self._resolve_compat_hint()

        # Create PySpice circuit
        circuit_name = getattr(self.circuit, "name", "Circuit")
        self.spice_circuit = SpiceCircuit(circuit_name)

        # Map circuit-synth nets to SPICE nodes
        self._map_nodes()

        # Add components to SPICE circuit
        self._add_components()

        # Emit .model cards for the semiconductor models the components referenced.
        self._emit_models()

        # Add power sources (voltage/current sources)
        self._add_power_sources()

        return self.spice_circuit

    def _map_nodes(self):
        """Create mapping from circuit-synth nets to SPICE node names."""
        self.node_map = {}

        # Handle both dict and list formats for nets
        if hasattr(self.circuit.nets, "values"):
            # Dict format: {name: net_object}
            nets_to_process = self.circuit.nets.values()
        elif hasattr(self.circuit.nets, "__iter__"):
            # List format: [net_object, ...]
            nets_to_process = self.circuit.nets
        else:
            logger.error("Unknown nets format")
            return

        # Map GND net to SPICE ground
        for net in nets_to_process:
            net_name = getattr(net, "name", str(net))
            if net_name.upper() in ["GND", "GROUND", "VSS"]:
                self.node_map[net_name] = self.spice_circuit.gnd
            else:
                self.node_map[net_name] = net_name

    def _add_components(self):
        """Add circuit-synth components to SPICE circuit."""
        # circuit.components is a dict {ref: component}; iterating it directly
        # yields refs (strings), so pull the component objects out explicitly.
        components = self.circuit.components
        if hasattr(components, "values"):
            components = components.values()
        for component in components:
            self._add_component(component)

    @staticmethod
    def _classify(symbol: str) -> Optional[str]:
        """Map a KiCad symbol to a SPICE primitive kind, or None if unrecognized.

        Single source of truth shared by ``_add_component`` (dispatch) and
        ``validate`` (so validation and conversion never disagree about what is
        simulatable). Source checks come before the op-amp heuristic so a source
        symbol is never misclassified. Explicit SPICE sources use KiCad's real
        Simulation_SPICE library (VDC/VSIN/IDC/...); "Device:V"/"Device:I" are
        exact aliases (not real KiCad symbols but sometimes referenced by docs) --
        matched exactly so they do not also swallow "Device:Varistor".
        """
        if not symbol:
            return None
        if "Device:R" in symbol:
            return "resistor"
        if "Device:C" in symbol:
            return "capacitor"
        if "Device:L" in symbol:
            return "inductor"
        if "Device:D" in symbol or "Diode:" in symbol:
            return "diode"
        if (
            symbol.startswith("Simulation_SPICE:V")
            or "Reference_Voltage:" in symbol
            or symbol == "Device:V"
        ):
            return "voltage_source"
        if (
            symbol.startswith("Simulation_SPICE:I")
            or "Reference_Current:" in symbol
            or symbol == "Device:I"
        ):
            return "current_source"
        # Linear regulators before the op-amp heuristic: many regulator names
        # contain "lm" (LM317/LM1117) and would otherwise be misread as op-amps.
        if "Regulator_Linear:" in symbol:
            return "ldo"
        # Switching regulators: topology (buck vs boost) can't be read from the
        # symbol reliably, so classify to a pseudo-kind validate() turns into an
        # actionable "set Sim.Device=BUCK/BOOST" error (explicit beats guessing).
        if "Regulator_Switching:" in symbol:
            return "switcher_unknown"
        # Transformers before the op-amp heuristic (defensive); matches every
        # Device:Transformer_* variant, though only 1P_1S pin names (AA/AB/SA/SB)
        # resolve -- multi-winding parts fail terminal resolution with a clear error.
        if "Device:Transformer" in symbol:
            return "transformer"
        if any(x in symbol.lower() for x in ["op", "amp", "lm", "tl"]):
            return "opamp"
        if "Transistor_BJT:" in symbol or "Device:Q" in symbol:
            return "bjt"
        if "Transistor_FET:" in symbol or "Device:M" in symbol:
            return "mosfet"
        return None

    # KiCad ``Sim.Device`` device tokens -> our SPICE primitive kinds. Lets a
    # simulation-only stand-in ride on any symbol (the schematic keeps its real
    # symbol/footprint; only the simulation model is redirected). SUBCKT is left
    # unmapped here (external-model attach is Stage 9.3).
    _SIM_DEVICE_KINDS = {
        "R": "resistor",
        "C": "capacitor",
        "L": "inductor",
        "D": "diode",
        "NPN": "bjt",
        "PNP": "bjt",
        "NMOS": "mosfet",
        "PMOS": "mosfet",
        "V": "voltage_source",
        "I": "current_source",
        "LDO": "ldo",
        "BUCK": "buck",
        "BOOST": "boost",
        "FLYBACK": "flyback",
        "TRANSFORMER": "transformer",
        "XFMR": "transformer",
    }

    @staticmethod
    def _sim_props(component) -> dict:
        """KiCad ``Sim.*`` fields as ``{lowercased suffix: value}`` (empty if none).

        Reads them off ``_extra_fields`` like the waveform params. Accepts both the
        native dotted spelling (``Sim.Enable``) and an underscore fallback
        (``Sim_Enable``) in case a flow sanitizes the dot away.
        """
        extra = getattr(component, "_extra_fields", None)
        if not isinstance(extra, dict):
            return {}
        out = {}
        for k, v in extra.items():
            low = str(k).lower()
            if low.startswith("sim.") or low.startswith("sim_"):
                out[low[4:]] = v
        return out

    def _sim_excluded(self, component) -> bool:
        """True if ``Sim.Enable`` marks the component out of simulation.

        KiCad uses ``Sim.Enable="0"`` to keep a part on the schematic but exclude
        it from simulation. Excluded parts are skipped by both conversion and
        validation (and their pins do not count toward net connectivity).
        """
        val = self._sim_props(component).get("enable", None)
        if val is None:
            return False
        return str(val).strip().lower() in ("0", "false", "no", "off")

    def _distinct_compat_values(self) -> list:
        """Distinct non-empty ``Sim.Compat`` values across components (sorted)."""
        values = set()
        for component in self._iter_components():
            if self._sim_excluded(component):
                continue
            val = self._sim_props(component).get("compat")
            if val is not None and str(val).strip():
                values.add(str(val).strip())
        return sorted(values)

    def _resolve_compat_hint(self) -> Optional[str]:
        """The single ``Sim.Compat`` dialect requested by the schematic, or None.

        A disagreement between components is caught in ``validate()``; here we just
        take the first value so conversion still proceeds in the lenient path.
        """
        values = self._distinct_compat_values()
        return values[0] if values else None

    def _kind(self, component) -> Optional[str]:
        """SPICE primitive kind for a component: ``Sim.Device`` wins over the symbol.

        Returns None for an unrecognized ``Sim.Device`` token or an unmapped symbol
        (validation reports it, naming the offending token/symbol).
        """
        device = self._sim_props(component).get("device", None)
        if device:
            return self._SIM_DEVICE_KINDS.get(str(device).strip().upper())
        return self._classify(self._attr(component, "symbol", ""))

    def _add_component(self, component):
        """Add a single component to the SPICE circuit."""
        symbol = getattr(component, "symbol", "")
        ref = getattr(component, "ref", "X")
        value = getattr(component, "value", None)

        if self._sim_excluded(component):
            logger.info(f"{ref}: excluded from simulation (Sim.Enable=0)")
            return

        # An external vendor model (Sim.Library) supersedes the built-in handlers:
        # attach the .lib/.subckt directly (Stage 9.3).
        if self._sim_props(component).get("library"):
            self._add_external_model(component, ref)
            return

        # A model in the local MPN store is attached like an implicit Sim.Library
        # (Stage 9.4), above the datasheet-fit/generic tiers.
        store_path = self._store_lib_for(component)
        if store_path:
            self._add_store_model(component, ref, store_path)
            return

        handlers = {
            "resistor": self._add_resistor,
            "capacitor": self._add_capacitor,
            "inductor": self._add_inductor,
            "diode": self._add_diode,
            "voltage_source": self._add_voltage_source,
            "current_source": self._add_current_source,
            "opamp": self._add_opamp,
            "ldo": self._add_ldo,
            "buck": self._add_buck,
            "boost": self._add_boost,
            "flyback": self._add_flyback,
            "transformer": self._add_transformer,
            "bjt": self._add_bjt_transistor,
            "mosfet": self._add_mosfet,
        }
        handler = handlers.get(self._kind(component))
        if handler is None:
            logger.warning(f"Unknown component type: {symbol} - skipping")
            return
        handler(component, ref, value)

    def _add_resistor(self, component, ref: str, value: str):
        """Add resistor to SPICE circuit."""
        # Get connected nodes
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Resistor {ref} needs 2 connections, got {len(nodes)}")
            return

        # Convert value to SPICE format
        spice_value = self._convert_value_to_spice(value, "R")

        # Add to SPICE circuit
        self.spice_circuit.R(ref, nodes[0], nodes[1], spice_value)
        logger.debug(f"Added resistor {ref}: {nodes[0]} -> {nodes[1]} = {spice_value}")

    def _add_capacitor(self, component, ref: str, value: str):
        """Add capacitor to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Capacitor {ref} needs 2 connections, got {len(nodes)}")
            return

        spice_value = self._convert_value_to_spice(value, "C")
        self.spice_circuit.C(ref, nodes[0], nodes[1], spice_value)
        logger.debug(f"Added capacitor {ref}: {nodes[0]} -> {nodes[1]} = {spice_value}")

    def _add_inductor(self, component, ref: str, value: str):
        """Add inductor to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Inductor {ref} needs 2 connections, got {len(nodes)}")
            return

        spice_value = self._convert_value_to_spice(value, "L")
        self.spice_circuit.L(ref, nodes[0], nodes[1], spice_value)
        logger.debug(f"Added inductor {ref}: {nodes[0]} -> {nodes[1]} = {spice_value}")

    def _device_model_name(self, component) -> Optional[str]:
        """Model name a diode/BJT/MOSFET references (shared by handlers + validate).

        Returns ``None`` if the component is not a modelled semiconductor. A bare
        type keyword in ``value`` (``'npn'``/``'pmos'``/...) selects the matching
        generic; an empty ``value`` falls back to the ``Default*`` generic implied
        by the symbol's polarity; any other ``value`` is used verbatim as the model
        name (which ``validate`` then checks resolves to a built-in).
        """
        kind = self._kind(component)
        if kind not in ("diode", "bjt", "mosfet"):
            return None
        symbol = str(self._attr(component, "symbol", "")).lower()
        # A Sim.Device token (NPN/PNP/NMOS/PMOS) sets polarity when the symbol
        # doesn't (e.g. a sim-only stand-in on a generic symbol).
        device = str(self._sim_props(component).get("device", "")).strip().lower()
        value = self._attr(component, "value", None)
        v = str(value).strip().lower() if value else ""
        if v in self._TYPE_KEYWORD_MODELS:
            return self._TYPE_KEYWORD_MODELS[v]
        if value:
            return str(value)
        if kind == "diode":
            return "DefaultDiode"
        if kind == "bjt":
            return (
                "DefaultPNP" if ("pnp" in symbol or device == "pnp") else "DefaultNPN"
            )
        return (
            "DefaultPMOS" if ("pmos" in symbol or device == "pmos") else "DefaultNMOS"
        )

    @staticmethod
    def _parse_sim_params(spec) -> dict:
        """Parse a KiCad ``Sim.Params`` string (``"bf=200 is=1e-14"``) to ``{K: v}``.

        Keys are upper-cased (ngspice model params are case-insensitive; upper-case
        matches the built-in generics). Accepts space- or comma-separated pairs.
        """
        out = {}
        if not spec:
            return out
        for token in str(spec).replace(",", " ").split():
            key, sep, val = token.partition("=")
            if sep and key.strip():
                out[key.strip().upper()] = val.strip()
        return out

    @staticmethod
    def _coerce_param(value):
        """Coerce a model-param value to float when it looks numeric, else keep it."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return value

    # SPICE model_type (from the built-in ModelLibrary) -> our device kind, used to
    # reject attaching e.g. an NPN model card to a diode.
    _MODEL_TYPE_TO_KIND = {
        "D": "diode",
        "NPN": "bjt",
        "PNP": "bjt",
        "NMOS": "mosfet",
        "PMOS": "mosfet",
    }

    def _lookup_model_spec(self, name, kind):
        """Resolve a model name through the ladder -> ((device_type, params), tier).

        Tier is ``generic`` (built-in ``Default*``), ``datasheet_fit`` (a matching
        entry in the built-in ``ModelLibrary``), or ``unresolved`` (unknown, or a
        library entry whose device type is wrong for ``kind``). Returns
        ``(None, "unresolved")`` in the last case so validate() can report it.
        """
        if name in self.GENERIC_MODELS:
            device_type, params = self.GENERIC_MODELS[name]
            return (device_type, dict(params)), "generic"
        try:
            from .models import get_model_library

            entry = get_model_library().get_model(name)
        except Exception:  # pragma: no cover - library import/init failure
            entry = None
        if entry is not None:
            mtype = str(entry.model_type).upper()
            if self._MODEL_TYPE_TO_KIND.get(mtype) == kind:
                return (entry.model_type, dict(entry.parameters)), "datasheet_fit"
        return None, "unresolved"

    def _resolve_device_model(self, component, ref) -> Optional[str]:
        """Model name a device instance should reference; resolve tier + Sim.Params.

        Resolves ``_device_model_name`` through the tiered ladder
        (datasheet_fit -> generic), records provenance for the device, and applies
        any ``Sim.Params`` override as a per-device derived card (``{base}_{ref}``)
        so it can't collide with another part's overrides. Returns None for
        non-semiconductors. An unresolved base is referenced verbatim (validate()
        reports it) and recorded as tier ``unresolved``.
        """
        kind = self._kind(component)
        if kind not in ("diode", "bjt", "mosfet"):
            return None
        base = self._device_model_name(component)
        spec, tier = self._lookup_model_spec(base, kind)
        overrides = self._parse_sim_params(self._sim_props(component).get("params"))

        if spec is None:
            # An unknown model name carrying Sim.Params is NOT a dead end: fall
            # back to the kind's generic and overlay the overrides as a derived
            # card, so an unlisted part can be param-fitted (bug #11). With NO
            # overrides this stays a hard, loud validation error (below).
            if overrides and kind in self._KIND_GENERIC:
                generic = self._KIND_GENERIC[kind]
                device_type, gparams = self.GENERIC_MODELS[generic]
                merged = dict(gparams)
                for key, val in overrides.items():
                    merged[key] = self._coerce_param(val)
                derived = f"{generic}_{ref}"
                self.derived_models[derived] = (device_type, merged)
                self.model_provenance[ref] = ResolvedModel(
                    ref, kind, "generic", f"{base}->{generic}", overridden=True
                )
                logger.warning(
                    f"{ref}: model '{base}' not in library; simulating as "
                    f"{generic} + Sim.Params overrides (tier=generic)"
                )
                return derived
            self.model_provenance[ref] = ResolvedModel(ref, kind, "unresolved", base)
            return base

        device_type, params = spec
        self.model_provenance[ref] = ResolvedModel(
            ref, kind, tier, base, overridden=bool(overrides)
        )
        logger.info(
            f"{ref} ({base}): model tier={tier}"
            + (" (+Sim.Params override)" if overrides else "")
        )

        if not overrides:
            self._register_model_card(base, device_type, params, tier)
            return base

        merged = dict(params)
        for key, val in overrides.items():
            merged[key] = self._coerce_param(val)
        derived = f"{base}_{ref}"
        self.derived_models[derived] = (device_type, merged)
        return derived

    def _register_model_card(self, name, device_type, params, tier):
        """Mark a model for emission by tier (generic -> built-in, else explicit)."""
        if tier == "generic":
            self.used_models.add(name)
        else:  # datasheet_fit: emit the library's params explicitly
            self.library_models[name] = (device_type, params)

    # ------------------------------------------------------------------ #
    # External vendor models: Sim.Library / Sim.Name / Sim.Pins (9.3)    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _spice_model_store_dir() -> str:
        """Local MPN-keyed model store (~/.circuit_synth/spice_models/models)."""
        try:
            from .model_store import get_model_store

            return get_model_store().models_dir
        except Exception:  # pragma: no cover
            return os.path.join(
                os.path.expanduser("~"), ".circuit_synth", "spice_models", "models"
            )

    def _lib_search_dirs(self) -> List[str]:
        """Directories a relative Sim.Library is resolved against, in order."""
        dirs = [os.getcwd(), self._spice_model_store_dir()]
        # Fall back near the circuit's own source file when we can tell where it is.
        src = getattr(self.circuit, "source_file", None) or getattr(
            self.circuit, "_source_file", None
        )
        if src:
            dirs.insert(0, os.path.dirname(os.path.abspath(str(src))))
        return dirs

    def _resolve_lib_path(self, lib) -> Optional[str]:
        """Resolve a Sim.Library reference to an absolute path (existing if found)."""
        if not lib:
            return None
        p = str(lib)
        if os.path.isabs(p):
            return p
        for base in self._lib_search_dirs():
            cand = os.path.join(base, p)
            if os.path.exists(cand):
                return os.path.abspath(cand)
        return os.path.abspath(p)  # may not exist; validate() reports it

    @staticmethod
    def _scan_lib(path, name):
        """Find ``name`` in a .lib/.sub file -> ('subckt', [nodes]) | ('model', None).

        Returns ``(None, None)`` if the file is unreadable or defines neither a
        ``.subckt`` nor a ``.model`` by that name. Subckt node names are read from
        the definition line (params like ``PARAM=1`` end the node list).
        """
        if not name or not path:
            return None, None
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            return None, None
        sub = re.search(
            rf"^\s*\.subckt\s+{re.escape(str(name))}\b(.*)$",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
        if sub:
            nodes = []
            for tok in sub.group(1).split():
                if tok.lower() == "params:" or "=" in tok:
                    break  # PSpice 'PARAMS:' keyword or the first param -> nodes end
                nodes.append(tok)
            return "subckt", nodes
        mod = re.search(
            rf"^\s*\.model\s+{re.escape(str(name))}\b",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
        if mod:
            return "model", None
        return None, None

    @staticmethod
    def _scan_lib_first(path):
        """First model in a file -> ('subckt', name, [nodes]) | ('model', name, None).

        Used for store files keyed only by MPN, where the internal model/subckt
        name isn't known ahead of time. Returns ``(None, None, None)`` if none.
        """
        if not path:
            return None, None, None
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            return None, None, None
        sub = re.search(
            r"^\s*\.subckt\s+(\S+)(.*)$", text, re.IGNORECASE | re.MULTILINE
        )
        mod = re.search(r"^\s*\.model\s+(\S+)", text, re.IGNORECASE | re.MULTILINE)
        # Honor whichever appears first in the file.
        if sub and (not mod or sub.start() < mod.start()):
            nodes = []
            for tok in sub.group(2).split():
                if tok.lower() == "params:" or "=" in tok:
                    break
                nodes.append(tok)
            return "subckt", sub.group(1), nodes
        if mod:
            return "model", mod.group(1), None
        return None, None, None

    @staticmethod
    def _parse_sim_pins(spec) -> dict:
        """Parse KiCad ``Sim.Pins`` (``"1=out 2=inp"``) -> {symbol_pin: target}."""
        out = {}
        if not spec:
            return out
        for tok in str(spec).replace(",", " ").split():
            key, sep, val = tok.partition("=")
            if sep and key.strip():
                out[key.strip()] = val.strip()
        return out

    def _symbol_pin_nodes(self, component) -> dict:
        """{symbol pin number (str): spice node} for a component's connected pins."""
        out = {}
        pin_map = getattr(component, "_pins", None)
        if isinstance(pin_map, dict):
            for num, pin in pin_map.items():
                net = getattr(pin, "net", None)
                name = getattr(net, "name", None)
                if name:
                    out[str(num)] = self.node_map.get(name, name)
        return out

    def _external_nodes(self, component, pins_spec, subckt_nodes) -> List[str]:
        """Order a component's nets to match an external subckt's node order.

        With ``Sim.Pins`` each symbol pin maps to a subckt node (by name or 1-based
        position); nodes are emitted in subckt-definition order. Without it, the
        symbol's connected pins are used in pin-number order.
        """
        sym_node = self._symbol_pin_nodes(component)
        mapping = self._parse_sim_pins(pins_spec)
        if not mapping:
            return [sym_node[k] for k in sorted(sym_node, key=self._pin_sort_key)]
        pos_node = {}
        for sym_pin, target in mapping.items():
            node = sym_node.get(str(sym_pin))
            if node is None:
                continue
            if subckt_nodes and target in subckt_nodes:
                idx = subckt_nodes.index(target) + 1
            else:
                try:
                    idx = int(target)
                except (TypeError, ValueError):
                    continue
            pos_node[idx] = node
        return [pos_node[i] for i in sorted(pos_node)]

    def _include_lib(self, path) -> None:
        """`.include` an external file once (idempotent per converter)."""
        if not path or path in self.included_libs:
            return
        self.included_libs.add(path)
        try:
            self.spice_circuit.include(path)
            logger.debug(f"Included SPICE library {path}")
        except Exception as exc:  # pragma: no cover - PySpice/ngspice specifics
            logger.warning(f"Failed to include SPICE library {path}: {exc}")

    def _add_external_model(self, component, ref) -> None:
        """Attach a device's external vendor model (Sim.Library + Sim.Name)."""
        sim = self._sim_props(component)
        name = sim.get("name")
        path = self._resolve_lib_path(sim.get("library"))
        kind_in_file, subckt_nodes = self._scan_lib(path, name)
        self._emit_external(
            component, ref, path, name, kind_in_file, subckt_nodes, "sim_library"
        )

    def _add_store_model(self, component, ref, path) -> None:
        """Attach a device's model from the local MPN store (name discovered)."""
        kind_in_file, name, subckt_nodes = self._scan_lib_first(path)
        self._emit_external(
            component, ref, path, name, kind_in_file, subckt_nodes, "local_store"
        )

    def _emit_external(
        self, component, ref, path, name, kind_in_file, subckt_nodes, source
    ) -> None:
        """Shared emit for an external model (Sim.Library or store), by file kind."""
        self._include_lib(path)
        dev_kind = self._kind(component)
        base = os.path.basename(str(path))

        if kind_in_file == "subckt":
            nodes = self._external_nodes(
                component, self._sim_props(component).get("pins"), subckt_nodes
            )
            if subckt_nodes and len(nodes) != len(subckt_nodes):
                logger.warning(
                    f"{ref}: subckt '{name}' takes {len(subckt_nodes)} nodes but "
                    f"{len(nodes)} were mapped (check Sim.Pins)"
                )
            # Pass Sim.Params through as subckt parameters (X ... NAME p=v). A
            # Sim.Library part has no other Sim.Params consumer (the derived-model
            # path is only reached for built-in primitives), so this is safe to
            # reuse. Empty -> no kwargs -> byte-identical to the pre-20.2 emission.
            xparams = {
                k.lower(): v
                for k, v in self._parse_sim_params(
                    self._sim_props(component).get("params")
                ).items()
            }
            self.spice_circuit.X(ref, name, *nodes, **xparams)
            self.model_provenance[ref] = ResolvedModel(
                ref, dev_kind or "subckt", "vendor_lib", name, source=source
            )
            logger.info(f"{ref}: external subckt {name} from {base} ({source})")
        elif kind_in_file == "model":
            nodes = self._get_component_nodes(component)
            self._emit_primitive_with_external_model(
                dev_kind, ref, name, nodes, component
            )
            self.model_provenance[ref] = ResolvedModel(
                ref, dev_kind or "?", "vendor_lib", name, source=source
            )
            logger.info(f"{ref}: external .model {name} from {base} ({source})")
        else:
            # validate() reports this in strict mode; lenient mode just skips.
            logger.warning(f"{ref}: no usable model found in {path} - skipping")

    def _emit_primitive_with_external_model(
        self, kind, ref, name, nodes, component=None
    ) -> None:
        """Emit a D/Q/M instance referencing an external ``.model`` name (no card)."""
        if kind == "diode" and len(nodes) >= 2:
            # Resolve A/K by pin name so a vendor-lib diode isn't reversed either
            # (bug #12). component is None only for legacy callers -> positional.
            if component is not None:
                self._emit_diode(component, ref, name)
            else:
                self.spice_circuit.D(ref, nodes[0], nodes[1], model=name)
        elif kind == "bjt" and len(nodes) >= 3:
            self.spice_circuit.Q(ref, nodes[0], nodes[1], nodes[2], model=name)
        elif kind == "mosfet" and len(nodes) >= 3:
            bulk = nodes[3] if len(nodes) >= 4 else nodes[2]
            self.spice_circuit.M(ref, nodes[0], nodes[1], nodes[2], bulk, model=name)
        else:
            logger.warning(
                f"{ref}: external .model '{name}' needs a diode/BJT/MOSFET device "
                f"(kind={kind}, {len(nodes)} nodes) - skipping"
            )

    def _has_external_lib(self, component) -> bool:
        return bool(self._sim_props(component).get("library"))

    def _component_mpn(self, component) -> Optional[str]:
        """The MPN a component names, from an ``mpn`` field or its ``value``."""
        extra = getattr(component, "_extra_fields", None)
        if isinstance(extra, dict):
            for key in ("mpn", "MPN", "Mpn"):
                if extra.get(key):
                    return str(extra[key])
        value = self._attr(component, "value", None)
        return str(value) if value else None

    def _store_lib_for(self, component) -> Optional[str]:
        """Path to a local-store model file matching this device's MPN, or None.

        Only active devices (diode/BJT/MOSFET/op-amp) are matched, so a passive
        R/C/L is never hijacked by a coincidentally-named file. An explicit
        ``Sim.Library`` always takes precedence (handled before this is consulted).
        """
        if self._kind(component) not in ("diode", "bjt", "mosfet", "opamp"):
            return None
        mpn = self._component_mpn(component)
        if not mpn:
            return None
        try:
            from .model_store import get_model_store

            return get_model_store().lookup(mpn)
        except Exception:  # pragma: no cover
            return None

    def _emit_models(self):
        """Emit a ``.model`` card for each referenced built-in and derived model.

        Only models actually used by a component are emitted (PySpice would
        otherwise serialize every registered model). Unresolved custom model names
        are left to ``validate`` to report; in the lenient path they simply have no
        card (ngspice then errors on them, as before)."""
        for name in sorted(self.used_models):
            spec = self.GENERIC_MODELS.get(name)
            if spec is None:
                continue
            device_type, params = spec
            self.spice_circuit.model(name, device_type, **params)
            logger.debug(f"Emitted .model {name} {device_type}")
        for name in sorted(self.library_models):
            device_type, params = self.library_models[name]
            self.spice_circuit.model(name, device_type, **params)
            logger.debug(f"Emitted datasheet-fit .model {name} {device_type}")
        for name in sorted(self.derived_models):
            device_type, params = self.derived_models[name]
            self.spice_circuit.model(name, device_type, **params)
            logger.debug(f"Emitted derived .model {name} {device_type}")

        # One honest summary line: which fidelity tier every active device got, so
        # a textbook generic is never silently mistaken for the real part.
        if self.model_provenance:
            summary = ", ".join(
                f"{r}={p.tier}" for r, p in sorted(self.model_provenance.items())
            )
            logger.info(f"Model provenance: {summary}")
            generics = [
                p.name for p in self.model_provenance.values() if p.tier == "generic"
            ]
            if generics:
                logger.warning(
                    "Simulating with textbook-generic models (not datasheet-fit) "
                    f"for: {', '.join(sorted(set(generics)))}"
                )

    # Diode terminal pin names. KiCad Device:D/D_Schottky/D_Zener/LED all put
    # K (cathode) on pin 1 and A (anode) on pin 2, so pin-number order is the
    # reverse of SPICE's (anode, cathode) -- resolve by name instead (bug #12).
    _DIODE_ANODE_NAMES = {"A", "A1", "AA", "+"}
    _DIODE_CATHODE_NAMES = {"K", "K1", "KK", "-"}

    def _diode_terminals(self, component):
        """(anode_node, cathode_node) resolved by pin NAME, or None.

        Returns None -- so ``_add_diode`` falls back to positional order -- when
        there is no live pin map (dict/JSON circuits) or the connected pins don't
        yield exactly one anode-named and one cathode-named terminal (unnamed or
        multi-unit symbols). Only connected pins (``pin.net`` set) are considered.
        """
        pin_map = getattr(component, "_pins", None)
        if not isinstance(pin_map, dict):
            return None
        anode = cathode = None
        for pin in pin_map.values():
            net = getattr(pin, "net", None)
            if net is None:
                continue
            name = (getattr(pin, "name", "") or "").strip().upper()
            node = self.node_map.get(net.name, net.name)
            if name in self._DIODE_ANODE_NAMES:
                if anode is not None:
                    return None  # ambiguous
                anode = node
            elif name in self._DIODE_CATHODE_NAMES:
                if cathode is not None:
                    return None  # ambiguous
                cathode = node
        if anode is None or cathode is None:
            return None
        return anode, cathode

    def _emit_diode(self, component, ref: str, model_name: str) -> bool:
        """Emit one SPICE ``D`` card, terminals by A/K pin name, positional fallback.

        SPICE ``D`` is (anode, cathode). Resolving by name means a
        schematically-correct diode (KiCad pin 1 = K, pin 2 = A) simulates in the
        right direction (bug #12). Falls back to pin-number order only when the
        names can't be resolved -- and warns, so the fallback is never silent.
        Shared by the built-in path (``_add_diode``) and the external-model path
        (``_emit_primitive_with_external_model``). Returns False if the diode had
        too few connections to emit.
        """
        terminals = self._diode_terminals(component)
        if terminals is not None:
            anode, cathode = terminals
            self.spice_circuit.D(ref, anode, cathode, model=model_name)
            logger.debug(
                f"Added diode {ref}: A={anode} K={cathode} model={model_name} (by name)"
            )
            return True

        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Diode {ref} needs 2 connections, got {len(nodes)}")
            return False
        logger.warning(
            f"Diode {ref}: pins not resolvable by A/K name; using pin-number "
            f"order (pin1=anode). Verify polarity."
        )
        self.spice_circuit.D(ref, nodes[0], nodes[1], model=model_name)
        logger.debug(
            f"Added diode {ref}: {nodes[0]} -> {nodes[1]} model={model_name} (positional)"
        )
        return True

    def _add_diode(self, component, ref: str, value: str):
        """Add a built-in-model diode to the SPICE circuit (terminals by A/K name)."""
        model_name = self._resolve_device_model(component, ref) or "DefaultDiode"
        self._emit_diode(component, ref, model_name)

    # Ideal op-amp open-loop gain. Large enough that closed-loop behaviour is set
    # by the feedback network, frequency-independent (infinite GBW) so an active
    # filter's response is the RC network alone.
    OPAMP_OPEN_LOOP_GAIN = 1e6

    # Output-typed pins that aren't the real signal output on some dual-output
    # op-amp symbols (e.g. ADA4817 pin 2 is FB). Prefer a pin not named these.
    _OPAMP_NON_OUTPUT_PIN_NAMES = {"FB", "COMP"}

    def _opamp_terminals(self, component, pin_nums=None):
        """Resolve an op-amp's (out, in+, in-) SPICE nodes by pin function/name.

        Op-amp pins must be mapped semantically, not by position: KiCad pinouts
        vary (an LM358 unit is out=1, in-=2, in+=3), so pin-number order would
        swap the inputs. Uses the live pin map and considers only *connected*
        pins, so the unused unit of a dual op-amp (pins with no net) is skipped.
        Power pins (V+/V-) are not needed by the ideal model. Returns
        (out, in_plus, in_minus) spice nodes, or None if a signal terminal is
        missing or no live pin map is available.

        ``pin_nums`` (a set of pin-number strings) restricts resolution to one
        unit of a multi-unit symbol, so each amplifier section of a dual/quad
        gets its own terminals instead of all units collapsing together.
        """
        pin_map = getattr(component, "_pins", None)
        if not isinstance(pin_map, dict):
            return None
        outputs = []  # (pin_name, node) for every connected output-func pin
        in_plus = in_minus = None
        for num, pin in pin_map.items():
            if pin_nums is not None and str(num) not in pin_nums:
                continue  # a different unit's pin
            net = getattr(pin, "net", None)
            if net is None:
                continue  # unconnected (e.g. the unused unit of a dual op-amp)
            func = str(getattr(pin, "func", "")).lower()
            name = (getattr(pin, "name", "") or "").strip()
            node = self.node_map.get(net.name, net.name)
            if "output" in func:
                outputs.append((name, node))
            elif name == "+":
                in_plus = node
            elif name == "-":
                in_minus = node
        out = self._choose_opamp_output(component, outputs)
        if out is None or in_plus is None or in_minus is None:
            return None
        return out, in_plus, in_minus

    def _choose_opamp_output(self, component, outputs):
        """Pick the real output node from an op-amp's output-func pins.

        Some symbols expose more than one output-typed pin -- e.g. ADA4817 has pin 2
        ``FB`` (feedback, output-typed) and pin 7 ``OUT``. The old code kept whichever
        was iterated last (dict order), so a symbol with FB and OUT on *different*
        nets resolved nondeterministically and could open the feedback loop silently
        (report F4). The ideal VCVS has no separate feedback concept, so drive the
        true OUT: prefer a pin whose name isn't ``FB``/``COMP``. When output pins land
        on more than one distinct net, warn -- the single-output model can't represent
        that, so the user should know which pin was driven.
        """
        if not outputs:
            return None
        preferred = [
            (n, node)
            for (n, node) in outputs
            if n.upper() not in self._OPAMP_NON_OUTPUT_PIN_NAMES
        ]
        chosen_name, chosen_node = (preferred or outputs)[0]
        if len({node for (_, node) in outputs}) > 1:
            ref = getattr(component, "ref", None) or "?"
            ignored = ", ".join(
                sorted(f"{n}->{node}" for (n, node) in outputs if node != chosen_node)
            )
            logger.warning(
                f"Op-amp {ref} has output pins on multiple nets; driving "
                f"'{chosen_name}'->{chosen_node}, ignoring {ignored}. The ideal VCVS "
                f"models a single output -- verify this matches intent."
            )
        return chosen_node

    def _opamp_amp_units(self, component):
        """``{unit_number: {pin_numbers}}`` for the amplifier units of a
        multi-unit op-amp symbol -- units with at least one input pin AND one
        output pin. Power-only units (e.g. LM358 unit 3 = V+/V-) are excluded;
        the ideal/GBW model ignores supply pins.

        Returns ``{}`` when the symbol resolves to a single unit or can't be
        resolved, so the caller keeps the whole-component path. The pin->unit
        map is read from the KiCad symbol (Component.Pin.unit is not populated),
        the same source the schematic writer uses to place per-unit bodies.
        """
        symbol = self._attr(component, "symbol", None) or getattr(
            component, "symbol", None
        )
        if not symbol:
            return {}
        try:
            from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

            data = SymbolLibCache.get_symbol_data(symbol)
        except Exception:
            return {}
        if not data or data.get("unit_count", 1) <= 1:
            return {}
        unit_pins = {}  # unit -> {pin number strings}
        unit_has = {}  # unit -> {"in": bool, "out": bool}
        for p in data.get("pins", []):
            num = str(p.get("number", "")).strip()
            unit = p.get("unit", 0)
            if not num or not unit:  # unit 0 = common-to-all; not an amp section
                continue
            func = str(p.get("function", "")).lower()
            name = (p.get("name", "") or "").strip()
            unit_pins.setdefault(unit, set()).add(num)
            flags = unit_has.setdefault(unit, {"in": False, "out": False})
            if "output" in func:
                flags["out"] = True
            elif "input" in func or name in ("+", "-"):
                flags["in"] = True
        return {
            u: pins
            for u, pins in unit_pins.items()
            if unit_has.get(u, {}).get("in") and unit_has.get(u, {}).get("out")
        }

    def _add_opamp(self, component, ref: str, value: str):
        """Add an op-amp: ideal VCVS by default, 1-pole GBW macromodel when opted in.

        Terminals are resolved by pin function/name so the model is correct
        regardless of the symbol's pin numbering. Falls back to a positional guess
        only when no live pin map is available (dict/JSON-shaped circuits).

        A **multi-unit** symbol (dual/quad) with more than one wired amplifier
        section emits **one model per wired unit** -- otherwise both halves of a
        dual collapse into a single VCVS, leaving the second section's output net
        undriven (singular matrix, hard sim failure; bug #A). The first
        amplifier unit keeps the plain ``ref`` element name for netlist
        backward-compatibility; later units get ``{ref}u{unit}``. The die's GBW
        (if any) applies to every unit.

        Without a gain-bandwidth product the op-amp is an ideal VCVS with
        frequency-independent gain ``OPAMP_OPEN_LOOP_GAIN`` (exactly as before). With
        a GBW -- from an explicit ``Sim.Gbw`` field, or a ModelLibrary OPAMP entry
        whose ``value``/name carries a ``GBW`` param -- it becomes a single-pole
        macromodel so source/feedback capacitance limits bandwidth and can peak. Slew
        rate is out of scope (nonlinear); this models only the small-signal pole.
        """
        gbw_hz, tier = self._opamp_gbw(component, value)

        amp_units = self._opamp_amp_units(component)
        pin_map = getattr(component, "_pins", None)
        # Per-unit emission only when there are 2+ amplifier units AND a live pin
        # map to resolve each unit's terminals; otherwise the whole-component
        # path (incl. the dict/JSON positional fallback) runs unchanged.
        if len(amp_units) > 1 and isinstance(pin_map, dict):
            emitted = 0
            for unit in sorted(amp_units):
                unit_pins = amp_units[unit]
                wired = any(
                    getattr(pin, "net", None) is not None
                    for num, pin in pin_map.items()
                    if str(num) in unit_pins
                )
                if not wired:
                    continue  # unused spare section -- fine to leave unmodeled
                terminals = self._opamp_terminals(component, pin_nums=unit_pins)
                if terminals is None:
                    logger.warning(
                        f"Op-amp {ref} unit {unit} is partially wired (missing an "
                        f"input or output terminal); skipping this section"
                    )
                    continue
                out, in_plus, in_minus = terminals
                elem_ref = ref if emitted == 0 else f"{ref}u{unit}"
                self._emit_opamp_model(elem_ref, out, in_plus, in_minus, gbw_hz)
                emitted += 1
            if emitted:
                self._record_opamp_provenance(ref, tier, gbw_hz, units=emitted)
                return
            # Nothing wired -> fall through to the single-model path (which will
            # warn about too-few connections), preserving prior behavior.

        terminals = self._opamp_terminals(component)
        if terminals is None:
            nodes = self._get_component_nodes(component)
            if len(nodes) < 3:
                logger.warning(
                    f"Op-amp {ref} needs at least 3 connections, got {len(nodes)}"
                )
                return
            # Legacy positional fallback: [out, in+, in-].
            out, in_plus, in_minus = nodes[0], nodes[1], nodes[2]
        else:
            out, in_plus, in_minus = terminals

        self._emit_opamp_model(ref, out, in_plus, in_minus, gbw_hz)
        self._record_opamp_provenance(ref, tier, gbw_hz, units=1)

    def _emit_opamp_model(self, elem_ref, out, in_plus, in_minus, gbw_hz):
        """Emit one op-amp section: ideal VCVS, or the 1-pole GBW macromodel."""
        if gbw_hz is None:
            self._add_ideal_opamp(elem_ref, out, in_plus, in_minus)
        else:
            self._add_gbw_opamp(elem_ref, out, in_plus, in_minus, gbw_hz)

    def _record_opamp_provenance(self, ref, tier, gbw_hz, units):
        """One provenance entry per op-amp ref (not per unit). Notes the wired
        unit count when more than one section was modeled."""
        if gbw_hz is None:
            name = "ideal_vcvs"
            tier = "generic"
        else:
            name = f"gbw_1pole({self._fmt_hz(gbw_hz)})"
        if units > 1:
            name = f"{name} x{units} units"
        self.model_provenance[ref] = ResolvedModel(
            ref=ref, kind="opamp", tier=tier, name=name
        )

    def _add_ideal_opamp(self, ref, out, in_plus, in_minus):
        """Ideal op-amp: a single high-gain VCVS (unchanged legacy behaviour)."""
        gain = self.OPAMP_OPEN_LOOP_GAIN
        self.spice_circuit.VCVS(
            ref, out, self.spice_circuit.gnd, in_plus, in_minus, gain
        )
        logger.debug(
            f"Added op-amp {ref} (ideal VCVS, gain={gain}): "
            f"out={out}, in+={in_plus}, in-={in_minus}"
        )

    def _add_gbw_opamp(self, ref, out, in_plus, in_minus, gbw_hz):
        """Single-pole GBW-limited op-amp macromodel.

        ``Aol(s) = Aol0 / (1 + s/wp)`` with ``wp = 2*pi*GBW/Aol0``. Realized as a
        high-gain VCVS (Aol0) into an R-C low-pass (``R*C = 1/wp``), then a unity
        VCVS buffer driving the output node so the pole is unloaded by the feedback
        network. Two internal nodes per op-amp, named from ``ref``.
        """
        gnd = self.spice_circuit.gnd
        aol0 = self.OPAMP_OPEN_LOOP_GAIN
        wp = 2.0 * math.pi * gbw_hz / aol0  # dominant-pole angular frequency
        # Fix C, solve R for R*C = 1/wp (both stay in a numerically sane range).
        cap = 1e-9
        res = 1.0 / (wp * cap)

        p1 = f"{ref}_p1"  # gain-stage output (before the pole)
        p2 = f"{ref}_p2"  # after the R-C pole -> buffered to `out`
        self.spice_circuit.VCVS(f"{ref}_a", p1, gnd, in_plus, in_minus, aol0)
        self.spice_circuit.R(f"{ref}_p", p1, p2, res)
        self.spice_circuit.C(f"{ref}_p", p2, gnd, cap)
        self.spice_circuit.VCVS(f"{ref}_b", out, gnd, p2, gnd, 1.0)
        logger.debug(
            f"Added op-amp {ref} (1-pole GBW macromodel, GBW={self._fmt_hz(gbw_hz)}, "
            f"Aol0={aol0}, fp={wp / (2 * math.pi):.3g} Hz): out={out}, "
            f"in+={in_plus}, in-={in_minus}"
        )

    def _opamp_gbw(self, component, value):
        """Resolve an op-amp's gain-bandwidth product (Hz) and provenance tier.

        Explicit ``Sim.Gbw`` wins; otherwise a ``value``/name hit in the ModelLibrary
        on an OPAMP-type model carrying a ``GBW`` param. Returns ``(gbw_hz, tier)``
        with tier ``sim_params`` (explicit) or ``datasheet_fit`` (library), or
        ``(None, "generic")`` when neither is present -> ideal VCVS.
        """
        gbw_field = self._sim_props(component).get("gbw")
        if gbw_field is not None and str(gbw_field).strip():
            gbw = self._parse_frequency(gbw_field)
            if gbw and gbw > 0:
                return gbw, "sim_params"
            logger.warning(
                f"Op-amp {getattr(component, 'ref', '?')}: could not parse "
                f"Sim.Gbw '{gbw_field}'; falling back to ideal op-amp model"
            )

        name = (value or "").strip()
        if name:
            try:
                from circuit_synth.simulation.models import get_model_library

                model = get_model_library().models.get(name)
            except Exception:
                model = None
            if (
                model is not None
                and str(getattr(model, "model_type", "")).upper() == "OPAMP"
            ):
                gbw = getattr(model, "parameters", {}).get("GBW")
                if gbw and float(gbw) > 0:
                    return float(gbw), "datasheet_fit"
        return None, "generic"

    # ------------------------------------------------------------------ #
    # Linear regulators / LDOs: Tier-A behavioral macromodel (Stage 20.1) #
    # ------------------------------------------------------------------ #

    # Pin names (upper-cased) that identify an LDO's three terminals, so the model
    # is correct regardless of the symbol's pin numbering. First connected match
    # wins. A ground pin named ADJ is accepted (adjustable parts) but warned about.
    _LDO_IN_NAMES = {"VI", "VIN", "IN", "VIN+", "IN+", "VCC"}
    _LDO_OUT_NAMES = {"VO", "VOUT", "OUT"}
    _LDO_GND_NAMES = {"GND", "ADJ", "GND/ADJ"}

    # Macromodel param defaults (VOUT has no default -- it must be resolved).
    _LDO_PARAM_DEFAULTS = {"VDROP": 0.3, "RSER": 0.05, "IQ": 1e-3}

    @staticmethod
    def _parse_si_number(raw) -> Optional[float]:
        """Parse an LDO param value ('3.3', '0.3', '100m', '2m', '1u') to float.

        For LDO params (volts / ohms / amps) a bare ``m`` means **milli** and ``u``
        micro -- unlike the resistor-value parser, mega/kilo-scale regulator params
        are nonsensical here, so this small dedicated parser keeps ``m`` unambiguous.
        Plain decimals pass straight through. Returns None if unparseable.
        """
        if raw is None:
            return None
        s = str(raw).strip().lower().replace(" ", "")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            pass
        m = re.match(r"^(-?[0-9.]+)([a-z]+)$", s)
        if not m:
            return None
        mult = {
            "k": 1e3,
            "meg": 1e6,
            "m": 1e-3,
            "u": 1e-6,
            "n": 1e-9,
            "p": 1e-12,
        }.get(m.group(2))
        if mult is None:
            return None
        try:
            return float(m.group(1)) * mult
        except ValueError:
            return None

    def _ldo_terminals(self, component):
        """Resolve an LDO's (in, out, gnd) SPICE nodes by pin NAME.

        Uses the live pin map and considers only connected pins, so an unconnected
        EN/SENSE pin is ignored. Returns ``(nin, nout, ngnd)`` or None when a signal
        terminal is missing or no live pin map is available (dict/JSON circuits).
        """
        pin_map = getattr(component, "_pins", None)
        if not isinstance(pin_map, dict):
            return None
        nin = nout = ngnd = None
        adj_used = False
        for pin in pin_map.values():
            net = getattr(pin, "net", None)
            if net is None:
                continue
            name = (getattr(pin, "name", "") or "").strip().upper()
            node = self.node_map.get(net.name, net.name)
            if nin is None and name in self._LDO_IN_NAMES:
                nin = node
            elif nout is None and name in self._LDO_OUT_NAMES:
                nout = node
            elif ngnd is None and name in self._LDO_GND_NAMES:
                ngnd = node
                adj_used = name == "ADJ"
        if nin is None or nout is None or ngnd is None:
            return None
        if adj_used:
            logger.warning(
                f"LDO {getattr(component, 'ref', '?')}: ADJ pin used as the "
                f"reference/ground node; adjustable output modeled as a fixed VOUT "
                f"(the external divider is not read)"
            )
        return nin, nout, ngnd

    def _ldo_lib_params(self, value) -> Optional[dict]:
        """LDO macromodel params from a ModelLibrary entry named by ``value``.

        A SUBCKT-type entry carrying a ``VOUT`` param maps VOUT/VDROPOUT/IQ onto the
        macromodel (RSER falls back to its default). Returns None if no such entry.
        """
        name = (value or "").strip()
        if not name:
            return None
        try:
            from circuit_synth.simulation.models import get_model_library

            model = get_model_library().models.get(name)
        except Exception:  # pragma: no cover - library import/init failure
            model = None
        params = getattr(model, "parameters", None) if model is not None else None
        if not isinstance(params, dict) or "VOUT" not in params:
            return None
        return {
            "VOUT": float(params["VOUT"]),
            "VDROP": float(params.get("VDROPOUT", self._LDO_PARAM_DEFAULTS["VDROP"])),
            "RSER": float(params.get("RSER", self._LDO_PARAM_DEFAULTS["RSER"])),
            "IQ": float(params.get("IQ", self._LDO_PARAM_DEFAULTS["IQ"])),
        }

    def _ldo_params(self, component, value):
        """(params, tier) for an LDO, or ``(None, "sim_params")`` if VOUT unresolved.

        ``Sim.Params`` (with VOUT) wins at tier ``sim_params``; otherwise a
        ModelLibrary entry named by ``value`` gives tier ``datasheet_fit``.
        """
        raw = self._parse_sim_params(self._sim_props(component).get("params"))
        if "VOUT" in raw:
            vout = self._parse_si_number(raw["VOUT"])
            if vout is not None:
                params = {"VOUT": vout}
                for key, default in self._LDO_PARAM_DEFAULTS.items():
                    parsed = self._parse_si_number(raw[key]) if key in raw else None
                    params[key] = parsed if parsed is not None else default
                return params, "sim_params"
        lib = self._ldo_lib_params(value)
        if lib is not None:
            return lib, "datasheet_fit"
        return None, "sim_params"

    @staticmethod
    def _fmt_num(x: float) -> str:
        """Compact numeric literal for a netlist ('3.3', '0.002', not '0.0020000')."""
        return f"{x:g}"

    def _stub_unmodeled_pins(self, component, ref, modeled_nodes, gnd) -> None:
        """Tie each connected-but-unmodeled pin's node to ground through 1 GOhm.

        A macromodel drives only its resolved terminals; a real part's other pins
        (NR/SS/BYP/COMP/EN...) remain plain nodes. If such a node's net is cap-only
        (the usual decoupling), it has NO DC path, so ngspice's op-point solve hits
        a ``singular matrix`` on it (bug #16). A 1 GOhm resistor to ground gives the
        node a DC path at ~nA leakage -- harmless whether the net is cap-only,
        driven (an EN header), or resistor-loaded.

        ``modeled_nodes`` are the SPICE nodes the macromodel already uses; those and
        the ground node are skipped, and each remaining node is stubbed once (a pin
        group all tapping one node -- e.g. several pads on OUT -- yields no stub). No
        live pin map (dict/JSON circuits) -> no stubs.
        """
        pin_map = getattr(component, "_pins", None)
        if not isinstance(pin_map, dict):
            return
        skip = {str(n) for n in modeled_nodes if n is not None} | {str(gnd)}
        stubbed = set()
        lines = []
        for pin in pin_map.values():
            net = getattr(pin, "net", None)
            if net is None:
                continue
            node = str(self.node_map.get(net.name, net.name))
            if node in skip or node in stubbed:
                continue
            stubbed.add(node)
            lines.append(f"R{ref}_stub{len(stubbed)} {node} {gnd} 1e9")
            logger.debug(f"{ref}: 1G stub on unmodeled pin net {node}")
        if lines:
            self.spice_circuit.raw_spice += "\n" + "\n".join(lines)

    def _add_ldo(self, component, ref: str, value: str):
        """Add a linear regulator as a datasheet-parameterized behavioral macromodel.

        Emits (VOUT/VDROP/RSER/IQ from Sim.Params or a ModelLibrary entry)::

            B<ref>_reg <reg> <gnd> V = min(VOUT, V(<in>,<gnd>)-VDROP)
            R<ref>_ser <reg> <out> RSER
            B<ref>_iq  <in> <gnd> I = IQ

        so the output regulates to VOUT, tracks (VIN-VDROP) in dropout, and draws a
        quiescent current from the input. The B-sources go through ``raw_spice``
        (PySpice has no first-class behavioral-source polarity we need); the series
        resistor is a normal element. Limitation: no current limit / thermal
        foldback -- the output is a voltage-behavioral source and will source
        unlimited current into a short.
        """
        terminals = self._ldo_terminals(component)
        if terminals is None:
            nodes = self._get_component_nodes(component)
            if len(nodes) < 3:
                logger.warning(
                    f"LDO {ref} needs at least 3 connections, got {len(nodes)}"
                )
                return
            # Positional fallback (no live pin names): assume 78xx-style IN, GND, OUT.
            nin, ngnd, nout = nodes[0], nodes[1], nodes[2]
            logger.warning(
                f"LDO {ref}: no live pin map; assuming pin order IN, GND, OUT"
            )
        else:
            nin, nout, ngnd = terminals

        params, tier = self._ldo_params(component, value)
        if params is None:
            # validate() reports this in strict mode; the lenient path just skips.
            logger.warning(
                f"LDO {ref}: no VOUT resolved -- skipping "
                f'(set Sim.Params="vout=3.3 vdrop=0.3")'
            )
            return

        vout = self._fmt_num(params["VOUT"])
        vdrop = self._fmt_num(params["VDROP"])
        rser = self._fmt_num(params["RSER"])
        iq = self._fmt_num(params["IQ"])
        gnd = str(ngnd)
        inn = str(nin)
        reg = f"{ref}_reg"

        self.spice_circuit.raw_spice += (
            f"\nB{ref}_reg {reg} {gnd} V = min({vout}, V({inn},{gnd})-{vdrop})"
        )
        self.spice_circuit.R(f"{ref}_ser", reg, nout, rser)
        self.spice_circuit.raw_spice += f"\nB{ref}_iq {inn} {gnd} I = {iq}"

        # Give cap-only unmodeled pins (NR/BYP/EN...) a DC path so the op-point solves.
        self._stub_unmodeled_pins(component, ref, {nin, nout, ngnd}, gnd)

        self.model_provenance[ref] = ResolvedModel(
            ref=ref,
            kind="ldo",
            tier=tier,
            name=f"ldo_macro(vout={vout},vdrop={vdrop})",
        )
        logger.debug(
            f"Added LDO {ref} (behavioral macromodel, tier={tier}): in={inn}, "
            f"out={nout}, gnd={gnd}, VOUT={vout}, VDROP={vdrop}, RSER={rser}, IQ={iq}"
        )

    # ------------------------------------------------------------------ #
    # Transformers: coupled inductors via a K element (Stage 21.1)        #
    # ------------------------------------------------------------------ #

    def _transformer_terminals(self, component):
        """Resolve a 1P/1S transformer's AA/AB/SA/SB SPICE nodes by pin name.

        KiCad's ``Device:Transformer_1P_1S`` names its pins AA/AB (primary) and
        SA/SB (secondary), with the polarity dots printed at AA and SA. Returns a
        dict of all four nodes or None when any winding end is unconnected (no
        half-wound transformers) or no live pin map is available.
        """
        pin_map = getattr(component, "_pins", None)
        if not isinstance(pin_map, dict):
            return None
        nodes = {}
        for pin in pin_map.values():
            net = getattr(pin, "net", None)
            if net is None:
                continue
            name = (getattr(pin, "name", "") or "").strip().upper()
            if name in ("AA", "AB", "SA", "SB") and name not in nodes:
                nodes[name] = self.node_map.get(net.name, net.name)
        if set(nodes) != {"AA", "AB", "SA", "SB"}:
            return None
        return nodes

    def _transformer_params(self, component) -> Optional[dict]:
        """Winding params for a transformer, or None if LP / the ratio is missing.

        ``LP`` (primary inductance) is required; the secondary comes from an
        explicit ``LS`` or is derived as ``LP*N^2`` from the turns ratio ``N``
        (Ns/Np). ``K`` is the coupling coefficient, default 0.999; a value outside
        (0, 1] is rejected (ngspice requires it).
        """
        raw = self._parse_sim_params(self._sim_props(component).get("params"))
        lp = self._parse_si_number(raw["LP"]) if "LP" in raw else None
        if not lp or lp <= 0:
            return None
        ls = self._parse_si_number(raw["LS"]) if "LS" in raw else None
        if ls is None:
            n_ratio = self._parse_si_number(raw["N"]) if "N" in raw else None
            if not n_ratio or n_ratio <= 0:
                return None
            ls = lp * n_ratio * n_ratio
        if ls <= 0:
            return None
        k = self._parse_si_number(raw["K"]) if "K" in raw else 0.999
        if k is None or not (0 < k <= 1):
            return {"LP": lp, "LS": ls, "K": None}  # bad k -> validate() names it
        return {"LP": lp, "LS": ls, "K": k}

    def _add_transformer(self, component, ref: str, value: str):
        """Emit a transformer as two coupled inductors + a ``K`` card (raw_spice).

        Node order follows the KiCad symbol's dots (AA first, SA first), so the
        SPICE dot convention matches the printed dots and winding polarity is set
        entirely by user wiring -- a flyback ties the secondary dot (SA) to the
        secondary return and feeds the rectifier from SB. Winding currents are
        readable via ``branch_current("<ref>_P")`` / ``("<ref>_S")``.

        Simulation caveat (SPICE, not the design): every node needs a DC path to
        ground, so a galvanically isolated secondary must share the sim's GND net
        (or bridge to it through a large resistor).
        """
        term = self._transformer_terminals(component)
        if term is None:
            logger.warning(
                f"transformer {ref}: needs all of AA/AB/SA/SB connected - skipping"
            )
            return
        params = self._transformer_params(component)
        if params is None or params["K"] is None:
            logger.warning(
                f"transformer {ref}: unresolved winding params - skipping "
                f'(set Sim.Params="lp=100u n=0.5")'
            )
            return
        n = self._fmt_num
        lp, ls, k = n(params["LP"]), n(params["LS"]), n(params["K"])
        lines = [
            f"L{ref}_P {term['AA']} {term['AB']} {lp}",
            f"L{ref}_S {term['SA']} {term['SB']} {ls}",
            f"K{ref} L{ref}_P L{ref}_S {k}",
        ]
        self.spice_circuit.raw_spice += "\n" + "\n".join(lines)
        self.model_provenance[ref] = ResolvedModel(
            ref, "transformer", "sim_params", f"xfmr(lp={lp}, ls={ls}, k={k})"
        )
        logger.info(
            f"{ref}: transformer as coupled inductors (lp={lp}, ls={ls}, k={k}); "
            f"dots at AA/SA per the KiCad symbol"
        )

    # ------------------------------------------------------------------ #
    # Switching regulators: behavioral buck/boost macromodel (Stage 20.3) #
    # ------------------------------------------------------------------ #

    # Pin names (upper-cased) identifying a switcher's terminals. SW/VIN/GND are
    # required by the model; FB is the user's divider tap (not read by the
    # open-loop model, resolved only for completeness). First connected match wins.
    _SWITCH_SW_NAMES = {"SW", "LX", "SWITCH", "PH", "L1", "LX1"}
    _SWITCH_FB_NAMES = {"FB", "VFB", "FEEDBACK", "VSENSE", "SENSE"}
    _SWITCH_VIN_NAMES = {"VIN", "IN", "PVIN", "AVIN", "VCC"}
    _SWITCH_GND_NAMES = {"GND", "PGND", "AGND", "EP"}

    def _switcher_terminals(self, component):
        """Resolve a switcher's SW/VIN/GND (and optional FB) SPICE nodes by pin name.

        Returns a dict ``{"sw","vin","gnd","fb"}`` (fb may be None) or None when a
        required terminal is missing or no live pin map is available.
        """
        pin_map = getattr(component, "_pins", None)
        if not isinstance(pin_map, dict):
            return None
        sw = vin = gnd = fb = None
        for pin in pin_map.values():
            net = getattr(pin, "net", None)
            if net is None:
                continue
            name = (getattr(pin, "name", "") or "").strip().upper()
            node = self.node_map.get(net.name, net.name)
            if sw is None and name in self._SWITCH_SW_NAMES:
                sw = node
            elif vin is None and name in self._SWITCH_VIN_NAMES:
                vin = node
            elif gnd is None and name in self._SWITCH_GND_NAMES:
                gnd = node
            elif fb is None and name in self._SWITCH_FB_NAMES:
                fb = node
        if sw is None or vin is None or gnd is None:
            return None
        return {"sw": sw, "vin": vin, "gnd": gnd, "fb": fb}

    def _switcher_params(self, component, value, topology) -> Optional[dict]:
        """Macromodel params for a switcher, or None if a required one is missing.

        VOUT (target output) and FSW (switching frequency) are required; a flyback
        additionally requires N (the transformer turns ratio Ns/Np -- the CCM duty
        needs it, and it cannot be read from the separate transformer component).
        VF (diode drop used for the first-order duty correction), DMAX, RON_HS,
        VRAMP and VCLAMP (the flyback's emitted drain-clamp breakdown) take
        defaults. All parsed with the milli-aware SI parser.
        """
        raw = self._parse_sim_params(self._sim_props(component).get("params"))
        vout = self._parse_si_number(raw["VOUT"]) if "VOUT" in raw else None
        fsw = self._parse_si_number(raw["FSW"]) if "FSW" in raw else None
        if not vout or vout <= 0 or not fsw or fsw <= 0:
            return None

        def g(key, default):
            v = self._parse_si_number(raw[key]) if key in raw else None
            return v if v is not None else default

        params = {
            "VOUT": vout,
            "FSW": fsw,
            "VF": g("VF", 0.45),
            "DMAX": g("DMAX", 0.95 if topology == "buck" else 0.9),
            "RON_HS": g("RON_HS", 0.1),
            "VRAMP": g("VRAMP", 1.0),
        }
        if topology == "flyback":
            n_ratio = self._parse_si_number(raw["N"]) if "N" in raw else None
            if not n_ratio or n_ratio <= 0:
                return None
            params["N"] = n_ratio
            params["VCLAMP"] = g("VCLAMP", 150.0)
        return params

    def _switcher_mode(self, component) -> str:
        """Model variant for a switcher: ``'avg'`` (averaged, for loop stability)
        or ``'cycle'`` (the default cycle-accurate 20.3 model).

        Read from ``Sim.Params`` ``MODE=`` (case-insensitive); anything other than
        ``avg`` -- including absent -- is ``cycle``.
        """
        raw = self._parse_sim_params(self._sim_props(component).get("params"))
        return "avg" if str(raw.get("MODE", "")).strip().lower() == "avg" else "cycle"

    def _averaged_params(self, component) -> Optional[dict]:
        """Error-amp params for the averaged model, or None if VREF is missing.

        VREF (the controller's internal reference the divider tap regulates to) is
        required -- the averaged loop closes through the user's real divider, so the
        output is set by VREF and that ratio, not by VOUT. GM (error-amp
        transconductance), CEA (compensation cap) and REA (finite-DC-gain resistor)
        default to a plain gm-C integrator and are the knobs the user tunes for
        phase margin.
        """
        raw = self._parse_sim_params(self._sim_props(component).get("params"))
        vref = self._parse_si_number(raw["VREF"]) if "VREF" in raw else None
        if not vref or vref <= 0:
            return None

        def g(key, default):
            v = self._parse_si_number(raw[key]) if key in raw else None
            return v if v is not None else default

        return {
            "VREF": vref,
            "GM": g("GM", 1e-3),
            "CEA": g("CEA", 1e-7),
            "REA": g("REA", 1e6),
        }

    def _add_buck(self, component, ref: str, value: str):
        self._add_switching_regulator(component, ref, value, "buck")

    def _add_boost(self, component, ref: str, value: str):
        self._add_switching_regulator(component, ref, value, "boost")

    def _add_flyback(self, component, ref: str, value: str):
        self._add_switching_regulator(component, ref, value, "flyback")

    def _add_switching_regulator(self, component, ref, value, topology):
        """Emit a behavioral buck/boost/flyback macromodel replacing only the IC.

        v1 is a **computed-duty open-loop** model (the closed loop was found to
        limit-cycle in voltage mode; open-loop is robust and steady-state-accurate):

          * a sawtooth PWM ramp at FSW,
          * a duty from VOUT/VIN with a first-order diode-drop correction (buck:
            ``D=(VOUT+VF)/(VIN+VF)``; boost: ``D=1-VIN/(VOUT+VF)``; flyback CCM:
            ``D=(VOUT+VF)/((VOUT+VF)+N*VIN)``) -- tracks line, not load,
          * a comparator gating an ``S`` switch (buck: high-side + emitted freewheel
            diode; boost/flyback: low-side, relying on the user's external rectifier
            diode). A flyback additionally gets a **drain avalanche clamp** diode
            (``BV=VCLAMP``, default 150 V): without it, transformer leakage dumped
            into the ideal open switch rings to kV and ~30x-inflates the timepoint
            count -- a real integrated flyback switch avalanches at its rating.

        The inductor/transformer, output cap and feedback divider stay the user's
        real parts. Emitted via ``raw_spice`` (behavioral sources + a switch +
        ``.model`` cards). Limitations (documented, not silently hidden): no active
        load-step recovery (open loop), non-synchronous (diode Vf, so sync-rectifier
        efficiency is underestimated), no current limit; the flyback duty is the CCM
        formula (light-load/DCM reads high) and clamp dissipation is modeled but not
        reported as loss. Boost and flyback need UIC to converge (boost: start
        V(out) at V(in); flyback: start V(out) at 0); buck converges without it.
        """
        term = self._switcher_terminals(component)
        if term is None:
            logger.warning(
                f"{topology} {ref}: could not resolve SW/VIN/GND terminals - skipping"
            )
            return
        params = self._switcher_params(component, value, topology)
        if params is None:
            need = "VOUT/FSW/N" if topology == "flyback" else "VOUT/FSW"
            example = (
                "fsw=100k vout=5 n=0.5"
                if topology == "flyback"
                else "fsw=500k vout=3.3"
            )
            logger.warning(
                f"{topology} {ref}: no {need} resolved - skipping "
                f'(set Sim.Params="{example}")'
            )
            return

        # Give cap-only unmodeled pins (SS/BYP/EN/PG...) a DC path so the op-point
        # solves. Done before the MODE branch so both models get the stubs.
        self._stub_unmodeled_pins(
            component,
            ref,
            {term["sw"], term["vin"], term["gnd"], term["fb"]},
            term["gnd"],
        )

        # MODE=avg selects the averaged (non-switching) model for loop-stability
        # analysis. v1 is voltage-mode buck only; boost falls back to the cycle
        # model with a clear warning (honest, not silent).
        if self._switcher_mode(component) == "avg":
            if topology == "buck":
                self._emit_averaged_buck(component, ref, term, params)
                return
            logger.warning(
                f"{topology} {ref}: MODE=avg is voltage-mode-buck-only in v1; "
                f"using the cycle-accurate model instead"
            )

        sw, vin, gnd = str(term["sw"]), str(term["vin"]), str(term["gnd"])
        n = self._fmt_num
        vout = n(params["VOUT"])
        vf = n(params["VF"])
        dmax = n(params["DMAX"])
        ron = n(params["RON_HS"])
        vramp = n(params["VRAMP"])
        per = 1.0 / params["FSW"]
        saw, dd, gg = f"{ref}_saw", f"{ref}_d", f"{ref}_g"

        if topology == "buck":
            duty = f"({vout}+{vf})/(V({vin})+{vf})"
        elif topology == "boost":
            duty = f"1 - V({vin})/({vout}+{vf})"
        else:  # flyback CCM: VOUT = VIN*N*D/(1-D), first-order diode correction
            duty = f"({vout}+{vf})/(({vout}+{vf}) + {n(params['N'])}*V({vin}))"

        lines = [
            f"V{ref}_saw {saw} {gnd} PULSE(0 {vramp} 0 "
            f"{per * 0.99:.6g} {per * 0.005:.6g} {per * 0.005:.6g} {per:.6g})",
            f"B{ref}_d {dd} {gnd} V = min(max({duty}, 0.0), {dmax})",
            f"B{ref}_g {gg} {gnd} V = V({dd}) > V({saw}) ? 5 : 0",
        ]
        if topology == "buck":
            lines += [
                f"S{ref}_hs {vin} {sw} {gg} {gnd} SW{ref}",
                f".model SW{ref} SW(Ron={ron} Roff=1e6 Vt=2.5 Vh=0.2)",
                f"D{ref}_fw {gnd} {sw} DFW{ref}",
                f".model DFW{ref} D(IS=1e-9 N=1.05 CJO=100p)",
            ]
        else:  # boost/flyback: low-side switch; the rectifier diode is the user's
            lines += [
                f"S{ref}_ls {sw} {gnd} {gg} {gnd} SW{ref}",
                f".model SW{ref} SW(Ron={ron} Roff=1e6 Vt=2.5 Vh=0.2)",
            ]
        if topology == "flyback":
            # Drain avalanche clamp: bounds the leakage spike at the IC's rated
            # breakdown, exactly as an integrated flyback switch does.
            vclamp = n(params["VCLAMP"])
            lines += [
                f"D{ref}_cl {gnd} {sw} DCL{ref}",
                f".model DCL{ref} D(IS=1e-12 BV={vclamp} IBV=1m)",
            ]

        self.spice_circuit.raw_spice += "\n" + "\n".join(lines)
        name = f"{topology}_openloop(vout={vout})"
        if topology == "flyback":
            name = f"flyback_openloop(vout={vout}, n={n(params['N'])})"
        self.model_provenance[ref] = ResolvedModel(ref, topology, "sim_params", name)
        extra = (
            f"; drain clamp at BV={n(params['VCLAMP'])} V (set vclamp= to the IC's "
            f"rating); CCM duty formula (light-load/DCM reads high)"
            if topology == "flyback"
            else ""
        )
        logger.info(
            f"{ref}: {topology} behavioral macromodel (open-loop, vout={vout}, "
            f"fsw={self._fmt_hz(params['FSW'])}); active load-step recovery is not "
            f"modeled (open loop){extra}"
        )

    def _emit_averaged_buck(self, component, ref, term, params):
        """Emit the averaged (non-switching) voltage-mode buck model (Stage 20.5).

        Replaces the sawtooth/comparator/switch/diode of the cycle model with a
        continuous averaged PWM switch and a linear gm-C error amplifier, so ``.ac``
        linearizes it and produces a real loop gain (crossover / phase margin) --
        the question the cycle-accurate model structurally cannot answer::

            B<ref>_ea  <gnd> <ref>_c  I = GM*(VREF - V(<fb>))   ; error amp (integrator)
            C<ref>_ea  <ref>_c <gnd> CEA                         ; compensation cap
            R<ref>_ea  <ref>_c <gnd> REA                         ; finite DC gain
            B<ref>_sw  <ref>_swi <gnd> V = V(<ref>_c) * V(<vin>) ; averaged switch (d=V(c))
            R<ref>_sw  <ref>_swi <sw> RON_HS                     ; conduction loss

        The control voltage V(c) *is* the duty (in 0..1 at the operating point of a
        well-specified buck). The multiplicative averaged switch linearizes to a
        d->vout gain of ~VIN around the DC operating point, so the user's real L /
        Cout / divider supply the plant dynamics and the loop closes through the
        divider tap. Negative feedback: Vout low -> V(fb) low -> error>0 -> V(c) up
        -> duty up -> Vout up.

        No duty clamp is emitted: it is irrelevant to the small-signal ``.ac`` this
        model exists for, and a hard ``min/max`` saturation zeroes the Jacobian and
        breaks DC operating-point convergence (the clamp hides the feedback path
        from Newton during startup). Validity (documented, logged): CCM voltage-mode
        only; results above ~FSW/2 are meaningless (averaging breaks); no current
        limit.
        """
        avg = self._averaged_params(component)
        if avg is None:
            logger.warning(
                f"buck {ref}: MODE=avg needs Sim.Params VREF (the reference the "
                f'divider tap regulates to), e.g. "vref=0.8" - skipping'
            )
            return
        fb = term.get("fb")
        if fb is None:
            logger.warning(
                f"buck {ref}: MODE=avg needs a connected FB pin (the divider tap) "
                f"to close the loop - skipping"
            )
            return

        sw, vin, gnd = str(term["sw"]), str(term["vin"]), str(term["gnd"])
        fb = str(fb)
        n = self._fmt_num
        vref, gm, cea, rea = (
            n(avg["VREF"]),
            n(avg["GM"]),
            n(avg["CEA"]),
            n(avg["REA"]),
        )
        ron = n(params["RON_HS"])
        cc, swi = f"{ref}_c", f"{ref}_swi"

        lines = [
            f"B{ref}_ea {gnd} {cc} I = {gm}*({vref} - V({fb}))",
            f"C{ref}_ea {cc} {gnd} {cea}",
            f"R{ref}_ea {cc} {gnd} {rea}",
            f"B{ref}_sw {swi} {gnd} V = V({cc}) * V({vin})",
            f"R{ref}_sw {swi} {sw} {ron}",
        ]
        self.spice_circuit.raw_spice += "\n" + "\n".join(lines)
        self.model_provenance[ref] = ResolvedModel(
            ref, "buck", "sim_params", f"buck_averaged(vref={vref})"
        )
        fsw = params["FSW"]
        logger.info(
            f"{ref}: buck averaged macromodel (voltage-mode, CCM, vref={vref}, "
            f"gm={gm}, cea={cea}); for loop-gain/phase-margin via .ac. Results above "
            f"~{self._fmt_hz(fsw / 2)} (FSW/2) are not physical (averaging breaks)."
        )

    @staticmethod
    def _parse_frequency(value) -> Optional[float]:
        """Parse a GBW/frequency string ('1.4G', '10MEG', '1k', '5e5', '2MHz') to Hz.

        SI suffixes G/MEG/M/k (``M`` means mega here -- milli-Hz is meaningless for a
        GBW), optional trailing ``Hz``. Returns None if unparseable.
        """
        if value is None:
            return None
        s = str(value).strip().lower().replace(" ", "")
        if s.endswith("hz"):
            s = s[:-2]
        if not s:
            return None
        mult = 1.0
        for suf, m in (("meg", 1e6), ("g", 1e9), ("m", 1e6), ("k", 1e3)):
            if s.endswith(suf):
                mult = m
                s = s[: -len(suf)]
                break
        try:
            return float(s) * mult
        except ValueError:
            return None

    @staticmethod
    def _fmt_hz(hz: float) -> str:
        """Compact human label for a frequency ('1.4G', '10M', '5k', '200')."""
        for suf, scale in (("G", 1e9), ("M", 1e6), ("k", 1e3)):
            if hz >= scale:
                return f"{hz / scale:g}{suf}"
        return f"{hz:g}"

    def _named_terminal_nodes(self, component) -> dict:
        """``{uppercased pin name: spice node}`` for a component's connected pins.

        Transistor terminals must be mapped by pin *name* (C/B/E, D/G/S), not pin
        number: KiCad symbols number them inconsistently (2N7000 is pin1=S,2=G,3=D;
        BC547 is 1=C,2=B,3=E), so a positional mapping silently swaps
        drain/source (or collector/emitter) for many real parts.
        """
        out = {}
        pin_map = getattr(component, "_pins", None)
        if isinstance(pin_map, dict):
            for pin in pin_map.values():
                net = getattr(pin, "net", None)
                name = (getattr(pin, "name", "") or "").strip().upper()
                if net is not None and name:
                    out[name] = self.node_map.get(net.name, net.name)
        return out

    def _add_bjt_transistor(self, component, ref: str, value: str):
        """Add BJT transistor to SPICE circuit.

        Terminals are resolved by pin name (C/B/E); falls back to pin-number order
        only when the symbol doesn't name all three (rare).
        """
        named = self._named_terminal_nodes(component)
        if all(k in named for k in ("C", "B", "E")):
            c_node, b_node, e_node = named["C"], named["B"], named["E"]
        else:
            nodes = self._get_component_nodes(component)
            if len(nodes) < 3:
                logger.warning(
                    f"BJT {ref} needs 3 connections (C,B,E), got {len(nodes)}"
                )
                return
            c_node, b_node, e_node = nodes[0], nodes[1], nodes[2]

        # Determine model (NPN/PNP) from value keyword or symbol polarity, applying
        # any Sim.Params override.
        model_name = self._resolve_device_model(component, ref) or "DefaultNPN"

        self.spice_circuit.Q(ref, c_node, b_node, e_node, model=model_name)
        logger.debug(
            f"Added BJT {ref}: C={c_node}, B={b_node}, E={e_node}, model={model_name}"
        )

    def _add_mosfet(self, component, ref: str, value: str):
        """Add MOSFET to SPICE circuit.

        Terminals are resolved by pin name (D/G/S, plus an optional bulk pin B);
        falls back to pin-number order only when the symbol doesn't name D/G/S.
        Bulk defaults to the source when the symbol has no separate bulk pin
        (3-terminal parts like 2N7000/BSS84).
        """
        named = self._named_terminal_nodes(component)
        if all(k in named for k in ("D", "G", "S")):
            d_node, g_node, s_node = named["D"], named["G"], named["S"]
            b_node = named.get("B", s_node)
        else:
            nodes = self._get_component_nodes(component)
            if len(nodes) < 3:
                logger.warning(
                    f"MOSFET {ref} needs at least 3 connections (D,G,S), got {len(nodes)}"
                )
                return
            d_node, g_node, s_node = nodes[0], nodes[1], nodes[2]
            b_node = nodes[3] if len(nodes) >= 4 else nodes[2]

        # Determine model (NMOS/PMOS) from value keyword or symbol polarity, applying
        # any Sim.Params override.
        model_name = self._resolve_device_model(component, ref) or "DefaultNMOS"

        self.spice_circuit.M(ref, d_node, g_node, s_node, b_node, model=model_name)
        logger.debug(
            f"Added MOSFET {ref}: D={d_node}, G={g_node}, S={s_node}, B={b_node}, "
            f"model={model_name}"
        )

    def _add_voltage_source(self, component, ref: str, value: str):
        """Add voltage source to SPICE circuit.

        The emitted SPICE spec depends on the KiCad symbol:

        * ``VDC`` -> a DC value (from ``value``, default 5 V).
        * ``VAC`` -> ``DC 0 AC <mag>`` (small-signal only; ``value`` is the AC mag).
        * ``VSIN`` -> ``DC <off> AC <acmag> SIN(<off> <ampl> <freq> <td> <theta>)``
          -- both AC-analysis magnitude *and* a transient sinusoid, so one source
          works for both `.ac` and `.tran`. ``value`` sets ampl+acmag by default.
        * ``VPULSE`` -> ``PULSE(<v1> <v2> <td> <tr> <tf> <pw> <per>)``.
        * ``VPWL`` -> ``PWL(<t1> <v1> <t2> <v2> ...)`` (from a ``points`` field).

        Waveform parameters are read from the component's extra fields (any kwarg
        passed to ``Component`` lands in ``_extra_fields``), e.g.
        ``Component(symbol="Simulation_SPICE:VSIN", amplitude="1", frequency="1k")``.
        Numeric values keep their SI suffix (``1k``/``1m``/``1u``/``1n``) -- ngspice
        parses those directly.
        """
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(
                f"Voltage source {ref} needs 2 connections, got {len(nodes)}"
            )
            return

        # Add to list of voltage sources for tracking
        self.voltage_sources.append(ref)
        # Mark this source's nets so the net-name heuristic won't double-drive them.
        self.driven_nets.update(self._component_net_names(component))

        symbol = (getattr(component, "symbol", "") or "").upper()
        params = self._source_params(component)
        spec = self._voltage_source_spec(symbol, value, params)

        # nodes[] is in pin-number order, so nodes[0] is pin 1 (KiCad Sim.Pins
        # "1=+") and nodes[1] is pin 2 ("2=-"): V(name, +, -, spec).
        self.spice_circuit.V(ref, nodes[0], nodes[1], spec)
        logger.debug(
            f"Added voltage source {ref}: {nodes[0]}(+) -> {nodes[1]}(-) = {spec}"
        )

    def _source_params(self, component) -> dict:
        """Lowercased waveform-param map for a source (empty if none).

        Merges KiCad ``Sim.Params`` (as a base) with the component's own extra
        fields, where an explicit extra field wins over a ``Sim.Params`` value.
        The ``Sim.*`` fields themselves are dropped so they don't masquerade as
        waveform params.
        """
        extra = getattr(component, "_extra_fields", None)
        if not isinstance(extra, dict):
            return {}
        merged = {
            k.lower(): v
            for k, v in self._parse_sim_params(
                self._sim_props(component).get("params")
            ).items()
        }
        for k, v in extra.items():
            low = str(k).lower()
            if low.startswith("sim.") or low.startswith("sim_"):
                continue
            merged[low] = v
        return merged

    @staticmethod
    def _wave_num(value, default: str) -> str:
        """Normalize a waveform number, keeping its SI suffix for ngspice.

        Strips a trailing unit (V/A/Hz/s/F/H) so ``"1kHz"`` -> ``"1k"`` and
        ``"5V"`` -> ``"5"`` while leaving the SI prefix (k/m/u/n/p) intact.
        Returns ``default`` when ``value`` is None/empty.
        """
        if value is None:
            return default
        s = str(value).strip()
        if not s:
            return default
        for unit in ("hz", "v", "a", "s", "f", "h"):
            if len(s) > len(unit) and s.lower().endswith(unit):
                s = s[: -len(unit)]
                break
        return s

    def _pick(self, params: dict, keys, default: str) -> str:
        """First present param among ``keys`` (normalized), else ``default``."""
        for k in keys:
            if k in params and params[k] is not None and str(params[k]).strip():
                return self._wave_num(params[k], default)
        return default

    def _voltage_source_spec(self, symbol: str, value, params: dict):
        """Build the SPICE source spec (string or float) from symbol + params."""
        if "VPULSE" in symbol:
            v1 = self._pick(params, ("v1", "initial", "low"), "0")
            v2 = self._pick(
                params,
                ("v2", "pulsed", "high", "amplitude"),
                self._wave_num(value, "1"),
            )
            td = self._pick(params, ("td", "delay"), "0")
            tr = self._pick(params, ("tr", "rise"), "1n")
            tf = self._pick(params, ("tf", "fall"), "1n")
            pw = self._pick(params, ("pw", "width"), "0.5m")
            per = self._pick(params, ("per", "period"), "1m")
            return f"PULSE({v1} {v2} {td} {tr} {tf} {pw} {per})"

        if "VPWL" in symbol:
            pts = self._pwl_points(params)
            if pts:
                return f"PWL({pts})"
            # No points given -> degrade to a DC source at `value` (or 0).
            return self._convert_value_to_spice(value or "0V", "V")

        if "VSIN" in symbol:
            base = self._wave_num(value, "1")  # value sets ampl + AC mag by default
            offset = self._pick(params, ("offset", "dc", "voffset"), "0")
            ampl = self._pick(params, ("amplitude", "ampl", "amp"), base)
            freq = self._pick(params, ("frequency", "freq", "f"), "1k")
            td = self._pick(params, ("td", "delay"), "0")
            theta = self._pick(params, ("theta", "damping"), "0")
            ac_mag = self._pick(params, ("ac", "ac_mag", "acmag"), base)
            return f"DC {offset} AC {ac_mag} SIN({offset} {ampl} {freq} {td} {theta})"

        if "VAC" in symbol:
            ac_mag = self._convert_value_to_spice(value, "V") if value else 1.0
            return f"DC 0 AC {ac_mag}"

        # VDC / default: a plain DC value.
        return self._convert_value_to_spice(value or "5V", "V")

    def _pwl_points(self, params: dict) -> str:
        """Render VPWL points ('t1 v1 t2 v2 ...') from a ``points`` field.

        Accepts a list/tuple of (t, v) pairs, a flat list, or a whitespace/
        comma-separated string. Returns '' if no usable points are present.
        """
        pts = params.get("points")
        if pts is None:
            return ""
        if isinstance(pts, str):
            toks = [t for t in pts.replace(",", " ").split() if t]
            return " ".join(self._wave_num(t, "0") for t in toks)
        if isinstance(pts, (list, tuple)):
            flat = []
            for item in pts:
                if isinstance(item, (list, tuple)):
                    flat.extend(item)
                else:
                    flat.append(item)
            return " ".join(self._wave_num(t, "0") for t in flat)
        return ""

    def _add_current_source(self, component, ref: str, value: str):
        """Add current source to SPICE circuit.

        Symbol-aware, mirroring ``_add_voltage_source``: ``ISIN`` carries an AC
        magnitude (for ``.ac``) plus a transient sinusoid, ``IPULSE``/``IPWL`` get
        their waveforms, and ``IDC``/default stays a plain DC current. Without this
        an ``ISIN`` source injected only DC, so AC analysis saw zero drive.
        """
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(
                f"Current source {ref} needs 2 connections, got {len(nodes)}"
            )
            return

        # Mark this source's nets so the net-name heuristic won't double-drive them.
        self.driven_nets.update(self._component_net_names(component))

        symbol = (getattr(component, "symbol", "") or "").upper()
        params = self._source_params(component)
        spec = self._current_source_spec(symbol, value, params)

        # nodes[] is pin-number ordered (pin 1 = +, pin 2 = -); ngspice current
        # flows from the + node, through the source, to the - node.
        self.spice_circuit.I(ref, nodes[0], nodes[1], spec)
        logger.debug(
            f"Added current source {ref}: {nodes[0]}(+) -> {nodes[1]}(-) = {spec}"
        )

    def _current_source_spec(self, symbol: str, value, params: dict):
        """Build the SPICE current-source spec (string or float) from symbol+params.

        Current-source analogue of ``_voltage_source_spec`` (units 'A'):

        * ``ISIN``  -> ``DC <off> AC <acmag> SIN(<off> <ampl> <freq> <td> <theta>)``
          -- one source serves both ``.ac`` (via AC magnitude) and ``.tran``.
          ``value`` sets ampl+acmag by default.
        * ``IPULSE`` -> ``PULSE(<i1> <i2> <td> <tr> <tf> <pw> <per>)``.
        * ``IPWL``  -> ``PWL(<t1> <i1> ...)`` (from a ``points`` field).
        * ``IDC`` / default -> a plain DC current (from ``value``, default 1 mA).
        """
        if "IPULSE" in symbol:
            i1 = self._pick(params, ("i1", "initial", "low"), "0")
            i2 = self._pick(
                params,
                ("i2", "pulsed", "high", "amplitude"),
                self._wave_num(value, "1"),
            )
            td = self._pick(params, ("td", "delay"), "0")
            tr = self._pick(params, ("tr", "rise"), "1n")
            tf = self._pick(params, ("tf", "fall"), "1n")
            pw = self._pick(params, ("pw", "width"), "0.5m")
            per = self._pick(params, ("per", "period"), "1m")
            return f"PULSE({i1} {i2} {td} {tr} {tf} {pw} {per})"

        if "IPWL" in symbol:
            pts = self._pwl_points(params)
            if pts:
                return f"PWL({pts})"
            return self._convert_value_to_spice(value or "0A", "I")

        if "ISIN" in symbol:
            base = self._wave_num(value, "1")  # value sets ampl + AC mag by default
            offset = self._pick(params, ("offset", "dc", "ioffset"), "0")
            ampl = self._pick(params, ("amplitude", "ampl", "amp"), base)
            freq = self._pick(params, ("frequency", "freq", "f"), "1k")
            td = self._pick(params, ("td", "delay"), "0")
            theta = self._pick(params, ("theta", "damping"), "0")
            ac_mag = self._pick(params, ("ac", "ac_mag", "acmag"), base)
            return f"DC {offset} AC {ac_mag} SIN({offset} {ampl} {freq} {td} {theta})"

        # IDC / default: a plain DC current.
        return self._convert_value_to_spice(value or "1mA", "I")

    @staticmethod
    def _pin_sort_key(num):
        """Sort key that orders pin numbers numerically ('2' < '10') when possible."""
        s = str(num)
        return (0, int(s)) if s.isdigit() else (1, s)

    def _component_net_names(self, component) -> set:
        """Original (unmapped) net names connected to a component's pins.

        Best effort: only available for live Component objects that carry a
        ``_pins`` map. Returns an empty set for dict/JSON-shaped components.
        """
        names = set()
        pin_map = getattr(component, "_pins", None)
        if isinstance(pin_map, dict):
            for pin in pin_map.values():
                net = getattr(pin, "net", None)
                name = getattr(net, "name", None)
                if name:
                    names.add(name)
        return names

    def _get_component_nodes(self, component) -> List[str]:
        """Get the SPICE nodes connected to a component, in pin-number order.

        Pin order is significant: a voltage/current source's pin 1 is + and pin 2
        is - (KiCad ``Sim.Pins "1=+ 2=-"``), and a transistor's pins are C/B/E or
        D/G/S. A live Component exposes a ``{pin_num: Pin}`` map, so we read the
        node for each pin in ascending pin-number order. Unlike the legacy net
        scan this does *not* dedupe or alphabetically sort, so polarity and
        terminal order are preserved.

        Falls back to the legacy net scan for dict/JSON-shaped circuits whose
        components have no live ``_pins`` map.
        """
        pin_map = getattr(component, "_pins", None)
        if isinstance(pin_map, dict) and pin_map:
            ordered = []
            for _num, pin in sorted(
                pin_map.items(), key=lambda kv: self._pin_sort_key(kv[0])
            ):
                net = getattr(pin, "net", None)
                net_name = getattr(net, "name", None)
                if net_name is None:
                    continue  # unconnected pin
                ordered.append(self.node_map.get(net_name, net_name))
            if ordered:
                return ordered
            # else: fall through to the net scan (e.g. pins present but netless)

        return self._get_component_nodes_by_net_scan(component)

    def _get_component_nodes_by_net_scan(self, component) -> List[str]:
        """Legacy fallback: recover a component's nodes by scanning nets.

        Used for dict/JSON-shaped circuits without live Pin objects. Nodes are
        alphabetically sorted (pin order is not recoverable here), which is fine
        for symmetric R/C/L but does not guarantee polarity for sources.
        """
        nodes = []

        # Get component connections from the circuit
        # circuit.nets is a dict, iterate over values
        if hasattr(self.circuit.nets, "values"):
            nets_to_check = self.circuit.nets.values()
        else:
            nets_to_check = self.circuit.nets

        for net in nets_to_check:
            net_name = getattr(net, "name", str(net))

            # Check if this net has pins connected to our component
            if hasattr(net, "pins"):
                for pin in net.pins:
                    # Each pin has a reference back to its component
                    # The pin string format is like "Pin(~ of R1, net=VIN)"
                    pin_str = str(pin)
                    component_ref = getattr(component, "ref", "")

                    # Check if this pin belongs to our component
                    if f" of {component_ref}," in pin_str:
                        # Map to SPICE node name
                        spice_node = self.node_map.get(net_name, net_name)
                        if spice_node not in nodes:
                            nodes.append(spice_node)
                        break

        # Sort nodes to ensure consistent pin ordering (important for SPICE)
        # Convert all to strings first to avoid type comparison issues
        nodes.sort(key=str)

        # If we didn't find connections, log for debugging
        if not nodes:
            logger.warning(
                f"No connections found for component {getattr(component, 'ref', 'unknown')}"
            )

        return nodes

    def _convert_value_to_spice(self, value: str, component_type: str) -> float:
        """Convert circuit-synth component value to SPICE format."""
        if not value:
            # Default values
            defaults = {"R": 1000, "C": 1e-6, "L": 1e-3}
            return defaults.get(component_type, 1.0)

        # Parse value string (e.g., "10k", "100nF", "1mH")
        value = str(value).strip().replace(" ", "")

        # Extract numeric part and suffix
        match = re.match(r"^([0-9.]+)([a-zA-Z]*)$", value)
        if not match:
            logger.warning(f"Could not parse value '{value}', using 1.0")
            return 1.0

        numeric_part = float(match.group(1))
        suffix = match.group(2).lower()

        # Convert suffixes to multipliers
        multipliers = {
            # Resistance
            "r": 1,
            "ohm": 1,
            "ohms": 1,
            "k": 1e3,
            "kohm": 1e3,
            "kohms": 1e3,
            "m": 1e6,
            "meg": 1e6,
            "mohm": 1e6,
            "mohms": 1e6,
            # Capacitance
            "f": 1,
            "pf": 1e-12,
            "nf": 1e-9,
            "uf": 1e-6,
            "mf": 1e-3,
            "p": 1e-12,
            "n": 1e-9,
            "u": 1e-6,
            # Inductance
            "h": 1,
            "nh": 1e-9,
            "uh": 1e-6,
            "mh": 1e-3,
            # Voltage
            "v": 1,
            "mv": 1e-3,
            "kv": 1e3,
            # Current
            "a": 1,
            "ma": 1e-3,
            "ua": 1e-6,
            "na": 1e-9,
        }

        multiplier = multipliers.get(suffix, 1.0)
        return numeric_part * multiplier

    def _add_power_sources(self):
        """Add power sources needed for simulation."""
        # Check if we need to add power sources based on net names
        power_nets = []

        # Handle both dict and list formats for nets
        if hasattr(self.circuit.nets, "values"):
            nets_to_process = self.circuit.nets.values()
        elif hasattr(self.circuit.nets, "__iter__"):
            nets_to_process = self.circuit.nets
        else:
            return

        for net in nets_to_process:
            orig_name = getattr(net, "name", str(net))
            # An explicit source component already drives this net; don't add a
            # second heuristic supply on top of it (that would over-constrain the
            # node / fight the real source).
            if orig_name in self.driven_nets:
                continue
            voltage = self._heuristic_source_voltage(orig_name)
            if voltage is not None:
                power_nets.append((orig_name, voltage))

        # Add voltage sources
        for i, (net_name, voltage) in enumerate(power_nets):
            source_name = f"V_supply_{i+1}"
            spice_node = self.node_map.get(net_name, net_name)
            self.spice_circuit.V(
                source_name, spice_node, self.spice_circuit.gnd, voltage @ u_V
            )
            logger.info(
                f"Net '{net_name}': injecting heuristic {voltage} V supply "
                f"{source_name} from its NAME. If unintended, rename the net or "
                f"drive it with an explicit Simulation_SPICE:VDC (explicit "
                f"sources suppress this)."
            )

    def _extract_voltage_from_net_name(self, net_name: str) -> Optional[float]:
        """Extract voltage value from net name (e.g., '+5V' -> 5.0)."""
        upper = net_name.upper()

        # KiCad "decimal-in-V" notation where the V is the decimal point:
        # 3V3 -> 3.3, 1V8 -> 1.8. Checked first so "5V" (no trailing digit)
        # still falls through to the plain patterns below (-> 5.0, not 5.x).
        m = re.search(r"\+?([0-9]+)V([0-9]+)\b", upper)
        if m:
            try:
                return float(f"{m.group(1)}.{m.group(2)}")
            except ValueError:
                pass

        # Look for voltage patterns
        patterns = [
            r"\+?([0-9.]+)V",  # +5V, 3.3V, etc.
            r"VCC_?([0-9.]+)",  # VCC_5, VCC5, etc.
            r"VDD_?([0-9.]+)",  # VDD_3, VDD3, etc.
        ]

        for pattern in patterns:
            match = re.search(pattern, upper)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def _heuristic_source_voltage(self, net_name: str) -> Optional[float]:
        """Voltage the net-name heuristic would assign to this net, or None.

        Single source of truth shared by ``_add_power_sources`` (which actually
        injects the supply) and ``validate`` (which must know whether a
        single-connection net will nonetheless be driven). A bare ``VCC`` with no
        embedded number is *not* driven (no voltage to assign); ``VIN``/``VSUPPLY``
        default to 5 V.

        Rail keywords are matched as **whole tokens**, not substrings, so an
        intermediate net like ``VINT_RAW`` (tokens ``{VINT, RAW}``) is NOT treated
        as a ``VIN`` rail -- that substring trap injected a phantom 5 V supply and
        clamped a 32.5 V boost output (bug #13). Known accepted limitation: a name
        like ``MAIN_VIN_SENSE`` still matches on the whole token ``VIN`` -- token
        matching cannot tell it is a sense line; the INFO log in
        ``_add_power_sources`` makes any such injection visible.
        """
        upper = net_name.upper()
        tokens = {t for t in re.split(r"[^A-Z0-9+]+", upper) if t}
        if tokens & {"VCC", "VDD", "V+"}:
            return self._extract_voltage_from_net_name(upper)
        if tokens & {"VIN", "VSUPPLY"}:
            return self._extract_voltage_from_net_name(upper) or 5.0
        if any(re.fullmatch(r"\+?[0-9]+V[0-9]*", t) for t in tokens):
            return self._extract_voltage_from_net_name(upper)
        return None

    # ------------------------------------------------------------------ #
    # Validation                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _attr(obj, name, default=None):
        """Read an attribute from either a live object or a dict-shaped one."""
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _iter_components(self):
        comps = getattr(self.circuit, "components", None)
        if comps is None:
            return []
        return list(comps.values()) if hasattr(comps, "values") else list(comps)

    def _iter_nets(self):
        nets = getattr(self.circuit, "nets", None)
        if nets is None:
            return []
        return list(nets.values()) if hasattr(nets, "values") else list(nets)

    @staticmethod
    def _is_ground_name(name: str) -> bool:
        return str(name).upper() in ("GND", "GROUND", "VSS", "0")

    @staticmethod
    def _net_pin_count(net) -> Optional[int]:
        """Number of pins on a net, or None if the net can't report it."""
        pins = getattr(net, "pins", None)
        if pins is None:
            return None
        try:
            return len(pins)
        except TypeError:
            return None

    def _connected_pin_count(self, component) -> Optional[int]:
        """Number of a component's pins attached to a net, or None if unknown."""
        pin_map = getattr(component, "_pins", None)
        if not isinstance(pin_map, dict):
            return None
        return sum(
            1 for pin in pin_map.values() if getattr(pin, "net", None) is not None
        )

    def _net_live_pin_count(self, net, excluded_refs) -> Optional[int]:
        """Pins on a net whose owning component isn't excluded, or None if unknown.

        A ``Sim.Enable=0`` part's pins don't hold a net up, so a net left with
        fewer than two *live* pins is still floating.
        """
        pins = getattr(net, "pins", None)
        if pins is None:
            return None
        try:
            count = 0
            for pin in pins:
                comp = getattr(pin, "_component", None)
                cref = getattr(comp, "ref", None)
                if cref is not None and cref in excluded_refs:
                    continue
                count += 1
            return count
        except TypeError:
            return None

    def _all_driven_net_names(self) -> set:
        """Nets that will carry a source: explicit source components + heuristic rails.

        An excluded (``Sim.Enable=0``) source doesn't drive anything, so it isn't
        counted as excitation.
        """
        driven = set()
        for component in self._iter_components():
            if self._sim_excluded(component):
                continue
            if self._kind(component) in (
                "voltage_source",
                "current_source",
            ):
                driven |= self._component_net_names(component)
        for net in self._iter_nets():
            name = self._attr(net, "name", None) or str(net)
            if self._heuristic_source_voltage(name) is not None:
                driven.add(name)
        return driven

    def validate(self) -> None:
        """Check the circuit is safe to simulate; raise with every problem found.

        Catches the failure modes that otherwise produce a wrong-but-"successful"
        simulation or an opaque ngspice error:

        * a component whose symbol has no SPICE mapping (was silently skipped);
        * a net with a single connection that no source drives (floating node ->
          singular matrix);
        * no source at all (nothing to excite the circuit);
        * an op-amp with fewer than three connected pins (needs in+, in-, out).

        Checks that need data a dict/JSON-shaped circuit can't provide (live pin
        maps, net pin counts) are skipped for those inputs rather than raising
        false positives.
        """
        problems = []

        # Parts opted out via Sim.Enable=0 are ignored by every check below and
        # don't count toward net connectivity.
        excluded_refs = set()
        for component in self._iter_components():
            if self._sim_excluded(component):
                excluded_refs.add(self._attr(component, "ref", None) or "?")

        # 1. Every component must map to a known SPICE primitive (Sim.Device wins).
        #    Parts carrying an external model (Sim.Library) are exempt -- the
        #    external .subckt/.model defines their behaviour (checked in #6).
        for component in self._iter_components():
            if self._sim_excluded(component) or self._has_external_lib(component):
                continue
            symbol = self._attr(component, "symbol", "")
            ref = self._attr(component, "ref", None) or "?"
            if self._kind(component) is None:
                device = self._sim_props(component).get("device", None)
                if device:
                    problems.append(
                        f"{ref}: Sim.Device '{device}' is not a supported device "
                        f"(known: {', '.join(sorted(self._SIM_DEVICE_KINDS))})"
                    )
                else:
                    problems.append(
                        f"{ref}: unrecognized symbol '{symbol}' has no SPICE mapping "
                        f"(would be silently skipped)"
                    )

        driven = self._all_driven_net_names()

        # 2. There must be some excitation.
        if not driven:
            problems.append(
                "no voltage or current source found (declare a "
                "Simulation_SPICE:VDC/VAC, or use a rail-named net); simulation "
                "would have no excitation"
            )

        # 3. No floating nodes: every net needs >=2 connections, ground, or a source.
        for net in self._iter_nets():
            name = self._attr(net, "name", None) or str(net)
            if self._is_ground_name(name) or name in driven:
                continue
            if excluded_refs:
                # A net whose *only* pins belong to Sim.Enable=0 parts never enters
                # the SPICE netlist, so it isn't floating -- it's absent. Drop it
                # instead of flagging (report F6): otherwise a bias/output rail on a
                # sim-disabled sensor/connector aborts the whole simulation.
                live = self._net_live_pin_count(net, excluded_refs)
                total = self._net_pin_count(net)
                if live is not None and total is not None and live == 0 and total > 0:
                    logger.debug(
                        f"net '{name}' is private to Sim.Enable=0 part(s) "
                        f"({total} pin(s), all excluded); dropped from validation "
                        f"(not floating)"
                    )
                    continue
                count = live
            else:
                count = self._net_pin_count(net)
            if count is None:
                continue  # can't tell (dict/JSON net) -> don't block
            if count < 2:
                problems.append(
                    f"net '{name}' has {count} connection(s); needs >=2 or a source "
                    f"(floating node)"
                )

        # 4. Op-amps need at least their three signal pins connected.
        for component in self._iter_components():
            if self._sim_excluded(component):
                continue
            if self._kind(component) != "opamp":
                continue
            count = self._connected_pin_count(component)
            if count is None:
                continue
            if count < 3:
                ref = self._attr(component, "ref", None) or "?"
                problems.append(
                    f"{ref}: op-amp needs >=3 connected pins (in+, in-, out), "
                    f"found {count}"
                )

        # 4b. LDOs need their three terminals (in, out, gnd) connected, and a VOUT
        #     that resolves -- a regulator's output voltage cannot be guessed.
        for component in self._iter_components():
            if self._sim_excluded(component):
                continue
            if self._kind(component) != "ldo":
                continue
            ref = self._attr(component, "ref", None) or "?"
            count = self._connected_pin_count(component)
            if count is not None and count < 3:
                problems.append(
                    f"{ref}: LDO needs >=3 connected pins (in, out, gnd), "
                    f"found {count}"
                )
            params, _tier = self._ldo_params(
                component, self._attr(component, "value", None)
            )
            if params is None:
                problems.append(
                    f"{ref}: LDO has no resolvable output voltage; set "
                    f'Sim.Params="vout=3.3 vdrop=0.3" (or name a ModelLibrary '
                    f"entry with a VOUT param via value=)"
                )

        # 4c. Switching regulators: explicit topology + resolvable terminals/params.
        for component in self._iter_components():
            if self._sim_excluded(component):
                continue
            kind = self._kind(component)
            ref = self._attr(component, "ref", None) or "?"
            if kind == "switcher_unknown":
                problems.append(
                    f"{ref}: switching-regulator topology is ambiguous; set "
                    f"Sim.Device=BUCK or Sim.Device=BOOST"
                )
                continue
            if kind not in ("buck", "boost", "flyback"):
                continue
            if (
                getattr(component, "_pins", None) is not None
                and self._switcher_terminals(component) is None
            ):
                problems.append(
                    f"{ref}: {kind} needs connected SW, VIN and GND pins "
                    f"(resolved by pin name)"
                )
            if (
                self._switcher_params(
                    component, self._attr(component, "value", None), kind
                )
                is None
            ):
                if kind == "flyback":
                    problems.append(
                        f"{ref}: flyback needs Sim.Params with VOUT, FSW and N "
                        f"(the transformer turns ratio Ns/Np), e.g. "
                        f'Sim.Params="fsw=100k vout=5 n=0.5"'
                    )
                else:
                    problems.append(
                        f"{ref}: {kind} needs Sim.Params with VOUT and FSW, e.g. "
                        f'Sim.Params="fsw=500k vout=3.3"'
                    )

        # 4d. Transformers: all four winding ends connected + resolvable params.
        for component in self._iter_components():
            if self._sim_excluded(component):
                continue
            if self._kind(component) != "transformer":
                continue
            ref = self._attr(component, "ref", None) or "?"
            if (
                getattr(component, "_pins", None) is not None
                and self._transformer_terminals(component) is None
            ):
                problems.append(
                    f"{ref}: transformer needs all of AA/AB/SA/SB pins connected "
                    f"(no half-wound transformers)"
                )
            params = self._transformer_params(component)
            if params is None:
                problems.append(
                    f"{ref}: transformer needs Sim.Params with LP and N (or LS), "
                    f'e.g. Sim.Params="lp=100u n=0.5"'
                )
            elif params["K"] is None:
                problems.append(f"{ref}: transformer coupling k must be in (0, 1]")

        # 5. Every diode/BJT/MOSFET must reference a model that resolves to a
        #    built-in generic (otherwise ngspice errors on an undefined model).
        for component in self._iter_components():
            if self._sim_excluded(component) or self._has_external_lib(component):
                continue
            if self._store_lib_for(component):
                continue  # resolved from the local MPN store (tier vendor_lib)
            model = self._device_model_name(component)
            if model is None:
                continue
            kind = self._kind(component)
            spec, _tier = self._lookup_model_spec(model, kind)
            if spec is not None:
                continue
            # An unresolved base carrying Sim.Params degrades to the kind's generic
            # + overrides (see _resolve_device_model), so it is simulatable -- not an
            # error. With no overrides it stays a hard error below.
            overrides = self._parse_sim_params(self._sim_props(component).get("params"))
            if overrides and kind in self._KIND_GENERIC:
                continue
            ref = self._attr(component, "ref", None) or "?"
            # Distinguish a device-type mismatch from an entirely unknown name.
            try:
                from .models import get_model_library

                entry = get_model_library().get_model(model)
            except Exception:  # pragma: no cover
                entry = None
            if entry is not None:
                problems.append(
                    f"{ref}: model '{model}' is a {entry.model_type} but device is "
                    f"{kind} (wrong model type)"
                )
            else:
                known = ", ".join(sorted(self.GENERIC_MODELS))
                problems.append(
                    f"{ref}: references SPICE model '{model}' with no .model card "
                    f"(not in the model library; known generics: {known})"
                )

        # 6. External vendor models (Sim.Library) must be coherent and locatable.
        for component in self._iter_components():
            if self._sim_excluded(component) or not self._has_external_lib(component):
                continue
            sim = self._sim_props(component)
            ref = self._attr(component, "ref", None) or "?"
            name = sim.get("name")
            if not name:
                problems.append(
                    f"{ref}: Sim.Library set without Sim.Name (which subckt/model "
                    f"to use is ambiguous)"
                )
                continue
            path = self._resolve_lib_path(sim.get("library"))
            if not path or not os.path.exists(path):
                problems.append(
                    f"{ref}: Sim.Library file not found: {sim.get('library')}"
                )
                continue
            kind_in_file, _nodes = self._scan_lib(path, name)
            if kind_in_file is None:
                problems.append(
                    f"{ref}: Sim.Name '{name}' is neither a .subckt nor a .model in "
                    f"{os.path.basename(str(path))}"
                )

        # 7. Sim.Compat must be unambiguous: one ngspice dialect per simulation.
        compat_values = self._distinct_compat_values()
        if len(compat_values) > 1:
            problems.append(
                f"conflicting Sim.Compat values across components: "
                f"{', '.join(compat_values)} (one dialect per simulation)"
            )

        if problems:
            raise SimulationValidationError(problems)
