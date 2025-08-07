#!/usr/bin/env python3
"""
FMEA CLI Command for Circuit-Synth
Provides command-line interface for FMEA analysis of circuits
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from circuit_synth.quality_assurance import analyze_any_circuit

console = Console()


@click.command()
@click.argument("circuit_path", type=click.Path(exists=True))
@click.option("--output", "-o", help="Output PDF filename", default=None)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--top", "-t", default=10, help="Number of top risks to display")
@click.option("--threshold", default=125, help="RPN threshold for high risk")
def main(circuit_path: str, output: str, verbose: bool, top: int, threshold: int):
    """
    Perform FMEA analysis on a circuit design

    CIRCUIT_PATH: Path to circuit file (.py or .json) or directory

    Examples:

        cs-fmea ESP32_C6_Dev_Board/

        cs-fmea my_circuit.py -o analysis.pdf

        cs-fmea circuit.json --top 20 --threshold 150
    """

    console.print(
        Panel.fit(
            Text("🔍 FMEA Circuit Analysis Tool", style="bold blue"), style="blue"
        )
    )

    # Determine output filename
    if output is None:
        path = Path(circuit_path)
        if path.is_file():
            output = f"{path.stem}_FMEA_Report.pdf"
        else:
            output = f"{path.name}_FMEA_Report.pdf"

    console.print(f"📂 Analyzing: {circuit_path}", style="cyan")
    console.print(f"📄 Output: {output}", style="cyan")

    try:
        # Perform analysis
        from circuit_synth.quality_assurance.fmea_analyzer import UniversalFMEAAnalyzer

        analyzer = UniversalFMEAAnalyzer(verbose=verbose)

        # Parse circuit
        path = Path(circuit_path)
        if path.is_dir():
            # Look for circuit files
            json_files = list(path.glob("*.json"))
            py_files = list(path.glob("*.py"))

            if json_files:
                circuit_file = json_files[0]
            elif py_files:
                # Find main circuit file
                main_file = path / "main.py"
                if main_file.exists():
                    circuit_file = main_file
                else:
                    circuit_file = py_files[0]
            else:
                console.print("❌ No circuit files found", style="red")
                return
        else:
            circuit_file = path

        console.print(f"🔧 Parsing: {circuit_file.name}", style="yellow")

        # Analyze
        circuit_data, failure_modes = analyzer.analyze_circuit_file(str(circuit_file))

        # Display summary
        console.print("\n📊 Analysis Results:", style="bold green")

        # Statistics
        total = len(failure_modes)
        critical = sum(1 for fm in failure_modes if fm["rpn"] >= 300)
        high = sum(1 for fm in failure_modes if threshold <= fm["rpn"] < 300)
        medium = sum(1 for fm in failure_modes if 50 <= fm["rpn"] < threshold)
        low = sum(1 for fm in failure_modes if fm["rpn"] < 50)

        stats_table = Table(title="Risk Distribution", show_header=True)
        stats_table.add_column("Risk Level", style="cyan")
        stats_table.add_column("Count", justify="right")
        stats_table.add_column("Percentage", justify="right")

        stats_table.add_row(
            "🔴 Critical (≥300)", str(critical), f"{critical/total*100:.1f}%"
        )
        stats_table.add_row(
            "🟠 High (≥{})".format(threshold), str(high), f"{high/total*100:.1f}%"
        )
        stats_table.add_row(
            "🟡 Medium (50-{})".format(threshold - 1),
            str(medium),
            f"{medium/total*100:.1f}%",
        )
        stats_table.add_row("🟢 Low (<50)", str(low), f"{low/total*100:.1f}%")
        stats_table.add_row("", "", "")
        stats_table.add_row("Total", str(total), "100.0%", style="bold")

        console.print(stats_table)

        # Top risks
        console.print(f"\n🚨 Top {top} Risks:", style="bold red")

        risk_table = Table(show_header=True)
        risk_table.add_column("#", justify="right", style="dim")
        risk_table.add_column("Component", style="cyan")
        risk_table.add_column("Failure Mode", style="yellow")
        risk_table.add_column("RPN", justify="right", style="bold")
        risk_table.add_column("Risk", justify="center")

        for i, fm in enumerate(failure_modes[:top], 1):
            rpn = fm["rpn"]
            if rpn >= 300:
                risk_emoji = "🔴"
                risk_style = "red"
            elif rpn >= threshold:
                risk_emoji = "🟠"
                risk_style = "yellow"
            elif rpn >= 50:
                risk_emoji = "🟡"
                risk_style = "dim yellow"
            else:
                risk_emoji = "🟢"
                risk_style = "green"

            risk_table.add_row(
                str(i),
                fm["component"][:30],
                fm["failure_mode"][:40],
                str(rpn),
                risk_emoji,
                style=risk_style,
            )

        console.print(risk_table)

        # Component summary
        console.print(f"\n🔧 Component Analysis:", style="bold blue")
        console.print(
            f"  Total components analyzed: {circuit_data.get('component_count', 'N/A')}"
        )

        if circuit_data.get("subsystems"):
            console.print(f"  Subsystems identified: {len(circuit_data['subsystems'])}")
            for subsystem in circuit_data["subsystems"][:5]:
                console.print(f"    • {subsystem['name']}", style="dim")

        # Generate PDF report
        console.print(f"\n📝 Generating PDF report...", style="yellow")

        report_path = analyzer.generate_report(circuit_data, failure_modes, output)

        if report_path:
            file_size = Path(report_path).stat().st_size / 1024
            console.print(
                f"✅ Report generated: {report_path} ({file_size:.1f} KB)",
                style="green",
            )

            # Recommendations summary
            console.print("\n💡 Key Recommendations:", style="bold magenta")

            # Get unique recommendations for critical/high risks
            recommendations = set()
            for fm in failure_modes:
                if fm["rpn"] >= threshold:
                    rec = fm.get("recommendation", "")
                    if rec and len(rec) > 10:
                        recommendations.add(rec)

            for i, rec in enumerate(list(recommendations)[:5], 1):
                console.print(f"  {i}. {rec[:80]}...", style="dim")

            console.print("\n🎯 Next Steps:", style="bold")
            console.print("  1. Review the PDF report for detailed analysis")
            console.print("  2. Address critical and high-risk failure modes")
            console.print("  3. Implement recommended design improvements")
            console.print("  4. Re-run analysis after modifications")

        else:
            console.print("❌ Failed to generate report", style="red")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        if verbose:
            import traceback

            console.print(traceback.format_exc(), style="dim red")


if __name__ == "__main__":
    main()
