# GUI Crash Issue - Claude Message Threading

## Date: 2025-07-30

## Problem
The KiCad Claude plugin GUI crashes after sending messages to Claude, requiring hard stop of Python application.

## Symptoms
- Claude connection works (logs show successful connection and version)
- Message sending starts successfully (logs show "📤 Sending message to Claude")
- GUI freezes/crashes during Claude response processing
- Python application becomes unresponsive

## Root Cause Analysis
The issue is likely blocking I/O in the main GUI thread:

```python
# This blocks the GUI thread
response = claude.send_message(message)  # Can take 30+ seconds
```

## Technical Details
- `subprocess.run()` call to Claude CLI blocks the main thread
- GUI becomes unresponsive during the 30-45 second timeout
- No async/threading implementation for Claude API calls
- Tkinter main loop freezes waiting for subprocess response

## Solution Approach
Need to implement proper threading:

1. **Background Threading**: Move Claude API calls to background thread
2. **GUI Queue**: Use `queue.Queue` for thread-safe communication
3. **Periodic Updates**: Use `root.after()` to check for responses
4. **Loading States**: Show "thinking" indicator during API calls
5. **Timeout Handling**: Graceful handling of long responses

## Code Pattern Needed
```python
import threading
import queue

def send_message_threaded():
    def claude_worker():
        response = claude.send_message(message)
        response_queue.put(response)
    
    threading.Thread(target=claude_worker, daemon=True).start()
    check_response_queue()

def check_response_queue():
    try:
        response = response_queue.get_nowait()
        update_gui_with_response(response)
    except queue.Empty:
        root.after(100, check_response_queue)
```

## Priority
HIGH - This blocks the primary user workflow