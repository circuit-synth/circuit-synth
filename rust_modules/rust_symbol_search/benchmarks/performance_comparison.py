#!/usr/bin/env python3
"""
Comprehensive performance benchmark for Rust symbol search implementation.

This script benchmarks the Rust implementation across various scenarios and generates
detailed performance reports.
"""

import sys
import time
import statistics
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import argparse

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    from rust_symbol_search import RustSymbolSearcher, is_available as rust_available
except ImportError:
    rust_available = lambda: False
    RustSymbolSearcher = None

# Python implementation removed - using only Rust implementation
python_available = False
PythonSymbolSearcher = None


class PerformanceBenchmark:
    """Comprehensive performance benchmark suite."""
    
    def __init__(self):
        """Initialize the benchmark."""
        self.results = {}
        self.test_symbols = self.generate_test_symbols()
        self.test_queries = self.generate_test_queries()
    
    def generate_test_symbols(self) -> Dict[str, str]:
        """Generate a comprehensive set of test symbols."""
        symbols = {}
        
        # Basic components
        basic_components = [
            ("R", "Device"), ("C", "Device"), ("L", "Device"), ("D", "Device"),
            ("Q_NPN_BCE", "Device"), ("Q_PNP_BCE", "Device"), ("LED", "Device"),
            ("Varistor", "Device"), ("Crystal", "Device"), ("Fuse", "Device")
        ]
        
        # Voltage regulators
        regulators = [
            ("LM7805_TO220", "Regulator_Linear"), ("LM317_TO220", "Regulator_Linear"),
            ("AMS1117-3.3", "Regulator_Linear"), ("LM2596", "Regulator_Switching"),
            ("TLV62569", "Regulator_Switching"), ("AP2112K-3.3", "Regulator_Linear")
        ]
        
        # Connectors
        connectors = [
            ("USB_C_Receptacle", "Connector_USB"), ("USB_A", "Connector_USB"),
            ("Micro_SD_Card", "Connector_Card"), ("SD_Card_Device", "Connector_Card"),
            ("Conn_01x02", "Connector_Generic"), ("Conn_01x04", "Connector_Generic"),
            ("Conn_02x05_Odd_Even", "Connector_Generic")
        ]
        
        # Microcontrollers
        mcus = [
            ("ESP32-WROOM-32", "RF_Module"), ("STM32F103C8Tx", "MCU_ST_STM32F1"),
            ("ATmega328P-PU", "MCU_Microchip_ATmega"), ("STM32F407VGTx", "MCU_ST_STM32F4"),
            ("ESP8266-12E", "RF_Module"), ("STM32L476RGTx", "MCU_ST_STM32L4")
        ]
        
        # Sensors
        sensors = [
            ("LSM6DSL", "Sensor_Motion"), ("BME280", "Sensor_Humidity"),
            ("DS18B20", "Sensor_Temperature"), ("MPU6050", "Sensor_Motion"),
            ("BMP180", "Sensor_Pressure"), ("DHT22", "Sensor_Humidity")
        ]
        
        # Switches and buttons
        switches = [
            ("SW_Push", "Switch"), ("SW_DIP_x04", "Switch"),
            ("SW_SPDT", "Switch"), ("SW_Reed", "Switch")
        ]
        
        # Operational amplifiers
        opamps = [
            ("LM358", "Amplifier_Operational"), ("TL072", "Amplifier_Operational"),
            ("LM324", "Amplifier_Operational"), ("OPA2134", "Amplifier_Operational")
        ]
        
        # Add all components
        for name, lib in (basic_components + regulators + connectors + 
                         mcus + sensors + switches + opamps):
            symbols[name] = lib
        
        # Generate additional symbols for scale testing
        for i in range(1000):
            symbols[f"TestSymbol_{i:04d}"] = "TestLibrary"
            symbols[f"CustomIC_{i:04d}"] = "IC_Custom"
            symbols[f"Resistor_{i:04d}"] = "Resistor_Custom"
        
        return symbols
    
    def generate_test_queries(self) -> List[str]:
        """Generate test queries for benchmarking."""
        return [
            # Exact matches
            "Device:R", "Device:C", "Device:L",
            
            # Fuzzy matches
            "resistor", "capacitor", "inductor", "diode",
            
            # Complex components
            "voltage regulator", "USB connector", "microcontroller",
            "switching regulator", "SD card", "temperature sensor",
            
            # Common searches
            "5V regulator", "USB-C", "ESP32", "STM32", "connector",
            
            # Typos and variations
            "resitor", "capasitor", "usb conecter", "regulater",
            
            # Short queries
            "R", "C", "USB", "IC",
            
            # Long queries
            "high precision low noise voltage regulator",
            "USB Type-C connector with power delivery",
            "32-bit ARM microcontroller with WiFi",
            
            # Library-specific searches
            "Device", "Regulator_Linear", "Connector_USB",
            
            # Partial matches
            "LM78", "STM32F", "ESP", "BME"
        ]
    
    def benchmark_rust_implementation(self) -> Dict[str, Any]:
        """Benchmark the Rust implementation."""
        if not rust_available():
            return {"error": "Rust implementation not available"}
        
        print("Benchmarking Rust implementation...")
        
        searcher = RustSymbolSearcher()
        
        # Benchmark index building
        build_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            searcher.build_index(self.test_symbols)
            build_time = time.perf_counter() - start_time
            build_times.append(build_time * 1000)  # Convert to ms
        
        # Benchmark searches
        search_times = []
        result_counts = []
        
        for query in self.test_queries:
            query_times = []
            for _ in range(10):  # Multiple runs per query
                start_time = time.perf_counter()
                results = searcher.search(query, max_results=10, min_score=0.3)
                search_time = time.perf_counter() - start_time
                query_times.append(search_time * 1000)  # Convert to ms
            
            search_times.extend(query_times)
            result_counts.append(len(results))
        
        # Get statistics
        stats = searcher.get_stats()
        
        return {
            "implementation": "Rust",
            "available": True,
            "symbol_count": len(self.test_symbols),
            "query_count": len(self.test_queries),
            "build_times_ms": build_times,
            "avg_build_time_ms": statistics.mean(build_times),
            "search_times_ms": search_times,
            "avg_search_time_ms": statistics.mean(search_times),
            "median_search_time_ms": statistics.median(search_times),
            "p95_search_time_ms": self.percentile(search_times, 95),
            "p99_search_time_ms": self.percentile(search_times, 99),
            "min_search_time_ms": min(search_times),
            "max_search_time_ms": max(search_times),
            "total_searches": len(search_times),
            "avg_results_per_query": statistics.mean(result_counts),
            "under_1ms": sum(1 for t in search_times if t < 1.0),
            "under_5ms": sum(1 for t in search_times if t < 5.0),
            "under_10ms": sum(1 for t in search_times if t < 10.0),
            "under_100ms": sum(1 for t in search_times if t < 100.0),
            "stats": stats
        }
    
    # Python implementation removed - using only Rust implementation
    
    def percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def run_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark of Rust implementation."""
        print("Running Rust symbol search performance benchmark...")
        print(f"Testing with {len(self.test_symbols)} symbols and {len(self.test_queries)} queries")
        
        rust_results = self.benchmark_rust_implementation()
        
        return {
            "rust": rust_results,
            "benchmark_info": {
                "symbol_count": len(self.test_symbols),
                "query_count": len(self.test_queries),
                "timestamp": time.time()
            }
        }
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive performance report."""
        report = []
        report.append("=" * 80)
        report.append("RUST SYMBOL SEARCH PERFORMANCE BENCHMARK")
        report.append("=" * 80)
        report.append("")
        
        # Rust Results
        if results["rust"].get("available") and "error" not in results["rust"]:
            rust = results["rust"]
            report.append("🦀 RUST IMPLEMENTATION PERFORMANCE")
            report.append("-" * 40)
            report.append(f"Average search time: {rust['avg_search_time_ms']:.3f}ms")
            report.append(f"Median search time: {rust['median_search_time_ms']:.3f}ms")
            report.append(f"95th percentile: {rust['p95_search_time_ms']:.3f}ms")
            report.append(f"99th percentile: {rust['p99_search_time_ms']:.3f}ms")
            report.append(f"Average build time: {rust['avg_build_time_ms']:.3f}ms")
            report.append(f"Searches under 1ms: {rust['under_1ms']}/{rust['total_searches']} ({rust['under_1ms']/rust['total_searches']*100:.1f}%)")
            report.append(f"Searches under 5ms: {rust['under_5ms']}/{rust['total_searches']} ({rust['under_5ms']/rust['total_searches']*100:.1f}%)")
            report.append(f"Searches under 10ms: {rust['under_10ms']}/{rust['total_searches']} ({rust['under_10ms']/rust['total_searches']*100:.1f}%)")
            report.append(f"Searches under 100ms: {rust['under_100ms']}/{rust['total_searches']} ({rust['under_100ms']/rust['total_searches']*100:.1f}%)")
            report.append("")
            
            # Performance assessment
            report.append("📊 PERFORMANCE ASSESSMENT")
            report.append("-" * 40)
            avg_time = rust['avg_search_time_ms']
            if avg_time < 1.0:
                report.append("✅ EXCELLENT: Sub-millisecond average search times")
            elif avg_time < 5.0:
                report.append("✅ VERY GOOD: Sub-5ms average search times")
            elif avg_time < 10.0:
                report.append("✅ GOOD: Sub-10ms average search times")
            elif avg_time < 100.0:
                report.append("⚠️  ACCEPTABLE: Sub-100ms average search times")
            else:
                report.append("❌ NEEDS IMPROVEMENT: >100ms average search times")
            
            under_100ms_percent = rust['under_100ms']/rust['total_searches']*100
            if under_100ms_percent >= 95.0:
                report.append("✅ RELIABILITY: 95%+ searches under 100ms requirement met")
            else:
                report.append(f"⚠️  RELIABILITY: Only {under_100ms_percent:.1f}% searches under 100ms")
            
            report.append("")
        else:
            report.append("❌ RUST IMPLEMENTATION NOT AVAILABLE OR FAILED")
            if "error" in results["rust"]:
                report.append(f"Error: {results['rust']['error']}")
            report.append("")
        
        # Recommendations
        report.append("🎯 PRODUCTION READINESS")
        report.append("-" * 40)
        
        if results["rust"].get("available") and "error" not in results["rust"]:
            rust = results["rust"]
            avg_time = rust['avg_search_time_ms']
            under_100ms_percent = rust['under_100ms']/rust['total_searches']*100
            
            if avg_time < 10.0 and under_100ms_percent >= 95.0:
                report.append("✅ PRODUCTION READY: Excellent performance characteristics")
                report.append("   - Deploy immediately for production use")
            elif avg_time < 50.0 and under_100ms_percent >= 90.0:
                report.append("✅ PRODUCTION READY: Good performance characteristics")
                report.append("   - Suitable for production deployment")
            else:
                report.append("⚠️  NEEDS OPTIMIZATION: Performance below production standards")
                report.append("   - Consider optimization before production deployment")
        else:
            report.append("❌ NOT READY: Implementation not available")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main benchmark execution."""
    parser = argparse.ArgumentParser(description="Benchmark Rust symbol search performance")
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    parser.add_argument("--report", "-r", help="Output file for report (text)")
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark()
    results = benchmark.run_benchmark()
    
    # Generate and display report
    report = benchmark.generate_report(results)
    print(report)
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.report}")
    
    # Return success/failure based on results
    if (results["rust"].get("available") and "error" not in results["rust"] and
        results["rust"]["avg_search_time_ms"] < 100.0):
        print("\n🎉 Rust implementation meets performance requirements!")
        return 0
    else:
        print("\n⚠️  Performance requirements not met or implementation unavailable")
        return 1


if __name__ == "__main__":
    sys.exit(main())