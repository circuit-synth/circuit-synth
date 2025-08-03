"""
Memory-Bank CLI Interface

Command-line interface for memory-bank system commands.
"""

import click
from typing import List, Optional

from .commands import (
    init_memory_bank,
    add_board,
    remove_memory_bank
)


@click.command()
@click.argument('project_name')
def init_cli(project_name: str):
    """Initialize memory-bank system for a PCB project.
    
    Examples:
        cs-memory-bank-init "My IoT Project"
    """
    init_memory_bank(project_name, None)


@click.command()
def remove_cli():
    """Remove memory-bank system from current project."""
    remove_memory_bank()