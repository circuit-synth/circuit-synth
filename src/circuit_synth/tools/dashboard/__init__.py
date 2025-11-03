"""
Dashboard for TAC-8 Autonomous Coordination System

Provides web-based monitoring and metrics for the circuit-synth
coordinator, workers, and system resources.
"""

from .metrics import MetricsAggregator
from .server import create_app, app

__all__ = ['MetricsAggregator', 'create_app', 'app']
