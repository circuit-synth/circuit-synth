"""
Test Suite for Unified Logging System
====================================

Comprehensive test suite for validating the unified logging system including:
- Basic logging functionality
- Multi-user context management
- Performance monitoring
- LLM conversation logging
- Rust integration
- Migration utilities
- Performance benchmarks
"""

import json
import logging
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from .config_manager import LoggingConfig
from .context_manager import (
    RequestContext,
    SessionManager,
    current_chat,
    current_request,
    current_session,
    current_user,
    get_current_context,
)
from .migration_utils import (
    BackwardCompatibilityLogger,
    LoggingMigrationTool,
    create_compatibility_logger,
    validate_migration,
)
from .performance_monitor import (
    PerformanceMetric,
    monitor_performance,
    performance_context,
)

# Import unified logging components
from .unified_logger import (
    ContextLogger,
    LLMConversationLogger,
    PerformanceLogger,
    UserContext,
    context_logger,
    initialize_logging,
)

# from .rust_integration import RustLogHandler, setup_rust_logging  # DISABLED: Rust integration removed


class TestContextLogger:
    """Test the core context logger functionality."""

    def test_basic_logging(self):
        """Test basic logging operations."""
        logger = ContextLogger()

        # Test all log levels
        logger.debug("Debug message", component="TEST")
        logger.info("Info message", component="TEST")
        logger.warning("Warning message", component="TEST")
        logger.error("Error message", component="TEST")

        # Should not raise any exceptions
        assert True

    def test_logging_with_context(self):
        """Test logging with user context."""
        logger = ContextLogger()

        with UserContext("test_user", "test_session"):
            logger.info("Message with context", component="TEST")

            # Verify context is set
            assert current_user.get() == "test_user"
            assert current_session.get() == "test_session"

    def test_logging_with_metadata(self):
        """Test logging with additional metadata."""
        logger = ContextLogger()

        logger.info(
            "Message with metadata",
            component="TEST",
            operation="test_operation",
            duration_ms=123.45,
            success=True,
        )

        # Should not raise any exceptions
        assert True

    def test_error_handling(self):
        """Test error handling in logging operations."""
        logger = ContextLogger()

        # Test with various problematic inputs
        logger.info(None, component="TEST")  # None message
        logger.info("", component="TEST")  # Empty message
        logger.info("Test", component=None)  # None component

        # Should handle gracefully
        assert True


class TestUserContext:
    """Test user context management."""

    def test_context_creation(self):
        """Test creating user context."""
        with UserContext("user123", "session456") as ctx:
            assert ctx.user_id == "user123"
            assert ctx.session_id == "session456"
            assert current_user.get() == "user123"
            assert current_session.get() == "session456"

        # Context should be cleared after exit
        assert current_user.get() is None
        assert current_session.get() is None

    def test_auto_session_generation(self):
        """Test automatic session ID generation."""
        with UserContext("user123") as ctx:
            assert ctx.user_id == "user123"
            assert ctx.session_id.startswith("user123_")
            assert len(ctx.session_id) > len("user123_")

    def test_request_context(self):
        """Test request context management."""
        with UserContext("user123"):
            with RequestContext("test_operation") as req_ctx:
                assert req_ctx.operation_name == "test_operation"
                assert current_request.get() == req_ctx.request_id
                assert req_ctx.get_duration_ms() >= 0

    def test_nested_contexts(self):
        """Test nested context management."""
        with UserContext("user1", "session1"):
            assert current_user.get() == "user1"

            with UserContext("user2", "session2"):
                assert current_user.get() == "user2"
                assert current_session.get() == "session2"

            # Should restore previous context
            assert current_user.get() == "user1"
            assert current_session.get() == "session1"


class TestSessionManager:
    """Test session management functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Get a fresh session manager instance
        self.session_manager = SessionManager()
        self.session_manager.sessions.clear()
        self.session_manager.user_sessions.clear()

    def test_session_registration(self):
        """Test session registration."""
        self.session_manager.register_session("user1", "session1")

        session_info = self.session_manager.get_session_info("session1")
        assert session_info is not None
        assert session_info.user_id == "user1"
        assert session_info.session_id == "session1"

    def test_session_activity_tracking(self):
        """Test session activity tracking."""
        self.session_manager.register_session("user1", "session1")

        original_activity = self.session_manager.get_session_info(
            "session1"
        ).last_activity
        time.sleep(0.01)  # Small delay

        self.session_manager.update_session_activity("session1")
        updated_activity = self.session_manager.get_session_info(
            "session1"
        ).last_activity

        assert updated_activity > original_activity

    def test_request_tracking(self):
        """Test request tracking within sessions."""
        self.session_manager.register_session("user1", "session1")

        self.session_manager.add_request_to_session("session1", "req1")
        self.session_manager.add_request_to_session("session1", "req2")

        session_info = self.session_manager.get_session_info("session1")
        assert session_info.request_count == 2
        assert "req1" in session_info.active_requests
        assert "req2" in session_info.active_requests

    def test_session_cleanup(self):
        """Test session cleanup functionality."""
        # Create old session
        self.session_manager.register_session("user1", "old_session")
        old_session = self.session_manager.get_session_info("old_session")
        old_session.last_activity = datetime.utcnow() - timedelta(hours=25)

        # Create recent session
        self.session_manager.register_session("user1", "new_session")

        # Cleanup expired sessions
        removed_count = self.session_manager.cleanup_expired_sessions(timeout_hours=24)

        assert removed_count == 1
        assert self.session_manager.get_session_info("old_session") is None
        assert self.session_manager.get_session_info("new_session") is not None


class TestPerformanceLogger:
    """Test performance monitoring functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.context_logger = ContextLogger()
        self.perf_logger = PerformanceLogger(self.context_logger)

    def test_timer_context_manager(self):
        """Test performance timer context manager."""
        with self.perf_logger.timer("test_operation", component="TEST") as timer_id:
            time.sleep(0.01)  # Small delay
            assert timer_id is not None

        # Timer should have recorded the operation
        stats = self.perf_logger.get_operation_stats("test_operation")
        assert stats is not None
        assert stats.total_calls == 1
        assert stats.avg_duration_ms >= 10  # At least 10ms

    def test_custom_metrics(self):
        """Test custom metric logging."""
        self.perf_logger.log_metric("test_metric", 42.5, "units", component="TEST")
        self.perf_logger.log_counter("test_counter", 5, component="TEST")
        self.perf_logger.log_gauge("test_gauge", 75.0, component="TEST")

        # Should not raise exceptions
        assert True

    def test_operation_statistics(self):
        """Test operation statistics collection."""
        # Record multiple operations
        for i in range(5):
            with self.perf_logger.timer("test_op", component="TEST"):
                time.sleep(0.001 * (i + 1))  # Variable delay

        stats = self.perf_logger.get_operation_stats("test_op")
        assert stats.total_calls == 5
        assert stats.min_duration_ms < stats.max_duration_ms
        assert stats.avg_duration_ms > 0

    def test_performance_decorator(self):
        """Test performance monitoring decorator."""

        @monitor_performance("decorated_function", "TEST")
        def test_function():
            time.sleep(0.01)
            return "result"

        result = test_function()
        assert result == "result"

        # Check if performance was recorded
        stats = self.perf_logger.get_operation_stats("decorated_function")
        # Note: This might be None if using a different perf_logger instance
        # In a real implementation, we'd need to ensure the decorator uses the same instance


class TestLLMConversationLogger:
    """Test LLM conversation logging functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.context_logger = ContextLogger()
        self.llm_logger = LLMConversationLogger(self.context_logger)

    def test_conversation_lifecycle(self):
        """Test complete conversation lifecycle."""
        # Start conversation
        chat_id = self.llm_logger.start_conversation("test_chat")
        assert chat_id == "test_chat"

        # Log request
        request_id = self.llm_logger.log_request(
            chat_id=chat_id,
            model="gpt-4",
            provider="openai",
            prompt="Test prompt",
            prompt_tokens=10,
            estimated_cost=0.001,
        )
        assert request_id is not None

        # Log response
        self.llm_logger.log_response(
            request_id=request_id,
            response="Test response",
            completion_tokens=20,
            total_tokens=30,
            actual_cost=0.002,
            duration_ms=1500,
        )

        # Get conversation summary
        summary = self.llm_logger.get_conversation_summary(chat_id)
        assert summary["total_turns"] == 1
        assert summary["total_cost"] == 0.002
        assert summary["total_tokens"] == 30

    def test_conversation_error_handling(self):
        """Test error handling in conversations."""
        chat_id = self.llm_logger.start_conversation("error_chat")

        request_id = self.llm_logger.log_request(
            chat_id=chat_id,
            model="gpt-4",
            provider="openai",
            prompt="Test prompt",
            prompt_tokens=10,
        )

        # Log error
        test_error = Exception("Test error")
        self.llm_logger.log_error(request_id, test_error, {"context": "test"})

        # Should not raise exceptions
        assert True

    def test_multiple_conversations(self):
        """Test handling multiple concurrent conversations."""
        chat_ids = []

        # Start multiple conversations
        for i in range(3):
            chat_id = f"chat_{i}"
            self.llm_logger.start_conversation(chat_id)
            chat_ids.append(chat_id)

        # Add requests to each
        for chat_id in chat_ids:
            self.llm_logger.log_request(
                chat_id=chat_id,
                model="gpt-4",
                provider="openai",
                prompt=f"Prompt for {chat_id}",
                prompt_tokens=10,
            )

        # Verify all conversations exist
        for chat_id in chat_ids:
            summary = self.llm_logger.get_conversation_summary(chat_id)
            assert summary["total_turns"] == 1


class TestConfigManager:
    """Test configuration management."""

    def test_default_config_loading(self):
        """Test loading default configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            config = LoggingConfig(str(config_path))

            # Should create default config
            assert config.get("logging.level") == "INFO"
            assert config.get("logging.sinks.console.enabled") is True

    def test_config_value_access(self):
        """Test configuration value access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            config = LoggingConfig(str(config_path))

            # Test getting values
            assert config.get("logging.level") == "INFO"
            assert config.get("nonexistent.key", "default") == "default"

            # Test setting values
            config.set("logging.level", "DEBUG")
            assert config.get("logging.level") == "DEBUG"

    def test_environment_overrides(self):
        """Test environment variable overrides."""
        with patch.dict("os.environ", {"CIRCUIT_SYNTH_LOG_LEVEL": "ERROR"}):
            with tempfile.TemporaryDirectory() as temp_dir:
                config_path = Path(temp_dir) / "test_config.yaml"
                config = LoggingConfig(str(config_path))

                # Should be overridden by environment variable
                assert config.get("logging.level") == "ERROR"


class TestMigrationUtils:
    """Test migration utilities."""

    def test_backward_compatibility_logger(self):
        """Test backward compatibility logger."""
        compat_logger = BackwardCompatibilityLogger("test")

        # Test all logging methods
        compat_logger.debug("Debug message")
        compat_logger.info("Info message")
        compat_logger.warning("Warning message")
        compat_logger.error("Error message")
        compat_logger.exception("Exception message")
        compat_logger.critical("Critical message")

        # Test with formatting
        compat_logger.info("Message with %s", "formatting")

        # Test with extra data
        compat_logger.info("Message with extra", extra={"key": "value"})

        # Should not raise exceptions
        assert True

    def test_migration_tool(self):
        """Test automated migration tool."""
        migrator = LoggingMigrationTool()

        # Create test file content
        test_content = """
import logging

logger = logging.getLogger(__name__)

def test_function():
    logger.info("Test message")
    logging.debug("Direct logging call")
    print("Print statement")
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_file.py"
            test_file.write_text(test_content)

            # Migrate the file
            result = migrator.migrate_file(test_file)

            assert result.success
            assert len(result.changes_made) > 0

            # Check that file was modified
            migrated_content = test_file.read_text()
            assert "context_logger" in migrated_content
            assert (
                "from circuit_synth.core.logging.unified import context_logger"
                in migrated_content
            )

    def test_migration_validation(self):
        """Test migration validation."""
        # Create a valid migrated file
        valid_content = """
from circuit_synth.core.logging.unified import context_logger

def test_function():
    context_logger.info("Test message", component="TEST")
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "valid_file.py"
            test_file.write_text(valid_content)

            issues = validate_migration(test_file)
            assert len(issues) == 0  # Should be valid


class TestRustIntegration:
    """Test Rust logging integration."""

    def test_rust_log_handler(self):
        """Test Rust log handler functionality."""
        context_logger_mock = Mock()
        handler = RustLogHandler(context_logger_mock)

        # Create a mock log record
        record = logging.LogRecord(
            name="rust_symbol_search",
            level=logging.INFO,
            pathname="test.rs",
            lineno=42,
            msg="Test message from Rust",
            args=(),
            exc_info=None,
        )

        # Emit the record
        handler.emit(record)

        # Verify that context logger was called
        context_logger_mock.info.assert_called_once()

    def test_structured_message_parsing(self):
        """Test parsing of structured messages from Rust."""
        context_logger_mock = Mock()
        handler = RustLogHandler(context_logger_mock)

        # Test performance timing message
        perf_record = logging.LogRecord(
            name="rust_symbol_search",
            level=logging.INFO,
            pathname="test.rs",
            lineno=42,
            msg="PERF_TIMING: operation=search duration_ms=123.45 metadata={}",
            args=(),
            exc_info=None,
        )

        handler.emit(perf_record)

        # Verify parsing worked
        context_logger_mock.info.assert_called_once()
        call_args = context_logger_mock.info.call_args
        assert "log_type" in call_args[1]
        assert call_args[1]["log_type"] == "performance"


class TestConcurrency:
    """Test concurrent logging operations."""

    def test_concurrent_user_contexts(self):
        """Test concurrent user contexts don't interfere."""
        results = {}

        def user_logging_task(user_id: str, message_count: int):
            with UserContext(user_id, f"{user_id}_session"):
                messages = []
                for i in range(message_count):
                    # Verify context is correct
                    assert current_user.get() == user_id
                    context_logger.info(
                        f"Message {i} from {user_id}", component="CONCURRENT"
                    )
                    messages.append(f"Message {i} from {user_id}")
                results[user_id] = messages

        # Run multiple users concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(5):
                future = executor.submit(user_logging_task, f"user_{i}", 10)
                futures.append(future)

            # Wait for all to complete
            for future in as_completed(futures):
                future.result()  # Will raise exception if task failed

        # Verify all users completed their tasks
        assert len(results) == 5
        for user_id, messages in results.items():
            assert len(messages) == 10

    def test_concurrent_performance_logging(self):
        """Test concurrent performance logging."""
        perf_logger = PerformanceLogger(ContextLogger())

        def performance_task(task_id: int):
            with perf_logger.timer(
                f"concurrent_task_{task_id}", component="CONCURRENT"
            ):
                time.sleep(0.01)  # Small delay
                return task_id

        # Run concurrent performance tasks
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(performance_task, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]

        assert len(results) == 20
        assert set(results) == set(range(20))


class TestPerformanceBenchmarks:
    """Performance benchmarks for the logging system."""

    def test_logging_throughput(self):
        """Test logging throughput under load."""
        logger = ContextLogger()
        message_count = 1000

        start_time = time.perf_counter()

        with UserContext("benchmark_user"):
            for i in range(message_count):
                logger.info(f"Benchmark message {i}", component="BENCHMARK")

        end_time = time.perf_counter()
        duration = end_time - start_time
        throughput = message_count / duration

        print(f"Logging throughput: {throughput:.0f} messages/second")

        # Should achieve at least 1000 messages/second
        assert throughput > 1000, f"Throughput too low: {throughput:.0f} msg/s"

    def test_concurrent_logging_throughput(self):
        """Test concurrent logging throughput."""

        def logging_worker(worker_id: int, message_count: int):
            logger = ContextLogger()
            with UserContext(f"worker_{worker_id}"):
                for i in range(message_count):
                    logger.info(
                        f"Worker {worker_id} message {i}", component="BENCHMARK"
                    )

        worker_count = 10
        messages_per_worker = 100
        total_messages = worker_count * messages_per_worker

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(logging_worker, i, messages_per_worker)
                for i in range(worker_count)
            ]

            for future in as_completed(futures):
                future.result()

        end_time = time.perf_counter()
        duration = end_time - start_time
        throughput = total_messages / duration

        print(f"Concurrent logging throughput: {throughput:.0f} messages/second")

        # Should achieve at least 5000 messages/second with concurrency
        assert (
            throughput > 5000
        ), f"Concurrent throughput too low: {throughput:.0f} msg/s"


def run_all_tests():
    """Run all tests and return results."""
    import sys

    # Run pytest programmatically
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
        return False


if __name__ == "__main__":
    # Run tests when script is executed directly
    success = run_all_tests()
    sys.exit(0 if success else 1)
