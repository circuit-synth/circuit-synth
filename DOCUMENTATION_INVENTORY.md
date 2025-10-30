# Circuit-Synth Documentation Inventory

**Date:** 2025-10-30
**Purpose:** Complete list of all documentation files for alignment audit

---

## 🎯 PRIMARY USER-FACING DOCUMENTATION (CRITICAL)

These are what users see first and must be perfectly aligned.

### PyPI Package Documentation
1. **`README.md`** (root) - **PRIMARY SOURCE OF TRUTH**
   - Line count: 1065 lines
   - Used as PyPI long_description
   - First thing users see on pypi.org/project/circuit-synth
   - Contains: Installation, Quick Start, Examples, Features
   - Status: ⚠️ **HAS PATH ERRORS** (identified 4 critical issues)

2. **`pyproject.toml`** - Package metadata
   - Description: "Pythonic circuit design for production-ready KiCad projects"
   - readme = "README.md" (correctly references primary doc)
   - URLs: Homepage, Documentation, Repository, Issues
   - Status: ✅ **CORRECT**

### ReadTheDocs Documentation (circuit-synth.readthedocs.io)

3. **`.readthedocs.yaml`** - RTD build configuration
   - Python 3.12, Sphinx, PDF/EPUB export
   - Status: ✅ **CORRECT**

4. **`docs/conf.py`** - Sphinx configuration
   - Project metadata, theme, extensions
   - Status: ✅ **CORRECT**

5. **`docs/index.rst`** - Main documentation landing page
   - Quick Start, Core Principles, Current Capabilities
   - Status: ⚠️ **Missing `uv` installation method**

6. **`docs/installation.rst`** - Installation guide
   - Status: ❓ **NEEDS REVIEW**

7. **`docs/quickstart.rst`** - Quick start guide
   - Status: ❓ **NEEDS REVIEW**

8. **`docs/examples.rst`** - Example circuits
   - Status: ❓ **NEEDS REVIEW**

---

## 📚 SECONDARY TECHNICAL DOCUMENTATION

### Core Architecture & Design

9. **`docs/ARCHITECTURE.md`** - System architecture overview
10. **`docs/KICAD_SCH_API_INTEGRATION.md`** - KiCad schematic API integration
11. **`docs/JSON_SCHEMA.md`** - Circuit JSON schema documentation
12. **`docs/PROJECT_STRUCTURE.md`** - Project organization guide

### Feature-Specific Documentation

13. **`docs/BOM_EXPORT.md`** - Bill of Materials export guide
14. **`docs/PDF_EXPORT.md`** - PDF schematic export guide
15. **`docs/GERBER_EXPORT.md`** - Gerber manufacturing files export
16. **`docs/FMEA_GUIDE.md`** - Failure Mode and Effects Analysis guide
17. **`docs/SIMULATION_SETUP.md`** - SPICE simulation setup
18. **`docs/test_plan_generation.md`** - Test plan generation

### Development & Testing

19. **`docs/TESTING.md`** - Testing strategy and guidelines
20. **`docs/CONTRIBUTING.md`** - Contribution guidelines
21. **`docs/SCRIPT_REFERENCE.md`** - Command-line scripts reference
22. **`docs/ai_agents.rst`** - AI agent system documentation

### Product Requirements & Planning

23. **`docs/PRD_KICAD_SYNCER_REFACTOR.md`** - Sync refactor PRD
24. **`docs/PRD_KICAD_TO_JSON_EXPORT.md`** - JSON export PRD
25. **`docs/PRD_Multi_Agent_Haiku_Architecture.md`** - Multi-agent architecture
26. **`docs/PRD_SUMMARY.md`** - PRD summary
27. **`docs/PRD_Self_Improving_Agents.md`** - Self-improving agents PRD
28. **`docs/prd/migration-executive-summary.md`** - Migration summary
29. **`docs/prd/no_connect_feature.md`** - No-connect feature spec

### Testing Documentation

30. **`docs/testing/BIDIRECTIONAL_SYNC_STATUS.md`** - Sync status
31. **`docs/testing/README.md`** - Testing overview
32. **`docs/testing/TESTING_PLAN_SUMMARY.md`** - Test plan summary
33. **`docs/testing/TEST_FIXES_SUMMARY.md`** - Test fixes summary

---

## 🔧 INTERNAL/DEVELOPMENT DOCUMENTATION

### Release & CI/CD

34. **`.claude/commands/dev/release-pypi.md`** - PyPI release command
    - Status: ⚠️ **NEEDS DOC VALIDATION CHECKS ADDED**

35. **`tools/testing/PRE_RELEASE_CHECKLIST.md`** - Pre-release checklist
36. **`tools/ci-setup/CI_SETUP.md`** - CI setup guide
37. **`src/circuit_synth/data/tools/ci-setup/CI_SETUP.md`** - CI setup (duplicate?)

### Developer Guides

38. **`CLAUDE.md`** (root) - Claude Code development guide
    - Status: ✅ **PROJECT-SPECIFIC, CORRECT**

39. **`src/circuit_synth/data/CLAUDE.md`** - Template CLAUDE.md
40. **`tools/README.md`** - Tools overview
41. **`tools/CONSOLIDATION_PLAN.md`** - Tool consolidation plan

### Website Documentation

42. **`website/DEPLOYMENT.md`** - Website deployment guide
    - Status: ❓ **NEEDS REVIEW FOR ALIGNMENT**

---

## 📦 COMPONENT/MODULE-SPECIFIC DOCUMENTATION

### KiCad Integration

43. **`src/circuit_synth/kicad/README.md`** - KiCad module overview
44. **`src/circuit_synth/kicad/pcb_gen/README.md`** - PCB generation
45. **`src/circuit_synth/kicad/sch_gen/NEW_API_INTEGRATION_SUMMARY.md`** - New API summary

### Tools & Utilities

46. **`src/circuit_synth/tools/README.md`** - Tools module overview
47. **`src/circuit_synth/data/tools/README.md`** - Data tools

### Fast Generation & Reference Circuits

48. **`src/circuit_synth/fast_generation/reference_circuits/README.md`** - Reference circuits

### KiCad Plugins

49. **`kicad_plugins/README_SIMPLIFIED.md`** - Simplified plugin docs

---

## 🧪 TEST DOCUMENTATION

### Test Data & Fixtures

50. **`tests/README.md`** - Test suite overview
51. **`tests/fixtures/README.md`** - Test fixtures
52. **`tests/cache/README.md`** - Test cache
53. **`tests/test_data/custom_libraries/README.md`** - Custom libraries

### Bidirectional Sync Tests (47 test case READMEs)

54. **`tests/bidirectional/README.md`** - Bidirectional test overview
55-99. **`tests/bidirectional/XX_*/README.md`** - Individual test case docs
    - 01_blank_circuit through 48_multi_voltage_subcircuit
    - Each test has its own README explaining the test case
    - Status: ❓ **INTERNAL DOCS, LOW PRIORITY FOR USER ALIGNMENT**

### Other Test Docs

100. **`tests/test_bidirectional_automated/README.md`** - Automated tests
101. **`tests/test_bidirectional_automated/IMPLEMENTATION_STATUS.md`** - Status
102. **`tests/kicad_to_python/README.md`** - KiCad import tests
103. **`tests/kicad_to_python/04_esp32_c6_hierarchical/README.md`** - ESP32 test

---

## 📚 SUBMODULE DOCUMENTATION (External Projects)

### kicad-pcb-api (Submodule)

104. **`submodules/kicad-pcb-api/README.md`**
105. **`submodules/kicad-pcb-api/CLAUDE.md`**
106. **`submodules/kicad-pcb-api/INTEGRATION.md`**
107. **`submodules/kicad-pcb-api/docs/ARCHITECTURE_ANALYSIS.md`**
108. **`submodules/kicad-pcb-api/docs/IMPLEMENTATION_PLAN.md`**
109. **`submodules/kicad-pcb-api/docs/IMPROVEMENTS_ROADMAP.md`**
110. **`submodules/kicad-pcb-api/docs/PROGRESS_SUMMARY.md`**
111. **`submodules/kicad-pcb-api/src/kicad_pcb_api/README.md`**
112. **`submodules/kicad-pcb-api/src/kicad_pcb_api/routing/CHANGELOG.md`**
113. **`submodules/kicad-pcb-api/src/kicad_pcb_api/routing/FREEROUTING_SETUP.md`**

### Other Submodules

114. **`submodules/kicad-cli-docker/README.md`**
115. **`submodules/modm-devices/README.md`**
116. **`submodules/digikey-kicad/README.md`**
117. **`submodules/digikey-kicad/LICENSE.md`**

Status: ❓ **EXTERNAL, EXCLUDE FROM ALIGNMENT AUDIT**

---

## 📊 DOCUMENTATION ALIGNMENT PRIORITY

### CRITICAL (Must align perfectly - user-facing)

1. **README.md** ← PyPI long_description, GitHub landing page
2. **docs/index.rst** ← ReadTheDocs landing page
3. **docs/installation.rst** ← Installation instructions
4. **docs/quickstart.rst** ← Getting started guide
5. **pyproject.toml** ← Package metadata

**Action Required:**
- Fix 4 path errors in README.md
- Standardize installation instructions across all 5 files
- Ensure Quick Start examples work as written

### HIGH (Technical reference - must be accurate)

6. **docs/ARCHITECTURE.md**
7. **docs/BOM_EXPORT.md**
8. **docs/PDF_EXPORT.md**
9. **docs/GERBER_EXPORT.md**
10. **docs/FMEA_GUIDE.md**

**Action Required:**
- Verify all code examples work
- Check for outdated API references

### MEDIUM (Developer documentation - important but less visible)

11. **.claude/commands/dev/release-pypi.md**
12. **docs/CONTRIBUTING.md**
13. **docs/TESTING.md**
14. **CLAUDE.md**

**Action Required:**
- Add documentation validation to release-pypi.md
- Update any outdated development workflows

### LOW (Internal/legacy documentation)

15. All PRD documents (planning artifacts)
16. Test case READMEs (internal testing)
17. Tool-specific READMEs (developer tools)

**Action Required:**
- Archive or move to /docs/archive/ if outdated
- No immediate alignment needed

### EXCLUDE (External projects)

- All submodule documentation (kicad-pcb-api, digikey-kicad, etc.)
- These are separate projects with their own docs

---

## 🎯 ALIGNMENT STRATEGY

### Phase 1: Fix Critical User-Facing Errors (NOW)

**Files to fix:**
1. README.md - Fix 4 path errors
2. docs/index.rst - Add uv installation
3. docs/installation.rst - Standardize installation
4. docs/quickstart.rst - Verify examples work

**Time Estimate:** 30-45 minutes
**Impact:** Prevents user confusion, improves first experience

### Phase 2: Verify Technical Documentation (NEXT)

**Files to review:**
1. docs/BOM_EXPORT.md
2. docs/PDF_EXPORT.md
3. docs/GERBER_EXPORT.md
4. docs/FMEA_GUIDE.md
5. docs/ARCHITECTURE.md

**Check for:**
- Outdated code examples
- Wrong import statements
- Deprecated API usage

**Time Estimate:** 1-2 hours
**Impact:** Ensures technical docs are trustworthy

### Phase 3: Add Automation (THEN)

**Files to update:**
1. .claude/commands/dev/release-pypi.md - Add doc validation
2. Create automated tests for README examples
3. Add pre-commit hooks for doc validation

**Time Estimate:** 1-2 hours
**Impact:** Prevents future documentation drift

### Phase 4: Clean Up Legacy Docs (LATER)

**Action:**
- Move outdated PRD docs to /docs/archive/
- Remove duplicate README files
- Consolidate test documentation

**Time Estimate:** 2-3 hours
**Impact:** Reduces confusion, easier maintenance

---

## 📋 NEXT STEPS

1. **Review this inventory** with user - did we miss anything?
2. **Prioritize fixes** - start with Phase 1 (critical user-facing docs)
3. **Execute alignment** - fix one phase at a time
4. **Add automation** - prevent future drift

---

## 📝 NOTES

- Total documentation files identified: **117 files**
- Critical user-facing files: **5 files**
- High-priority technical docs: **5 files**
- Internal/developer docs: **~50 files**
- Test documentation: **~50 files**
- External submodule docs: **~14 files** (excluded from audit)

**Key Finding:** The documentation problem is NOT quantity (117 files is reasonable), it's **inconsistency between the 5 critical user-facing files** that users encounter first.

**Root Cause:** Recent refactoring changed project structure, but only code was updated - documentation wasn't kept in sync.

**Solution:** Fix the 5 critical files first (Phase 1), then add automation to prevent future drift (Phase 3).
