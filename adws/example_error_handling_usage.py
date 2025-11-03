#!/usr/bin/env python3
"""
Example: How to use the error handling system with coordinator

This example demonstrates:
1. Integrating TaskErrorTracking with Task
2. Handling failures with retry logic
3. Displaying health information
4. Manual recovery controls
"""

from dataclasses import dataclass, field
from adw_modules import (
    TaskErrorTracking,
    FailureType,
    TaskHealth,
    categorize_error,
    format_health_for_dashboard
)
from datetime import datetime
import time


@dataclass
class Task:
    """Example Task with error tracking"""
    id: str
    description: str
    status: str = "pending"
    worker_id: str = None
    error: str = None

    # Integrated error tracking
    error_tracking: TaskErrorTracking = field(default_factory=TaskErrorTracking)


def simulate_worker_failure(task: Task, error_msg: str):
    """Simulate a worker failure and handle it"""
    print(f"\n💥 Worker failed for {task.id}: {error_msg}")

    # Categorize the error
    failure_type = categorize_error(error_msg, context={})

    # Record the failure
    task.error_tracking.record_failure(failure_type)
    task.error = error_msg

    # Check if we can retry
    if task.error_tracking.can_retry():
        task.status = "pending"  # Will retry
        backoff = task.error_tracking.calculate_backoff()
        health = task.error_tracking.get_health_status()

        print(f"   ⚠️ Health: {health.value}")
        print(f"   🔄 Will retry (attempt {task.error_tracking.attempt_count + 1}/{task.error_tracking.max_attempts})")
        print(f"   ⏳ Backoff: {backoff}s")
    else:
        task.status = "failed"  # Max attempts reached
        print(f"   ❌ Task failed permanently")
        print(f"   ☠️ Health: DEAD")

        # Generate alerts
        alerts = task.error_tracking.get_alerts()
        for alert in alerts:
            print(f"   {alert}")


def display_task_dashboard(task: Task):
    """Display task in dashboard format"""
    print(f"\n📊 Dashboard View for {task.id}:")
    print(f"[] {task.id}: {task.description}")

    # Show health information
    health_lines = format_health_for_dashboard(task.error_tracking)
    for line in health_lines:
        print(line)


def manual_recovery_example(task: Task):
    """Demonstrate manual recovery controls"""
    print(f"\n🔧 Manual Recovery Options for {task.id}:")

    print("\n1. Manual Retry (reset attempt counter)")
    print("   task.error_tracking.manual_retry()")
    print("   task.status = 'pending'")

    print("\n2. Manual Cancel")
    print("   task.status = 'cancelled'")
    print("   task.error = 'User cancelled'")

    print("\n3. Manual Reset (clear all error history)")
    print("   task.error_tracking.manual_reset()")
    print("   task.status = 'pending'")


def main():
    """Run the example"""
    print("=" * 70)
    print("Error Handling System - Usage Example")
    print("=" * 70)

    # Create a task
    task = Task(id="gh-452", description="Implement error handling")

    # Scenario 1: First failure (worktree error)
    print("\n\n📝 Scenario 1: First Failure (WORKTREE_ERROR)")
    print("-" * 70)
    simulate_worker_failure(task, "worktree already exists at trees/gh-452")
    display_task_dashboard(task)

    # Scenario 2: Second failure (same error type)
    print("\n\n📝 Scenario 2: Second Failure (WORKTREE_ERROR again)")
    print("-" * 70)
    simulate_worker_failure(task, "failed to create worktree")
    display_task_dashboard(task)

    # Scenario 3: Third failure (max attempts)
    print("\n\n📝 Scenario 3: Third Failure (Max attempts reached)")
    print("-" * 70)
    simulate_worker_failure(task, "worktree error occurred")
    display_task_dashboard(task)

    # Show manual recovery options
    manual_recovery_example(task)

    # Demonstrate manual reset
    print("\n\n📝 Scenario 4: Manual Reset")
    print("-" * 70)
    print("Performing manual reset...")
    task.error_tracking.manual_reset()
    task.status = "pending"
    task.error = None
    print(f"✅ Task reset to clean state")
    print(f"   Health: {task.error_tracking.get_health_status().value}")
    print(f"   Attempts: {task.error_tracking.attempt_count}/{task.error_tracking.max_attempts}")
    display_task_dashboard(task)

    # Example of different failure types
    print("\n\n📝 Scenario 5: Different Failure Types")
    print("-" * 70)

    task2 = Task(id="gh-453", description="Test multiple failure types")

    failures = [
        "timeout occurred during execution",
        "failed to create PR",
        "validation error in output"
    ]

    for error_msg in failures:
        failure_type = categorize_error(error_msg)
        task2.error_tracking.record_failure(failure_type)
        print(f"Failure {task2.error_tracking.attempt_count}: {failure_type.value}")

    print(f"\n📊 Failure History:")
    for i, failure in enumerate(task2.error_tracking.failure_history, 1):
        print(f"  {i}. {failure.value}")

    print(f"\n⚠️ Repeated failures? {task2.error_tracking.has_repeated_failures()}")
    if not task2.error_tracking.has_repeated_failures():
        print("   (No - all different failure types)")

    # Example with repeated failures
    print("\n\n📝 Scenario 6: Repeated Failure Detection")
    print("-" * 70)

    task3 = Task(id="gh-454", description="Test repeated failure alerts")

    for i in range(3):
        task3.error_tracking.record_failure(FailureType.TIMEOUT)
        print(f"Timeout #{i+1}")

    print(f"\n⚠️ Repeated failures? {task3.error_tracking.has_repeated_failures()}")
    print(f"   Repeated type: {task3.error_tracking.get_repeated_failure_type().value}")

    print("\n🚨 Alerts:")
    for alert in task3.error_tracking.get_alerts():
        print(f"   {alert}")

    print("\n\n" + "=" * 70)
    print("✅ Example Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Integrate TaskErrorTracking into coordinator.py Task class")
    print("2. Update check_completions() to use failure handling")
    print("3. Update main loop to respect backoff periods")
    print("4. Update tasks.md formatting to show health info")
    print("\nSee ERROR_HANDLING_INTEGRATION.md for detailed integration guide.")
    print("=" * 70)


if __name__ == "__main__":
    main()
