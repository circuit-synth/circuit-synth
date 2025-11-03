#!/usr/bin/env python3
"""
Multi-Stage Worker Orchestrator

Manages sequential execution of TAC-X pipeline stages:
1. Planning - Analyze issue and create plan
2. Building - Implement plan with test-first development
3. Reviewing - Quality assessment and approval
4. PR Creation - Create GitHub PR

Each stage runs as a separate Claude invocation with fresh, minimal context.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class StageResult:
    """Result from a pipeline stage"""
    stage_name: str
    success: bool
    started_at: str
    completed_at: str
    output_file: Optional[str] = None
    error: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0


@dataclass
class PipelineState:
    """State of multi-stage pipeline"""
    task_id: str
    issue_number: str
    worktree_path: str
    branch_name: str
    current_stage: str = "planning"
    status: str = "running"  # running, completed, errored, blocked
    completed_stages: Dict[str, bool] = field(default_factory=dict)
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class MultiStageWorker:
    """Orchestrates multi-stage autonomous pipeline"""

    def __init__(self, task_id: str, issue_number: str, worktree_path: Path,
                 branch_name: str, llm_config: Dict[str, Any], api_logger):
        self.task_id = task_id
        self.issue_number = issue_number
        self.worktree_path = Path(worktree_path)
        self.branch_name = branch_name
        self.llm_config = llm_config
        self.api_logger = api_logger

        # Create .tac directory structure
        self.tac_dir = self.worktree_path / ".tac"
        self.stages_dir = self.tac_dir / "stages"
        self.outputs_dir = self.tac_dir / "outputs"

        self.tac_dir.mkdir(exist_ok=True)
        self.stages_dir.mkdir(exist_ok=True)
        self.outputs_dir.mkdir(exist_ok=True)

        # Load or init state
        self.state = self.load_or_init_state()

        # Prompts directory
        self.prompts_dir = Path(__file__).parent.parent / "prompts"

    def load_or_init_state(self) -> PipelineState:
        """Load existing pipeline state or create new one"""
        state_file = self.tac_dir / "pipeline.json"

        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)

                state = PipelineState(
                    task_id=data['task_id'],
                    issue_number=data['issue_number'],
                    worktree_path=data['worktree_path'],
                    branch_name=data['branch_name'],
                    current_stage=data['current_stage'],
                    status=data['status'],
                    completed_stages=data['completed_stages'],
                    started_at=data.get('started_at'),
                    completed_at=data.get('completed_at'),
                    error=data.get('error')
                )

                # Restore stage results
                for stage_name, result_data in data.get('stage_results', {}).items():
                    state.stage_results[stage_name] = StageResult(**result_data)

                return state
            except (json.JSONDecodeError, KeyError) as e:
                print(f"   ⚠️  Failed to load state, creating new: {e}")

        # Create new state
        return PipelineState(
            task_id=self.task_id,
            issue_number=self.issue_number,
            worktree_path=str(self.worktree_path),
            branch_name=self.branch_name,
            started_at=datetime.now().isoformat()
        )

    def save_state(self):
        """Save pipeline state to disk"""
        state_file = self.tac_dir / "pipeline.json"

        # Convert dataclass to dict
        state_dict = {
            'task_id': self.state.task_id,
            'issue_number': self.state.issue_number,
            'worktree_path': self.state.worktree_path,
            'branch_name': self.state.branch_name,
            'current_stage': self.state.current_stage,
            'status': self.state.status,
            'completed_stages': self.state.completed_stages,
            'started_at': self.state.started_at,
            'completed_at': self.state.completed_at,
            'error': self.state.error,
            'stage_results': {}
        }

        # Convert stage results
        for stage_name, result in self.state.stage_results.items():
            state_dict['stage_results'][stage_name] = {
                'stage_name': result.stage_name,
                'success': result.success,
                'started_at': result.started_at,
                'completed_at': result.completed_at,
                'output_file': result.output_file,
                'error': result.error,
                'tokens_input': result.tokens_input,
                'tokens_output': result.tokens_output
            }

        with open(state_file, 'w') as f:
            json.dump(state_dict, f, indent=2)

    def run(self) -> PipelineState:
        """Execute all pipeline stages sequentially"""
        print(f"\n🚀 Starting TAC-X Multi-Stage Pipeline for {self.task_id}")
        print(f"   Branch: {self.branch_name}")
        print(f"   Worktree: {self.worktree_path}")
        print()

        # Define pipeline stages
        stages = [
            ("planning", self.run_planner_stage),
            ("building", self.run_builder_stage),
            ("reviewing", self.run_reviewer_stage),
            ("pr_creation", self.run_pr_creator_stage),
        ]

        # Execute stages sequentially
        for stage_name, stage_func in stages:
            # Skip if already completed (resume support)
            if self.state.completed_stages.get(stage_name, False):
                print(f"✓ Stage '{stage_name}' already completed, skipping")
                continue

            # Update current stage
            self.state.current_stage = stage_name
            self.save_state()

            try:
                # Run stage
                result = stage_func()

                # Record result
                self.state.stage_results[stage_name] = result
                self.state.completed_stages[stage_name] = result.success

                if not result.success:
                    # Stage failed
                    self.state.status = 'errored'
                    self.state.error = result.error
                    self.save_state()
                    print(f"   ❌ Pipeline failed at stage '{stage_name}'")
                    return self.state

                self.save_state()

            except Exception as e:
                # Unexpected error
                self.state.status = 'errored'
                self.state.error = str(e)
                self.save_state()
                print(f"   ❌ Pipeline crashed at stage '{stage_name}': {e}")
                raise

        # All stages completed successfully
        self.state.status = 'completed'
        self.state.completed_at = datetime.now().isoformat()
        self.save_state()

        print(f"\n✅ TAC-X Pipeline completed successfully for {self.task_id}")
        return self.state

    def run_planner_stage(self) -> StageResult:
        """Stage 1: Planning - Analyze issue and create plan"""
        print(f"📋 Stage 1: Planning")
        print(f"   Analyzing issue #{self.issue_number}...")

        started_at = datetime.now().isoformat()

        # Fetch issue from GitHub
        issue_data = self._fetch_github_issue()

        # Create context file for planner
        context_file = self.create_planner_context(issue_data)

        # Run planner agent
        result = self.invoke_agent(
            stage="planning",
            prompt_file=self.prompts_dir / "1-planner.md",
            context_vars={
                'task_id': self.task_id,
                'issue_number': self.issue_number,
                'worktree_path': str(self.worktree_path),
                'branch_name': self.branch_name,
                'issue_title': issue_data['title'],
                'issue_body': issue_data['body'],
                'issue_description': f"{issue_data['title']}\n\n{issue_data['body']}"
            }
        )

        completed_at = datetime.now().isoformat()

        # Verify plan.md was created
        plan_file = self.worktree_path / "plan.md"
        if not plan_file.exists():
            return StageResult(
                stage_name="planning",
                success=False,
                started_at=started_at,
                completed_at=completed_at,
                error="Planner did not create plan.md"
            )

        print(f"   ✓ Plan created: plan.md")
        return StageResult(
            stage_name="planning",
            success=True,
            started_at=started_at,
            completed_at=completed_at,
            output_file="plan.md",
            tokens_input=result['tokens_input'],
            tokens_output=result['tokens_output']
        )

    def run_builder_stage(self) -> StageResult:
        """Stage 2: Building - Implement plan with TDD"""
        print(f"\n🔨 Stage 2: Building")
        print(f"   Implementing solution...")

        started_at = datetime.now().isoformat()

        # Load plan content
        plan_file = self.worktree_path / "plan.md"
        plan_content = plan_file.read_text() if plan_file.exists() else "[Plan not found]"

        # Run builder agent
        result = self.invoke_agent(
            stage="building",
            prompt_file=self.prompts_dir / "2-builder.md",
            context_vars={
                'task_id': self.task_id,
                'issue_number': self.issue_number,
                'worktree_path': str(self.worktree_path),
                'branch_name': self.branch_name,
                'plan_path': "plan.md",
                'plan_content': plan_content
            }
        )

        completed_at = datetime.now().isoformat()

        # Verify implementation.md was created
        impl_file = self.worktree_path / "implementation.md"
        success = impl_file.exists()

        if success:
            print(f"   ✓ Implementation complete: implementation.md")
        else:
            print(f"   ⚠️  Builder did not create implementation.md")

        return StageResult(
            stage_name="building",
            success=success,
            started_at=started_at,
            completed_at=completed_at,
            output_file="implementation.md" if success else None,
            error=None if success else "Builder did not create implementation.md",
            tokens_input=result['tokens_input'],
            tokens_output=result['tokens_output']
        )

    def run_reviewer_stage(self) -> StageResult:
        """Stage 3: Reviewing - Quality assessment"""
        print(f"\n✅ Stage 3: Reviewing")
        print(f"   Assessing quality...")

        started_at = datetime.now().isoformat()

        # Load plan and implementation
        plan_file = self.worktree_path / "plan.md"
        impl_file = self.worktree_path / "implementation.md"

        plan_content = plan_file.read_text() if plan_file.exists() else "[Plan not found]"
        impl_content = impl_file.read_text() if impl_file.exists() else "[Implementation not found]"

        # Run reviewer agent
        result = self.invoke_agent(
            stage="reviewing",
            prompt_file=self.prompts_dir / "3-reviewer.md",
            context_vars={
                'task_id': self.task_id,
                'issue_number': self.issue_number,
                'worktree_path': str(self.worktree_path),
                'branch_name': self.branch_name,
                'plan_path': "plan.md",
                'implementation_path': "implementation.md",
                'plan_content': plan_content,
                'implementation_content': impl_content
            }
        )

        completed_at = datetime.now().isoformat()

        # Verify review.md was created
        review_file = self.worktree_path / "review.md"
        if not review_file.exists():
            return StageResult(
                stage_name="reviewing",
                success=False,
                started_at=started_at,
                completed_at=completed_at,
                error="Reviewer did not create review.md"
            )

        # Check if reviewer approved
        review_content = review_file.read_text()
        approved = "APPROVED FOR PR CREATION" in review_content

        if approved:
            print(f"   ✓ Review complete: APPROVED")
        else:
            print(f"   ⚠️  Review complete: NEEDS WORK or BLOCKED")
            # Don't fail the stage, but mark as needing human intervention

        return StageResult(
            stage_name="reviewing",
            success=True,  # Stage succeeded even if approval was not granted
            started_at=started_at,
            completed_at=completed_at,
            output_file="review.md",
            tokens_input=result['tokens_input'],
            tokens_output=result['tokens_output']
        )

    def run_pr_creator_stage(self) -> StageResult:
        """Stage 4: PR Creation - Create GitHub PR"""
        print(f"\n🎉 Stage 4: PR Creation")

        started_at = datetime.now().isoformat()

        # Load review to check approval
        review_file = self.worktree_path / "review.md"
        review_content = review_file.read_text() if review_file.exists() else ""

        approved = "APPROVED FOR PR CREATION" in review_content

        if not approved:
            print(f"   ⚠️  Reviewer did not approve - skipping PR creation")
            print(f"   Human intervention needed")
            return StageResult(
                stage_name="pr_creation",
                success=True,  # Not a failure, just paused
                started_at=started_at,
                completed_at=datetime.now().isoformat(),
                error="Reviewer did not approve - human intervention needed"
            )

        print(f"   Creating pull request...")

        # Load all context
        plan_content = (self.worktree_path / "plan.md").read_text() if (self.worktree_path / "plan.md").exists() else ""
        impl_content = (self.worktree_path / "implementation.md").read_text() if (self.worktree_path / "implementation.md").exists() else ""

        # Run PR creator agent
        result = self.invoke_agent(
            stage="pr_creation",
            prompt_file=self.prompts_dir / "4-pr-creator.md",
            context_vars={
                'task_id': self.task_id,
                'issue_number': self.issue_number,
                'worktree_path': str(self.worktree_path),
                'branch_name': self.branch_name,
                'plan_path': "plan.md",
                'implementation_path': "implementation.md",
                'review_path': "review.md",
                'review_verdict': "APPROVED FOR PR CREATION"
            }
        )

        completed_at = datetime.now().isoformat()

        print(f"   ✓ PR created successfully")

        return StageResult(
            stage_name="pr_creation",
            success=True,
            started_at=started_at,
            completed_at=completed_at,
            tokens_input=result['tokens_input'],
            tokens_output=result['tokens_output']
        )

    def create_planner_context(self, issue_data: Dict[str, str]) -> Path:
        """Create minimal context file for planning stage"""
        context = f"""# Planning Context for {self.task_id}

## GitHub Issue

**Issue:** #{self.issue_number}
**Title:** {issue_data['title']}

**Description:**
{issue_data['body']}

## Your Task

Create a detailed implementation plan in `plan.md`.

Use Read, Grep, Glob to explore the codebase (read-only).
Do NOT make code changes - only plan.
"""

        context_file = self.tac_dir / "context-planning.md"
        context_file.write_text(context)
        return context_file

    def invoke_agent(self, stage: str, prompt_file: Path, context_vars: Dict[str, str]) -> Dict[str, Any]:
        """Invoke Claude for a specific stage with fresh context"""

        # Substitute variables in prompt
        prompt_content = prompt_file.read_text()
        for key, value in context_vars.items():
            prompt_content = prompt_content.replace(f"{{{key}}}", str(value))

        # Write substituted prompt
        stage_prompt_file = self.stages_dir / f"{stage}-prompt.md"
        stage_prompt_file.write_text(prompt_content)

        # Prepare log file
        log_file = self.stages_dir / f"{stage}.jsonl"

        # Build command
        cmd = [
            "claude",
            "-p", str(stage_prompt_file),
            "--output-format", "jsonl"
        ]

        print(f"   Running: claude -p {stage_prompt_file.name}")

        # Run agent
        with open(log_file, 'w') as f:
            proc = subprocess.run(
                cmd,
                cwd=self.worktree_path,
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=3600  # 1 hour timeout
            )

        # Parse tokens from JSONL
        tokens_input = 0
        tokens_output = 0

        if log_file.exists():
            with open(log_file) as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get('type') == 'usage':
                            tokens_input = event.get('input_tokens', 0)
                            tokens_output = event.get('output_tokens', 0)
                    except json.JSONDecodeError:
                        continue

        return {
            'returncode': proc.returncode,
            'tokens_input': tokens_input,
            'tokens_output': tokens_output
        }

    def _fetch_github_issue(self) -> Dict[str, str]:
        """Fetch GitHub issue details"""
        try:
            result = subprocess.run(
                ["gh", "issue", "view", self.issue_number, "--json", "title,body"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'title': data.get('title', '[No title]'),
                    'body': data.get('body', '[No description]')
                }
        except Exception as e:
            print(f"   ⚠️  Failed to fetch issue: {e}")

        return {
            'title': f"Issue #{self.issue_number}",
            'body': "[Failed to fetch issue description]"
        }
