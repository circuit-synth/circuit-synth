# Circuit-Synth TAC-8 Coordinator - Raspberry Pi Deployment Guide

**Last Updated**: November 2, 2025  
**Status**: Production Ready

---

## Prerequisites Verified ✅

- ✅ Git installed and configured
- ✅ GitHub CLI authenticated
- ✅ Claude CLI installed and working
- ✅ Python 3.12+ available
- ✅ Repository cloned at `/home/shane/Desktop/circuit-synth`

---

## Phase 1 Implementation Complete ✅

All core fixes implemented and tested:

### 1. Idempotent Worktree Creation
- `ensure_worktree()` handles existing directories gracefully
- Manual fallback with `shutil.rmtree()` for orphaned directories
- `git worktree prune` removes stale git references
- **Verified**: Successfully cleaned up and recreated worktrees

### 2. Zombie Process Reaping
- SIGCHLD handler automatically reaps child processes
- Non-blocking `waitpid(-1, WNOHANG)` implementation
- Proper exit code extraction and logging
- **Verified**: No defunct processes after worker completion

### 3. Enhanced Status Tracking
- PR detection via `gh pr list --head <branch>`
- Automatic GitHub issue comments on completion
- Worktree cleanup after successful PR creation
- Failed task handling with BLOCKED.md support

---

## Production Deployment (Systemd)

### Service File Created

Location: `tools/circuit-synth-coordinator.service`

```ini
[Unit]
Description=Circuit-Synth TAC-8 Autonomous Coordinator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=shane
WorkingDirectory=/home/shane/Desktop/circuit-synth
ExecStart=/usr/bin/python3 /home/shane/Desktop/circuit-synth/adws/coordinator.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=circuit-synth-coordinator

[Install]
WantedBy=multi-user.target
```

### Installation Steps

**Run these commands manually** (requires sudo password):

```bash
# 1. Install service file
sudo cp /home/shane/Desktop/circuit-synth/tools/circuit-synth-coordinator.service /etc/systemd/system/

# 2. Reload systemd
sudo systemctl daemon-reload

# 3. Enable service (start on boot)
sudo systemctl enable circuit-synth-coordinator

# 4. Start service now
sudo systemctl start circuit-synth-coordinator

# 5. Verify it's running
sudo systemctl status circuit-synth-coordinator
```

---

## Monitoring the Coordinator

### View Live Logs

```bash
# Follow coordinator logs in real-time
sudo journalctl -u circuit-synth-coordinator -f

# Show last 100 lines
sudo journalctl -u circuit-synth-coordinator -n 100

# Show logs since last boot
sudo journalctl -u circuit-synth-coordinator -b
```

### Check Service Status

```bash
# Service status
sudo systemctl status circuit-synth-coordinator

# Check if enabled for boot
sudo systemctl is-enabled circuit-synth-coordinator

# View running processes
ps aux | grep coordinator
```

### Monitor Workers

```bash
# View worker conversation logs
python3 tools/view_worker.py <issue_number>

# Check tasks.md status
cat tasks.md

# Watch tasks.md live
watch -n 5 cat tasks.md

# Check for zombie processes (should be none)
ps aux | grep defunct
```

---

## Service Management

### Stop Coordinator

```bash
sudo systemctl stop circuit-synth-coordinator
```

### Restart Coordinator

```bash
sudo systemctl restart circuit-synth-coordinator
```

### Disable Auto-Start on Boot

```bash
sudo systemctl disable circuit-synth-coordinator
```

### Re-enable Auto-Start

```bash
sudo systemctl enable circuit-synth-coordinator
```

---

## Testing the Deployment

### 1. Create Test Issue

```bash
gh issue create --repo circuit-synth/circuit-synth \
  --title "Test: Deployment verification" \
  --body "Test issue to verify autonomous coordinator deployment." \
  --label "rpi-auto,priority:P0"
```

### 2. Monitor Progress

```bash
# Watch logs
sudo journalctl -u circuit-synth-coordinator -f
```

### 3. Expected Workflow

1. Coordinator detects new issue (within 30 seconds)
2. Worker spawns and starts work
3. Worker creates PR
4. Coordinator detects PR and updates tasks.md
5. GitHub issue gets comment with PR link
6. Worktree cleaned up

### 4. Verify Success

```bash
# Check if PR was created
gh pr list --repo circuit-synth/circuit-synth

# Check tasks.md shows completion
cat tasks.md | grep -A 5 "Completed Today"

# Verify no zombies
ps aux | grep defunct
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check for errors
sudo journalctl -u circuit-synth-coordinator -n 50

# Check service file syntax
sudo systemctl cat circuit-synth-coordinator

# Verify paths exist
ls -la /home/shane/Desktop/circuit-synth/adws/coordinator.py
```

### Workers Not Launching

```bash
# Check gh CLI auth
gh auth status

# Check Claude CLI
claude --help

# Check Python version
python3 --version  # Should be 3.12+
```

### Worktree Errors

```bash
# Clean up all worktrees manually
cd /home/shane/Desktop/circuit-synth
git worktree prune
for tree in trees/gh-*; do 
    git worktree remove "$tree" --force 2>/dev/null || rm -rf "$tree"
done
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce max_concurrent_workers in config
nano adws/config.toml
# Change: max_concurrent_workers = 1

# Restart service
sudo systemctl restart circuit-synth-coordinator
```

---

## Configuration

### Adjusting Settings

Edit `adws/config.toml`:

```bash
nano adws/config.toml
```

Common adjustments:
- `max_concurrent_workers`: Lower to 1-2 on limited hardware
- `poll_interval_seconds`: Increase to 60 to reduce polling
- `worker_timeout_hours`: Increase if tasks take longer

**After changes:**
```bash
sudo systemctl restart circuit-synth-coordinator
```

---

## Performance Metrics

### Expected Performance

- **Polling Interval**: 30 seconds
- **Max Concurrent Workers**: 3
- **Worker Timeout**: 2 hours
- **Memory Usage**: ~50-100MB per coordinator + 200-500MB per worker
- **CPU Usage**: <5% idle, 10-30% during worker activity

### Resource Limits

On Raspberry Pi 5 (8GB RAM):
- Can run 3 workers comfortably
- Reduce to 1-2 if other services are running

---

## Backup and Recovery

### Backup Configuration

```bash
# Backup config
cp adws/config.toml adws/config.toml.backup

# Backup tasks.md
cp tasks.md tasks.md.backup
```

### Restore After Crash

The coordinator is stateless! Just restart:

```bash
sudo systemctl restart circuit-synth-coordinator
```

Tasks in `tasks.md` will resume automatically.

---

## Updates

### Pull Latest Code

```bash
cd /home/shane/Desktop/circuit-synth
git pull origin main

# Restart service to use new code
sudo systemctl restart circuit-synth-coordinator
```

---

## Uninstall

If you need to remove the coordinator:

```bash
# Stop and disable service
sudo systemctl stop circuit-synth-coordinator
sudo systemctl disable circuit-synth-coordinator

# Remove service file
sudo rm /etc/systemd/system/circuit-synth-coordinator.service

# Reload systemd
sudo systemctl daemon-reload

# Clean up worktrees (optional)
cd /home/shane/Desktop/circuit-synth
for tree in trees/gh-*; do 
    git worktree remove "$tree" --force 2>/dev/null || rm -rf "$tree"
done
```

---

## Success Criteria ✅

The deployment is successful when:

1. ✅ Service starts without errors
2. ✅ Logs show coordinator polling GitHub
3. ✅ Workers launch for new issues
4. ✅ PRs are created automatically
5. ✅ tasks.md updates when PRs are created
6. ✅ GitHub issues get comments
7. ✅ No zombie processes accumulate
8. ✅ Service restarts automatically if it crashes
9. ✅ Service starts on boot

---

## Current Status

- **Code Version**: Commit `0a56ae4`
- **Branch**: main
- **All Phase 1 fixes**: Implemented and tested
- **Systemd service**: Created and ready
- **Documentation**: Complete

**Ready for 24/7 operation!**

Run the installation commands above to deploy.
