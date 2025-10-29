---
name: compare-three-repos
description: Comprehensive comparison and alignment analysis of circuit-synth, kicad-sch-api, and kicad-pcb-api
allowed-tools: "*"
model: claude-sonnet-4-5
---

# Comprehensive Three-Repository Comparison & Alignment Prompt

## Objective

Conduct an exhaustive, multi-dimensional comparison of **circuit-synth**, **kicad-sch-api**, and **kicad-pcb-api** to:

1. **Identify and synchronize best practices** across all three repositories
2. **Ensure architectural consistency** and alignment in design patterns
3. **Extract shared code** for potential common library
4. **Standardize tooling, testing, and development workflows**
5. **Establish integration patterns** between the three repositories
6. **Create unified style guides** and coding conventions
7. **Produce actionable roadmap** for alignment and improvement

This comparison treats all three repositories as equal partners in the circuit-synth ecosystem, identifying bidirectional and tridirectional insights where each repo can learn from the others.

---

## Repository Context

### Repository 1: circuit-synth
- **Purpose**: High-level Python circuit design framework with AI integration
- **Role**: Orchestrator and user-facing API for circuit-as-code design
- **Key Features**:
  - Python circuit definitions with `@circuit` decorator
  - Claude Code AI agent integration
  - Bidirectional KiCad workflow
  - JSON-centric architecture
  - Component sourcing and manufacturing integration
- **Dependencies**: Depends on both kicad-sch-api and kicad-pcb-api
- **Location**: `/Users/shanemattner/Desktop/circuit-synth`

### Repository 2: kicad-sch-api
- **Purpose**: Professional KiCAD schematic manipulation library
- **Role**: Low-level schematic file operations with exact format preservation
- **Key Features**:
  - S-expression parsing/formatting
  - Component/wire/label management
  - Symbol library caching
  - Exact KiCAD format preservation
  - Enhanced collections with indexing
- **Dependencies**: Foundation library (minimal external dependencies)
- **Location**: `/Users/shanemattner/Desktop/kicad-sch-api`

### Repository 3: kicad-pcb-api
- **Purpose**: Professional KiCAD PCB manipulation library
- **Role**: Low-level PCB file operations with exact format preservation
- **Key Features**:
  - S-expression parsing/formatting
  - Footprint/track/via management
  - Placement algorithms (hierarchical, spiral)
  - Freerouting integration (DSN/SES)
  - Advanced routing capabilities
- **Dependencies**: Foundation library (minimal external dependencies)
- **Location**: `/Users/shanemattner/Desktop/kicad-pcb-api`

### Integration Model

```
┌─────────────────────────────────────────────┐
│         circuit-synth (Orchestrator)        │
│  - High-level circuit definitions           │
│  - AI agent integration                     │
│  - User-facing API                          │
└─────────┬───────────────────────┬───────────┘
          │                       │
          │ depends on            │ depends on
          │                       │
    ┌─────▼────────┐       ┌─────▼────────┐
    │ kicad-sch-api│       │ kicad-pcb-api│
    │ - Schematic  │       │ - PCB layout │
    │ - Low-level  │       │ - Low-level  │
    └──────────────┘       └──────────────┘
```

---

## Part 1: Best Practices Synthesis & Standardization

### 1.1 Code Organization & Module Structure

**Analyze across all three repositories:**

1. **Directory structure patterns**:
   - Which repo has the cleanest separation of concerns?
   - How are core/utils/tools/tests organized?
   - Where should shared utilities live?
   - Module naming conventions (`_manager.py`, `_parser.py`, etc.)

2. **Import organization**:
   - Relative vs absolute imports patterns
   - Circular dependency avoidance strategies
   - Public API exposure patterns (`__init__.py` organization)

3. **Module size and cohesion**:
   - Which modules are appropriately sized vs monolithic?
   - Single Responsibility Principle adherence
   - Coupling between modules

**Deliverable**:
- Module structure comparison matrix
- Best practices document for directory organization
- Recommendations for restructuring any repo that deviates

### 1.2 Design Pattern Alignment

**Compare design patterns used across all three repos:**

1. **Parser/Formatter patterns**:
   - How are S-expressions handled in sch-api vs pcb-api?
   - Can parsing logic be unified?
   - Format preservation strategies

2. **Collection patterns**:
   - IndexedCollection implementations
   - Lookup optimization strategies (O(1) access)
   - Filtering and query interfaces
   - Which implementation is best?

3. **Manager patterns**:
   - Separation of concerns in managers
   - Manager interfaces and consistency
   - Which manager design is most maintainable?

4. **Registry patterns**:
   - Parser registry implementations
   - Component/symbol registration
   - Plugin architectures

5. **Validation patterns**:
   - Where validation lives (early vs late)
   - Error collection and reporting
   - Validation result structures

**Deliverable**:
- Design pattern inventory across all three repos
- Pattern quality ratings (1-5 scale)
- Unified pattern recommendations
- Specific refactoring suggestions

### 1.3 Type System & Type Hints Strategy

**Analyze type hint usage across repos:**

1. **Type coverage**:
   - Percentage of functions with type hints
   - Consistency of type annotation style
   - Use of Optional, Union, TypeVar, Generic

2. **Dataclass usage**:
   - When are dataclasses used vs regular classes?
   - Immutability patterns
   - Validation strategies (Pydantic vs manual)

3. **Type checking configuration**:
   - mypy configuration comparison
   - Strictness levels
   - Excluded paths and patterns

4. **Protocol usage**:
   - Structural typing patterns
   - Abstract interfaces
   - Which repo has the best approach?

**Deliverable**:
- Type system comparison report
- Coverage metrics for each repo
- Unified type hint style guide
- Migration plan for inconsistent repos

---

## Part 2: Shared Code Identification & Extraction

### 2.1 Duplicate Code Analysis

**Systematically identify code duplication:**

1. **S-expression processing**:
   - Parser logic in sch-api vs pcb-api
   - Formatter logic
   - Common utilities
   - Percentage overlap

2. **File I/O patterns**:
   - File loading/saving patterns
   - Temp file + atomic rename patterns
   - Error handling for file operations

3. **Collection implementations**:
   - Indexed collection base classes
   - Lookup optimization logic
   - Filtering/query logic

4. **Validation utilities**:
   - Common validation patterns
   - Error collection mechanisms
   - Validation result structures

5. **KiCAD integration**:
   - KiCAD CLI wrappers
   - Path detection
   - Version compatibility checks

**Deliverable**:
- Duplicate code inventory with line-by-line references
- Percentage overlap calculations
- Priority ranking for extraction

### 2.2 Shared Library Design

**Design a shared common library:**

1. **Proposed library name**: `kicad-common` or `circuit-synth-core`

2. **Proposed structure**:
```
kicad-common/
├── kicad_common/
│   ├── sexp/                   # S-expression parsing/formatting
│   │   ├── parser.py
│   │   ├── formatter.py
│   │   └── types.py
│   ├── collections/            # Shared collection base classes
│   │   ├── indexed.py
│   │   ├── filtered.py
│   │   └── bulk_ops.py
│   ├── validation/             # Common validation
│   │   ├── error_collection.py
│   │   ├── validators.py
│   │   └── results.py
│   ├── kicad/                  # KiCAD integration utilities
│   │   ├── cli.py
│   │   ├── paths.py
│   │   └── version.py
│   ├── io/                     # File I/O utilities
│   │   ├── atomic_write.py
│   │   └── safe_read.py
│   └── utils/                  # Generic utilities
│       ├── logging.py
│       └── config.py
└── tests/
```

3. **Extraction priorities**:
   - Phase 1: S-expression utilities (highest impact)
   - Phase 2: Collection base classes
   - Phase 3: Validation framework
   - Phase 4: KiCAD integration utilities

4. **Version management**:
   - How will shared library versions be managed?
   - Dependency specifications in all three repos
   - Breaking change policies

5. **Testing strategy**:
   - How will shared library be tested?
   - Integration tests in dependent repos
   - Backward compatibility guarantees

**Deliverable**:
- Detailed shared library design document
- Extraction roadmap with phases
- Migration guide for all three repos
- Testing strategy for shared library

### 2.3 API Standardization

**Identify and standardize common APIs:**

1. **Load/Save patterns**:
   - `load_schematic()` vs `load_pcb()` vs circuit-synth patterns
   - Save conventions
   - Error handling patterns

2. **Collection interfaces**:
   - Standard methods: `add()`, `remove()`, `get()`, `filter()`
   - Bulk operation APIs
   - Query interfaces

3. **Manager interfaces**:
   - Standard manager methods
   - Initialization patterns
   - State management

4. **Error handling**:
   - Exception hierarchies
   - Error message formats
   - Validation result structures

**Deliverable**:
- API standardization guide
- Interface specifications
- Migration plan for non-compliant APIs

---

## Part 3: Testing Infrastructure Unification

### 3.1 Testing Philosophy Alignment

**Compare testing approaches:**

1. **Test organization**:
   - Directory structures (`tests/`, naming conventions)
   - Test categorization (unit, integration, e2e, reference)
   - Marker usage consistency

2. **Test quality**:
   - Coverage percentages
   - Coverage targets and enforcement
   - Test naming conventions
   - AAA pattern consistency

3. **Reference testing**:
   - How reference tests work in sch-api vs pcb-api
   - Manual KiCAD file creation workflows
   - Format preservation validation strategies

4. **Fixture management**:
   - Pytest fixture organization
   - Fixture scopes and reusability
   - Test data organization

**Deliverable**:
- Testing philosophy comparison
- Unified testing guidelines document
- Best practices from each repo
- Coverage targets for all repos

### 3.2 Test Infrastructure Standardization

**Create consistent test infrastructure:**

1. **Pytest configuration**:
   - `pytest.ini` or `pyproject.toml` settings
   - Marker definitions
   - Plugin usage
   - Coverage configuration

2. **Test utilities**:
   - Shared test helpers
   - Mock factories
   - Assertion helpers
   - File comparison utilities

3. **CI/CD test execution**:
   - Test matrix consistency (Python versions, OS)
   - Test execution order
   - Parallel test execution
   - Performance benchmarking in CI

**Deliverable**:
- Unified pytest configuration
- Shared test utility library
- CI/CD testing strategy

### 3.3 Reference Testing Strategy

**Standardize reference-based testing:**

1. **Reference file organization**:
   - Directory structure for reference projects
   - Naming conventions
   - Documentation requirements

2. **Reference test workflow**:
   - Manual creation process (which repo has best workflow?)
   - Automation opportunities
   - Format validation approach

3. **Diff testing**:
   - File diff strategies
   - Acceptable differences (timestamps, UUIDs)
   - Semantic vs byte-level comparison

**Deliverable**:
- Unified reference testing guide
- Shared reference test utilities
- Reference project templates

---

## Part 4: Development Workflow & Tooling

### 4.1 Development Tool Alignment

**Standardize development tools:**

1. **Package management**:
   - uv usage consistency
   - Dependency specification patterns
   - Lock file management

2. **Code quality tools**:
   - Black configuration
   - isort configuration
   - flake8/ruff configuration
   - mypy configuration
   - Pre-commit hooks

3. **Build and release**:
   - pyproject.toml standardization
   - Version management patterns
   - Release automation
   - PyPI publishing workflows

**Deliverable**:
- Unified tool configuration files
- Development setup scripts
- Release process documentation

### 4.2 Claude Code Integration

**Analyze and unify Claude Code setup:**

1. **Custom commands comparison**:
   - Which commands exist in each repo?
   - Which are duplicated?
   - Which should be standardized?
   - Command organization patterns

2. **Agent integration**:
   - circuit-synth specialized agents
   - Agent implementation patterns
   - Agent configuration
   - How can agents be shared?

3. **Settings and hooks**:
   - `.claude/settings.json` comparison
   - Hook configurations
   - Model selection patterns
   - Best practices from each repo

4. **Documentation and discoverability**:
   - CLAUDE.md file comparison
   - Command documentation
   - Agent documentation

**Deliverable**:
- Unified Claude Code integration guide
- Standardized command library
- Shared agent implementations where applicable
- Best practices document

### 4.3 CI/CD Pipeline Standardization

**Align CI/CD across repos:**

1. **Workflow comparison**:
   - GitHub Actions configuration
   - Test matrices
   - Quality gates
   - Artifact publishing

2. **Test execution**:
   - Test parallelization
   - Cache strategies
   - Performance benchmarking
   - Coverage reporting

3. **Release automation**:
   - Version bumping
   - Changelog generation
   - PyPI publishing
   - GitHub releases

**Deliverable**:
- Unified GitHub Actions workflows
- CI/CD best practices guide
- Release automation templates

---

## Part 5: Documentation Standardization

### 5.1 Documentation Structure

**Compare and align documentation:**

1. **README structure**:
   - Which README is most comprehensive?
   - Section organization
   - Code examples
   - Installation instructions
   - Feature highlights

2. **API documentation**:
   - Docstring coverage and quality
   - Docstring format (Google vs NumPy vs Sphinx)
   - Auto-generated docs
   - Example code coverage

3. **Architecture documentation**:
   - System design documentation
   - Design decision records (ADR)
   - Module interdependencies
   - Integration patterns

4. **User guides**:
   - Quickstart guides
   - Tutorials
   - Best practices guides
   - Example projects

**Deliverable**:
- Unified documentation structure
- Documentation templates
- Style guide for docs
- Documentation gaps identified

### 5.2 Code Documentation Standards

**Standardize code-level documentation:**

1. **Docstring requirements**:
   - When are docstrings required?
   - Minimum docstring content
   - Type hint vs docstring redundancy
   - Example inclusion requirements

2. **Inline comments**:
   - When to use inline comments
   - Comment style and formatting
   - TODO/FIXME patterns
   - Complex logic documentation

3. **Module-level documentation**:
   - Module docstring requirements
   - Architecture documentation
   - Usage examples
   - Cross-references

**Deliverable**:
- Unified documentation style guide
- Docstring templates
- Documentation enforcement in CI

### 5.3 CLAUDE.md Standardization

**Align CLAUDE.md files:**

1. **Content comparison**:
   - Which CLAUDE.md is most comprehensive?
   - Section organization
   - Command documentation
   - Testing guidance
   - Architecture overview

2. **Required sections**:
   - Project overview
   - Architecture
   - Key commands
   - Testing strategy
   - Development workflow
   - Related projects

3. **Best practices**:
   - Which repo has the clearest guidance?
   - Testing workflows
   - Format preservation guidance (for sch/pcb)
   - Integration patterns

**Deliverable**:
- CLAUDE.md template
- Best practices compilation
- Updates for all three repos

---

## Part 6: Architecture & Integration Analysis

### 6.1 Integration Patterns

**Analyze how repos integrate:**

1. **circuit-synth → kicad-sch-api**:
   - How does circuit-synth use sch-api?
   - API surface used
   - Pain points or missing features
   - Abstraction layers

2. **circuit-synth → kicad-pcb-api**:
   - How does circuit-synth use pcb-api?
   - API surface used
   - Pain points or missing features
   - Abstraction layers

3. **Shared concepts**:
   - Nets (schematic vs PCB)
   - Components vs footprints
   - Properties and metadata
   - Coordinate systems
   - Design rules

4. **Bidirectional workflow**:
   - How does circuit-synth orchestrate both APIs?
   - Synchronization patterns
   - Data flow architecture
   - Error propagation

**Deliverable**:
- Integration architecture diagrams
- API usage patterns
- Missing feature identification
- Integration improvement roadmap

### 6.2 Dependency Management

**Analyze dependency relationships:**

1. **Version coupling**:
   - How are versions coordinated?
   - Breaking change impacts
   - Minimum version requirements
   - Version testing matrices

2. **Circular dependencies**:
   - Any circular dependencies between repos?
   - How are they avoided?
   - Abstraction boundaries

3. **Shared dependencies**:
   - Common third-party dependencies
   - Version alignment issues
   - Dependency conflict resolution

**Deliverable**:
- Dependency graph
- Version management strategy
- Dependency upgrade coordination plan

### 6.3 Data Model Alignment

**Compare and align data models:**

1. **Component representation**:
   - How are components modeled in each repo?
   - Property systems comparison
   - Metadata handling

2. **Net/connection modeling**:
   - Net representation in sch-api
   - Net representation in pcb-api
   - Net representation in circuit-synth
   - Alignment opportunities

3. **Geometric types**:
   - Point/Position types
   - Rotation/orientation
   - Bounding boxes
   - Coordinate system conventions

4. **Configuration systems**:
   - How is configuration handled?
   - Default values
   - User customization
   - Configuration serialization

**Deliverable**:
- Data model comparison diagrams
- Alignment opportunities
- Shared type library design
- Migration plan for unified types

---

## Part 7: Code Quality & Style Alignment

### 7.1 Coding Style Standards

**Compare and standardize style:**

1. **Naming conventions**:
   - Module naming
   - Class naming (PascalCase consistency)
   - Function naming (snake_case consistency)
   - Private vs public naming (`_private`)
   - Constants (UPPER_CASE)

2. **Code formatting**:
   - Line length (88 vs 100 vs 120)
   - String quotes (single vs double)
   - Import sorting
   - Blank lines and spacing

3. **Python idioms**:
   - List comprehensions vs loops
   - Context managers (`with` statements)
   - Exception handling patterns
   - Type annotations

**Deliverable**:
- Unified style guide
- Formatter configurations (Black, isort)
- Linter configurations
- Code review checklist

### 7.2 Error Handling Patterns

**Standardize error handling:**

1. **Exception hierarchies**:
   - Compare exception class hierarchies
   - Which is most comprehensive?
   - Naming conventions
   - Error categorization

2. **Error messages**:
   - Message formatting
   - Contextual information
   - Actionable guidance
   - Consistency across repos

3. **Error recovery**:
   - Graceful degradation
   - Rollback patterns
   - Validation before action
   - Multi-error collection

**Deliverable**:
- Unified exception hierarchy
- Error message guidelines
- Error handling best practices

### 7.3 Logging Standards

**Standardize logging approach:**

1. **Logging libraries**:
   - loguru usage in circuit-synth
   - Standard logging in sch-api/pcb-api?
   - Which approach is best?

2. **Log levels**:
   - When to use DEBUG vs INFO vs WARNING
   - Error logging patterns
   - Performance logging

3. **Log formatting**:
   - Structured logging
   - Timestamp formats
   - Contextual information

**Deliverable**:
- Unified logging guidelines
- Logger configuration templates
- Best practices document

---

## Part 8: Performance & Optimization

### 8.1 Performance Baseline

**Benchmark all three repos:**

1. **File I/O performance**:
   - Load time vs file size
   - Save time vs file size
   - Memory usage patterns

2. **Parsing performance**:
   - S-expression parsing speed (sch vs pcb)
   - Memory overhead
   - Optimization opportunities

3. **Collection operations**:
   - Lookup performance (O(1) verification)
   - Iteration performance
   - Filtering performance
   - Bulk operations

4. **Algorithm performance** (pcb-api):
   - Placement algorithm benchmarks
   - Routing performance
   - Collision detection

**Deliverable**:
- Performance benchmark suite
- Baseline measurements for all repos
- Performance regression tests

### 8.2 Optimization Opportunities

**Identify optimization potential:**

1. **Caching strategies**:
   - Symbol caching in sch-api
   - Similar patterns in pcb-api
   - Cache invalidation patterns
   - Memory vs speed tradeoffs

2. **Lazy loading**:
   - Where is lazy loading used?
   - Opportunities for lazy evaluation
   - Memory savings potential

3. **Algorithmic improvements**:
   - Data structure choices
   - Complexity analysis
   - Optimization low-hanging fruit

**Deliverable**:
- Optimization roadmap
- Priority ranking
- Expected performance gains

### 8.3 Scalability Assessment

**Test scalability limits:**

1. **Large file handling**:
   - 1000+ component schematics
   - 1000+ component PCBs
   - Complex hierarchical designs
   - Memory profiling

2. **Batch operations**:
   - Bulk component addition
   - Bulk property updates
   - Bulk validation

**Deliverable**:
- Scalability test results
- Bottleneck identification
- Scalability improvement plan

---

## Part 9: Special Topics

### 9.1 Format Preservation Strategies

**Compare format preservation (sch vs pcb):**

1. **Techniques used**:
   - How is exact format achieved?
   - Whitespace preservation
   - Comment preservation
   - UUID handling

2. **Testing strategies**:
   - Diff-based validation
   - Semantic equivalence
   - Round-trip testing

3. **Best practices**:
   - Which repo has better approach?
   - Lessons learned
   - Common pitfalls

**Deliverable**:
- Format preservation best practices
- Shared testing utilities
- Implementation guidelines

### 9.2 AI Integration Patterns

**Analyze AI integration (circuit-synth specific):**

1. **Agent architecture**:
   - How are agents implemented?
   - Agent communication patterns
   - State management

2. **LLM integration**:
   - API usage patterns
   - Prompt engineering
   - Response parsing

3. **Reusability potential**:
   - Can AI patterns be shared with sch/pcb APIs?
   - Agent framework extraction
   - Prompt library sharing

**Deliverable**:
- AI integration architecture doc
- Reusable components identification
- Integration guide for sch/pcb APIs

---

## Part 10: Feature Completeness & Parity

### 10.1 Feature Matrix

**Create comprehensive feature comparison:**

| Feature Category | circuit-synth | kicad-sch-api | kicad-pcb-api | Notes |
|-----------------|---------------|---------------|---------------|-------|
| File I/O | ✓ | ✓ | ✓ | |
| S-expression parsing | Indirect | ✓ | ✓ | Could be shared |
| Component management | ✓ | ✓ | ✓ | Different abstractions |
| Net management | ✓ | ✓ | ✓ | Alignment needed |
| Hierarchical design | ✓ | ✓ | Partial | PCB needs improvement |
| Placement algorithms | ✓ | N/A | ✓ | |
| Routing | ✓ | N/A | ✓ | |
| Validation | ✓ | ✓ | ✓ | Could be unified |
| AI integration | ✓ | - | - | Could extend to others |
| ... | ... | ... | ... | ... |

**Deliverable**:
- Complete feature matrix (50+ features)
- Feature coverage percentages
- Gap analysis

### 10.2 API Completeness

**Assess API coverage:**

1. **Essential operations**:
   - CRUD operations for all entities
   - Bulk operations
   - Query/filter capabilities
   - Validation and error handling

2. **Advanced features**:
   - Hierarchical design support
   - Complex manipulations
   - Performance optimizations
   - Extensibility hooks

3. **Missing capabilities**:
   - Features present in one but not others
   - User-requested features
   - Industry standard operations

**Deliverable**:
- API completeness assessment
- Priority ranking for missing features
- Implementation roadmap

### 10.3 Quality Assessment

**Rate feature quality across repos:**

For each major feature, rate on:
- **Correctness** (1-5): Does it work as documented?
- **Completeness** (1-5): Handles all use cases?
- **Robustness** (1-5): Edge case handling?
- **Performance** (1-5): Acceptable for real-world use?
- **Maintainability** (1-5): Code clarity and organization?

**Deliverable**:
- Feature quality matrix
- Improvement opportunities
- Refactoring priorities

---

## Part 11: Bidirectional & Tridirectional Insights

### 11.1 What circuit-synth Can Learn

**Improvements for circuit-synth from sch-api and pcb-api:**

1. **From kicad-sch-api**:
   - Exact format preservation techniques
   - Parser/formatter separation
   - Symbol caching strategies
   - Collection performance optimizations
   - Reference testing methodologies

2. **From kicad-pcb-api**:
   - Placement algorithm patterns
   - Manager separation of concerns
   - DSN/SES import/export patterns
   - Routing integration approaches

**Deliverable**: Specific improvements with file/line references

### 11.2 What kicad-sch-api Can Learn

**Improvements for kicad-sch-api from circuit-synth and pcb-api:**

1. **From circuit-synth**:
   - AI integration patterns
   - Higher-level abstractions
   - User-friendly APIs
   - Claude Code integration
   - Manufacturing integration

2. **From kicad-pcb-api**:
   - Manager pattern implementations
   - Testing organization
   - Documentation structure
   - Placement algorithm frameworks

**Deliverable**: Specific improvements with file/line references

### 11.3 What kicad-pcb-api Can Learn

**Improvements for kicad-pcb-api from circuit-synth and sch-api:**

1. **From circuit-synth**:
   - AI integration patterns
   - User-facing API design
   - Manufacturing integration
   - Component sourcing patterns

2. **From kicad-sch-api**:
   - Symbol caching patterns (for footprint libraries)
   - Collection implementations
   - Testing methodology
   - Documentation organization

**Deliverable**: Specific improvements with file/line references

---

## Part 12: Strategic Recommendations & Roadmap

### 12.1 Unification Strategy

**Create comprehensive unification plan:**

1. **Phase 1: Quick Wins (0-1 months)**
   - Standardize code formatting (Black, isort)
   - Align pytest configurations
   - Standardize CLAUDE.md files
   - Create shared coding style guide
   - Align exception naming conventions

2. **Phase 2: Shared Library Extraction (1-3 months)**
   - Extract S-expression utilities to `kicad-common`
   - Extract collection base classes
   - Extract validation framework
   - Update all three repos to use shared library
   - Establish version management strategy

3. **Phase 3: API Standardization (3-6 months)**
   - Standardize collection interfaces
   - Align manager patterns
   - Unify error handling
   - Create consistent load/save APIs

4. **Phase 4: Advanced Integration (6-12 months)**
   - Enhanced AI integration for sch/pcb APIs
   - Unified testing infrastructure
   - Shared Claude Code agents
   - Advanced performance optimizations

**Deliverable**:
- Detailed phase breakdown
- Task assignments
- Success criteria for each phase
- Risk assessment

### 12.2 Architecture Vision

**Long-term architectural goals:**

1. **Shared foundation**:
```
┌─────────────────────────────────────┐
│         circuit-synth               │ (High-level orchestration)
└────────┬─────────────────┬──────────┘
         │                 │
    ┌────▼──────┐     ┌────▼──────┐
    │ kicad-sch │     │ kicad-pcb │    (Domain-specific APIs)
    │    -api   │     │    -api   │
    └────────┬──┘     └──┬─────────┘
             │           │
             └─────┬─────┘
                   │
            ┌──────▼──────┐
            │ kicad-common│              (Shared foundation)
            │   - sexp    │
            │   - colls   │
            │   - valid   │
            └─────────────┘
```

2. **API boundaries**:
   - Clear separation between layers
   - Minimal coupling
   - Well-defined interfaces
   - Extensibility points

3. **Version management**:
   - Semantic versioning
   - Compatibility guarantees
   - Deprecation policies
   - Migration guides

**Deliverable**:
- Architecture vision document
- Layer responsibility matrix
- Interface specifications
- Governance model

### 12.3 Implementation Roadmap

**Prioritized action items:**

For each improvement identified:

| Priority | Task | Repo(s) | Effort | Impact | Dependencies | Owner |
|----------|------|---------|--------|--------|--------------|-------|
| P0 | Extract S-exp parser | All | 2 weeks | High | None | TBD |
| P0 | Standardize Black config | All | 1 day | Medium | None | TBD |
| P1 | Unify collection interfaces | All | 1 week | High | Shared lib | TBD |
| P1 | Align pytest config | All | 2 days | Medium | None | TBD |
| P2 | Create shared test utils | All | 1 week | Medium | Testing std | TBD |
| ... | ... | ... | ... | ... | ... | ... |

**Deliverable**:
- Complete prioritized task list (100+ items)
- Gantt chart or timeline
- Resource requirements
- Risk mitigation strategies

---

## Execution Strategy

### Parallel Analysis Approach

Execute this comparison using **18 parallel Sonnet agents** working simultaneously:

**Agent 1: Code Organization**
- Task: Part 1.1 - Module structure and organization
- Output: `01-code-organization.md`

**Agent 2: Design Patterns**
- Task: Part 1.2 - Design pattern alignment
- Output: `02-design-patterns.md`

**Agent 3: Type Systems**
- Task: Part 1.3 - Type hints and type system
- Output: `03-type-systems.md`

**Agent 4: Duplicate Code**
- Task: Part 2.1 - Identify all code duplication
- Output: `04-duplicate-code.md`

**Agent 5: Shared Library Design**
- Task: Part 2.2 - Design shared library
- Output: `05-shared-library-design.md`

**Agent 6: API Standardization**
- Task: Part 2.3 - API alignment
- Output: `06-api-standardization.md`

**Agent 7: Testing Infrastructure**
- Task: Part 3 (all subsections) - Testing unification
- Output: `07-testing-infrastructure.md`

**Agent 8: Development Tooling**
- Task: Part 4.1 and 4.2 - Tools and Claude Code
- Output: `08-development-tooling.md`

**Agent 9: CI/CD Pipelines**
- Task: Part 4.3 - CI/CD alignment
- Output: `09-cicd-pipelines.md`

**Agent 10: Documentation**
- Task: Part 5 (all subsections) - Documentation standards
- Output: `10-documentation.md`

**Agent 11: Integration Architecture**
- Task: Part 6 (all subsections) - Integration analysis
- Output: `11-integration-architecture.md`

**Agent 12: Code Quality**
- Task: Part 7 (all subsections) - Style and quality
- Output: `12-code-quality.md`

**Agent 13: Performance**
- Task: Part 8 (all subsections) - Performance analysis
- Output: `13-performance.md`

**Agent 14: Special Topics**
- Task: Part 9 (all subsections) - Format preservation, AI
- Output: `14-special-topics.md`

**Agent 15: Feature Completeness**
- Task: Part 10 (all subsections) - Feature matrix and gaps
- Output: `15-feature-completeness.md`

**Agent 16: Bidirectional Insights**
- Task: Part 11 (all subsections) - What each can learn
- Output: `16-bidirectional-insights.md`

**Agent 17: Strategic Roadmap**
- Task: Part 12 (all subsections) - Unification and vision
- Output: `17-strategic-roadmap.md`

**Agent 18: Consolidation**
- Task: Synthesize all findings into executive summary
- Output: `00-executive-summary.md`, `README.md`, `IMPLEMENTATION-PLAN.md`

### Agent Instructions

Each agent should:

1. **Analyze all three repositories** at specified paths
2. **Create detailed markdown** with specific code references (`file:line`)
3. **Use comparison tables** for side-by-side analysis
4. **Quantify findings** with metrics and percentages
5. **Provide actionable recommendations** with priorities
6. **Reference related findings** from other agents
7. **Follow consistent formatting** (H2 for sections, H3 for subsections)
8. **Include code examples** where relevant
9. **Rate quality** on 1-5 scales where applicable
10. **Be specific, not vague** - always cite exact locations

### Timeline

- **Parallel execution**: ~60-90 minutes per agent
- **Consolidation**: ~60 minutes
- **Total elapsed time**: ~2-3 hours
- **Total effort**: ~25-30 hours (18 agents × 1.5 hours)
- **Output**: 70-100 pages across 18+ markdown files

---

## Deliverable Structure

All outputs organized in `three-repo-comparison/` directory:

```
three-repo-comparison/
├── README.md                          # Navigation and index
├── 00-executive-summary.md            # High-level synthesis (10-15 pages)
├── 01-code-organization.md            # Module structure analysis
├── 02-design-patterns.md              # Pattern alignment
├── 03-type-systems.md                 # Type hint strategy
├── 04-duplicate-code.md               # Duplication analysis
├── 05-shared-library-design.md        # Common library design
├── 06-api-standardization.md          # API alignment
├── 07-testing-infrastructure.md       # Testing unification
├── 08-development-tooling.md          # Dev tools and Claude Code
├── 09-cicd-pipelines.md               # CI/CD alignment
├── 10-documentation.md                # Docs standardization
├── 11-integration-architecture.md     # Integration patterns
├── 12-code-quality.md                 # Style and quality
├── 13-performance.md                  # Performance benchmarks
├── 14-special-topics.md               # Format preservation, AI
├── 15-feature-completeness.md         # Feature matrix
├── 16-bidirectional-insights.md       # Cross-learning opportunities
├── 17-strategic-roadmap.md            # Unification strategy
├── IMPLEMENTATION-PLAN.md             # Detailed action items
├── ARCHITECTURE-DIAGRAMS.md           # Visual representations
└── SHARED-LIBRARY-SPEC.md             # kicad-common specification
```

---

## Success Criteria

This comparison succeeds when it delivers:

1. ✅ **Comprehensive coverage**: All 12 major areas analyzed across all 3 repos
2. ✅ **Specific findings**: 100+ concrete observations with code references
3. ✅ **Quantified metrics**: Coverage %, performance numbers, duplication %
4. ✅ **Actionable roadmap**: Prioritized 200+ task list with effort estimates
5. ✅ **Shared library design**: Complete specification for `kicad-common`
6. ✅ **Best practices compilation**: Unified guidelines for all repos
7. ✅ **Architecture vision**: Clear long-term direction
8. ✅ **Integration patterns**: Documented inter-repo collaboration
9. ✅ **Quality assessment**: Feature ratings and improvement priorities
10. ✅ **Executive-ready**: Summary suitable for decision-makers

---

## Key Principles

1. **Equality**: No repo is "better" - each has lessons for the others
2. **Evidence-based**: Every claim supported by code references
3. **Practical**: Focus on implementable improvements, not theory
4. **Balanced**: Acknowledge tradeoffs and context
5. **Specific**: Cite exact files and line numbers
6. **Quantified**: Provide metrics wherever possible
7. **Prioritized**: Rank recommendations by impact/effort
8. **Holistic**: Consider the entire ecosystem, not isolated repos

---

**This command enables comprehensive analysis of the circuit-synth ecosystem with focus on practical unification, best practice adoption, and strategic alignment across all three repositories.**
