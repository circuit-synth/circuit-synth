#!/usr/bin/env python3
"""
Defensive Baseline Measurement Script

This script establishes comprehensive baseline metrics for the current Python
implementation of circuit-synth, creating a "golden standard" for all future
Rust integration comparisons.

Usage:
    uv run python scripts/defensive_baseline.py
    
Environment Variables:
    BASELINE_RUNS=10                    # Number of test runs (default: 5)
    BASELINE_OUTPUT_DIR=baseline_data   # Output directory for baseline data
    BASELINE_VERBOSE=true               # Enable verbose logging
"""

import sys
import os
import json
import time
import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import logging

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.core.defensive_logging import DefensiveLogger, get_defensive_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('BASELINE_VERBOSE', 'false').lower() == 'true' else logging.WARNING,
    format='%(asctime)s | %(levelname)-8s | BASELINE | %(message)s'
)

logger = logging.getLogger(__name__)


@dataclass
class BaselineRun:
    """Single baseline run results"""
    run_number: int
    total_time: float
    circuit_creation_time: float
    kicad_netlist_time: float
    json_netlist_time: float
    kicad_project_time: float
    
    # File checksums for consistency validation
    kicad_netlist_checksum: str
    json_netlist_checksum: str
    kicad_project_files: Dict[str, str]  # filename -> checksum
    
    # System information
    python_version: str
    system_info: Dict[str, str]
    
    # Success/failure status
    success: bool
    error_message: str = ""


@dataclass
class BaselineResults:
    """Comprehensive baseline results"""
    timestamp: str
    circuit_synth_version: str
    runs: List[BaselineRun]
    
    # Aggregate statistics
    avg_total_time: float
    std_total_time: float
    min_total_time: float
    max_total_time: float
    
    # Consistency validation
    all_outputs_identical: bool
    reference_checksums: Dict[str, str]
    
    # Performance breakdown
    avg_circuit_creation: float
    avg_kicad_netlist: float
    avg_json_netlist: float
    avg_kicad_project: float


class DefensiveBaselineMeasurement:
    """Ultra-defensive baseline measurement system"""
    
    def __init__(self):
        self.defensive_logger = get_defensive_logger("baseline_measurement")
        self.num_runs = int(os.environ.get('BASELINE_RUNS', '5'))
        self.output_dir = Path(os.environ.get('BASELINE_OUTPUT_DIR', 'baseline_data'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up any existing test outputs
        self.cleanup_test_outputs()
        
        self.defensive_logger.logger.info(f"🛡️  DEFENSIVE BASELINE MEASUREMENT INITIALIZED")
        self.defensive_logger.logger.info(f"   🔢 Number of runs: {self.num_runs}")
        self.defensive_logger.logger.info(f"   📁 Output directory: {self.output_dir}")

    def cleanup_test_outputs(self):
        """Clean up any existing test outputs to ensure clean baseline"""
        cleanup_patterns = [
            "example_kicad_project.net",
            "example_kicad_project.json",
            "example_kicad_project/",
        ]
        
        for pattern in cleanup_patterns:
            if os.path.exists(pattern):
                if os.path.isdir(pattern):
                    shutil.rmtree(pattern)
                    self.defensive_logger.logger.info(f"🧹 Cleaned up directory: {pattern}")
                else:
                    os.remove(pattern)
                    self.defensive_logger.logger.info(f"🧹 Cleaned up file: {pattern}")

    def run_single_baseline(self, run_number: int) -> BaselineRun:
        """Run a single baseline measurement"""
        self.defensive_logger.logger.info(f"🚀 STARTING BASELINE RUN #{run_number}")
        
        # Clean up before each run
        self.cleanup_test_outputs()
        
        try:
            # Import circuit_synth to trigger any import overhead
            import circuit_synth
            
            # Time the complete example script execution
            total_start = time.perf_counter()
            
            # Execute the example script and capture detailed timing
            result = self._execute_example_script_with_timing()
            
            total_end = time.perf_counter()
            total_time = total_end - total_start
            
            # Validate outputs and calculate checksums
            checksums = self._validate_and_checksum_outputs()
            
            # Collect system information
            system_info = self._collect_system_info()
            
            baseline_run = BaselineRun(
                run_number=run_number,
                total_time=total_time,
                circuit_creation_time=result['circuit_creation'],
                kicad_netlist_time=result['kicad_netlist'],
                json_netlist_time=result['json_netlist'],
                kicad_project_time=result['kicad_project'],
                kicad_netlist_checksum=checksums['netlist'],
                json_netlist_checksum=checksums['json'],
                kicad_project_files=checksums['project_files'],
                python_version=sys.version,
                system_info=system_info,
                success=True
            )
            
            self.defensive_logger.logger.info(f"✅ BASELINE RUN #{run_number} COMPLETED")
            self.defensive_logger.logger.info(f"   ⏱️  Total time: {total_time:.4f}s")
            self.defensive_logger.logger.info(f"   🔐 Netlist checksum: {checksums['netlist'][:16]}...")
            
            return baseline_run
            
        except Exception as e:
            self.defensive_logger.logger.error(f"❌ BASELINE RUN #{run_number} FAILED")
            self.defensive_logger.logger.error(f"   🔴 Error: {type(e).__name__}: {e}")
            
            return BaselineRun(
                run_number=run_number,
                total_time=0.0,
                circuit_creation_time=0.0,
                kicad_netlist_time=0.0,
                json_netlist_time=0.0,
                kicad_project_time=0.0,
                kicad_netlist_checksum="",
                json_netlist_checksum="",
                kicad_project_files={},
                python_version=sys.version,
                system_info=self._collect_system_info(),
                success=False,
                error_message=str(e)
            )

    def _execute_example_script_with_timing(self) -> Dict[str, float]:
        """Execute the example script and capture detailed timing"""
        # We'll modify the example script temporarily to capture timing
        # For now, simulate the timing breakdown based on our profiling data
        
        # Import and execute the circuit creation
        sys.path.append('examples')
        
        # Time circuit creation
        circuit_start = time.perf_counter()
        
        # Import the example script and execute main parts
        import importlib.util
        spec = importlib.util.spec_from_file_location("example_module", "examples/example_kicad_project.py")
        example_module = importlib.util.module_from_spec(spec)
        
        # Execute the module to get the root function
        spec.loader.exec_module(example_module)
        circuit = example_module.root()
        
        circuit_end = time.perf_counter()
        
        # Time KiCad netlist generation
        kicad_netlist_start = time.perf_counter()
        circuit.generate_kicad_netlist("example_kicad_project.net")
        kicad_netlist_end = time.perf_counter()
        
        # Time JSON netlist generation
        json_netlist_start = time.perf_counter()
        circuit.generate_json_netlist("example_kicad_project.json")
        json_netlist_end = time.perf_counter()
        
        # Time KiCad project generation
        kicad_project_start = time.perf_counter()
        circuit.generate_kicad_project("example_kicad_project", force_regenerate=False, draw_bounding_boxes=True)
        kicad_project_end = time.perf_counter()
        
        return {
            'circuit_creation': circuit_end - circuit_start,
            'kicad_netlist': kicad_netlist_end - kicad_netlist_start,
            'json_netlist': json_netlist_end - json_netlist_start,
            'kicad_project': kicad_project_end - kicad_project_start,
        }

    def _validate_and_checksum_outputs(self) -> Dict[str, Any]:
        """Validate all outputs exist and calculate checksums"""
        checksums = {}
        
        # Check KiCad netlist
        netlist_path = Path("example_kicad_project.net")
        if netlist_path.exists():
            with open(netlist_path, 'rb') as f:
                checksums['netlist'] = hashlib.md5(f.read()).hexdigest()
        else:
            raise FileNotFoundError("KiCad netlist not generated")
        
        # Check JSON netlist
        json_path = Path("example_kicad_project.json")
        if json_path.exists():
            with open(json_path, 'rb') as f:
                checksums['json'] = hashlib.md5(f.read()).hexdigest()
        else:
            raise FileNotFoundError("JSON netlist not generated")
        
        # Check KiCad project files
        project_dir = Path("example_kicad_project")
        if project_dir.exists():
            project_files = {}
            for file_path in project_dir.rglob("*"):
                if file_path.is_file():
                    with open(file_path, 'rb') as f:
                        relative_path = str(file_path.relative_to(project_dir))
                        project_files[relative_path] = hashlib.md5(f.read()).hexdigest()
            checksums['project_files'] = project_files
        else:
            raise FileNotFoundError("KiCad project directory not generated")
        
        self.defensive_logger.logger.info(f"🔍 OUTPUT VALIDATION COMPLETED")
        self.defensive_logger.logger.info(f"   📄 Netlist files: 2")
        self.defensive_logger.logger.info(f"   📁 Project files: {len(checksums['project_files'])}")
        
        return checksums

    def _collect_system_info(self) -> Dict[str, str]:
        """Collect system information for reproducibility"""
        import platform
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'machine': platform.machine(),
        }
        
        # Try to get UV version
        try:
            result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                system_info['uv_version'] = result.stdout.strip()
        except:
            system_info['uv_version'] = 'not available'
        
        return system_info

    def run_comprehensive_baseline(self) -> BaselineResults:
        """Run comprehensive baseline measurement with multiple runs"""
        self.defensive_logger.logger.info(f"🎯 STARTING COMPREHENSIVE BASELINE MEASUREMENT")
        self.defensive_logger.logger.info(f"   🔢 Total runs: {self.num_runs}")
        
        runs = []
        successful_runs = []
        
        for i in range(1, self.num_runs + 1):
            run = self.run_single_baseline(i)
            runs.append(run)
            
            if run.success:
                successful_runs.append(run)
            
            # Small delay between runs
            time.sleep(0.5)
        
        if not successful_runs:
            raise RuntimeError("No successful baseline runs completed")
        
        # Calculate aggregate statistics
        total_times = [run.total_time for run in successful_runs]
        avg_total = sum(total_times) / len(total_times)
        
        # Calculate standard deviation
        variance = sum((t - avg_total) ** 2 for t in total_times) / len(total_times)
        std_total = variance ** 0.5
        
        # Validate consistency (all outputs should be identical)
        reference_run = successful_runs[0]
        all_identical = True
        
        for run in successful_runs[1:]:
            if (run.kicad_netlist_checksum != reference_run.kicad_netlist_checksum or
                run.json_netlist_checksum != reference_run.json_netlist_checksum):
                all_identical = False
                break
        
        # Create baseline results
        baseline_results = BaselineResults(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            circuit_synth_version="current",  # Could extract from package
            runs=runs,
            avg_total_time=avg_total,
            std_total_time=std_total,
            min_total_time=min(total_times),
            max_total_time=max(total_times),
            all_outputs_identical=all_identical,
            reference_checksums={
                'netlist': reference_run.kicad_netlist_checksum,
                'json': reference_run.json_netlist_checksum,
                'project_files': reference_run.kicad_project_files,
            },
            avg_circuit_creation=sum(run.circuit_creation_time for run in successful_runs) / len(successful_runs),
            avg_kicad_netlist=sum(run.kicad_netlist_time for run in successful_runs) / len(successful_runs),
            avg_json_netlist=sum(run.json_netlist_time for run in successful_runs) / len(successful_runs),
            avg_kicad_project=sum(run.kicad_project_time for run in successful_runs) / len(successful_runs),
        )
        
        self.defensive_logger.logger.info(f"📊 COMPREHENSIVE BASELINE COMPLETED")
        self.defensive_logger.logger.info(f"   ✅ Successful runs: {len(successful_runs)}/{self.num_runs}")
        self.defensive_logger.logger.info(f"   ⏱️  Average time: {avg_total:.4f}s ± {std_total:.4f}s")
        self.defensive_logger.logger.info(f"   🔍 Output consistency: {'PASS' if all_identical else 'FAIL'}")
        
        return baseline_results

    def save_baseline_results(self, results: BaselineResults) -> Path:
        """Save baseline results to JSON file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        filename = f"baseline_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Convert to JSON-serializable format
        results_dict = asdict(results)
        
        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2, sort_keys=True)
        
        # Also save as "latest" for easy reference
        latest_path = self.output_dir / "baseline_latest.json"
        with open(latest_path, 'w') as f:
            json.dump(results_dict, f, indent=2, sort_keys=True)
        
        self.defensive_logger.logger.info(f"💾 BASELINE RESULTS SAVED")
        self.defensive_logger.logger.info(f"   📁 File: {filepath}")
        self.defensive_logger.logger.info(f"   📁 Latest: {latest_path}")
        
        return filepath

    def generate_baseline_report(self, results: BaselineResults) -> str:
        """Generate human-readable baseline report"""
        report = []
        report.append("=" * 80)
        report.append("🛡️  CIRCUIT-SYNTH DEFENSIVE BASELINE REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {results.timestamp}")
        report.append(f"Version: {results.circuit_synth_version}")
        report.append(f"Successful runs: {len([r for r in results.runs if r.success])}/{len(results.runs)}")
        report.append("")
        
        report.append("📊 PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append(f"Average total time:     {results.avg_total_time:.4f}s ± {results.std_total_time:.4f}s")
        report.append(f"Range:                  {results.min_total_time:.4f}s - {results.max_total_time:.4f}s")
        report.append("")
        report.append("⏱️  TIMING BREAKDOWN")
        report.append("-" * 40)
        report.append(f"Circuit creation:       {results.avg_circuit_creation:.4f}s")
        report.append(f"KiCad netlist:          {results.avg_kicad_netlist:.4f}s")
        report.append(f"JSON netlist:           {results.avg_json_netlist:.4f}s")
        report.append(f"KiCad project:          {results.avg_kicad_project:.4f}s")
        report.append("")
        
        report.append("🔍 CONSISTENCY VALIDATION")
        report.append("-" * 40)
        report.append(f"All outputs identical:  {'✅ PASS' if results.all_outputs_identical else '❌ FAIL'}")
        report.append(f"Reference netlist:      {results.reference_checksums['netlist'][:16]}...")
        report.append(f"Reference JSON:         {results.reference_checksums['json'][:16]}...")
        report.append(f"Project files:          {len(results.reference_checksums['project_files'])} files")
        report.append("")
        
        if not results.all_outputs_identical:
            report.append("⚠️  WARNING: Output inconsistency detected!")
            report.append("This suggests non-deterministic behavior in the current implementation.")
            report.append("Rust integration should proceed with extra caution.")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main baseline measurement execution"""
    print("🛡️  Starting Circuit-Synth Defensive Baseline Measurement")
    print("=" * 60)
    
    try:
        baseline = DefensiveBaselineMeasurement()
        results = baseline.run_comprehensive_baseline()
        
        # Save results
        results_file = baseline.save_baseline_results(results)
        
        # Generate and display report
        report = baseline.generate_baseline_report(results)
        print("\n" + report)
        
        # Save report to file
        report_file = baseline.output_dir / f"baseline_report_{int(time.time())}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📁 Results saved to: {results_file}")
        print(f"📁 Report saved to: {report_file}")
        
        if not results.all_outputs_identical:
            print("\n⚠️  WARNING: Inconsistent outputs detected!")
            print("Consider investigating before Rust integration.")
            sys.exit(1)
        else:
            print("\n✅ Baseline measurement completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Baseline measurement failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()