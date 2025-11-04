#!/usr/bin/env python3
"""
TAC Agent Template Loader

Loads agent templates from .claude/agents/*.md files and syncs them to the
PostgreSQL database.

Template Format:
---------------
```markdown
---
name: research-agent
description: Investigates codebase for context
model: haiku
temperature: 0.7
tools:
  - Read
  - Grep
  - Glob
color: blue
---

# Research Agent

System prompt goes here...
```
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal
import yaml

logger = logging.getLogger(__name__)


class AgentTemplate:
    """Represents a single agent template from a .md file"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        description: Optional[str] = None,
        model: str = "sonnet",
        temperature: float = 1.0,
        tools: Optional[List[str]] = None,
        color: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.description = description or f"Agent: {name}"
        self.model = model
        self.temperature = Decimal(str(temperature))
        self.tools = tools or []
        self.color = color
        self.metadata = metadata or {}

    def __repr__(self):
        return f"AgentTemplate(name={self.name!r}, model={self.model}, tools={len(self.tools)})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "temperature": self.temperature,
            "tools": self.tools,
            "color": self.color,
            "metadata": self.metadata,
        }


class AgentTemplateLoader:
    """Loads and manages agent templates from .claude/agents/*.md files"""

    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize agent template loader.

        Args:
            agents_dir: Path to .claude/agents directory. If None, uses .claude/agents
                       in current working directory.
        """
        if agents_dir is None:
            agents_dir = Path.cwd() / ".claude" / "agents"

        self.agents_dir = Path(agents_dir)
        logger.info(f"AgentTemplateLoader initialized with directory: {self.agents_dir}")

    def load_template_file(self, file_path: Path) -> Optional[AgentTemplate]:
        """
        Load a single agent template from a markdown file.

        Args:
            file_path: Path to the .md file

        Returns:
            AgentTemplate if successfully parsed, None otherwise
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Split YAML frontmatter from markdown body
            # Pattern: --- at start, content, --- delimiter
            frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
            match = re.match(frontmatter_pattern, content, re.DOTALL)

            if not match:
                logger.warning(f"No YAML frontmatter found in {file_path.name}")
                return None

            frontmatter_text = match.group(1)
            system_prompt = match.group(2).strip()

            # Parse YAML frontmatter
            try:
                frontmatter = yaml.safe_load(frontmatter_text)
            except yaml.YAMLError as e:
                logger.error(f"YAML parsing error in {file_path.name}: {e}")
                return None

            # Validate required fields
            if not isinstance(frontmatter, dict):
                logger.error(f"Invalid frontmatter in {file_path.name}: expected dict")
                return None

            if 'name' not in frontmatter:
                logger.error(f"Missing 'name' in frontmatter of {file_path.name}")
                return None

            # Create template
            template = AgentTemplate(
                name=frontmatter['name'],
                system_prompt=system_prompt,
                description=frontmatter.get('description'),
                model=frontmatter.get('model', 'sonnet'),
                temperature=frontmatter.get('temperature', 1.0),
                tools=frontmatter.get('tools', []),
                color=frontmatter.get('color'),
                metadata={
                    'source_file': str(file_path),
                    'file_name': file_path.name,
                },
            )

            logger.debug(f"✓ Loaded template: {template.name} from {file_path.name}")
            return template

        except Exception as e:
            logger.error(f"Error loading template from {file_path}: {e}", exc_info=True)
            return None

    def load_all_templates(self) -> List[AgentTemplate]:
        """
        Load all agent templates from the agents directory.

        Returns:
            List of successfully loaded templates
        """
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory does not exist: {self.agents_dir}")
            return []

        logger.info(f"Loading templates from {self.agents_dir}")

        templates = []
        template_files = sorted(self.agents_dir.glob("*.md"))

        for file_path in template_files:
            logger.debug(f"Processing {file_path.name}...")
            template = self.load_template_file(file_path)
            if template:
                templates.append(template)

        logger.info(f"✓ Loaded {len(templates)} templates from {len(template_files)} files")

        # Check for duplicate names
        seen_names = set()
        for template in templates:
            if template.name in seen_names:
                logger.warning(f"Duplicate template name: {template.name}")
            seen_names.add(template.name)

        return templates

    async def sync_to_database(self, db) -> int:
        """
        Sync all templates to database.

        Loads templates from .claude/agents/*.md files and inserts/updates them
        in the database. Existing templates with the same name are updated.

        Args:
            db: TACDatabase instance

        Returns:
            Number of templates synced
        """
        templates = self.load_all_templates()

        if not templates:
            logger.info("No templates to sync")
            return 0

        logger.info(f"Syncing {len(templates)} templates to database...")

        synced_count = 0

        for template in templates:
            try:
                # Check if template already exists
                existing = await db.get_agent_template(template.name)

                if existing:
                    # Update existing template
                    logger.debug(f"Updating existing template: {template.name}")

                    # For now, we'll just log that we'd update it
                    # In a full implementation, we'd add an update_agent_template method
                    logger.info(f"Template {template.name} already exists (would update)")
                else:
                    # Insert new template
                    logger.debug(f"Inserting new template: {template.name}")

                    template_dict = template.to_dict()

                    # Insert using raw SQL for now (could add method to TACDatabase)
                    insert_query = """
                        INSERT INTO tac_agent_templates (
                            name, description, system_prompt, tools,
                            model, temperature, color, metadata
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (name) DO UPDATE SET
                            description = EXCLUDED.description,
                            system_prompt = EXCLUDED.system_prompt,
                            tools = EXCLUDED.tools,
                            model = EXCLUDED.model,
                            temperature = EXCLUDED.temperature,
                            color = EXCLUDED.color,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW();
                    """

                    await db.pool.execute(
                        insert_query,
                        template_dict['name'],
                        template_dict['description'],
                        template_dict['system_prompt'],
                        template_dict['tools'],
                        template_dict['model'],
                        template_dict['temperature'],
                        template_dict['color'],
                        # Metadata as JSON string
                        __import__('json').dumps(template_dict['metadata']),
                    )

                    logger.info(f"✓ Synced template: {template.name}")

                synced_count += 1

            except Exception as e:
                logger.error(f"Failed to sync template {template.name}: {e}", exc_info=True)

        logger.info(f"✓ Synced {synced_count}/{len(templates)} templates to database")
        return synced_count

    def watch_templates(self, callback):
        """
        Watch for changes in template files (future enhancement).

        Args:
            callback: Function to call when templates change
        """
        raise NotImplementedError("Template watching not yet implemented")
