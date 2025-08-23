#!/bin/bash
# Circuit-synth Environment Cleanup Script
# Ensures local submodule is used instead of pip-installed packages

set -e

echo "🧹 Circuit-synth Environment Cleanup"
echo "=================================="

# Function to detect virtual environment
detect_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "📦 Detected virtual environment: $VIRTUAL_ENV"
        return 0
    elif [[ -d ".venv" ]]; then
        echo "📦 Detected local .venv directory"
        return 0
    else
        echo "⚠️  No virtual environment detected"
        return 1
    fi
}

# Function to remove pip-installed circuit-synth
remove_pip_packages() {
    echo "🗑️  Removing pip-installed circuit-synth packages..."
    
    # Find Python site-packages directories
    SITE_PACKAGES=$(python -c "import site; print('\n'.join(site.getsitepackages() + [site.getusersitepackages()]))" 2>/dev/null || true)
    
    # Also check current environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        SITE_PACKAGES="$SITE_PACKAGES
$VIRTUAL_ENV/lib/python*/site-packages"
    fi
    
    # Look for .venv in current directory
    if [[ -d ".venv" ]]; then
        SITE_PACKAGES="$SITE_PACKAGES
.venv/lib/python*/site-packages"
    fi
    
    # Remove circuit-synth packages from all locations
    echo "$SITE_PACKAGES" | while read -r path; do
        if [[ -d "$path" ]]; then
            echo "🔍 Checking: $path"
            find "$path" -maxdepth 1 -name "*circuit*synth*" -type d 2>/dev/null | while read -r pkg; do
                echo "   🗑️  Removing: $pkg"
                rm -rf "$pkg"
            done
        fi
    done
}

# Function to clear Python cache
clear_python_cache() {
    echo "🧹 Clearing Python cache files..."
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    echo "   ✅ Python cache cleared"
}

# Function to verify environment
verify_environment() {
    echo "🔍 Verifying environment..."
    
    # Check if we can import from local paths
    if python -c "import sys; sys.path.insert(0, './src'); import circuit_synth; print(f'✅ Using local: {circuit_synth.__file__}')" 2>/dev/null; then
        echo "   ✅ Local submodule is accessible"
    else
        echo "   ❌ Cannot import from local submodule"
        return 1
    fi
    
    # Check submodule status
    if [[ -d "submodules/circuit-synth/.git" ]]; then
        cd submodules/circuit-synth
        COMMIT=$(git log --oneline -1)
        echo "   📍 Submodule at: $COMMIT"
        cd - > /dev/null
    else
        echo "   ⚠️  Submodule not properly initialized"
    fi
}

# Main execution
main() {
    echo "Starting cleanup process..."
    
    # Step 1: Detect environment
    if detect_venv; then
        echo "✅ Virtual environment detected"
    else
        echo "⚠️  Consider using a virtual environment"
    fi
    
    # Step 2: Remove conflicting packages
    remove_pip_packages
    
    # Step 3: Clear caches
    clear_python_cache
    
    # Step 4: Verify setup
    if verify_environment; then
        echo ""
        echo "🎉 Environment cleanup complete!"
        echo "✅ Circuit-synth will now use the local submodule"
    else
        echo ""
        echo "❌ Environment setup failed"
        echo "🔧 Try: git submodule update --init --recursive"
        exit 1
    fi
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi