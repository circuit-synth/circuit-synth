# Claude CLI GUI Hanging Issue

## Date: 2025-07-30

## Problem
Claude CLI hangs when called from tkinter GUI applications, despite working perfectly from command line.

## Evidence
- **Command Line**: Works perfectly (`claude "test"` returns response in ~4 seconds)
- **GUI Context**: Hangs indefinitely, requiring force quit
- **Debug Confirmed**: Connection succeeds, messages send, but no responses received

## Technical Details
- **Debug Test**: `/debug.py` confirms Claude CLI works from KiCad Python environment
- **GUI Hanging**: All GUI-based calls hang after `📤 Sending message to Claude:`
- **Process Isolation Attempted**: `stdin=subprocess.DEVNULL`, `start_new_session=True` - still hangs

## Workaround
Use `mock_ai.py` for full GUI functionality with simulated responses while investigating the underlying cause.