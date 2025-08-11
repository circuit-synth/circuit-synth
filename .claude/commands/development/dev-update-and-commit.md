# /dev-update-and-commit

Update documentation, run quality checks, and commit changes with proper Git workflow for circuit-synth development.

## Usage
```
/dev-update-and-commit "description of changes"
```

## Description
Automated workflow for maintaining code quality and documentation consistency during circuit-synth development. This command handles the complete development lifecycle from code formatting to documentation updates and Git commits.

## Workflow Steps

### 1. Code Quality & Formatting
```bash
# Format code with consistent styling
black src/ tests/
isort src/ tests/

# Lint code for quality issues
flake8 src/ tests/
mypy src/ --ignore-missing-imports
```

### 2. Documentation Updates
```bash
# Update API documentation
sphinx-build docs/ docs/_build/

# Generate updated examples and usage guides
python tools/maintenance/update_examples_with_stock.py

# Update README if needed
# Update CONTRIBUTING.md with new patterns
```

### 3. Testing & Validation
```bash
# Run comprehensive test suite
uv run pytest --cov=circuit_synth

# Validate critical functionality
./tools/testing/run_all_tests.sh --python-only
```

### 4. Git Workflow
```bash
# Stage changes selectively
git add src/ tests/ docs/ 

# Create descriptive commit message
git commit -m "description: specific changes made

- Details of implementation
- Testing performed
- Breaking changes (if any)

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Command Options

### Basic Usage
```bash
/dev-update-and-commit "Add new component placement algorithm"
```

### Selective Updates
```bash
# Skip certain steps if needed
/dev-update-and-commit "Fix type hints" --skip-tests
/dev-update-and-commit "Update docs only" --docs-only
```

## Prerequisites
- Clean Git working directory (no uncommitted changes)
- All development dependencies installed (`uv sync`)
- KiCad CLI available (for full validation)
- Write permissions to repository

## Quality Checks Performed

### Code Quality
- **Black**: Consistent code formatting
- **isort**: Import statement organization
- **flake8**: Code style and complexity analysis
- **mypy**: Type checking and annotation validation

### Testing
- **Unit tests**: Core functionality validation
- **Integration tests**: External dependency testing
- **Regression tests**: Breaking change detection

### Documentation
- **API docs**: Automatic generation from docstrings
- **Examples**: Updated with current API patterns
- **README**: Consistency with latest features

## Best Practices

### Commit Message Format
```
<type>: <concise description>

<detailed explanation of changes>
<testing performed>
<any breaking changes>

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types of Changes
- **feat**: New feature implementation
- **fix**: Bug fix or error resolution
- **docs**: Documentation updates
- **refactor**: Code restructuring without behavior changes
- **test**: Testing improvements or additions
- **chore**: Maintenance tasks and tooling updates

This command ensures consistent code quality and proper documentation maintenance throughout the development process.