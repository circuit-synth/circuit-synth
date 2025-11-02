# Circuit-Synth Autonomous Workflows (ADWs)

TAC-8 inspired autonomous coordination system for circuit-synth development.

## What Is This?

This directory contains the **autonomous coordination system** that runs on your Raspberry Pi to automatically work on circuit-synth issues while you sleep/work on other things.

## Architecture

```
Simple TAC-8 Style System:

1. Coordinator polls GitHub (every 30s)
2. Finds issues with "rpi-auto" label
3. Adds to tasks.md (markdown state file)
4. Spawns Claude workers (max 3 concurrent)
5. Workers create PRs
6. You review and merge
```

## Files

- `coordinator.py` - Main polling loop (~500 lines, simple!)
- `config.toml` - Configuration (repo, labels, LLM settings)
- `../tasks.md` - Work queue (single source of truth)
- `../worker_template.md` - Prompt for workers
- `../trees/` - Git worktrees for parallel work
- `../logs/` - Worker output logs

## Quick Start

### On Raspberry Pi

```bash
# 1. Clone repo
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# 2. Install Python 3.11+
sudo apt install python3.11

# 3. Run coordinator
python3 adws/coordinator.py
```

That's it! Coordinator will:
- Poll GitHub for `rpi-auto` issues
- Spawn workers to fix them
- Create PRs for you to review

### On Your Dev Machine

```bash
# Just work normally!
# Review PRs created by coordinator
gh pr list

# Or add work manually
echo "[] Fix bug in subcircuits {p0}" >> tasks.md
```

## How It Works

### Adding Work

**Via GitHub** (automatic):
```bash
gh issue create --title "Fix voltage divider" --label "rpi-auto"
# Coordinator sees it in 30s, adds to tasks.md
```

**Via Manual Edit**:
```bash
echo "[] gh-123: Fix bug in tests {p1}" >> tasks.md
```

### Checking Status

```bash
# Just read the markdown file
cat tasks.md

# Or view on GitHub
# https://github.com/circuit-synth/circuit-synth/blob/main/tasks.md
```

### Starting/Stopping

**Start:**
```bash
python3 adws/coordinator.py
```

**Stop:**
```bash
# Ctrl+C for graceful shutdown
# Or: pkill -f coordinator.py
```

**Auto-start on boot** (systemd):
```bash
# Copy service file
sudo cp scripts/coordinator.service /etc/systemd/system/
sudo systemctl enable coordinator
sudo systemctl start coordinator
```

## Configuration

Edit `config.toml`:

```toml
[coordinator]
max_concurrent_workers = 3  # How many workers at once
poll_interval_seconds = 30  # How often to check GitHub

[github]
repo_owner = "circuit-synth"
repo_name = "circuit-synth"
issue_label = "rpi-auto"     # Which issues to process

[llm]
provider = "claude"          # or "aider", "openai", etc
model_default = "claude-sonnet-4-5"
```

### LLM-Agnostic Design

The coordinator works with any CLI-based LLM:

**Claude (default):**
```toml
command_template = ["claude", "-p", "{prompt_file}", "--model", "{model}", "--verbose"]
```

**Aider:**
```toml
command_template = ["aider", "--yes", "--message-file", "{prompt_file}", "--model", "{model}"]
```

**OpenAI:**
```toml
command_template = ["openai-cli", "{prompt_file}", "-m", "{model}"]
```

Just change the `command_template` in config.toml!

## The Simplicity

Notice what's **NOT** here:
- ❌ No database
- ❌ No message queue
- ❌ No REST API
- ❌ No web server
- ❌ No Docker
- ❌ No frameworks

Just:
- ✅ One Python script
- ✅ One markdown file
- ✅ Git worktrees
- ✅ Subprocess calls

**This is the genius of TAC-8:** Maximum simplicity, maximum power.

## Workflow Example

```
1. You create GitHub issue #456: "Fix dashboard bug"
   - Add label: "rpi-auto"

2. Coordinator sees it (30s later)
   - Adds to tasks.md: [] gh-456: Fix dashboard bug {p0}

3. Coordinator claims it
   - Updates: [🟡 w-abc123, trees/gh-456] gh-456: ...
   - Creates worktree: trees/gh-456/
   - Spawns worker: claude -p prompt.txt

4. Worker works (30-60 minutes)
   - Reads GitHub issue
   - Explores code
   - Writes tests
   - Implements fix
   - Creates PR #789

5. Coordinator detects completion
   - Updates: [✅ a1b2c3d, w-abc123] gh-456: ... PR: #789

6. You review (next morning)
   - gh pr view 789
   - gh pr merge 789
   - Done!
```

## Troubleshooting

### Coordinator not starting
```bash
# Check Python version
python3 --version  # Need 3.11+

# Check dependencies
pip install tomllib-w  # If on Python 3.10
```

### Workers failing
```bash
# Check logs
tail -f logs/gh-456.jsonl

# Check worktree
cd trees/gh-456
git status
```

### No issues being picked up
```bash
# Check GitHub label exists
gh label list | grep rpi-auto

# Check config
cat adws/config.toml
```

## Monitoring

```bash
# Watch coordinator output
python3 adws/coordinator.py

# Check active workers
ps aux | grep claude

# View work queue
cat tasks.md

# Check worktrees
git worktree list
```

## Comparison to circuit-synth-tac (old repo)

| Feature | Old (circuit-synth-tac) | New (adws/) |
|---------|------------------------|-------------|
| **Lines of code** | 2000+ | ~500 |
| **Dependencies** | Many (Dash, Plotly, etc) | Zero (stdlib only) |
| **State management** | JSON + Markdown | Pure markdown |
| **Complexity** | PMAgent, StateManager, etc | One script |
| **Philosophy** | Complex orchestration | TAC-8 simplicity |

We learned from TAC-8: **simpler is better**.

## Credits

Inspired by [TAC-8](https://github.com/tac-8) - the simple, powerful autonomous workflow system.

---

**Remember:** The `tasks.md` file is your entire UI. Read it to see what's happening. It's that simple.
