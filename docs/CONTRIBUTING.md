# Contributing to Circuit-Synth

Thank you for your interest in contributing to circuit-synth.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
```

2. Install dependencies:
```bash
uv sync
```

3. Run tests:
```bash
./tools/testing/run_full_regression_tests.py
```

4. (Optional) Register Claude Code agents:
```bash
uv run register-agents
```

## Development Workflow

1. Create a feature branch from `develop`
2. Make your changes with tests
3. Run the test suite: `./tools/testing/run_full_regression_tests.py`
4. Submit a pull request to `develop`

## Code Style

- Python: Use `black`, `isort`, `mypy`, `flake8`
- Write tests for new functionality
- Update documentation as needed


## Quick Start Options

### 1. Add a Circuit Example (15 mins)
Create a new example in `examples/` showing a common circuit pattern:

```python
# examples/led_driver.py
from circuit_synth import *

@circuit(name="led_driver")
def led_driver():
    """LED with current limiting resistor."""
    led = Component("Device:LED", ref="D")
    resistor = Component("Device:R", ref="R", value="220")
    
    VCC = Net('VCC')
    GND = Net('GND')
    
    resistor[1] += VCC
    resistor[2] += led[1]  
    led[2] += GND
```

- Component processing (Issue #40) - 97% of generation time
- Netlist processing (Issue #36)
- KiCad parsing (Issue #37)

### 3. Component Search Improvements  
Extend manufacturing integrations in `src/circuit_synth/manufacturing/`:
- Add Digi-Key support
- Improve JLCPCB filtering
- Add alternative component suggestions

## Development Environment Setup

```bash
# Clone and install
git clone https://github.com/shanemattner/circuit-synth.git
cd circuit-synth
uv sync

# Run tests
uv run pytest

```

## Development Workflow

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes following existing patterns
4. Test: `./tools/testing/run_full_regression_tests.py`
5. Format: `black src/ && isort src/`
6. Push and create a pull request

## Testing

```bash
# Run all tests
./tools/testing/run_full_regression_tests.py

# Python tests only
uv run pytest --cov=circuit_synth

# Specific test
uv run pytest tests/unit/test_core_circuit.py -v
```

We follow Test-Driven Development (TDD):
1. Write tests first
2. Make them pass with minimal code
3. Refactor while keeping tests green

## Types of Contributions

### Bug Reports
Include:
- Circuit-synth version
- Minimal reproduction code
- Error messages
- Expected vs actual behavior

### Feature Requests
- Describe the problem being solved
- Provide use cases
- Consider implementation complexity

### Code Contributions
1. Discuss in an issue first
2. Follow code standards (black, mypy, flake8)
3. Add tests for new features
4. Update documentation

## Code Style

- Follow PEP 8 (88 char line length)
- Use type hints for public functions
- Write docstrings for public APIs
- No bare `except` clauses

## Architecture

Circuit-synth uses a JSON-centric architecture:
- **Python → JSON → KiCad** for circuit generation
- **KiCad → JSON → Python** for round-trip conversion
- JSON serves as the canonical data format

Key directories:
- `src/circuit_synth/core/` - Core circuit classes
- `src/circuit_synth/kicad/` - KiCad file I/O
- `src/circuit_synth/manufacturing/` - JLCPCB integration



2. Use pure Python for all functionality
3. Focus on readability and maintainability

High-impact areas:
- Component processing (97% of time)
- Netlist generation
- KiCad parsing

## Pull Request Guidelines

- Reference related issues ("Fixes #123")
- Include tests for new features
- Update documentation as needed
- Ensure all CI checks pass

We review PRs within 48 hours and provide constructive feedback.

## Getting Help

- [GitHub Issues](https://github.com/circuit-synth/circuit-synth/issues) - Bug reports
- [GitHub Discussions](https://github.com/circuit-synth/circuit-synth/discussions) - Questions
- Claude Code agents - Use `contributor` agent for guidance

## Code of Conduct

We are committed to a welcoming environment for all contributors.
- Be respectful and constructive
- Accept feedback gracefully
- Focus on what's best for the community

## Recognition

Significant contributors are:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

Thank you for contributing to Circuit-Synth!