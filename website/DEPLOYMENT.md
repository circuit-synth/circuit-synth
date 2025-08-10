# Circuit-Synth Website Deployment Guide

This document provides comprehensive instructions for deploying the Circuit-Synth website from the repository's `main` branch to a production server.

## 📋 Overview

The deployment system consists of:
- **Main Branch**: Contains the production website files in the `website/` directory (`index.html`, `style.css`, etc.)
- **Deployment Script**: Automated deployment with error handling and logging
- **Management Script**: Easy-to-use commands for deployment operations
- **Backup System**: Automatic backups before each deployment

## 🚀 Quick Deployment

### Prerequisites
- Server with nginx installed and configured
- Git repository cloned to `/root/circuit-synth/`
- Root access to the server
- Main branch checked out

### One-Command Deployment
```bash
# SSH into your server
ssh root@your-server-ip

# Navigate to repository
cd /root/circuit-synth

# Make scripts executable and run deployment
chmod +x website/deploy-website.sh website/website-manager.sh
sudo ./website/deploy-website.sh
```

## 📜 Deployment Scripts

### 1. Main Deployment Script (`deploy-website.sh`)

**Purpose**: Comprehensive deployment with full error handling, logging, and backup.

**Features**:
- ✅ Automatic backup of current website
- ✅ Git repository validation and updates
- ✅ Website file validation
- ✅ Proper file permissions and ownership
- ✅ Nginx configuration testing and reload
- ✅ Deployment verification
- ✅ Comprehensive logging
- ✅ Error handling and rollback capability

**Usage**:
```bash
sudo ./website/deploy-website.sh
```

### 2. Management Script (`website-manager.sh`)

**Purpose**: Easy-to-use interface for common deployment operations.

**Commands**:
```bash
sudo ./website/website-manager.sh deploy      # Deploy website
sudo ./website/website-manager.sh status      # Show deployment status
sudo ./website/website-manager.sh logs        # Show recent logs
sudo ./website/website-manager.sh backup      # List available backups
sudo ./website/website-manager.sh restore <backup-name>  # Restore from backup
sudo ./website/website-manager.sh test        # Test website accessibility
sudo ./website/website-manager.sh help        # Show help
```

## 🔄 Deployment Process

The deployment script follows this process:

1. **Pre-deployment Checks**
   - Verify root permissions
   - Check repository accessibility
   - Validate git repository state

2. **Backup Current Website**
   - Create timestamped backup in `/var/backups/circuit-synth-website/`
   - Maintain last 10 backups automatically

3. **Repository Update**
   - Switch to `main` branch
   - Stash any local changes
   - Pull latest changes from origin

4. **File Validation**
   - Check for required files (`index.html`)
   - Validate HTML syntax (if `tidy` is available)
   - Verify file integrity

5. **Deployment**
   - Copy website files to `/var/www/html/`
   - Set proper ownership (`www-data:www-data`)
   - Set correct permissions (755 for directories, 644 for files)

6. **Service Management**
   - Test nginx configuration
   - Reload nginx service
   - Verify website accessibility

## 📁 File Locations

### Server Paths
- **Website Files**: `/var/www/html/`
- **Repository**: `/root/circuit-synth/`
- **Logs**: `/var/log/circuit-synth-deploy.log`
- **Backups**: `/var/backups/circuit-synth-website/`

### Repository Files (main branch)
- **Main Page**: `website/index.html`
- **Styles**: `website/style.css`
- **Deployment Script**: `website/deploy-website.sh`
- **Management Script**: `website/website-manager.sh`

## 🧪 Testing

### Manual Testing
```bash
# Test website accessibility
sudo ./website/website-manager.sh test

# Manual HTTP test
curl -I http://localhost
curl -I https://localhost  # if HTTPS configured
```

## 🚨 Troubleshooting

### Common Issues

**1. Permission Denied**
```bash
# Ensure scripts are executable
chmod +x website/deploy-website.sh website/website-manager.sh

# Run with sudo
sudo ./website/deploy-website.sh
```

**2. Git Repository Issues**
```bash
# Check repository status
cd /root/circuit-synth
git status

# Reset if needed
git stash
git checkout main
git pull origin main
```

**3. Nginx Issues**
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx status
sudo systemctl status nginx

# Restart nginx if needed
sudo systemctl restart nginx
```

---

**Last Updated**: 2025-02-01
**Version**: 1.0