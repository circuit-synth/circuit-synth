#!/bin/bash
#
# Raspberry Pi Cleanup Script
# Removes all non-essential services to dedicate Pi to TAC-8 coordinator
#
# WARNING: This will PERMANENTLY REMOVE Docker containers and services
# Review carefully before running!
#

set -e

echo "=========================================="
echo "Raspberry Pi Cleanup for TAC-8"
echo "=========================================="
echo ""
echo "This will remove:"
echo "  - Docker and all containers (Plex, Sonarr, etc.)"
echo "  - CUPS (printing service)"
echo "  - Avahi (mDNS)"
echo "  - Snapd"
echo "  - GNOME Remote Desktop"
echo ""
echo "This will KEEP:"
echo "  - SSH"
echo "  - Network services"
echo "  - Circuit-Synth TAC coordinator"
echo ""
read -p "Are you SURE you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 1: Stopping and removing Docker"
echo "=========================================="

# Stop all Docker containers
echo "Stopping all Docker containers..."
docker stop $(docker ps -aq) 2>/dev/null || true

# Remove all Docker containers
echo "Removing all Docker containers..."
docker rm $(docker ps -aq) 2>/dev/null || true

# Stop Docker service
echo "Stopping Docker service..."
sudo systemctl stop docker.service containerd.service

# Disable Docker from starting on boot
echo "Disabling Docker service..."
sudo systemctl disable docker.service containerd.service

# Remove Docker and containerd
echo "Uninstalling Docker..."
sudo apt-get remove -y docker docker-engine docker.io containerd runc docker-compose 2>/dev/null || true

# Clean up Docker data
echo "Removing Docker data..."
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd

echo "✓ Docker removed"

echo ""
echo "=========================================="
echo "Step 2: Removing CUPS (printing)"
echo "=========================================="

sudo systemctl stop cups cups-browsed 2>/dev/null || true
sudo systemctl disable cups cups-browsed 2>/dev/null || true
sudo apt-get remove -y cups cups-browsed cups-daemon 2>/dev/null || true

echo "✓ CUPS removed"

echo ""
echo "=========================================="
echo "Step 3: Removing Avahi (mDNS)"
echo "=========================================="

sudo systemctl stop avahi-daemon 2>/dev/null || true
sudo systemctl disable avahi-daemon 2>/dev/null || true
sudo apt-get remove -y avahi-daemon 2>/dev/null || true

echo "✓ Avahi removed"

echo ""
echo "=========================================="
echo "Step 4: Removing Snapd"
echo "=========================================="

sudo systemctl stop snapd 2>/dev/null || true
sudo systemctl disable snapd 2>/dev/null || true
sudo apt-get remove -y snapd 2>/dev/null || true
sudo rm -rf /snap /var/snap /var/lib/snapd

echo "✓ Snapd removed"

echo ""
echo "=========================================="
echo "Step 5: Removing GNOME Remote Desktop"
echo "=========================================="

sudo systemctl stop gnome-remote-desktop 2>/dev/null || true
sudo systemctl disable gnome-remote-desktop 2>/dev/null || true

echo "✓ GNOME Remote Desktop disabled"

echo ""
echo "=========================================="
echo "Step 6: Cleaning up packages"
echo "=========================================="

sudo apt-get autoremove -y
sudo apt-get autoclean

echo "✓ Package cleanup complete"

echo ""
echo "=========================================="
echo "Step 7: Freeing up disk space"
echo "=========================================="

# Clean apt cache
sudo apt-get clean

# Clean journal logs older than 7 days
sudo journalctl --vacuum-time=7d

# Show disk usage
echo ""
echo "Disk usage after cleanup:"
df -h / | grep -v Filesystem

echo ""
echo "=========================================="
echo "✅ Cleanup Complete!"
echo "=========================================="
echo ""
echo "Services still running:"
sudo systemctl list-units --type=service --state=running | grep -v -E 'ssh|systemd|dbus|user@|network' | head -20

echo ""
echo "Listening ports (should only be SSH on :22):"
sudo netstat -tulpn | grep LISTEN | grep -v ':22'

echo ""
echo "Reboot recommended: sudo reboot"
