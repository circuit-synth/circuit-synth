#!/usr/bin/env python3
"""Test TACWorkerAdapter directly"""
import sys
import asyncio
from pathlib import Path
import tomllib

# Add adws to path
sys.path.insert(0, str(Path(__file__).parent / "adws"))

from adw_modules.tac_worker_adapter import TACWorkerAdapter
from adw_modules.tac_database import TACDatabase
from adw_modules.api_logger import ClaudeAPILogger
from adw_modules.workflow_config import WorkflowConfig

# Load config
config_file = Path(__file__).parent / "adws" / "config.toml"
with open(config_file, "rb") as f:
    config = tomllib.load(f)

# Create API logger
api_logger = ClaudeAPILogger(Path(__file__).parent / "logs" / "api")

async def main():
    """Test TAC worker"""
    print("=" * 80)
    print("TESTING TAC WORKER ADAPTER")
    print("=" * 80)

    # Initialize database
    db = TACDatabase()
    await db.connect()
    print("✓ Connected to TAC database")

    try:
        # Load workflow configuration
        workflow_yaml = Path("trees/gh-504/.tac/workflow.yaml")
        workflow_config = None
        if workflow_yaml.exists():
            print(f"\nLoading workflow from {workflow_yaml}")
            workflow_config = WorkflowConfig.from_yaml(workflow_yaml)
        else:
            print("\nNo workflow.yaml found, using default")

        # Create TAC worker adapter
        print("\nCreating TACWorkerAdapter...")
        worker = await TACWorkerAdapter.create(
            issue_number="gh-504",
            worktree_path=Path("trees/gh-504"),
            branch_name="auto/test-worker",
            llm_config=config['llm'],
            api_logger=api_logger,
            database=db,
            full_config=config,
            workflow_config=workflow_config
        )

        print(f"✓ Created TAC worker (task_id={worker.task_id})")

        # Run pipeline with full tracking
        print("\n" + "=" * 80)
        print("RUNNING PIPELINE")
        print("=" * 80)
        await worker.run()

        print(f"\n✓ Pipeline completed")
        return 0
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Close database connection
        await db.close()
        print("✓ Closed database connection")

# Run async main
if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
