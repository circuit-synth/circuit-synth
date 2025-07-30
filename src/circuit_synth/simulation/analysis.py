"""
Analysis types for SPICE simulation.

This module defines different types of circuit analysis that can be
performed with circuit-synth SPICE integration.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union


@dataclass
class DCAnalysis:
    """DC operating point and sweep analysis configuration."""

    # Operating point analysis (no parameters needed)
    operating_point: bool = True

    # DC sweep parameters
    source: Optional[str] = None  # Source to sweep (e.g., "Vsupply")
    start: Optional[float] = None
    stop: Optional[float] = None
    step: Optional[float] = None

    def is_sweep(self) -> bool:
        """Check if this is a sweep analysis."""
        return all(
            x is not None for x in [self.source, self.start, self.stop, self.step]
        )


@dataclass
class ACAnalysis:
    """AC small-signal analysis configuration."""

    start_frequency: float = 1e0  # Start frequency (Hz)
    stop_frequency: float = 1e6  # Stop frequency (Hz)
    points_per_decade: int = 10  # Points per decade
    variation: str = "dec"  # 'dec', 'oct', or 'lin'

    def get_total_points(self) -> int:
        """Calculate total number of frequency points."""
        import math

        if self.variation == "dec":
            decades = math.log10(self.stop_frequency / self.start_frequency)
            return int(decades * self.points_per_decade)
        elif self.variation == "oct":
            octaves = math.log2(self.stop_frequency / self.start_frequency)
            return int(octaves * self.points_per_decade)
        else:  # linear
            return self.points_per_decade


@dataclass
class TransientAnalysis:
    """Transient (time-domain) analysis configuration."""

    step_time: float = 1e-6  # Time step (seconds)
    end_time: float = 1e-3  # End time (seconds)
    start_time: float = 0.0  # Start time (seconds)
    max_step: Optional[float] = None  # Maximum step size

    def get_num_points(self) -> int:
        """Calculate number of time points."""
        return int((self.end_time - self.start_time) / self.step_time) + 1


# Predefined analysis configurations for common scenarios
class CommonAnalyses:
    """Common analysis configurations."""

    @staticmethod
    def dc_operating_point() -> DCAnalysis:
        """Simple DC operating point analysis."""
        return DCAnalysis(operating_point=True)

    @staticmethod
    def dc_sweep(
        source: str, start: float, stop: float, points: int = 100
    ) -> DCAnalysis:
        """DC sweep analysis."""
        step = (stop - start) / (points - 1)
        return DCAnalysis(
            operating_point=False, source=source, start=start, stop=stop, step=step
        )

    @staticmethod
    def ac_frequency_response(start_hz: float = 1, stop_hz: float = 1e6) -> ACAnalysis:
        """Standard AC frequency response analysis."""
        return ACAnalysis(
            start_frequency=start_hz,
            stop_frequency=stop_hz,
            points_per_decade=20,
            variation="dec",
        )

    @staticmethod
    def transient_step_response(
        duration_ms: float = 1.0, resolution_us: float = 1.0
    ) -> TransientAnalysis:
        """Step response transient analysis."""
        return TransientAnalysis(
            step_time=resolution_us * 1e-6, end_time=duration_ms * 1e-3, start_time=0.0
        )

    @staticmethod
    def transient_pulse_response(
        pulse_width_us: float = 100, resolution_ns: float = 10
    ) -> TransientAnalysis:
        """Pulse response transient analysis."""
        duration = pulse_width_us * 5  # 5x pulse width for settling
        return TransientAnalysis(
            step_time=resolution_ns * 1e-9, end_time=duration * 1e-6, start_time=0.0
        )
