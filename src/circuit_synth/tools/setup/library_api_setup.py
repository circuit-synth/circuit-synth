"""
CLI tools for setting up library API credentials
"""

from pathlib import Path

import click

from circuit_synth.kicad.library_sourcing.config import LibrarySourceConfig
from circuit_synth.kicad.library_sourcing.models import LibrarySource


@click.command()
@click.argument("api_key")
def setup_snapeda_api(api_key: str):
    """Setup SnapEDA API credentials"""

    config = LibrarySourceConfig()
    config.update_api_credentials(LibrarySource.SNAPEDA, api_key=api_key, enabled=True)

    click.echo(f"✅ SnapEDA API configured successfully")
    click.echo(f"Config saved to: {config.config_file}")


@click.command()
@click.argument("api_key")
@click.argument("client_id")
def setup_digikey_api(api_key: str, client_id: str):
    """Setup DigiKey API credentials"""

    config = LibrarySourceConfig()
    config.update_api_credentials(
        LibrarySource.DIGIKEY_API, api_key=api_key, client_id=client_id, enabled=True
    )

    click.echo(f"✅ DigiKey API configured successfully")
    click.echo(f"Config saved to: {config.config_file}")


@click.command()
def show_library_setup():
    """Show library sourcing setup instructions"""

    config = LibrarySourceConfig()
    instructions = config.setup_wizard()

    click.echo(instructions)


if __name__ == "__main__":
    show_library_setup()
