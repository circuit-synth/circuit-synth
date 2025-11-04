#!/usr/bin/env python3
"""
Test TAC-X multi-stage pipeline with custom workflow configurations
Tests issue #504 with different LLM providers via OpenRouter
"""

import os
import sys
import logging
from pathlib import Path
import subprocess
import shutil

# Add adws module to path
sys.path.insert(0, str(Path(__file__).parent / "adws"))

from adw_modules.workflow_config import WorkflowConfig
from adw_modules.multi_stage_worker import MultiStageWorker
from adw_modules.api_logger import ClaudeAPILogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_worktree(issue_number: str, workflow_name: str) -> Path:
    """Create a git worktree for testing"""
    base_dir = Path(__file__).parent / "trees"
    base_dir.mkdir(exist_ok=True)

    worktree_name = f"gh-{issue_number}-{workflow_name}"
    worktree_path = base_dir / worktree_name
    branch_name = f"test/issue-{issue_number}-{workflow_name}"

    # Remove existing worktree if it exists
    if worktree_path.exists():
        logger.info(f"Removing existing worktree: {worktree_path}")
        subprocess.run(["git", "worktree", "remove", str(worktree_path), "--force"],
                      capture_output=True)

    # Create new worktree
    logger.info(f"Creating worktree: {worktree_path}")
    result = subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, str(worktree_path), "main"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # Branch might already exist, try without -b
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")

    return worktree_path


def test_workflow(workflow_path: Path, issue_number: str, workflow_name: str):
    """Test the pipeline with a specific workflow configuration"""

    print("\n" + "=" * 80)
    print(f"TESTING WORKFLOW: {workflow_name}")
    print("=" * 80)

    # Check API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return False

    # Load workflow
    print(f"\n1. Loading workflow from {workflow_path}")
    try:
        workflow = WorkflowConfig.from_yaml(workflow_path)
        print(f"   ✓ Workflow loaded: {workflow.name}")
        print(f"   ✓ Stages: {len(workflow.stages)}")
        for stage in workflow.stages:
            print(f"     - {stage.name}: {stage.provider}/{stage.model}")
    except Exception as e:
        print(f"   ❌ Failed to load workflow: {e}")
        return False

    # Setup worktree
    print(f"\n2. Setting up worktree for issue #{issue_number}")
    try:
        worktree_path = setup_worktree(issue_number, workflow_name)
        print(f"   ✓ Worktree created: {worktree_path}")
    except Exception as e:
        print(f"   ❌ Failed to create worktree: {e}")
        return False

    # Fetch issue details
    print(f"\n3. Fetching issue #{issue_number} from GitHub")
    try:
        result = subprocess.run(
            ["gh", "issue", "view", issue_number, "--json", "title,body"],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        issue_data = json.loads(result.stdout)
        print(f"   ✓ Issue: {issue_data['title']}")
    except Exception as e:
        print(f"   ❌ Failed to fetch issue: {e}")
        return False

    # Create LLM config and API logger
    print(f"\n4. Initializing worker")
    try:
        # LLM config is a simple dict (will be overridden by workflow anyway)
        llm_config = {
            "provider": "openrouter",
            "model": "default",
            "command_template": [],
            "model_default": "default"
        }

        api_logger = ClaudeAPILogger(
            log_dir=Path(__file__).parent / "logs" / "api"
        )

        print(f"   ✓ LLM config created")
        print(f"   ✓ API logger initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return False

    # Create worker with custom workflow
    print(f"\n5. Creating MultiStageWorker with custom workflow")
    try:
        worker = MultiStageWorker(
            task_id=f"gh-{issue_number}",
            issue_number=issue_number,
            worktree_path=worktree_path,
            branch_name=f"test/issue-{issue_number}-{workflow_name}",
            llm_config=llm_config,
            api_logger=api_logger,
            workflow_config=workflow  # Custom workflow!
        )
        print(f"   ✓ Worker created with {len(workflow.stages)} stages")
    except Exception as e:
        print(f"   ❌ Failed to create worker: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Execute pipeline
    print(f"\n6. Executing pipeline")
    print("   This will run all 4 stages: planning → building → reviewing → pr_creation")
    print("   " + "-" * 76)

    try:
        state = worker.run()

        if state.status == "completed":
            print("\n   " + "=" * 76)
            print("   ✅ PIPELINE COMPLETED SUCCESSFULLY")
            print("   " + "=" * 76)
            success = True
        else:
            print("\n   " + "=" * 76)
            print(f"   ❌ PIPELINE FAILED - Status: {state.status}")
            print("   " + "=" * 76)
            success = False

    except Exception as e:
        print(f"\n   ❌ Pipeline execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Display results
    print(f"\n7. Results")
    tac_dir = worktree_path / ".tac"

    if tac_dir.exists():
        print(f"\n   📁 TAC artifacts in: {tac_dir}")

        # Show workflow used
        workflow_file = tac_dir / "workflow.yaml"
        if workflow_file.exists():
            print(f"   ✓ Workflow config: {workflow_file}")

        # Show stage logs
        stages_dir = tac_dir / "stages"
        if stages_dir.exists():
            stage_files = sorted(stages_dir.glob("*.jsonl"))
            print(f"\n   📊 Stage execution logs:")
            for stage_file in stage_files:
                size_kb = stage_file.stat().st_size / 1024
                print(f"     - {stage_file.name}: {size_kb:.1f} KB")

        # Show cost estimate
        print(f"\n   💰 Cost Analysis:")
        print(f"     Run: python3 tools/analyze-pipeline.py gh-{issue_number}-{workflow_name}")

    print("\n" + "=" * 80)
    return success


def main():
    """Run tests with both workflows"""

    print("TAC-X Multi-Provider Pipeline Test")
    print("=" * 80)
    print("Testing issue #504 with multiple LLM providers via OpenRouter")
    print()

    issue_number = "504"

    # Test 1: Gemini 2.5 Flash
    workflow_gemini = Path("/tmp/workflow-gemini-2.5-flash.yaml")
    if workflow_gemini.exists():
        result_gemini = test_workflow(workflow_gemini, issue_number, "gemini")
    else:
        print(f"❌ Workflow file not found: {workflow_gemini}")
        result_gemini = False

    # Test 2: Grok Code Fast 1
    workflow_grok = Path("/tmp/workflow-grok-code-fast-1.yaml")
    if workflow_grok.exists():
        result_grok = test_workflow(workflow_grok, issue_number, "grok")
    else:
        print(f"❌ Workflow file not found: {workflow_grok}")
        result_grok = False

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Gemini 2.5 Flash:  {'✅ PASSED' if result_gemini else '❌ FAILED'}")
    print(f"Grok Code Fast 1: {'✅ PASSED' if result_grok else '❌ FAILED'}")
    print("=" * 80)

    return result_gemini and result_grok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
