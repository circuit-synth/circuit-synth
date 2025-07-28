"""
Component Matcher for KiCad Schematic Synchronization

This module provides component matching logic to identify corresponding components
between Circuit Synth JSON definitions and existing KiCad schematics.

The matching is based on configurable criteria such as reference designator,
component value, and footprint information.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result of component matching operation"""

    matched_pairs: List[Tuple[str, str]]  # (circuit_component_id, kicad_component_ref)
    unmatched_circuit: List[str]  # Circuit components with no KiCad match
    unmatched_kicad: List[str]  # KiCad components with no circuit match
    match_confidence: Dict[str, float]  # Confidence scores for matches


class ComponentMatcher:
    """
    Matches components between Circuit Synth and KiCad representations.

    Uses configurable matching criteria to identify corresponding components
    and handle cases where components exist in only one representation.
    """

    def __init__(self, match_criteria: List[str] = None):
        """
        Initialize component matcher.

        Args:
            match_criteria: List of properties to use for matching.
                          Default: ["reference", "value", "footprint"]
        """
        self.match_criteria = match_criteria or ["reference", "value", "footprint"]
        logger.debug(
            f"ComponentMatcher initialized with criteria: {self.match_criteria}"
        )

    def match_components(
        self, circuit_components: Dict, kicad_components: Dict
    ) -> MatchResult:
        """
        Match components between circuit and KiCad representations.

        Args:
            circuit_components: Dict of circuit components {id: component_data}
            kicad_components: Dict of KiCad components {ref: component_data}

        Returns:
            MatchResult containing matched pairs and unmatched components
        """
        logger.info(
            f"Matching {len(circuit_components)} circuit components with {len(kicad_components)} KiCad components"
        )

        matched_pairs = []
        match_confidence = {}
        used_kicad_refs = set()

        # First pass: exact matches on reference designator
        for circuit_id, circuit_comp in circuit_components.items():
            circuit_ref = self._get_component_reference(circuit_comp)
            if circuit_ref and circuit_ref in kicad_components:
                # Verify this is a good match using other criteria
                kicad_comp = kicad_components[circuit_ref]
                confidence = self._calculate_match_confidence(circuit_comp, kicad_comp)

                if confidence > 0.7:  # High confidence threshold for reference matches
                    matched_pairs.append((circuit_id, circuit_ref))
                    match_confidence[circuit_id] = confidence
                    used_kicad_refs.add(circuit_ref)
                    logger.debug(
                        f"Reference match: {circuit_id} -> {circuit_ref} (confidence: {confidence:.2f})"
                    )

        # Second pass: fuzzy matching for remaining components
        unmatched_circuit = [
            cid
            for cid in circuit_components.keys()
            if cid not in [pair[0] for pair in matched_pairs]
        ]
        unmatched_kicad = [
            ref for ref in kicad_components.keys() if ref not in used_kicad_refs
        ]

        # Try to match remaining components using value and footprint
        for circuit_id in unmatched_circuit[:]:  # Copy list to modify during iteration
            circuit_comp = circuit_components[circuit_id]
            best_match = None
            best_confidence = 0.0

            for kicad_ref in unmatched_kicad:
                kicad_comp = kicad_components[kicad_ref]
                confidence = self._calculate_match_confidence(circuit_comp, kicad_comp)

                if (
                    confidence > best_confidence and confidence > 0.5
                ):  # Minimum threshold
                    best_match = kicad_ref
                    best_confidence = confidence

            if best_match:
                matched_pairs.append((circuit_id, best_match))
                match_confidence[circuit_id] = best_confidence
                unmatched_circuit.remove(circuit_id)
                unmatched_kicad.remove(best_match)
                logger.debug(
                    f"Fuzzy match: {circuit_id} -> {best_match} (confidence: {best_confidence:.2f})"
                )

        result = MatchResult(
            matched_pairs=matched_pairs,
            unmatched_circuit=unmatched_circuit,
            unmatched_kicad=unmatched_kicad,
            match_confidence=match_confidence,
        )

        logger.info(
            f"Matching complete: {len(matched_pairs)} matches, "
            f"{len(unmatched_circuit)} unmatched circuit, "
            f"{len(unmatched_kicad)} unmatched KiCad"
        )

        return result

    def _get_component_reference(self, component) -> Optional[str]:
        """Extract reference designator from component data"""
        # Handle different component data formats
        if hasattr(component, "reference"):
            return component.reference
        elif isinstance(component, dict):
            return component.get("reference") or component.get("ref")
        return None

    def _get_component_value(self, component) -> Optional[str]:
        """Extract component value from component data"""
        if hasattr(component, "value"):
            return component.value
        elif isinstance(component, dict):
            return component.get("value")
        return None

    def _get_component_footprint(self, component) -> Optional[str]:
        """Extract footprint from component data"""
        if hasattr(component, "footprint"):
            return component.footprint
        elif isinstance(component, dict):
            return component.get("footprint")
        return None

    def _calculate_match_confidence(self, circuit_comp, kicad_comp) -> float:
        """
        Calculate confidence score for component match.

        Returns:
            Float between 0.0 and 1.0 indicating match confidence
        """
        score = 0.0
        criteria_count = 0

        # Check reference match
        if "reference" in self.match_criteria:
            circuit_ref = self._get_component_reference(circuit_comp)
            kicad_ref = self._get_component_reference(kicad_comp)
            if circuit_ref and kicad_ref:
                if circuit_ref == kicad_ref:
                    score += 0.5  # Reference match is highly weighted
                criteria_count += 1

        # Check value match
        if "value" in self.match_criteria:
            circuit_val = self._get_component_value(circuit_comp)
            kicad_val = self._get_component_value(kicad_comp)
            if circuit_val and kicad_val:
                if circuit_val.lower() == kicad_val.lower():
                    score += 0.3
                criteria_count += 1

        # Check footprint match
        if "footprint" in self.match_criteria:
            circuit_fp = self._get_component_footprint(circuit_comp)
            kicad_fp = self._get_component_footprint(kicad_comp)
            if circuit_fp and kicad_fp:
                if circuit_fp == kicad_fp:
                    score += 0.2
                criteria_count += 1

        # Normalize score based on available criteria
        if criteria_count > 0:
            return min(score, 1.0)  # Cap at 1.0
        else:
            return 0.0
