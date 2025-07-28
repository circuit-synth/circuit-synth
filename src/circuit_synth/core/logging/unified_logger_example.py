"""
Example: How to use the unified logger in practice.
This shows a complete flow from login to circuit generation.
"""

import uuid
from datetime import datetime

from circuit_synth.core.logging.unified_logger import (
    context_logger,
    llm_conversation_logger,
    logger,
    performance_logger,
)


def example_user_flow():
    """Demonstrate a complete user flow with unified logging."""

    # User login
    username = "admin"
    session_id = (
        f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )

    context_logger.info(
        "User login successful",
        component="AUTH",
        user=username,
        session=session_id,
        success=True,
    )

    # Create a new chat
    chat_id = f"chat_{uuid.uuid4().hex[:12]}"
    log_chat(
        f'New chat created: "Voltage Regulator Design"',
        user=username,
        chat=chat_id,
        session=session_id,
    )

    # User sends a message
    context_logger.info(
        "User message received", component="CHAT", user=username, chat=chat_id
    )

    # LLM request
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    prompt = "Design a 5V to 3.3V voltage regulator with 1A output current"

    log_llm_request(
        user=username,
        chat=chat_id,
        request_id=request_id,
        model="gemini-2.5-flash",
        prompt_preview=prompt,
        tokens=150,
    )

    # Simulate LLM response
    import time

    time.sleep(0.1)  # Simulate API delay

    log_llm_response(
        user=username,
        chat=chat_id,
        request_id=request_id,
        tokens=300,
        cost=0.0045,
        duration_ms=2400,
    )

    # Start circuit generation
    generation_id = f"gen_{uuid.uuid4().hex[:8]}"

    context_logger.info(
        "Circuit generation started",
        component="CIRCUIT",
        user=username,
        chat=chat_id,
        generation_id=generation_id,
        circuit_type="voltage_regulator",
    )

    # Log progress stages
    logger.circuit_progress(
        user=username,
        chat=chat_id,
        generation_id=generation_id,
        stage="Python code generated",
        details="1.2KB",
    )

    # Using timer context for performance tracking
    with logger.timer("circuit_execution", user=username, chat=chat_id):
        # Simulate circuit execution
        time.sleep(0.05)

        logger.circuit_progress(
            user=username,
            chat=chat_id,
            generation_id=generation_id,
            stage="KiCad project created",
        )

    # Complete circuit generation
    context_logger.info(
        "Circuit generation completed",
        component="CIRCUIT",
        user=username,
        chat=chat_id,
        generation_id=generation_id,
        files=4,
        size_kb=15.6,
    )

    # File operation
    logger.file_operation(
        user=username,
        chat=chat_id,
        operation="Saved",
        filename="voltage_regulator.zip",
        size_kb=15.6,
    )

    # Simulate an error
    try:
        raise ValueError("Invalid component value: R1 = -100 ohms")
    except Exception as e:
        context_logger.error(
            "Circuit validation failed",
            error=e,
            user=username,
            chat=chat_id,
            generation=generation_id,
        )

    # User logout
    context_logger.info(
        "User logout", component="AUTH", user=username, session=session_id, success=True
    )


def example_multi_user_activity():
    """Show how multiple users appear in the unified log."""

    # User 1 activity
    context_logger.info(
        "User login successful",
        component="AUTH",
        user="alice",
        session="alice_20250627_214530_abc123",
    )
    context_logger.info(
        'New chat: "Op-Amp Filter"', component="CHAT", user="alice", chat="chat_aaa111"
    )

    # User 2 activity (interleaved)
    context_logger.info(
        "User login successful",
        component="AUTH",
        user="bob",
        session="bob_20250627_214531_def456",
    )
    context_logger.info(
        'New chat: "Power Supply"', component="CHAT", user="bob", chat="chat_bbb222"
    )

    # Concurrent LLM requests
    log_llm_request(
        user="alice",
        chat="chat_aaa111",
        request_id="req_111",
        model="gemini-2.5-flash",
        prompt_preview="Design a low-pass filter...",
        tokens=120,
    )

    log_llm_request(
        user="bob",
        chat="chat_bbb222",
        request_id="req_222",
        model="gemini-2.5-flash",
        prompt_preview="Create a 12V power supply...",
        tokens=150,
    )

    # Responses come back in different order
    log_llm_response(
        user="bob",
        chat="chat_bbb222",
        request_id="req_222",
        tokens=400,
        cost=0.0060,
        duration_ms=1800,
    )

    log_llm_response(
        user="alice",
        chat="chat_aaa111",
        request_id="req_111",
        tokens=350,
        cost=0.0052,
        duration_ms=2100,
    )


def example_log_output():
    """Show what the actual log file looks like."""

    print("Example log output:")
    print("-" * 80)
    print(
        """
2025-06-27 21:45:30.123 [INFO ] [AUTH    ] user=admin session=admin_20250627_214530_abc123 | User login successful
2025-06-27 21:45:35.456 [INFO ] [CHAT    ] user=admin chat=chat_abc123 session=admin_20250627_214530_abc123 | New chat created: "Voltage Regulator Design"
2025-06-27 21:45:40.789 [INFO ] [LLM     ] user=admin chat=chat_abc123 req=req_xyz789 | Request to gemini-2.5-flash: "Design a 5V to 3.3V voltage regulator with 1A output current" (150 tokens)
2025-06-27 21:45:43.234 [INFO ] [LLM     ] user=admin chat=chat_abc123 req=req_xyz789 | Response received: 300 tokens, $0.0045, 2.4s
2025-06-27 21:45:43.567 [INFO ] [CIRCUIT ] user=admin chat=chat_abc123 gen=gen_def456 | Circuit generation started: voltage_regulator
2025-06-27 21:45:48.890 [INFO ] [CIRCUIT ] user=admin chat=chat_abc123 gen=gen_def456 | Python code generated: 1.2KB
2025-06-27 21:45:52.123 [INFO ] [CIRCUIT ] user=admin chat=chat_abc123 gen=gen_def456 | KiCad files created: 4 files, 15.6KB total
2025-06-27 21:45:52.456 [INFO ] [FILES   ] user=admin chat=chat_abc123 | Saved: voltage_regulator.zip (15.6KB)
2025-06-27 21:46:15.789 [ERROR] [CIRCUIT ] user=admin chat=chat_abc123 gen=gen_def456 | Circuit validation failed: ValueError: Invalid component value: R1 = -100 ohms
2025-06-27 21:46:20.123 [INFO ] [AUTH    ] user=admin session=admin_20250627_214530_abc123 | User logout
"""
    )
    print("-" * 80)


if __name__ == "__main__":
    print("Unified Logger Example")
    print("======================\n")

    print("1. Running single user flow...")
    example_user_flow()
    print("   ✓ Check logs/circuit_synth.log for output\n")

    print("2. Running multi-user activity...")
    example_multi_user_activity()
    print("   ✓ Check logs/circuit_synth.log for interleaved user logs\n")

    print("3. Example log output:")
    example_log_output()

    print("\nGrep examples:")
    print("--------------")
    print('grep "user=admin" logs/circuit_synth.log          # All admin activity')
    print(
        'grep "\\[LLM     \\]" logs/circuit_synth.log      # All LLM requests/responses'
    )
    print('grep "\\[ERROR\\]" logs/circuit_synth.log         # All errors')
    print('grep "chat=chat_abc123" logs/circuit_synth.log   # Specific chat activity')
