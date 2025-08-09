#!/usr/bin/env python3
"""
Comprehensive Release Testing Suite for Circuit-Synth

This tool performs exhaustive testing of the package before releasing to PyPI:
1. Tests in isolated virtual environments
2. Tests from TestPyPI first
3. Tests on multiple Python versions
4. Tests with Docker containers (if available)
6. Tests actual circuit creation and KiCad generation
"""

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Container for test results"""
    test_name: str
    passed: bool
    message: str
    duration: float
    details: Optional[Dict] = None


class ReleaseTestSuite:
    """Comprehensive release testing for circuit-synth"""
    
    def __init__(self, package_version: str, skip_docker: bool = False):
        self.package_version = package_version
        self.skip_docker = skip_docker
        self.results: List[TestResult] = []
        self.test_pypi_url = "https://test.pypi.org/simple/"
        self.prod_pypi_url = "https://pypi.org/simple/"
        
    def run_all_tests(self) -> bool:
        """Run all release tests"""
        logger.info("=" * 80)
        logger.info(f"🚀 CIRCUIT-SYNTH RELEASE TEST SUITE v{self.package_version}")
        logger.info("=" * 80)
        
        all_passed = True
        
        # 1. Build the distribution
        if not self._test_build_distribution():
            logger.error("❌ Failed to build distribution")
            return False
            
        # 2. Test local wheel installation
        all_passed &= self._test_local_wheel_install()
        
        # 3. Upload to TestPyPI
        if not self._upload_to_test_pypi():
            logger.warning("⚠️ Could not upload to TestPyPI, skipping TestPyPI tests")
        else:
            # 4. Test from TestPyPI
            all_passed &= self._test_from_test_pypi()
        
        # 5. Test on multiple Python versions
        all_passed &= self._test_multiple_python_versions()
        
        # 6. Test in Docker (if available)
        if not self.skip_docker and shutil.which("docker"):
            all_passed &= self._test_in_docker()
        
        
        # 8. Test actual circuit functionality
        all_passed &= self._test_circuit_functionality()
        
        # Print summary
        self._print_summary()
        
        return all_passed
    
    def _test_build_distribution(self) -> bool:
        """Build the distribution files"""
        logger.info("\n📦 Building distribution...")
        start_time = time.time()
        
        try:
            # Clean dist directory
            dist_path = Path("dist")
            if dist_path.exists():
                shutil.rmtree(dist_path)
            
            # Build with uv
            result = subprocess.run(
                ["uv", "build"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Verify files exist
            wheel_files = list(dist_path.glob("*.whl"))
            tar_files = list(dist_path.glob("*.tar.gz"))
            
            if not wheel_files or not tar_files:
                raise Exception("Distribution files not created")
            
            duration = time.time() - start_time
            self.results.append(TestResult(
                "Build Distribution",
                True,
                f"Built wheel and source distribution",
                duration,
                {"wheel": str(wheel_files[0]), "source": str(tar_files[0])}
            ))
            logger.info(f"✅ Distribution built successfully in {duration:.2f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                "Build Distribution",
                False,
                str(e),
                duration
            ))
            logger.error(f"❌ Failed to build distribution: {e}")
            return False
    
    def _test_local_wheel_install(self) -> bool:
        """Test installation from local wheel"""
        logger.info("\n🧪 Testing local wheel installation...")
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Find wheel file
                wheel_file = list(Path("dist").glob("*.whl"))[0]
                
                # Create virtual environment
                venv_path = Path(temp_dir) / "venv"
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    check=True,
                    capture_output=True
                )
                
                # Install wheel
                pip_path = venv_path / "bin" / "pip" if platform.system() != "Windows" else venv_path / "Scripts" / "pip.exe"
                python_path = venv_path / "bin" / "python" if platform.system() != "Windows" else venv_path / "Scripts" / "python.exe"
                
                subprocess.run(
                    [str(pip_path), "install", str(wheel_file)],
                    check=True,
                    capture_output=True
                )
                
                # Test imports
                test_script = '''
import circuit_synth
from circuit_synth import Component, Net, circuit


# Create simple circuit
@circuit
def test_circuit():
    r1 = Component("Device:R", "R", value="1k")
    r2 = Component("Device:R", "R", value="2k")
    vcc = Net("VCC")
    gnd = Net("GND")
    r1[1] += vcc
    r1[2] += gnd
    r2[1] += vcc
    r2[2] += gnd

print("✅ All imports and basic functionality working!")
'''
                
                result = subprocess.run(
                    [str(python_path), "-c", test_script],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    raise Exception(f"Test script failed: {result.stderr}")
                
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "Local Wheel Install",
                    True,
                    "Package installed and imports work",
                    duration
                ))
                logger.info(f"✅ Local wheel installation test passed in {duration:.2f}s")
                return True
                
            except Exception as e:
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "Local Wheel Install",
                    False,
                    str(e),
                    duration
                ))
                logger.error(f"❌ Local wheel installation test failed: {e}")
                return False
    
    def _upload_to_test_pypi(self) -> bool:
        """Upload package to TestPyPI"""
        logger.info("\n📤 Uploading to TestPyPI...")
        
        try:
            # Check if .pypirc exists or environment variables are set
            pypirc_path = Path.home() / ".pypirc"
            if not pypirc_path.exists() and not os.environ.get("TWINE_USERNAME"):
                logger.warning("No .pypirc file or TWINE_USERNAME environment variable found")
                logger.info("Skipping TestPyPI upload - configure credentials to enable")
                return False
            
            result = subprocess.run(
                ["uv", "run", "twine", "upload", "--repository", "testpypi", "dist/*"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"TestPyPI upload failed: {result.stderr}")
                return False
            
            logger.info("✅ Uploaded to TestPyPI successfully")
            # Wait for package to be available
            logger.info("⏳ Waiting 30 seconds for TestPyPI to update...")
            time.sleep(30)
            return True
            
        except Exception as e:
            logger.warning(f"TestPyPI upload failed: {e}")
            return False
    
    def _test_from_test_pypi(self) -> bool:
        """Test installation from TestPyPI"""
        logger.info("\n🧪 Testing installation from TestPyPI...")
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Create virtual environment
                venv_path = Path(temp_dir) / "venv"
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    check=True,
                    capture_output=True
                )
                
                pip_path = venv_path / "bin" / "pip" if platform.system() != "Windows" else venv_path / "Scripts" / "pip.exe"
                python_path = venv_path / "bin" / "python" if platform.system() != "Windows" else venv_path / "Scripts" / "python.exe"
                
                # Install from TestPyPI with PyPI as extra index for dependencies
                subprocess.run(
                    [
                        str(pip_path), "install",
                        "--index-url", self.test_pypi_url,
                        "--extra-index-url", self.prod_pypi_url,
                        f"circuit-synth=={self.package_version}"
                    ],
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                
                # Test imports
                result = subprocess.run(
                    [str(python_path), "-c", "import circuit_synth; print('✅ TestPyPI package works!')"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "TestPyPI Install",
                    True,
                    "Package installed from TestPyPI successfully",
                    duration
                ))
                logger.info(f"✅ TestPyPI installation test passed in {duration:.2f}s")
                return True
                
            except Exception as e:
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "TestPyPI Install",
                    False,
                    str(e),
                    duration
                ))
                logger.error(f"❌ TestPyPI installation test failed: {e}")
                return False
    
    def _test_multiple_python_versions(self) -> bool:
        """Test on multiple Python versions if available"""
        logger.info("\n🐍 Testing multiple Python versions...")
        
        python_versions = ["3.12", "3.11", "3.10"]
        available_versions = []
        
        # Find available Python versions
        for version in python_versions:
            python_exe = f"python{version}"
            if shutil.which(python_exe):
                available_versions.append((version, python_exe))
        
        if not available_versions:
            logger.warning("No additional Python versions found for testing")
            return True
        
        all_passed = True
        wheel_file = list(Path("dist").glob("*.whl"))[0]
        
        for version, python_exe in available_versions:
            logger.info(f"\nTesting Python {version}...")
            start_time = time.time()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Create virtual environment
                    venv_path = Path(temp_dir) / "venv"
                    subprocess.run(
                        [python_exe, "-m", "venv", str(venv_path)],
                        check=True,
                        capture_output=True
                    )
                    
                    pip_path = venv_path / "bin" / "pip"
                    python_path = venv_path / "bin" / "python"
                    
                    # Install package
                    subprocess.run(
                        [str(pip_path), "install", str(wheel_file)],
                        check=True,
                        capture_output=True
                    )
                    
                    # Test import
                    subprocess.run(
                        [str(python_path), "-c", "import circuit_synth"],
                        check=True,
                        capture_output=True
                    )
                    
                    duration = time.time() - start_time
                    self.results.append(TestResult(
                        f"Python {version}",
                        True,
                        "Package works",
                        duration
                    ))
                    logger.info(f"✅ Python {version} test passed in {duration:.2f}s")
                    
                except Exception as e:
                    duration = time.time() - start_time
                    self.results.append(TestResult(
                        f"Python {version}",
                        False,
                        str(e),
                        duration
                    ))
                    logger.error(f"❌ Python {version} test failed: {e}")
                    all_passed = False
        
        return all_passed
    
    def _test_in_docker(self) -> bool:
        """Test in Docker containers"""
        logger.info("\n🐳 Testing in Docker containers...")
        start_time = time.time()
        
        # Create Dockerfile
        dockerfile_content = f'''
FROM python:3.12-slim
WORKDIR /test
COPY dist/*.whl /test/
RUN pip install /test/*.whl
RUN python -c "import circuit_synth; from circuit_synth import Component, Net, circuit; print('✅ Docker test passed!')"
'''
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Write Dockerfile
                dockerfile_path = Path(temp_dir) / "Dockerfile"
                dockerfile_path.write_text(dockerfile_content)
                
                # Copy dist directory
                shutil.copytree("dist", Path(temp_dir) / "dist")
                
                # Build Docker image
                subprocess.run(
                    ["docker", "build", "-t", f"circuit-synth-test:{self.package_version}", temp_dir],
                    check=True,
                    capture_output=True
                )
                
                # Run container
                result = subprocess.run(
                    ["docker", "run", "--rm", f"circuit-synth-test:{self.package_version}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "Docker Container",
                    True,
                    "Package works in Docker",
                    duration
                ))
                logger.info(f"✅ Docker test passed in {duration:.2f}s")
                return True
                
            except Exception as e:
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "Docker Container",
                    False,
                    str(e),
                    duration
                ))
                logger.error(f"❌ Docker test failed: {e}")
                return False
    
        start_time = time.time()
        
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Create virtual environment
                venv_path = Path(temp_dir) / "venv"
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    check=True,
                    capture_output=True
                )
                
                pip_path = venv_path / "bin" / "pip" if platform.system() != "Windows" else venv_path / "Scripts" / "pip.exe"
                python_path = venv_path / "bin" / "python" if platform.system() != "Windows" else venv_path / "Scripts" / "python.exe"
                
                # Install package
                wheel_file = list(Path("dist").glob("*.whl"))[0]
                subprocess.run(
                    [str(pip_path), "install", str(wheel_file)],
                    check=True,
                    capture_output=True
                )
                
                all_passed = True
                    test_script = f'''
import {module}
print(f"✅ {module} imported successfully")

# Test that module has expected attributes
attrs = dir({module})
if not attrs:
    raise Exception("{module} has no attributes!")
'''
                    
                    result = subprocess.run(
                        [str(python_path), "-c", test_script],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        logger.error(f"❌ {module} failed: {result.stderr}")
                        all_passed = False
                    else:
                        logger.info(f"✅ {module} works correctly")
                
                duration = time.time() - start_time
                self.results.append(TestResult(
                    all_passed,
                    duration
                ))
                return all_passed
                
            except Exception as e:
                duration = time.time() - start_time
                self.results.append(TestResult(
                    False,
                    str(e),
                    duration
                ))
                return False
    
    def _test_circuit_functionality(self) -> bool:
        """Test actual circuit creation and KiCad generation"""
        logger.info("\n⚡ Testing circuit functionality...")
        start_time = time.time()
        
        test_script = '''
from circuit_synth import Component, Net, circuit

@circuit
def test_circuit():
    """Test circuit with various components"""
    # Create components
    r1 = Component("Device:R", "R", value="10k")
    r2 = Component("Device:R", "R", value="20k")
    c1 = Component("Device:C", "C", value="100nF")
    
    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    sig = Net("SIGNAL")
    
    # Connect components
    r1[1] += vcc
    r1[2] += sig
    r2[1] += sig
    r2[2] += gnd
    c1[1] += sig
    c1[2] += gnd

# Generate the circuit
circuit_obj = test_circuit()

# Test JSON export
json_data = circuit_obj.to_dict()
assert "components" in json_data
assert "nets" in json_data
assert len(json_data["components"]) == 3
assert len(json_data["nets"]) == 3

print("✅ Circuit functionality test passed!")
'''
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Create virtual environment
                venv_path = Path(temp_dir) / "venv"
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    check=True,
                    capture_output=True
                )
                
                pip_path = venv_path / "bin" / "pip" if platform.system() != "Windows" else venv_path / "Scripts" / "pip.exe"
                python_path = venv_path / "bin" / "python" if platform.system() != "Windows" else venv_path / "Scripts" / "python.exe"
                
                # Install package
                wheel_file = list(Path("dist").glob("*.whl"))[0]
                subprocess.run(
                    [str(pip_path), "install", str(wheel_file)],
                    check=True,
                    capture_output=True
                )
                
                # Run test script
                result = subprocess.run(
                    [str(python_path), "-c", test_script],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "Circuit Functionality",
                    True,
                    "Circuit creation and export works",
                    duration
                ))
                logger.info(f"✅ Circuit functionality test passed in {duration:.2f}s")
                return True
                
            except Exception as e:
                duration = time.time() - start_time
                self.results.append(TestResult(
                    "Circuit Functionality",
                    False,
                    str(e),
                    duration
                ))
                logger.error(f"❌ Circuit functionality test failed: {e}")
                return False
    
    def _print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        
        passed_count = sum(1 for r in self.results if r.passed)
        failed_count = len(self.results) - passed_count
        total_time = sum(r.duration for r in self.results)
        
        # Print individual results
        for result in self.results:
            status = "✅" if result.passed else "❌"
            logger.info(f"{status} {result.test_name}: {result.message} ({result.duration:.2f}s)")
        
        logger.info("-" * 80)
        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"Passed: {passed_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Total Time: {total_time:.2f}s")
        
        if failed_count == 0:
            logger.info("\n🎉 ALL TESTS PASSED! Package is ready for release to PyPI.")
        else:
            logger.error(f"\n⚠️ {failed_count} TEST(S) FAILED! Do not release to PyPI.")


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive release testing for circuit-synth"
    )
    parser.add_argument(
        "version",
        help="Package version to test (e.g., 0.8.3)"
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Docker container tests"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run test suite
    test_suite = ReleaseTestSuite(args.version, args.skip_docker)
    success = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()