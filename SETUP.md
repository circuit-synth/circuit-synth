# TAC-8 Coordinator: Complete Setup Guide

**Purpose**: Reproduce this entire autonomous coordination system on any computer from scratch.

**Last Updated**: November 2, 2025
**Tested On**: Raspberry Pi 5 (Ubuntu 24.04 ARM64), Ubuntu 22.04 x86_64

---

## Prerequisites

### Hardware Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB free
- Internet: Stable connection for GitHub API

**Recommended (Raspberry Pi 5)**:
- CPU: 4 cores ARM64
- RAM: 8 GB
- Disk: 64 GB microSD (Class 10 or better)
- Internet: Ethernet preferred over WiFi

---

## Step 1: System Preparation

### 1.1 Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Install Base Dependencies

```bash
# Python 3.12+ (required for tomllib)
sudo apt install -y python3 python3-pip python3-venv

# Git (required for worktrees, version control)
sudo apt install -y git git-lfs

# GitHub CLI (required for issue fetching, PR creation)
# Install from: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
type -p curl >/dev/null || (sudo apt update && sudo apt install curl -y)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
&& sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update \
&& sudo apt install gh -y

# Verify
python3 --version  # Should be 3.12+
git --version      # Should be 2.34+
gh --version       # Should be 2.0+
```

### 1.3 Install Claude Code CLI

**Option A: Official installation** (recommended):
```bash
# Visit https://claude.com/download
# Or install via package manager if available
```

**Option B: Verify existing installation**:
```bash
which claude  # Should show path
claude --version  # Should show version
```

### 1.4 Configure Git

```bash
# Set git identity (used for autonomous commits)
git config --global user.email "contact@circuitsynth.com"
git config --global user.name "Circuit Synth Contributors"

# Verify
git config --global --list | grep user
```

### 1.5 Authenticate with GitHub

```bash
# Login to GitHub CLI
gh auth login
# Select:
# - GitHub.com
# - HTTPS
# - Yes (authenticate Git)
# - Login with web browser

# Verify
gh auth status
```

---

## Step 2: Clone Repository

### 2.1 Choose Installation Directory

```bash
# Recommended for Raspberry Pi
cd ~
mkdir -p projects
cd projects

# Or use Desktop (for development)
cd ~/Desktop
```

### 2.2 Clone circuit-synth Repository

```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
```

### 2.3 Verify Repository Structure

```bash
# Should see:
ls adws/coordinator.py          # ✓ Main coordinator
ls worker_template.md           # ✓ Worker prompt template
ls adws/config.toml             # ✓ Configuration
ls adws/IMPLEMENTATION_PLAN.md  # ✓ Implementation plan
ls tools/view_worker.py         # ✓ Worker viewer tool
```

---

## Step 3: Configure Coordinator

### 3.1 Review Configuration

```bash
cat adws/config.toml
```

Default configuration:
```toml
[coordinator]
max_concurrent_workers = 3
poll_interval_seconds = 30
worker_timeout_hours = 2

[github]
repo_owner = "circuit-synth"
repo_name = "circuit-synth"
issue_label = "rpi-auto"

[llm]
provider = "claude"
command_template = [
    "claude",
    "-p", "{prompt_file}",
    "--model", "{model}",
    "--output-format", "stream-json",
    "--verbose",
    "--dangerously-skip-permissions"
]
model_default = "claude-sonnet-4-5"
```

### 3.2 Customize (If Needed)

```bash
# Edit configuration
nano adws/config.toml

# Common changes:
# - repo_owner/repo_name: If using different repository
# - issue_label: If using different label (default "rpi-auto")
# - max_concurrent_workers: Lower to 1-2 on limited hardware
# - poll_interval_seconds: Increase to 60 if rate-limiting
```

### 3.3 Test Configuration

```bash
# Validate TOML syntax
python3 -c "import tomllib; tomllib.load(open('adws/config.toml', 'rb'))"
# Should return no errors
```

---

## Step 4: Setup Python Environment (Optional but Recommended)

### 4.1 Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4.2 Install Python Dependencies

```bash
# If requirements.txt exists
pip install -r requirements.txt

# Or install manually
pip install --upgrade pip
```

---

## Step 5: Test GitHub Integration

### 5.1 Test Issue Fetching

```bash
# Test GitHub CLI access
gh issue list --repo circuit-synth/circuit-synth --label "rpi-auto" --limit 5

# Should show issues (or empty if none exist)
```

### 5.2 Create Test Issue

```bash
# Create a simple test issue
gh issue create --repo circuit-synth/circuit-synth \
  --title "Test: Setup verification" \
  --body "This is a test issue to verify autonomous coordination setup." \
  --label "rpi-auto,priority:P2"

# Note the issue number (e.g., #500)
```

---

## Step 6: Test Claude CLI Integration

### 6.1 Verify Claude Access

```bash
# Test Claude CLI
claude --help

# Should show help without errors
```

### 6.2 Test Prompt Execution

```bash
# Create test prompt
echo "What is 2+2? Reply with just the number." > /tmp/test_prompt.txt

# Run Claude
claude -p /tmp/test_prompt.txt --model claude-sonnet-4-5 \
  --output-format stream-json --verbose --dangerously-skip-permissions

# Should execute successfully and return 4
```

---

## Step 7: First Coordinator Run (Dry Run)

### 7.1 Run Coordinator for 1 Minute

```bash
# Start coordinator
timeout 60 python3 adws/coordinator.py

# Should see:
# 🚀 Circuit-Synth Coordinator starting...
# 📥 Found X new tasks from GitHub
# (runs for 60 seconds, then timeout kills it)
```

### 7.2 Verify Directories Created

```bash
ls -la logs/   # Should have prompt files and .jsonl logs
ls -la trees/  # May have worktree directories
```

### 7.3 Check for Errors

```bash
# Look for any errors in output
# Common issues:
# - "gh: command not found" → Install GitHub CLI
# - "claude: command not found" → Install Claude CLI
# - "Authentication required" → Run gh auth login
```

---

## Step 8: Full End-to-End Test

### 8.1 Create Controlled Test Issue

```bash
# Create very simple test issue
gh issue create --repo circuit-synth/circuit-synth \
  --title "Test: Add comment to README" \
  --body "Add a comment '# TAC-8 tested' to the top of README.md" \
  --label "rpi-auto,priority:P0"

# Note issue number (e.g., #501)
```

### 8.2 Start Coordinator

```bash
# Run coordinator in foreground
python3 adws/coordinator.py

# Or background with logging
python3 adws/coordinator.py > coordinator.log 2>&1 &
echo $! > coordinator.pid
```

### 8.3 Monitor Progress

In another terminal:

```bash
# Watch status
watch -n 5 python3 tools/status.py

# Or tail logs
tail -f logs/gh-501.jsonl | jq -r 'select(.type=="assistant") | .message.content[]? | select(.type=="text")? | .text'

# Or check tasks.md
watch -n 5 cat tasks.md
```

### 8.4 Wait for Completion

**Expected timeline**: 2-5 minutes
- Worker spawns
- Worker reads issue
- Worker makes changes
- Worker creates PR
- Status updates to "completed"

### 8.5 Verify Success

```bash
# Check if PR was created
gh pr list --repo circuit-synth/circuit-synth | grep "Test: Add comment"

# Check tasks.md shows completion
cat tasks.md | grep -A 3 "gh-501"

# Should show:
# [✅ <commit>, w-<id>] gh-501: Test: Add comment to README
# - Completed: <timestamp>
# - PR: <url>
```

### 8.6 Stop Coordinator

```bash
# If running in foreground: Ctrl+C

# If running in background:
kill $(cat coordinator.pid)
```

---

## Step 9: Production Setup (Raspberry Pi Only)

### 9.1 Create Systemd Service

```bash
# Copy service file
sudo cp tools/coordinator.service /etc/systemd/system/circuit-synth-coordinator.service

# Edit paths if needed
sudo nano /etc/systemd/system/circuit-synth-coordinator.service

# Update WorkingDirectory and ExecStart to match your installation:
# WorkingDirectory=/home/pi/projects/circuit-synth
# ExecStart=/usr/bin/python3 /home/pi/projects/circuit-synth/adws/coordinator.py
```

### 9.2 Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable (start on boot)
sudo systemctl enable circuit-synth-coordinator

# Start service
sudo systemctl start circuit-synth-coordinator

# Check status
sudo systemctl status circuit-synth-coordinator
```

### 9.3 Monitor Service

```bash
# View logs
sudo journalctl -u circuit-synth-coordinator -f

# Check status dashboard
python3 tools/status.py
```

---

## Step 10: Verification Checklist

Run through this checklist to verify everything works:

- [ ] Git installed and configured
- [ ] GitHub CLI authenticated (`gh auth status`)
- [ ] Claude CLI installed and working (`claude --help`)
- [ ] Repository cloned
- [ ] Configuration reviewed (adws/config.toml)
- [ ] Can fetch GitHub issues (`gh issue list`)
- [ ] Can run Claude (`claude -p test.txt`)
- [ ] Coordinator starts without errors
- [ ] Directories created (logs/, trees/)
- [ ] Test issue created
- [ ] Worker spawned for test issue
- [ ] PR created by worker
- [ ] tasks.md updated
- [ ] (Pi only) Systemd service running

---

## Troubleshooting

### Issue: "gh: command not found"

**Solution**: Install GitHub CLI
```bash
# See Step 1.2 for installation commands
```

### Issue: "claude: command not found"

**Solution**: Install Claude CLI
```bash
# Visit https://claude.com/download
# Follow installation instructions for your platform
```

### Issue: "Authentication required"

**Solution**: Login to GitHub
```bash
gh auth login
# Follow prompts
```

### Issue: "fatal: already exists" (worktree errors)

**Solution**: Clean up stale worktrees
```bash
cd ~/projects/circuit-synth
for tree in trees/gh-*; do
  git worktree remove "$tree" --force 2>/dev/null
done
```

### Issue: Worker doesn't start

**Symptoms**: Coordinator says "spawned worker" but nothing happens

**Debug**:
```bash
# Check worker logs
ls -lh logs/

# Try running worker command manually
cat logs/gh-XXX-prompt.txt  # See what prompt was generated
claude -p logs/gh-XXX-prompt.txt --model claude-sonnet-4-5 \
  --output-format stream-json --verbose --dangerously-skip-permissions
```

### Issue: Python version too old

**Symptoms**: `ModuleNotFoundError: No module named 'tomllib'`

**Solution**: Upgrade Python to 3.12+
```bash
# On Ubuntu 24.04+
sudo apt install python3.12

# Or use pyenv
curl https://pyenv.run | bash
pyenv install 3.12
pyenv global 3.12
```

### Issue: Permission denied errors

**Solution**: Ensure correct ownership
```bash
sudo chown -R $USER:$USER ~/projects/circuit-synth
chmod +x tools/*.py
chmod +x adws/coordinator.py
```

---

## Reproducing on Different Systems

### On Ubuntu/Debian

Follow all steps as written above.

### On macOS

**Differences**:
- Install via Homebrew: `brew install gh python@3.12`
- Claude CLI installation may differ
- Paths may be different (~/Library/ instead of ~/.config/)

### On Windows (WSL2)

**Differences**:
- Use WSL2 Ubuntu
- Install Windows Terminal for better experience
- Clone repo inside WSL filesystem, not /mnt/c/

### On Another Raspberry Pi

**Fastest path**:
```bash
# Install dependencies
sudo apt update && sudo apt install -y git gh python3

# Clone repository
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth

# Configure GitHub
gh auth login

# Install Claude CLI
# (follow official instructions)

# Start coordinator
python3 adws/coordinator.py
```

---

## Maintenance

### Update to Latest Version

```bash
cd ~/projects/circuit-synth
git pull origin main
```

### Backup Configuration

```bash
# Backup custom config
cp adws/config.toml adws/config.toml.backup

# Backup tasks.md (if you want to preserve history)
cp tasks.md tasks.md.backup
```

### Clean Up Old Worktrees

```bash
# Remove all worktrees (safe - doesn't affect main repo)
for tree in trees/gh-*; do
  git worktree remove "$tree" --force
done

# Remove old logs (older than 7 days)
find logs/ -name "*.jsonl" -mtime +7 -delete
```

---

## Next Steps

After successful setup:

1. **Read documentation**:
   - `adws/IMPLEMENTATION_PLAN.md` - What's next to implement
   - `adws/CONTROL_AND_MONITORING.md` - How to control workers
   - `adws/GIT_WORKFLOW.md` - How to commit changes

2. **Monitor for a few days**:
   - Check `python3 tools/status.py` daily
   - Review PRs created
   - Adjust config if needed

3. **Implement improvements**:
   - Follow IMPLEMENTATION_PLAN.md Phase 1 (core fixes)
   - Add metrics (Phase 2)
   - Deploy to production (Phase 6)

---

## Support

**Documentation**:
- GitHub: https://github.com/circuit-synth/circuit-synth
- Issues: https://github.com/circuit-synth/circuit-synth/issues

**Prerequisites Help**:
- GitHub CLI: https://cli.github.com/manual/
- Claude Code: https://claude.com/docs
- Git Worktrees: https://git-scm.com/docs/git-worktree

---

**Estimated Setup Time**: 30-60 minutes
**Skill Level Required**: Intermediate (comfortable with terminal, git, python)
**Cost**: $0 (uses Claude Code subscription, not API)

**You should now have a fully functional autonomous coordination system!** 🚀
