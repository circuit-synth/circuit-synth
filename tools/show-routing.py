#!/usr/bin/env python3
"""
Display routing rules and test routing decisions
"""

import sys
import tomllib
from pathlib import Path

# Add parent to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'adws'))

from adw_modules.routing import ModelRouter

CONFIG_FILE = REPO_ROOT / 'adws' / 'config.toml'


def test_routing_scenarios(router):
    """Test routing with different task scenarios"""
    scenarios = [
        {
            "name": "Critical security issue",
            "attrs": {"priority": "critical", "labels": ["security"], "retry_count": 0}
        },
        {
            "name": "Normal bug fix",
            "attrs": {"priority": "normal", "labels": ["bug"], "retry_count": 0}
        },
        {
            "name": "Retry after failure",
            "attrs": {"priority": "normal", "labels": ["bug"], "retry_count": 1}
        },
        {
            "name": "Off-hours task (3am)",
            "attrs": {"priority": "normal", "labels": ["feature"], "retry_count": 0},
            "override_hour": 3
        },
        {
            "name": "Documentation update",
            "attrs": {"priority": "low", "labels": ["documentation"], "retry_count": 0}
        },
        {
            "name": "High priority feature",
            "attrs": {"priority": "high", "labels": ["feature"], "retry_count": 0}
        }
    ]

    print("\n" + "=" * 70)
    print("ROUTING DECISION TESTS")
    print("=" * 70)
    print()

    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print(f"  Attrs: {scenario['attrs']}")

        # TODO: Support hour override for testing
        provider, model = router.route(scenario['attrs'])

        print(f"  → Routed to: {provider} / {model}")
        print()


def main():
    # Load config
    with open(CONFIG_FILE, 'rb') as f:
        config = tomllib.load(f)

    # Initialize router
    router = ModelRouter(config)

    print("=" * 70)
    print("🧭 Model Routing Configuration")
    print("=" * 70)
    print()

    router.print_rules()

    # Test routing scenarios
    test_routing_scenarios(router)


if __name__ == '__main__':
    main()
