# Bidirectional Update Testing Pattern

## Systematic Testing Approach

### Directory Structure Pattern
```
bidirectional_update_test/
├── BIDIRECTIONAL_TEST_WORKFLOW.md     # Master workflow guide
├── step0_initial_kicad/                # Manual KiCad baseline
├── step1_imported_python/              # KiCad → Python 
├── step2_generated_kicad/              # Python → KiCad
├── step3_manual_kicad_edits/           # Simulate user changes
├── step4_reimported_python/            # Modified KiCad → Python  
├── step5_python_additions/             # Add components in Python
└── step6_bidirectional_sync/           # Final integration
```

### Command Patterns That Work

#### KiCad → Python Import
```bash
# Directory to directory (works)
uv run kicad-to-python <kicad_project_dir> <output_dir>

# Project to specific file (overwrites completely)  
uv run kicad-to-python <kicad_project_dir> <python_file> --backup
```

#### Python → KiCad Generation
```bash
cd <python_dir>
uv run python main.py
# Generates KiCad project in working directory
```

### Testing Validation Pattern

#### For Each Step
1. **Document expected behavior**
2. **Run actual commands**  
3. **Compare expected vs actual results**
4. **Update documentation with findings**
5. **Only proceed if step passes or gaps are documented**

#### Evidence Collection
- Command outputs and logs
- File diffs between expected and actual
- Screenshots of KiCad before/after
- Preservation test results

### Success Criteria Template

```markdown
**Test Questions:**
- [ ] Does command execute without errors?
- [ ] Are expected files generated?
- [ ] Is content structurally correct? 
- [ ] Are user modifications preserved?
- [ ] Can KiCad open generated files?

**Results:**
- ✅ Success items
- ⚠️  Partial/workaround items  
- ❌ Failed items with details
```

## Reusable for Other Features

This pattern works for testing any complex circuit-synth workflow:
1. **Step-by-step progression** from simple to complex
2. **Separate directories** for each step (enables retesting)
3. **Clear success criteria** and validation
4. **Documentation updates** with actual vs expected behavior