"""
Model routing engine for intelligent provider/model selection

Supports routing based on:
- Task priority (critical, high, normal, low)
- Issue labels
- Retry count (use cheaper models for retries)
- Time of day (use cheaper models during off-hours)
- Cost optimization
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RoutingRule:
    """A single routing rule with conditions and target"""

    def __init__(self, rule_config: Dict):
        """Initialize routing rule

        Args:
            rule_config: Rule configuration dict with conditions and target
        """
        self.name = rule_config.get('name', 'unnamed-rule')
        self.conditions = rule_config.get('conditions', {})
        self.provider = rule_config.get('provider')
        self.model = rule_config.get('model')
        self.priority = rule_config.get('priority', 50)  # Higher = checked first

    def matches(self, task_attrs: Dict) -> bool:
        """Check if task attributes match this rule's conditions

        Args:
            task_attrs: Task attributes to check (priority, labels, retry_count, etc.)

        Returns:
            True if all conditions match
        """
        for condition_key, condition_value in self.conditions.items():
            task_value = task_attrs.get(condition_key)

            # Handle different condition types
            if condition_key == 'priority':
                # Exact match or list of priorities
                if isinstance(condition_value, list):
                    if task_value not in condition_value:
                        return False
                elif task_value != condition_value:
                    return False

            elif condition_key == 'labels':
                # Task must have at least one of the specified labels
                if isinstance(condition_value, list):
                    task_labels = task_value or []
                    if not any(label in task_labels for label in condition_value):
                        return False

            elif condition_key == 'retry_count':
                # Numeric comparison
                if isinstance(condition_value, dict):
                    # Support operators: gte, lte, eq
                    retry_count = task_value or 0
                    if 'gte' in condition_value and retry_count < condition_value['gte']:
                        return False
                    if 'lte' in condition_value and retry_count > condition_value['lte']:
                        return False
                    if 'eq' in condition_value and retry_count != condition_value['eq']:
                        return False
                elif task_value != condition_value:
                    return False

            elif condition_key == 'hour_range':
                # Time-based routing (e.g., [0, 8] for midnight-8am)
                current_hour = datetime.now().hour
                start, end = condition_value
                if start <= end:
                    if not (start <= current_hour < end):
                        return False
                else:  # Wraps midnight (e.g., [22, 6])
                    if not (current_hour >= start or current_hour < end):
                        return False

            else:
                # Default: exact match
                if task_value != condition_value:
                    return False

        return True

    def __repr__(self):
        return f"RoutingRule({self.name}, priority={self.priority})"


class ModelRouter:
    """Routes tasks to appropriate provider/model based on rules"""

    def __init__(self, config: Dict):
        """Initialize router with config

        Args:
            config: Full config dict with 'routing' section
        """
        self.config = config
        self.rules = []

        # Load routing rules from config
        routing_config = config.get('routing', {})
        self.enabled = routing_config.get('enabled', False)
        self.default_provider = routing_config.get('default_provider', 'claude-cli')
        self.default_model = routing_config.get('default_model', 'claude-sonnet-4-5')

        # Load rules
        rules_config = routing_config.get('rules', [])
        for rule_config in rules_config:
            self.rules.append(RoutingRule(rule_config))

        # Sort rules by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

        logger.info(f"Initialized ModelRouter with {len(self.rules)} rules (enabled={self.enabled})")

    def route(self, task_attrs: Dict) -> tuple[str, str]:
        """Select provider and model for task

        Args:
            task_attrs: Task attributes (priority, labels, retry_count, etc.)

        Returns:
            (provider_name, model_name) tuple
        """
        # If routing disabled, use defaults
        if not self.enabled:
            logger.debug(f"Routing disabled, using defaults: {self.default_provider}/{self.default_model}")
            return (self.default_provider, self.default_model)

        # Check rules in priority order
        for rule in self.rules:
            if rule.matches(task_attrs):
                provider = rule.provider or self.default_provider
                model = rule.model or self.default_model
                logger.info(f"✓ Rule matched: {rule.name} → {provider}/{model}")
                logger.debug(f"  Task attrs: {task_attrs}")
                return (provider, model)

        # No rules matched, use defaults
        logger.info(f"No rules matched, using defaults: {self.default_provider}/{self.default_model}")
        logger.debug(f"  Task attrs: {task_attrs}")
        return (self.default_provider, self.default_model)

    def print_rules(self):
        """Print all routing rules"""
        if not self.enabled:
            print("⚠️  Routing is DISABLED")
            print(f"   Using: {self.default_provider}/{self.default_model}")
            return

        print(f"Router enabled: {self.enabled}")
        print(f"Default: {self.default_provider}/{self.default_model}")
        print()
        print("Routing Rules (priority order):")
        for rule in self.rules:
            print(f"  [{rule.priority}] {rule.name}")
            print(f"      Conditions: {rule.conditions}")
            print(f"      Target: {rule.provider or '(default)'}/{rule.model or '(default)'}")
