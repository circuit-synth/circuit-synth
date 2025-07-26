#!/usr/bin/env python3
"""
Integration tests for Rust symbol search implementation.

These tests validate that the Rust implementation produces results
that are compatible with and at least as accurate as the Python version.
"""

import sys
import pytest
import time
from pathlib import Path
from typing import Dict, List, Any, Set
from unittest.mock import Mock, patch

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from rust_symbol_search import RustSymbolSearcher, is_available as rust_available
    RUST_AVAILABLE = rust_available()
except ImportError:
    RUST_AVAILABLE = False
    RustSymbolSearcher = None

# Python implementation removed - using only Rust implementation
PYTHON_AVAILABLE = False
PythonSymbolSearcher = None


class TestSymbolData:
    """Test data for integration tests."""
    
    @staticmethod
    def get_comprehensive_symbols() -> Dict[str, str]:
        """Get a comprehensive set of test symbols."""
        return {
            # Basic components
            "R": "Device",
            "C": "Device", 
            "L": "Device",
            "D": "Device",
            "Q_NPN_BCE": "Device",
            "Q_PNP_BCE": "Device",
            "LED": "Device",
            "Varistor": "Device",
            "Crystal": "Device",
            "Fuse": "Device",
            
            # Voltage regulators
            "LM7805_TO220": "Regulator_Linear",
            "LM317_TO220": "Regulator_Linear",
            "AMS1117-3.3": "Regulator_Linear",
            "LM2596": "Regulator_Switching",
            "TLV62569": "Regulator_Switching",
            "AP2112K-3.3": "Regulator_Linear",
            
            # Connectors
            "USB_C_Receptacle": "Connector_USB",
            "USB_A": "Connector_USB",
            "Micro_SD_Card": "Connector_Card",
            "SD_Card_Device": "Connector_Card",
            "Conn_01x02": "Connector_Generic",
            "Conn_01x04": "Connector_Generic",
            "Conn_02x05_Odd_Even": "Connector_Generic",
            
            # Microcontrollers
            "ESP32-WROOM-32": "RF_Module",
            "STM32F103C8Tx": "MCU_ST_STM32F1",
            "ATmega328P-PU": "MCU_Microchip_ATmega",
            "STM32F407VGTx": "MCU_ST_STM32F4",
            "ESP8266-12E": "RF_Module",
            "STM32L476RGTx": "MCU_ST_STM32L4",
            
            # Sensors
            "LSM6DSL": "Sensor_Motion",
            "BME280": "Sensor_Humidity",
            "DS18B20": "Sensor_Temperature",
            "MPU6050": "Sensor_Motion",
            "BMP180": "Sensor_Pressure",
            "DHT22": "Sensor_Humidity",
            
            # Switches
            "SW_Push": "Switch",
            "SW_DIP_x04": "Switch",
            "SW_SPDT": "Switch",
            "SW_Reed": "Switch",
            
            # Operational amplifiers
            "LM358": "Amplifier_Operational",
            "TL072": "Amplifier_Operational",
            "LM324": "Amplifier_Operational",
            "OPA2134": "Amplifier_Operational",
        }
    
    @staticmethod
    def get_accuracy_test_cases() -> List[tuple]:
        """Get test cases for accuracy validation."""
        return [
            # (query, expected_symbol, expected_library, description)
            ("Device:R", "R", "Device", "Exact lib_id match"),
            ("Device:C", "C", "Device", "Exact lib_id match"),
            ("Device:L", "L", "Device", "Exact lib_id match"),
            ("resistor", "R", "Device", "Fuzzy match for resistor"),
            ("capacitor", "C", "Device", "Fuzzy match for capacitor"),
            ("inductor", "L", "Device", "Fuzzy match for inductor"),
            ("diode", "D", "Device", "Fuzzy match for diode"),
            ("LED", "LED", "Device", "Exact match for LED"),
            ("5V regulator", "LM7805_TO220", "Regulator_Linear", "Complex search"),
            ("USB connector", "USB_C_Receptacle", "Connector_USB", "Complex search"),
            ("microcontroller", "ESP32-WROOM-32", "RF_Module", "Complex search"),
            ("temperature sensor", "DS18B20", "Sensor_Temperature", "Complex search"),
        ]


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust implementation not available")
class TestRustImplementation:
    """Test the Rust implementation functionality."""
    
    def test_basic_functionality(self):
        """Test basic search functionality."""
        searcher = RustSymbolSearcher()
        symbols = TestSymbolData.get_comprehensive_symbols()
        
        searcher.build_index(symbols)
        assert searcher.is_ready()
        
        # Test exact match
        results = searcher.search("Device:R", max_results=5)
        assert len(results) > 0
        assert results[0]["name"] == "R"
        assert results[0]["library"] == "Device"
        
        # Test fuzzy match
        results = searcher.search("resistor", max_results=5)
        assert len(results) > 0
    
    def test_performance_requirements(self):
        """Test that performance requirements are met."""
        searcher = RustSymbolSearcher()
        symbols = TestSymbolData.get_comprehensive_symbols()
        
        # Test index build time
        start_time = time.perf_counter()
        searcher.build_index(symbols)
        build_time = time.perf_counter() - start_time
        
        assert build_time < 0.1, f"Index build took {build_time:.3f}s, expected < 0.1s"
        
        # Test search times
        test_queries = ["resistor", "Device:R", "USB", "regulator", "sensor"]
        
        for query in test_queries:
            start_time = time.perf_counter()
            results = searcher.search(query, max_results=10)
            search_time = time.perf_counter() - start_time
            
            assert search_time < 0.01, f"Search for '{query}' took {search_time:.3f}s, expected < 0.01s"
            assert len(results) >= 0  # Should not crash
    
    def test_accuracy_requirements(self):
        """Test accuracy requirements."""
        searcher = RustSymbolSearcher()
        symbols = TestSymbolData.get_comprehensive_symbols()
        searcher.build_index(symbols)
        
        test_cases = TestSymbolData.get_accuracy_test_cases()
        passed_tests = 0
        
        for query, expected_symbol, expected_library, description in test_cases:
            results = searcher.search(query, max_results=5)
            
            # Check if expected result is in top 3
            found = False
            for result in results[:3]:
                if (result["name"] == expected_symbol and 
                    result["library"] == expected_library):
                    found = True
                    break
            
            if found:
                passed_tests += 1
            else:
                print(f"Failed: {description} - '{query}' -> expected {expected_library}:{expected_symbol}")
                print(f"  Got: {[r['lib_id'] for r in results[:3]]}")
        
        accuracy = passed_tests / len(test_cases)
        assert accuracy >= 0.90, f"Accuracy {accuracy:.1%} below required 90%"
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        searcher = RustSymbolSearcher()
        symbols = TestSymbolData.get_comprehensive_symbols()
        searcher.build_index(symbols)
        
        # Empty query
        results = searcher.search("", max_results=5)
        assert len(results) == 0
        
        # Whitespace only
        results = searcher.search("   ", max_results=5)
        assert len(results) == 0
        
        # Very long query
        long_query = "a" * 1000
        results = searcher.search(long_query, max_results=5)
        # Should not crash
        
        # Special characters
        results = searcher.search("Device:R", max_results=5)
        assert len(results) > 0
        
        # Case insensitive
        results1 = searcher.search("USB", max_results=5)
        results2 = searcher.search("usb", max_results=5)
        assert len(results1) > 0
        assert len(results2) > 0
    
    def test_result_format(self):
        """Test that results have the correct format."""
        searcher = RustSymbolSearcher()
        symbols = TestSymbolData.get_comprehensive_symbols()
        searcher.build_index(symbols)
        
        results = searcher.search("resistor", max_results=5)
        
        for result in results:
            assert isinstance(result, dict)
            assert "lib_id" in result
            assert "name" in result
            assert "library" in result
            assert "score" in result
            assert "match_type" in result
            assert "match_details" in result
            
            assert isinstance(result["lib_id"], str)
            assert isinstance(result["name"], str)
            assert isinstance(result["library"], str)
            assert isinstance(result["score"], float)
            assert isinstance(result["match_type"], str)
            assert isinstance(result["match_details"], dict)
            
            assert 0.0 <= result["score"] <= 1.0
            assert ":" in result["lib_id"]


# Compatibility tests removed - using only Rust implementation
# The Rust implementation is now the single production solution


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust implementation not available")
    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        searcher = RustSymbolSearcher()
        symbols = {"R": "Device", "C": "Device"}
        searcher.build_index(symbols)
        
        # Invalid max_results
        with pytest.raises(ValueError):
            searcher.search("resistor", max_results=0)
        
        with pytest.raises(ValueError):
            searcher.search("resistor", max_results=-1)
        
        # Invalid min_score
        with pytest.raises(ValueError):
            searcher.search("resistor", min_score=-0.1)
        
        with pytest.raises(ValueError):
            searcher.search("resistor", min_score=1.1)
        
        # Invalid query type
        with pytest.raises(TypeError):
            searcher.search(123)
    
    @pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust implementation not available")
    def test_uninitialized_searcher(self):
        """Test behavior with uninitialized searcher."""
        searcher = RustSymbolSearcher()
        
        # Should work but return no results
        results = searcher.search("resistor")
        assert len(results) == 0


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])