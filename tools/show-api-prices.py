#!/usr/bin/env python3
"""
Display current API pricing from config
"""

import sys
import tomllib
from pathlib import Path

# Add parent to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'adws'))

CONFIG_FILE = REPO_ROOT / 'adws' / 'config.toml'


def format_price(price: float) -> str:
    """Format price nicely"""
    if price < 1:
        return f"${price:.2f}"
    else:
        return f"${price:.1f}"


def calculate_example_costs(input_cost: float, output_cost: float):
    """Calculate example costs for common scenarios"""
    # Example: 10k input, 2k output tokens (typical task)
    example_input = 10_000
    example_output = 2_000

    cost = (example_input / 1_000_000) * input_cost + (example_output / 1_000_000) * output_cost
    return cost


def main():
    # Load config
    with open(CONFIG_FILE, 'rb') as f:
        config = tomllib.load(f)

    models = config.get('models', [])

    if not models:
        print("❌ No models found in config")
        return

    print("=" * 70)
    print("💰 Current API Pricing Configuration")
    print("=" * 70)
    print()

    # Table header
    print(f"{'Model':<30} {'Input':<12} {'Output':<12} {'Example*':<12}")
    print(f"{'':30} {'(per 1M)':<12} {'(per 1M)':<12} {'(10k/2k)':<12}")
    print("-" * 70)

    # Print each model
    for model in models:
        name = model['name']
        input_cost = model.get('cost_per_million_input', 0.0)
        output_cost = model.get('cost_per_million_output', 0.0)

        example_cost = calculate_example_costs(input_cost, output_cost)

        print(f"{name:<30} {format_price(input_cost):<12} {format_price(output_cost):<12} {format_price(example_cost):<12}")

    print()
    print("*Example: 10k input tokens + 2k output tokens (typical task)")
    print()

    # Show cost comparisons
    print("=" * 70)
    print("📊 Cost Comparison (10k input / 2k output)")
    print("=" * 70)
    print()

    costs = []
    for model in models:
        name = model['name']
        input_cost = model.get('cost_per_million_input', 0.0)
        output_cost = model.get('cost_per_million_output', 0.0)
        example_cost = calculate_example_costs(input_cost, output_cost)
        costs.append((name, example_cost))

    # Sort by cost
    costs.sort(key=lambda x: x[1])

    cheapest_cost = costs[0][1]

    for name, cost in costs:
        savings = ((cost - cheapest_cost) / cost * 100) if cost > 0 else 0
        bar_length = int(cost / costs[-1][1] * 40)
        bar = "█" * bar_length

        if cost == cheapest_cost:
            print(f"💚 {name:<30} {format_price(cost):<10} {bar}")
        elif savings < 50:
            print(f"💛 {name:<30} {format_price(cost):<10} {bar}")
        else:
            print(f"💰 {name:<30} {format_price(cost):<10} {bar}")

    print()
    print(f"Savings: Use {costs[0][0]} instead of {costs[-1][0]} = {((costs[-1][1] - costs[0][1]) / costs[-1][1] * 100):.0f}% cheaper")
    print()


if __name__ == '__main__':
    main()
