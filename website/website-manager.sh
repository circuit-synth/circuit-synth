#!/bin/bash

# Circuit-Synth Website Management Script
# Easy-to-use interface for common deployment operations

set -euo pipefail

# Configuration
REPO_DIR="/root/circuit-synth"
WEBSITE_DIR="/var/www/html"
BACKUP_DIR="/var/backups/circuit-synth-website"
LOG_FILE="/var/log/circuit-synth-deploy.log"
DEPLOY_SCRIPT="$REPO_DIR/website/deploy-website.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

print_header() {
    echo -e "${CYAN}=== $* ===${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root. Use: sudo $0"
        exit 1
    fi
}

# Show help
show_help() {
    echo -e "${CYAN}Circuit-Synth Website Manager${NC}"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo -e "  ${GREEN}deploy${NC}                    Deploy website from repository"
    echo -e "  ${GREEN}status${NC}                    Show deployment status"
    echo -e "  ${GREEN}logs${NC}                      Show recent deployment logs"
    echo -e "  ${GREEN}backup${NC}                    List available backups"
    echo -e "  ${GREEN}restore${NC} <backup-name>     Restore from backup"
    echo -e "  ${GREEN}test${NC}                      Test website accessibility"
    echo -e "  ${GREEN}help${NC}                      Show this help message"
    echo
    echo "Examples:"
    echo "  sudo $0 deploy"
    echo "  sudo $0 status"
    echo "  sudo $0 restore backup-20250201-143022"
    echo
}

# Deploy website
deploy_website() {
    print_header "DEPLOYING WEBSITE"
    
    if [[ ! -f "$DEPLOY_SCRIPT" ]]; then
        print_error "Deployment script not found: $DEPLOY_SCRIPT"
        exit 1
    fi
    
    # Make script executable
    chmod +x "$DEPLOY_SCRIPT"
    
    # Run deployment
    "$DEPLOY_SCRIPT"
}

# Show deployment status
show_status() {
    print_header "DEPLOYMENT STATUS"
    
    # Check if website directory exists
    if [[ -d "$WEBSITE_DIR" ]]; then
        print_success "Website directory exists: $WEBSITE_DIR"
        
        # Count files
        local file_count=$(find "$WEBSITE_DIR" -type f | wc -l)
        print_info "Files in website directory: $file_count"
        
        # Check index.html
        if [[ -f "$WEBSITE_DIR/index.html" ]]; then
            print_success "index.html found"
            local index_size=$(stat -f%z "$WEBSITE_DIR/index.html" 2>/dev/null || stat -c%s "$WEBSITE_DIR/index.html" 2>/dev/null || echo "unknown")
            print_info "index.html size: $index_size bytes"
        else
            print_warning "index.html not found"
        fi
    else
        print_warning "Website directory does not exist: $WEBSITE_DIR"
    fi
    
    # Check nginx status
    if systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_error "Nginx is not running"
    fi
    
    # Check repository status
    if [[ -d "$REPO_DIR" ]]; then
        print_success "Repository directory exists: $REPO_DIR"
        
        cd "$REPO_DIR" || exit 1
        if [[ -d ".git" ]]; then
            print_success "Git repository found"
            
            # Show current branch
            local current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
            print_info "Current branch: $current_branch"
            
            # Show last commit
            local last_commit=$(git log -1 --format="%h - %s (%cr)" 2>/dev/null || echo "unknown")
            print_info "Last commit: $last_commit"
        else
            print_warning "Not a git repository"
        fi
    else
        print_error "Repository directory does not exist: $REPO_DIR"
    fi
    
    # Show last deployment
    if [[ -f "$LOG_FILE" ]]; then
        print_info "Last deployment log entry:"
        tail -1 "$LOG_FILE" | sed 's/^/  /'
    else
        print_warning "No deployment log found"
    fi
}

# Show recent logs
show_logs() {
    print_header "RECENT DEPLOYMENT LOGS"
    
    if [[ -f "$LOG_FILE" ]]; then
        print_info "Showing last 20 lines from $LOG_FILE:"
        echo
        tail -20 "$LOG_FILE"
    else
        print_warning "No deployment log found: $LOG_FILE"
    fi
}

# List backups
list_backups() {
    print_header "AVAILABLE BACKUPS"
    
    if [[ -d "$BACKUP_DIR" ]]; then
        local backups=($(ls -1t "$BACKUP_DIR" 2>/dev/null || true))
        
        if [[ ${#backups[@]} -eq 0 ]]; then
            print_warning "No backups found in $BACKUP_DIR"
        else
            print_info "Found ${#backups[@]} backup(s):"
            echo
            for backup in "${backups[@]}"; do
                local backup_path="$BACKUP_DIR/$backup"
                local backup_date=$(stat -f%Sm -t"%Y-%m-%d %H:%M:%S" "$backup_path" 2>/dev/null || stat -c%y "$backup_path" 2>/dev/null | cut -d. -f1 || echo "unknown")
                local backup_size=$(du -sh "$backup_path" 2>/dev/null | cut -f1 || echo "unknown")
                echo -e "  ${GREEN}$backup${NC} (${backup_date}, ${backup_size})"
            done
            echo
            print_info "To restore a backup, use: sudo $0 restore <backup-name>"
        fi
    else
        print_warning "Backup directory does not exist: $BACKUP_DIR"
    fi
}

# Restore from backup
restore_backup() {
    local backup_name="$1"
    
    if [[ -z "$backup_name" ]]; then
        print_error "Backup name required. Use: sudo $0 restore <backup-name>"
        print_info "Available backups:"
        list_backups
        exit 1
    fi
    
    print_header "RESTORING FROM BACKUP"
    
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [[ ! -d "$backup_path" ]]; then
        print_error "Backup not found: $backup_path"
        print_info "Available backups:"
        list_backups
        exit 1
    fi
    
    print_info "Restoring from backup: $backup_name"
    print_warning "This will overwrite the current website!"
    
    # Create a backup of current state before restore
    local restore_backup_name="pre-restore-$(date '+%Y%m%d-%H%M%S')"
    local restore_backup_path="$BACKUP_DIR/$restore_backup_name"
    
    if [[ -d "$WEBSITE_DIR" ]]; then
        print_info "Creating backup of current state: $restore_backup_name"
        cp -r "$WEBSITE_DIR" "$restore_backup_path" || {
            print_error "Failed to create pre-restore backup"
            exit 1
        }
    fi
    
    # Restore from backup
    print_info "Copying files from backup..."
    rm -rf "$WEBSITE_DIR"
    cp -r "$backup_path" "$WEBSITE_DIR" || {
        print_error "Failed to restore from backup"
        exit 1
    }
    
    # Set proper permissions
    print_info "Setting file permissions..."
    chown -R www-data:www-data "$WEBSITE_DIR" || print_warning "Failed to set ownership"
    find "$WEBSITE_DIR" -type d -exec chmod 755 {} \; || print_warning "Failed to set directory permissions"
    find "$WEBSITE_DIR" -type f -exec chmod 644 {} \; || print_warning "Failed to set file permissions"
    
    # Reload nginx
    print_info "Reloading nginx..."
    if systemctl reload nginx; then
        print_success "Nginx reloaded successfully"
    else
        print_warning "Failed to reload nginx"
    fi
    
    print_success "Restore completed successfully!"
    print_info "Restored from: $backup_name"
    print_info "Pre-restore backup created: $restore_backup_name"
}

# Test website accessibility
test_website() {
    print_header "TESTING WEBSITE ACCESSIBILITY"
    
    # Test nginx status
    if systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_error "Nginx is not running"
        return 1
    fi
    
    # Test HTTP response
    print_info "Testing HTTP response..."
    local http_status
    http_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
    
    case "$http_status" in
        200)
            print_success "HTTP test passed (status: $http_status)"
            ;;
        000)
            print_error "HTTP test failed (connection error)"
            return 1
            ;;
        *)
            print_warning "HTTP test returned status: $http_status"
            ;;
    esac
    
    # Test file accessibility
    if [[ -f "$WEBSITE_DIR/index.html" ]] && [[ -r "$WEBSITE_DIR/index.html" ]]; then
        print_success "Website files are accessible"
    else
        print_error "Website files are not accessible"
        return 1
    fi
    
    # Test content
    if curl -s http://localhost/ | grep -q "Circuit-Synth" 2>/dev/null; then
        print_success "Website content appears to be loading correctly"
    else
        print_warning "Could not verify website content"
    fi
    
    print_success "Website accessibility test completed"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        deploy)
            check_root
            deploy_website
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        backup)
            list_backups
            ;;
        restore)
            check_root
            restore_backup "${2:-}"
            ;;
        test)
            test_website
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"