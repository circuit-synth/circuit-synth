#!/usr/bin/env python3
"""
TAC-X Pipeline Analysis Tool

Comprehensive analysis of multi-stage pipeline execution.
Generates reports, summaries, and investigation data for human review.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import argparse


class PipelineAnalyzer:
    """Analyze TAC-X pipeline execution"""

    def __init__(self, task_id: str, repo_root: Path = None):
        self.task_id = task_id
        self.repo_root = repo_root or Path.cwd()
        self.worktree_path = self.repo_root / "trees" / task_id
        self.tac_dir = self.worktree_path / ".tac"

        if not self.tac_dir.exists():
            print(f"❌ Task {task_id} not found at {self.worktree_path}")
            sys.exit(1)

    def analyze(self) -> Dict[str, Any]:
        """Complete analysis of pipeline"""
        return {
            'task_id': self.task_id,
            'worktree_path': str(self.worktree_path),
            'pipeline_state': self.load_pipeline_state(),
            'stages': self.analyze_stages(),
            'outputs': self.analyze_outputs(),
            'git_info': self.analyze_git(),
            'tokens': self.analyze_tokens(),
            'timeline': self.create_timeline()
        }

    def load_pipeline_state(self) -> Dict[str, Any]:
        """Load pipeline state"""
        state_file = self.tac_dir / "pipeline.json"
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {}

    def analyze_stages(self) -> List[Dict[str, Any]]:
        """Analyze each pipeline stage"""
        stages_dir = self.tac_dir / "stages"
        if not stages_dir.exists():
            return []

        stages = []
        for stage_file in sorted(stages_dir.glob("*.jsonl")):
            stage_name = stage_file.stem
            stages.append({
                'name': stage_name,
                'log_file': str(stage_file),
                'log_size': stage_file.stat().st_size,
                'events': self.count_events(stage_file),
                'tokens': self.extract_tokens(stage_file)
            })

        return stages

    def count_events(self, jsonl_file: Path) -> Dict[str, int]:
        """Count event types in JSONL log"""
        counts = {}
        with open(jsonl_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    event_type = event.get('type', 'unknown')
                    counts[event_type] = counts.get(event_type, 0) + 1
                except json.JSONDecodeError:
                    continue
        return counts

    def extract_tokens(self, jsonl_file: Path) -> Dict[str, int]:
        """Extract token usage from JSONL"""
        tokens = {'input': 0, 'output': 0}
        with open(jsonl_file) as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if event.get('type') == 'usage':
                        tokens['input'] = event.get('input_tokens', 0)
                        tokens['output'] = event.get('output_tokens', 0)
                except json.JSONDecodeError:
                    continue
        return tokens

    def analyze_outputs(self) -> Dict[str, Any]:
        """Analyze output artifacts"""
        outputs = {}

        # Check for key output files
        for artifact in ['plan.md', 'implementation.md', 'review.md']:
            artifact_path = self.worktree_path / artifact
            if artifact_path.exists():
                outputs[artifact] = {
                    'exists': True,
                    'size': artifact_path.stat().st_size,
                    'lines': len(artifact_path.read_text().splitlines()),
                    'preview': artifact_path.read_text()[:500]
                }
            else:
                outputs[artifact] = {'exists': False}

        return outputs

    def analyze_git(self) -> Dict[str, Any]:
        """Analyze git information"""
        import subprocess

        try:
            # Get commit count
            commit_count = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True
            ).stdout.strip()

            # Get last commit
            last_commit = subprocess.run(
                ["git", "log", "-1", "--oneline"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True
            ).stdout.strip()

            # Get diff stats
            diff_stats = subprocess.run(
                ["git", "diff", "--stat", "main...HEAD"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True
            ).stdout.strip()

            return {
                'commit_count': commit_count,
                'last_commit': last_commit,
                'diff_stats': diff_stats
            }
        except Exception as e:
            return {'error': str(e)}

    def analyze_tokens(self) -> Dict[str, Any]:
        """Aggregate token usage across all stages"""
        total_input = 0
        total_output = 0

        stages_dir = self.tac_dir / "stages"
        if stages_dir.exists():
            for stage_file in stages_dir.glob("*.jsonl"):
                tokens = self.extract_tokens(stage_file)
                total_input += tokens['input']
                total_output += tokens['output']

        total = total_input + total_output
        return {
            'total_input': total_input,
            'total_output': total_output,
            'total': total,
            'cost_estimate': self.estimate_cost(total_input, total_output)
        }

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost (Sonnet 4 pricing)"""
        # Claude Sonnet 4: $3/M input, $15/M output
        input_cost = (input_tokens / 1_000_000) * 3.0
        output_cost = (output_tokens / 1_000_000) * 15.0
        return round(input_cost + output_cost, 4)

    def create_timeline(self) -> List[Dict[str, str]]:
        """Create timeline of pipeline events"""
        state = self.load_pipeline_state()
        timeline = []

        if state.get('started_at'):
            timeline.append({
                'time': state['started_at'],
                'event': 'Pipeline started'
            })

        for stage_name, result in state.get('stage_results', {}).items():
            timeline.append({
                'time': result['started_at'],
                'event': f"Stage '{stage_name}' started"
            })
            timeline.append({
                'time': result['completed_at'],
                'event': f"Stage '{stage_name}' completed ({'✓' if result['success'] else '✗'})"
            })

        if state.get('completed_at'):
            timeline.append({
                'time': state['completed_at'],
                'event': f"Pipeline completed (status: {state.get('status')})"
            })

        return timeline

    def print_report(self, analysis: Dict[str, Any]):
        """Print human-readable report"""
        print("=" * 80)
        print(f"TAC-X PIPELINE ANALYSIS: {self.task_id}")
        print("=" * 80)
        print()

        # Pipeline status
        state = analysis['pipeline_state']
        print(f"📊 Status: {state.get('status', 'unknown').upper()}")
        print(f"📁 Worktree: {analysis['worktree_path']}")
        print(f"🌿 Branch: {state.get('branch_name')}")
        print(f"⏰ Started: {state.get('started_at', 'N/A')}")
        print(f"⏰ Completed: {state.get('completed_at', 'N/A')}")
        print()

        # Stages
        print("=" * 80)
        print("PIPELINE STAGES")
        print("=" * 80)
        for stage in analysis['stages']:
            print(f"\n📋 Stage: {stage['name']}")
            print(f"   Log: {stage['log_file']}")
            print(f"   Size: {stage['log_size']:,} bytes")
            print(f"   Events: {dict(stage['events'])}")
            print(f"   Tokens: {stage['tokens']['input']:,} in / {stage['tokens']['output']:,} out")
        print()

        # Outputs
        print("=" * 80)
        print("OUTPUT ARTIFACTS")
        print("=" * 80)
        for artifact, info in analysis['outputs'].items():
            if info['exists']:
                print(f"\n✓ {artifact}")
                print(f"   Size: {info['size']:,} bytes")
                print(f"   Lines: {info['lines']}")
                print(f"   Preview: {info['preview'][:100]}...")
            else:
                print(f"\n✗ {artifact} - NOT FOUND")
        print()

        # Git info
        print("=" * 80)
        print("GIT INFORMATION")
        print("=" * 80)
        git = analysis['git_info']
        if 'error' not in git:
            print(f"Commits: {git['commit_count']}")
            print(f"Last commit: {git['last_commit']}")
            print(f"\nDiff stats:")
            print(git['diff_stats'])
        else:
            print(f"Error: {git['error']}")
        print()

        # Token usage
        print("=" * 80)
        print("TOKEN USAGE & COST")
        print("=" * 80)
        tokens = analysis['tokens']
        print(f"Input tokens: {tokens['total_input']:,}")
        print(f"Output tokens: {tokens['total_output']:,}")
        print(f"Total tokens: {tokens['total']:,}")
        print(f"Estimated cost: ${tokens['cost_estimate']:.4f}")
        print()

        # Timeline
        print("=" * 80)
        print("TIMELINE")
        print("=" * 80)
        for entry in analysis['timeline']:
            print(f"{entry['time']}: {entry['event']}")
        print()

        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Analyze TAC-X pipeline execution")
    parser.add_argument("task_id", help="Task ID (e.g., gh-500)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save", help="Save report to file")

    args = parser.parse_args()

    analyzer = PipelineAnalyzer(args.task_id)
    analysis = analyzer.analyze()

    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        analyzer.print_report(analysis)

    if args.save:
        report_file = Path(args.save)
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"✓ Report saved to {report_file}")


if __name__ == "__main__":
    main()
