"""
Claude API Usage Logger - Comprehensive tracking of all Claude API calls

Tracks:
- Tokens used (input/output/total)
- Response timing (time to first token, total time, tokens/sec)
- Prompts and responses
- Model and settings
- Cost estimates
- Error information

Logs to JSONL format for easy analysis.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import subprocess


@dataclass
class APICallMetrics:
    """Metrics for a single Claude API call"""

    # Request info
    timestamp: str
    task_id: Optional[str]
    worker_id: Optional[str]
    model: str
    prompt_file: Optional[str]
    prompt_length: int  # Characters

    # Response info
    response_length: Optional[int] = None  # Characters
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tokens_total: Optional[int] = None

    # Timing
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    time_to_first_token: Optional[float] = None
    tokens_per_second: Optional[float] = None

    # Status
    success: bool = False
    error_message: Optional[str] = None
    exit_code: Optional[int] = None

    # Settings
    settings: Optional[Dict[str, Any]] = None

    # Cost (estimated)
    estimated_cost_usd: Optional[float] = None


class ClaudeAPILogger:
    """Logger for Claude API calls with comprehensive metrics"""

    def __init__(self, log_dir: Path, model_catalog: Optional[list] = None):
        """Initialize logger

        Args:
            log_dir: Directory to store logs
            model_catalog: List of model dicts from config (optional)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Build cost table from catalog (or use defaults)
        if model_catalog:
            self.cost_table = self._build_cost_table(model_catalog)
        else:
            # Fallback to hardcoded costs if no catalog provided
            self.cost_table = {
                'claude-sonnet-4-5': {'input': 3.0, 'output': 15.0},
                'claude-opus-4': {'input': 15.0, 'output': 75.0},
                'claude-haiku-4': {'input': 0.25, 'output': 1.25},
            }

        # Daily log file
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.log_dir / f"api-calls-{today}.jsonl"

    def _build_cost_table(self, catalog: list) -> dict:
        """Build cost lookup table from model catalog

        Args:
            catalog: List of model dicts with name, cost_per_million_input, cost_per_million_output

        Returns:
            Dict mapping model name to input/output costs
        """
        cost_table = {}
        for model in catalog:
            cost_table[model['name']] = {
                'input': model.get('cost_per_million_input', 0.0),
                'output': model.get('cost_per_million_output', 0.0)
            }
        return cost_table

    def start_call(self, task_id: Optional[str], worker_id: Optional[str],
                   model: str, prompt_file: Optional[str],
                   prompt_content: str, settings: Optional[Dict] = None) -> APICallMetrics:
        """Start tracking an API call

        Args:
            task_id: Task ID (e.g., "gh-456")
            worker_id: Worker ID (e.g., "w-abc123")
            model: Model name
            prompt_file: Path to prompt file
            prompt_content: Prompt text
            settings: Additional settings (temperature, etc.)

        Returns:
            APICallMetrics object to be updated with results
        """
        metrics = APICallMetrics(
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            worker_id=worker_id,
            model=model,
            prompt_file=str(prompt_file) if prompt_file else None,
            prompt_length=len(prompt_content),
            start_time=time.time(),
            settings=settings
        )

        return metrics

    def end_call(self, metrics: APICallMetrics, response_content: Optional[str] = None,
                 tokens_input: Optional[int] = None, tokens_output: Optional[int] = None,
                 success: bool = True, error_message: Optional[str] = None,
                 exit_code: Optional[int] = None):
        """Complete tracking of an API call

        Args:
            metrics: Metrics object from start_call()
            response_content: Response text
            tokens_input: Input tokens used
            tokens_output: Output tokens used
            success: Whether call succeeded
            error_message: Error message if failed
            exit_code: Process exit code
        """
        metrics.end_time = time.time()
        metrics.duration_seconds = metrics.end_time - metrics.start_time
        metrics.success = success
        metrics.error_message = error_message
        metrics.exit_code = exit_code

        if response_content:
            metrics.response_length = len(response_content)

        if tokens_input:
            metrics.tokens_input = tokens_input

        if tokens_output:
            metrics.tokens_output = tokens_output

        if tokens_input and tokens_output:
            metrics.tokens_total = tokens_input + tokens_output

            # Calculate tokens per second
            if metrics.duration_seconds and metrics.duration_seconds > 0:
                metrics.tokens_per_second = tokens_output / metrics.duration_seconds

            # Estimate cost
            metrics.estimated_cost_usd = self._estimate_cost(
                metrics.model, tokens_input, tokens_output
            )

        # Write to log
        self._write_log(metrics)

    def _estimate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        """Estimate cost in USD

        Args:
            model: Model name
            tokens_input: Input tokens
            tokens_output: Output tokens

        Returns:
            Estimated cost in USD
        """
        if model not in self.cost_table:
            return 0.0

        rates = self.cost_table[model]
        cost_input = (tokens_input / 1_000_000) * rates['input']
        cost_output = (tokens_output / 1_000_000) * rates['output']

        return cost_input + cost_output

    def _write_log(self, metrics: APICallMetrics):
        """Write metrics to JSONL log file"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')

    def parse_stream_json_output(self, output_file: Path) -> Dict[str, Any]:
        """Parse Claude CLI stream-json output to extract metrics

        Args:
            output_file: Path to JSONL output file

        Returns:
            Dict with tokens_input, tokens_output, and response content
        """
        tokens_input = 0
        tokens_output = 0
        response_content = []

        if not output_file.exists():
            return {
                'tokens_input': 0,
                'tokens_output': 0,
                'response_content': ''
            }

        try:
            with open(output_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)

                        # Content delta
                        if event.get('type') == 'content_block_delta':
                            delta = event.get('delta', {})
                            if delta.get('type') == 'text_delta':
                                response_content.append(delta.get('text', ''))

                        # Usage info
                        elif event.get('type') == 'message_start':
                            usage = event.get('message', {}).get('usage', {})
                            tokens_input = usage.get('input_tokens', 0)

                        elif event.get('type') == 'message_delta':
                            usage = event.get('usage', {})
                            tokens_output = usage.get('output_tokens', 0)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"⚠️  Error parsing stream-json output: {e}")

        return {
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'response_content': ''.join(response_content)
        }

    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of API usage for a day

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Summary dict with totals and stats
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        log_file = self.log_dir / f"api-calls-{date}.jsonl"
        if not log_file.exists():
            return {
                'date': date,
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_tokens': 0,
                'total_tokens_input': 0,
                'total_tokens_output': 0,
                'total_cost_usd': 0.0,
                'avg_duration_seconds': 0.0,
                'avg_tokens_per_second': 0.0,
                'models': {}
            }

        total_calls = 0
        successful_calls = 0
        failed_calls = 0
        total_tokens = 0
        total_tokens_input = 0
        total_tokens_output = 0
        total_cost = 0.0
        total_duration = 0.0
        total_tps = 0.0
        models = {}

        with open(log_file, 'r') as f:
            for line in f:
                try:
                    metrics = json.loads(line)
                    total_calls += 1

                    if metrics.get('success'):
                        successful_calls += 1
                    else:
                        failed_calls += 1

                    if metrics.get('tokens_total'):
                        total_tokens += metrics['tokens_total']
                    if metrics.get('tokens_input'):
                        total_tokens_input += metrics['tokens_input']
                    if metrics.get('tokens_output'):
                        total_tokens_output += metrics['tokens_output']
                    if metrics.get('estimated_cost_usd'):
                        total_cost += metrics['estimated_cost_usd']
                    if metrics.get('duration_seconds'):
                        total_duration += metrics['duration_seconds']
                    if metrics.get('tokens_per_second'):
                        total_tps += metrics['tokens_per_second']

                    # Track by model
                    model = metrics.get('model', 'unknown')
                    if model not in models:
                        models[model] = {
                            'calls': 0,
                            'tokens': 0,
                            'cost': 0.0
                        }
                    models[model]['calls'] += 1
                    if metrics.get('tokens_total'):
                        models[model]['tokens'] += metrics['tokens_total']
                    if metrics.get('estimated_cost_usd'):
                        models[model]['cost'] += metrics['estimated_cost_usd']

                except json.JSONDecodeError:
                    continue

        return {
            'date': date,
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_tokens': total_tokens,
            'total_tokens_input': total_tokens_input,
            'total_tokens_output': total_tokens_output,
            'total_cost_usd': round(total_cost, 4),
            'avg_duration_seconds': round(total_duration / total_calls, 2) if total_calls > 0 else 0.0,
            'avg_tokens_per_second': round(total_tps / successful_calls, 2) if successful_calls > 0 else 0.0,
            'models': models
        }
