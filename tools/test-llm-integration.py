#!/usr/bin/env python3
"""
LLM Integration Test Suite

Tests TAC components with REAL LLM API calls to validate end-to-end functionality.

This test suite makes actual API calls to:
- Claude Code (Anthropic)
- OpenRouter

Tests include:
- Helper agent spawning with real execution
- Token counting and cost tracking
- Database tracking of real LLM usage
- TACWorkerAdapter integration with real agents

IMPORTANT: This test will incur small API costs (est. $0.10-0.50).
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_database import TACDatabase
from adw_modules.tac_models import TaskCreate, StageCreate
from adw_modules.tac_helper_manager import HelperAgentManager
from adw_modules.tac_worker_adapter import TACWorkerAdapter
from adw_modules.tac_agent_loader import AgentTemplateLoader


# Simple test helper template for LLM integration
TEST_HELPER_TEMPLATE = """---
name: llm-test-helper
description: Simple test helper for LLM integration testing
model: haiku
temperature: 0.3
tools: []
color: blue
---

You are a test helper agent for validating LLM integration.

When given a task, respond with a brief JSON object containing:
- "status": "success"
- "task_received": <the task you received>
- "response": <a brief 1-sentence response>

Keep responses very short to minimize API costs.
"""


async def setup_test_template(db: TACDatabase):
    """Create test template in database"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Write test template
        (tmpdir_path / "llm-test-helper.md").write_text(TEST_HELPER_TEMPLATE)

        # Load and sync to database
        loader = AgentTemplateLoader(agents_dir=tmpdir_path)
        await loader.sync_to_database(db)

        print("✓ Test template created")


async def test_helper_with_anthropic():
    """Test 1: Helper agent execution with Anthropic Claude"""
    print("Test 1: Helper Agent with Anthropic Claude")
    print("-" * 50)

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set, skipping test")
        print()
        return

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-LLM-001"))
        stage_id = await db.create_stage(StageCreate(
            task_id=task_id,
            stage_name="planning",
        ))

        print(f"✓ Created task {task_id}")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Spawn helper with real LLM execution
        print("⚡ Spawning helper with Anthropic Claude (Haiku)...")
        async with manager.spawn_helper(
            task_id=task_id,
            stage_id=stage_id,
            template_name="llm-test-helper",
            purpose="Test Anthropic API integration",
            provider="anthropic",
        ) as helper:
            print(f"✓ Helper spawned: {helper.agent_name}")

            # Execute helper with real LLM call
            prompt = "Please respond with the status JSON as instructed. Task: Verify Anthropic integration works."

            print("⚡ Executing helper with real API call...")
            result = await helper.run(prompt=prompt)

            print(f"✓ Helper executed")
            print(f"  Status: {result['status']}")
            print(f"  Message: {result['message'][:100]}...")

            # Verify token usage was tracked
            assert helper.input_tokens > 0, "Should have input tokens"
            assert helper.output_tokens > 0, "Should have output tokens"
            assert helper.cost > Decimal("0"), "Should have cost"

            print(f"✓ Token usage tracked:")
            print(f"  Input tokens: {helper.input_tokens}")
            print(f"  Output tokens: {helper.output_tokens}")
            print(f"  Cost: ${helper.cost}")

        # Verify helper was tracked in database
        helper_db = await db.get_helper_with_events(helper.helper_id)
        assert helper_db.helper.status == "completed", "Helper should be completed"
        assert helper_db.helper.input_tokens > 0, "Should have tracked tokens"

        print("✓ Helper tracked in database with real usage")

        # Verify cost rolled up to task
        task = await db.get_task(task_id)
        assert task.total_cost >= helper.cost, "Cost should roll up to task"
        print(f"✓ Cost rolled up to task: ${task.total_cost}")

        print("✓ Anthropic integration test PASSED")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-LLM-%';"
        )
        await db.pool.execute(
            "DELETE FROM tac_agent_templates WHERE name = 'llm-test-helper';"
        )
        await db.close()

    print()


async def test_helper_with_openrouter():
    """Test 2: Helper agent execution with OpenRouter"""
    print("Test 2: Helper Agent with OpenRouter")
    print("-" * 50)

    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠ OPENROUTER_API_KEY not set, skipping test")
        print()
        return

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-LLM-002"))
        stage_id = await db.create_stage(StageCreate(
            task_id=task_id,
            stage_name="building",
        ))

        print(f"✓ Created task {task_id}")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Spawn helper with real LLM execution via OpenRouter
        print("⚡ Spawning helper with OpenRouter (Claude Haiku)...")
        async with manager.spawn_helper(
            task_id=task_id,
            stage_id=stage_id,
            template_name="llm-test-helper",
            purpose="Test OpenRouter API integration",
            provider="openrouter",
            model_override="anthropic/claude-3-haiku",
        ) as helper:
            print(f"✓ Helper spawned: {helper.agent_name}")

            # Execute helper with real LLM call
            prompt = "Please respond with the status JSON. Task: Verify OpenRouter integration works."

            print("⚡ Executing helper with real API call...")
            result = await helper.run(prompt=prompt)

            print(f"✓ Helper executed")
            print(f"  Status: {result['status']}")

            # Verify token usage was tracked
            assert helper.input_tokens > 0, "Should have input tokens"
            assert helper.output_tokens > 0, "Should have output tokens"
            assert helper.cost > Decimal("0"), "Should have cost"

            print(f"✓ Token usage tracked:")
            print(f"  Input tokens: {helper.input_tokens}")
            print(f"  Output tokens: {helper.output_tokens}")
            print(f"  Cost: ${helper.cost}")

        print("✓ OpenRouter integration test PASSED")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-LLM-%';"
        )
        await db.pool.execute(
            "DELETE FROM tac_agent_templates WHERE name = 'llm-test-helper';"
        )
        await db.close()

    print()


async def test_worker_adapter_with_real_llm():
    """Test 3: TACWorkerAdapter with real LLM execution"""
    print("Test 3: TACWorkerAdapter with Real LLM")
    print("-" * 50)

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set, skipping test")
        print()
        return

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create temp worktree
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir)

            # Create worker adapter
            print("⚡ Creating TACWorkerAdapter...")
            worker = await TACWorkerAdapter.create(
                issue_number="TEST-LLM-003",
                worktree_path=worktree_path,
                branch_name="test/llm-003",
                llm_config={"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
                api_logger=None,
                database=db,
            )

            print(f"✓ Worker created with task_id: {worker.task_id}")

            # Start a stage
            stage_id = await worker.log_stage_start("planning")
            print(f"✓ Stage 'planning' started")

            # Spawn helper via adapter with real LLM
            print("⚡ Spawning helper via adapter...")
            async with worker.spawn_helper(
                template_name="llm-test-helper",
                purpose="Test adapter integration with real LLM",
            ) as helper:
                print(f"✓ Helper spawned: {helper.agent_name}")

                # Execute with real LLM
                print("⚡ Executing helper...")
                result = await helper.run(prompt="Test task: Validate adapter integration")

                print(f"✓ Helper executed")
                assert helper.input_tokens > 0, "Should have tokens"
                print(f"  Tokens: {helper.input_tokens} → {helper.output_tokens}")
                print(f"  Cost: ${helper.cost}")

            # Verify everything tracked correctly
            task_summary = await db.get_task_summary(worker.task_id)

            assert len(task_summary.stages) == 1, "Should have 1 stage"
            assert len(task_summary.helpers) == 1, "Should have 1 helper"
            assert task_summary.helpers[0].status == "completed", "Helper should be completed"
            assert task_summary.task.total_cost > Decimal("0"), "Should have cost"

            print(f"✓ Complete task summary:")
            print(f"  Stages: {len(task_summary.stages)}")
            print(f"  Helpers: {len(task_summary.helpers)}")
            print(f"  Total cost: ${task_summary.task.total_cost}")
            print(f"  Total tokens: {task_summary.task.total_input_tokens} → {task_summary.task.total_output_tokens}")

        print("✓ TACWorkerAdapter integration test PASSED")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-LLM-%';"
        )
        await db.pool.execute(
            "DELETE FROM tac_agent_templates WHERE name = 'llm-test-helper';"
        )
        await db.close()

    print()


async def test_concurrent_helpers():
    """Test 4: Multiple concurrent helpers with real LLM calls"""
    print("Test 4: Concurrent Helpers with Real LLM")
    print("-" * 50)

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set, skipping test")
        print()
        return

    db = TACDatabase()
    await db.connect()

    try:
        # Setup test template
        await setup_test_template(db)

        # Create task and stage
        task_id = await db.create_task(TaskCreate(issue_number="TEST-LLM-004"))
        stage_id = await db.create_stage(StageCreate(
            task_id=task_id,
            stage_name="building",
        ))

        print(f"✓ Created task {task_id}")

        # Create helper manager
        manager = HelperAgentManager(db)

        # Spawn 3 helpers concurrently
        async def spawn_and_run(n: int):
            async with manager.spawn_helper(
                task_id=task_id,
                stage_id=stage_id,
                template_name="llm-test-helper",
                purpose=f"Concurrent helper {n}",
            ) as helper:
                result = await helper.run(prompt=f"Task {n}: Quick test")
                return helper.helper_id, helper.cost

        print("⚡ Spawning 3 concurrent helpers with real LLM calls...")
        results = await asyncio.gather(
            spawn_and_run(1),
            spawn_and_run(2),
            spawn_and_run(3),
        )

        print(f"✓ All 3 helpers completed")

        # Verify all helpers completed
        total_cost = Decimal("0")
        for helper_id, cost in results:
            helper_db = await db.get_helper_with_events(helper_id)
            assert helper_db.helper.status == "completed", f"Helper {helper_id} should be completed"
            total_cost += cost
            print(f"  Helper {helper_id}: ${cost}")

        # Verify cost aggregation
        task = await db.get_task(task_id)
        assert task.total_cost >= total_cost, "All costs should roll up"
        print(f"✓ Total cost aggregated: ${task.total_cost}")

        print("✓ Concurrent helpers test PASSED")

    finally:
        # Cleanup
        await db.pool.execute(
            "DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-LLM-%';"
        )
        await db.pool.execute(
            "DELETE FROM tac_agent_templates WHERE name = 'llm-test-helper';"
        )
        await db.close()

    print()


async def main():
    """Run all LLM integration tests"""
    print("=" * 50)
    print("LLM Integration Test Suite")
    print("=" * 50)
    print()
    print("IMPORTANT: These tests make REAL API calls and will incur small costs.")
    print("Estimated cost: $0.10 - $0.50")
    print()

    # Check for required API keys
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))

    if not has_anthropic and not has_openrouter:
        print("✗ No API keys found!")
        print()
        print("Please set at least one of:")
        print("  export ANTHROPIC_API_KEY=sk-...")
        print("  export OPENROUTER_API_KEY=sk-or-v1-...")
        print()
        sys.exit(1)

    print(f"API Keys found:")
    print(f"  Anthropic: {'✓' if has_anthropic else '✗'}")
    print(f"  OpenRouter: {'✓' if has_openrouter else '✗'}")
    print()

    try:
        # Run tests
        await test_helper_with_anthropic()
        await test_helper_with_openrouter()
        await test_worker_adapter_with_real_llm()
        await test_concurrent_helpers()

        print("=" * 50)
        print("✓ All LLM Integration Tests Passed!")
        print("=" * 50)
        print()
        print("Validated:")
        print("  ✓ Helper agent execution with real LLM")
        print("  ✓ Token counting and cost tracking")
        print("  ✓ Database tracking of real usage")
        print("  ✓ TACWorkerAdapter integration")
        print("  ✓ Concurrent helper execution")
        print("  ✓ Cost aggregation across helpers")
        print()
        print("Ready for production use!")
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
