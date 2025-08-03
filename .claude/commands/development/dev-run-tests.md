---
allowed-tools: Bash(uv*), Bash(pytest*), Bash(open*)
description: Run test suite with optional formatting (dev dependencies required)
---

Run test suite for circuit-synth project.

**Prerequisites:** Install dev dependencies first:
```bash
uv pip install -e ".[dev]"
```

**Test workflow:**

1. **Run tests first (most important):**
   ```bash
   uv run pytest --cov=circuit_synth -v
   ```

2. **Optional: Format code (if making changes):**
   ```bash
   uv run black src/
   uv run isort src/
   ```

3. **Optional: Check linting (expect many warnings):**
   ```bash
   uv run flake8 src/  # Will show style issues - not blocking
   ```

4. **Generate coverage report:**
   ```bash
   uv run pytest --cov=circuit_synth --cov-report=html
   open htmlcov/index.html  # View coverage in browser
   ```

**Expected Results:**
- ✅ Tests should pass (~158 tests, ~3 skipped)
- ⚠️ Flake8 will show many style warnings (known issue)
- ⚠️ MyPy has type checking errors (known issue)
- 📊 Coverage around 24% (room for improvement)

**Note:** Focus on test passing rather than linting. The codebase has known style issues that don't affect functionality.