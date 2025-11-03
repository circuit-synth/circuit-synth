# ================================
# Circuit-Synth TAC-8 Monitoring Aliases
# ================================
# Add to your ~/.bashrc:
#   source ~/Desktop/circuit-synth/tools/bashrc-aliases.sh

# TAC-8 directory
export TAC_DIR=~/Desktop/circuit-synth

# Navigate to TAC directory
alias tac='cd $TAC_DIR'

# ================================================================================
# MONITORING TOOLS
# ================================================================================

# Live monitoring dashboard (refreshes every 5 seconds)
alias tac-monitor='cd $TAC_DIR && ./tools/monitor-live.py'

# Quick status summary
alias tac-status='cd $TAC_DIR && ./tools/query-logs.py summary'

# View conversation for a specific task
alias tac-view='cd $TAC_DIR && ./tools/view-conversation.py'

# Generate historical report
alias tac-report='cd $TAC_DIR && ./tools/generate-report.py --all'

# Export task data (usage: tac-export gh-471)
alias tac-export='cd $TAC_DIR && ./tools/export-task.py'

# ================================================================================
# LOG FILE MONITORING
# ================================================================================

# Tail coordinator log
alias tac-tail='tail -f $TAC_DIR/coordinator.log'

# Watch coordinator log
alias tac-watch='watch -n 2 "tail -20 $TAC_DIR/coordinator.log 2>/dev/null || echo \"Coordinator not running\""'

# View all logs directory
alias tac-logs='ls -lh $TAC_DIR/logs/*.jsonl'

# ================================================================================
# PROCESS MANAGEMENT
# ================================================================================

# Check coordinator status
alias tac-ps='ps aux | grep -E "coordinator.py|claude.*gh-" | grep -v grep'

# Kill coordinator
alias tac-kill='pkill -f coordinator.py'

# Start coordinator
alias tac-start='cd $TAC_DIR/adws && python3 coordinator.py > ../coordinator.log 2>&1 &'

# Restart coordinator
alias tac-restart='tac-kill && sleep 2 && tac-start && echo "Coordinator restarted"'

# ================================================================================
# GITHUB INTEGRATION
# ================================================================================

# List issues with rpi-auto label
alias tac-issues='gh issue list --repo circuit-synth/circuit-synth --label "rpi-auto" --json number,title,state --template "{{range .}}#{{.number}}: {{.title}} [{{.state}}]{{\"\\n\"}}{{end}}"'

# Add rpi-auto label to issue (usage: tac-label-add 471)
tac-label-add() {
    gh issue edit "$1" --repo circuit-synth/circuit-synth --add-label rpi-auto
    echo "✅ Added rpi-auto label to issue #$1"
    echo "   Coordinator will pick it up in ~30 seconds"
}

# Remove rpi-auto label from issue (usage: tac-label-remove 471)
tac-label-remove() {
    gh issue edit "$1" --repo circuit-synth/circuit-synth --remove-label rpi-auto
    echo "✅ Removed rpi-auto label from issue #$1"
    echo "   Coordinator will stop spawning workers"
}

# View PR for task (usage: tac-pr gh-471)
alias tac-pr='gh pr list --repo circuit-synth/circuit-synth --head'

# ================================================================================
# SEARCH & ANALYSIS
# ================================================================================

# Search conversations for text (usage: tac-search "label cleanup")
alias tac-search='cd $TAC_DIR && ./tools/query-logs.py search'

# Token usage for specific task (usage: tac-tokens gh-471)
alias tac-tokens='cd $TAC_DIR && ./tools/query-logs.py tokens'

# Timeline of all activity
alias tac-timeline='cd $TAC_DIR && ./tools/generate-report.py --timeline'

# Detailed task report (usage: tac-task gh-471)
alias tac-task='cd $TAC_DIR && ./tools/generate-report.py --task'

# ================================================================================
# WORKTREE MANAGEMENT
# ================================================================================

# List active worktrees
alias tac-trees='cd $TAC_DIR && ls -lh trees/ 2>/dev/null || echo "No worktrees"'

# Clean up completed worktrees (manual)
alias tac-clean='cd $TAC_DIR && echo "Worktrees:" && git worktree list && echo && echo "To remove: git worktree remove trees/<name> --force"'

# ================================================================================
# TMUX MONITORING SESSIONS
# ================================================================================

# 3-column tail monitoring (requires tmux)
alias tac-tmux='tmux new-session -d -s tac \; send-keys "cd $TAC_DIR && tac-tail" Enter \; split-window -h \; send-keys "cd $TAC_DIR && tac-watch" Enter \; split-window -h \; send-keys "cd $TAC_DIR && tac-monitor" Enter \; select-layout even-horizontal \; attach-session -t tac'

# Attach to existing tmux session
alias tac-attach='tmux attach-session -t tac'

# Kill tmux session
alias tac-tmux-kill='tmux kill-session -t tac'

# ================================================================================
# SYSTEM RESOURCES
# ================================================================================

# System resource usage
alias tac-resources='echo "=== TAC-8 System Resources ===" && echo "CPU: $(top -bn1 | grep load | awk '\''{printf \"%.2f%%\", $(NF-2)}'\'')" && echo "Memory: $(free | grep Mem | awk '\''{printf \"%.2f%%\", $3/$2 * 100.0}'\'')" && echo "Disk: $(df $TAC_DIR | tail -1 | awk '\''{printf \"%s (%s used)\", $5, $3}'\'')"'

# ================================================================================
# HELP
# ================================================================================

# Show all TAC aliases
alias tac-help='echo "
🤖 TAC-8 MONITORING ALIASES

📊 MONITORING:
  tac-monitor       - Live dashboard (refreshes every 5s)
  tac-status        - Quick summary of all logs
  tac-view <log>    - View conversation (e.g., tac-view logs/gh-471.jsonl)
  tac-report        - Generate historical report
  tac-export <task> - Export task data (e.g., tac-export gh-471)

📋 LOGS:
  tac-tail          - Tail coordinator log
  tac-watch         - Watch coordinator log (refreshes every 2s)
  tac-logs          - List all conversation logs

🔧 PROCESS:
  tac-ps            - Check coordinator status
  tac-start         - Start coordinator
  tac-restart       - Restart coordinator
  tac-kill          - Stop coordinator

🏷️  GITHUB:
  tac-issues        - List issues with rpi-auto label
  tac-label-add     - Add rpi-auto to issue (usage: tac-label-add 471)
  tac-label-remove  - Remove rpi-auto from issue
  tac-pr            - View PR for task

🔍 SEARCH:
  tac-search        - Search conversations
  tac-tokens        - Token usage for task
  tac-timeline      - Activity timeline
  tac-task          - Detailed task report

📁 MANAGEMENT:
  tac               - Navigate to TAC directory
  tac-trees         - List worktrees
  tac-clean         - Clean up worktrees
  tac-tmux          - 3-column tmux monitoring
  tac-help          - Show this help

⚙️  SYSTEM:
  tac-resources     - System resource usage
"'

# Print welcome message when sourced
echo "🤖 TAC-8 monitoring aliases loaded! Try: tac-help"
