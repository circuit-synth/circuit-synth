# Regression Test Document: Develop to Main

## Overview
This document outlines the comprehensive changes from `develop` to `main` branch and provides regression testing guidelines to ensure no functionality is broken during the merge.

**Change Summary:**
- 226 files changed: 39,103 insertions, 5,909 deletions
- Major features: Local KiCad integration, Agent system expansion, SPICE simulation, Unified pin access

## Critical Changes Requiring Testing

### 1. Local KiCad Integration ⚠️ **HIGH RISK**

**Files Removed:**
```
docker/*                                      - All containerized infrastructure removed
scripts/circuit-synth-docker                  - CLI wrapper removed
scripts/run-with-kicad.sh                     - Containerized runtime removed
```

**Impact:** Circuit-synth now requires local KiCad installation instead of containers
**Regression Tests:**
- [ ] Verify local KiCad installation detection works
- [ ] Test KiCad symbol/footprint search with local installation
- [ ] Validate schematic generation with local KiCad
- [ ] Ensure error messages guide users to install KiCad locally

### 2. Agent System Expansion 🔄 **MEDIUM RISK**

**Changes:**
```
+.claude/agents/simulation-expert.md           - New agent for SPICE
-.claude/agents/architect.md                   - Removed agents  
-.claude/agents/code.md
-.claude/agents/orchestrator.md
-.claude/agents/power-expert.md
-.claude/agents/signal-integrity.md
+src/circuit_synth/agents/circuit_creator_agent.py  - 700+ lines new
```

**Impact:** Major agent system restructuring
**Regression Tests:**
- [ ] Test agent discovery and loading
- [ ] Validate circuit creation agent functionality
- [ ] Ensure simulation-expert agent works with SPICE
- [ ] Check that removed agents don't break existing workflows

### 3. SPICE Simulation Integration 🆕 **MEDIUM RISK**

**New Files:**
```
+src/circuit_synth/simulation/__init__.py      - 39 lines
+src/circuit_synth/simulation/analysis.py     - 115 lines
+src/circuit_synth/simulation/converter.py    - 313 lines  
+src/circuit_synth/simulation/simulator.py    - 236 lines
+examples/circuit_synth_simulation_demo.py    - 219 lines
+examples/simple_pspice_example.py            - 188 lines
```

**Impact:** Complete new SPICE simulation capability
**Regression Tests:**
- [ ] Test SPICE netlist generation from circuits
- [ ] Validate simulation execution and results
- [ ] Check PySpice integration and dependencies
- [ ] Ensure simulation examples work end-to-end

### 4. Unified Pin Access Interface 🔄 **HIGH RISK**

**Core Changes:**
```
+src/circuit_synth/core/component.py          - 180+ lines added
+examples/demo_unified_pin_access.py          - 108 lines
+examples/test_unified_pin_access.py          - 160 lines
```

**Impact:** New `component.pins.VCC` syntax alongside existing `component["VCC"]`
**Regression Tests:**
- [ ] Test both old and new pin access syntaxes work
- [ ] Validate pin name resolution and error handling
- [ ] Check compatibility with existing circuit designs
- [ ] Ensure no breaking changes to established patterns

### 5. Advanced Examples and Agent Training 📚 **LOW RISK**

**Major Additions:**
```
+examples/advanced/stm32_development_board.py - 478 lines
+examples/agent-training/*                    - Extensive training data
+src/circuit_synth/data/examples/*            - Duplicated examples
```

**Impact:** Large example library for agent training
**Regression Tests:**
- [ ] Verify all examples execute without errors
- [ ] Check STM32 development board generates valid KiCad
- [ ] Validate agent training examples for accuracy
- [ ] Test example discovery and loading

### 6. Documentation Reorganization 📖 **LOW RISK**

**Moved Files:**
```
CONTRIBUTING.md → docs/CONTRIBUTING.md
PROJECT_STRUCTURE.md → docs/PROJECT_STRUCTURE.md
+docs/PERFORMANCE_OPTIMIZATION.md             - 201 lines
+docs/SETUP_CLAUDE_INTEGRATION.md             - 334 lines
+docs/SIMULATION_SETUP.md                     - 165 lines
```

**Impact:** Better organized documentation structure
**Regression Tests:**
- [ ] Verify all documentation links work
- [ ] Check README references to moved files
- [ ] Validate Claude integration setup instructions

## Test Execution Plan

### Phase 1: Core Functionality (Critical)
```bash
# Test basic circuit creation still works
uv run pytest tests/unit/test_core_circuit.py -v

# Test KiCad integration with local installation
uv run pytest tests/kicad/ -v

# Test netlist generation
uv run pytest tests/kicad_netlist_exporter/ -v
```

### Phase 2: New Features (Important)
```bash
# Test unified pin access
python examples/demo_unified_pin_access.py
python examples/test_unified_pin_access.py

# Test SPICE simulation
python examples/circuit_synth_simulation_demo.py
python examples/simple_pspice_example.py

# Test advanced examples
python examples/advanced/stm32_development_board.py
```

### Phase 3: Agent System (Important)
```bash
# Test agent registration and discovery
uv run register-agents

# Test circuit creator agent
# (Manual test through Claude Code interface)

# Test example-driven agent training
python -m circuit_synth.tools.circuit_creator_cli
```

### Phase 4: Integration Tests (Validation)
```bash
# Run comprehensive test suite
./scripts/run_all_tests.sh

# Test Rust integration still works
./scripts/test_rust_modules.sh

# Validate formatting and linting
make format-check
make lint
```

## Known Risks and Mitigations

### Risk 1: Local KiCad Dependency
**Risk:** Users without local KiCad installation may be unable to run circuit-synth
**Mitigation:** 
- Update installation docs to require local KiCad
- Add clear error messages for missing KiCad
- Test on fresh systems without KiCad installed

### Risk 2: Agent System Changes
**Risk:** Existing Claude Code workflows may break due to removed agents
**Mitigation:**
- Test all documented Claude Code workflows
- Update CLAUDE.md with current agent list
- Verify agent discovery mechanism works

### Risk 3: Pin Access API Changes  
**Risk:** Dual API for pin access may cause confusion or bugs
**Mitigation:**
- Extensive testing of both syntaxes
- Clear documentation of recommended approach
- Backward compatibility validation

### Risk 4: Large Example Dataset
**Risk:** Duplicated examples may become inconsistent or outdated
**Mitigation:**
- Implement example consistency checks
- Create update mechanism for example synchronization
- Regular validation of example accuracy

## Success Criteria

**Must Pass:**
- [ ] All existing unit tests pass
- [ ] KiCad integration works without Docker
- [ ] Basic circuit creation → schematic generation workflow
- [ ] Pin access with both old and new syntax
- [ ] Agent discovery and loading

**Should Pass:**
- [ ] SPICE simulation examples execute successfully
- [ ] Advanced STM32 example generates valid KiCad
- [ ] Documentation links and references work
- [ ] Formatting and linting checks pass

**Nice to Have:**
- [ ] All example files execute without warnings
- [ ] Agent training examples provide good coverage
- [ ] Performance improvements are measurable

## Post-Merge Validation

After merging to main, validate on clean environment:

1. **Fresh Installation Test:**
   ```bash
   git clone <repo>
   cd circuit-synth2
   uv pip install -e ".[dev]"
   uv run register-agents
   ```

2. **End-to-End Workflow:**
   ```bash
   python examples/example_kicad_project.py
   # Verify KiCad files are generated and valid
   ```

3. **Claude Code Integration:**
   - Test specialized agents work correctly
   - Verify slash commands function
   - Check memory bank integration

This regression testing plan ensures that the significant changes from develop to main don't break existing functionality while validating new features work as expected.