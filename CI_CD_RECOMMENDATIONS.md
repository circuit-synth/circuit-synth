# CI/CD Configuration Recommendations for circuit-synth

## Current Test Suite Analysis

The circuit-synth test suite has multiple test categories with different requirements:

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Pure Python logic tests
   - No external dependencies
   - **Should run in CI:** ✅ YES
   - **Target:** 100% pass rate

2. **Integration Tests** (`tests/integration/`)
   - File I/O operations
   - Library integration
   - **Should run in CI:** ✅ YES (with caveats)
   - **Target:** 95%+ pass rate

3. **E2E Tests** (`tests/e2e/`)
   - Requires KiCad CLI tools
   - External tool dependencies
   - **Should run in CI:** ⚠️ CONDITIONAL
   - **Recommendation:** Separate job with KiCad installed

4. **Bidirectional Tests** (`tests/bidirectional/`)
   - KiCad file generation/parsing
   - May require KiCad environment
   - **Should run in CI:** ⚠️ CONDITIONAL
   - **Recommendation:** Separate job or nightly builds

5. **PCB Generation Tests** (`tests/pcb_generation/`)
   - PCB file manipulation
   - Requires KiCad PCB API
   - **Should run in CI:** ⚠️ CONDITIONAL
   - **Recommendation:** Separate job with KiCad

## Recommended CI/CD Strategy

### Phase 1: Core CI (Fast, Always Run)

**Run on every PR and commit**

```yaml
name: Core Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run unit tests only
        run: |
          uv run pytest tests/unit/ -v --tb=short
      - name: Check coverage
        run: |
          uv run pytest tests/unit/ --cov=circuit_synth --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests-basic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run integration tests (no KiCad)
        run: |
          uv run pytest tests/integration/ \
            -v --tb=short \
            -m "not requires_kicad"
```

**Requirements:**
- Unit tests MUST pass 100%
- Integration tests should pass 95%+
- Fast execution (< 5 minutes)

### Phase 2: Extended Tests (Slower, Conditional)

**Run on PR approval or nightly**

```yaml
name: Extended Tests

on:
  pull_request:
    types: [labeled]
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  kicad-tests:
    runs-on: ubuntu-latest
    if: contains(github.event.pull_request.labels.*.name, 'test-with-kicad')
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install KiCad
        run: |
          sudo add-apt-repository --yes ppa:kicad/kicad-8.0-releases
          sudo apt update
          sudo apt install --install-recommends kicad kicad-cli -y
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run E2E tests
        run: |
          uv run pytest tests/e2e/ -v --tb=short
      - name: Run bidirectional tests
        run: |
          uv run pytest tests/bidirectional/ -v --tb=short
      - name: Run PCB generation tests
        run: |
          uv run pytest tests/pcb_generation/ -v --tb=short
```

### Phase 3: Full Test Suite (Nightly)

**Run complete test suite overnight**

```yaml
name: Nightly Full Test Suite

on:
  schedule:
    - cron: '0 3 * * *'  # 3 AM daily
  workflow_dispatch:  # Manual trigger

jobs:
  full-suite:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install KiCad
        run: |
          sudo add-apt-repository --yes ppa:kicad/kicad-8.0-releases
          sudo apt update
          sudo apt install --install-recommends kicad kicad-cli -y
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run ALL tests
        run: |
          uv run pytest tests/ \
            -v --tb=short \
            --junit-xml=test-results.xml \
            --html=test-report.html
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            test-results.xml
            test-report.html
      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "Nightly tests failed! Check GitHub Actions for details."
            }
```

## Test Markers Strategy

Add pytest markers to categorize tests:

```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (fast, no I/O)",
    "integration: Integration tests (file I/O allowed)",
    "e2e: End-to-end tests (external tools)",
    "requires_kicad: Requires KiCad CLI tools",
    "requires_api: Requires external API access",
    "slow: Slow running tests (>5 seconds)",
]
```

Then mark tests appropriately:

```python
import pytest

@pytest.mark.unit
def test_circuit_creation():
    """Fast unit test"""
    pass

@pytest.mark.integration
@pytest.mark.requires_kicad
def test_kicad_export():
    """Requires KiCad CLI"""
    pass
```

## Pre-commit Hooks

Add local pre-commit checks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: unit-tests
        name: Run unit tests
        entry: uv run pytest tests/unit/ -x
        language: system
        pass_filenames: false
        always_run: true
```

## Current Test Status Requirements

### Before Enabling CI

**Priority 1: Fix Unit Tests** (CRITICAL)
- Unit tests MUST reach 100% pass rate
- These are the foundation for CI/CD
- No external dependencies = no excuses

**Current unit test issues to fix:**
- `AttributeError` errors (API compatibility)
- `TypeError` errors (API signature changes)
- `AssertionError` errors (logic bugs)
- Missing mock data/fixtures

**Priority 2: Categorize Integration Tests**
- Mark tests that require KiCad: `@pytest.mark.requires_kicad`
- Mark tests that require external APIs: `@pytest.mark.requires_api`
- Ensure basic integration tests pass without KiCad

**Priority 3: Document Known Failures**
- XFail tests with GitHub issues: `@pytest.mark.xfail(reason="Issue #XXX")`
- Skip tests not yet implemented: `@pytest.mark.skip(reason="Not implemented")`
- Track progress toward 100% pass rate

## Recommended Implementation Order

1. **Week 1: Unit Test Cleanup**
   - Fix all unit test failures
   - Add proper mocking where needed
   - Achieve 100% unit test pass rate

2. **Week 2: Integration Test Categorization**
   - Add pytest markers
   - Separate KiCad-dependent tests
   - Document test requirements

3. **Week 3: CI/CD Setup**
   - Implement Phase 1 (Core CI)
   - Set up code coverage reporting
   - Add status badges to README

4. **Week 4: Extended Testing**
   - Implement Phase 2 (KiCad tests)
   - Set up nightly builds
   - Add test result notifications

## Success Metrics

### Short-term (1 month)
- ✅ 100% unit test pass rate
- ✅ Core CI running on all PRs
- ✅ Code coverage > 80%

### Medium-term (3 months)
- ✅ Integration tests categorized and passing
- ✅ E2E tests running in CI
- ✅ Nightly full test suite

### Long-term (6 months)
- ✅ All tests passing or explicitly xfail/skip with issues
- ✅ Automated deployment on passing tests
- ✅ Test coverage > 90%

## Additional Recommendations

### Test Data Management
- Use `pytest.fixture` for test data
- Store reference KiCad files in `tests/test_data/`
- Use `tmp_path` fixture for temporary files

### Performance
- Keep unit tests under 0.1s each
- Keep integration tests under 1s each
- Use pytest-xdist for parallel execution

### Documentation
- Add docstrings to all tests explaining what they validate
- Document test requirements in test module docstrings
- Keep test failure reports up to date

## Test Failure Report Generation

Use the provided `parse_test_results.py` script to generate comprehensive failure reports:

```bash
# Run tests and capture output
uv run pytest tests --tb=short -v 2>&1 | tee test_results_full.txt

# Generate failure reports
python parse_test_results.py

# Review reports
ls test_failure_reports/
```

This creates:
- `SUMMARY.md` - Overall test health
- `*_failures.md` - Category-specific reports
- `unit_failures/` - Detailed unit test failure analysis

## Conclusion

The key to successful CI/CD is:
1. **Start small** - Unit tests only at first
2. **Be strict** - 100% pass rate required
3. **Expand gradually** - Add test categories as they stabilize
4. **Document everything** - Track progress and issues
5. **Automate notifications** - Know when things break

With this strategy, circuit-synth can have a robust CI/CD pipeline that catches bugs early while not being blocked by environment-dependent tests.
