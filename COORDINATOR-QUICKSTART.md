# TAC-8 Coordinator - Quick Start Guide

## ✅ System Status

**Logs**: Clean (8 conversation logs, 91,460 tokens)
**Config**: Safe (max 1 worker, 30s poll)
**Tools**: Ready (view-conversation.py, query-logs.py, monitor-live.py)
**Corrupted Files**: Archived to logs/corrupted/

## 🚀 Starting the Coordinator

### Option 1: Foreground (watch it run)
```bash
cd adws
python3 coordinator.py
```

### Option 2: Background (runs in background)
```bash
cd adws
nohup python3 coordinator.py > ../coordinator.log 2>&1 &
echo $!  # This is the PID
```

### Option 3: With live monitoring (recommended)
```bash
# Terminal 1: Start coordinator
cd adws
python3 coordinator.py

# Terminal 2: Watch live dashboard
./tools/monitor-live.py
```

## 📊 Monitoring Tools

### Live Dashboard
```bash
./tools/monitor-live.py
```
Shows:
- Coordinator status (running/stopped)
- Active workers
- Recent log activity (last 5 min)
- Worktrees with changes
- Today's token usage and cost

Refreshes every 5 seconds. Press Ctrl+C to exit.

### Query Logs
```bash
# Summary of all conversations
./tools/query-logs.py summary

# Token usage for specific task
./tools/query-logs.py tokens gh-449

# Search conversations
./tools/query-logs.py search "spawn loop"

# List all logs
./tools/query-logs.py list
```

### View Conversation
```bash
# Full conversation
./tools/view-conversation.py logs/gh-449.jsonl

# Just summary
./tools/view-conversation.py logs/gh-449.jsonl --summary
```

### Coordinator Log
```bash
# Live tail
tail -f coordinator.log

# Last 50 lines
tail -50 coordinator.log

# Search for errors
grep -i error coordinator.log
```

## 🎯 What to Watch

### Good Signs
- ✅ Coordinator polling every 30 seconds
- ✅ Workers spawning for rpi-auto labeled issues
- ✅ Log files being created/updated in logs/
- ✅ Worktrees cleaned up after completion
- ✅ PR creation for completed tasks

### Warning Signs
- ⚠️ Worker running for > 2 hours (timeout)
- ⚠️ Worktree with changes but no running worker
- ⚠️ Multiple spawn attempts for same task
- ⚠️ Error messages in coordinator.log

### Red Flags
- 🔴 Coordinator stopped unexpectedly
- 🔴 Spawn loop (same task spawning repeatedly)
- 🔴 OOM errors
- 🔴 Disk full
- 🔴 All null byte log files (corruption)

## 🛠️ Troubleshooting

### Coordinator won't start
```bash
# Check if already running
ps aux | grep coordinator.py

# Check for port conflicts
lsof -i :8000  # If using dashboard

# Check Python dependencies
cd adws
python3 -c "import toml, requests; print('OK')"
```

### Worker stuck
```bash
# Find worker PID
ps aux | grep "claude -p"

# Check worker log
./tools/view-conversation.py logs/gh-XXX.jsonl --summary

# Kill if needed (last resort)
kill <PID>
```

### Spawn loop detected
```bash
# Check coordinator log
grep "gh-XXX" coordinator.log | tail -20

# Check worktree status
ls -la trees/gh-XXX
git -C trees/gh-XXX status

# Manual fix
rm -rf trees/gh-XXX  # Remove stuck worktree
```

### Logs corrupted
```bash
# Run health check
file logs/*.jsonl | grep -v "JSON"

# Move corrupted to archive
mkdir -p logs/corrupted
mv logs/gh-XXX.jsonl logs/corrupted/
```

## 🔧 Configuration

### adws/config.toml

Current safe settings:
```toml
[coordinator]
max_concurrent_workers = 1  # Prevents resource exhaustion
poll_interval_seconds = 30
worker_timeout_hours = 2
```

### Adjusting for production
```toml
[coordinator]
max_concurrent_workers = 3  # Increase when stable
poll_interval_seconds = 60  # Less frequent polling
worker_timeout_hours = 4    # Longer for complex tasks
```

## 📝 Creating Test Issues

Want to test? Create a GitHub issue with:
- Label: `rpi-auto`
- Title: Clear description of task
- Body: Detailed requirements

Example:
```
Title: Add LED blink example to examples/
Body: Create a simple LED blink example using GPIO pin 17.
```

## 🔄 Normal Workflow

1. **Issue Created** - User creates GitHub issue with `rpi-auto` label
2. **Detection** - Coordinator polls and detects new issue
3. **Worktree Created** - New git worktree in `trees/gh-XXX`
4. **Worker Spawned** - `claude -p` process starts working on task
5. **Work Progress** - Conversation logged to `logs/gh-XXX.jsonl`
6. **PR Created** - Worker creates pull request when done
7. **Cleanup** - Worktree removed (or preserved if recent changes)

## 🎬 Quick Start Steps

1. **Verify no issues labeled rpi-auto** (unless you want to test)
   ```bash
   gh issue list --label rpi-auto
   ```

2. **Start monitoring dashboard** (terminal 1)
   ```bash
   ./tools/monitor-live.py
   ```

3. **Start coordinator** (terminal 2)
   ```bash
   cd adws
   python3 coordinator.py
   ```

4. **Watch logs** (terminal 3, optional)
   ```bash
   tail -f coordinator.log
   ```

5. **Create test issue** (if desired)
   ```bash
   gh issue create \
     --title "Test: Add simple LED example" \
     --body "Create examples/led_blink.py" \
     --label rpi-auto
   ```

6. **Observe**
   - Monitor dashboard shows worker spawn
   - coordinator.log shows activity
   - logs/gh-XXX.jsonl being created
   - trees/gh-XXX worktree appears

## 📊 Today's Recap

- **Fixed**: 2 corrupted logs (gh-450, gh-453)
- **Recovered**: gh-455 (167 events salvaged)
- **Tools Created**: view-conversation.py, query-logs.py, monitor-live.py
- **Documentation**: VIEWING-LOGS.md, TAC-8-SIMPLIFIED-LOGGING.md

**Ready to run!** 🚀
