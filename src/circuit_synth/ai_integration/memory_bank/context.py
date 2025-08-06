"""
Context Management for Memory-Bank System

Handles context switching between different PCBs and agent configurations.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context switching between PCB variants."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize with project root directory."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.context_file = self.project_root / ".circuit-synth-context.json"

    def switch_board(self, board_name: str) -> bool:
        """Switch context to specific PCB board."""
        try:
            # Validate board exists
            board_path = self.project_root / "pcbs" / board_name
            if not board_path.exists():
                logger.error(f"Board '{board_name}' not found in pcbs/ directory")
                return False

            # Validate board has .claude configuration
            claude_dir = board_path / ".claude"
            if not claude_dir.exists():
                logger.warning(f"Board '{board_name}' missing .claude configuration")
                # Create basic .claude structure
                self._create_basic_claude_config(claude_dir, board_name)

            # Update context file
            context = {
                "current_project": str(self.project_root),
                "current_pcb": board_name,
                "pcb_path": str(board_path),
                "claude_config_path": str(claude_dir),
                "memory_bank_path": str(board_path / "memory-bank"),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
            }

            with open(self.context_file, "w") as f:
                json.dump(context, f, indent=2)

            logger.info(f"🔄 Switched to board: {board_name}")
            logger.info(f"📋 Claude config: pcbs/{board_name}/.claude/")
            logger.info(f"🧠 Memory-bank: pcbs/{board_name}/memory-bank/")

            return True

        except Exception as e:
            logger.error(f"Failed to switch to board '{board_name}': {e}")
            return False

    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get current context information."""
        if not self.context_file.exists():
            return None

        try:
            with open(self.context_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read context file: {e}")
            return None

    def get_current_board(self) -> Optional[str]:
        """Get currently active board name."""
        context = self.get_current_context()
        return context.get("current_pcb") if context else None

    def get_current_memory_bank_path(self) -> Optional[Path]:
        """Get path to current board's memory-bank."""
        context = self.get_current_context()
        if context and "memory_bank_path" in context:
            return Path(context["memory_bank_path"])
        return None

    def list_available_boards(self) -> List[str]:
        """List all available boards in the project."""
        pcbs_dir = self.project_root / "pcbs"
        if not pcbs_dir.exists():
            return []

        boards = []
        for item in pcbs_dir.iterdir():
            if item.is_dir():
                boards.append(item.name)

        return sorted(boards)

    def get_context_status(self) -> Dict[str, Any]:
        """Get comprehensive context status information."""
        context = self.get_current_context()
        available_boards = self.list_available_boards()

        status = {
            "has_context": context is not None,
            "current_board": context.get("current_pcb") if context else None,
            "available_boards": available_boards,
            "total_boards": len(available_boards),
            "context_file_exists": self.context_file.exists(),
            "project_root": str(self.project_root),
        }

        if context:
            status.update(
                {
                    "pcb_path": context.get("pcb_path"),
                    "memory_bank_path": context.get("memory_bank_path"),
                    "claude_config_path": context.get("claude_config_path"),
                    "last_updated": context.get("last_updated"),
                }
            )

            # Check if paths exist
            if "pcb_path" in context:
                status["pcb_path_exists"] = Path(context["pcb_path"]).exists()
            if "memory_bank_path" in context:
                status["memory_bank_exists"] = Path(
                    context["memory_bank_path"]
                ).exists()
            if "claude_config_path" in context:
                status["claude_config_exists"] = Path(
                    context["claude_config_path"]
                ).exists()

        return status

    def clear_context(self) -> bool:
        """Clear current context (reset to project level)."""
        try:
            if self.context_file.exists():
                self.context_file.unlink()

            logger.info("🔄 Cleared board context - working at project level")
            return True

        except Exception as e:
            logger.error(f"Failed to clear context: {e}")
            return False

    def _create_basic_claude_config(self, claude_dir: Path, board_name: str):
        """Create basic .claude configuration for a board."""
        try:
            claude_dir.mkdir(exist_ok=True)

            # Create basic instructions
            instructions_content = f"""# {board_name} Board Agent

Working on {board_name} PCB variant.

## Memory-Bank Integration
- Update memory-bank files in ./memory-bank/
- Track decisions, fabrication, testing, timeline, issues
- Automatic updates on git commits

## Context  
- Board: {board_name}
- Files: ./{board_name}.kicad_sch, ./{board_name}.kicad_pcb
- Memory-bank: ./memory-bank/
"""

            instructions_path = claude_dir / "instructions.md"
            with open(instructions_path, "w") as f:
                f.write(instructions_content)

            logger.info(f"Created basic .claude config for {board_name}")

        except Exception as e:
            logger.error(f"Failed to create .claude config: {e}")

    def auto_detect_board(self) -> Optional[str]:
        """Auto-detect board based on current working directory."""
        cwd = Path.cwd()

        # Check if we're in a board directory
        if cwd.parent.name == "pcbs" and (cwd / ".claude").exists():
            return cwd.name

        # Check if we're in a subdirectory of a board
        current = cwd
        while current != current.parent:
            if current.parent.name == "pcbs" and (current / ".claude").exists():
                return current.name
            current = current.parent

        return None

    def ensure_context(self) -> bool:
        """Ensure we have a valid context, auto-detecting if needed."""
        # Check if we already have valid context
        context = self.get_current_context()
        if context and context.get("current_pcb"):
            board_path = Path(context.get("pcb_path", ""))
            if board_path.exists():
                return True

        # Try auto-detection
        detected_board = self.auto_detect_board()
        if detected_board:
            logger.info(f"Auto-detected board: {detected_board}")
            return self.switch_board(detected_board)

        # No context available
        return False
