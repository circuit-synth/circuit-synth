# Repository Review Command

**Purpose:** Complete repository analysis to identify what's working, what's broken, and what needs attention.

## Usage
```bash
/dev-review-repo [options]
```

## Options
- `--focus=all` - Focus areas: `architecture`, `security`, `performance`, `testing`, `docs`, `circuit-synth`, `all` (default: all)
- `--output-dir=repo-review` - Directory for review outputs (default: repo-review)
- `--run-examples=true` - Test all examples (default: true)
- `--check-security=true` - Security scanning (default: true)

## What This Does

This command analyzes the entire repository and creates structured reports based on your existing repo-review pattern:

### 1. Core Functionality
- **Circuit/Component/Net system** - Does the core work?
- **KiCad integration** - Can it generate working files?
- **Examples validation** - Do the examples actually run?
- **Agent system** - Are the Claude agents functional?
- **Memory bank** - Is the knowledge base organized and useful?

### 2. Code Quality and Migration Cleanup
- **Code that works** vs code that doesn't
- **Python/Rust transition artifacts** - leftover code from language switches
- **Duplicate implementations** - same functionality in multiple places
- **Dead code** from abandoned migrations
- **Inconsistent patterns** - mixing old and new approaches
- **Overly complex functions** that need simplification
- **Missing error handling** that could cause crashes

### 3. Security Issues
- **Exposed secrets** (API keys, passwords)
- **Unsafe code patterns** (eval, exec, shell injection)
- **Vulnerable dependencies** with known CVEs
- **File system vulnerabilities** (path traversal, etc.)

### 4. Performance Problems
- **Slow operations** identified through profiling
- **Memory leaks** or excessive memory usage
- **I/O bottlenecks** in file operations
- **Inefficient algorithms** that need optimization

### 5. Testing Reality
- **What's actually tested** vs what should be tested
- **Broken tests** that need fixing
- **Missing test coverage** in critical areas
- **Test quality** - are tests meaningful or just padding?

### 6. Documentation State
- **Accurate documentation** vs outdated docs
- **Missing API documentation** for public functions
- **Broken examples** in documentation
- **Installation instructions** that actually work

### 7. Dependencies and Integration
- **Outdated packages** that need updates
- **Security vulnerabilities** in dependencies
- **KiCad compatibility** across versions
- **Plugin ecosystem** health and compatibility

## Output Structure

The command generates reports matching your existing repo-review structure:

```
repo-review/
├── 00-executive-summary-and-recommendations.md  # What needs attention most
├── 01-core-functionality-analysis.md            # Does the main stuff work?
├── 02-code-quality-and-cleanup.md               # Python/Rust migration mess
├── 03-security-analysis.md                      # Security problems found
├── 04-performance-analysis.md                   # Slow spots and bottlenecks
├── 05-testing-analysis.md                       # Test coverage and quality
├── 06-documentation-analysis.md                 # Doc accuracy and gaps
├── 07-dependencies-analysis.md                  # Package health and issues
└── findings/                                    # Raw data and logs
```

### Report Format

Each file follows your existing pattern:

```markdown
# [Area] Analysis Review

## Overview
Brief summary of what was found

## Strengths
What's working well in this area

## Areas for Improvement
What needs fixing or attention

## Detailed Findings
Specific issues with examples and locations

## Recommendations
Concrete next steps to improve this area
```

## What It Actually Does

### 1. Test Core Functionality
```bash
# Does the main stuff work?
uv run python examples/example_kicad_project.py
uv run python -c "from circuit_synth import Circuit, Component, Net"

# Are examples broken?
find examples/ -name "*.py" -exec python -m py_compile {} \;

# KiCad integration working?
kicad-cli version
```

### 2. Find Python/Rust Migration Mess
```bash
# Look for duplicate implementations
find . -name "*.py" -exec grep -l "rust_modules\|rust_integration" {} \;
find . -name "*.rs" 2>/dev/null

# Find dead code patterns
grep -r "TODO.*rust\|FIXME.*rust\|deprecated.*rust" --include="*.py" .
grep -r "import.*rust\|from.*rust" --include="*.py" .

# Look for inconsistent patterns
grep -r "class.*Component" --include="*.py" src/ | wc -l
grep -r "def.*component" --include="*.py" src/ | wc -l
```

### 3. Security Scan
```bash
# Look for secrets
grep -r "api[_-]key\|password\|secret\|token" --include="*.py" .

# Dangerous patterns
grep -r "eval\|exec\|subprocess\|os\.system" --include="*.py" .

# Dependency vulnerabilities
safety check
bandit -r src/
```

### 4. Performance Check
```bash
# Profile the main example
python -m cProfile examples/example_kicad_project.py

# Find slow functions
grep -r "time\.sleep\|threading\|asyncio" --include="*.py" src/
```

### 5. Test Reality Check
```bash
# What tests exist?
find tests/ -name "*.py" | wc -l

# Do they pass?
uv run pytest tests/ --tb=short

# Coverage gaps
uv run pytest --cov=circuit_synth --cov-report=term-missing
```

### 6. Documentation Audit
```bash
# Outdated docs
find . -name "README.md" -exec grep -l "rust\|Rust" {} \;

# Missing docs
python -c "
import circuit_synth
import inspect
for name, obj in inspect.getmembers(circuit_synth):
    if inspect.isclass(obj) and not obj.__doc__:
        print(f'Missing docs: {name}')
"
```

### 7. Dependency Health
```bash
# Outdated packages
pip list --outdated

# Vulnerabilities
pip-audit

# Rust leftovers
find . -name "Cargo.toml" -o -name "*.rs"
```

## Special Focus Areas for This Repo

### Python/Rust Migration Cleanup
Since this repo went Python → Rust → Python, it specifically looks for:
- **Duplicate implementations** of the same functionality
- **Dead Rust code** that's no longer used
- **Inconsistent patterns** where some code uses old style, some new
- **Import confusion** between Python and Rust versions
- **Build artifacts** left over from Rust attempts

### Circuit-Synth Specific Issues
- **KiCad integration breaks** - does it actually generate working files?
- **Component database issues** - are JLCPCB lookups working?
- **Agent system problems** - are Claude agents functional?
- **Memory bank organization** - is knowledge findable and accurate?
- **Example validation** - do the examples actually run and work?

## Example Usage

```bash
# Full repository review
/dev-review-repo

# Focus on specific area
/dev-review-repo --focus=security

# Skip example testing (faster)
/dev-review-repo --run-examples=false

# Focus on Python/Rust cleanup
/dev-review-repo --focus=code-quality
```

## What You Get

After running, you'll have a `repo-review/` directory with markdown files that tell you:

1. **What's broken** and needs immediate fixing
2. **What's working well** and should be left alone  
3. **Where the Python/Rust migration left a mess** that needs cleanup
4. **Security issues** that need attention
5. **Performance bottlenecks** slowing things down
6. **Test gaps** where coverage is missing
7. **Documentation problems** where docs are wrong or missing
8. **Dependency issues** with outdated or vulnerable packages

Each report is focused on **actionable findings** rather than abstract metrics or grades. The goal is to give you a clear picture of what actually needs work.

---

**This command creates a practical repository review focused on finding real issues and providing actionable recommendations for circuit-synth projects.**