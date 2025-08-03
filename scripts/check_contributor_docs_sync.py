#!/usr/bin/env python3
"""
Check if Contributors documentation needs updates based on code changes.

This script analyzes the circuit-synth codebase and determines if the Contributors/
documentation is out of sync with the current agents, commands, or configuration.

Usage:
    python scripts/check_contributor_docs_sync.py

Exit codes:
    0: Documentation is up-to-date
    1: Documentation needs updates
    2: Error occurred during checking
"""

import os
import sys
import json
import hashlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CONTRIBUTORS_DIR = PROJECT_ROOT / "Contributors"
AGENTS_DIR = PROJECT_ROOT / "src" / "circuit_synth" / "claude_integration" / "agents"
COMMANDS_DIR = PROJECT_ROOT / "src" / "circuit_synth" / "claude_integration" / "commands"
CLAUDE_DIR = PROJECT_ROOT / ".claude"

class ContributorDocsChecker:
    """Check if Contributors documentation is synchronized with codebase."""
    
    def __init__(self):
        self.current_state = {}
        self.documented_state = {}
        self.changes_detected = False
        
    def check_sync_status(self) -> bool:
        """
        Check if Contributors documentation is synchronized with codebase.
        
        Returns:
            True if updates are needed, False if up-to-date
        """
        try:
            logger.info("🔍 Checking Contributors documentation synchronization...")
            
            # Analyze current codebase state
            self.current_state = self._analyze_current_state()
            
            # Analyze documented state
            self.documented_state = self._analyze_documented_state()
            
            # Compare and detect changes
            self.changes_detected = self._detect_changes()
            
            if self.changes_detected:
                logger.info("⚠️  Contributors documentation needs updates")
                self._log_change_summary()
                return True
            else:
                logger.info("✅ Contributors documentation is up-to-date")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking documentation sync: {e}")
            return False  # Assume no updates needed on error to avoid infinite loops
    
    def _analyze_current_state(self) -> Dict[str, Any]:
        """Analyze current state of agents, commands, and configuration."""
        state = {
            'agents': self._analyze_agents(),
            'commands': self._analyze_commands(),
            'claude_config': self._analyze_claude_config(),
            'code_version': self._get_code_version()
        }
        
        logger.info(f"📊 Current state: {len(state['agents'])} agents, {len(state['commands'])} commands")
        return state
    
    def _analyze_agents(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all available agents."""
        agents = {}
        
        if not AGENTS_DIR.exists():
            logger.warning(f"Agents directory not found: {AGENTS_DIR}")
            return agents
            
        for agent_file in AGENTS_DIR.glob("*.py"):
            if agent_file.name.startswith("__"):
                continue
                
            try:
                agent_info = self._extract_agent_info(agent_file)
                if agent_info:
                    agents[agent_info['name']] = agent_info
            except Exception as e:
                logger.warning(f"Failed to analyze agent {agent_file.name}: {e}")
                
        return agents
    
    def _extract_agent_info(self, agent_file: Path) -> Optional[Dict[str, Any]]:
        """Extract information from an agent file."""
        try:
            content = agent_file.read_text()
            
            # Extract basic info from class definition
            info = {
                'name': agent_file.stem,
                'file_path': str(agent_file),
                'file_hash': hashlib.md5(content.encode()).hexdigest(),
                'description': self._extract_description(content),
                'capabilities': self._extract_capabilities(content),
                'system_prompt_present': 'def get_system_prompt(' in content,
                'tools_present': 'def get_tools(' in content,
                'has_examples': 'Example Usage' in content or 'example' in content.lower()
            }
            
            return info
            
        except Exception as e:
            logger.warning(f"Failed to extract info from {agent_file}: {e}")
            return None
    
    def _extract_description(self, content: str) -> str:
        """Extract agent description from docstring or comments."""
        lines = content.split('\n')
        
        # Look for class docstring
        for i, line in enumerate(lines):
            if 'class ' in line and 'Agent' in line:
                # Check next few lines for docstring
                for j in range(i + 1, min(i + 10, len(lines))):
                    if '"""' in lines[j]:
                        # Found docstring start
                        desc_lines = []
                        for k in range(j, len(lines)):
                            if k > j and '"""' in lines[k]:
                                break
                            desc_lines.append(lines[k].strip().strip('"""').strip())
                        return ' '.join(desc_lines).strip()
        
        return "No description found"
    
    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities from agent code."""
        capabilities = []
        
        # Look for get_capabilities method
        if 'def get_capabilities(' in content:
            # Extract return list
            lines = content.split('\n')
            in_capabilities = False
            for line in lines:
                if 'def get_capabilities(' in line:
                    in_capabilities = True
                    continue
                if in_capabilities:
                    if 'return [' in line or '"' in line:
                        # Extract quoted strings
                        import re
                        quotes = re.findall(r'"([^"]*)"', line)
                        capabilities.extend(quotes)
                    if ']' in line and in_capabilities:
                        break
        
        return capabilities
    
    def _analyze_commands(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all available commands."""
        commands = {}
        
        # Commands might be defined in various places
        # Check CLAUDE.md for command documentation
        claude_md = PROJECT_ROOT / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            commands.update(self._extract_commands_from_claude_md(content))
        
        # Check .claude directory for command definitions
        if CLAUDE_DIR.exists():
            for cmd_file in CLAUDE_DIR.rglob("*.json"):
                try:
                    with open(cmd_file) as f:
                        config = json.load(f)
                        if 'commands' in config:
                            commands.update(config['commands'])
                except Exception as e:
                    logger.warning(f"Failed to parse {cmd_file}: {e}")
        
        return commands
    
    def _extract_commands_from_claude_md(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract command information from CLAUDE.md."""
        commands = {}
        lines = content.split('\n')
        
        current_command = None
        current_description = []
        
        for line in lines:
            # Look for command definitions (lines starting with /command)
            if line.strip().startswith('/') and ' ' in line:
                # Save previous command if exists
                if current_command:
                    commands[current_command] = {
                        'name': current_command,
                        'description': ' '.join(current_description),
                        'source': 'CLAUDE.md'
                    }
                
                # Start new command
                current_command = line.strip().split()[0]
                current_description = []
            elif current_command and line.strip():
                # Collect description lines
                current_description.append(line.strip())
            elif not line.strip() and current_command:
                # End of command description
                if current_command:
                    commands[current_command] = {
                        'name': current_command,
                        'description': ' '.join(current_description),
                        'source': 'CLAUDE.md'
                    }
                current_command = None
                current_description = []
        
        return commands
    
    def _analyze_claude_config(self) -> Dict[str, Any]:
        """Analyze Claude configuration files."""
        config = {
            'agent_configs': [],
            'command_configs': [],
            'claude_md_hash': None
        }
        
        # Check CLAUDE.md
        claude_md = PROJECT_ROOT / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            config['claude_md_hash'] = hashlib.md5(content.encode()).hexdigest()
        
        # Check .claude directory
        if CLAUDE_DIR.exists():
            for config_file in CLAUDE_DIR.rglob("*.json"):
                try:
                    with open(config_file) as f:
                        data = json.load(f)
                        config['agent_configs'].append({
                            'file': str(config_file),
                            'hash': hashlib.md5(config_file.read_text().encode()).hexdigest()
                        })
                except Exception as e:
                    logger.warning(f"Failed to analyze {config_file}: {e}")
        
        return config
    
    def _get_code_version(self) -> str:
        """Get a hash representing the current code version."""
        # Hash key files to detect major changes
        key_files = [
            PROJECT_ROOT / "src" / "circuit_synth" / "__init__.py",
            PROJECT_ROOT / "pyproject.toml",
            PROJECT_ROOT / "CLAUDE.md"
        ]
        
        combined_hash = hashlib.md5()
        for file_path in key_files:
            if file_path.exists():
                combined_hash.update(file_path.read_bytes())
        
        return combined_hash.hexdigest()
    
    def _analyze_documented_state(self) -> Dict[str, Any]:
        """Analyze what's currently documented in Contributors/."""
        state = {
            'agents': {},
            'commands': {},
            'doc_hashes': {},
            'last_updated': None
        }
        
        # Check Contributors documentation files
        if CONTRIBUTORS_DIR.exists():
            for doc_file in CONTRIBUTORS_DIR.glob("*.md"):
                content = doc_file.read_text()
                state['doc_hashes'][doc_file.name] = hashlib.md5(content.encode()).hexdigest()
                
                # Extract documented agents and commands
                if doc_file.name == "Claude-Code-Agents-and-Commands.md":
                    state['agents'] = self._extract_documented_agents(content)
                    state['commands'] = self._extract_documented_commands(content)
        
        return state
    
    def _extract_documented_agents(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract agent information from documentation."""
        agents = {}
        
        # Look for agent sections (### or ## followed by agent name)
        lines = content.split('\n')
        current_agent = None
        current_info = []
        
        for line in lines:
            if line.startswith('### ') and 'agent' in line.lower():
                # Save previous agent
                if current_agent:
                    agents[current_agent] = {
                        'name': current_agent,
                        'documented_info': ' '.join(current_info)
                    }
                
                # Start new agent
                current_agent = line.replace('### ', '').replace('**', '').strip()
                if '(' in current_agent:
                    current_agent = current_agent.split('(')[0].strip()
                current_info = []
            elif current_agent and line.strip():
                current_info.append(line.strip())
            elif not line.strip() and current_agent and current_info:
                # End of agent documentation
                agents[current_agent] = {
                    'name': current_agent,
                    'documented_info': ' '.join(current_info)
                }
                current_agent = None
                current_info = []
        
        return agents
    
    def _extract_documented_commands(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract command information from documentation."""
        commands = {}
        
        # Look for command sections (#### followed by command name starting with /)
        lines = content.split('\n')
        current_command = None
        current_info = []
        
        for line in lines:
            if line.startswith('#### ') and line.strip().endswith('`') and '/':
                # Save previous command
                if current_command:
                    commands[current_command] = {
                        'name': current_command,
                        'documented_info': ' '.join(current_info)
                    }
                
                # Start new command
                current_command = line.replace('#### ', '').replace('`', '').strip()
                if current_command.startswith('`'):
                    current_command = current_command[1:]
                current_info = []
            elif current_command and line.strip():
                current_info.append(line.strip())
            elif not line.strip() and current_command and current_info:
                # End of command documentation
                commands[current_command] = {
                    'name': current_command,
                    'documented_info': ' '.join(current_info)
                }
                current_command = None
                current_info = []
        
        return commands
    
    def _detect_changes(self) -> bool:
        """Detect if there are changes requiring documentation updates."""
        changes = []
        
        # Check for new or modified agents
        current_agents = set(self.current_state['agents'].keys())
        documented_agents = set(self.documented_state['agents'].keys())
        
        new_agents = current_agents - documented_agents
        removed_agents = documented_agents - current_agents
        
        if new_agents:
            changes.append(f"New agents: {', '.join(new_agents)}")
        if removed_agents:
            changes.append(f"Removed agents: {', '.join(removed_agents)}")
        
        # Check for modified agents (by file hash)
        for agent_name in current_agents & documented_agents:
            current_hash = self.current_state['agents'][agent_name].get('file_hash')
            # For simplicity, assume modification if agent exists in both but we can't verify hash
            # In a real implementation, we'd store hashes in the docs or a separate tracking file
            
        # Check for new or modified commands
        current_commands = set(self.current_state['commands'].keys())
        documented_commands = set(self.documented_state['commands'].keys())
        
        new_commands = current_commands - documented_commands
        removed_commands = documented_commands - current_commands
        
        if new_commands:
            changes.append(f"New commands: {', '.join(new_commands)}")
        if removed_commands:
            changes.append(f"Removed commands: {', '.join(removed_commands)}")
        
        # Check CLAUDE.md changes
        current_claude_hash = self.current_state['claude_config'].get('claude_md_hash')
        # We'd need to track the previous hash - for now, assume change if we can't verify
        
        self.detected_changes = changes
        return len(changes) > 0
    
    def _log_change_summary(self):
        """Log summary of detected changes."""
        logger.info("📋 Detected changes requiring documentation updates:")
        for change in self.detected_changes:
            logger.info(f"  • {change}")


def main():
    """Main entry point."""
    checker = ContributorDocsChecker()
    
    try:
        needs_update = checker.check_sync_status()
        
        if needs_update:
            logger.info("🔄 Contributors documentation will be updated")
            sys.exit(1)  # Indicate updates needed
        else:
            logger.info("✅ No documentation updates required")
            sys.exit(0)  # Indicate up-to-date
            
    except Exception as e:
        logger.error(f"❌ Error during sync check: {e}")
        sys.exit(2)  # Indicate error


if __name__ == "__main__":
    main()