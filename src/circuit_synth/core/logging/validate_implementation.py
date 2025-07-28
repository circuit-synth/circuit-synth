#!/usr/bin/env python3
"""
Validation Script for Unified Logging System
===========================================

This script validates the implementation of the unified logging system by:
1. Testing basic functionality
2. Validating performance requirements
3. Checking all components work together
4. Generating a validation report
"""

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Add the project root to the path so we can import the logging modules
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_basic_functionality():
    """Test basic logging functionality."""
    print("🔍 Testing basic functionality...")

    try:
        # Import the unified logging system
        from circuit_synth.core.logging import (
            UserContext,
            context_logger,
            llm_conversation_logger,
            performance_logger,
            setup_unified_logging,
        )

        # Test basic logging
        context_logger.info("Basic logging test", component="VALIDATION")
        context_logger.debug("Debug message test", component="VALIDATION")
        context_logger.warning("Warning message test", component="VALIDATION")
        context_logger.error("Error message test", component="VALIDATION")

        # Test user context
        with UserContext("test_user", "validation_session"):
            context_logger.info("User context test", component="VALIDATION")

        # Test performance logging
        with performance_logger.timer("validation_test", component="VALIDATION"):
            time.sleep(0.01)  # Small delay

        # Test LLM conversation logging
        chat_id = llm_conversation_logger.start_conversation("validation_chat")
        request_id = llm_conversation_logger.log_request(
            chat_id=chat_id,
            model="test-model",
            provider="test",
            prompt="Test prompt",
            prompt_tokens=10,
            estimated_cost=0.001,
        )
        llm_conversation_logger.log_response(
            request_id=request_id,
            response="Test response",
            completion_tokens=20,
            total_tokens=30,
            actual_cost=0.002,
            duration_ms=100,
        )

        print("✅ Basic functionality test passed")
        return True

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_performance_requirements():
    """Test performance requirements (>10,000 messages/second)."""
    print("🚀 Testing performance requirements...")

    try:
        from circuit_synth.core.logging import UserContext, context_logger

        # Test single-threaded performance
        message_count = 5000
        start_time = time.perf_counter()

        with UserContext("perf_user"):
            for i in range(message_count):
                context_logger.info(
                    f"Performance test message {i}", component="PERF_TEST"
                )

        end_time = time.perf_counter()
        duration = end_time - start_time
        throughput = message_count / duration

        print(f"📊 Single-threaded throughput: {throughput:.0f} messages/second")

        # Test multi-threaded performance
        def worker_task(worker_id: int, messages_per_worker: int):
            with UserContext(f"worker_{worker_id}"):
                for i in range(messages_per_worker):
                    context_logger.info(
                        f"Worker {worker_id} message {i}", component="PERF_TEST"
                    )

        worker_count = 10
        messages_per_worker = 500
        total_messages = worker_count * messages_per_worker

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(worker_task, i, messages_per_worker)
                for i in range(worker_count)
            ]

            for future in as_completed(futures):
                future.result()

        end_time = time.perf_counter()
        duration = end_time - start_time
        concurrent_throughput = total_messages / duration

        print(
            f"📊 Multi-threaded throughput: {concurrent_throughput:.0f} messages/second"
        )

        # Check if we meet the requirement
        requirement_met = concurrent_throughput > 10000

        if requirement_met:
            print("✅ Performance requirements met (>10,000 messages/second)")
        else:
            print(
                f"⚠️  Performance requirement not met: {concurrent_throughput:.0f} < 10,000 messages/second"
            )

        return requirement_met, concurrent_throughput

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback

        traceback.print_exc()
        return False, 0


def test_configuration_loading():
    """Test configuration loading and management."""
    print("⚙️  Testing configuration loading...")

    try:
        from circuit_synth.core.logging.config_manager import LoggingConfig

        # Test loading default configuration
        config = LoggingConfig()

        # Test getting values
        level = config.get("logging.level")
        console_enabled = config.get("logging.sinks.console.enabled")

        print(f"📋 Configuration loaded - Level: {level}, Console: {console_enabled}")

        # Test setting values
        config.set("logging.level", "DEBUG")
        new_level = config.get("logging.level")

        if new_level == "DEBUG":
            print("✅ Configuration management test passed")
            return True
        else:
            print("❌ Configuration management test failed")
            return False

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_migration_utilities():
    """Test migration utilities."""
    print("🔄 Testing migration utilities...")

    try:
        from circuit_synth.core.logging.migration_utils import (
            BackwardCompatibilityLogger,
            LoggingMigrationTool,
        )

        # Test backward compatibility logger
        compat_logger = BackwardCompatibilityLogger("test")
        compat_logger.info("Compatibility test message")
        compat_logger.debug("Debug compatibility message")
        compat_logger.warning("Warning compatibility message")
        compat_logger.error("Error compatibility message")

        # Test migration tool
        migrator = LoggingMigrationTool()

        print("✅ Migration utilities test passed")
        return True

    except Exception as e:
        print(f"❌ Migration utilities test failed: {e}")
        return False


def test_context_management():
    """Test context management and thread safety."""
    print("🧵 Testing context management and thread safety...")

    try:
        from circuit_synth.core.logging import (
            UserContext,
            context_logger,
            current_session,
            current_user,
        )

        # Test context isolation
        results = {}

        def context_test_worker(user_id: str):
            with UserContext(user_id, f"{user_id}_session"):
                # Verify context is correct
                actual_user = current_user.get()
                actual_session = current_session.get()

                results[user_id] = {
                    "user": actual_user,
                    "session": actual_session,
                    "expected_user": user_id,
                    "expected_session": f"{user_id}_session",
                }

                context_logger.info(
                    f"Context test from {user_id}", component="CONTEXT_TEST"
                )

        # Run multiple workers concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(context_test_worker, f"user_{i}") for i in range(5)
            ]

            for future in as_completed(futures):
                future.result()

        # Verify all contexts were isolated correctly
        all_correct = True
        for user_id, result in results.items():
            if result["user"] != result["expected_user"]:
                print(f"❌ Context isolation failed for {user_id}")
                all_correct = False

        if all_correct:
            print("✅ Context management and thread safety test passed")
            return True
        else:
            print("❌ Context management test failed")
            return False

    except Exception as e:
        print(f"❌ Context management test failed: {e}")
        return False


def generate_validation_report(results: dict):
    """Generate a comprehensive validation report."""
    print("\n" + "=" * 60)
    print("📋 UNIFIED LOGGING SYSTEM VALIDATION REPORT")
    print("=" * 60)
    print(f"Validation Date: {datetime.now().isoformat()}")
    print(f"System: Circuit Synth Unified Logging v2.0")
    print()

    # Summary
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result.get("passed", False))

    print(f"📊 SUMMARY:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print()

    # Detailed results
    print("📋 DETAILED RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
        print(f"   {test_name}: {status}")

        if "throughput" in result:
            print(f"      Throughput: {result['throughput']:.0f} messages/second")

        if "error" in result:
            print(f"      Error: {result['error']}")

    print()

    # Performance analysis
    if "performance" in results and results["performance"].get("passed"):
        throughput = results["performance"].get("throughput", 0)
        print("🚀 PERFORMANCE ANALYSIS:")
        print(f"   Measured Throughput: {throughput:.0f} messages/second")
        print(f"   Requirement: >10,000 messages/second")
        print(f"   Performance Margin: {((throughput - 10000) / 10000) * 100:.1f}%")
        print()

    # Recommendations
    print("💡 RECOMMENDATIONS:")
    if passed_tests == total_tests:
        print(
            "   ✅ All tests passed! The unified logging system is ready for production."
        )
        print("   ✅ Performance requirements are met.")
        print("   ✅ All components are functioning correctly.")
    else:
        print("   ⚠️  Some tests failed. Review the detailed results above.")
        print("   ⚠️  Address any failing components before production deployment.")

        if "performance" in results and not results["performance"].get("passed"):
            print("   ⚠️  Performance requirements not met. Consider optimization.")

    print()
    print("=" * 60)


def main():
    """Main validation function."""
    print("🚀 Starting Circuit Synth Unified Logging System Validation")
    print("=" * 60)

    results = {}

    # Run all validation tests
    tests = [
        ("basic_functionality", test_basic_functionality),
        ("configuration", test_configuration_loading),
        ("migration_utilities", test_migration_utilities),
        ("context_management", test_context_management),
        ("performance", test_performance_requirements),
    ]

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")

        try:
            if test_name == "performance":
                passed, throughput = test_func()
                results[test_name] = {"passed": passed, "throughput": throughput}
            else:
                passed = test_func()
                results[test_name] = {"passed": passed}

        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = {"passed": False, "error": str(e)}

    # Generate final report
    generate_validation_report(results)

    # Return overall success
    all_passed = all(result.get("passed", False) for result in results.values())
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
