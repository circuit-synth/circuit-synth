# Contributing to Circuit Synth

Thank you for your interest in contributing to Circuit Synth! This guide will help you get started with contributing to the project.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Git

### Getting Started

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/circuit-synth.git
   cd circuit-synth
   ```

2. **Install dependencies (recommended with uv):**
   ```bash
   # Install the project in development mode
   uv pip install -e ".[dev]"
   
   # Install dependencies
   uv sync
   ```

3. **Alternative installation with pip:**
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Code Quality

We maintain high code quality standards using several tools:

```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/
```

### Testing

Run tests to ensure your changes don't break existing functionality:

```bash
# Run tests (recommended with uv)
uv run pytest

# Run tests with coverage
uv run pytest --cov=circuit_synth

# Alternative with pip
pytest
pytest --cov=circuit_synth
```

### Building

To build the package locally:

```bash
# Using uv (recommended)
uv build

# Using traditional tools
python -m build
```

## Project Structure

```
circuit-synth/
├── src/circuit_synth/          # Main package code
│   ├── core/                   # Core circuit functionality
│   ├── kicad/                  # KiCad integration
│   ├── kicad_api/             # KiCad API wrappers
│   ├── pcb/                   # PCB generation
│   └── schematic/             # Schematic generation
├── rust_modules/              # Rust performance modules
├── examples/                  # Usage examples
├── tests/                     # Test files
└── docs/                      # Documentation
```

## Contributing Guidelines

### Reporting Issues

- Use the [GitHub issue tracker](https://github.com/circuitsynth/circuit-synth/issues)
- Search existing issues before creating new ones
- Provide clear reproduction steps and environment details
- Include relevant code snippets and error messages

### Submitting Pull Requests

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, well-documented code
   - Follow existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   # Run the full test suite
   uv run pytest
   
   # Check code quality
   black src/ --check
   isort src/ --check-only
   flake8 src/
   mypy src/
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style

- Follow [PEP 8](https://pep8.org/) Python style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Include type hints for all functions and methods
- Write docstrings for public APIs

### Commit Messages

Use conventional commit format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

## Areas for Contribution

### High Priority Areas

1. **Intelligent Component Placement:**
   - Improve PCB component placement algorithms
   - Add schematic placement intelligence
   - Optimize for signal integrity and thermal considerations

2. **KiCad Integration:**
   - Enhance KiCad API compatibility
   - Improve symbol and footprint library management
   - Add support for newer KiCad versions

3. **Documentation:**
   - Add more examples and tutorials
   - Improve API documentation
   - Create video tutorials

### Other Areas

- Performance optimization
- Test coverage improvement
- CI/CD enhancements
- Platform compatibility (Windows, macOS, Linux)
- Integration with other EDA tools

## Getting Help

- **Documentation:** [https://circuitsynth.readthedocs.io](https://circuitsynth.readthedocs.io)
- **Discussions:** [GitHub Discussions](https://github.com/circuitsynth/circuit-synth/discussions)
- **Issues:** [GitHub Issues](https://github.com/circuitsynth/circuit-synth/issues)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code.

## License

By contributing to Circuit Synth, you agree that your contributions will be licensed under the MIT License that covers the project.

## Recognition

Contributors are recognized in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file and in release notes. Thank you for helping make Circuit Synth better!