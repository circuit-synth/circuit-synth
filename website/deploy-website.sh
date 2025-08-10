#!/bin/bash

# Circuit-Synth Website Deployment Script
# This script deploys the website from the repository to /var/www/html/
# with comprehensive error handling, logging, and backup functionality.

set -euo pipefail

# Configuration
REPO_DIR="/root/circuit-synth"
WEBSITE_DIR="/var/www/html"
BACKUP_DIR="/var/backups/circuit-synth-website"
LOG_FILE="/var/log/circuit-synth-deploy.log"
WEBSITE_BRANCH="main"
MAX_BACKUPS=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    log "SUCCESS" "$@"
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    log "WARNING" "$@"
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}[ERROR]${NC} $*"
}

# Error handler
error_exit() {
    log_error "Deployment failed: $1"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "This script must be run as root. Use: sudo $0"
    fi
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")" || error_exit "Failed to create log directory"
    
    # Ensure website directory exists
    mkdir -p "$WEBSITE_DIR" || error_exit "Failed to create website directory"
    
    log_success "Directories setup complete"
}

# Backup current website
backup_website() {
    log_info "Creating backup of current website..."
    
    local backup_name="backup-$(date '+%Y%m%d-%H%M%S')"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [[ -d "$WEBSITE_DIR" ]] && [[ "$(ls -A "$WEBSITE_DIR" 2>/dev/null)" ]]; then
        cp -r "$WEBSITE_DIR" "$backup_path" || error_exit "Failed to create backup"
        log_success "Backup created: $backup_path"
        
        # Clean up old backups (keep only last MAX_BACKUPS)
        local backup_count=$(ls -1 "$BACKUP_DIR" | wc -l)
        if [[ $backup_count -gt $MAX_BACKUPS ]]; then
            log_info "Cleaning up old backups (keeping last $MAX_BACKUPS)..."
            ls -1t "$BACKUP_DIR" | tail -n +$((MAX_BACKUPS + 1)) | while read -r old_backup; do
                rm -rf "$BACKUP_DIR/$old_backup"
                log_info "Removed old backup: $old_backup"
            done
        fi
    else
        log_warning "No existing website found to backup"
    fi
}

# Validate repository
validate_repository() {
    log_info "Validating repository..."
    
    if [[ ! -d "$REPO_DIR" ]]; then
        error_exit "Repository directory not found: $REPO_DIR"
    fi
    
    cd "$REPO_DIR" || error_exit "Failed to change to repository directory"
    
    if [[ ! -d ".git" ]]; then
        error_exit "Not a git repository: $REPO_DIR"
    fi
    
    log_success "Repository validation complete"
}

# Update repository
update_repository() {
    log_info "Updating repository..."
    
    cd "$REPO_DIR" || error_exit "Failed to change to repository directory"
    
    # Stash any local changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        log_warning "Local changes detected, stashing..."
        git stash push -m "Auto-stash before deployment $(date)" || error_exit "Failed to stash changes"
    fi
    
    # Checkout website branch
    log_info "Switching to $WEBSITE_BRANCH branch..."
    git checkout "$WEBSITE_BRANCH" || error_exit "Failed to checkout $WEBSITE_BRANCH branch"
    
    # Pull latest changes
    log_info "Pulling latest changes..."
    git pull origin "$WEBSITE_BRANCH" || error_exit "Failed to pull latest changes"
    
    log_success "Repository update complete"
}

# Validate website files
validate_website_files() {
    log_info "Validating website files..."
    
    local website_source="$REPO_DIR/website"
    
    if [[ ! -d "$website_source" ]]; then
        error_exit "Website source directory not found: $website_source"
    fi
    
    # Check for required files
    if [[ ! -f "$website_source/index.html" ]]; then
        error_exit "Required file not found: index.html"
    fi
    
    # Validate HTML if tidy is available
    if command -v tidy >/dev/null 2>&1; then
        log_info "Validating HTML syntax..."
        if ! tidy -q -e "$website_source/index.html" 2>/dev/null; then
            log_warning "HTML validation warnings detected (continuing anyway)"
        else
            log_success "HTML validation passed"
        fi
    else
        log_warning "HTML validator (tidy) not available, skipping syntax check"
    fi
    
    log_success "Website files validation complete"
}

# Deploy website files
deploy_files() {
    log_info "Deploying website files..."
    
    local website_source="$REPO_DIR/website"
    
    # Copy files to website directory
    cp -r "$website_source"/* "$WEBSITE_DIR/" || error_exit "Failed to copy website files"
    
    # Set proper ownership
    chown -R www-data:www-data "$WEBSITE_DIR" || error_exit "Failed to set file ownership"
    
    # Set proper permissions
    find "$WEBSITE_DIR" -type d -exec chmod 755 {} \; || error_exit "Failed to set directory permissions"
    find "$WEBSITE_DIR" -type f -exec chmod 644 {} \; || error_exit "Failed to set file permissions"
    
    log_success "Website files deployed successfully"
}

# Test and reload nginx
manage_nginx() {
    log_info "Testing nginx configuration..."
    
    # Test nginx configuration
    if ! nginx -t 2>/dev/null; then
        error_exit "Nginx configuration test failed"
    fi
    
    log_success "Nginx configuration test passed"
    
    # Reload nginx
    log_info "Reloading nginx..."
    if ! systemctl reload nginx; then
        error_exit "Failed to reload nginx"
    fi
    
    log_success "Nginx reloaded successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if nginx is running
    if ! systemctl is-active --quiet nginx; then
        error_exit "Nginx is not running"
    fi
    
    # Test HTTP response
    local http_status
    http_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || echo "000")
    
    if [[ "$http_status" == "200" ]]; then
        log_success "Website is responding correctly (HTTP $http_status)"
    else
        log_warning "Website HTTP response: $http_status (may be normal depending on configuration)"
    fi
    
    # Check if index.html exists and is readable
    if [[ -f "$WEBSITE_DIR/index.html" ]] && [[ -r "$WEBSITE_DIR/index.html" ]]; then
        log_success "Website files are accessible"
    else
        error_exit "Website files are not accessible"
    fi
    
    log_success "Deployment verification complete"
}

# Main deployment function
main() {
    log_info "Starting Circuit-Synth website deployment..."
    log_info "Timestamp: $(date)"
    log_info "User: $(whoami)"
    log_info "Repository: $REPO_DIR"
    log_info "Website directory: $WEBSITE_DIR"
    
    # Run deployment steps
    check_root
    setup_directories
    backup_website
    validate_repository
    update_repository
    validate_website_files
    deploy_files
    manage_nginx
    verify_deployment
    
    log_success "🎉 Website deployment completed successfully!"
    log_info "Website is now live and serving updated content"
    log_info "Deployment log: $LOG_FILE"
    
    # Show deployment summary
    echo
    echo -e "${GREEN}=== DEPLOYMENT SUMMARY ===${NC}"
    echo -e "${BLUE}Repository:${NC} $REPO_DIR"
    echo -e "${BLUE}Website:${NC} $WEBSITE_DIR"
    echo -e "${BLUE}Backup:${NC} $BACKUP_DIR"
    echo -e "${BLUE}Log:${NC} $LOG_FILE"
    echo -e "${BLUE}Status:${NC} ${GREEN}SUCCESS${NC}"
    echo
}

# Run main function
main "$@"