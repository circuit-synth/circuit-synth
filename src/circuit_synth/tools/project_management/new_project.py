#!/usr/bin/env python3
"""
Circuit-Synth New Project Setup Tool

Creates a complete circuit-synth project with:
- Claude AI agents registration (.claude/ directory)
- Example circuits (main.py + simple examples)
- Project README with usage guide
- KiCad installation verification
- Optional KiCad library setup
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

# Import circuit-synth modules
from circuit_synth.ai_integration.claude import register_circuit_agents
from circuit_synth.core.kicad_validator import validate_kicad_installation

# Import new interactive CLI modules
from .interactive_cli import parse_cli_flags, run_interactive_setup
from .project_config import get_default_config
from .template_manager import CLAUDEMDGenerator, READMEGenerator, TemplateManager

console = Console()


def _claude_tooling_summary(project_path: Path) -> str:
    """One-line tally of the AI tooling installed under ``.claude/``.

    Counts skills (``.claude/skills/*/SKILL.md``) as well as agents and commands.
    Earlier this listed only agents + commands -- both empty ``.gitkeep`` dirs in the
    default scaffold -- so a user saw "0 agents, 0 commands" and wrongly concluded no
    AI tooling was installed, even though the design-circuit skill ships (finding F1).
    """
    claude_dir = project_path / ".claude"
    skill_files = sorted((claude_dir / "skills").glob("*/SKILL.md"))
    skills = [p.parent.name for p in skill_files]
    agents_count = len(list((claude_dir / "agents").rglob("*.md")))
    commands_count = len(list((claude_dir / "commands").rglob("*.md")))

    if skills:
        skills_part = f"{len(skills)} skill{'s' if len(skills) != 1 else ''} " + (
            f"({', '.join(skills)})"
        )
    else:
        skills_part = "0 skills"
    return f"{skills_part}, {agents_count} agents, {commands_count} commands"


def create_claude_directory_from_templates(
    project_path: Path, developer_mode: bool = False
) -> None:
    """Install the project's AI tooling from the packaged example_project template.

    Copies the ``.claude/`` tree (skills / agents / commands), the ``.mcp.json``
    MCP-server config, and the ``tools/`` helpers into the new project. This
    packaged template is the single source of truth and works for both editable
    and wheel installs.

    Args:
        project_path: Target project directory
        developer_mode: If True, keep contributor agents and dev commands
    """
    circuit_synth_dir = Path(__file__).parent.parent.parent  # -> circuit_synth/
    template_root = circuit_synth_dir / "data" / "templates" / "example_project"
    template_claude_dir = template_root / ".claude"
    dest_claude_dir = project_path / ".claude"

    console.print("Setting up Claude Code integration from template...", style="blue")

    if not template_claude_dir.exists():
        # This is a packaging bug, not normal operation: the installed
        # circuit-synth is missing its bundled template data.
        console.print(
            f"PACKAGING ERROR: template .claude not found at "
            f"{template_claude_dir}. The installed circuit-synth is missing its "
            f"packaged template data (data/templates/example_project/.claude).",
            style="red",
        )
        dest_claude_dir.mkdir(parents=True, exist_ok=True)
        return

    try:
        # 1. Copy the .claude tree (skills / agents / commands).
        if dest_claude_dir.exists():
            shutil.rmtree(dest_claude_dir)
        shutil.copytree(template_claude_dir, dest_claude_dir)

        # 2. Copy sibling helpers that belong at the project root.
        mcp_src = template_root / ".mcp.json"
        if mcp_src.exists():
            shutil.copy2(mcp_src, project_path / ".mcp.json")
        tools_src = template_root / "tools"
        if tools_src.is_dir():
            dest_tools = project_path / "tools"
            if dest_tools.exists():
                shutil.rmtree(dest_tools)
            shutil.copytree(tools_src, dest_tools)

        # 3. Developer-mode filtering: end users don't get dev-only material.
        if not developer_mode:
            for sub in ("commands/development", "commands/setup", "agents/development"):
                d = dest_claude_dir / sub
                if d.exists():
                    shutil.rmtree(d)

        # 4. Internal-only file, never shipped to user projects.
        mcp_settings_file = dest_claude_dir / "mcp_settings.json"
        if mcp_settings_file.exists():
            mcp_settings_file.unlink()

        # 5. Report exactly what installed.
        skills_count = len(list((dest_claude_dir / "skills").rglob("SKILL.md")))
        agents_count = len(list((dest_claude_dir / "agents").rglob("*.md")))
        commands_count = len(list((dest_claude_dir / "commands").rglob("*.md")))
        console.print(f"Skills available: {skills_count}", style="green")
        console.print(f"Agents available: {agents_count}", style="green")
        console.print(f"Commands available: {commands_count}", style="green")
        console.print(
            f"Created project-local .claude in {dest_claude_dir}", style="blue"
        )
        if (project_path / ".mcp.json").exists():
            console.print(
                "Enable schematic MCP tools with: uv add mcp-kicad-sch-api",
                style="cyan",
            )

    except Exception as e:
        console.print(
            f"Could not install Claude setup from template: {e}", style="yellow"
        )


def copy_complete_claude_setup(
    project_path: Path, developer_mode: bool = False
) -> None:
    """Install the project's .claude setup, MCP config, and tool helpers.

    Thin wrapper over :func:`create_claude_directory_from_templates`, which reads
    from the packaged example_project template (the only source that works for
    both editable and wheel installs).
    """
    create_claude_directory_from_templates(project_path, developer_mode)


def check_kicad_installation() -> Dict[str, Any]:
    """Check KiCad installation and return path info (cross-platform)"""
    console.print("Checking KiCad installation...", style="yellow")

    try:
        result = validate_kicad_installation()

        # Check if KiCad CLI is available (main requirement)
        if result.get("cli_available", False):
            console.print("KiCad found!", style="green")
            console.print(f"   CLI Path: {result.get('cli_path', 'Unknown')}")
            console.print(f"   Version: {result.get('cli_version', 'Unknown')}")

            # Check libraries
            if result.get("libraries_available", False):
                console.print(
                    f"   Symbol libraries: {result.get('symbol_path', 'Not found')}"
                )
                console.print(
                    f"   Footprint libraries: {result.get('footprint_path', 'Not found')}"
                )
            else:
                console.print(
                    "   Libraries not found but CLI available", style="yellow"
                )

            result["kicad_installed"] = True
            return result
        else:
            console.print("KiCad not found", style="red")
            console.print("Install options:", style="cyan")

            # Cross-platform installation suggestions
            if sys.platform == "darwin":  # macOS
                console.print("   • Download: https://www.kicad.org/download/macos/")
                console.print("   • Homebrew: brew install kicad")
            elif sys.platform == "win32":  # Windows
                console.print("   • Download: https://www.kicad.org/download/windows/")
                console.print("   • Chocolatey: choco install kicad")
                console.print("   • Winget: winget install KiCad.KiCad")
            else:  # Linux
                console.print("   • Download: https://www.kicad.org/download/linux/")
                console.print("   • Ubuntu/Debian: sudo apt install kicad")
                console.print("   • Fedora: sudo dnf install kicad")
                console.print("   • Arch: sudo pacman -S kicad")

            result["kicad_installed"] = False
            return result

    except Exception as e:
        console.print(f"Could not verify KiCad installation: {e}", style="yellow")
        return {"kicad_installed": False, "error": str(e)}


def copy_example_project_template(project_path: Path) -> bool:
    """Copy the entire example_project template to the target project directory

    Returns:
        bool: True if template was successfully copied, False otherwise
    """

    # Find the project template in the package data directory
    circuit_synth_dir = Path(
        __file__
    ).parent.parent.parent  # Get to circuit_synth directory
    template_dir = circuit_synth_dir / "data" / "templates" / "example_project"

    # Fallback: check for example_project in repo root (for development)
    if not template_dir.exists():
        circuit_synth_root = Path(__file__).parent.parent.parent.parent
        fallback_template = circuit_synth_root / "example_project"
        if fallback_template.exists():
            template_dir = fallback_template

    if not template_dir.exists():
        console.print(
            f"Project template not found at {template_dir}", style="yellow"
        )
        console.print("Falling back to basic project creation", style="yellow")
        return False

    console.print(
        f"Copying complete project template from {template_dir}", style="blue"
    )

    try:
        # Copy all files and directories from template to project_path
        for item in template_dir.iterdir():
            if item.is_file():
                # Copy individual files
                dest_file = project_path / item.name
                shutil.copy2(item, dest_file)
                console.print(f"   Copied {item.name}", style="green")
            elif item.is_dir():
                # Copy entire directories
                dest_dir = project_path / item.name
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(item, dest_dir)
                console.print(f"   Copied {item.name}/ directory", style="green")

        console.print("Complete project template copied successfully", style="green")
        console.print(
            "   Ready-to-use ESP32-C6 development board example included!",
            style="cyan",
        )
        console.print(
            "   Claude Code agents and commands included from template!",
            style="cyan",
        )
        return True

    except Exception as e:
        console.print(f"Could not copy project template: {e}", style="yellow")
        console.print(
            "Project setup will continue without template files", style="yellow"
        )
        return False


@click.command()
@click.option("--skip-kicad-check", is_flag=True, help="Skip KiCad installation check")
@click.option("--quick", is_flag=True, help="Quick start with defaults (no prompts)")
@click.option(
    "--circuits", type=str, help="Comma-separated circuits: resistor,led,esp32,usb"
)
@click.option("--no-agents", is_flag=True, help="Skip Claude AI agents setup")
@click.option("--developer", is_flag=True, help="Include developer tools")
def main(
    skip_kicad_check: bool,
    quick: bool,
    circuits: Optional[str],
    no_agents: bool,
    developer: bool,
):
    """Setup circuit-synth in the current uv project directory

    Run this command from within your uv project directory after:
    1. uv init my-project
    2. cd my-project
    3. uv add circuit-synth
    4. uv run cs-new-project

    Examples:
        # Interactive mode (default) - shows menu to select circuits
        uv run cs-new-project

        # Quick start with defaults (resistor divider)
        uv run cs-new-project --quick

        # Select specific circuits via flags
        uv run cs-new-project --circuits resistor,led,esp32

        # Minimal project without Claude agents
        uv run cs-new-project --circuits minimal --no-agents
    """

    # Use current directory as project path
    project_path = Path.cwd()

    # Remove default main.py created by uv init (we don't need it)
    default_main = project_path / "main.py"
    if default_main.exists():
        default_main.unlink()

    # Step 1: Check KiCad installation (unless skipped)
    kicad_installed = False
    if not skip_kicad_check:
        kicad_info = check_kicad_installation()
        kicad_installed = kicad_info.get("kicad_installed", False)
        if not kicad_installed:
            if not Confirm.ask(
                "Continue without KiCad? (You'll need it later for opening projects)"
            ):
                console.print("Aborted - Please install KiCad first", style="red")
                sys.exit(1)

    # Step 2: Determine project configuration
    config = None

    if quick:
        # Quick mode: use defaults, no prompts
        console.print("[bold cyan]Quick Start Mode[/bold cyan]")
        config = get_default_config()
        if developer:
            config.developer_mode = True
        console.print(
            f"Creating project with: [green]{', '.join([c.display_name for c in config.circuits])}[/green]"
        )
        console.print()

    elif circuits or no_agents:
        # Flag-based mode: parse flags into configuration
        config = parse_cli_flags(circuits, no_agents, developer)
        if config is None:
            sys.exit(1)  # parse_cli_flags already printed error

    else:
        # Interactive mode: run interactive CLI
        config = run_interactive_setup(project_path, developer_mode=developer)
        if config is None:
            console.print("[yellow]Setup cancelled by user[/yellow]")
            sys.exit(0)

    # Step 3: Initialize template manager and generators
    template_mgr = TemplateManager()
    readme_gen = READMEGenerator()
    claude_md_gen = CLAUDEMDGenerator()

    # Step 4: Create circuit-synth directory and copy all selected circuits
    console.print("\n[bold cyan]Creating Project Files...[/bold cyan]")

    if config.has_circuits():
        for idx, circuit in enumerate(config.circuits):
            try:
                # First circuit becomes main.py, others use their own names
                is_first = idx == 0
                template_mgr.copy_circuit_to_project(
                    circuit, project_path, is_first=is_first
                )

                if is_first:
                    console.print(
                        f"Created circuit-synth/main.py ({circuit.display_name})",
                        style="green",
                    )
                else:
                    console.print(
                        f"Created circuit-synth/{circuit.value}.py ({circuit.display_name})",
                        style="green",
                    )

            except FileNotFoundError as e:
                console.print(
                    f"[yellow]Could not add {circuit.display_name}: {e}[/yellow]"
                )
    else:
        console.print(
            "[yellow]No circuits selected. Creating empty project.[/yellow]"
        )

    # Step 6: Setup Claude AI agents if requested
    if config.include_agents:
        console.print("\n[cyan]Setting up Claude Code integration...[/cyan]")
        try:
            copy_complete_claude_setup(
                project_path, developer_mode=config.developer_mode
            )
            console.print(
                f"Claude Code setup complete ({_claude_tooling_summary(project_path)})",
                style="green",
            )
        except Exception as e:
            console.print(f"[yellow]Could not setup Claude agents: {e}[/yellow]")
    else:
        console.print("\n[dim]Skipped Claude agents setup[/dim]")

    # Step 7: Generate README.md and CLAUDE.md
    console.print("\n[cyan]Generating documentation...[/cyan]")

    readme_content = readme_gen.generate(config, project_path)
    readme_path = project_path / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    console.print("Created README.md", style="green")

    claude_md_content = claude_md_gen.generate(config)
    claude_md_path = project_path / "CLAUDE.md"
    claude_md_path.write_text(claude_md_content, encoding="utf-8")
    console.print("Created CLAUDE.md", style="green")

    # Step 8: KiCad plugins note (if KiCad is installed)
    if kicad_installed:
        console.print("\n[cyan]KiCad plugins available separately[/cyan]")
        console.print(
            "[dim]   Run 'uv run cs-setup-kicad-plugins' to install AI integration plugins[/dim]"
        )

    # Success message
    console.print()
    success_text = Text(
        f"Circuit-synth project setup complete!", style="bold green"
    ) + Text(f"\n\nLocation: {project_path}")

    if config.has_circuits():
        circuits_names = ", ".join([c.display_name for c in config.circuits])
        success_text += Text(
            f"\nCircuits ({len(config.circuits)}): {circuits_names}"
        )

    success_text += Text(
        f"\n\nGet started: [cyan]uv run python circuit-synth/main.py[/cyan]"
    )
    success_text += Text(f"\nDocumentation: See README.md")

    if config.has_circuits():
        success_text += Text(
            f"\nManufacturing: Templates auto-generate BOM and PDF"
        )

    if config.include_agents:
        success_text += Text(
            f"\nAI tooling: {_claude_tooling_summary(project_path)}"
        )

    console.print(Panel.fit(success_text, title="Success!", style="green"))


if __name__ == "__main__":
    main()
