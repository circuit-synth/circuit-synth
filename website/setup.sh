#!/bin/bash
# Digital Ocean Setup for Circuit-Synth Website with Existing Website Preservation
# Run this on your Digital Ocean droplet that already has the circuit-synth repo

set -e

echo "🚀 Setting up Circuit-Synth website with auto-update timer..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y nginx git net-tools

# Ensure we're in the right directory (wherever the script is run from)
REPO_DIR=$(pwd)

# Preserve existing website if it exists
echo "💾 Preserving existing website..."
# Create website directory if it doesn't exist
mkdir -p website

if [ -f "/var/www/html/index.html" ]; then
    cp /var/www/html/index.html website/old_website.html
    cp /var/www/html/index.html website/index.html
    echo "✅ Existing website preserved as old_website.html and copied as index.html"
else
    echo "ℹ️  No existing website found in /var/www/html/"
fi

# Set up systemd service and timer directly (not from repo files)
echo "⏰ Setting up auto-update timer..."
cat > /etc/systemd/system/circuit-synth-update.service << EOF
[Unit]
Description=Update Circuit-Synth website from GitHub
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=$REPO_DIR
ExecStartPre=/usr/bin/git config --global --add safe.directory $REPO_DIR
ExecStart=/usr/bin/git pull origin main
ExecStartPost=/bin/bash -c 'if [ -f "website/index.html" ]; then cp website/index.html /var/www/html/; fi'
ExecStartPost=/bin/bash -c 'if [ -f "website/style.css" ]; then cp website/style.css /var/www/html/; fi'
ExecStartPost=/bin/bash -c 'chown www-data:www-data /var/www/html/index.html /var/www/html/style.css 2>/dev/null || true'
ExecStartPost=/usr/bin/systemctl reload nginx
StandardOutput=journal
StandardError=journal
EOF

cat > /etc/systemd/system/circuit-synth-update.timer << 'EOF'
[Unit]
Description=Update Circuit-Synth website every hour
Requires=circuit-synth-update.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Reload systemd and enable timer
sudo systemctl daemon-reload
sudo systemctl enable circuit-synth-update.timer
sudo systemctl start circuit-synth-update.timer

# Ensure /var/www/html exists and has proper permissions
echo "🔧 Setting up web directory permissions..."
sudo mkdir -p /var/www/html
sudo chown -R www-data:www-data /var/www/html
sudo chown -R www-data:www-data /var/www/circuit-synth

# Note: Nginx is already configured with SSL, so we skip nginx setup

# Test the timer works
echo "🧪 Testing auto-update service..."
sudo systemctl start circuit-synth-update.service
sudo systemctl status circuit-synth-update.service --no-pager -l

echo ""
echo "✅ Circuit-Synth website auto-update setup complete!"
echo ""
echo "📊 Status:"
echo "   Website: https://www.circuit-synth.com (SSL enabled)"
echo "   Auto-update: Every hour from GitHub"
echo "   Web root: /var/www/html/ (your existing site)"
echo "   Repo: $REPO_DIR (source files)"
echo ""
echo "💾 Your existing beautiful website has been:"
echo "   • Preserved as website/old_website.html in the repo"
echo "   • Copied as website/index.html for version control"
echo "   • Left running unchanged at /var/www/html/"
echo ""
echo "🔍 Useful commands:"
echo "   Check timer status: sudo systemctl status circuit-synth-update.timer"
echo "   View update logs: sudo journalctl -u circuit-synth-update.service -f"
echo "   Manual update: sudo systemctl start circuit-synth-update.service"
echo "   Next update: systemctl list-timers circuit-synth-update.timer"
echo ""
echo "🌐 How it works:"
echo "   1. Every hour, git pulls latest changes from GitHub"
echo "   2. If website/index.html exists, copies it to /var/www/html/"
echo "   3. If website/style.css exists, copies it to /var/www/html/"
echo "   4. Reloads nginx to serve updated content"
echo ""
echo "🚀 To update your website:"
echo "   1. Edit website/index.html in your GitHub repo"
echo "   2. Push changes to main branch"
echo "   3. Wait up to 1 hour for automatic update"
echo "   4. Or run: sudo systemctl start circuit-synth-update.service"