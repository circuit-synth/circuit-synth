#!/usr/bin/env python3
"""
Simple TDD for Rust Integration - Keep It Simple!

Just the basics:
1. Test Python function works
2. Test Rust function works (when it exists)  
3. Test they produce same output
4. Test Rust is faster

That's it. No complex frameworks.
"""

import pytest
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def python_component_sexp(component_data):
    """Simple Python S-expression generator for testing"""
    ref = component_data.get("ref", "U?")
    symbol = component_data.get("symbol", "Device:Unknown")
    value = component_data.get("value", "")
    
    result = f'(symbol (lib_id "{symbol}") (at 0 0 0) (unit 1)\n'
    result += f'  (property "Reference" "{ref}")\n'
    if value:
        result += f'  (property "Value" "{value}")\n'
    result += ')'
    
    return result


def rust_component_sexp(component_data):
    """Rust S-expression generator - doesn't exist yet"""
    # This will fail until we implement it
    try:
        import rust_kicad_schematic_writer
        return rust_kicad_schematic_writer.generate_component_sexp(component_data)
    except ImportError:
        raise Exception("Rust module not implemented yet")


def normalize_timestamps(text):
    """Remove timestamps to make outputs comparable"""
    import re
    # Remove timestamp-like patterns
    text = re.sub(r'/root-\d+/', '/root-TIMESTAMP/', text)
    text = re.sub(r'uuid "[0-9a-f-]+"', 'uuid "NORMALIZED"', text)
    return text


class TestComponentSExpression:
    """Dead simple TDD tests"""
    
    def test_python_works(self):
        """Test: Python implementation works"""
        component = {
            "ref": "R1",
            "symbol": "Device:R", 
            "value": "10K"
        }
        
        result = python_component_sexp(component)
        
        print(f"Python result: {result}")
        
        assert "R1" in result
        assert "Device:R" in result
        assert "10K" in result
        assert result.startswith('(symbol')
        
        print("✅ Python implementation works")
    
    def test_rust_doesnt_exist_yet(self):
        """Test: Rust implementation fails (RED phase)"""
        component = {
            "ref": "R1", 
            "symbol": "Device:R",
            "value": "10K"
        }
        
        with pytest.raises(Exception):
            rust_component_sexp(component)
        
        print("✅ Rust implementation correctly fails (expected in RED phase)")
    
    @pytest.mark.skip(reason="Enable when Rust implementation exists")
    def test_rust_python_same_output(self):
        """Test: Rust and Python produce same output (GREEN phase)"""
        component = {
            "ref": "R1",
            "symbol": "Device:R",
            "value": "10K"
        }
        
        python_result = python_component_sexp(component)
        rust_result = rust_component_sexp(component)
        
        # Normalize any timestamps/UUIDs
        python_normalized = normalize_timestamps(python_result)
        rust_normalized = normalize_timestamps(rust_result)
        
        print(f"Python: {python_normalized}")
        print(f"Rust:   {rust_normalized}")
        
        assert python_normalized == rust_normalized
        
        print("✅ Rust and Python produce identical output")
    
    @pytest.mark.skip(reason="Enable when Rust implementation exists")
    def test_rust_is_faster(self):
        """Test: Rust is faster than Python (REFACTOR phase)"""
        component = {
            "ref": "U1",
            "symbol": "RF_Module:ESP32-S3-MINI-1", 
            "value": "ESP32-S3-MINI-1"
        }
        
        # Time Python
        start = time.perf_counter()
        for _ in range(1000):
            python_component_sexp(component)
        python_time = time.perf_counter() - start
        
        # Time Rust
        start = time.perf_counter()
        for _ in range(1000):
            rust_component_sexp(component)
        rust_time = time.perf_counter() - start
        
        speedup = python_time / rust_time
        
        print(f"Python: {python_time:.4f}s")
        print(f"Rust:   {rust_time:.4f}s")
        print(f"Speedup: {speedup:.1f}x")
        
        assert speedup > 2.0, f"Rust only {speedup:.1f}x faster, expected >2x"
        
        print("✅ Rust is significantly faster than Python")


def update_memory_bank(message):
    """Simple memory bank update"""
    memory_file = Path(__file__).parent.parent.parent / "memory-bank" / "progress" / "simple-rust-tdd.md"
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(memory_file, 'a') as f:
        f.write(f"- **{timestamp}**: {message}\n")
    
    print(f"📝 Updated memory bank: {message}")


if __name__ == "__main__":
    print("🧪 Simple Rust TDD Demo")
    print("=" * 40)
    
    # Initialize memory bank
    update_memory_bank("Started simple TDD for S-expression generation")
    
    # Run basic tests
    test = TestComponentSExpression()
    
    try:
        test.test_python_works()
        update_memory_bank("✅ Python implementation test passed")
    except Exception as e:
        print(f"❌ Python test failed: {e}")
        update_memory_bank(f"❌ Python test failed: {e}")
    
    try:
        test.test_rust_doesnt_exist_yet()
        update_memory_bank("✅ Rust RED phase test passed (expected failure)")
    except Exception as e:
        print(f"❌ Rust RED test failed: {e}")
        update_memory_bank(f"❌ Rust RED test failed: {e}")
    
    print("\n🎯 Next steps:")
    print("1. Implement minimal Rust function in rust_kicad_schematic_writer")
    print("2. Enable test_rust_python_same_output test")
    print("3. Make it pass (GREEN phase)")
    print("4. Enable performance test (REFACTOR phase)")
    
    update_memory_bank("TDD setup complete - ready for Rust implementation")