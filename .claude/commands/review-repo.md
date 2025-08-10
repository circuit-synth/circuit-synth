# Comprehensive Repository Review Command

**Purpose:** Complete repository analysis with automatic feature discovery to identify what's working, what's broken, and what needs attention. Automatically surveys the repository to ensure no features are missed.

## Usage
```bash
/dev-review-repo [options]
```

## Options
- `--focus=all` - Focus areas: `architecture`, `security`, `performance`, `testing`, `docs`, `circuit-synth`, `agents`, `manufacturing`, `all` (default: all)
- `--output-dir=repo-review` - Directory for review outputs (default: repo-review)
- `--run-tests=true` - Run test suites (default: true)
- `--test-examples=true` - Test all example circuits (default: true)
- `--test-agents=true` - Test all AI agents functionality (default: true)
- `--check-security=true` - Security scanning (default: true)
- `--format=true` - Auto-format code before analysis (default: true)
- `--generate-fixes=false` - Generate automated fix suggestions (default: false)
- `--website-check=true` - Validate circuit-synth.com content accuracy (default: true)
- `--feature-discovery=true` - Auto-discover features from codebase (default: true)
- `--depth=standard` - Analysis depth: `quick`, `standard`, `deep` (default: standard)

## What This Does

### Phase 1: Automatic Feature Discovery
The command first performs automatic feature discovery to ensure nothing is missed:

1. **Codebase Survey** - Scans all directories and modules to identify features
2. **Commit Analysis** - Reviews recent commits for new/modified features
3. **Agent Discovery** - Identifies all available AI agents and their capabilities
4. **Tool Discovery** - Finds all CLI tools and development utilities
5. **Integration Discovery** - Identifies external integrations (KiCad, JLCPCB, DigiKey, etc.)
6. **Documentation Survey** - Maps all documentation and examples
7. **Undocumented Feature Detection** - Identifies features in code but missing from documentation
8. **Documentation Accuracy Validation** - Verifies documentation matches actual code behavior

### Phase 2: Comprehensive Analysis
Based on discovered features, performs targeted analysis:

### 1. Core Circuit-Synth Functionality
- **Circuit/Component/Net system** - Core object model validation
- **Hierarchical circuits** - Subcircuit and sheet management
- **Pin connections** - Connection validation and net routing
- **Reference management** - Component reference designator handling
- **Annotations system** - Docstring and manual annotations
- **JSON serialization** - Round-trip conversion testing

### 2. KiCad Integration
- **Symbol library access** - Cross-platform symbol search
- **Footprint validation** - Component footprint verification
- **Schematic generation** - .kicad_sch file creation
- **PCB generation** - .kicad_pcb file creation
- **Project file generation** - Complete KiCad project structure
- **S-expression formatting** - Proper KiCad file formatting
- **Version compatibility** - KiCad 6/7/8 support

### 3. Manufacturing Integration
- **JLCPCB Integration**
  - Component availability checking
  - Fast search optimization
  - Cache management
  - API rate limiting
- **DigiKey Integration**
  - OAuth authentication
  - Product search API
  - Pricing and availability
  - KiCad symbol mapping
- **Unified Search System**
  - Multi-source component search
  - Comparison functionality
  - Filtering and sorting
- **OSHPark/PCBWay** (placeholder modules)

### 4. AI Agent System
- **Core Agents**
  - circuit-architect (master coordinator)
  - circuit-generation-agent (code generation)
  - simulation-expert (SPICE simulation)
  - test-plan-creator (validation)
- **Manufacturing Agents**
  - component-guru (sourcing optimization)
  - component-search (multi-source search)
  - dfm-agent (design for manufacturing)
  - digikey-parts-finder
  - jlc-parts-finder
- **Quality Assurance Agents**
  - fmea-orchestrator (failure analysis)
  - fmea-analyst
  - fmea-component-analyst
  - fmea-reliability-engineer
- **Specialized Agents**
  - stm32-mcu-finder (MCU selection)
  - circuit-debugger (PCB troubleshooting)
  - contributor (development assistance)
- **Agent Infrastructure**
  - Memory bank system (progress tracking, decisions, patterns, issues, knowledge)
  - Knowledge management and context preservation
  - Agent registration (MCP)
  - Prompt engineering
- **Memory Bank System**
  - PCB design change tracking
  - Technical decision recording
  - Pattern and solution storage
  - Issue tracking with workarounds
  - Cross-session knowledge preservation

### 5. Quality Assurance Systems
- **FMEA (Failure Mode and Effects Analysis)**
  - Component failure analysis
  - System reliability assessment
  - Risk prioritization
  - Report generation (50+ pages)
- **DFM (Design for Manufacturing)**
  - Manufacturing constraints
  - Component placement optimization
  - Assembly complexity analysis
  - Cost optimization
- **Circuit Validation**
  - Syntax validation
  - Import verification
  - Runtime execution testing
  - Circuit structure validation
- **Test Plan Generation**
  - Automated circuit test plan creation
  - Validation strategy development
  - Test case generation for circuits
  - Quality assurance test frameworks
- **Debugging System**
  - Symptom analysis
  - Pattern recognition
  - Troubleshooting trees
  - Equipment guidance

- **Build System**
  - Cargo integration
  - Maturin builds
  - CI/CD pipeline

### 7. Development Tools
- **Testing Infrastructure**
  - Unit tests (pytest)
  - Integration tests
  - Regression tests
  - Full regression suite
- **Build Tools**
  - format_all.sh
- **Analysis Tools**
  - Dead code analysis
  - Performance profiling
  - Memory profiling
  - Coverage analysis
- **CI/CD Tools**
  - GitHub Actions setup
  - PyPI release automation
  - Documentation generation

### 8. Component Information Systems
- **Microcontrollers**
  - STM32 (modm-devices integration)
  - ESP32 (planned)
  - PIC (planned)
  - AVR (planned)
- **Analog Components** (planned)
  - Op-amps
  - ADCs/DACs
  - Voltage references
- **Power Components** (planned)
  - Regulators
  - Power management ICs
  - Protection circuits
- **RF Components** (planned)
  - Wireless modules
  - Antennas
  - RF transceivers

### 9. Simulation and Validation
- **SPICE Integration**
  - PySpice backend
  - Netlist generation
  - Component models
  - Simulation results
- **Electrical Rules Check**
  - Connection validation
  - Power supply verification
  - Signal integrity basics
- **Design Rule Check**
  - Component placement rules
  - Routing constraints
  - Manufacturing limits

### 10. Documentation and Examples
- **Core Documentation**
  - README.md accuracy
  - Contributors.md completeness
  - API documentation (Sphinx)
  - Installation guides
- **Example Circuits**
  - Basic examples
  - Advanced examples
  - Testing examples
  - Tool examples
- **Agent Documentation**
  - Agent capabilities
  - Command documentation
  - Workflow examples
- **Website Content**
  - circuit-synth.com accuracy
  - Feature descriptions
  - Installation instructions
  - Code examples

## Output Structure

```
repo-review/
├── 00-feature-discovery-report.md           # Auto-discovered features
├── 01-executive-summary.md                  # High-level overview and priorities
├── 02-core-functionality-analysis.md        # Circuit/Component/Net system
├── 03-kicad-integration-analysis.md         # KiCad generation and compatibility
├── 04-manufacturing-integration-analysis.md # JLCPCB, DigiKey, unified search
├── 05-agent-system-analysis.md              # All AI agents and capabilities
├── 06-quality-assurance-analysis.md         # FMEA, DFM, validation, debugging
├── 08-development-tools-analysis.md         # Testing, build, CI/CD tools
├── 09-component-systems-analysis.md         # MCU and component databases
├── 10-simulation-validation-analysis.md     # SPICE and electrical checks
├── 11-code-quality-analysis.md              # Code patterns, complexity, cleanup
├── 12-security-analysis.md                  # Security vulnerabilities
├── 13-performance-analysis.md               # Performance bottlenecks
├── 14-testing-coverage-analysis.md          # Test quality and coverage
├── 15-documentation-analysis.md             # Documentation accuracy and quality
├── 16-dependency-analysis.md                # Package health and updates
├── 18-website-validation-analysis.md        # circuit-synth.com and website/ directory accuracy
├── 19-undocumented-features-analysis.md     # Features in code but not documented
├── 20-test-plan-analysis.md                 # Test plan generation capabilities
├── 21-recommendations-roadmap.md            # Prioritized action items
└── findings/                                 # Raw data, logs, and detailed reports
    ├── discovered-features.json             # Auto-discovered feature list
    ├── agent-test-results/                  # Agent functionality tests
    ├── example-test-results/                # Example circuit tests
    ├── security-scan-results/               # Security scan outputs
    ├── performance-profiles/                # Performance profiling data
    ├── coverage-reports/                    # Test coverage reports
    ├── memory-bank-test-results/            # Memory bank system tests
    ├── test-plan-analysis/                  # Test plan generation results
    ├── undocumented-features/               # Features found but not documented
    └── doc-accuracy-checks/                 # Documentation vs code validation
```

## Implementation Details

### Feature Discovery Process

```python
def discover_features():
    features = {
        'core_modules': scan_python_modules('src/circuit_synth'),
        'agents': discover_agents('.claude/agents'),
        'commands': discover_commands('.claude/commands'),
        'tools': discover_tools('tools', 'src/circuit_synth/tools'),
        'examples': scan_examples('examples'),
        'integrations': detect_integrations(),
        'recent_features': analyze_recent_commits(100),
        'memory_bank': scan_memory_bank('memory-bank/'),
        'undocumented_features': find_undocumented_features(),
        'doc_accuracy': validate_documentation_accuracy(),
    }
    return features
```

### Agent Testing Framework

```python
def test_agent_functionality(agent_name):
    """Test if an agent can be loaded and responds correctly"""
    tests = {
        'load_test': can_load_agent(agent_name),
        'prompt_test': test_agent_prompt(agent_name),
        'capability_test': verify_agent_capabilities(agent_name),
        'knowledge_test': check_agent_knowledge(agent_name),
    }
    return tests

def test_memory_bank_system():
    """Test memory bank functionality for PCB design tracking"""
    tests = {
        'structure_test': verify_memory_bank_structure(),
        'read_write_test': test_memory_bank_operations(),
        'context_preservation': test_cross_session_memory(),
        'decision_tracking': test_technical_decision_storage(),
    }
    return tests

def find_undocumented_features():
    """Find features implemented in code but missing from documentation"""
    code_features = extract_features_from_code()
    doc_features = extract_features_from_docs()
    undocumented = set(code_features) - set(doc_features)
    return list(undocumented)

def validate_documentation_accuracy():
    """Verify documentation matches actual code behavior"""
    mismatches = []
    for doc_example in find_code_examples_in_docs():
        if not validate_example_against_code(doc_example):
            mismatches.append(doc_example)
    return mismatches
```

### Comprehensive Analysis Execution

```bash
# Create output directory structure

# Phase 1: Feature Discovery
echo "=== Automatic Feature Discovery ==="
python -c "
import os
import json
from pathlib import Path

# Discover all Python modules
modules = []
for root, dirs, files in os.walk('src/circuit_synth'):
    for file in files:
        if file.endswith('.py'):
            modules.append(os.path.join(root, file))

# Discover all agents
agents = []
for agent_file in Path('.claude/agents').rglob('*.md'):
    agents.append(str(agent_file))


# Recent features from commits
import subprocess
commits = subprocess.check_output(['git', 'log', '--oneline', '-100']).decode()
features = [line for line in commits.split('\n') if 'feat:' in line]

discovery = {
    'python_modules': len(modules),
    'agents': len(agents),
    'recent_features': len(features),
    'timestamp': str(datetime.now())
}

with open('repo-review/findings/discovered-features.json', 'w') as f:
    json.dump(discovery, f, indent=2)
"

# Phase 2: Test Core Functionality
echo "=== Testing Core Circuit-Synth Features ==="
uv run python -c "from circuit_synth import Circuit, Component, Net; print('Core imports: OK')"
uv run python example_project/circuit-synth/main.py --validate

# Phase 3: Test KiCad Integration
echo "=== Testing KiCad Integration ==="
kicad-cli version
find /usr/share/kicad/symbols -name "*.kicad_sym" | head -5

# Phase 4: Test Manufacturing Integration
echo "=== Testing Manufacturing Integration ==="
uv run python -c "
from circuit_synth.manufacturing import find_parts
results = find_parts('resistor 10k', sources='all')
print(f'Unified search: {len(results)} results')
"

# Phase 5: Test Agent System
echo "=== Testing AI Agent System ==="
for agent in $(ls .claude/agents/**/*.md); do
    echo "Testing agent: $(basename $agent .md)"
    # Test agent loading and basic functionality
done

# Phase 6: Test Quality Assurance Systems
echo "=== Testing Quality Assurance Systems ==="
uv run python -m circuit_synth.quality_assurance.fmea_cli --help
uv run python -m circuit_synth.debugging.debug_cli --help

for module in */; do
done
cd ..

# Phase 8: Run Test Suites
echo "=== Running Test Suites ==="
uv run pytest tests/unit/ -v --tb=short
uv run pytest tests/integration/ -v --tb=short
./tools/testing/run_full_regression_tests.py --quick

# Phase 9: Security Analysis
echo "=== Security Analysis ==="
safety check
bandit -r src/ -f json > repo-review/findings/bandit-report.json

# Phase 10: Performance Analysis
echo "=== Performance Analysis ==="
python -m cProfile -o repo-review/findings/profile.stats example_project/circuit-synth/main.py

# Phase 11: Documentation Validation  
echo "=== Documentation Validation ==="
sphinx-build -b html docs/ docs/_build/html 2>/dev/null || echo "Sphinx documentation build failed or not configured"
markdown-link-check README.md Contributors.md 2>/dev/null || echo "Markdown link check failed or tool not installed"

# Phase 11.5: Website Validation
echo "=== Website Validation ==="
if [ -d "website" ]; then
    echo "📱 Found website directory - validating content..."
    
    # Check website structure
    required_files=("index.html" "style.css" "deploy-website.sh")
    for file in "${required_files[@]}"; do
        if [ -f "website/$file" ]; then
            echo "✅ website/$file exists"
        else
            echo "❌ Missing website/$file"
        fi
    done
    
    # Validate HTML content
    if [ -f "website/index.html" ]; then
        # Check for current version references
        current_version=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/' || echo "unknown")
        echo "Current version: $current_version"
        
        # Check website content accuracy
        html_content=$(cat website/index.html)
        
        # Check for branding consistency
        if echo "$html_content" | grep -q "circuit-synth"; then
            echo "✅ Circuit-synth branding found"
        else
            echo "⚠️ Missing circuit-synth branding in website"
        fi
        
        # Check for key features mentioned
        features=("Python" "KiCad" "AI" "manufacturing" "SPICE")
        for feature in "${features[@]}"; do
            if echo "$html_content" | grep -qi "$feature"; then
                echo "✅ Feature '$feature' mentioned in website"
            else
                echo "⚠️ Feature '$feature' not found in website content"
            fi
        done
        
        # Check installation instructions
        if echo "$html_content" | grep -q "uv add circuit-synth"; then
            echo "✅ Installation instructions include uv"
        else
            echo "⚠️ Website may need updated installation instructions"
        fi
        
        # Check for Claude Code integration mention
        if echo "$html_content" | grep -qi "claude"; then
            echo "✅ Claude Code integration mentioned"
        else
            echo "⚠️ Claude Code integration not prominently featured"
        fi
    fi
    
    # Validate deployment script
    if [ -f "website/deploy-website.sh" ]; then
        echo "🚀 Checking deployment script..."
        if bash -n website/deploy-website.sh; then
            echo "✅ Deployment script syntax OK"
        else
            echo "❌ Deployment script has syntax errors"
        fi
        
        # Check if deployment docs exist
        if [ -f "website/DEPLOYMENT.md" ]; then
            echo "✅ Deployment documentation exists"
        else
            echo "⚠️ Missing website/DEPLOYMENT.md"
        fi
    fi
    
    # Check CSS for responsive design
    if [ -f "website/style.css" ]; then
        css_content=$(cat website/style.css)
        if echo "$css_content" | grep -q "@media"; then
            echo "✅ CSS includes responsive design rules"
        else
            echo "⚠️ CSS may lack responsive design"
        fi
    fi
    
    # Check for asset files
    asset_types=("*.png" "*.jpg" "*.svg" "*.ico")
    assets_found=0
    for pattern in "${asset_types[@]}"; do
        if find website/ -name "$pattern" -type f | head -1 | grep -q .; then
            assets_found=$((assets_found + 1))
            echo "✅ Found assets matching $pattern"
        fi
    done
    
    if [ $assets_found -gt 0 ]; then
        echo "✅ Website includes visual assets"
    else
        echo "⚠️ No visual assets found in website/"
    fi
    
else
    echo "❌ Website directory not found - website content not validated"
    echo "💡 Consider adding website/ directory for circuit-synth.com deployment"
fi

# Check for broken example references after cleanup
echo "=== Documentation Alignment Check ==="
grep -r "examples/" README.md docs/ .claude/ --include="*.md" --include="*.rst" || echo "No examples/ references found"
find . -name "*.md" -o -name "*.rst" | xargs grep -l "example_kicad_project.py" | while read file; do
  echo "Checking: $file"
  grep -n "example_kicad_project.py" "$file"
done

# Phase 11.1: Find Undocumented Features
echo "=== Finding Undocumented Features ==="
uv run python -c "
import os
import re
from pathlib import Path

# Scan Python files for classes and functions
code_features = set()
for py_file in Path('src/circuit_synth').rglob('*.py'):
    try:
        content = py_file.read_text()
        # Find class definitions
        classes = re.findall(r'^class\s+([A-Za-z][A-Za-z0-9_]*)', content, re.MULTILINE)
        # Find function definitions
        functions = re.findall(r'^def\s+([A-Za-z][A-Za-z0-9_]*)', content, re.MULTILINE)
        code_features.update(classes)
        code_features.update(functions)
    except:
        pass

# Scan documentation for mentioned features
doc_features = set()
doc_files = []
doc_files.extend(Path('.').glob('*.md'))
if Path('docs').exists():
    doc_files.extend(Path('docs').rglob('*.md'))
    doc_files.extend(Path('docs').rglob('*.rst'))
if Path('.claude').exists():
    doc_files.extend(Path('.claude').rglob('*.md'))

for doc_file in doc_files:
    try:
        content = doc_file.read_text().lower()
        # Extract potential feature names from documentation
        words = re.findall(r'[a-z][a-z0-9_]+', content)
        doc_features.update(words)
    except:
        pass

# Find features in code but not documented (case-insensitive)
code_lower = {f.lower() for f in code_features}
doc_lower = {f.lower() for f in doc_features}
undocumented = [f for f in code_features if f.lower() not in doc_lower and len(f) > 3]

print(f'Total code features found: {len(code_features)}')
print(f'Potentially undocumented features: {len(undocumented)}')
if undocumented[:10]:  # Show first 10
    print('Sample undocumented features:', undocumented[:10])
" > repo-review/findings/undocumented-features/feature-analysis.txt

# Phase 11.2: Documentation Accuracy Check
echo "=== Documentation Accuracy Validation ==="
uv run python -c "
import re
from pathlib import Path

# Find code examples in documentation
code_examples = []
doc_files = []
doc_files.extend(Path('.').glob('*.md'))
if Path('docs').exists():
    doc_files.extend(Path('docs').rglob('*.md'))

for doc_file in doc_files:
    try:
        content = doc_file.read_text()
        # Find Python code blocks
        python_blocks = re.findall(r'\`\`\`python\n(.+?)\`\`\`', content, re.DOTALL)
        for block in python_blocks:
            code_examples.append({
                'file': str(doc_file),
                'code': block.strip()
            })
    except:
        pass

print(f'Found {len(code_examples)} Python code examples in documentation')

# Try to validate some examples
valid_examples = 0
for example in code_examples[:5]:  # Check first 5
    try:
        # Basic syntax check
        compile(example['code'], '<string>', 'exec')
        valid_examples += 1
    except SyntaxError:
        print(f'Syntax error in {example[\"file\"]}')
    except:
        pass

print(f'Syntactically valid examples: {valid_examples}/{min(5, len(code_examples))}')
" > repo-review/findings/doc-accuracy-checks/syntax-validation.txt

# Check for broken example references after cleanup
echo "=== Documentation Alignment Check ==="
grep -r "examples/" README.md docs/ .claude/ --include="*.md" --include="*.rst" || echo "No examples/ references found"
find . -name "*.md" -o -name "*.rst" | xargs grep -l "example_kicad_project.py" | while read file; do
  echo "Checking: $file"
  grep -n "example_kicad_project.py" "$file"
done

# Phase 12: Dependency Analysis
echo "=== Dependency Analysis ==="
pip list --outdated > repo-review/findings/outdated-packages.txt
pip-audit --format json > repo-review/findings/pip-audit.json
```

## Report Templates

### Feature Discovery Report
```markdown
# Automatic Feature Discovery Report

## Summary
- Total Python modules: X
- Total AI agents: X
- Total CLI tools: X
- Recent features (last 100 commits): X

## Discovered Features

### Core Systems
[List of discovered core modules and their purposes]

### AI Agents
[List of all agents with their capabilities]

### Manufacturing Integrations
[List of all supplier integrations]

### Quality Assurance Systems
[List of QA tools and systems]

### Development Tools
[List of all development utilities]

## Features Not Yet Documented
[Features found in code but not in documentation]

## Features Not Yet Tested
[Features without corresponding tests]

## Memory Bank System Status
[Status of memory bank directories and functionality]

## Test Plan Generation Features
[Test plan creation capabilities and agents]

## Documentation Accuracy Issues
[Examples and descriptions that don't match current code]
```

### Agent System Analysis Report
```markdown
# AI Agent System Analysis

## Agent Inventory
Total agents discovered: X

### Functional Agents (Passing Tests)
- agent_name: test_results

### Non-Functional Agents (Failing Tests)
- agent_name: failure_reason

### Agent Categories
- Circuit Design: X agents
- Manufacturing: X agents
- Quality Assurance: X agents
- Development: X agents

## Agent Infrastructure
- Memory bank status: [OK/Issues]
- MCP registration: [OK/Issues]
- Knowledge management: [OK/Issues]

## Memory Bank System Analysis
- Directory structure: [OK/Missing directories]
- Content preservation: [OK/Issues]
- Cross-session memory: [OK/Issues]
- Design decision tracking: [OK/Issues]

## Test Plan Generation Analysis
- test-plan-creator agent: [OK/Missing/Broken]
- Test framework integration: [OK/Issues]
- Automated test generation: [OK/Issues]

## Recommendations
[Specific fixes for non-functional agents and systems]
```

## Advanced Features

### Automatic Feature Survey
When `--feature-discovery=true`:
- Scans entire codebase for modules and classes
- Analyzes git history for feature additions
- Discovers all agents and tools
- Maps integrations and dependencies
- Creates comprehensive feature inventory

### Agent Testing
When `--test-agents=true`:
- Loads each agent and verifies structure
- Tests agent prompts and capabilities
- Validates agent knowledge base
- Checks MCP registration

- Checks compilation status
- Tests Python bindings
- Measures performance impact
- Identifies unused modules

### Depth Levels
- `quick`: Basic functionality tests only
- `standard`: Full test suite and analysis
- `deep`: Include performance profiling and security scanning

## Usage Examples

```bash
# Full comprehensive review with all features
/dev-review-repo

# Quick review focusing on core functionality
/dev-review-repo --depth=quick --focus=circuit-synth

# Agent system review with testing
/dev-review-repo --focus=agents --test-agents=true

# Manufacturing integration review
/dev-review-repo --focus=manufacturing

# Security-focused review
/dev-review-repo --focus=security --check-security=true

# Documentation and website validation
/dev-review-repo --focus=docs --website-check=true

```

## Integration with Development Workflow

### Pre-Release Checklist
Run before any release:
```bash
/dev-review-repo --depth=deep --generate-fixes=true
```

### Weekly Health Check
Regular maintenance:
```bash
/dev-review-repo --depth=standard --focus=all
```

### Post-Feature Development
After adding new features:
```bash
/dev-review-repo --feature-discovery=true --test-agents=true
```

## Customization

Create `.repo-review-config.yml` for custom settings:
```yaml
feature_discovery:
  include_paths:
    - src/
    - example_project/
    - tools/
  exclude_patterns:
    - __pycache__
    - .git
    - .venv

testing:
  test_timeout: 60
  parallel_tests: true
  
analysis:
  complexity_threshold: 10
  coverage_threshold: 80
  
reports:
  include_raw_data: true
  generate_html: false
```

---

**This comprehensive repository review command ensures complete coverage of all circuit-synth features through automatic discovery, preventing stale review configurations from missing new functionality.**