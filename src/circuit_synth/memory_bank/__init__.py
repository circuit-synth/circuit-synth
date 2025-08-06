"""
Circuit Memory-Bank System

Automatic engineering documentation and project knowledge preservation for PCB design.
"""

from .commands import (
    get_current_context,
    get_memory_bank_status,
    init_memory_bank,
    list_boards,
    remove_memory_bank,
    search_memory_bank,
    switch_board,
)
from .context import ContextManager
from .core import MemoryBankManager, MemoryBankUpdater
from .git_integration import (
    GitHookManager,
    get_commit_info,
    is_git_repository,
    update_memory_bank_from_commit,
)
from .templates import (
    DECISIONS_TEMPLATE,
    FABRICATION_TEMPLATE,
    ISSUES_TEMPLATE,
    TESTING_TEMPLATE,
    TIMELINE_TEMPLATE,
    generate_claude_md,
)

__all__ = [
    "MemoryBankManager",
    "MemoryBankUpdater",
    "ContextManager",
    "GitHookManager",
    "switch_board",
    "list_boards",
    "get_current_context",
    "init_memory_bank",
    "remove_memory_bank",
    "get_memory_bank_status",
    "search_memory_bank",
    "update_memory_bank_from_commit",
    "get_commit_info",
    "is_git_repository",
    "DECISIONS_TEMPLATE",
    "FABRICATION_TEMPLATE",
    "TESTING_TEMPLATE",
    "TIMELINE_TEMPLATE",
    "ISSUES_TEMPLATE",
    "generate_claude_md",
]
