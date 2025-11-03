#!/usr/bin/env python3
"""
OpenRouter CLI wrapper - makes OpenRouter API compatible with provider system

Usage:
    openrouter-cli.py -p <prompt_file> --model <model> --output-file <output_file>

Reads prompt from file, calls OpenRouter API, outputs stream-json format compatible with Claude CLI.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path


def call_openrouter_api(prompt: str, model: str, api_key: str) -> dict:
    """Call OpenRouter API with prompt

    Args:
        prompt: The prompt text
        model: Model name (e.g., 'anthropic/claude-3.5-sonnet')
        api_key: OpenRouter API key

    Returns:
        API response dict
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/circuit-synth/circuit-synth",
        "X-Title": "Circuit-Synth TAC-8 Coordinator"
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.loads(response.read())
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"OpenRouter API error: {e.code} - {error_body}")


def write_stream_json_output(output_file: Path, response: dict, prompt_tokens: int, completion_tokens: int, duration_ms: int):
    """Write output in stream-json format compatible with Claude CLI

    Args:
        output_file: Path to output file
        response: OpenRouter API response
        prompt_tokens: Input token count
        completion_tokens: Output token count
        duration_ms: Duration in milliseconds
    """
    # Extract response text
    content = response.get('choices', [{}])[0].get('message', {}).get('content', '')

    # Write stream-json format (compatible with Claude CLI output)
    with open(output_file, 'w') as f:
        # Init event
        init_event = {
            "type": "system",
            "subtype": "init",
            "model": response.get('model', 'unknown'),
            "provider": "openrouter"
        }
        f.write(json.dumps(init_event) + '\n')

        # Message event
        message_event = {
            "type": "assistant",
            "message": {
                "id": response.get('id', 'unknown'),
                "role": "assistant",
                "content": [
                    {"type": "text", "text": content}
                ],
                "model": response.get('model', 'unknown'),
                "usage": {
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens
                }
            }
        }
        f.write(json.dumps(message_event) + '\n')

        # Result event
        result_event = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "duration_ms": duration_ms,
            "result": content[:200],  # Truncate for summary
            "usage": {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens
            }
        }
        f.write(json.dumps(result_event) + '\n')


def main():
    parser = argparse.ArgumentParser(description='OpenRouter CLI wrapper')
    parser.add_argument('-p', '--prompt', required=True, help='Path to prompt file')
    parser.add_argument('--model', required=True, help='Model name (e.g., anthropic/claude-3.5-sonnet)')
    parser.add_argument('--output-file', required=True, help='Path to output file (stream-json format)')
    parser.add_argument('--output-format', default='stream-json', help='Output format (only stream-json supported)')

    args = parser.parse_args()

    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Read prompt
    prompt_file = Path(args.prompt)
    if not prompt_file.exists():
        print(f"Error: Prompt file not found: {prompt_file}", file=sys.stderr)
        sys.exit(1)

    prompt = prompt_file.read_text()

    # Call OpenRouter API
    print(f"Calling OpenRouter API with model: {args.model}", file=sys.stderr)
    start_time = time.time()

    try:
        response = call_openrouter_api(prompt, args.model, api_key)
    except Exception as e:
        print(f"API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    duration_ms = int((time.time() - start_time) * 1000)

    # Extract usage
    usage = response.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)

    # Write output in stream-json format
    output_file = Path(args.output_file)
    write_stream_json_output(output_file, response, prompt_tokens, completion_tokens, duration_ms)

    print(f"✅ Response written to {output_file}", file=sys.stderr)
    print(f"   Tokens: {prompt_tokens} input, {completion_tokens} output", file=sys.stderr)
    print(f"   Duration: {duration_ms}ms", file=sys.stderr)


if __name__ == '__main__':
    main()
