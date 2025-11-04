#!/usr/bin/env python3
"""
Phase 3 Agent Template Loader Test Suite

Tests the AgentTemplateLoader module including file parsing,
YAML frontmatter extraction, and database synchronization.
"""

import asyncio
import sys
import tempfile
import shutil
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_agent_loader import AgentTemplateLoader, AgentTemplate
from adw_modules.tac_database import TACDatabase


# Test template content
RESEARCH_AGENT_TEMPLATE = """---
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

You are a research specialist focused on investigating codebases.

## Your Role

1. Search for relevant files using Glob patterns
2. Read file contents to understand context
3. Use Grep to find specific patterns
4. Provide comprehensive analysis

## Output Format

Provide findings in this format:

```markdown
## Files Found
- path/to/file1.py - Description
- path/to/file2.py - Description

## Key Findings
- Finding 1
- Finding 2

## Recommendations
- Recommendation 1
- Recommendation 2
```
"""

TEST_AGENT_TEMPLATE = """---
name: test-agent
description: Runs and validates tests
model: sonnet
temperature: 0.5
tools:
  - Bash
  - Read
color: green
---

# Test Agent

You are a testing specialist.

Run tests, analyze failures, and suggest fixes.
"""


async def test_template_parsing():
    """Test 1: Parse agent templates from markdown files"""
    print("Test 1: Template Parsing")
    print("-" * 50)

    # Create temporary directory with test templates
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Write test templates
        (tmpdir_path / "research-agent.md").write_text(RESEARCH_AGENT_TEMPLATE)
        (tmpdir_path / "test-agent.md").write_text(TEST_AGENT_TEMPLATE)

        # Load templates
        loader = AgentTemplateLoader(agents_dir=tmpdir_path)
        templates = loader.load_all_templates()

        assert len(templates) == 2, f"Expected 2 templates, got {len(templates)}"
        print(f"✓ Loaded {len(templates)} templates")

        # Check research-agent
        research = next(t for t in templates if t.name == "research-agent")
        assert research.model == "haiku", f"Expected haiku, got {research.model}"
        assert research.temperature == Decimal("0.7"), f"Expected 0.7, got {research.temperature}"
        assert len(research.tools) == 3, f"Expected 3 tools, got {len(research.tools)}"
        assert "Read" in research.tools, "Expected 'Read' in tools"
        assert research.color == "blue", f"Expected blue, got {research.color}"
        print("✓ research-agent parsed correctly")

        # Check test-agent
        test_agent = next(t for t in templates if t.name == "test-agent")
        assert test_agent.model == "sonnet", f"Expected sonnet, got {test_agent.model}"
        assert test_agent.temperature == Decimal("0.5"), f"Expected 0.5, got {test_agent.temperature}"
        assert len(test_agent.tools) == 2, f"Expected 2 tools, got {len(test_agent.tools)}"
        print("✓ test-agent parsed correctly")

        # Check system prompts
        assert "research specialist" in research.system_prompt.lower()
        assert "testing specialist" in test_agent.system_prompt.lower()
        print("✓ System prompts extracted")

    print()


async def test_database_sync():
    """Test 2: Sync templates to database"""
    print("Test 2: Database Synchronization")
    print("-" * 50)

    # Create temporary directory with test templates
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Write test templates
        (tmpdir_path / "research-agent.md").write_text(RESEARCH_AGENT_TEMPLATE)
        (tmpdir_path / "test-agent.md").write_text(TEST_AGENT_TEMPLATE)

        # Connect to database
        db = TACDatabase()
        await db.connect()

        try:
            # Clean up existing test templates
            await db.pool.execute(
                "DELETE FROM tac_agent_templates WHERE name IN ('research-agent', 'test-agent');"
            )
            print("✓ Cleaned up existing test templates")

            # Sync templates
            loader = AgentTemplateLoader(agents_dir=tmpdir_path)
            synced_count = await loader.sync_to_database(db)

            assert synced_count == 2, f"Expected 2 synced, got {synced_count}"
            print(f"✓ Synced {synced_count} templates to database")

            # Verify in database
            research = await db.get_agent_template("research-agent")
            assert research is not None, "research-agent should exist in database"
            assert research.model == "haiku"
            assert research.temperature == Decimal("0.7")
            assert len(research.tools) == 3
            assert research.color == "blue"
            print("✓ research-agent verified in database")

            test_agent = await db.get_agent_template("test-agent")
            assert test_agent is not None, "test-agent should exist in database"
            assert test_agent.model == "sonnet"
            assert test_agent.temperature == Decimal("0.5")
            print("✓ test-agent verified in database")

            # Test re-sync (should update existing)
            synced_count = await loader.sync_to_database(db)
            assert synced_count == 2, "Re-sync should also sync 2 templates"
            print("✓ Re-sync successful (templates updated)")

            # Cleanup
            await db.pool.execute(
                "DELETE FROM tac_agent_templates WHERE name IN ('research-agent', 'test-agent');"
            )
            print("✓ Cleaned up test data")

        finally:
            await db.close()

    print()


async def test_real_templates():
    """Test 3: Load and sync real templates from .claude/agents"""
    print("Test 3: Real Templates")
    print("-" * 50)

    # Check if .claude/agents exists
    agents_dir = Path.cwd() / ".claude" / "agents"
    if not agents_dir.exists():
        print("⚠ No .claude/agents directory found, skipping")
        print()
        return

    # Load real templates
    loader = AgentTemplateLoader()
    templates = loader.load_all_templates()

    print(f"✓ Loaded {len(templates)} real templates")

    for template in templates:
        print(f"  - {template.name} (model: {template.model}, tools: {len(template.tools)})")

    if templates:
        # Connect to database
        db = TACDatabase()
        await db.connect()

        try:
            # Sync to database
            synced_count = await loader.sync_to_database(db)
            print(f"✓ Synced {synced_count} templates to database")

            # Verify one template
            first_template = templates[0]
            db_template = await db.get_agent_template(first_template.name)
            assert db_template is not None, f"{first_template.name} should exist in database"
            print(f"✓ Verified {first_template.name} in database")

        finally:
            await db.close()

    print()


async def test_list_templates():
    """Test 4: List all templates from database"""
    print("Test 4: List Templates")
    print("-" * 50)

    db = TACDatabase()
    await db.connect()

    try:
        templates = await db.list_agent_templates(active_only=True)
        print(f"✓ Found {len(templates)} active templates in database")

        for template in templates[:5]:  # Show first 5
            print(f"  - {template.name}: {template.description}")

        if len(templates) > 5:
            print(f"  ... and {len(templates) - 5} more")

    finally:
        await db.close()

    print()


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Phase 3 Agent Template Loader Test Suite")
    print("=" * 50)
    print()

    try:
        await test_template_parsing()
        await test_database_sync()
        await test_real_templates()
        await test_list_templates()

        print("=" * 50)
        print("✓ All Phase 3 Tests Passed!")
        print("=" * 50)
        print()
        print("Agent Template System Status:")
        print("  Template parsing: Working")
        print("  YAML frontmatter: Working")
        print("  Database sync: Working")
        print("  Template listing: Working")
        print()
        print("Ready for Phase 4: Helper agent spawn mechanism")
        print()

    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"✗ Test Failed: {e}")
        print("=" * 50)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 50)
        print(f"✗ Error: {e}")
        print("=" * 50)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
