"""
Freerouting Runner Module for Circuit Synth

This module provides subprocess management for running the Freerouting JAR file
to automatically route PCB designs. It handles configuration options, progress
tracking, timeouts, and error handling.

Author: Circuit Synth Team
Date: 2025-06-23
"""

import logging
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class RoutingEffort(Enum):
    """Routing effort levels for Freerouting"""

    FAST = "fast"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FreeroutingConfig:
    """Configuration options for Freerouting"""

    # Paths
    java_path: str = "java"  # Path to Java executable
    freerouting_jar: Optional[str] = None  # Path to Freerouting JAR

    # Routing options
    effort: RoutingEffort = RoutingEffort.MEDIUM
    optimization_passes: int = 10
    via_costs: float = 50.0
    allowed_layers: Optional[list] = None  # None means all layers

    # Performance options
    memory_mb: int = 1024  # Java heap size in MB
    timeout_seconds: Optional[int] = 3600  # 1 hour default timeout

    # Progress tracking
    progress_callback: Optional[Callable[[float, str], None]] = None
    update_interval: float = 1.0  # Progress update interval in seconds


class FreeroutingRunner:
    """Manages Freerouting subprocess execution"""

    # Common Freerouting JAR locations
    DEFAULT_JAR_LOCATIONS = [
        # Current directory
        "./freerouting.jar",
        "./Freerouting.jar",
        # User home
        "~/freerouting/freerouting.jar",
        "~/Freerouting/freerouting.jar",
        # System locations
        "/usr/local/bin/freerouting.jar",
        "/opt/freerouting/freerouting.jar",
        # Windows locations
        "C:/Program Files/Freerouting/freerouting.jar",
        "C:/freerouting/freerouting.jar",
    ]

    def __init__(self, config: Optional[FreeroutingConfig] = None):
        """
        Initialize Freerouting runner

        Args:
            config: Configuration options (uses defaults if None)
        """
        self.config = config or FreeroutingConfig()
        self._process: Optional[subprocess.Popen] = None
        self._output_thread: Optional[threading.Thread] = None
        self._progress: float = 0.0
        self._status: str = "Not started"
        self._stop_event = threading.Event()

        # Find Freerouting JAR if not specified
        if not self.config.freerouting_jar:
            self.config.freerouting_jar = self._find_freerouting_jar()

    def _find_freerouting_jar(self) -> Optional[str]:
        """Find Freerouting JAR file in common locations"""
        for location in self.DEFAULT_JAR_LOCATIONS:
            path = Path(os.path.expanduser(location))
            if path.exists() and path.is_file():
                logger.info(f"Found Freerouting JAR at: {path}")
                return str(path)

        logger.warning("Freerouting JAR not found in default locations")
        return None

    def _check_java(self) -> bool:
        """Check if Java is available"""
        try:
            result = subprocess.run(
                [self.config.java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info(f"Java found: {result.stderr.strip()}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        logger.error("Java runtime not found")
        return False

    def _parse_progress(self, line: str) -> Optional[float]:
        """
        Parse progress from Freerouting output

        Freerouting outputs progress in various formats:
        - "Pass 1 of 10"
        - "Optimization: 50%"
        - "Routing net 25 of 100"
        """
        # Pass number pattern
        pass_match = re.search(r"Pass (\d+) of (\d+)", line)
        if pass_match:
            current = int(pass_match.group(1))
            total = int(pass_match.group(2))
            return (current / total) * 100

        # Percentage pattern
        percent_match = re.search(r"(\d+)%", line)
        if percent_match:
            return float(percent_match.group(1))

        # Net routing pattern
        net_match = re.search(r"Routing net (\d+) of (\d+)", line)
        if net_match:
            current = int(net_match.group(1))
            total = int(net_match.group(2))
            return (current / total) * 100

        return None

    def _monitor_output(self):
        """Monitor Freerouting output in a separate thread"""
        if not self._process or not self._process.stdout:
            return

        try:
            # Handle both real process stdout and mock iterators
            if hasattr(self._process.stdout, "readline"):
                # Real process with readline
                for line in iter(self._process.stdout.readline, ""):
                    if self._stop_event.is_set():
                        break
                    self._process_line(line)
            else:
                # Mock iterator or direct iteration
                for line in self._process.stdout:
                    if self._stop_event.is_set():
                        break
                    self._process_line(line)

        except Exception as e:
            logger.error(f"Error monitoring output: {e}")

    def _process_line(self, line):
        """Process a single line of output"""
        line = line.strip()
        if not line:
            return

        logger.debug(f"Freerouting: {line}")

        # Parse progress
        progress = self._parse_progress(line)
        if progress is not None:
            self._progress = progress
            self._status = line

            if self.config.progress_callback:
                self.config.progress_callback(progress, line)

        # Check for completion
        if "Routing complete" in line or "finished" in line.lower():
            self._progress = 100.0
            self._status = "Routing complete"
            if self.config.progress_callback:
                self.config.progress_callback(100.0, "Routing complete")

        # Check for errors
        if "error" in line.lower() or "exception" in line.lower():
            self._status = f"Error: {line}"
            logger.error(f"Freerouting error: {line}")

    def route(
        self, dsn_file: str, output_file: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Run Freerouting on a DSN file

        Args:
            dsn_file: Path to input DSN file
            output_file: Path to output SES file (defaults to dsn_file.ses)

        Returns:
            Tuple of (success, output_file_or_error_message)
        """
        # Validate inputs
        if not os.path.exists(dsn_file):
            return False, f"DSN file not found: {dsn_file}"

        if not self.config.freerouting_jar:
            return False, "Freerouting JAR not found. Please specify path in config."

        if not os.path.exists(self.config.freerouting_jar):
            return False, f"Freerouting JAR not found at: {self.config.freerouting_jar}"

        if not self._check_java():
            return False, "Java runtime not found. Please install Java or specify path."

        # Default output file
        if not output_file:
            output_file = str(Path(dsn_file).with_suffix(".ses"))

        # Build command
        cmd = [
            self.config.java_path,
            f"-Xmx{self.config.memory_mb}m",  # Memory allocation
            "-jar",
            self.config.freerouting_jar,
            "-de",
            dsn_file,  # Input DSN
            "-do",
            output_file,  # Output SES
            "-mp",
            str(self.config.optimization_passes),  # Max passes
        ]

        # Add effort level
        if self.config.effort == RoutingEffort.FAST:
            cmd.extend(["-fast"])
        elif self.config.effort == RoutingEffort.HIGH:
            cmd.extend(["-accurate"])
        # MEDIUM is default, no flag needed

        # Add via costs if not default
        if self.config.via_costs != 50.0:
            cmd.extend(["-vc", str(self.config.via_costs)])

        # Add layer restrictions if specified
        if self.config.allowed_layers:
            layers_str = ",".join(map(str, self.config.allowed_layers))
            cmd.extend(["-layers", layers_str])

        logger.info(f"Starting Freerouting with command: {' '.join(cmd)}")

        try:
            # Reset state
            self._progress = 0.0
            self._status = "Starting Freerouting..."
            self._stop_event.clear()

            # Start process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
            )

            # Start output monitoring thread
            self._output_thread = threading.Thread(
                target=self._monitor_output, daemon=True
            )
            self._output_thread.start()

            # Wait for completion with timeout
            start_time = time.time()
            while self._process.poll() is None:
                if self.config.timeout_seconds:
                    elapsed = time.time() - start_time
                    if elapsed > self.config.timeout_seconds:
                        logger.error("Freerouting timeout exceeded")
                        self.stop()
                        return (
                            False,
                            f"Timeout after {self.config.timeout_seconds} seconds",
                        )

                time.sleep(self.config.update_interval)

            # Check return code
            if self._process.returncode == 0:
                # Verify output file exists
                if os.path.exists(output_file):
                    logger.info(f"Routing complete. Output saved to: {output_file}")
                    return True, output_file
                else:
                    return False, "Routing completed but output file not found"
            else:
                return False, f"Freerouting failed with code {self._process.returncode}"

        except Exception as e:
            logger.error(f"Error running Freerouting: {e}")
            return False, str(e)

        finally:
            self._stop_event.set()
            if self._output_thread and self._output_thread.is_alive():
                self._output_thread.join(timeout=5)

    def stop(self):
        """Stop the routing process"""
        logger.info("Stopping Freerouting...")
        self._stop_event.set()

        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Freerouting did not terminate, killing process")
                self._process.kill()

    def get_progress(self) -> Tuple[float, str]:
        """
        Get current progress

        Returns:
            Tuple of (progress_percentage, status_message)
        """
        return self._progress, self._status


def route_pcb(
    dsn_file: str,
    output_file: Optional[str] = None,
    effort: str = "medium",
    optimization_passes: int = 10,
    timeout_seconds: Optional[int] = 3600,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Tuple[bool, str]:
    """
    Convenience function to route a PCB

    Args:
        dsn_file: Path to input DSN file
        output_file: Path to output SES file (optional)
        effort: Routing effort level ('fast', 'medium', 'high')
        optimization_passes: Number of optimization passes
        timeout_seconds: Timeout in seconds (None for no timeout)
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (success, output_file_or_error_message)
    """
    # Convert effort string to enum
    effort_map = {
        "fast": RoutingEffort.FAST,
        "medium": RoutingEffort.MEDIUM,
        "high": RoutingEffort.HIGH,
    }
    effort_enum = effort_map.get(effort.lower(), RoutingEffort.MEDIUM)

    # Create config
    config = FreeroutingConfig(
        effort=effort_enum,
        optimization_passes=optimization_passes,
        timeout_seconds=timeout_seconds,
        progress_callback=progress_callback,
    )

    # Run routing
    runner = FreeroutingRunner(config)
    return runner.route(dsn_file, output_file)
