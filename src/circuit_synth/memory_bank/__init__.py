"""
Circuit Memory-Bank System

Automatic engineering documentation and project knowledge preservation for PCB design.
"""

from .core import MemoryBankManager, MemoryBankUpdater
from .templates import (
    DECISIONS_TEMPLATE,
    FABRICATION_TEMPLATE,
    TESTING_TEMPLATE,
    TIMELINE_TEMPLATE,
    ISSUES_TEMPLATE,
    generate_claude_md
)
from .context import ContextManager
from .commands import (
    switch_board,
    list_boards,
    get_current_context,
    init_memory_bank,
    remove_memory_bank,
    get_memory_bank_status,
    search_memory_bank
)
from .git_integration import (
    GitHookManager,
    update_memory_bank_from_commit,
    get_commit_info,
    is_git_repository
)

__all__ = [
    'MemoryBankManager',
    'MemoryBankUpdater',
    'ContextManager',
    'GitHookManager',
    'switch_board',
    'list_boards', 
    'get_current_context',
    'init_memory_bank',
    'remove_memory_bank',
    'get_memory_bank_status',
    'search_memory_bank',
    'update_memory_bank_from_commit',
    'get_commit_info',
    'is_git_repository',
    'DECISIONS_TEMPLATE',
    'FABRICATION_TEMPLATE',
    'TESTING_TEMPLATE',
    'TIMELINE_TEMPLATE',
    'ISSUES_TEMPLATE', 
    'generate_claude_md'
]