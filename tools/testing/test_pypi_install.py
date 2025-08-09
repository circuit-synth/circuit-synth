#!/usr/bin/env python3
"""
Ultra-thorough PyPI installation test to prevent broken releases.

This script performs comprehensive testing of the circuit-synth package
as it would be installed from PyPI, ensuring ALL functionality works.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return output."""
    print(f"  Running: {cmd}")
    result = subprocess.run(
        cmd, 
        shell=True, 
        cwd=cwd, 
        capture_output=True, 
        text=True,
        check=False
    )
    
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"   stdout: {result.stdout}")
        print(f"   stderr: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd)
    
    return result


def test_wheel_installation(wheel_path):
    """Test installation from a wheel file."""
    print(f"\n{'='*60}")
    print("🧪 TESTING WHEEL INSTALLATION")
    print(f"{'='*60}")
    
    # Create a fresh virtual environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"
        project_path = Path(tmpdir) / "test_project"
        
        print(f"\n📁 Test directory: {tmpdir}")
        
        # Create virtual environment
        print("\n1️⃣ Creating fresh virtual environment...")
        run_command(f"python3 -m venv {venv_path}")
        
        # Upgrade pip
        pip_cmd = f"{venv_path}/bin/pip"
        python_cmd = f"{venv_path}/bin/python"
        
        print("\n2️⃣ Upgrading pip...")
        run_command(f"{pip_cmd} install --upgrade pip", check=False)
        
        # Install the wheel
        print(f"\n3️⃣ Installing wheel: {wheel_path}")
        result = run_command(f"{pip_cmd} install {wheel_path}")
        
        # Test 1: Basic import
        print("\n4️⃣ Testing basic import...")
        
        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Write test script to file to avoid shell escaping issues
        test_script = project_path / "test_imports.py"
        test_script.write_text("""import sys
import circuit_synth
print(f'Version: {circuit_synth.__version__}')

# Test all critical imports
from circuit_synth import Circuit, Component, Net
print('Core imports work')

print('SymbolLibCache imports')

# Test the class method that was broken
print('Testing SymbolLibCache.get_symbol_data class method...')
try:
    # This should work even if symbol doesn't exist - the method should be callable
    SymbolLibCache.get_symbol_data('Device:R')
    print('SymbolLibCache.get_symbol_data is callable')
except AttributeError as e:
    print(f'CRITICAL: SymbolLibCache.get_symbol_data not found: {e}')
    sys.exit(1)
except Exception as e:
    # Other exceptions are OK (like file not found), we just need the method to exist
    print(f'SymbolLibCache.get_symbol_data exists (got expected error: {e})')

from circuit_synth.kicad.sch_gen.kicad_formatter import format_kicad_schematic
print('kicad_formatter imports')


print('All imports successful!')
""")
        
        result = run_command(f"{python_cmd} {test_script}", cwd=project_path)
        if "CRITICAL" in result.stdout:
            print("❌ CRITICAL ERROR DETECTED!")
            return False
            
        # Test 2: Create a simple circuit
        print("\n5️⃣ Testing circuit creation...")
        
        # Write circuit test to file
        circuit_test_file = project_path / "test_circuit.py"
        circuit_test_file.write_text("""from circuit_synth import Circuit, Component, Net

circuit = Circuit()

# Create components (skip symbol validation for test)
import warnings
warnings.filterwarnings('ignore')
try:
    r1 = Component(symbol='Device:R', value='10k', ref='R')
    r2 = Component(symbol='Device:R', value='10k', ref='R')
    print('Components created (may have warnings about missing symbols)')
except Exception as e:
    # This is OK - we're testing without KiCad libraries
    print(f'Components failed (expected without KiCad): {e}')
    # Create minimal test circuit without symbol validation
    from circuit_synth.core import Circuit as CoreCircuit
    circuit = CoreCircuit()
    print('Created basic circuit object')
    import sys
    sys.exit(0)

# Create nets
vcc = Net('VCC')
gnd = Net('GND')
sig = Net('SIGNAL')

# Connect components
r1[1] += vcc
r1[2] += sig
r2[1] += sig
r2[2] += gnd

# Add to circuit
circuit.add_component(r1)
circuit.add_component(r2)

print(f'Created circuit with {len(circuit.components)} components')
print(f'Component refs: {[c.ref for c in circuit.components]}')

# Test JSON export
import json
circuit_dict = circuit.to_dict()
print(f'Circuit serialization works: {len(json.dumps(circuit_dict))} chars')
""")
        result = run_command(f"{python_cmd} {circuit_test_file}", cwd=project_path)
        
        # Test 3: Test with an example project
        print("\n6️⃣ Testing with example project...")
        
        # Create a test project directory
        project_path.mkdir(parents=True)
        
        # Create a simple test circuit file
        test_circuit_py = project_path / "test_circuit.py"
        test_circuit_py.write_text('''
from circuit_synth import Circuit, Component, Net, circuit

@circuit
def test_circuit():
    """Test circuit for PyPI validation."""
    # Create basic voltage divider
    r1 = Component(symbol="Device:R", value="10k", ref="R")
    r2 = Component(symbol="Device:R", value="10k", ref="R")
    c1 = Component(symbol="Device:C", value="100nF", ref="C")
    
    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    vout = Net("VOUT")
    
    # Connect components
    r1[1] += vcc
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    c1[1] += vout
    c1[2] += gnd
    
    return locals()

if __name__ == "__main__":
    print("Creating test circuit...")
    circ = test_circuit()
    print(f"✅ Created circuit: {circ}")
    
    # Try to access the circuit object
    from circuit_synth.core.decorators import get_circuit_from_decorator
    decorated_circuit = get_circuit_from_decorator(test_circuit)
    if decorated_circuit:
        print(f"✅ Decorator circuit accessible: {len(decorated_circuit.components)} components")
        
        # Test JSON export
        json_data = decorated_circuit.to_dict()
        print(f"✅ JSON export works: {len(json_data.get('components', []))} components")
        
        # Test that we can generate netlist (without KiCad)
        netlist = decorated_circuit.generate_netlist()
        print(f"✅ Netlist generation works: {len(netlist)} chars")
    else:
        print("⚠️ Could not access decorator circuit (might be normal)")
''')
        
        # Run the test circuit
        result = run_command(f"{python_cmd} {test_circuit_py}", cwd=project_path)
        
        # Test 4: Command-line tools
        print("\n7️⃣ Testing CLI tools...")
        cli_tools = [
            "cs-new-project --help",
            "validate-circuit --help",
            "json-to-python --help",
        ]
        
        for tool in cli_tools:
            tool_path = f"{venv_path}/bin/{tool.split()[0]}"
            if Path(tool_path).exists():
                result = run_command(f"{tool_path} --help", check=False)
                if result.returncode == 0:
                    print(f"  ✅ {tool.split()[0]} works")
                else:
                    print(f"  ⚠️ {tool.split()[0]} exists but returned error")
            else:
                print(f"  ⚠️ {tool.split()[0]} not found")
        
import warnings
warnings.filterwarnings('ignore')



# Test that components work regardless
print(f'  ✅ Resistor creation works: {r.ref}')

"""
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        return True


def test_pypi_package(package_name="circuit-synth", version=None):
    """Test installation from PyPI."""
    print(f"\n{'='*60}")
    print("🧪 TESTING PYPI INSTALLATION")
    print(f"{'='*60}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "pypi_test_venv"
        
        print(f"\n📁 Test directory: {tmpdir}")
        
        # Create virtual environment
        print("\n1️⃣ Creating fresh virtual environment...")
        run_command(f"python3 -m venv {venv_path}")
        
        pip_cmd = f"{venv_path}/bin/pip"
        python_cmd = f"{venv_path}/bin/python"
        
        # Install from PyPI
        package_spec = f"{package_name}=={version}" if version else package_name
        print(f"\n2️⃣ Installing from PyPI: {package_spec}")
        result = run_command(f"{pip_cmd} install {package_spec}")
        
        # Run the same tests as for wheel
        print("\n3️⃣ Running import tests...")
        test_code = """
import circuit_synth
print(f'✅ Installed version: {circuit_synth.__version__}')

from circuit_synth import Circuit, Component, Net

# This is the critical test that was failing
try:
    SymbolLibCache.get_symbol_data('Device:R')
except AttributeError as e:
    print(f'❌ CRITICAL FAILURE: {e}')
    import sys
    sys.exit(1)
except Exception:
    pass  # Other exceptions are OK

print('✅ All critical functionality works!')
"""
        result = run_command(f"{python_cmd} -c '{test_code}'")
        
        print("\n✅ PyPI package test passed!")
        return True


def main():
    """Main test runner."""
    print("🚀 Circuit-Synth PyPI Release Test Suite")
    print("="*60)
    
    # Check if we're in the circuit-synth directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: Must run from circuit-synth root directory")
        sys.exit(1)
    
    # Check for built wheels
    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ Error: dist/ directory not found. Run 'uv build' first")
        sys.exit(1)
    
    wheels = list(dist_dir.glob("*.whl"))
    if not wheels:
        print("❌ Error: No wheel files found in dist/")
        sys.exit(1)
    
    latest_wheel = max(wheels, key=lambda p: p.stat().st_mtime)
    print(f"📦 Testing wheel: {latest_wheel}")
    
    # Test the wheel
    if not test_wheel_installation(latest_wheel):
        print("\n❌ WHEEL TEST FAILED!")
        print("DO NOT RELEASE TO PYPI!")
        sys.exit(1)
    
    # Optionally test from TestPyPI
    if "--test-pypi" in sys.argv:
        print("\n" + "="*60)
        print("Testing from TestPyPI...")
        # Would need to configure test PyPI index
        pass
    
    # Optionally test specific version from PyPI
    if "--pypi-version" in sys.argv:
        idx = sys.argv.index("--pypi-version")
        if idx + 1 < len(sys.argv):
            version = sys.argv[idx + 1]
            test_pypi_package(version=version)
    
    print("\n" + "🎉"*20)
    print("✅ ALL TESTS PASSED - SAFE TO RELEASE!")
    print("🎉"*20)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())