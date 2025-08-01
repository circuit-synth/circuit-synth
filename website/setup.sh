#!/bin/bash
# Simple Digital Ocean Setup for Circuit-Synth Website
# Run this on your Digital Ocean droplet

set -e

echo "🚀 Setting up Circuit-Synth website with auto-update timer..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y nginx git

# Create web directory
sudo mkdir -p /var/www/circuit-synth
cd /var/www/circuit-synth

# Clone repository (public repo, no auth needed)
echo "📥 Cloning Circuit-Synth repository..."
sudo git clone https://github.com/circuit-synth/circuit-synth.git .

# Copy website files to web root
echo "🌐 Setting up website files..."
sudo cp -r website/*.html website/*.css /var/www/circuit-synth/ 2>/dev/null || echo "No HTML/CSS files found"

# Set up systemd service and timer
echo "⏰ Setting up auto-update timer..."
sudo cp website/circuit-synth-update.service /etc/systemd/system/
sudo cp website/circuit-synth-update.timer /etc/systemd/system/

# Reload systemd and enable timer
sudo systemctl daemon-reload
sudo systemctl enable circuit-synth-update.timer
sudo systemctl start circuit-synth-update.timer

# Set up Nginx configuration
echo "🔧 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/circuit-synth > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    root /var/www/circuit-synth;
    index index.html index.htm;

    location / {
        try_files \$uri \$uri/ =404;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/circuit-synth /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Start and enable nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Set proper permissions
sudo chown -R www-data:www-data /var/www/circuit-synth

# Test the timer works
echo "🧪 Testing auto-update service..."
sudo systemctl start circuit-synth-update.service
sudo systemctl status circuit-synth-update.service --no-pager -l

echo ""
echo "✅ Circuit-Synth website setup complete!"
echo ""
echo "📊 Status:"
echo "   Website: http://$(curl -s ipinfo.io/ip 2>/dev/null || echo 'your-droplet-ip')"
echo "   Auto-update: Every hour"
echo ""
echo "🔍 Useful commands:"
echo "   Check timer status: sudo systemctl status circuit-synth-update.timer"
echo "   View update logs: sudo journalctl -u circuit-synth-update.service -f"
echo "   Manual update: sudo systemctl start circuit-synth-update.service"
echo "   Next update: systemctl list-timers circuit-synth-update.timer"
echo ""
echo "🌐 Your website will automatically update every hour from GitHub!"
echo "   Just push changes to the main branch and wait up to 1 hour."