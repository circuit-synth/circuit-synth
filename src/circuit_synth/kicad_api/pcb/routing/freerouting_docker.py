"""
Docker-based Freerouting Runner for Circuit Synth

This module provides a simplified Freerouting runner that uses Docker
containers exclusively, avoiding Java version compatibility issues.

Author: Circuit Synth Team
Date: 2025-06-23
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class FreeroutingDocker:
    """Runs Freerouting using Docker container"""

    DOCKER_IMAGE = "ghcr.io/freerouting/freerouting:nightly"

    def __init__(self):
        """Initialize Docker-based Freerouting runner"""
        self.docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Docker found: {result.stdout.strip()}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        logger.error("Docker not found. Please install Docker Desktop.")
        return False

    def route(
        self,
        dsn_file: str,
        output_file: Optional[str] = None,
        optimization_passes: int = 10,
        timeout_seconds: Optional[int] = 3600,
    ) -> Tuple[bool, str]:
        """
        Run Freerouting on a DSN file using Docker

        Args:
            dsn_file: Path to input DSN file
            output_file: Path to output SES file (defaults to dsn_file.ses)
            optimization_passes: Number of optimization passes
            timeout_seconds: Timeout in seconds (None for no timeout)

        Returns:
            Tuple of (success, output_file_or_error_message)
        """
        if not self.docker_available:
            return False, "Docker is not available. Please install Docker Desktop."

        # Validate inputs
        if not os.path.exists(dsn_file):
            return False, f"DSN file not found: {dsn_file}"

        # Default output file
        if not output_file:
            output_file = str(Path(dsn_file).with_suffix(".ses"))

        # Get absolute paths for Docker volume mounting
        abs_dsn = os.path.abspath(dsn_file)
        abs_output = os.path.abspath(output_file)
        work_dir = os.path.dirname(abs_dsn)
        dsn_name = os.path.basename(abs_dsn)
        output_name = os.path.basename(abs_output)

        # Build Docker command
        # The nightly image needs the full java command
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{work_dir}:/work",  # Mount the directory
            self.DOCKER_IMAGE,
            "java",
            "-jar",
            "/app/freerouting-executable.jar",
            "-de",
            f"/work/{dsn_name}",  # Input DSN
            "-do",
            f"/work/{output_name}",  # Output SES
            "-mp",
            str(optimization_passes),  # Max passes
        ]

        logger.info(f"Running Freerouting with Docker: {' '.join(cmd)}")
        logger.debug(f"Working directory: {work_dir}")
        logger.debug(f"DSN file: {dsn_name} (size: {os.path.getsize(abs_dsn)} bytes)")

        try:
            # Pull the image if needed (with progress)
            logger.info("Checking Docker image...")
            pull_result = subprocess.run(
                ["docker", "image", "inspect", self.DOCKER_IMAGE],
                capture_output=True,
                text=True,
                timeout=10,  # Add 10 second timeout
            )

            if pull_result.returncode != 0:
                logger.info(
                    "Pulling Docker image (this may take a moment on first run)..."
                )
                pull_cmd = ["docker", "pull", self.DOCKER_IMAGE]
                pull_result = subprocess.run(pull_cmd, capture_output=True, text=True)
                if pull_result.returncode != 0:
                    return False, f"Failed to pull Docker image: {pull_result.stderr}"

            # Run Freerouting
            logger.info("Running Freerouting...")
            logger.info(f"Timeout set to {timeout_seconds} seconds")
            logger.info("Note: Routing complex boards can take several minutes...")

            # Run without capturing output to see progress
            result = subprocess.run(
                cmd,
                # Don't capture output - let it stream to console
                capture_output=False,
                text=True,
                timeout=timeout_seconds,
            )

            if result.returncode == 0:
                # Check if output file was created
                if os.path.exists(output_file):
                    output_size = os.path.getsize(output_file)
                    logger.info(
                        f"Routing complete. Output saved to: {output_file} (size: {output_size} bytes)"
                    )

                    # Log all output for debugging
                    if result.stdout:
                        logger.info("Freerouting stdout:")
                        for line in result.stdout.split("\n"):
                            if line.strip():
                                logger.info(f"  {line}")

                    if result.stderr:
                        logger.warning("Freerouting stderr:")
                        for line in result.stderr.split("\n"):
                            if line.strip():
                                logger.warning(f"  {line}")

                    # Check if output is empty
                    if output_size == 0:
                        logger.warning("Output SES file is empty (0 bytes)")
                        # Try to read DSN to check for nets
                        try:
                            with open(dsn_file, "r") as f:
                                dsn_content = f.read()
                                if "network" not in dsn_content.lower():
                                    logger.warning(
                                        "DSN file appears to have no network/nets defined"
                                    )
                                logger.debug(
                                    f"First 500 chars of DSN:\n{dsn_content[:500]}"
                                )
                        except Exception as e:
                            logger.error(f"Failed to read DSN for debugging: {e}")

                    return True, output_file
                else:
                    logger.error("Routing completed but output file not found")
                    logger.debug(f"Expected output at: {output_file}")
                    logger.debug(f"Directory contents: {os.listdir(work_dir)}")
                    return False, "Routing completed but output file not found"
            else:
                error_msg = f"Freerouting failed with code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nStderr: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nStdout: {result.stdout}"
                logger.error(error_msg)
                return False, error_msg

        except subprocess.TimeoutExpired:
            return False, f"Freerouting timeout after {timeout_seconds} seconds"
        except Exception as e:
            logger.error(f"Error running Freerouting: {e}")
            return False, str(e)


def route_pcb_docker(
    dsn_file: str,
    output_file: Optional[str] = None,
    optimization_passes: int = 10,
    timeout_seconds: Optional[int] = 3600,
) -> Tuple[bool, str]:
    """
    Convenience function to route a PCB using Docker

    Args:
        dsn_file: Path to input DSN file
        output_file: Path to output SES file (optional)
        optimization_passes: Number of optimization passes
        timeout_seconds: Timeout in seconds (None for no timeout)

    Returns:
        Tuple of (success, output_file_or_error_message)
    """
    runner = FreeroutingDocker()
    return runner.route(dsn_file, output_file, optimization_passes, timeout_seconds)
