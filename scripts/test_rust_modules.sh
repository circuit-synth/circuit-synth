#!/bin/bash
# scripts/test_rust_modules.sh - Automated Rust module testing for CI/CD
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUST_MODULES_DIR="$PROJECT_ROOT/rust_modules"
TEST_RESULTS_FILE="$PROJECT_ROOT/rust_test_results.json"
VERBOSE=${VERBOSE:-false}
FAIL_FAST=${FAIL_FAST:-false}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Initialize test results
init_results() {
    cat > "$TEST_RESULTS_FILE" << EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "modules": {},
  "summary": {
    "total_modules": 0,
    "tested_modules": 0,
    "passing_modules": 0,
    "failing_modules": 0,
    "skipped_modules": 0
  }
}
EOF
}

# Update test results
update_results() {
    local module_name="$1"
    local status="$2"
    local tests_passed="$3"
    local tests_failed="$4"
    local error_message="$5"
    
    # Use jq to update JSON (install jq if not available)
    if command -v jq >/dev/null 2>&1; then
        local temp_file=$(mktemp)
        jq --arg module "$module_name" \
           --arg status "$status" \
           --argjson passed "$tests_passed" \
           --argjson failed "$tests_failed" \
           --arg error "$error_message" \
           '.modules[$module] = {
             "status": $status,
             "tests_passed": $passed,
             "tests_failed": $failed,
             "error_message": $error
           }' "$TEST_RESULTS_FILE" > "$temp_file" && mv "$temp_file" "$TEST_RESULTS_FILE"
    fi
}

# Test individual Rust module
test_rust_module() {
    local module_path="$1"
    local module_name=$(basename "$module_path")
    
    log_info "Testing module: $module_name"
    
    if [ ! -d "$module_path" ]; then
        log_warning "Module directory not found: $module_path"
        update_results "$module_name" "skipped" 0 0 "Directory not found"
        return 0
    fi
    
    if [ ! -f "$module_path/Cargo.toml" ]; then
        log_warning "No Cargo.toml found in $module_path"
        update_results "$module_name" "skipped" 0 0 "No Cargo.toml"
        return 0
    fi
    
    cd "$module_path"
    
    # Run Rust unit tests without Python bindings
    log_info "  Running unit tests for $module_name..."
    
    local test_output
    local test_exit_code
    
    if [ "$VERBOSE" = "true" ]; then
        test_output=$(cargo test --lib --no-default-features 2>&1)
        test_exit_code=$?
    else
        test_output=$(cargo test --lib --no-default-features 2>&1)
        test_exit_code=$?
    fi
    
    # Parse test results
    local tests_passed=0
    local tests_failed=0
    
    if echo "$test_output" | grep -q "test result:"; then
        # Extract passed and failed counts using grep and cut (more reliable)
        local result_line=$(echo "$test_output" | grep "test result:" | tail -1)
        
        # Extract passed count: "X passed"
        tests_passed=$(echo "$result_line" | grep -o '[0-9]\+ passed' | cut -d' ' -f1 || echo "0")
        
        # Extract failed count: "Y failed"  
        tests_failed=$(echo "$result_line" | grep -o '[0-9]\+ failed' | cut -d' ' -f1 || echo "0")
        
        # Ensure we have numeric values
        tests_passed=${tests_passed:-0}
        tests_failed=${tests_failed:-0}
    fi
    
    if [ $test_exit_code -eq 0 ]; then
        log_success "  ✅ $module_name: $tests_passed tests passed"
        update_results "$module_name" "passed" "$tests_passed" "$tests_failed" ""
        return 0
    else
        log_error "  ❌ $module_name: $tests_passed passed, $tests_failed failed"
        if [ "$VERBOSE" = "true" ]; then
            echo "$test_output"
        fi
        update_results "$module_name" "failed" "$tests_passed" "$tests_failed" "Test failures"
        
        if [ "$FAIL_FAST" = "true" ]; then
            log_error "FAIL_FAST enabled, stopping on first failure"
            exit 1
        fi
        return 1
    fi
}

# Test Python-Rust integration for modules with Python bindings
test_python_integration() {
    local module_path="$1"
    local module_name=$(basename "$module_path")
    
    if [ ! -f "$module_path/pyproject.toml" ]; then
        return 0  # Skip if no Python bindings
    fi
    
    log_info "  Testing Python integration for $module_name..."
    
    cd "$module_path"
    
    # Try to build with maturin
    if command -v maturin >/dev/null 2>&1; then
        if maturin develop --quiet 2>/dev/null; then
            # Test import
            cd "$PROJECT_ROOT"
            if uv run python -c "import $module_name; print('✅ Import successful')" 2>/dev/null; then
                log_success "  ✅ Python integration working for $module_name"
                return 0
            else
                log_warning "  ⚠️  Python import failed for $module_name"
                return 1
            fi
        else
            log_warning "  ⚠️  maturin build failed for $module_name"
            return 1
        fi
    else
        log_warning "  ⚠️  maturin not available, skipping Python integration test"
        return 0
    fi
}

# Discover Rust modules
discover_modules() {
    find "$RUST_MODULES_DIR" -maxdepth 1 -type d -name "rust_*" | sort
}

# Generate summary report
generate_summary() {
    log_info "Generating test summary..."
    
    if command -v jq >/dev/null 2>&1 && [ -f "$TEST_RESULTS_FILE" ]; then
        local total=$(jq '.modules | length' "$TEST_RESULTS_FILE")
        local passed=$(jq '[.modules[] | select(.status == "passed")] | length' "$TEST_RESULTS_FILE")
        local failed=$(jq '[.modules[] | select(.status == "failed")] | length' "$TEST_RESULTS_FILE")
        local skipped=$(jq '[.modules[] | select(.status == "skipped")] | length' "$TEST_RESULTS_FILE")
        
        # Update summary in JSON
        local temp_file=$(mktemp)
        jq --argjson total "$total" \
           --argjson passed "$passed" \
           --argjson failed "$failed" \
           --argjson skipped "$skipped" \
           '.summary = {
             "total_modules": $total,
             "tested_modules": ($total - $skipped),
             "passing_modules": $passed,
             "failing_modules": $failed,
             "skipped_modules": $skipped
           }' "$TEST_RESULTS_FILE" > "$temp_file" && mv "$temp_file" "$TEST_RESULTS_FILE"
        
        echo ""
        log_info "📊 Rust Testing Summary:"
        echo "  📦 Total modules: $total"
        echo "  ✅ Passing: $passed"
        echo "  ❌ Failing: $failed" 
        echo "  ⏭️  Skipped: $skipped"
        echo ""
        
        if [ "$failed" -gt 0 ]; then
            log_error "Some Rust modules have test failures"
            if command -v jq >/dev/null 2>&1; then
                echo "Failed modules:"
                jq -r '.modules | to_entries[] | select(.value.status == "failed") | "  - \(.key): \(.value.error_message)"' "$TEST_RESULTS_FILE"
            fi
            return 1
        else
            log_success "All tested Rust modules passing!"
            return 0
        fi
    else
        log_warning "Could not generate detailed summary (jq not available or no results file)"
        return 0
    fi
}

# Main function
main() {
    log_info "🦀 Starting automated Rust module testing..."
    echo "Working directory: $PROJECT_ROOT"
    echo "Rust modules directory: $RUST_MODULES_DIR"
    echo ""
    
    # Check dependencies
    if ! command -v cargo >/dev/null 2>&1; then
        log_error "cargo not found. Please install Rust toolchain."
        exit 1
    fi
    
    # Initialize results
    init_results
    
    # Discover and test modules
    local modules
    modules=$(discover_modules)
    
    if [ -z "$modules" ]; then
        log_warning "No Rust modules found in $RUST_MODULES_DIR"
        exit 0
    fi
    
    local failed_count=0
    local total_count=0
    
    for module_path in $modules; do
        ((total_count++))
        if ! test_rust_module "$module_path"; then
            ((failed_count++))
        fi
        
        # Test Python integration if available
        test_python_integration "$module_path" || true
        
        echo ""  # Add spacing between modules
    done
    
    # Generate summary
    if ! generate_summary; then
        exit 1
    fi
    
    log_info "Rust testing completed. Results saved to: $TEST_RESULTS_FILE"
    
    if [ "$failed_count" -gt 0 ]; then
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fail-fast)
            FAIL_FAST=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose     Show detailed test output"
            echo "  -f, --fail-fast   Stop on first test failure"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  VERBOSE=true      Enable verbose output"
            echo "  FAIL_FAST=true    Enable fail-fast mode"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main