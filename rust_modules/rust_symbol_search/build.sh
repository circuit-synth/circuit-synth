#!/bin/bash
set -e

echo "🦀 Building Rust Symbol Search Engine"
echo "===================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v cargo &> /dev/null; then
    echo "❌ Cargo not found. Please install Rust: https://rustup.rs/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Build Rust library
echo ""
echo "🔨 Building Rust library..."
cargo build --release

echo "✅ Rust library built successfully"

# Run Rust tests
echo ""
echo "🧪 Running Rust tests..."
cargo test --release

echo "✅ Rust tests passed"

# Install maturin if not present
echo ""
echo "📦 Checking maturin..."
if ! python3 -c "import maturin" 2>/dev/null; then
    echo "Installing maturin..."
    pip install maturin
fi

echo "✅ Maturin ready"

# Build Python bindings
echo ""
echo "🐍 Building Python bindings..."
maturin develop --release

echo "✅ Python bindings built successfully"

# Run Python tests
echo ""
echo "🧪 Running Python integration tests..."
if command -v pytest &> /dev/null; then
    python3 -m pytest tests/ -v
else
    echo "⚠️  pytest not found, running basic test..."
    python3 -c "
import sys
sys.path.insert(0, 'python')
from rust_symbol_search import RustSymbolSearcher, is_available
print(f'Rust available: {is_available()}')
if is_available():
    searcher = RustSymbolSearcher()
    symbols = {'R': 'Device', 'C': 'Device'}
    searcher.build_index(symbols)
    results = searcher.search('resistor', max_results=5)
    print(f'Search test: {len(results)} results found')
    print('✅ Basic functionality test passed')
else:
    print('❌ Rust implementation not available')
    sys.exit(1)
"
fi

echo "✅ Python tests passed"

# Run performance benchmark
echo ""
echo "⚡ Running performance benchmark..."
python3 benchmarks/performance_comparison.py --output benchmark_results.json --report benchmark_report.txt

echo "✅ Performance benchmark completed"

# Display results
echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "📊 Quick Performance Check:"
python3 -c "
import json
try:
    with open('benchmark_results.json', 'r') as f:
        results = json.load(f)
    
    if 'rust' in results and 'available' in results['rust'] and results['rust']['available']:
        rust_data = results['rust']
        print(f'  Index build time: {rust_data[\"avg_build_time_ms\"]:.1f}ms')
        print(f'  Average search time: {rust_data[\"avg_search_time_ms\"]:.3f}ms')
        print(f'  Searches under 5ms: {rust_data[\"under_5ms\"]}/{rust_data[\"total_searches\"]} ({rust_data[\"under_5ms\"]/rust_data[\"total_searches\"]*100:.1f}%)')
        
        if 'comparison' in results and results['comparison']:
            comp = results['comparison']
            print(f'  Performance improvement: {comp[\"search_speedup\"]:.1f}x faster than Python')
    else:
        print('  Benchmark data not available')
except:
    print('  Benchmark results not found')
"

echo ""
echo "📁 Generated Files:"
echo "  - benchmark_results.json (detailed benchmark data)"
echo "  - benchmark_report.txt (human-readable report)"
echo ""
echo "🚀 Ready for deployment!"
echo ""
echo "Next steps:"
echo "  1. Review benchmark_report.txt for performance analysis"
echo "  2. Run 'pip install -e .' to install the package"
echo "  3. Import and use: from rust_symbol_search import RustSymbolSearcher"