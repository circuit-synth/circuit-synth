# TAC-8 Autonomous Development System - Setup Guide

**TAC-8** (Task Autonomous Coordinator - 8 concurrent workers max) is the autonomous development system for circuit-synth. This guide will help you set up TAC-8 from scratch on a Linux system.

---

## Overview

TAC-8 enables autonomous development by:
- Polling GitHub for issues labeled `rpi-auto`
- Spawning autonomous Claude workers in isolated git worktrees
- Capturing complete conversation logs in JSONL format
- Providing comprehensive monitoring and analysis tools

---

## Prerequisites

### Required Software

1. **Python 3.9+**
   ```bash
   python3 --version  # Should be 3.9 or higher
   ```

2. **Git with worktree support**
   ```bash
   git --version  # Should be 2.25+
   ```

3. **GitHub CLI**
   ```bash
   gh --version
   # If not installed:
   # Ubuntu/Debian: sudo apt install gh
   # Or: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
   ```

4. **Claude CLI with provider support**
   ```bash
   claude --version
   # Installation: npm install -g @anthropic-ai/claude-cli
   # Or pip install claude-cli
   ```

5. **tmux** (optional, for multi-pane monitoring)
   ```bash
   sudo apt install tmux
   ```

### Required Credentials

1. **GitHub Authentication**
   ```bash
   gh auth login
   # Follow prompts to authenticate
   ```

2. **Claude API Key** or **Provider Configuration**
   TAC-8 uses `claude -p <provider>` for LLM calls, supporting multiple providers:

   - **Anthropic API**: Set `ANTHROPIC_API_KEY` environment variable
   - **AWS Bedrock**: Configure `~/.aws/credentials`
   - **GCP Vertex**: Set up `gcloud` authentication

   The coordinator spawns workers with: `claude -p <provider> --stream-json`

---

## Installation Steps

### 1. Clone Repository

```bash
cd ~/Desktop
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
```

### 2. Install Python Dependencies

```bash
# Core dependencies
pip3 install toml requests python-dotenv

# Optional: For monitoring dashboard
pip3 install rich blessed
```

### 3. Configure Coordinator

Edit `adws/config.toml`:

```toml
[coordinator]
poll_interval = 30              # Poll GitHub every 30 seconds
max_concurrent_workers = 1      # Max parallel workers (1 recommended for Raspberry Pi)
github_repo = "circuit-synth/circuit-synth"
github_label = "rpi-auto"       # Label to trigger autonomous work

[worker]
provider = "anthropic"          # LLM provider: anthropic, bedrock, vertex
model = "claude-sonnet-4"       # Model to use
timeout = 3600                  # Worker timeout in seconds
max_retries = 3                 # Retries on failure

[paths]
trees_dir = "trees"             # Worktree directory
logs_dir = "logs"               # Conversation logs
tasks_file = "tasks.md"         # Task queue file
```

### 4. Set Environment Variables

Create `.env` file in project root (optional, if using environment-based config):

```bash
# Provider-specific credentials
ANTHROPIC_API_KEY=your_key_here

# Optional: Override config.toml settings
TAC_POLL_INTERVAL=30
TAC_MAX_WORKERS=1
```

### 5. Install Bashrc Aliases

Add to your `~/.bashrc`:

```bash
# TAC-8 Monitoring Tools
source ~/Desktop/circuit-synth/tools/bashrc-aliases.sh
```

Then reload:

```bash
source ~/.bashrc
```

You should see:
```
🤖 TAC-8 monitoring aliases loaded! Try: tac-help
```

### 6. Create Required Directories

```bash
cd ~/Desktop/circuit-synth

# Directories are auto-created by coordinator, but you can create them manually:
mkdir -p trees logs exports

# Verify structure
ls -ld trees logs exports
```

### 7. Verify Installation

```bash
# Check all tools are available
tac-help

# Should show:
# 🤖 TAC-8 MONITORING ALIASES
# [list of all commands]
```

---

## Starting TAC-8

### Manual Start

```bash
cd ~/Desktop/circuit-synth/adws
python3 coordinator.py > ../coordinator.log 2>&1 &
```

### Using Alias

```bash
tac-start
```

### Verify It's Running

```bash
tac-ps

# Should show:
# shane    12345  ... python3 coordinator.py
```

### Monitor Coordinator

```bash
# Tail coordinator log
tac-tail

# Or watch with refresh
tac-watch

# Or use live dashboard
tac-monitor
```

---

## Directory Structure

After installation and first run:

```
circuit-synth/
├── adws/
│   ├── coordinator.py          # Main coordinator
│   ├── config.toml             # Configuration
│   └── adw_modules/            # Coordinator modules
│       ├── api_logger.py       # API usage tracking
│       └── error_handling.py   # Error recovery
│
├── trees/                      # Git worktrees (one per active task)
│   └── gh-471/                 # Example: worktree for issue #471
│       ├── CLAUDE.md           # Worker instructions
│       ├── src/                # Isolated working directory
│       └── ...
│
├── logs/                       # Conversation logs
│   ├── gh-471.jsonl            # Complete conversation for task gh-471
│   ├── gh-472.jsonl
│   └── ...
│
├── exports/                    # Exported task data
│   ├── gh-471_export.json      # Full task data
│   └── gh-471_export.md        # Human-readable report
│
├── tools/                      # Monitoring and analysis tools
│   ├── monitor-live.py         # Real-time dashboard
│   ├── query-logs.py           # Multi-log analysis
│   ├── view-conversation.py    # Single conversation viewer
│   ├── generate-report.py      # Historical reports
│   ├── export-task.py          # Export task data
│   └── bashrc-aliases.sh       # Shell aliases
│
├── coordinator.log             # Coordinator stdout/stderr
├── tasks.md                    # Task queue state
└── pricing-cache.json          # API usage cache
```

---

## Using TAC-8

### Triggering Autonomous Work

1. **Add label to GitHub issue:**
   ```bash
   tac-label-add 471

   # Or manually:
   gh issue edit 471 --add-label rpi-auto
   ```

2. **Coordinator detects label** (within 30 seconds)

3. **Worker spawns** in `trees/gh-471/`

4. **Worker works autonomously:**
   - Reads issue
   - Explores codebase
   - Writes tests
   - Implements solution
   - Creates PR
   - **Removes `rpi-auto` label** (prevents duplicate workers)

5. **PR ready for review**

### Monitoring Active Work

**Real-time dashboard:**
```bash
tac-monitor
```

**Quick status:**
```bash
tac-status
```

**View specific task conversation:**
```bash
tac-view logs/gh-471.jsonl
```

**Check running processes:**
```bash
tac-ps
```

**Export complete task data:**
```bash
tac-export gh-471
# Creates: exports/gh-471_export.json and exports/gh-471_export.md
```

### Stopping Work

**Stop spawning new workers for a task:**
```bash
tac-label-remove 471
```

**Stop coordinator:**
```bash
tac-kill
```

**Restart coordinator:**
```bash
tac-restart
```

---

## Monitoring Tools Reference

### 1. `tac-monitor` - Real-time Dashboard

Continuously updating dashboard showing:
- Active tasks
- Worker status
- Recent log activity
- System resources

**Usage:**
```bash
tac-monitor
# Press Ctrl+C to exit
```

### 2. `tac-status` - Quick Summary

One-time summary of all logs:
- Task list
- Token usage
- Tool usage
- Recent activity

**Usage:**
```bash
tac-status
```

### 3. `tac-view` - Conversation Viewer

View full conversation for a specific task:

**Usage:**
```bash
tac-view logs/gh-471.jsonl
```

### 4. `tac-export` - Data Export

Export complete task data (conversation, tokens, metadata):

**Usage:**
```bash
# Export as both JSON and Markdown
tac-export gh-471

# JSON only
tac-export gh-471 --format json

# Custom output directory
tac-export gh-471 --output /path/to/exports/
```

**Output:**
- `exports/gh-471_export.json` - Full data with all events
- `exports/gh-471_export.md` - Human-readable report

### 5. `tac-report` - Historical Analysis

Generate comprehensive historical report:

**Usage:**
```bash
# Report on all tasks
tac-report

# Timeline view
tac-timeline

# Specific task detail
tac-task gh-471
```

---

## Troubleshooting

### Coordinator Not Starting

**Check logs:**
```bash
cat coordinator.log
```

**Common issues:**
- Missing config.toml: `cp adws/config.toml.example adws/config.toml`
- Wrong Python version: `python3 --version` (need 3.9+)
- Missing dependencies: `pip3 install toml requests`

### Worker Fails Immediately

**Check worker log:**
```bash
ls trees/gh-*/
cat trees/gh-471/worker.log  # If exists
```

**Common issues:**
- Claude CLI not installed: `claude --version`
- API key not set: Check `ANTHROPIC_API_KEY` or provider config
- Git worktree conflict: Remove old worktree with `git worktree remove trees/gh-471 --force`

### Duplicate Workers Spawning

**Symptoms:** Multiple PRs created for same issue

**Cause:** Worker didn't remove `rpi-auto` label

**Fix:**
1. Manually remove label: `tac-label-remove 471`
2. Kill duplicate workers: `tac-kill`
3. Clean up extra worktrees: `git worktree list` and remove duplicates

**Prevention:** Worker template includes label removal step (fixed in PR #502)

### Logs Corrupted or Missing

**Recovery:**
```bash
# Check for corrupted logs
./tools/query-logs.py summary

# Corrupted logs are archived to logs/corrupted/
ls logs/corrupted/
```

**Prevention:** Ensure adequate disk space and avoid killing workers mid-stream

### Monitor Tools Not Working

**Check installation:**
```bash
which python3
ls -l tools/*.py
```

**Make executable:**
```bash
chmod +x tools/*.py
```

**Check Python path in shebangs:**
```bash
head -1 tools/*.py
# Should show: #!/usr/bin/env python3
```

### Bashrc Aliases Not Loading

**Verify sourcing:**
```bash
grep bashrc-aliases ~/.bashrc
# Should show: source ~/Desktop/circuit-synth/tools/bashrc-aliases.sh
```

**Reload bashrc:**
```bash
source ~/.bashrc
```

**Check path:**
```bash
ls ~/Desktop/circuit-synth/tools/bashrc-aliases.sh
```

---

## Advanced Configuration

### Multiple Concurrent Workers

**Edit `adws/config.toml`:**
```toml
[coordinator]
max_concurrent_workers = 3  # Allow up to 3 parallel workers
```

**Note:** Requires sufficient system resources. Raspberry Pi should use 1.

### Custom Polling Interval

**Edit `adws/config.toml`:**
```toml
[coordinator]
poll_interval = 60  # Poll every 60 seconds instead of 30
```

### Different Model or Provider

**Edit `adws/config.toml`:**
```toml
[worker]
provider = "bedrock"           # Use AWS Bedrock
model = "claude-3-opus-20240229"  # Use Opus model
```

### Tmux Monitoring Layout

**Start 3-pane monitoring:**
```bash
tac-tmux
```

**Layout:**
```
┌─────────────────┬─────────────────┬─────────────────┐
│                 │                 │                 │
│   tac-tail      │   tac-watch     │  tac-monitor    │
│   (coordinator  │   (recent logs) │  (live dash)    │
│    log tail)    │                 │                 │
│                 │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
```

**Attach to existing session:**
```bash
tac-attach
```

**Kill tmux session:**
```bash
tac-tmux-kill
```

---

## Best Practices

### 1. Label Management

- **Add `rpi-auto` only when ready** for autonomous work
- **Remove label** if you want to work manually
- **One label at a time** for resource-constrained systems

### 2. Monitoring

- **Check `tac-status` daily** to review activity
- **Export completed tasks** for archival: `tac-export gh-471`
- **Monitor coordinator log** during active work: `tac-tail`

### 3. Cleanup

**Regularly clean up completed worktrees:**
```bash
tac-clean
# Shows: git worktree list
# To remove: git worktree remove trees/gh-471 --force
```

**Archive old logs:**
```bash
# Move logs older than 30 days to archive
mkdir -p logs/archive
find logs -name "*.jsonl" -mtime +30 -exec mv {} logs/archive/ \;
```

### 4. Resource Management

**Check system resources:**
```bash
tac-resources
```

**Monitor API usage:**
```bash
cat pricing-cache.json | python3 -m json.tool
```

### 5. Backup

**Backup conversation logs:**
```bash
# Logs contain complete task history
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

**Backup exports:**
```bash
tar -czf exports-backup-$(date +%Y%m%d).tar.gz exports/
```

---

## Architecture Notes

### Worker Lifecycle

1. **Coordinator detects** issue with `rpi-auto` label
2. **Creates git worktree** at `trees/gh-{issue_number}/`
3. **Generates worker prompt** from `worker_template.md`
4. **Spawns Claude worker**: `claude -p {provider} --stream-json`
5. **Logs conversation** to `logs/gh-{issue_number}.jsonl`
6. **Worker completes**:
   - Creates PR
   - Removes `rpi-auto` label
   - Updates `tasks.md`
7. **Coordinator cleans up** worktree after 24h (if completed)

### Log Format

Logs use JSONL (JSON Lines) format:
```json
{"type": "system", "timestamp": "2025-11-03T10:30:00Z", "session_id": "abc", "model": "claude-sonnet-4"}
{"type": "user", "timestamp": "2025-11-03T10:30:01Z", "message": {"role": "user", "content": "..."}}
{"type": "assistant", "timestamp": "2025-11-03T10:30:05Z", "message": {"role": "assistant", "content": [...], "usage": {"input_tokens": 1000, "output_tokens": 500}}}
```

Each line is a valid JSON object, making it easy to stream and parse incrementally.

### Provider Abstraction

TAC-8 uses `claude -p <provider>` for LLM calls, not direct API calls. This provides:
- **Flexibility**: Switch between Anthropic, Bedrock, Vertex without code changes
- **Reliability**: Claude CLI handles retries, rate limiting
- **Cost tracking**: Consistent usage tracking across providers

---

## Reproducing Setup on New Machine

### Quick Setup Script

```bash
#!/bin/bash
# setup-tac8.sh - Quick setup for TAC-8

set -e

echo "🤖 Setting up TAC-8..."

# 1. Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 required"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Git required"; exit 1; }
command -v gh >/dev/null 2>&1 || { echo "❌ GitHub CLI required"; exit 1; }
command -v claude >/dev/null 2>&1 || { echo "❌ Claude CLI required"; exit 1; }

echo "✅ Prerequisites met"

# 2. Install Python dependencies
pip3 install toml requests python-dotenv rich blessed

echo "✅ Dependencies installed"

# 3. Authenticate GitHub
gh auth status || gh auth login

echo "✅ GitHub authenticated"

# 4. Add bashrc aliases
if ! grep -q "bashrc-aliases.sh" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# TAC-8 Monitoring Tools" >> ~/.bashrc
    echo "source ~/Desktop/circuit-synth/tools/bashrc-aliases.sh" >> ~/.bashrc
    echo "✅ Bashrc aliases added"
else
    echo "✅ Bashrc aliases already configured"
fi

# 5. Source bashrc
source ~/.bashrc

echo ""
echo "🎉 TAC-8 setup complete!"
echo ""
echo "Next steps:"
echo "  1. Configure adws/config.toml (set provider, model)"
echo "  2. Set API key: export ANTHROPIC_API_KEY=your_key"
echo "  3. Start coordinator: tac-start"
echo "  4. Monitor: tac-monitor"
echo ""
echo "Try: tac-help"
```

Save as `tools/setup-tac8.sh`, make executable, and run:

```bash
chmod +x tools/setup-tac8.sh
./tools/setup-tac8.sh
```

---

## Reference: All TAC-8 Commands

### Monitoring
- `tac-monitor` - Live dashboard (refreshes every 5s)
- `tac-status` - Quick summary of all logs
- `tac-view <log>` - View conversation (e.g., `tac-view logs/gh-471.jsonl`)
- `tac-report` - Generate historical report
- `tac-export <task>` - Export task data (e.g., `tac-export gh-471`)

### Logs
- `tac-tail` - Tail coordinator log
- `tac-watch` - Watch coordinator log (refreshes every 2s)
- `tac-logs` - List all conversation logs

### Process Management
- `tac-ps` - Check coordinator status
- `tac-start` - Start coordinator
- `tac-restart` - Restart coordinator
- `tac-kill` - Stop coordinator

### GitHub Integration
- `tac-issues` - List issues with rpi-auto label
- `tac-label-add <issue>` - Add rpi-auto to issue (usage: `tac-label-add 471`)
- `tac-label-remove <issue>` - Remove rpi-auto from issue
- `tac-pr <branch>` - View PR for task

### Search & Analysis
- `tac-search <text>` - Search conversations
- `tac-tokens <task>` - Token usage for task
- `tac-timeline` - Activity timeline
- `tac-task <task>` - Detailed task report

### Management
- `tac` - Navigate to TAC directory
- `tac-trees` - List worktrees
- `tac-clean` - Clean up worktrees
- `tac-tmux` - 3-column tmux monitoring
- `tac-help` - Show help message

### System
- `tac-resources` - System resource usage

---

## Support

**Issues:** https://github.com/circuit-synth/circuit-synth/issues

**Documentation:** See `docs/` directory for more details

**Worker Template:** `worker_template.md` defines worker behavior

**Configuration:** `adws/config.toml` for coordinator settings

---

*Last updated: 2025-11-03*
*Version: 1.0*
