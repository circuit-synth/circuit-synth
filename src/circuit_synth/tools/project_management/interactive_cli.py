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

from .project_config import BaseCircuit, ExampleCircuit, ProjectConfig, get_default_config


console = Console()


def display_welcome() -> None:
    """Display welcome banner"""
    welcome_text = Text("🚀 Circuit-Synth Project Setup", style="bold blue")
    console.print(Panel.fit(welcome_text, style="blue"))
    console.print()


def select_base_circuit() -> BaseCircuit:
    """Interactive base circuit selection with rich UI

    Returns:
        Selected BaseCircuit enum value
    """
    console.print("[bold cyan]Select Base Circuit[/bold cyan]")
    console.print()

    # Create options table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Circuit", style="green", width=20)
    table.add_column("Difficulty", style="yellow", width=18)
    table.add_column("Description", width=50)

    circuits = list(BaseCircuit)
    for idx, circuit in enumerate(circuits, 1):
        table.add_row(
            str(idx),
            circuit.display_name,
            circuit.difficulty,
            circuit.description
        )

    console.print(table)
    console.print()

    # Prompt for selection
    choice = Prompt.ask(
        "Select base circuit",
        choices=[str(i) for i in range(1, len(circuits) + 1)],
        default="1"
    )

    selected = circuits[int(choice) - 1]
    console.print(f"✅ Selected: [bold green]{selected.display_name}[/bold green]")
    console.print()

    return selected


def select_examples() -> List[ExampleCircuit]:
    """Interactive example circuits selection (multi-select)

    Returns:
        List of selected ExampleCircuit enum values
    """
    console.print("[bold cyan]Add Optional Example Circuits?[/bold cyan]")
    console.print()
    console.print("Example circuits provide reference implementations for complex designs.")
    console.print("You can select multiple examples or skip this step.")
    console.print()

    # Ask if user wants to add examples
    if not Confirm.ask("Would you like to add example circuits?", default=False):
        console.print("⏭️  Skipping examples")
        console.print()
        return []

    # Create options table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Example", style="green", width=25)
    table.add_column("Difficulty", style="yellow", width=18)
    table.add_column("Description", width=45)

    examples = list(ExampleCircuit)
    for idx, example in enumerate(examples, 1):
        table.add_row(
            str(idx),
            example.display_name,
            example.difficulty,
            example.description
        )

    console.print(table)
    console.print()

    # Prompt for selections
    console.print("[dim]Enter example numbers separated by commas (e.g., 1,3) or press Enter to skip[/dim]")
    selection = Prompt.ask(
        "Select examples",
        default=""
    )

    if not selection.strip():
        console.print("⏭️  No examples selected")
        console.print()
        return []

    # Parse selections
    selected_examples = []
    try:
        indices = [int(x.strip()) for x in selection.split(',')]
        for idx in indices:
            if 1 <= idx <= len(examples):
                selected_examples.append(examples[idx - 1])
            else:
                console.print(f"[yellow]⚠️  Skipping invalid option: {idx}[/yellow]")
    except ValueError:
        console.print("[red]❌ Invalid input format. No examples added.[/red]")
        console.print()
        return []

    if selected_examples:
        console.print(f"✅ Selected {len(selected_examples)} example(s):")
        for ex in selected_examples:
            console.print(f"   • [green]{ex.display_name}[/green]")
    console.print()

    return selected_examples


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
    summary_table.add_row("Base Circuit", config.base_circuit.display_name)

    if config.has_examples():
        examples_list = ", ".join([ex.display_name for ex in config.examples])
        summary_table.add_row("Example Circuits", examples_list)
    else:
        summary_table.add_row("Example Circuits", "[dim]None[/dim]")

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

    # Step 1: Select base circuit
    base_circuit = select_base_circuit()

    # Step 2: Select optional examples
    examples = select_examples()

    # Step 3: Additional configuration
    config_options = select_configuration()

    # Override developer mode if passed as argument
    if developer_mode:
        config_options['developer_mode'] = True

    # Create configuration
    config = ProjectConfig(
        base_circuit=base_circuit,
        examples=examples,
        include_agents=config_options['include_agents'],
        include_kicad_plugins=config_options['include_kicad_plugins'],
        developer_mode=config_options['developer_mode']
    )

    # Step 4: Show summary and confirm
    if not show_confirmation(config, project_path):
        console.print("[yellow]❌ Setup cancelled[/yellow]")
        return None

    return config


def parse_cli_flags(
    base: Optional[str],
    examples: Optional[str],
    no_agents: bool,
    developer: bool
) -> Optional[ProjectConfig]:
    """Parse command-line flags into ProjectConfig

    Args:
        base: Base circuit name (e.g., "resistor", "led", "regulator", "minimal")
        examples: Comma-separated example names (e.g., "esp32,usb")
        no_agents: If True, don't include Claude agents
        developer: If True, enable developer mode

    Returns:
        ProjectConfig if valid, None if invalid flags
    """
    # Map friendly names to enum values
    base_circuit_map = {
        "resistor": BaseCircuit.RESISTOR_DIVIDER,
        "resistor_divider": BaseCircuit.RESISTOR_DIVIDER,
        "led": BaseCircuit.LED_BLINKER,
        "led_blinker": BaseCircuit.LED_BLINKER,
        "regulator": BaseCircuit.VOLTAGE_REGULATOR,
        "voltage_regulator": BaseCircuit.VOLTAGE_REGULATOR,
        "minimal": BaseCircuit.MINIMAL,
        "empty": BaseCircuit.MINIMAL
    }

    example_circuit_map = {
        "esp32": ExampleCircuit.ESP32_DEV_BOARD,
        "esp32_dev_board": ExampleCircuit.ESP32_DEV_BOARD,
        "stm32": ExampleCircuit.STM32_MINIMAL,
        "stm32_minimal": ExampleCircuit.STM32_MINIMAL,
        "usb": ExampleCircuit.USB_C_BASIC,
        "usb_c": ExampleCircuit.USB_C_BASIC,
        "usb_c_basic": ExampleCircuit.USB_C_BASIC,
        "power": ExampleCircuit.POWER_SUPPLY,
        "power_supply": ExampleCircuit.POWER_SUPPLY,
        "power_supply_module": ExampleCircuit.POWER_SUPPLY
    }

    # Parse base circuit
    if base:
        base_key = base.lower().strip()
        if base_key not in base_circuit_map:
            console.print(f"[red]❌ Invalid base circuit: {base}[/red]")
            console.print(f"[yellow]Valid options: {', '.join(base_circuit_map.keys())}[/yellow]")
            return None
        base_circuit = base_circuit_map[base_key]
    else:
        base_circuit = BaseCircuit.RESISTOR_DIVIDER  # Default

    # Parse examples
    selected_examples = []
    if examples:
        example_names = [e.strip().lower() for e in examples.split(',')]
        for name in example_names:
            if name not in example_circuit_map:
                console.print(f"[yellow]⚠️  Unknown example: {name} (skipping)[/yellow]")
                console.print(f"[dim]Valid options: {', '.join(example_circuit_map.keys())}[/dim]")
            else:
                selected_examples.append(example_circuit_map[name])

    return ProjectConfig(
        base_circuit=base_circuit,
        examples=selected_examples,
        include_agents=not no_agents,
        include_kicad_plugins=False,
        developer_mode=developer
    )
