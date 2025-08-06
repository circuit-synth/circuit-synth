"""
Memory-Bank CLI Commands

Command-line interface functions for memory-bank system.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .context import ContextManager
from .core import MemoryBankManager

logger = logging.getLogger(__name__)


def switch_board(board_name: str, project_root: Optional[str] = None) -> bool:
    """Switch to specific PCB board context.

    Args:
        board_name: Name of the board to switch to
        project_root: Project root directory (defaults to current directory)

    Returns:
        True if successful, False otherwise
    """
    context_manager = ContextManager(project_root)
    return context_manager.switch_board(board_name)


def list_boards(project_root: Optional[str] = None) -> List[str]:
    """List all available boards in the project.

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        List of board names
    """
    context_manager = ContextManager(project_root)
    return context_manager.list_available_boards()


def get_current_context(project_root: Optional[str] = None) -> Dict[str, Any]:
    """Get current context status information.

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        Dictionary with context status information
    """
    context_manager = ContextManager(project_root)
    return context_manager.get_context_status()


def init_memory_bank(
    project_name: str,
    board_names: Optional[List[str]] = None,
    project_root: Optional[str] = None,
) -> bool:
    """Initialize memory-bank system for a project.

    Args:
        project_name: Name of the project
        board_names: List of board names (optional)
        project_root: Project root directory (defaults to current directory)

    Returns:
        True if successful, False otherwise
    """
    manager = MemoryBankManager(project_root)

    # Use default board name if none provided
    if not board_names:
        default_board = f"{project_name.lower().replace(' ', '-')}-v1"
        board_names = [default_board]

    success = manager.create_project_structure(project_name, board_names)

    if success:
        print(f"✅ Memory-bank system initialized for '{project_name}'")
        print(f"📁 Created project structure with {len(board_names)} board(s)")
        for board in board_names:
            print(f"   - pcbs/{board}/")
        print("📋 Generated CLAUDE.md with memory-bank documentation")
        print("🚀 Ready to use cs-switch-board and automatic documentation!")
    else:
        print("❌ Failed to initialize memory-bank system")

    return success


def add_board(board_name: str, project_root: Optional[str] = None) -> bool:
    """Add a new board to existing memory-bank project.

    Args:
        board_name: Name of the new board
        project_root: Project root directory (defaults to current directory)

    Returns:
        True if successful, False otherwise
    """
    manager = MemoryBankManager(project_root)

    if not manager.is_memory_bank_enabled():
        print("❌ Memory-bank not enabled. Run 'cs-memory-bank-init' first.")
        return False

    success = manager.add_board(board_name)

    if success:
        print(f"✅ Added board: {board_name}")
        print(f"📁 Created pcbs/{board_name}/ with memory-bank structure")
        print(f"🔄 Use 'cs-switch-board {board_name}' to work on this board")
    else:
        print(f"❌ Failed to add board: {board_name}")

    return success


def remove_memory_bank(project_root: Optional[str] = None) -> bool:
    """Remove memory-bank system from project.

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        True if successful, False otherwise
    """
    manager = MemoryBankManager(project_root)

    if not manager.is_memory_bank_enabled():
        print("ℹ️  Memory-bank not currently enabled")
        return True

    success = manager.remove_memory_bank()

    if success:
        print("✅ Memory-bank system disabled")
        print("📁 Memory-bank directories preserved (not deleted)")
        print("ℹ️  Use 'cs-memory-bank-init' to re-enable")
    else:
        print("❌ Failed to remove memory-bank system")

    return success


def get_memory_bank_status(project_root: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive memory-bank status information.

    Args:
        project_root: Project root directory (defaults to current directory)

    Returns:
        Dictionary with status information
    """
    manager = MemoryBankManager(project_root)
    context_manager = ContextManager(project_root)

    # Get basic status
    status = {
        "enabled": manager.is_memory_bank_enabled(),
        "config": manager.get_config(),
        "context": context_manager.get_context_status(),
    }

    # Print status information
    print("🧠 Memory-Bank System Status")
    print("=" * 30)

    if status["enabled"]:
        config = status["config"]
        print(f"✅ Status: Enabled")
        print(f"📋 Project: {config.get('project_name', 'Unknown')}")
        print(f"📁 Boards: {len(config.get('boards', []))}")

        for board in config.get("boards", []):
            print(f"   - {board}")

        print(f"📅 Created: {config.get('created', 'Unknown')}")
    else:
        print("❌ Status: Disabled")
        print("ℹ️  Run 'cs-memory-bank-init' to enable")

    print("\n🔄 Context Information")
    print("-" * 25)

    context_status = status["context"]
    if context_status["has_context"]:
        print(f"📍 Current Board: {context_status['current_board']}")
        print(f"📁 Available Boards: {context_status['total_boards']}")

        if context_status.get("memory_bank_exists"):
            print("✅ Memory-bank files: Found")
        else:
            print("⚠️  Memory-bank files: Missing")
    else:
        print("⚠️  No active board context")
        if context_status["available_boards"]:
            print(
                f"📁 Available boards: {', '.join(context_status['available_boards'])}"
            )
            print("💡 Use 'cs-switch-board <board-name>' to set context")
        else:
            print("📁 No boards found")

    return status


def search_memory_bank(
    query: str, board_name: Optional[str] = None, project_root: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search memory-bank content for specific terms.

    Args:
        query: Search query string
        board_name: Specific board to search (optional, searches current board if None)
        project_root: Project root directory (defaults to current directory)

    Returns:
        List of search results with file paths and matching content
    """
    results = []
    project_path = Path(project_root) if project_root else Path.cwd()

    # Determine search scope
    if board_name:
        search_paths = [project_path / "pcbs" / board_name / "memory-bank"]
    else:
        # Search current board context
        context_manager = ContextManager(project_root)
        current_memory_bank = context_manager.get_current_memory_bank_path()
        if current_memory_bank:
            search_paths = [current_memory_bank]
        else:
            # Search all boards
            pcbs_dir = project_path / "pcbs"
            search_paths = []
            if pcbs_dir.exists():
                for board_dir in pcbs_dir.iterdir():
                    if board_dir.is_dir():
                        memory_bank = board_dir / "memory-bank"
                        if memory_bank.exists():
                            search_paths.append(memory_bank)

    # Search through files
    query_lower = query.lower()

    for search_path in search_paths:
        if not search_path.exists():
            continue

        for md_file in search_path.glob("*.md"):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find matching lines
                matching_lines = []
                lines = content.split("\n")

                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        # Include some context
                        start = max(0, i - 1)
                        end = min(len(lines), i + 2)
                        context_lines = lines[start:end]

                        matching_lines.append(
                            {
                                "line_number": i + 1,
                                "line": line.strip(),
                                "context": context_lines,
                            }
                        )

                if matching_lines:
                    results.append(
                        {
                            "file": str(md_file),
                            "board": (
                                search_path.parent.name
                                if "pcbs" in search_path.parts
                                else "project"
                            ),
                            "matches": matching_lines,
                        }
                    )

            except Exception as e:
                logger.debug(f"Error searching {md_file}: {e}")

    # Print results
    if results:
        print(f"🔍 Found {len(results)} file(s) matching '{query}'")
        print("=" * 50)

        for result in results:
            print(f"\n📁 {result['file']}")
            print(f"📋 Board: {result['board']}")

            for match in result["matches"][:3]:  # Show first 3 matches per file
                print(f"   Line {match['line_number']}: {match['line']}")

            if len(result["matches"]) > 3:
                print(f"   ... and {len(result['matches']) - 3} more matches")
    else:
        print(f"🔍 No results found for '{query}'")

    return results
