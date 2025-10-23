"""
Interactive CLI for cs-new-project

Provides rich, user-friendly interactive prompts for project configuration.
"""

from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .project_config import Circuit, ProjectConfig, get_default_config


console = Console()


def display_welcome() -> None:
    """Display welcome banner"""
    welcome_text = Text("🚀 Circuit-Synth Project Setup", style="bold blue")
    console.print(Panel.fit(welcome_text, style="blue"))
    console.print()


def select_circuits() -> List[Circuit]:
    """Interactive circuit selection with multi-select

    Returns:
        List of selected Circuit enum values
    """
    console.print("[bold cyan]Select Circuit Templates[/bold cyan]")
    console.print()
    console.print("Choose which circuits to include in your project.")
    console.print("You can select multiple circuits by entering comma-separated numbers (e.g., 1,2,5)")
    console.print()

    # Create options table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Circuit", style="green")
    table.add_column("Description")

    circuits = list(Circuit)
    for idx, circuit in enumerate(circuits, 1):
        table.add_row(
            str(idx),
            circuit.display_name,
            circuit.description
        )

    console.print(table)
    console.print()

    # Prompt for selections
    console.print("[dim]Enter circuit numbers separated by commas, or press Enter for default (Resistor Divider)[/dim]")
    selection = Prompt.ask(
        "Select circuits",
        default="1"  # Default to resistor divider
    )

    # Parse selections
    selected_circuits = []
    try:
        # Split and filter out empty strings (handles trailing commas)
        indices = [int(x.strip()) for x in selection.split(',') if x.strip()]
        for idx in indices:
            if 1 <= idx <= len(circuits):
                selected_circuits.append(circuits[idx - 1])
            else:
                console.print(f"[yellow]⚠️  Skipping invalid option: {idx}[/yellow]")
    except ValueError:
        console.print("[red]❌ Invalid input format. Using default (Resistor Divider)[/red]")
        selected_circuits = [Circuit.RESISTOR_DIVIDER]

    if not selected_circuits:
        console.print("[yellow]⚠️  No circuits selected. Using default (Resistor Divider)[/yellow]")
        selected_circuits = [Circuit.RESISTOR_DIVIDER]

    console.print()
    console.print(f"✅ Selected {len(selected_circuits)} circuit(s):")
    for circuit in selected_circuits:
        console.print(f"   • [green]{circuit.display_name}[/green]")
    console.print()

    return selected_circuits


def select_configuration() -> dict:
    """Select additional configuration options

    Returns:
        Dictionary with configuration settings
    """
    console.print("[bold cyan]Additional Configuration[/bold cyan]")
    console.print()

    config = {}

    # Claude AI agents
    config['include_agents'] = Confirm.ask(
        "Include Claude AI agents for AI-powered design?",
        default=True
    )

    # KiCad plugins (usually not needed for new users)
    config['include_kicad_plugins'] = Confirm.ask(
        "Include KiCad plugin setup?",
        default=False
    )

    # Developer mode
    config['developer_mode'] = Confirm.ask(
        "Developer mode (includes contributor tools)?",
        default=False
    )

    console.print()
    return config


def show_confirmation(config: ProjectConfig, project_path) -> bool:
    """Show configuration summary and confirm

    Args:
        config: Project configuration
        project_path: Project directory path

    Returns:
        True if user confirms, False otherwise
    """
    console.print("[bold cyan]📋 Project Summary[/bold cyan]")
    console.print()

    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Setting", style="cyan", width=20)
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Project Location", str(project_path))

    if config.has_circuits():
        circuits_list = ", ".join([c.display_name for c in config.circuits])
        summary_table.add_row(f"Circuits ({len(config.circuits)})", circuits_list)
    else:
        summary_table.add_row("Circuits", "[dim]None[/dim]")

    summary_table.add_row("Claude AI Agents", "✅ Yes" if config.include_agents else "❌ No")
    summary_table.add_row("KiCad Plugins", "✅ Yes" if config.include_kicad_plugins else "❌ No")

    if config.developer_mode:
        summary_table.add_row("Developer Mode", "✅ Enabled")

    console.print(summary_table)
    console.print()

    return Confirm.ask("✅ Create project with these settings?", default=True)


def run_interactive_setup(project_path, developer_mode: bool = False) -> Optional[ProjectConfig]:
    """Run the complete interactive setup workflow

    Args:
        project_path: Path to project directory
        developer_mode: If True, enable developer mode by default

    Returns:
        ProjectConfig if user completes setup, None if cancelled
    """
    display_welcome()

    # Step 1: Select circuits
    circuits = select_circuits()

    # Step 2: Additional configuration
    config_options = select_configuration()

    # Override developer mode if passed as argument
    if developer_mode:
        config_options['developer_mode'] = True

    # Create configuration
    config = ProjectConfig(
        circuits=circuits,
        include_agents=config_options['include_agents'],
        include_kicad_plugins=config_options['include_kicad_plugins'],
        developer_mode=config_options['developer_mode']
    )

    # Step 3: Show summary and confirm
    if not show_confirmation(config, project_path):
        console.print("[yellow]❌ Setup cancelled[/yellow]")
        return None

    return config


def parse_cli_flags(
    circuits: Optional[str],
    no_agents: bool,
    developer: bool
) -> Optional[ProjectConfig]:
    """Parse command-line flags into ProjectConfig

    Args:
        circuits: Comma-separated circuit names (e.g., "resistor,led,esp32")
        no_agents: If True, don't include Claude agents
        developer: If True, enable developer mode

    Returns:
        ProjectConfig if valid, None if invalid flags
    """
    # Map friendly names to enum values
    circuit_map = {
        # Beginner
        "resistor": Circuit.RESISTOR_DIVIDER,
        "resistor_divider": Circuit.RESISTOR_DIVIDER,
        "led": Circuit.LED_BLINKER,
        "led_blinker": Circuit.LED_BLINKER,
        # Intermediate
        "regulator": Circuit.VOLTAGE_REGULATOR,
        "voltage_regulator": Circuit.VOLTAGE_REGULATOR,
        "usb": Circuit.USB_C_BASIC,
        "usb_c": Circuit.USB_C_BASIC,
        "usb_c_basic": Circuit.USB_C_BASIC,
        "power": Circuit.POWER_SUPPLY,
        "power_supply": Circuit.POWER_SUPPLY,
        "power_supply_module": Circuit.POWER_SUPPLY,
        # Advanced
        "esp32": Circuit.ESP32_DEV_BOARD,
        "esp32_dev_board": Circuit.ESP32_DEV_BOARD,
        "stm32": Circuit.STM32_MINIMAL,
        "stm32_minimal": Circuit.STM32_MINIMAL,
        # Expert
        "minimal": Circuit.MINIMAL,
        "empty": Circuit.MINIMAL
    }

    # Parse circuits
    selected_circuits = []
    if circuits:
        circuit_names = [c.strip().lower() for c in circuits.split(',')]
        for name in circuit_names:
            if name not in circuit_map:
                console.print(f"[yellow]⚠️  Unknown circuit: {name} (skipping)[/yellow]")
                console.print(f"[dim]Valid options: {', '.join(sorted(set(circuit_map.keys())))}[/dim]")
            else:
                selected_circuits.append(circuit_map[name])

    # Use default if no circuits selected
    if not selected_circuits:
        selected_circuits = [Circuit.RESISTOR_DIVIDER]

    return ProjectConfig(
        circuits=selected_circuits,
        include_agents=not no_agents,
        include_kicad_plugins=False,
        developer_mode=developer
    )
