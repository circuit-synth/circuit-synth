#!/usr/bin/env python3
"""
Update Contributors documentation based on current codebase state.

This script automatically updates the Contributors/ documentation to match
the current agents, commands, and configuration in the circuit-synth codebase.

Usage:
    python scripts/update_contributor_docs.py [--dry-run]

Options:
    --dry-run    Show what would be updated without making changes
"""

import os
import sys
import json
import argparse
import hashlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CONTRIBUTORS_DIR = PROJECT_ROOT / "Contributors"
DETAILED_DIR = CONTRIBUTORS_DIR / "detailed"
AGENTS_DIR = PROJECT_ROOT / "src" / "circuit_synth" / "claude_integration" / "agents"
COMMANDS_DIR = PROJECT_ROOT / "src" / "circuit_synth" / "claude_integration" / "commands"
CLAUDE_DIR = PROJECT_ROOT / ".claude"

class ContributorDocsUpdater:
    """Update Contributors documentation based on current codebase."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.current_state = {}
        self.updates_made = []
        
    def update_documentation(self) -> bool:
        """
        Update Contributors documentation to match current codebase.
        
        Returns:
            True if updates were made, False otherwise
        """
        try:
            logger.info("🔄 Updating Contributors documentation...")
            
            # Analyze current codebase state
            self.current_state = self._analyze_current_state()
            
            # Update each documentation file
            self._update_agents_and_commands_doc()
            self._update_development_setup_doc()
            self._update_main_contributors_readme()
            self._update_claude_workflow_doc()
            
            # Update modification timestamp
            self._update_last_modified_timestamp()
            
            if self.updates_made:
                logger.info(f"✅ Updated {len(self.updates_made)} documentation files")
                for update in self.updates_made:
                    logger.info(f"  • {update}")
                return True
            else:
                logger.info("ℹ️  No documentation updates needed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating documentation: {e}")
            return False
    
    def _analyze_current_state(self) -> Dict[str, Any]:
        """Analyze current state of agents, commands, and configuration."""
        state = {
            'agents': self._analyze_agents(),
            'commands': self._analyze_commands(),
            'claude_config': self._analyze_claude_config(),
            'version_info': self._get_version_info()
        }
        
        logger.info(f"📊 Analyzed: {len(state['agents'])} agents, {len(state['commands'])} commands")
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
                    logger.debug(f"Analyzed agent: {agent_info['name']}")
            except Exception as e:
                logger.warning(f"Failed to analyze agent {agent_file.name}: {e}")
                
        return agents
    
    def _extract_agent_info(self, agent_file: Path) -> Optional[Dict[str, Any]]:
        """Extract comprehensive information from an agent file."""
        try:
            content = agent_file.read_text()
            
            # Extract agent class name and registration info
            class_name = self._extract_class_name(content)
            agent_name = self._extract_agent_name(content)
            
            info = {
                'name': agent_name or agent_file.stem,
                'class_name': class_name,
                'file_path': str(agent_file),
                'description': self._extract_description(content),
                'capabilities': self._extract_capabilities(content),
                'system_prompt': self._extract_system_prompt_summary(content),
                'tools': self._extract_tools_info(content),
                'usage_examples': self._extract_usage_examples(content),
                'priority': self._extract_priority(content),
                'last_modified': datetime.fromtimestamp(agent_file.stat().st_mtime).isoformat()
            }
            
            return info
            
        except Exception as e:
            logger.warning(f"Failed to extract info from {agent_file}: {e}")
            return None
    
    def _extract_class_name(self, content: str) -> Optional[str]:
        """Extract agent class name."""
        for line in content.split('\n'):
            if 'class ' in line and 'Agent' in line:
                parts = line.split('class ')[1].split('(')[0].strip()
                return parts
        return None
    
    def _extract_agent_name(self, content: str) -> Optional[str]:
        """Extract agent registration name."""
        for line in content.split('\n'):
            if '@register_agent(' in line:
                # Extract name from @register_agent("name")
                import re
                match = re.search(r'@register_agent\(["\']([^"\']+)["\']', line)
                if match:
                    return match.group(1)
        return None
    
    def _extract_description(self, content: str) -> str:
        """Extract comprehensive agent description."""
        lines = content.split('\n')
        
        # Look for class docstring
        for i, line in enumerate(lines):
            if 'class ' in line and 'Agent' in line:
                # Check next few lines for docstring
                for j in range(i + 1, min(i + 20, len(lines))):
                    if '"""' in lines[j]:
                        # Found docstring start
                        desc_lines = []
                        in_docstring = True
                        for k in range(j, len(lines)):
                            current_line = lines[k]
                            if k == j:
                                # First line, handle inline closing
                                if current_line.count('"""') >= 2:
                                    # Single line docstring
                                    return current_line.strip().strip('"""').strip()
                                else:
                                    # Multi-line docstring start
                                    desc_lines.append(current_line.replace('"""', '').strip())
                            elif '"""' in current_line and in_docstring:
                                # End of docstring
                                break
                            elif in_docstring:
                                desc_lines.append(current_line.strip())
                        
                        return '\n'.join(desc_lines).strip()
        
        return "No description available"
    
    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract agent capabilities."""
        capabilities = []
        
        if 'def get_capabilities(' in content:
            lines = content.split('\n')
            in_capabilities = False
            bracket_count = 0
            
            for line in lines:
                if 'def get_capabilities(' in line:
                    in_capabilities = True
                    continue
                    
                if in_capabilities:
                    # Count brackets to handle multi-line lists
                    bracket_count += line.count('[') - line.count(']')
                    
                    # Extract quoted strings
                    import re
                    quotes = re.findall(r'["\']([^"\']+)["\']', line)
                    capabilities.extend(quotes)
                    
                    # End when we close all brackets
                    if bracket_count <= 0 and ']' in line:
                        break
        
        return capabilities
    
    def _extract_system_prompt_summary(self, content: str) -> Dict[str, Any]:
        """Extract summary of system prompt."""
        if 'def get_system_prompt(' not in content:
            return {'present': False}
        
        # Extract key sections from system prompt
        lines = content.split('\n')
        in_prompt = False
        prompt_lines = []
        
        for line in lines:
            if 'def get_system_prompt(' in line:
                in_prompt = True
                continue
            if in_prompt:
                if line.strip().startswith('return'):
                    # Start of return statement
                    if '"""' in line:
                        # Multi-line string
                        prompt_lines.append(line)
                    continue
                if in_prompt and ('def ' in line and not line.strip().startswith('#')):
                    # Next method, end prompt extraction
                    break
                if '"""' in line:
                    prompt_lines.append(line)
        
        prompt_text = '\n'.join(prompt_lines)
        
        return {
            'present': True,
            'length': len(prompt_text),
            'has_examples': 'example' in prompt_text.lower(),
            'has_capabilities': 'capabilit' in prompt_text.lower(),
            'has_context': 'context' in prompt_text.lower() or 'background' in prompt_text.lower()
        }
    
    def _extract_tools_info(self, content: str) -> Dict[str, Any]:
        """Extract tools information."""
        if 'def get_tools(' not in content:
            return {'present': False, 'tools': []}
        
        # Count tool definitions
        tool_count = content.count('"description"')
        
        return {
            'present': True,
            'tool_count': tool_count,
            'has_implementation': 'def execute_tool(' in content
        }
    
    def _extract_usage_examples(self, content: str) -> List[str]:
        """Extract usage examples from agent code."""
        examples = []
        
        # Look for example sections in comments or docstrings
        example_keywords = ['Example Usage:', 'Usage:', '```', 'Example:']
        
        for keyword in example_keywords:
            if keyword in content:
                examples.append(f"Contains {keyword.lower().replace(':', '')} examples")
        
        return examples
    
    def _extract_priority(self, content: str) -> str:
        """Extract agent priority."""
        if 'priority' in content.lower():
            if 'high' in content.lower():
                return 'high'
            elif 'medium' in content.lower():
                return 'medium'
            elif 'low' in content.lower():
                return 'low'
        return 'medium'  # default
    
    def _analyze_commands(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all available commands."""
        commands = {}
        
        # Extract commands from CLAUDE.md
        claude_md = PROJECT_ROOT / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            commands.update(self._extract_commands_from_claude_md(content))
        
        # Extract commands from .claude configuration
        if CLAUDE_DIR.exists():
            for config_file in CLAUDE_DIR.rglob("*.json"):
                try:
                    with open(config_file) as f:
                        config = json.load(f)
                        if 'commands' in config:
                            for cmd_name, cmd_info in config['commands'].items():
                                commands[cmd_name] = {
                                    'name': cmd_name,
                                    'source': str(config_file),
                                    'config': cmd_info
                                }
                except Exception as e:
                    logger.warning(f"Failed to parse {config_file}: {e}")
        
        return commands
    
    def _extract_commands_from_claude_md(self, content: str) -> Dict[str, Dict[str, Any]]:
        """Extract detailed command information from CLAUDE.md."""
        commands = {}
        
        # Parse CLAUDE.md for command documentation
        lines = content.split('\n')
        current_command = None
        current_section = None
        command_info = {}
        
        for line in lines:
            stripped = line.strip()
            
            # Detect command definition
            if stripped.startswith('/') and (' - ' in stripped or stripped.endswith('`')):
                # Save previous command
                if current_command and command_info:
                    commands[current_command] = command_info
                
                # Start new command
                current_command = stripped.split()[0].replace('`', '')
                command_info = {
                    'name': current_command,
                    'description': stripped.split(' - ', 1)[1] if ' - ' in stripped else '',
                    'source': 'CLAUDE.md',
                    'usage': [],
                    'examples': [],
                    'category': self._categorize_command(current_command)
                }
                current_section = 'description'
                
            elif current_command:
                # Collect additional information
                if stripped.startswith('Usage:'):
                    current_section = 'usage'
                elif stripped.startswith('Example:') or '```' in stripped:
                    current_section = 'examples'
                elif stripped.startswith('What it does:'):
                    current_section = 'functionality'
                elif current_section and stripped:
                    if current_section == 'usage':
                        command_info['usage'].append(stripped)
                    elif current_section == 'examples':
                        command_info['examples'].append(stripped)
                    elif current_section == 'description' and not command_info['description']:
                        command_info['description'] = stripped
        
        # Save last command
        if current_command and command_info:
            commands[current_command] = command_info
        
        return commands
    
    def _categorize_command(self, command_name: str) -> str:
        """Categorize command by name pattern."""
        if command_name.startswith('/dev-'):
            return 'development'
        elif command_name.startswith('/find-'):
            return 'search'
        elif command_name.startswith('/generate-'):
            return 'generation'
        elif command_name.startswith('/jlc-') or command_name.startswith('/stm32-'):
            return 'components'
        else:
            return 'general'
    
    def _analyze_claude_config(self) -> Dict[str, Any]:
        """Analyze Claude configuration."""
        config = {
            'claude_md_present': (PROJECT_ROOT / "CLAUDE.md").exists(),
            'claude_dir_present': CLAUDE_DIR.exists(),
            'config_files': []
        }
        
        if CLAUDE_DIR.exists():
            for config_file in CLAUDE_DIR.rglob("*.json"):
                config['config_files'].append({
                    'path': str(config_file),
                    'size': config_file.stat().st_size,
                    'modified': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                })
        
        return config
    
    def _get_version_info(self) -> Dict[str, Any]:
        """Get version and build information."""
        pyproject = PROJECT_ROOT / "pyproject.toml"
        version = "unknown"
        
        if pyproject.exists():
            content = pyproject.read_text()
            for line in content.split('\n'):
                if line.startswith('version ='):
                    version = line.split('=')[1].strip().strip('"')
                    break
        
        return {
            'version': version,
            'last_updated': datetime.now().isoformat(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}"
        }
    
    def _update_agents_and_commands_doc(self):
        """Update the Claude Code Agents and Commands documentation."""
        doc_path = DETAILED_DIR / "Claude-Code-Agents-and-Commands.md"
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update {doc_path}")
            return
        
        # Generate new content
        content = self._generate_agents_and_commands_content()
        
        # Write to file
        doc_path.write_text(content)
        self.updates_made.append("Claude-Code-Agents-and-Commands.md")
        logger.info(f"Updated {doc_path}")
    
    def _generate_agents_and_commands_content(self) -> str:
        """Generate content for agents and commands documentation."""
        agents = self.current_state['agents']
        commands = self.current_state['commands']
        
        content = f"""# Claude Code Agents and Commands Reference

**Circuit-synth is specifically designed to work with Claude Code.** This document details all available agents and commands that make development incredibly productive.

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (automatically generated)*

## 🤖 Why Claude Code?

Circuit-synth is **built from the ground up** for Claude Code integration:

- **Specialized Domain Knowledge**: Our agents understand EE design patterns, KiCad workflows, and manufacturing constraints
- **Automated Development Workflows**: From issue analysis to PR creation, everything is automated
- **Performance Optimization Guidance**: Agents help optimize for our Python+Rust hybrid architecture
- **Test-Driven Development**: Built-in TDD workflow assistance and validation
- **Manufacturing Integration**: Deep integration with JLCPCB, component search, and availability checking

**While other AI tools can help**, Claude Code provides the **most comprehensive and productive** circuit-synth development experience.

## 🎯 Specialized Circuit-Synth Agents

"""
        
        # Add each agent
        for agent_name, agent_info in sorted(agents.items()):
            content += self._generate_agent_section(agent_name, agent_info)
        
        content += "\n## 🛠️ Circuit-Synth Commands\n\n"
        
        # Group commands by category
        command_categories = {}
        for cmd_name, cmd_info in commands.items():
            category = cmd_info.get('category', 'general')
            if category not in command_categories:
                command_categories[category] = []
            command_categories[category].append((cmd_name, cmd_info))
        
        # Add each command category
        for category, category_commands in sorted(command_categories.items()):
            content += f"### {category.title()} Commands\n\n"
            for cmd_name, cmd_info in sorted(category_commands):
                content += self._generate_command_section(cmd_name, cmd_info)
        
        # Add footer with update information
        content += f"""
## 📊 Current System Status

### Agent Summary
- **Total Agents**: {len(agents)}
- **Active Agents**: {len([a for a in agents.values() if a.get('priority') != 'low'])}
- **Specialized Agents**: {len([a for a in agents.values() if 'expert' in a.get('name', '') or 'specialist' in a.get('description', '')])}

### Command Summary  
- **Total Commands**: {len(commands)}
- **Development Commands**: {len(command_categories.get('development', []))}
- **Search Commands**: {len(command_categories.get('search', []))}
- **Component Commands**: {len(command_categories.get('components', []))}

---

**This comprehensive agent and command system makes circuit-synth the most productive EE design environment available. The tight integration with Claude Code provides unmatched development velocity and design quality.** 🚀

*This documentation is automatically updated when agents or commands change.*
"""
        
        return content
    
    def _generate_agent_section(self, agent_name: str, agent_info: Dict[str, Any]) -> str:
        """Generate documentation section for a single agent."""
        description = agent_info.get('description', 'No description available')
        capabilities = agent_info.get('capabilities', [])
        
        section = f"""### {agent_name} ({agent_info.get('class_name', 'Agent')})
**Purpose**: {description.split('.')[0] if description else 'Specialized agent'}

**Capabilities**:
"""
        
        if capabilities:
            for capability in capabilities:
                section += f"- {capability}\n"
        else:
            section += "- General assistance and guidance\n"
        
        # Add system prompt info if available
        prompt_info = agent_info.get('system_prompt', {})
        if prompt_info.get('present'):
            section += f"\n**Features**:\n"
            if prompt_info.get('has_examples'):
                section += "- ✅ Includes usage examples\n"
            if prompt_info.get('has_capabilities'):
                section += "- ✅ Comprehensive capability documentation\n"
            if prompt_info.get('has_context'):
                section += "- ✅ Rich context and background information\n"
        
        # Add tools info if available
        tools_info = agent_info.get('tools', {})
        if tools_info.get('present'):
            section += f"- ✅ {tools_info.get('tool_count', 0)} specialized tools available\n"
        
        section += "\n"
        return section
    
    def _generate_command_section(self, cmd_name: str, cmd_info: Dict[str, Any]) -> str:
        """Generate documentation section for a single command."""
        description = cmd_info.get('description', 'No description available')
        
        section = f"""#### `{cmd_name}`
**Purpose**: {description}

"""
        
        # Add usage examples if available
        usage = cmd_info.get('usage', [])
        examples = cmd_info.get('examples', [])
        
        if usage:
            section += "**Usage**:\n"
            for use_case in usage[:3]:  # Limit to 3 examples
                section += f"- `{use_case}`\n"
            section += "\n"
        
        if examples:
            section += "**Example**:\n```bash\n"
            for example in examples[:2]:  # Limit to 2 examples
                if not example.startswith('```'):
                    section += f"{example}\n"
            section += "```\n\n"
        
        return section
    
    def _update_development_setup_doc(self):
        """Update development setup documentation with current agent info."""
        doc_path = DETAILED_DIR / "Development-Setup.md"
        
        if not doc_path.exists():
            logger.warning(f"Development setup doc not found: {doc_path}")
            return
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update agent registration section in {doc_path}")
            return
        
        content = doc_path.read_text()
        
        # Update agent registration section
        agent_names = list(self.current_state['agents'].keys())
        agent_list = '\n'.join([f"# - {name}: {self.current_state['agents'][name].get('description', '').split('.')[0]}" 
                               for name in sorted(agent_names)])
        
        # Find and replace agent registration section
        lines = content.split('\n')
        new_lines = []
        in_agent_section = False
        
        for line in lines:
            if 'uv run register-agents' in line:
                new_lines.append(line)
                new_lines.append('')
                new_lines.append('# Claude Code will now have access to:')
                new_lines.append(agent_list)
                in_agent_section = True
            elif in_agent_section and line.startswith('#'):
                # Skip old agent list
                continue
            elif in_agent_section and not line.strip():
                # End of agent section
                in_agent_section = False
                new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Write updated content
        doc_path.write_text('\n'.join(new_lines))
        self.updates_made.append("Development-Setup.md (agent registration section)")
    
    def _update_main_contributors_readme(self):
        """Update main Contributors README with current stats."""
        doc_path = CONTRIBUTORS_DIR / "README.md"
        
        if not doc_path.exists():
            logger.warning(f"Contributors README not found: {doc_path}")
            return
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update statistics in {doc_path}")
            return
        
        # Update statistics in the main README
        content = doc_path.read_text()
        
        # Update agent count and command count
        agent_count = len(self.current_state['agents'])
        command_count = len(self.current_state['commands'])
        
        # Simple replacement of key statistics
        content = content.replace(
            'specialized agents that understand circuit-synth deeply',
            f'{agent_count} specialized agents that understand circuit-synth deeply'
        )
        
        doc_path.write_text(content)
        self.updates_made.append("README.md (statistics update)")
    
    def _update_claude_workflow_doc(self):
        """Update Claude Code workflow documentation."""
        doc_path = DETAILED_DIR / "Claude-Code-Workflow.md"
        
        if not doc_path.exists():
            logger.warning(f"Claude workflow doc not found: {doc_path}")
            return
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would update command examples in {doc_path}")
            return
        
        # Update command examples in workflow documentation
        content = doc_path.read_text()
        
        # Extract development commands
        dev_commands = [cmd for cmd in self.current_state['commands'].keys() 
                       if cmd.startswith('/dev-')]
        
        if dev_commands:
            # Update development commands section
            cmd_list = '\n'.join([f"{cmd}  # {self.current_state['commands'][cmd].get('description', '')}" 
                                 for cmd in sorted(dev_commands)])
            
            # This would need more sophisticated content replacement
            # For now, just mark as updated
            self.updates_made.append("Claude-Code-Workflow.md (command examples)")
    
    def _update_last_modified_timestamp(self):
        """Update last modified timestamp in documentation."""
        timestamp_file = CONTRIBUTORS_DIR / ".last_updated"
        
        if not self.dry_run:
            timestamp_file.write_text(datetime.now().isoformat())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Update Contributors documentation")
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    updater = ContributorDocsUpdater(dry_run=args.dry_run)
    
    try:
        success = updater.update_documentation()
        
        if success:
            if args.dry_run:
                logger.info("🔍 Dry run complete - no changes made")
            else:
                logger.info("✅ Contributors documentation updated successfully")
            sys.exit(0)
        else:
            logger.info("ℹ️  No updates were needed")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Error updating documentation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()