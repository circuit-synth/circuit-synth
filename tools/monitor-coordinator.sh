#!/bin/bash
# Simple coordinator monitoring script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$REPO_ROOT/coordinator.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          TAC-8 COORDINATOR MONITOR                            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo

# Check if coordinator is running
COORD_PID=$(ps aux | grep "python3 coordinator.py" | grep -v grep | awk '{print $2}' | head -1)

if [ -z "$COORD_PID" ]; then
    echo -e "${RED}❌ Coordinator NOT RUNNING${NC}"
    echo
    echo "To start: cd adws && nohup python3 coordinator.py > ../coordinator.log 2>&1 &"
    exit 1
else
    echo -e "${GREEN}✅ Coordinator RUNNING${NC}"
    echo -e "   PID: ${COORD_PID}"

    # Get uptime
    ETIME=$(ps -p $COORD_PID -o etime= | xargs)
    echo -e "   Uptime: ${ETIME}"

    # Get memory usage
    MEM=$(ps -p $COORD_PID -o %mem= | xargs)
    echo -e "   Memory: ${MEM}%"
fi

echo

# Count active worktrees
if [ -d "$REPO_ROOT/trees" ]; then
    WORKER_COUNT=$(ls "$REPO_ROOT/trees" 2>/dev/null | wc -l)
    echo -e "${YELLOW}📁 Active Worktrees: ${WORKER_COUNT}${NC}"
    if [ $WORKER_COUNT -gt 0 ]; then
        echo "   Latest:"
        ls -t "$REPO_ROOT/trees" 2>/dev/null | head -5 | sed 's/^/      - /'
    fi
else
    echo -e "${YELLOW}📁 No active worktrees${NC}"
fi

echo

# Show recent activity
if [ -f "$LOG_FILE" ]; then
    echo -e "${BLUE}📋 Recent Activity (last 15 lines):${NC}"
    echo "────────────────────────────────────────────────────────────────"
    tail -15 "$LOG_FILE" | sed 's/^/   /'
    echo "────────────────────────────────────────────────────────────────"
else
    echo -e "${RED}❌ No log file found: $LOG_FILE${NC}"
fi

echo

# Show open issues
echo -e "${BLUE}🎯 Open Issues (rpi-auto):${NC}"
if command -v gh &> /dev/null; then
    gh issue list --label rpi-auto --limit 5 2>/dev/null | head -5 | sed 's/^/   /'
else
    echo "   (gh CLI not available)"
fi

echo

# Show recent API usage
if [ -d "$REPO_ROOT/logs/api" ]; then
    API_COUNT=$(ls "$REPO_ROOT/logs/api"/*.json 2>/dev/null | wc -l)
    if [ $API_COUNT -gt 0 ]; then
        echo -e "${GREEN}💰 API Logs: ${API_COUNT} sessions${NC}"
        echo "   Latest:"
        ls -t "$REPO_ROOT/logs/api"/*.json 2>/dev/null | head -3 | xargs -I {} basename {} | sed 's/^/      - /'
    fi
fi

echo
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Monitoring commands:"
echo -e "  ${GREEN}tail -f coordinator.log${NC}       # Live log streaming"
echo -e "  ${GREEN}./tools/show-providers.py${NC}     # Provider status"
echo -e "  ${GREEN}./tools/show-routing.py${NC}       # Routing rules"
echo -e "  ${GREEN}./tools/api-usage-report.py${NC}   # API costs"
echo -e "  ${GREEN}kill $COORD_PID${NC}              # Stop coordinator"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
