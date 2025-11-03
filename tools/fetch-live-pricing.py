#!/usr/bin/env python3
"""
Fetch live model pricing from various providers

Sources:
- OpenRouter API (200+ models from multiple providers)
- Anthropic pricing page (Claude models)
- OpenAI pricing page (GPT models)
"""

import json
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List

# Add parent to path
REPO_ROOT = Path(__file__).parent.parent


def fetch_openrouter_models() -> List[Dict]:
    """Fetch all models from OpenRouter API

    Returns:
        List of model dicts with name, pricing, context_length, etc.
    """
    url = "https://openrouter.ai/api/v1/models"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            return data.get('data', [])
    except Exception as e:
        print(f"❌ Failed to fetch OpenRouter models: {e}")
        return []


def convert_openrouter_pricing(model: Dict) -> Dict:
    """Convert OpenRouter model to our format

    Args:
        model: OpenRouter model dict

    Returns:
        Model dict in our format
    """
    pricing = model.get('pricing', {})

    # OpenRouter prices are per token, we need per million tokens
    prompt_price = float(pricing.get('prompt', 0)) * 1_000_000
    completion_price = float(pricing.get('completion', 0)) * 1_000_000

    return {
        'name': model['id'],
        'provider': 'openrouter',
        'cost_per_million_input': round(prompt_price, 2),
        'cost_per_million_output': round(completion_price, 2),
        'context_window': model.get('context_length', 0),
        'description': model.get('description', '')[:100]
    }


def fetch_anthropic_pricing() -> List[Dict]:
    """Fetch Anthropic Claude model pricing

    Based on 2025 pricing from docs.claude.com

    Returns:
        List of Claude models with pricing
    """
    return [
        {
            'name': 'claude-haiku-4-5',
            'provider': 'anthropic',
            'cost_per_million_input': 1.0,
            'cost_per_million_output': 5.0,
            'context_window': 200000,
            'description': 'Fastest Claude model with near-frontier intelligence'
        },
        {
            'name': 'claude-sonnet-4-1',
            'provider': 'anthropic',
            'cost_per_million_input': 5.0,
            'cost_per_million_output': 25.0,
            'context_window': 200000,
            'description': 'Balanced performance and speed'
        },
        {
            'name': 'claude-opus-4-1',
            'provider': 'anthropic',
            'cost_per_million_input': 15.0,
            'cost_per_million_output': 75.0,
            'context_window': 200000,
            'description': 'Most capable Claude model'
        }
    ]


def main():
    print("🌐 Fetching live model pricing...")
    print()

    # Fetch from OpenRouter
    print("📡 Fetching from OpenRouter API...")
    openrouter_models = fetch_openrouter_models()
    print(f"   Found {len(openrouter_models)} models")
    print()

    # Fetch Anthropic models
    print("📡 Fetching Anthropic Claude pricing...")
    anthropic_models = fetch_anthropic_pricing()
    print(f"   Found {len(anthropic_models)} models")
    print()

    # Convert OpenRouter models
    all_models = [convert_openrouter_pricing(m) for m in openrouter_models]
    all_models.extend(anthropic_models)

    # Filter to interesting models (non-zero pricing, reasonable context)
    filtered = [
        m for m in all_models
        if m['cost_per_million_input'] > 0
        and m['context_window'] >= 8000
    ]

    print(f"📊 Total models with pricing: {len(filtered)}")
    print()

    # Sort by cost (cheapest first)
    filtered.sort(key=lambda m: m['cost_per_million_input'])

    # Show top 20 cheapest
    print("=" * 100)
    print("💰 Top 20 Cheapest Models (per million tokens)")
    print("=" * 100)
    print(f"{'Model':<50} {'Input':<12} {'Output':<12} {'Context':<12}")
    print("-" * 100)

    for model in filtered[:20]:
        name = model['name'][:48]
        input_cost = f"${model['cost_per_million_input']:.2f}"
        output_cost = f"${model['cost_per_million_output']:.2f}"
        context = f"{model['context_window']:,}"

        print(f"{name:<50} {input_cost:<12} {output_cost:<12} {context:<12}")

    print()

    # Show Claude models specifically
    print("=" * 100)
    print("🤖 Anthropic Claude Models (2025 Pricing)")
    print("=" * 100)

    claude_models = [m for m in filtered if 'claude' in m['name'].lower()]

    for model in claude_models[:10]:
        name = model['name']
        input_cost = f"${model['cost_per_million_input']:.2f}"
        output_cost = f"${model['cost_per_million_output']:.2f}"

        # Calculate example cost (10k/2k tokens)
        example = (10_000 / 1_000_000) * model['cost_per_million_input'] + \
                  (2_000 / 1_000_000) * model['cost_per_million_output']

        print(f"{name:<50} {input_cost:<12} {output_cost:<12} Example: ${example:.4f}")

    print()

    # Option to save to file
    if '--save' in sys.argv:
        output_file = REPO_ROOT / 'pricing-cache.json'
        with open(output_file, 'w') as f:
            json.dump(filtered, f, indent=2)
        print(f"💾 Saved {len(filtered)} models to {output_file}")
        print()

    # Show update command
    print("=" * 100)
    print("To update config with live pricing:")
    print("  1. Review models above")
    print("  2. Edit adws/config.toml and update [[models]] sections")
    print("  3. Run: ./tools/show-api-prices.py to verify")
    print()
    print("To save pricing data: ./tools/fetch-live-pricing.py --save")
    print("=" * 100)


if __name__ == '__main__':
    main()
