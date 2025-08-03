# Contributing to Circuit-Synth

**🚀 NEW: We've built the most contributor-friendly EE design tool ever!**

Circuit-synth is specifically designed to work with **Claude Code** for maximum developer productivity. We've created comprehensive onboarding resources and specialized AI agents to help you contribute effectively.

## 🤖 Quick Start (Recommended)

**For the best experience, use [Claude Code](https://claude.ai/code) with our specialized agents:**

```bash
# 1. Clone and setup
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync

# 2. Register our specialized Claude Code agents
uv run register-agents

# 3. Start with our comprehensive contributor guides
# Read: Contributors/README.md
```

**Why Claude Code?** We've built specialized agents that understand circuit-synth architecture, guide you through Rust integration, help with TDD workflows, and automate code reviews.

## 📚 Comprehensive Contributor Resources

**Start here for the complete experience:**
- **[Contributors/README.md](../Contributors/README.md)** - Main onboarding guide (START HERE!)
- **[Contributors/Architecture-Overview.md](../Contributors/Architecture-Overview.md)** - Technical architecture
- **[Contributors/Development-Setup.md](../Contributors/Development-Setup.md)** - Detailed setup
- **[Contributors/Claude-Code-Workflow.md](../Contributors/Claude-Code-Workflow.md)** - Our actual development workflow
- **[Contributors/Rust-Integration-Guide.md](../Contributors/Rust-Integration-Guide.md)** - High-impact Rust contributions
- **[Contributors/Testing-Guidelines.md](../Contributors/Testing-Guidelines.md)** - TDD approach
- **[Contributors/Claude-Code-Agents-and-Commands.md](../Contributors/Claude-Code-Agents-and-Commands.md)** - All agents and commands

## 🎯 High-Impact Opportunities

**Rust Integration (Perfect for Major Impact):**
- **[Issue #36](https://github.com/circuit-synth/circuit-synth/issues/36)**: Netlist processor (HIGH PRIORITY)
- **[Issue #37](https://github.com/circuit-synth/circuit-synth/issues/37)**: KiCad integration compilation (HIGH PRIORITY)
- **[Issue #40](https://github.com/circuit-synth/circuit-synth/issues/40)**: Component processing (97% performance impact!)

**Easy Entry Points:**
- Examples and tutorials for other EEs
- Component library expansion
- Test coverage improvements
- Documentation enhancements

## 🤖 Alternative AI Tools

While optimized for Claude Code, other tools work too:
- **ChatGPT/GPT-4**: Read our `Contributors/` docs for context
- **Cursor/GitHub Copilot**: Good code completion with our patterns  
- **Any LLM**: Extensive documentation designed for AI agent consumption

---

## Traditional Contributing Guide

### Development Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shanemattner/circuit-synth.git
   cd circuit-synth
   ```

2. **Install dependencies with uv** (recommended):
   ```bash
   # Install UV if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install project in development mode
   uv sync
   ```

3. **Optional: Enable Rust acceleration** (6x performance boost):
   ```bash
   # Install Rust toolchain if not already installed
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source ~/.cargo/env
   
   # Install maturin for Python-Rust bindings
   pip install maturin
   
   # Compile Rust modules for performance acceleration
   cd rust_modules/rust_kicad_integration
   maturin develop --release
   cd ../..
   ```

4. **Verify installation** (with optional Rust acceleration):
   ```bash
   uv run python examples/example_kicad_project.py
   # If Rust is compiled, you'll see performance improvements in the logs
   ```

### Development Workflow

**Branch Strategy**:
- **Never commit directly to main** unless explicitly needed
- Create feature branches: `feature/ratsnest-generation`
- Create fix branches: `fix/security-validation`
- Use descriptive branch names

**Testing Requirements**:
Before any contribution, ensure all regression tests pass:

```bash
# 1. Core Circuit Logic Test
uv run python examples/example_kicad_project.py

# 2. Web Dashboard Smoke Test
uv run circuit-synth-web  # Verify startup, then terminate

# 3. Core Import Test
uv run python -c "import circuit_synth; print('Core imports working')"

# 4. Unit Tests
uv run pytest tests/unit/test_core_circuit.py -v

# 5. Security Tests (if available)
uv run pytest tests/security/test_security_integration.py -v
```

## Types of Contributions

### 🐛 Bug Reports

**Before submitting**:
- Search existing issues to avoid duplicates
- Test with the latest version
- Include reproduction steps

**Include in your report**:
- Circuit-synth version (`import circuit_synth; print(circuit_synth.__version__)`)
- Python version and operating system
- KiCad version (if relevant)
- Minimal code example that reproduces the issue
- Expected vs. actual behavior
- Error messages and stack traces

### 💡 Feature Requests

**Good feature requests**:
- Clearly describe the problem you're trying to solve
- Explain how it fits with Circuit-Synth's goals
- Consider implementation complexity
- Provide use cases and examples

### 🔧 Code Contributions

**Development Process**:

1. **Create an issue** discussing your planned changes
2. **Fork the repository** and create a feature branch
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Submit a pull request**

**Code Standards**:

```bash
# Format code
uv run black src/
uv run isort src/

# Lint code
uv run flake8 src/
uv run mypy src/

# Run tests
uv run pytest
```

## Development Guidelines

### Code Style

- **Follow PEP 8** with line length of 88 characters
- **Use type hints** for all public functions
- **Write docstrings** for classes and public methods
- **No bare `except` clauses** - always specify exception types

### Testing

**Test Categories**:
- **Unit tests**: Individual component testing
- **Integration tests**: Multi-component workflows
- **Functional tests**: End-to-end scenarios
- **Regression tests**: Prevent functionality breakdown

**Writing Tests**:
```python
import pytest
from circuit_synth import Circuit, Component, Net

def test_basic_circuit_creation():
    """Test that circuits can be created and components added."""
    circuit = Circuit("test_circuit")
    
    # Add test logic...
    assert len(circuit.components) == 0
    
    # Add component
    resistor = Component("Device:R", ref="R", value="1k")
    circuit.add_component(resistor)
    
    assert len(circuit.components) == 1
```

### Documentation

**Documentation Requirements**:
- Update README.md for user-facing changes
- Add docstrings for new public APIs
- Include code examples for new features
- Update relevant documentation files

**Example Documentation**:
```python
def generate_kicad_project(self, project_name: str, 
                          generate_pcb: bool = True,
                          force_regenerate: bool = True) -> None:
    """
    Generate a complete KiCad project from this circuit.
    
    Args:
        project_name: Name for the generated KiCad project
        generate_pcb: Whether to generate PCB file (default: True)
        force_regenerate: Force regeneration of existing files (default: True)
        
    Example:
        >>> circuit = esp32s3_simple()
        >>> circuit.generate_kicad_project("my_project")
        
    Raises:
        CircuitError: If circuit validation fails
        FileNotFoundError: If required libraries are missing
    """
```

## Project Architecture

### Core Components

- **`src/circuit_synth/core/`**: Core circuit design functionality
- **`src/circuit_synth/kicad/`**: KiCad file format handling
- **`src/circuit_synth/pcb/`**: PCB generation and layout
- **`src/circuit_synth/kicad_api/`**: Low-level KiCad API integration

### Key Design Principles

1. **Simple Python Code**: No special DSL - just Python classes
2. **Transparent Output**: Generated KiCad files are human-readable
3. **Bidirectional**: Support import from existing KiCad projects
4. **Professional Workflow**: Integrate with existing EE processes

### Adding New Features

**Feature Development Process**:

1. **Design Phase**:
   - Create design document explaining the feature
   - Consider impact on existing APIs
   - Plan backward compatibility

2. **Implementation Phase**:
   - Start with failing tests (TDD approach)
   - Implement minimal functionality
   - Iterate with feedback

3. **Integration Phase**:
   - Ensure all regression tests pass
   - Update examples if needed
   - Document new functionality

## Submitting Changes

### Pull Request Guidelines

**PR Requirements**:
- **Descriptive title** and detailed description
- **Reference related issues** (e.g., "Fixes #123")
- **Include tests** for new functionality
- **Update documentation** if needed
- **All CI checks pass**

**PR Template**:
```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that breaks existing functionality)
- [ ] Documentation update

## Testing
- [ ] All regression tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Changes are backward compatible (or breaking changes documented)
```

### Review Process

**What to Expect**:
- Initial feedback within 48 hours
- Constructive code review focusing on:
  - Code quality and maintainability
  - Test coverage and reliability
  - Documentation completeness
  - Performance implications

**Addressing Feedback**:
- Respond to all review comments
- Make requested changes in additional commits
- Ask questions if feedback is unclear
- Mark conversations as resolved when addressed

## Community Guidelines

### Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, nationality, or other similar characteristics.

**Expected Behavior**:
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

**Unacceptable Behavior**:
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Communication

**Preferred Channels**:
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Pull Requests**: Code review and discussion

**Communication Guidelines**:
- Be respectful and constructive
- Stay on topic
- Help others learn and grow
- Assume good intentions

## Recognition

Contributors who make significant contributions will be:
- Added to the CONTRIBUTORS.md file
- Mentioned in release notes
- Credited in documentation where appropriate

Thank you for helping make Circuit-Synth better! 🚀

---

**Questions?** Feel free to ask in [GitHub Discussions](https://github.com/shanemattner/circuit-synth/discussions) or open an issue.