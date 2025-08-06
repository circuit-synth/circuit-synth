"""
Memory-Bank Core Components

Core classes for managing memory-bank system functionality.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .circuit_diff import CircuitDiffAnalyzer, format_diff_for_memory_bank
from .templates import TEMPLATE_FILES, generate_claude_md

logger = logging.getLogger(__name__)


class MemoryBankManager:
    """Manages memory-bank directory structure and file operations."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize with project root directory."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.memory_bank_config_file = (
            self.project_root / ".circuit-synth-memory-bank-config.json"
        )

    def create_project_structure(
        self, project_name: str, board_names: List[str] = None
    ) -> bool:
        """Create complete memory-bank directory structure for a new project."""
        try:
            board_names = board_names or [
                f"{project_name.lower().replace(' ', '-')}-v1"
            ]

            # Create project-level .claude directory
            project_claude_dir = self.project_root / ".claude"
            project_claude_dir.mkdir(exist_ok=True)

            # Create project-level memory-bank
            project_memory_bank = self.project_root / "memory-bank"
            project_memory_bank.mkdir(exist_ok=True)
            self._create_project_level_files(project_memory_bank)

            # Create pcbs directory
            pcbs_dir = self.project_root / "pcbs"
            pcbs_dir.mkdir(exist_ok=True)

            # Create board-specific structures
            for board_name in board_names:
                self._create_board_structure(pcbs_dir, board_name)

            # Generate CLAUDE.md
            claude_md_content = generate_claude_md(
                project_name=project_name,
                boards=board_names,
                project_specific_instructions=f"This is the {project_name} project with memory-bank system enabled.",
            )

            claude_md_path = self.project_root / "CLAUDE.md"
            with open(claude_md_path, "w") as f:
                f.write(claude_md_content)

            # Create memory-bank configuration
            config = {
                "enabled": True,
                "project_name": project_name,
                "boards": board_names,
                "created": datetime.now().isoformat(),
                "version": "1.0",
            }

            with open(self.memory_bank_config_file, "w") as f:
                json.dump(config, f, indent=2)

            logger.info(f"Created memory-bank structure for project: {project_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create memory-bank structure: {e}")
            return False

    def _create_project_level_files(self, memory_bank_dir: Path):
        """Create project-level memory-bank files."""
        files = {
            "project-overview.md": """# Project Overview

*High-level project status and cross-board insights*

## Project Status
**Current Phase**: Development  
**Active Boards**: List active board variants  
**Key Milestones**: Major project milestones  

---

""",
            "cross-pcb-insights.md": """# Cross-PCB Insights

*Lessons learned and patterns across board variants*

## Design Patterns
**Successful Approaches**: What works well across boards  
**Common Issues**: Problems seen on multiple boards  
**Component Choices**: Parts that perform well consistently  

---

""",
            "vendor-analysis.md": """# Vendor Analysis

*Supplier performance tracking across the project*

## Vendor Performance
**JLCPCB**: Fabrication quality, delivery times, costs  
**Component Suppliers**: Availability, quality, pricing  
**Assembly Services**: Quality, turnaround, cost  

---

""",
            "component-database.md": """# Component Database

*Component performance tracking across projects*

## Component Performance
**Voltage Regulators**: Performance across different boards  
**Microcontrollers**: Success rates, issues, alternatives  
**Passive Components**: Reliable suppliers and specifications  

---

""",
        }

        for filename, content in files.items():
            file_path = memory_bank_dir / filename
            if not file_path.exists():
                with open(file_path, "w") as f:
                    f.write(content)

    def _create_board_structure(self, pcbs_dir: Path, board_name: str):
        """Create directory structure for a specific board."""
        board_dir = pcbs_dir / board_name
        board_dir.mkdir(exist_ok=True)

        # Create .claude directory for board-level agent
        claude_dir = board_dir / ".claude"
        claude_dir.mkdir(exist_ok=True)

        # Create board-level agent instructions
        instructions_content = f"""# {board_name} Board Agent Instructions

You are working on the {board_name} PCB variant.

## Memory-Bank Integration
- Automatically update memory-bank files in ./memory-bank/ 
- Track design decisions in decisions.md
- Log fabrication orders in fabrication.md
- Record test results in testing.md
- Maintain timeline in timeline.md
- Document issues in issues.md

## Context
- Current board: {board_name}
- Memory-bank location: ./memory-bank/
- KiCad files: ./{board_name}.kicad_sch, ./{board_name}.kicad_pcb

## Automatic Documentation
Update memory-bank files when:
- Git commits are made
- Component changes occur
- Tests are performed
- Issues are encountered
"""

        instructions_path = claude_dir / "instructions.md"
        with open(instructions_path, "w") as f:
            f.write(instructions_content)

        # Create memory-bank directory
        memory_bank_dir = board_dir / "memory-bank"
        memory_bank_dir.mkdir(exist_ok=True)

        # Create cache directory
        cache_dir = memory_bank_dir / "cache"
        cache_dir.mkdir(exist_ok=True)

        # Create standard memory-bank files
        for filename, template in TEMPLATE_FILES.items():
            file_path = memory_bank_dir / filename
            if not file_path.exists():
                with open(file_path, "w") as f:
                    f.write(template)

    def add_board(self, board_name: str) -> bool:
        """Add a new board to existing project."""
        try:
            if not self.is_memory_bank_enabled():
                logger.error("Memory-bank not enabled for this project")
                return False

            pcbs_dir = self.project_root / "pcbs"
            if not pcbs_dir.exists():
                pcbs_dir.mkdir()

            self._create_board_structure(pcbs_dir, board_name)

            # Update configuration
            config = self.get_config()
            if config:
                config["boards"].append(board_name)
                config["last_updated"] = datetime.now().isoformat()

                with open(self.memory_bank_config_file, "w") as f:
                    json.dump(config, f, indent=2)

            logger.info(f"Added board: {board_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add board {board_name}: {e}")
            return False

    def remove_memory_bank(self) -> bool:
        """Remove memory-bank system from project."""
        try:
            # Remove configuration file
            if self.memory_bank_config_file.exists():
                self.memory_bank_config_file.unlink()

            # Note: We don't delete the actual memory-bank directories
            # as they may contain valuable data. Just disable the system.

            logger.info("Memory-bank system disabled")
            return True

        except Exception as e:
            logger.error(f"Failed to remove memory-bank: {e}")
            return False

    def is_memory_bank_enabled(self) -> bool:
        """Check if memory-bank is enabled for current project."""
        if not self.memory_bank_config_file.exists():
            return False

        try:
            with open(self.memory_bank_config_file, "r") as f:
                config = json.load(f)
                return config.get("enabled", False)
        except Exception:
            return False

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Get memory-bank configuration."""
        if not self.memory_bank_config_file.exists():
            return None

        try:
            with open(self.memory_bank_config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read config: {e}")
            return None

    def get_boards(self) -> List[str]:
        """Get list of boards in project."""
        config = self.get_config()
        if config:
            return config.get("boards", [])

        # Fallback: scan pcbs directory
        pcbs_dir = self.project_root / "pcbs"
        if pcbs_dir.exists():
            return [d.name for d in pcbs_dir.iterdir() if d.is_dir()]

        return []


class MemoryBankUpdater:
    """Handles automatic updates to memory-bank files."""

    def __init__(self, board_path: str):
        """Initialize for specific board directory."""
        self.board_path = Path(board_path)
        self.memory_bank_path = self.board_path / "memory-bank"

    def update_from_commit(self, commit_hash: str, commit_message: str = "") -> bool:
        """Update memory-bank files based on git commit."""
        try:
            if not self.memory_bank_path.exists():
                logger.warning(f"Memory-bank not found at {self.memory_bank_path}")
                return False

            # Get commit details
            if not commit_message:
                commit_message = self._get_commit_message(commit_hash)

            # Use intelligent circuit diff analysis
            diff_analyzer = CircuitDiffAnalyzer(str(self.board_path))
            circuit_diff = diff_analyzer.analyze_commit_changes(commit_hash)

            # Update appropriate files
            updated_files = []

            # Always update decisions.md if there are significant changes
            if circuit_diff.has_significant_changes():
                if self._update_decisions_file_with_diff(circuit_diff):
                    updated_files.append("decisions.md")

            # Update timeline for milestone-worthy changes
            if self._should_update_timeline_from_diff(circuit_diff):
                if self._update_timeline_file_with_diff(circuit_diff):
                    updated_files.append("timeline.md")

            # Update issues.md if problems are mentioned
            if self._should_update_issues_from_diff(circuit_diff):
                if self._update_issues_file_with_diff(circuit_diff):
                    updated_files.append("issues.md")

            if updated_files:
                logger.info(f"✓ Updated memory-bank files: {', '.join(updated_files)}")
                return True
            else:
                logger.debug(
                    f"No memory-bank updates needed for commit {commit_hash[:7]}"
                )
                return False

        except Exception as e:
            logger.warning(
                f"Memory-bank update failed for commit {commit_hash[:7]}: {e}"
            )
            return False

    def _get_commit_message(self, commit_hash: str) -> str:
        """Get commit message from git."""
        try:
            result = subprocess.run(
                ["git", "log", "--format=%B", "-n", "1", commit_hash],
                capture_output=True,
                text=True,
                cwd=self.board_path,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _analyze_commit_changes(self, commit_hash: str) -> Dict[str, Any]:
        """Analyze what changed in the commit."""
        changes = {
            "files_changed": [],
            "kicad_files": [],
            "python_files": [],
            "has_schematic_changes": False,
            "has_pcb_changes": False,
        }

        try:
            # Get list of changed files
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{commit_hash}~1", commit_hash],
                capture_output=True,
                text=True,
                cwd=self.board_path,
            )

            files = result.stdout.strip().split("\n") if result.stdout.strip() else []
            changes["files_changed"] = files

            for file in files:
                if file.endswith(".kicad_sch"):
                    changes["kicad_files"].append(file)
                    changes["has_schematic_changes"] = True
                elif file.endswith(".kicad_pcb"):
                    changes["kicad_files"].append(file)
                    changes["has_pcb_changes"] = True
                elif file.endswith(".py"):
                    changes["python_files"].append(file)

        except Exception as e:
            logger.debug(f"Failed to analyze commit changes: {e}")

        return changes

    def _should_update_decisions(
        self, changes: Dict[str, Any], commit_message: str
    ) -> bool:
        """Determine if decisions.md should be updated."""
        # Update if there are schematic changes or significant commit message
        return (
            changes["has_schematic_changes"]
            or changes["has_pcb_changes"]
            or len(commit_message) > 20
        )  # Non-trivial commit message

    def _should_update_timeline(
        self, changes: Dict[str, Any], commit_message: str
    ) -> bool:
        """Determine if timeline.md should be updated."""
        # Update for major changes or milestone keywords
        milestone_keywords = ["version", "release", "milestone", "complete", "finished"]
        return changes["has_schematic_changes"] or any(
            keyword in commit_message.lower() for keyword in milestone_keywords
        )

    def _update_decisions_file(
        self, commit_hash: str, commit_message: str, changes: Dict[str, Any]
    ) -> bool:
        """Update decisions.md with commit information."""
        try:
            decisions_file = self.memory_bank_path / "decisions.md"

            # Read existing content
            content = ""
            if decisions_file.exists():
                with open(decisions_file, "r") as f:
                    content = f.read()

            # Create new entry
            date = datetime.now().strftime("%Y-%m-%d")
            entry = f"""
## {date}: {commit_message[:60]}{'...' if len(commit_message) > 60 else ''} (Commit: {commit_hash[:7]})
**Change**: {commit_message}  
**Files Modified**: {', '.join(changes['files_changed'][:5])}{'...' if len(changes['files_changed']) > 5 else ''}  
**Commit**: {commit_hash}  
**Impact**: {'Schematic changes' if changes['has_schematic_changes'] else 'PCB changes' if changes['has_pcb_changes'] else 'Code changes'}  

"""

            # Insert after the template section
            if "---\n\n" in content:
                parts = content.split("---\n\n", 1)
                new_content = parts[0] + "---\n" + entry + "\n" + parts[1]
            else:
                # If no template section, prepend
                new_content = content + entry

            # Write updated content
            with open(decisions_file, "w") as f:
                f.write(new_content)

            return True

        except Exception as e:
            logger.error(f"Failed to update decisions.md: {e}")
            return False

    def _update_timeline_file(
        self, commit_hash: str, commit_message: str, changes: Dict[str, Any]
    ) -> bool:
        """Update timeline.md with milestone information."""
        try:
            timeline_file = self.memory_bank_path / "timeline.md"

            # Read existing content
            content = ""
            if timeline_file.exists():
                with open(timeline_file, "r") as f:
                    content = f.read()

            # Create timeline entry
            date = datetime.now().strftime("%Y-%m-%d")
            entry = f"""
## {date}: {commit_message}
**Status**: Completed  
**Commit**: {commit_hash[:7]}  
**Details**: {'Schematic updates' if changes['has_schematic_changes'] else 'PCB updates' if changes['has_pcb_changes'] else 'Code updates'}  

"""

            # Insert after template section
            if "---\n\n" in content:
                parts = content.split("---\n\n", 1)
                new_content = parts[0] + "---\n" + entry + "\n" + parts[1]
            else:
                new_content = content + entry

            # Write updated content
            with open(timeline_file, "w") as f:
                f.write(new_content)

            return True

        except Exception as e:
            logger.error(f"Failed to update timeline.md: {e}")
            return False

    def _update_decisions_file_with_diff(self, circuit_diff) -> bool:
        """Update decisions.md with intelligent circuit diff analysis."""
        try:
            decisions_file = self.memory_bank_path / "decisions.md"

            # Read existing content
            content = ""
            if decisions_file.exists():
                with open(decisions_file, "r") as f:
                    content = f.read()

            # Generate formatted diff entry
            diff_entry = format_diff_for_memory_bank(circuit_diff)

            # Insert after template section
            if "---\n\n" in content:
                parts = content.split("---\n\n", 1)
                new_content = parts[0] + "---\n\n" + diff_entry + parts[1]
            else:
                new_content = content + "\n" + diff_entry

            # Write updated content
            with open(decisions_file, "w") as f:
                f.write(new_content)

            return True

        except Exception as e:
            logger.error(f"Failed to update decisions.md with diff: {e}")
            return False

    def _update_timeline_file_with_diff(self, circuit_diff) -> bool:
        """Update timeline.md with diff-based milestone information."""
        try:
            timeline_file = self.memory_bank_path / "timeline.md"

            # Read existing content
            content = ""
            if timeline_file.exists():
                with open(timeline_file, "r") as f:
                    content = f.read()

            # Create timeline entry
            date = datetime.now().strftime("%Y-%m-%d")
            commit_msg = (
                circuit_diff.commit_message[:50] + "..."
                if len(circuit_diff.commit_message) > 50
                else circuit_diff.commit_message
            )

            # Determine milestone type
            comp_changes = len(circuit_diff.component_changes)
            net_changes = len(circuit_diff.net_changes)

            if comp_changes > 0 and net_changes > 0:
                milestone_type = "Major Circuit Update"
            elif comp_changes > 0:
                milestone_type = "Component Changes"
            elif net_changes > 0:
                milestone_type = "Net Changes"
            else:
                milestone_type = "Code Update"

            entry = f"""
## {date}: {milestone_type}
**Milestone**: {commit_msg}  
**Status**: Completed  
**Commit**: {circuit_diff.commit_hash[:7]}  
**Details**: {comp_changes} component changes, {net_changes} net changes  
**Impact**: Circuit functionality {'significantly' if comp_changes + net_changes > 5 else 'moderately'} updated  

"""

            # Insert after template section
            if "---\n\n" in content:
                parts = content.split("---\n\n", 1)
                new_content = parts[0] + "---\n" + entry + "\n" + parts[1]
            else:
                new_content = content + entry

            # Write updated content
            with open(timeline_file, "w") as f:
                f.write(new_content)

            return True

        except Exception as e:
            logger.error(f"Failed to update timeline.md with diff: {e}")
            return False

    def _update_issues_file_with_diff(self, circuit_diff) -> bool:
        """Update issues.md if problems are indicated in the commit."""
        try:
            issues_file = self.memory_bank_path / "issues.md"

            # Check if commit message indicates a problem/fix
            problem_keywords = [
                "fix",
                "bug",
                "error",
                "issue",
                "problem",
                "broken",
                "fail",
            ]
            message_lower = circuit_diff.commit_message.lower()

            if not any(keyword in message_lower for keyword in problem_keywords):
                return False  # No issues indicated

            # Read existing content
            content = ""
            if issues_file.exists():
                with open(issues_file, "r") as f:
                    content = f.read()

            # Create issue entry
            date = datetime.now().strftime("%Y-%m-%d")

            # Determine severity based on changes
            total_changes = len(circuit_diff.component_changes) + len(
                circuit_diff.net_changes
            )
            if total_changes > 10:
                severity = "High"
            elif total_changes > 3:
                severity = "Medium"
            else:
                severity = "Low"

            entry = f"""
## {date}: {circuit_diff.commit_message}
**Issue**: Problem resolved in commit {circuit_diff.commit_hash[:7]}  
**Severity**: {severity}  
**Root Cause**: Circuit issue requiring {total_changes} changes  
**Solution**: {circuit_diff.commit_message}  
**Status**: Resolved  
**Prevention**: Monitor similar patterns in future designs  

"""

            # Insert after template section
            if "---\n\n" in content:
                parts = content.split("---\n\n", 1)
                new_content = parts[0] + "---\n" + entry + "\n" + parts[1]
            else:
                new_content = content + entry

            # Write updated content
            with open(issues_file, "w") as f:
                f.write(new_content)

            return True

        except Exception as e:
            logger.error(f"Failed to update issues.md with diff: {e}")
            return False

    def _should_update_timeline_from_diff(self, circuit_diff) -> bool:
        """Determine if timeline should be updated based on circuit diff."""
        # Update timeline for significant changes or milestone keywords
        total_changes = len(circuit_diff.component_changes) + len(
            circuit_diff.net_changes
        )
        milestone_keywords = [
            "version",
            "release",
            "milestone",
            "complete",
            "finished",
            "ready",
        ]

        return total_changes >= 3 or any(  # Significant number of changes
            keyword in circuit_diff.commit_message.lower()
            for keyword in milestone_keywords
        )

    def _should_update_issues_from_diff(self, circuit_diff) -> bool:
        """Determine if issues should be updated based on circuit diff."""
        # Update issues if commit message indicates problem resolution
        problem_keywords = ["fix", "bug", "error", "issue", "problem", "broken", "fail"]
        return any(
            keyword in circuit_diff.commit_message.lower()
            for keyword in problem_keywords
        )
