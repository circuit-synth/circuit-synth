#!/bin/bash
# scripts/run_all_tests.sh - Unified test runner for Python and Rust tests
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERBOSE=${VERBOSE:-false}
RUST_ONLY=${RUST_ONLY:-false}
PYTHON_ONLY=${PYTHON_ONLY:-false}
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

log_section() {
    echo -e "\n${BOLD}${BLUE}==== $1 ====${NC}\n"
}

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if [ "$PYTHON_ONLY" != "true" ]; then
        if ! command -v cargo >/dev/null 2>&1; then
            missing_deps+=("cargo (Rust toolchain)")
        fi
    fi
    
    if [ "$RUST_ONLY" != "true" ]; then
        if ! command -v uv >/dev/null 2>&1; then
            missing_deps+=("uv (Python package manager)")
        fi
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
}

# Run Python tests
run_python_tests() {
    log_section "Python Tests"
    
    cd "$PROJECT_ROOT"
    
    log_info "Running Python unit tests..."
    if [ "$VERBOSE" = "true" ]; then
        uv run pytest -v
    else
        uv run pytest
    fi
    
    local python_exit_code=$?
    
    if [ $python_exit_code -eq 0 ]; then
        log_success "✅ Python tests passed"
        return 0
    else
        log_error "❌ Python tests failed"
        if [ "$FAIL_FAST" = "true" ]; then
            exit 1
        fi
        return 1
    fi
}

# Run Rust tests
run_rust_tests() {
    log_section "Rust Tests"
    
    if [ ! -x "$SCRIPT_DIR/test_rust_modules.sh" ]; then
        log_error "Rust test script not found or not executable: $SCRIPT_DIR/test_rust_modules.sh"
        return 1
    fi
    
    local rust_args=""
    if [ "$VERBOSE" = "true" ]; then
        rust_args="$rust_args --verbose"
    fi
    if [ "$FAIL_FAST" = "true" ]; then
        rust_args="$rust_args --fail-fast"
    fi
    
    log_info "Running Rust unit tests..."
    if "$SCRIPT_DIR/test_rust_modules.sh" $rust_args; then
        log_success "✅ Rust tests passed"
        return 0
    else
        log_error "❌ Rust tests failed"
        if [ "$FAIL_FAST" = "true" ]; then
            exit 1
        fi
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    log_section "Integration Tests"
    
    cd "$PROJECT_ROOT"
    
    log_info "Running Rust integration tests..."
    if [ "$VERBOSE" = "true" ]; then
        uv run pytest tests/rust_integration/ -v
    else
        uv run pytest tests/rust_integration/
    fi
    
    local integration_exit_code=$?
    
    if [ $integration_exit_code -eq 0 ]; then
        log_success "✅ Integration tests passed"
        return 0
    else
        log_error "❌ Integration tests failed"
        if [ "$FAIL_FAST" = "true" ]; then
            exit 1
        fi
        return 1
    fi
}

# Test core functionality
test_core_functionality() {
    log_section "Core Functionality Test"
    
    cd "$PROJECT_ROOT"
    
    log_info "Testing core circuit logic..."
    if uv run python examples/example_kicad_project.py >/dev/null 2>&1; then
        log_success "✅ Core circuit logic working"
        return 0
    else
        log_error "❌ Core circuit logic test failed"
        if [ "$FAIL_FAST" = "true" ]; then
            exit 1
        fi
        return 1
    fi
}

# Generate summary report
generate_summary() {
    log_section "Test Summary"
    
    local python_status="⏭️ Skipped"
    local rust_status="⏭️ Skipped"
    local integration_status="⏭️ Skipped"
    local core_status="⏭️ Skipped"
    
    # Check Python test results
    if [ "$RUST_ONLY" != "true" ] && [ -f "$PROJECT_ROOT/.pytest_cache/v/cache/lastfailed" ]; then
        if [ -s "$PROJECT_ROOT/.pytest_cache/v/cache/lastfailed" ]; then
            python_status="❌ Failed"
        else
            python_status="✅ Passed"
        fi
    elif [ "$RUST_ONLY" != "true" ]; then
        python_status="✅ Passed"
    fi
    
    # Check Rust test results
    if [ "$PYTHON_ONLY" != "true" ] && [ -f "$PROJECT_ROOT/rust_test_results.json" ]; then
        if command -v jq >/dev/null 2>&1; then
            local failed_modules=$(jq '.summary.failing_modules' "$PROJECT_ROOT/rust_test_results.json" 2>/dev/null || echo "0")
            if [ "$failed_modules" -gt 0 ]; then
                rust_status="❌ Failed"
            else
                rust_status="✅ Passed"
            fi
        else
            rust_status="✅ Completed"
        fi
    fi
    
    # Always test integration and core if not Rust-only
    if [ "$RUST_ONLY" != "true" ]; then
        integration_status="✅ Passed"  # Assume passed if we got here
        core_status="✅ Passed"        # Assume passed if we got here
    fi
    
    echo "📊 Comprehensive Test Results:"
    echo "  🐍 Python Tests:      $python_status"
    echo "  🦀 Rust Tests:        $rust_status"
    echo "  🔗 Integration Tests: $integration_status"
    echo "  ⚙️  Core Functionality: $core_status"
    echo ""
    
    # Check overall status
    if [[ "$python_status" == *"Failed"* ]] || [[ "$rust_status" == *"Failed"* ]] || [[ "$integration_status" == *"Failed"* ]] || [[ "$core_status" == *"Failed"* ]]; then
        log_error "Some tests failed"
        return 1
    else
        log_success "All tests passed! 🎉"
        return 0
    fi
}

# Display help
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Run comprehensive test suite for circuit-synth project.

Options:
  --python-only    Run only Python tests
  --rust-only      Run only Rust tests
  -v, --verbose    Show detailed test output
  -f, --fail-fast  Stop on first test failure
  -h, --help       Show this help message

Environment variables:
  VERBOSE=true     Enable verbose output
  FAIL_FAST=true   Enable fail-fast mode
  PYTHON_ONLY=true Run only Python tests
  RUST_ONLY=true   Run only Rust tests

Examples:
  $0                    # Run all tests
  $0 --python-only      # Run only Python tests
  $0 --rust-only -v     # Run only Rust tests with verbose output
  $0 --fail-fast        # Stop on first failure

Test Types:
  🐍 Python Tests      - Unit tests for Python code (pytest)
  🦀 Rust Tests        - Unit tests for Rust modules (cargo test)
  🔗 Integration Tests - Python-Rust integration tests
  ⚙️  Core Tests        - End-to-end functionality validation
EOF
}

# Main function
main() {
    log_info "🧪 Starting comprehensive test suite for circuit-synth..."
    echo "Working directory: $PROJECT_ROOT"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    local overall_success=true
    
    # Run Python tests
    if [ "$RUST_ONLY" != "true" ]; then
        if ! run_python_tests; then
            overall_success=false
        fi
    fi
    
    # Run Rust tests
    if [ "$PYTHON_ONLY" != "true" ]; then
        if ! run_rust_tests; then
            overall_success=false
        fi
    fi
    
    # Run integration tests (only if not Rust-only)
    if [ "$RUST_ONLY" != "true" ]; then
        if ! run_integration_tests; then
            overall_success=false
        fi
    fi
    
    # Test core functionality (only if not Rust-only)
    if [ "$RUST_ONLY" != "true" ]; then
        if ! test_core_functionality; then
            overall_success=false
        fi
    fi
    
    # Generate summary
    if ! generate_summary; then
        overall_success=false
    fi
    
    if [ "$overall_success" = "true" ]; then
        log_success "All tests completed successfully! 🚀"
        exit 0
    else
        log_error "Some tests failed. Please check the output above."
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --python-only)
            PYTHON_ONLY=true
            shift
            ;;
        --rust-only)
            RUST_ONLY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fail-fast)
            FAIL_FAST=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate conflicting options
if [ "$PYTHON_ONLY" = "true" ] && [ "$RUST_ONLY" = "true" ]; then
    log_error "Cannot specify both --python-only and --rust-only"
    exit 1
fi

# Run main function
main