# Circuit-Synth Release Process

## Overview

This document outlines the official release process for Circuit-Synth, ensuring consistent, high-quality releases with proper testing and documentation.

## Pre-Release Requirements

### 1. Code Quality Validation

**Mandatory Regression Tests** - ALL must pass before release:

```bash
# 1. Core Circuit Logic Test
uv run python examples/example_kicad_project.py

# 2. Web Dashboard Smoke Test (basic startup)
uv run circuit-synth-web  # Verify startup, then terminate

# 3. LLM Analysis Pipeline Test
uv run python -m circuit_synth.intelligence.scripts.llm_circuit_analysis --help

# 4. PRIMARY REGRESSION TEST - Puppeteer E2E
cd tests/e2e/puppeteer && npm test

# 5. Unit Tests
uv run pytest tests/unit/test_core_circuit.py -v

# 6. Security Tests
uv run pytest tests/security/test_security_integration.py -v
```

**Code Quality Checks**:
```bash
# Format and lint
black src/
isort src/
flake8 src/
mypy src/

# Test coverage
uv run pytest --cov=circuit_synth
```

### 2. Version Management

**Semantic Versioning (SemVer)**:
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

**Version Update Process**:
1. Update version in `pyproject.toml`
2. Update version in `src/circuit_synth/__init__.py`
3. Update CHANGELOG.md with release notes

### 3. Documentation Requirements

**Required Documentation**:
- [ ] README.md updated with latest features
- [ ] CHANGELOG.md entries for this release
- [ ] API documentation current (if public APIs changed)
- [ ] Examples tested and working
- [ ] Docker integration tested

## Release Types

### Development Releases (Alpha/Beta)

**Purpose**: Testing new features with community feedback

**Process**:
```bash
# Create release branch
git checkout -b release/v1.2.0-alpha.1
git push -u origin release/v1.2.0-alpha.1

# Run regression tests
# ... execute all mandatory tests above ...

# Tag and release
git tag v1.2.0-alpha.1
git push origin v1.2.0-alpha.1

# Create GitHub release (marked as pre-release)
gh release create v1.2.0-alpha.1 --prerelease --title "v1.2.0-alpha.1" --notes-file RELEASE_NOTES.md
```

### Stable Releases

**Purpose**: Production-ready releases for general use

**Process**:
```bash
# Ensure main branch is ready
git checkout main
git pull origin main

# Final regression test suite
# ... execute ALL mandatory tests above ...

# Merge release branch (if using)
git merge release/v1.2.0
git push origin main

# Tag stable release
git tag v1.2.0
git push origin v1.2.0

# Create GitHub release
gh release create v1.2.0 --title "Circuit-Synth v1.2.0" --notes-file RELEASE_NOTES.md

# Build and publish to PyPI (if configured)
uv build
# twine upload dist/*  # When PyPI publishing is set up
```

## Release Testing Matrix

### Feature-Specific Testing

Based on changes in the release, test relevant functionality:

**Recent ratsnest generation feature**:
```bash
# Test ratsnest generation
cd examples/
uv run python example_kicad_project.py
# Verify generated .kicad_pcb contains ratsnest connections
```

**KiCad integration changes**:
```bash
# Test complete KiCad workflow
uv run python examples/example_kicad_project.py
# Open generated project in KiCad to verify compatibility
```

**Docker updates**:
```bash
# Test Docker build and functionality
docker build -t circuit-synth-test .
docker run --rm circuit-synth-test python examples/example_kicad_project.py
```

### Platform Testing

**Supported Platforms**:
- macOS (primary development)
- Linux (Docker primary)
- Windows (via Docker)

**Docker Testing**:
```bash
# Test production Docker image
docker-compose -f docker/docker-compose.production.yml up --build
```

## Release Checklist

### Pre-Release Preparation

- [ ] All regression tests pass
- [ ] Version numbers updated in all files
- [ ] CHANGELOG.md updated with release notes
- [ ] README.md reflects current feature set
- [ ] Documentation is current
- [ ] Memory bank updated with release information
- [ ] No debug files or temporary outputs in repository

### Release Execution

- [ ] Create release branch (for major releases)
- [ ] Final regression test execution
- [ ] Git tag created with proper version
- [ ] GitHub release created with release notes
- [ ] Docker images built and tested
- [ ] PyPI package published (when configured)

### Post-Release

- [ ] Release announcement (if applicable)
- [ ] Update project status in README
- [ ] Archive release branch (if used)
- [ ] Update memory bank with release completion
- [ ] Plan next release milestones

## Branch Strategy

### Main Branch Protection
- **Never commit directly to main** unless explicitly needed
- **All development via feature branches**
- **Pull requests required for main branch changes**

### Release Branches
```bash
# For major/minor releases
release/v1.2.0

# For patches
hotfix/v1.2.1
```

### Branch Naming Convention
```bash
feature/ratsnest-generation
fix/security-validation
release/v1.2.0
hotfix/v1.2.1
```

## Quality Gates

### Automated Testing Requirements

**All releases must pass**:
1. **Core functionality**: `examples/example_kicad_project.py`
2. **Web dashboard**: Basic startup test
3. **LLM integration**: CLI availability test
4. **E2E regression**: Full Puppeteer test suite
5. **Unit tests**: Core circuit logic validation
6. **Security tests**: Authentication and validation

### Manual Verification Requirements

**Major releases**:
- [ ] KiCad project opens correctly in KiCad
- [ ] Generated PCB files are valid
- [ ] Docker integration works end-to-end
- [ ] Documentation examples are current

**All releases**:
- [ ] No temporary/debug files included
- [ ] License headers are correct
- [ ] Version consistency across all files

## Release Notes Template

```markdown
# Circuit-Synth v1.2.0

## New Features
- Feature 1: Description and benefit
- Feature 2: Description and benefit

## Improvements
- Enhancement 1: What was improved
- Enhancement 2: Performance or usability improvement

## Bug Fixes
- Fix 1: What was broken and how it's fixed
- Fix 2: Security or stability fix

## Breaking Changes
- Change 1: What changed and migration path
- Change 2: API changes and upgrade instructions

## Technical Notes
- Dependencies updated
- Performance improvements
- Internal refactoring (if user-visible)

## Testing
All regression tests pass:
- ✅ Core circuit logic
- ✅ Web dashboard startup
- ✅ LLM analysis pipeline
- ✅ Puppeteer E2E tests
- ✅ Unit test suite
- ✅ Security validation

## Installation
```bash
pip install circuit-synth==1.2.0
# or
uv add circuit-synth==1.2.0
```

## Docker
```bash
docker pull circuit-synth:v1.2.0
```
```

## Rollback Procedures

### If Release Issues Discovered

**Immediate Actions**:
1. **Document the issue** in memory bank and GitHub issues
2. **Assess severity**: Critical vs. minor issues
3. **Communication**: Update release notes with known issues

**Critical Issues**:
```bash
# Remove problematic release
gh release delete v1.2.0
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0

# Create hotfix
git checkout -b hotfix/v1.2.1 v1.1.0
# Apply fixes...
# Follow release process for v1.2.1
```

**Minor Issues**:
- Document in release notes
- Plan fix for next patch release
- Provide workarounds if available

## Automation Opportunities

### Future Improvements
- **GitHub Actions**: Automate regression testing on PR
- **Automated versioning**: Based on conventional commits
- **PyPI publishing**: Automated on release tag
- **Docker registry**: Automated image building and publishing
- **Release notes**: Generated from commit messages and PRs

### Current Manual Process
This process is currently manual to ensure quality and control during the open source transition. Automation will be added incrementally as the project matures.

---

**Document Version**: 1.0  
**Last Updated**: 2025-07-28  
**Next Review**: After first official release