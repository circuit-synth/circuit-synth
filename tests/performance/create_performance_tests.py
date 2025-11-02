#!/usr/bin/env python3
"""Generate performance benchmark tests."""
from pathlib import Path

tests = [
    {
        "num": "01",
        "name": "small_circuit",
        "title": "Small Circuit Performance",
        "description": "10-50 components",
        "circuit_code": '''#!/usr/bin/env python3
"""Small circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="small_circuit")
def small_circuit():
    """Small circuit with 20 resistors."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create 20 resistors
    for i in range(1, 21):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += vcc
        r[2] += gnd

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = small_circuit()
    circuit_obj.generate_kicad_project(project_name="small_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Small circuit generated in {elapsed:.2f}s")
''',
        "timeout": 30,
        "max_time": 10.0,
    },
    {
        "num": "02",
        "name": "medium_circuit",
        "title": "Medium Circuit Performance",
        "description": "100-500 components",
        "circuit_code": '''#!/usr/bin/env python3
"""Medium circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="medium_circuit")
def medium_circuit():
    """Medium circuit with 200 components."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create 200 resistors
    for i in range(1, 201):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += vcc
        r[2] += gnd

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = medium_circuit()
    circuit_obj.generate_kicad_project(project_name="medium_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Medium circuit generated in {elapsed:.2f}s")
''',
        "timeout": 60,
        "max_time": 30.0,
    },
    {
        "num": "03",
        "name": "large_circuit",
        "title": "Large Circuit Performance",
        "description": "1000+ components",
        "circuit_code": '''#!/usr/bin/env python3
"""Large circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="large_circuit")
def large_circuit():
    """Large circuit with 1000 components."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create 1000 resistors
    for i in range(1, 1001):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += vcc
        r[2] += gnd

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = large_circuit()
    circuit_obj.generate_kicad_project(project_name="large_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Large circuit generated in {elapsed:.2f}s")
''',
        "timeout": 120,
        "max_time": 60.0,
    },
    {
        "num": "04",
        "name": "deep_hierarchy",
        "title": "Deep Hierarchy Performance",
        "description": "10+ hierarchy levels",
        "circuit_code": '''#!/usr/bin/env python3
"""Deep hierarchy circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="level_10")
def level_10(sig_in, sig_out):
    r = Component(symbol="Device:R", ref="R10", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_out

@circuit(name="level_9")
def level_9(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_9")
    r = Component(symbol="Device:R", ref="R9", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_10(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_8")
def level_8(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_8")
    r = Component(symbol="Device:R", ref="R8", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_9(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_7")
def level_7(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_7")
    r = Component(symbol="Device:R", ref="R7", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_8(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_6")
def level_6(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_6")
    r = Component(symbol="Device:R", ref="R6", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_7(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_5")
def level_5(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_5")
    r = Component(symbol="Device:R", ref="R5", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_6(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_4")
def level_4(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_4")
    r = Component(symbol="Device:R", ref="R4", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_5(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_3")
def level_3(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_3")
    r = Component(symbol="Device:R", ref="R3", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_4(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="level_2")
def level_2(sig_in, sig_out):
    sig_mid = Net(name="SIG_MID_2")
    r = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r[1] += sig_in
    r[2] += sig_mid
    level_3(sig_in=sig_mid, sig_out=sig_out)

@circuit(name="deep_hierarchy")
def deep_hierarchy():
    """Deep hierarchy with 10 levels."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig_in = Net(name="SIG_IN")

    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r1[1] += vcc
    r1[2] += sig_in

    level_2(sig_in=sig_in, sig_out=gnd)

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = deep_hierarchy()
    circuit_obj.generate_kicad_project(project_name="deep_hierarchy", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Deep hierarchy circuit generated in {elapsed:.2f}s")
''',
        "timeout": 60,
        "max_time": 30.0,
    },
    {
        "num": "05",
        "name": "wide_hierarchy",
        "title": "Wide Hierarchy Performance",
        "description": "50+ subcircuits",
        "circuit_code": '''#!/usr/bin/env python3
"""Wide hierarchy circuit for performance testing."""
from circuit_synth import circuit, Component, Net

# Create 30 subcircuit functions
def create_subcircuit(idx):
    @circuit(name=f"subcircuit_{idx}")
    def subcircuit(sig_in, sig_out):
        r = Component(symbol="Device:R", ref=f"R{idx}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += sig_in
        r[2] += sig_out
    return subcircuit

# Generate subcircuits
subcircuits = [create_subcircuit(i) for i in range(1, 31)]

@circuit(name="wide_hierarchy")
def wide_hierarchy():
    """Wide hierarchy with 30 subcircuits."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Instantiate all 30 subcircuits in parallel
    for i, subcircuit_func in enumerate(subcircuits, 1):
        sig = Net(name=f"SIG_{i}")
        subcircuit_func(sig_in=vcc, sig_out=sig)

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = wide_hierarchy()
    circuit_obj.generate_kicad_project(project_name="wide_hierarchy", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Wide hierarchy circuit generated in {elapsed:.2f}s")
''',
        "timeout": 60,
        "max_time": 30.0,
    },
    {
        "num": "06",
        "name": "complex_routing",
        "title": "Complex Routing Performance",
        "description": "High net density circuit",
        "circuit_code": '''#!/usr/bin/env python3
"""Complex routing circuit for performance testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="complex_routing")
def complex_routing():
    """Circuit with high net density (50 components, 50 nets)."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Create 50 resistors with interconnections
    components = []
    nets = []

    for i in range(1, 51):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        components.append(r)
        net = Net(name=f"NET_{i}")
        nets.append(net)

    # Connect in chain with high density
    for i in range(len(components)):
        if i == 0:
            components[i][1] += vcc
            components[i][2] += nets[i]
        elif i == len(components) - 1:
            components[i][1] += nets[i-1]
            components[i][2] += gnd
        else:
            components[i][1] += nets[i-1]
            components[i][2] += nets[i]

if __name__ == "__main__":
    import time
    start = time.time()
    circuit_obj = complex_routing()
    circuit_obj.generate_kicad_project(project_name="complex_routing", placement_algorithm="hierarchical", generate_pcb=True)
    elapsed = time.time() - start
    print(f"✅ Complex routing circuit generated in {elapsed:.2f}s")
''',
        "timeout": 60,
        "max_time": 30.0,
    },
    {
        "num": "07",
        "name": "memory_usage",
        "title": "Memory Usage Monitoring",
        "description": "Monitor memory during generation",
        "circuit_code": '''#!/usr/bin/env python3
"""Memory usage monitoring test."""
from circuit_synth import circuit, Component, Net
import tracemalloc

@circuit(name="memory_circuit")
def memory_circuit():
    """Circuit for memory monitoring (100 components)."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    for i in range(1, 101):
        r = Component(symbol="Device:R", ref=f"R{i}", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
        r[1] += vcc
        r[2] += gnd

if __name__ == "__main__":
    import time
    tracemalloc.start()
    start = time.time()

    circuit_obj = memory_circuit()
    circuit_obj.generate_kicad_project(project_name="memory_circuit", placement_algorithm="hierarchical", generate_pcb=True)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start

    print(f"✅ Memory circuit generated in {elapsed:.2f}s")
    print(f"   Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"   Peak memory: {peak / 1024 / 1024:.2f} MB")
''',
        "timeout": 60,
        "max_time": 30.0,
    },
]

for test in tests:
    test_dir = Path(f"{test['num']}_{test['name']}")
    test_dir.mkdir(exist_ok=True)

    # Create circuit file
    circuit_file = test_dir / f"{test['name']}.py"
    circuit_file.write_text(test['circuit_code'])

    # Create test file
    test_file = test_dir / f"test_{test['num']}_perf.py"
    test_content = f'''#!/usr/bin/env python3
"""Test {test['num']}: {test['title']}"""
import pytest, subprocess, shutil, time
from pathlib import Path

def test_{test['num']}_performance(request):
    """Test {test['description']}."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "{test['name']}.py"
    output_dir = test_dir / "{test['name']}"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Measure generation time
        start_time = time.time()
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout={test['timeout']})
        elapsed_time = time.time() - start_time

        # Verify generation succeeded
        assert result.returncode == 0, f"Generation failed: {{result.stderr}}"

        # Check performance threshold
        max_time = {test['max_time']}
        assert elapsed_time < max_time, f"Generation took {{elapsed_time:.2f}}s, expected < {{max_time}}s"

        print(f"\\n✅ Test {test['num']} PASSED: {test['title']}")
        print(f"   Generation time: {{elapsed_time:.2f}}s (limit: {{max_time}}s)")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
'''
    test_file.write_text(test_content)

    # Create README
    readme_file = test_dir / "README.md"
    readme_content = f'''# Test {test['num']}: {test['title']}

Performance test for {test['description']}.

```bash
pytest test_*.py -v
```

Performance threshold: {test['max_time']}s
'''
    readme_file.write_text(readme_content)

    print(f"✅ Created Test {test['num']}: {test['title']}")

print("\n✅ All performance benchmark tests created!")
