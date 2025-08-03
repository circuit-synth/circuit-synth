"""
Memory-Bank CLI Interface

Command-line interface for memory-bank system commands.
"""

import click
from typing import List, Optional

from .commands import (
    switch_board,
    list_boards,
    get_current_context,
    init_memory_bank,
    add_board,
    remove_memory_bank,
    get_memory_bank_status,
    search_memory_bank
)


@click.command()
@click.argument('board_name', required=False)
@click.option('--list', 'list_boards_flag', is_flag=True, help='List available boards')
@click.option('--status', is_flag=True, help='Show current context status')
def switch_board_cli(board_name: Optional[str], list_boards_flag: bool, status: bool):
    """Switch to specific PCB board context.
    
    Examples:
        cs-switch-board esp32-v1     # Switch to esp32-v1 board
        cs-switch-board --list       # List available boards  
        cs-switch-board --status     # Show current context
    """
    if list_boards_flag:
        boards = list_boards()
        if boards:
            print("📁 Available boards:")
            for board in boards:
                print(f"   - {board}")
            print(f"\n💡 Use 'cs-switch-board <board-name>' to switch context")
        else:
            print("📁 No boards found")
            print("💡 Use 'cs-memory-bank-init' to create a memory-bank project")
        return
    
    if status:
        get_current_context()
        return
    
    if not board_name:
        print("❌ Board name required")
        print("💡 Use 'cs-switch-board --list' to see available boards")
        print("💡 Use 'cs-switch-board <board-name>' to switch context")
        return
    
    success = switch_board(board_name)
    if not success:
        print(f"❌ Failed to switch to board: {board_name}")
        print("💡 Use 'cs-switch-board --list' to see available boards")


@click.command()
@click.argument('project_name')
@click.option('--boards', '-b', multiple=True, help='Board names to create (can be specified multiple times)')
def init_cli(project_name: str, boards: tuple):
    """Initialize memory-bank system for a project.
    
    Examples:
        cs-memory-bank-init "My IoT Project"
        cs-memory-bank-init "Sensor Hub" -b main-v1 -b debug-v1
    """
    board_list = list(boards) if boards else None
    init_memory_bank(project_name, board_list)


@click.command()
@click.argument('board_name')
def add_board_cli(board_name: str):
    """Add a new board to existing memory-bank project.
    
    Examples:
        cs-memory-bank-add-board sensor-v2
    """
    add_board(board_name)


@click.command()
def remove_cli():
    """Remove memory-bank system from current project."""
    remove_memory_bank()


@click.command()
def status_cli():
    """Show comprehensive memory-bank status."""
    get_memory_bank_status()


@click.command()
@click.argument('query')
@click.option('--board', '-b', help='Search specific board (default: current board or all boards)')
def search_cli(query: str, board: Optional[str]):
    """Search memory-bank content for specific terms.
    
    Examples:
        cs-memory-bank-search "voltage regulator"
        cs-memory-bank-search "USB" --board esp32-v1
    """
    search_memory_bank(query, board)