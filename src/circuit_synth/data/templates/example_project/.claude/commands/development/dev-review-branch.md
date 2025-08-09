# Development Branch Review Command

**Purpose:** Comprehensive branch analysis for code quality, security, performance, and risk assessment before merging to main. Specialized for circuit-synth development workflows.

## Usage
```bash
/dev-review-branch [options]
```

## Options
- `--target=main` - Target branch to compare against (default: main)
- `--depth=full` - Review depth: `quick`, `standard`, `full`, `forensic` (default: standard)
- `--focus=security` - Focus areas: `security`, `performance`, `architecture`, `circuit-synth`, `dependencies`, `all` (default: all)
- `--format=markdown` - Output format: `markdown`, `json`, `summary`, `checklist` (default: markdown)
- `--threshold=medium` - Risk threshold: `low`, `medium`, `high`, `critical` (default: medium)
- `--history=10` - Number of commits to analyze in detail (default: 10)
- `--diff-context=5` - Lines of context for code analysis (default: 5)
- `--auto-fix=false` - Suggest automated fixes for detected issues (default: false)
- `--interactive=false` - Interactive mode for detailed issue exploration (default: false)

## What This Does

This command performs a comprehensive analysis of the current branch against the target branch, examining:

### 1. High-Impact Changes Analysis
- **Architectural changes** that could break system functionality
- **API modifications** that might affect backward compatibility  
- **Dependency changes** in package files (pyproject.toml, uv.lock, Cargo.toml)
- **Infrastructure changes** (CI/CD, deployment, containerization, KiCad integration)
- **Security-sensitive code** modifications
- **Circuit-synth core changes** (Circuit, Component, Net classes)
- **KiCad integration modifications** (symbol/footprint handling, netlist generation)
- **Memory bank and agent system** modifications
- **Plugin ecosystem** modifications (KiCad plugins, external integrations)

### 2. Risk Assessment Matrix
**CRITICAL RISK** - Block merge until resolved:
- Security vulnerabilities (exposed secrets, unsafe operations)
- Breaking API changes to Circuit/Component/Net without deprecation
- KiCad integration breaking changes
- Performance regressions >50% or affecting core workflows
- Missing KiCad validation for new components

**HIGH RISK** - Immediate attention required:
- Breaking API changes without deprecation notices
- Performance regressions >20%
- Critical dependency updates (KiCad, PySpice, modm-devices)
- Database/schema modifications
- Memory bank structure changes affecting persistence
- Agent system modifications that could break workflows

**MEDIUM RISK** - Careful review needed:
- New external dependencies (especially circuit/EDA related)
- Complex algorithm changes (placement, routing, validation)
- Test infrastructure modifications
- Documentation gaps for new features
- Plugin API changes
- Example circuit modifications without validation
- Memory bank content changes
- Agent prompt or capability modifications

**LOW RISK** - Routine improvements:
- Code formatting and style fixes (Black, isort)
- Comment updates and documentation improvements
- Example circuit additions with proper validation
- Non-breaking feature additions
- Test case additions
- Memory bank knowledge additions
- Agent coaching improvements
- Plugin documentation updates

### 3. Code Quality Review
**Circuit-Synth Specific Anti-Patterns:**
- Direct KiCad file manipulation without validation
- Hardcoded component symbols/footprints without verification
- Missing pin connection validation
- Net naming conflicts or duplicates
- Component reference designator conflicts
- Missing KiCad library path validation
- Unsafe SPICE netlist generation
- Memory bank data without proper structure

**General Anti-Pattern Detection:**
- Circular dependencies (especially in circuit modules)
- Global state management
- Overly complex functions (>100 lines, >10 complexity)
- Deep inheritance hierarchies (>3 levels)
- Magic numbers and hardcoded strings (component values, pin numbers)
- Poor error handling patterns
- Blocking I/O in main threads
- Unsafe file operations
- Memory leaks in long-running processes

**Complexity Analysis:**
- Function length and cyclomatic complexity (target: <50 lines, <10 complexity)
- Class design and responsibility distribution (Single Responsibility Principle)
- Module coupling and cohesion (minimize cross-module dependencies)
- Documentation completeness (docstrings, type hints, examples)
- Circuit design complexity (component count, net density, hierarchy depth)
- KiCad integration complexity (symbol/footprint dependencies)
- Agent prompt complexity and maintainability
- Memory bank structure and navigation complexity

**Comment Quality Assessment:**
- Unnecessary obvious comments ("increment i", "set variable x")
- Outdated comments that don't match code behavior
- Missing docstrings for public APIs (especially Circuit/Component methods)
- TODO/FIXME comments that should be GitHub issues
- Circuit design comments without electrical context
- KiCad integration comments without library references
- Agent prompt comments without examples
- Memory bank entries without proper categorization

### 4. Security Analysis
**Circuit-Synth Specific Security:**
- Hardcoded JLCPCB API keys or credentials
- Unsafe KiCad file parsing (XML/S-expression injection)
- Unvalidated component data from external sources
- Command injection through KiCad CLI integration
- Unsafe Python code execution in circuit generation
- Memory bank data exposure (PII, proprietary designs)
- Plugin security (arbitrary code execution risks)

**General Security Review:**
- Hardcoded credentials or API keys
- SQL injection vulnerability patterns
- File system access without validation
- Command injection possibilities (especially shell commands)
- Unsafe deserialization patterns (pickle, eval)
- Path traversal vulnerabilities
- Input validation bypass

**Dependency Security:**
- New dependencies vulnerability scanning (npm audit, safety)
- Version updates security implications
- Supply chain risk assessment
- License compatibility issues
- Deprecated dependency usage

### 5. Performance Impact Analysis
**Circuit-Synth Specific Performance:**
- KiCad symbol/footprint loading performance
- Circuit netlist generation efficiency
- Component validation speed (modm-devices queries)
- JLCPCB API rate limiting and caching
- Memory bank search and retrieval performance
- Agent response time and context management
- Plugin load time and memory usage

**General Performance Analysis:**
- Large file additions/modifications (>1MB files)
- Database query efficiency changes
- Algorithm complexity modifications (O(n²) or worse)
- Memory usage pattern changes (memory leaks, excessive allocation)
- I/O operation efficiency (file operations, network requests)
- CPU-intensive operations in main threads
- Caching strategy effectiveness
- Concurrent processing optimization

### 6. Documentation Impact Assessment

**CRITICAL: Always review if core documentation needs updates based on changes:**

- **@README.md** - Check if new features, installation steps, usage examples, or architecture changes need documentation
- **@Contributors.md** - Review if new development processes, tools, contribution paths, or setup procedures were added  
- **@docs/** directory - Assess if API docs, technical guides, tutorials, or reference documentation requires updates
- **Agent files** in `.claude/agents/` - Verify if agent knowledge, capabilities, prompts, or tools need updates
- **Command files** in `.claude/commands/` - Check if new commands, workflows, or development processes were added

**Key documentation review questions:**
- Does this change introduce new user-facing features? → Update @README.md features section
- Does this change affect how contributors set up or work? → Update @Contributors.md
- Does this change add/modify APIs, commands, or workflows? → Update relevant @docs/ files
- Does this change affect what agents can help with or know about? → Update relevant agent knowledge
- Does this change add new development tools, commands, or processes? → Update command documentation
- Does this change modify project structure or architecture? → Update architecture documentation

**Documentation review checklist:**
- [ ] @README.md reflects new features and capabilities
- [ ] @Contributors.md includes any new development workflows  
- [ ] @docs/ API/technical documentation is current
- [ ] Agent knowledge in `.claude/agents/` is up-to-date
- [ ] Command documentation in `.claude/commands/` is accurate
- [ ] Architecture diagrams and explanations are current

### 7. Testing Coverage Analysis
**Circuit-Synth Testing Requirements:**
- Circuit generation validation (netlists, KiCad files)
- Component symbol/footprint verification
- KiCad integration testing (all supported versions)
- Example circuit validation (complete end-to-end)
- SPICE simulation testing
- Agent workflow testing
- Plugin functionality testing
- Memory bank integrity testing

**General Testing Analysis:**
- Test coverage for new functionality (target: >80%)
- Test quality and completeness (unit, integration, E2E)
- Regression test adequacy
- Performance test coverage
- Security test coverage
- Edge case and error condition testing
- Mock/stub usage appropriateness
- Test maintenance burden
- Circuit simulation test coverage
- KiCad file generation validation
- Component database integrity tests

### 8. Circuit-Synth Domain Analysis
**Core Circuit Logic:**
- Circuit/Component/Net class modifications
- Pin connection validation
- Net naming and routing logic
- Component reference management
- Hierarchical circuit design changes

**KiCad Integration:**
- Symbol library path changes
- Footprint validation modifications
- Netlist generation algorithm changes
- S-expression parsing modifications
- KiCad version compatibility

**Manufacturing Integration:**
- JLCPCB component availability changes
- Digikey/Mouser integration modifications
- Component sourcing algorithm changes
- Stock validation and caching
- Pricing and availability updates

**AI Agent System:**
- Agent prompt modifications
- Capability additions or removals
- Workflow orchestration changes
- Memory bank integration changes
- Example-driven training modifications

### 9. Dependency Analysis
**Python Dependencies:**
- New packages in pyproject.toml
- Version constraint changes
- Optional dependency modifications
- Development dependency updates

- Cargo.toml modifications
- Performance-critical dependency changes
- Cross-platform compatibility

**External Tool Dependencies:**
- KiCad version requirements
- PySpice compatibility
- System library requirements
- Plugin ecosystem dependencies

### 10. Memory Bank and Knowledge Management
**Memory Bank Changes:**
- Knowledge base additions/modifications
- Technical decision documentation
- Pattern and template updates
- Historical context preservation

**Agent Training Data:**
- Example circuit modifications
- Coaching prompt updates
- Success pattern documentation
- Failure case documentation

### 11. Automated Fix Suggestions
**Common Issues:**
- Missing type hints → Generate type annotations
- Hardcoded values → Extract to constants
- Missing docstrings → Generate documentation templates
- Inconsistent formatting → Black/isort fixes
- Missing tests → Generate test templates
- KiCad symbol issues → Library path validation

## Output Structure

The command generates a comprehensive markdown report with:

```markdown
# Development Branch Review: [branch] → [target]

## 🎯 Executive Summary
- Overall risk assessment (CRITICAL/HIGH/MEDIUM/LOW)
- Key changes summary with impact analysis
- Immediate action items with priorities
- Merge recommendation with confidence level

## 📊 Change Metrics  
- Files changed: +X, -Y (breakdown by category)
- Commits analyzed: X with Y authors
- Test coverage: X% (change from baseline)
- Complexity score: X/10 (McCabe, Halstead)
- Security score: X/10 (vulnerability assessment)

## 🔍 Detailed Analysis
### 🏗️ Architectural Impact
### ⚠️ Risk Assessment Matrix
### 🧹 Code Quality Review
### 🔒 Security Analysis  
### ⚡ Performance Impact
### 🧪 Testing Coverage
### 📚 Documentation Impact Assessment
### ⚙️ Circuit-Synth Domain Analysis
### 📦 Dependency Analysis
### 🧠 Memory Bank Analysis
### 🤖 AI Agent Impact

## 🔧 Automated Fix Suggestions
### Critical Issues (Auto-fixable)
### Warning Issues (Suggestions)  
### Optimization Opportunities

## 🎯 Recommendations
### 🚨 Immediate Actions Required (Blocking)
### ⚠️ Suggested Improvements (High Priority)
### 💡 Future Considerations (Backlog)
### 📈 Technical Debt Opportunities

## ✅ Circuit-Synth Merge Readiness Checklist
- [ ] Core circuit logic tests passing
- [ ] KiCad integration validated
- [ ] Example circuits generate successfully
- [ ] No hardcoded component references
- [ ] Symbol/footprint validation complete
- [ ] Agent workflows functional
- [ ] Memory bank integrity maintained
- [ ] Plugin compatibility verified
- [ ] Performance regression test passed
- [ ] Security scan clean
- [ ] Documentation updated
- [ ] Breaking changes documented

## 📈 Branch Quality Score: X/100
### Scoring Breakdown:
- Code Quality: X/25
- Security: X/25
- Performance: X/20  
- Testing: X/15
- Documentation: X/10
- Circuit-Synth Compliance: X/5
```

## Implementation Strategy

The command uses these tools systematically:

### 1. Git Analysis (Comprehensive)
```bash
# Commit analysis
git log --oneline --graph --decorate main..HEAD
git log --stat --format=fuller main..HEAD
git show --name-status HEAD~$history..HEAD

# Change analysis
git diff --stat main..HEAD
git diff --name-status main..HEAD
git diff --numstat main..HEAD
git diff --dirstat main..HEAD

# Author and timing analysis
git log --format="%an|%ae|%ad|%s" --date=iso main..HEAD
git log --since="1 week ago" --until="now" --oneline

# Merge conflict potential
git merge-tree $(git merge-base main HEAD) main HEAD
```

### 2. Code Analysis (Multi-layered)
```bash
# Security pattern detection
grep -r "api[_-]key\|password\|secret\|token" --include="*.py" .
grep -r "eval\|exec\|subprocess\|os\.system" --include="*.py" .
grep -r "pickle\|marshal\|yaml\.load" --include="*.py" .

# Circuit-synth pattern analysis
grep -r "Component\|Circuit\|Net" --include="*.py" src/
grep -r "kicad\|symbol\|footprint" --include="*.py" .
grep -r "JLCPCB\|modm-devices" --include="*.py" .

# Complexity analysis using tools
radon cc --min=C src/  # Cyclomatic complexity
radon mi --min=C src/  # Maintainability index
radon raw src/         # Raw metrics

# Import analysis
pydeps src/ --show-deps --cluster
python -m pip list --outdated
```

### 3. Circuit-Synth Specific Validation
```bash
# Core functionality validation
uv run python examples/example_kicad_project.py --validate
uv run python -c "from circuit_synth import Circuit, Component, Net; print('Core imports OK')"

# KiCad integration testing
kicad-cli version  # Verify KiCad availability
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5

# Agent system validation
ls .claude/agents/*.md | wc -l
grep -c "^#" .claude/agents/*.md

# Memory bank integrity
find memory-bank/ -name "*.md" -exec wc -l {} \; | sort -nr
```

### 4. Testing and Quality Validation
```bash
# Test execution
uv run pytest --cov=circuit_synth --cov-report=term-missing
uv run pytest tests/unit/test_core_circuit.py -v

# Code formatting and linting
black --check --diff src/
isort --check-only --diff src/
flake8 src/ --max-line-length=100
mypy src/ --ignore-missing-imports

# Documentation validation
sphinx-build -b html docs/ docs/_build/html
markdown-link-check README.md
```

### 5. Performance and Resource Analysis
```bash
# File size analysis
find . -name "*.py" -exec wc -c {} \; | sort -nr | head -20
du -sh memory-bank/ examples/ src/

# Performance profiling setup
python -m cProfile -o profile.stats examples/example_kicad_project.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('tottime').print_stats(20)"

# Memory usage analysis
memory_profiler examples/example_kicad_project.py
```

### 6. Dependency and Security Analysis
```bash
# Python dependency security
safety check
bandit -r src/ -f json

# JavaScript/Node.js (for plugins)
npm audit
npm outdated

# License compliance
licensecheck --recursive src/
pip-licenses --format=table
```

### 7. Circuit-Synth Domain Validation
```bash
# Component validation
python -m circuit_synth.tools.validate_components examples/

# KiCad library validation
python -m circuit_synth.kicad.validate_libraries

# Agent capability testing
python -m circuit_synth.agents.test_agent_capabilities

# Memory bank validation
python -m circuit_synth.ai_integration.memory_bank.validate_structure
```

## Example Usage

```bash
# Quick security-focused review
/dev-review-branch --depth=quick --focus=security

# Full comprehensive review for major release
/dev-review-branch --depth=full --target=main --auto-fix=true

# Performance-focused review with JSON output
/dev-review-branch --focus=performance --format=json --threshold=high

# Circuit-synth specific deep analysis
/dev-review-branch --focus=circuit-synth --depth=forensic --interactive=true

# Dependency-focused review with auto-suggestions
/dev-review-branch --focus=dependencies --auto-fix=true --format=checklist

# Interactive review for complex changes
/dev-review-branch --depth=full --interactive=true --history=20

# Pre-merge validation (strict mode)
/dev-review-branch --threshold=critical --format=checklist --depth=full
```

## Integration Points

### Git Workflow Integration
- **Pre-commit hooks** - Quick validation before commits
- **Pre-merge hooks** - Comprehensive review before merging  
- **GitHub Actions** - Automated PR review comments
- **GitLab CI** - Pipeline integration with quality gates

### CI/CD Pipeline Integration
- **Automated review reports** - JSON/markdown output for build systems
- **Quality gate enforcement** - Block merges on critical issues
- **Performance regression detection** - Benchmark comparison
- **Security scanning integration** - SAST/DAST tool coordination

### Development Environment Integration
- **VS Code extension** - Real-time review feedback
- **Claude Code integration** - Native command support
- **IDE plugins** - Code quality highlights
- **Terminal aliases** - Quick access commands

### Circuit-Synth Ecosystem Integration
- **KiCad plugin validation** - Ensure plugin compatibility
- **Agent system testing** - Validate AI agent functionality
- **Memory bank validation** - Ensure knowledge base integrity
- **Example circuit testing** - Validate all example outputs

### External Tool Integration
- **SonarQube** - Code quality metrics sync
- **Dependabot** - Dependency update validation
- **Snyk** - Security vulnerability scanning
- **CodeClimate** - Maintainability scoring

## Quality Gates and Thresholds

### CRITICAL (Block Merge)
**Circuit-Synth Specific:**
- Core Circuit/Component/Net API breaking changes
- KiCad integration failures
- Missing component validation
- Example circuits fail to generate
- Agent system completely broken
- Memory bank corruption

**General Critical:**
- Security vulnerabilities (CWE-89, CWE-79, CWE-502)
- Performance regression >50%
- Test coverage drop >20%
- Build failures
- License compliance violations

### HIGH RISK (Review Required)
**Circuit-Synth Specific:**
- New component types without validation
- KiCad library path changes
- Plugin API modifications
- Agent prompt significant changes
- Manufacturing integration changes

**General High Risk:**
- Breaking API changes without deprecation
- New dependencies with security issues
- Performance regression >20%
- Complex algorithm changes (O(n²) or worse)
- Missing documentation for public APIs

### MEDIUM RISK (Review Recommended)
**Circuit-Synth Specific:**
- Example circuit modifications
- Memory bank structural changes
- Agent coaching updates
- Plugin compatibility changes

**General Medium Risk:**
- Code complexity above thresholds (CC >10, MI <20)
- Missing type hints (>10% of functions)
- Test coverage gaps (new code <80%)
- Documentation inconsistencies

### LOW RISK (Informational)
- Code style inconsistencies
- Minor optimization opportunities
- Documentation improvements
- Test enhancement suggestions
- Memory bank knowledge additions

## Automated Quality Scoring

```python
# Quality Score Calculation (0-100)
quality_score = {
    'code_quality': (
        cyclomatic_complexity_score * 0.3 +
        maintainability_index_score * 0.3 +
        type_coverage_score * 0.2 +
        documentation_score * 0.2
    ) * 0.25,
    
    'security': (
        vulnerability_score * 0.4 +
        dependency_security_score * 0.3 +
        code_security_score * 0.3
    ) * 0.25,
    
    'performance': (
        execution_time_score * 0.4 +
        memory_usage_score * 0.3 +
        algorithmic_efficiency_score * 0.3
    ) * 0.20,
    
    'testing': (
        coverage_score * 0.4 +
        test_quality_score * 0.3 +
        integration_test_score * 0.3
    ) * 0.15,
    
    'documentation': (
        api_documentation_score * 0.5 +
        readme_accuracy_score * 0.3 +
        example_quality_score * 0.2
    ) * 0.10,
    
    'circuit_synth_compliance': (
        core_api_compliance * 0.3 +
        kicad_integration_score * 0.3 +
        agent_system_score * 0.2 +
        memory_bank_score * 0.2
    ) * 0.05
}

total_score = sum(quality_score.values())
```

## Advanced Features

### Interactive Mode
When `--interactive=true` is specified:
- Step-through analysis of each high-risk change
- Interactive code exploration with context
- Real-time fix suggestion and application
- Collaborative review session support

### Auto-Fix Capabilities  
When `--auto-fix=true` is specified:
- Automatic code formatting (Black, isort)
- Type hint generation for missing annotations
- Docstring template generation
- Import optimization and cleanup
- Basic security fix applications

### Integration Hooks
```bash
# Git pre-merge hook integration
echo '/dev-review-branch --threshold=high --format=checklist' > .git/hooks/pre-merge-commit

# CI/CD pipeline integration
github-actions:
  - name: Branch Review
    run: /dev-review-branch --format=json --depth=full > review.json
  - name: Comment PR
    run: gh pr comment --body-file review.json
```

### Customization
Create `.circuit-synth-review.yml` for custom rules:
```yaml
quality_gates:
  critical:
    - security_vulnerabilities: 0
    - circuit_validation_failures: 0
    - kicad_integration_failures: 0
  high:
    - performance_regression_threshold: 20
    - test_coverage_drop_threshold: 15
    - complexity_threshold: 10
  
circuit_synth_rules:
  required_validations:
    - component_symbol_exists
    - footprint_validation
    - net_connectivity_check
  
  prohibited_patterns:
    - hardcoded_component_references
    - direct_kicad_file_manipulation
    - unsafe_spice_generation
```

### Performance Optimization
- Parallel analysis execution
- Intelligent caching of analysis results
- Delta analysis (only analyze changed sections)
- Background analysis for long-running reviews

---

**This comprehensive development branch review command ensures circuit-synth maintains the highest standards of code quality, security, performance, and domain-specific compliance across all merges to main. It combines general software engineering best practices with circuit design and KiCad integration expertise.**