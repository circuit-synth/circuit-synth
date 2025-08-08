"""
Advanced Visualization and Export for SPICE Simulation Results

This module provides comprehensive output capabilities for simulation results:
- Professional plots (Bode, phase, time-domain)
- PDF report generation
- CSV/JSON data export
- SPICE netlist export
- Interactive HTML plots
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    import matplotlib.gridspec as gridspec
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available - plotting disabled")

try:
    import plotly.graph_objects as go
    import plotly.offline as pyo

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.info("plotly not available - interactive plots disabled")


class SimulationVisualizer:
    """Advanced visualization for simulation results."""

    def __init__(self, simulation_result):
        """Initialize with a SimulationResult object."""
        self.result = simulation_result
        self.analysis_type = simulation_result.analysis_type

    def plot_time_domain(
        self,
        nodes: List[str],
        time_array: Optional[np.ndarray] = None,
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[plt.Figure]:
        """
        Create time-domain plot for transient analysis.

        Args:
            nodes: List of node names to plot
            time_array: Time points array
            save_path: Optional path to save plot
            show: Whether to display the plot

        Returns:
            matplotlib Figure object or None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib required for plotting")
            return None

        fig, ax = plt.subplots(figsize=(12, 6))

        for node in nodes:
            try:
                voltage = self.result.get_voltage(node)
                if isinstance(voltage, list):
                    if time_array is not None:
                        ax.plot(
                            time_array * 1000, voltage, label=f"V({node})", linewidth=2
                        )
                    else:
                        ax.plot(voltage, label=f"V({node})", linewidth=2)
            except KeyError:
                logger.warning(f"Node {node} not found in results")

        ax.set_xlabel("Time (ms)" if time_array is not None else "Sample")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("Transient Analysis - Time Domain Response")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved time-domain plot to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_bode(
        self,
        input_node: str,
        output_node: str,
        frequency_array: Optional[np.ndarray] = None,
        save_path: Optional[str] = None,
        show: bool = True,
    ) -> Optional[plt.Figure]:
        """
        Create Bode plot (magnitude and phase) for AC analysis.

        Args:
            input_node: Input reference node
            output_node: Output node to analyze
            frequency_array: Frequency points array
            save_path: Optional path to save plot
            show: Whether to display the plot

        Returns:
            matplotlib Figure object or None
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib required for plotting")
            return None

        fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])

        # Magnitude plot
        ax1 = fig.add_subplot(gs[0])
        try:
            output_voltage = self.result.get_voltage(output_node)
            input_voltage = self.result.get_voltage(input_node)

            if isinstance(output_voltage, list) and isinstance(input_voltage, list):
                # Calculate gain in dB
                gain = np.array(output_voltage) / np.array(input_voltage)
                gain_db = 20 * np.log10(np.abs(gain))

                if frequency_array is not None:
                    ax1.semilogx(frequency_array, gain_db, linewidth=2, color="blue")
                else:
                    ax1.plot(gain_db, linewidth=2, color="blue")
        except Exception as e:
            logger.error(f"Error calculating Bode plot: {e}")

        ax1.set_ylabel("Magnitude (dB)")
        ax1.set_title("Bode Plot - Frequency Response")
        ax1.grid(True, which="both", alpha=0.3)

        # Phase plot
        ax2 = fig.add_subplot(gs[1])
        try:
            if isinstance(output_voltage, list) and isinstance(input_voltage, list):
                # Calculate phase
                gain_complex = np.array(output_voltage) / np.array(input_voltage)
                phase = np.angle(gain_complex, deg=True)

                if frequency_array is not None:
                    ax2.semilogx(frequency_array, phase, linewidth=2, color="red")
                else:
                    ax2.plot(phase, linewidth=2, color="red")
        except Exception as e:
            logger.error(f"Error calculating phase: {e}")

        ax2.set_xlabel("Frequency (Hz)" if frequency_array is not None else "Point")
        ax2.set_ylabel("Phase (degrees)")
        ax2.grid(True, which="both", alpha=0.3)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            logger.info(f"Saved Bode plot to {save_path}")

        if show:
            plt.show()

        return fig

    def export_to_csv(self, filepath: str, nodes: Optional[List[str]] = None):
        """
        Export simulation results to CSV file.

        Args:
            filepath: Path to save CSV file
            nodes: Optional list of nodes to export (exports all if None)
        """
        import csv

        if nodes is None:
            nodes = self.result.list_nodes()

        data_rows = []
        headers = ["Point"]

        # Collect data for each node
        max_length = 0
        node_data = {}

        for node in nodes:
            try:
                voltage = self.result.get_voltage(node)
                if isinstance(voltage, list):
                    node_data[node] = voltage
                    max_length = max(max_length, len(voltage))
                    headers.append(f"V({node})")
                else:
                    node_data[node] = [voltage]  # Single value
                    headers.append(f"V({node})")
            except KeyError:
                logger.warning(f"Node {node} not found")

        # Build data rows
        for i in range(max_length):
            row = [i]
            for node in nodes:
                if node in node_data:
                    if i < len(node_data[node]):
                        row.append(node_data[node][i])
                    else:
                        row.append("")
            data_rows.append(row)

        # Write CSV
        with open(filepath, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(data_rows)

        logger.info(f"Exported results to CSV: {filepath}")

    def export_to_json(self, filepath: str):
        """
        Export simulation results to JSON file.

        Args:
            filepath: Path to save JSON file
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": self.analysis_type,
            "nodes": {},
            "metadata": {"tool": "circuit-synth", "version": "1.0.0"},
        }

        # Export all node voltages
        for node in self.result.list_nodes():
            try:
                voltage = self.result.get_voltage(node)
                if isinstance(voltage, list):
                    data["nodes"][node] = [float(v) for v in voltage]
                else:
                    data["nodes"][node] = float(voltage)
            except Exception as e:
                logger.warning(f"Could not export node {node}: {e}")

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported results to JSON: {filepath}")

    def generate_pdf_report(
        self,
        filepath: str,
        circuit_name: str = "Circuit",
        include_plots: bool = True,
        include_data: bool = True,
        testbench_config: Optional[Dict] = None,
    ):
        """
        Generate comprehensive PDF report of simulation results.

        Args:
            filepath: Path to save PDF file
            circuit_name: Name of the circuit
            include_plots: Whether to include plots
            include_data: Whether to include data tables
            testbench_config: Optional test bench configuration to include
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("matplotlib required for PDF generation")
            return

        with PdfPages(filepath) as pdf:
            # Title page
            fig = plt.figure(figsize=(8.5, 11))
            fig.suptitle(
                f"SPICE Simulation Report\n{circuit_name}",
                fontsize=20,
                fontweight="bold",
            )

            # Add metadata
            ax = fig.add_subplot(111)
            ax.axis("off")

            report_text = f"""
Analysis Type: {self.analysis_type.upper()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Tool: circuit-synth SPICE simulator

Summary:
- Number of nodes analyzed: {len(self.result.list_nodes())}
- Simulation completed successfully
            """

            if testbench_config:
                report_text += f"\n\nTest Bench Configuration:"
                report_text += (
                    f"\n- Description: {testbench_config.get('description', 'N/A')}"
                )
                report_text += f"\n- Analyses performed: {len(testbench_config.get('analyses', []))}"

            ax.text(
                0.1,
                0.7,
                report_text,
                fontsize=12,
                verticalalignment="top",
                family="monospace",
            )

            pdf.savefig(fig, bbox_inches="tight")
            plt.close()

            # Add plots based on analysis type
            if include_plots:
                if self.analysis_type == "transient":
                    # Time domain plot
                    fig = self.plot_time_domain(
                        self.result.list_nodes()[:4], show=False  # First 4 nodes
                    )
                    if fig:
                        pdf.savefig(fig, bbox_inches="tight")
                        plt.close(fig)

                elif self.analysis_type == "ac":
                    # Frequency response plot
                    nodes = self.result.list_nodes()
                    if len(nodes) >= 2:
                        fig = self.plot_bode(nodes[0], nodes[1], show=False)
                        if fig:
                            pdf.savefig(fig, bbox_inches="tight")
                            plt.close(fig)

            # Add data table page
            if include_data:
                fig = plt.figure(figsize=(8.5, 11))
                ax = fig.add_subplot(111)
                ax.axis("tight")
                ax.axis("off")

                # Create data table
                nodes = self.result.list_nodes()[:10]  # First 10 nodes
                table_data = []

                for node in nodes:
                    try:
                        voltage = self.result.get_voltage(node)
                        if isinstance(voltage, list):
                            # Show first and last values for arrays
                            if len(voltage) > 0:
                                table_data.append(
                                    [node, f"{voltage[0]:.3f}V", f"{voltage[-1]:.3f}V"]
                                )
                        else:
                            table_data.append([node, f"{voltage:.3f}V", "-"])
                    except:
                        pass

                if table_data:
                    table = ax.table(
                        cellText=table_data,
                        colLabels=["Node", "First/DC Value", "Last Value"],
                        cellLoc="center",
                        loc="center",
                    )
                    table.auto_set_font_size(False)
                    table.set_fontsize(10)
                    table.scale(1.2, 1.5)

                ax.set_title("Simulation Data Summary", fontsize=14, fontweight="bold")
                pdf.savefig(fig, bbox_inches="tight")
                plt.close()

        logger.info(f"Generated PDF report: {filepath}")

    def create_interactive_plot(
        self, nodes: List[str], output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Create interactive HTML plot using Plotly.

        Args:
            nodes: List of nodes to plot
            output_path: Optional path to save HTML file

        Returns:
            HTML string or filepath
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("plotly not available for interactive plots")
            return None

        fig = go.Figure()

        for node in nodes:
            try:
                voltage = self.result.get_voltage(node)
                if isinstance(voltage, list):
                    fig.add_trace(
                        go.Scatter(
                            y=voltage,
                            mode="lines",
                            name=f"V({node})",
                            line=dict(width=2),
                        )
                    )
            except KeyError:
                logger.warning(f"Node {node} not found")

        fig.update_layout(
            title=f"{self.analysis_type.upper()} Analysis Results",
            xaxis_title="Sample/Time/Frequency",
            yaxis_title="Voltage (V)",
            hovermode="x unified",
            showlegend=True,
            template="plotly_white",
        )

        if output_path:
            pyo.plot(fig, filename=output_path, auto_open=False)
            logger.info(f"Saved interactive plot to {output_path}")
            return output_path
        else:
            return pyo.plot(fig, output_type="div", include_plotlyjs="cdn")

    def export_spice_netlist(self, filepath: str, include_models: bool = True):
        """
        Export the SPICE netlist used for simulation.

        Args:
            filepath: Path to save netlist file
            include_models: Whether to include model definitions
        """
        # This would export the PySpice netlist
        netlist_content = f"* SPICE Netlist Generated by circuit-synth\n"
        netlist_content += f"* Analysis Type: {self.analysis_type}\n"
        netlist_content += f"* Generated: {datetime.now().isoformat()}\n\n"

        # Add circuit netlist (would come from spice_circuit object)
        netlist_content += "* Circuit netlist would be here\n"
        netlist_content += "* (Requires access to spice_circuit object)\n\n"

        if include_models:
            netlist_content += "* Model definitions\n"
            netlist_content += ".MODEL DefaultDiode D (IS=1e-14 RS=0.1)\n"
            netlist_content += ".MODEL DefaultNPN NPN (BF=100)\n"
            netlist_content += ".MODEL DefaultNMOS NMOS (VTO=2.0 KP=0.1)\n"

        netlist_content += "\n.END\n"

        with open(filepath, "w") as f:
            f.write(netlist_content)

        logger.info(f"Exported SPICE netlist to {filepath}")


def enhance_simulation_result(SimulationResultClass):
    """
    Monkey-patch the SimulationResult class to add export methods.
    This allows us to add methods without modifying the original class.
    """

    def export_csv(self, filepath: str, nodes: Optional[List[str]] = None):
        """Export results to CSV."""
        viz = SimulationVisualizer(self)
        viz.export_to_csv(filepath, nodes)

    def export_json(self, filepath: str):
        """Export results to JSON."""
        viz = SimulationVisualizer(self)
        viz.export_to_json(filepath)

    def generate_report(self, filepath: str, **kwargs):
        """Generate PDF report."""
        viz = SimulationVisualizer(self)
        viz.generate_pdf_report(filepath, **kwargs)

    def plot_interactive(self, nodes: List[str], output_path: Optional[str] = None):
        """Create interactive plot."""
        viz = SimulationVisualizer(self)
        return viz.create_interactive_plot(nodes, output_path)

    # Add methods to the class
    SimulationResultClass.export_csv = export_csv
    SimulationResultClass.export_json = export_json
    SimulationResultClass.generate_report = generate_report
    SimulationResultClass.plot_interactive = plot_interactive

    return SimulationResultClass
