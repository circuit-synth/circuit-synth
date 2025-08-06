"""
Memory-Bank File Templates

Standard templates for memory-bank markdown files with consistent formatting.
"""

from datetime import datetime
from typing import Any, Dict

DECISIONS_TEMPLATE = """# Design Decisions

*This file automatically tracks design decisions and component choices*

## Template Entry
**Date**: YYYY-MM-DD  
**Change**: Brief description of what changed  
**Commit**: Git commit hash  
**Rationale**: Why this change was made  
**Alternatives Considered**: Other options evaluated  
**Impact**: Effects on design, cost, performance  
**Testing**: Any validation performed  

---

"""

FABRICATION_TEMPLATE = """# Fabrication History

*This file tracks PCB orders, delivery, and assembly notes*

## Template Order
**Order ID**: Vendor order number  
**Date**: YYYY-MM-DD  
**Specs**: Board specifications (size, layers, finish, etc.)  
**Quantity**: Number of boards ordered  
**Cost**: Total cost including shipping  
**Expected Delivery**: Estimated delivery date  
**Status**: Order status and tracking information  
**Received**: Actual delivery date and quality notes  
**Assembly Notes**: Assembly process and any issues  

---

"""

TESTING_TEMPLATE = """# Testing Results

*This file tracks test results, measurements, and performance validation*

## Template Test
**Test Name**: Brief description of test performed  
**Date**: YYYY-MM-DD  
**Setup**: Test equipment and conditions  
**Results**: Measured values and outcomes  
**Specification**: Expected values and pass/fail status  
**Notes**: Additional observations and analysis  

---

"""

TIMELINE_TEMPLATE = """# Project Timeline

*This file tracks project milestones, key events, and deadlines*

## Template Milestone
**Date**: YYYY-MM-DD  
**Milestone**: Brief description of milestone or event  
**Status**: Completed, In Progress, Planned  
**Details**: Additional context and notes  
**Next Steps**: What needs to happen next  

---

"""

ISSUES_TEMPLATE = """# Issues & Solutions

*This file tracks problems encountered, root causes, and solutions*

## Template Issue
**Date**: YYYY-MM-DD  
**Issue**: Brief description of the problem  
**Severity**: Low, Medium, High, Critical  
**Root Cause**: Technical analysis of what caused the issue  
**Solution**: How the problem was resolved  
**Prevention**: Steps to avoid similar issues in future  
**Status**: Open, In Progress, Resolved  

---

"""


def generate_claude_md(project_name: str, boards: list = None, **kwargs) -> str:
    """Generate project-specific CLAUDE.md with memory-bank documentation."""

    boards = boards or ["board-v1", "board-v2"]
    timestamp = datetime.now().isoformat()

    # Extract optional parameters
    project_specific_instructions = kwargs.get(
        "project_specific_instructions", "Add any project-specific instructions here."
    )

    template = f"""# CLAUDE.md - {project_name}

This file provides guidance to Claude Code when working on the {project_name} project.

## Memory-Bank System

This project uses the Circuit Memory-Bank System for automatic engineering documentation and project knowledge preservation.

### Overview
The memory-bank system automatically tracks:
- **Design Decisions**: Component choices and rationale
- **Fabrication History**: PCB orders, delivery, and assembly
- **Testing Results**: Performance data and issue resolution
- **Timeline Events**: Project milestones and key dates
- **Cross-Board Insights**: Knowledge shared between PCB variants

### Multi-Level Agent System

This project uses a nested agent structure:

```
{project_name}/
├── .claude/                    # Project-level agent
├── pcbs/
"""

    # Add board structure dynamically
    for i, board in enumerate(boards):
        template += f"""│   ├── {board}/
│   │   ├── .claude/           # PCB-level agent
│   │   └── memory-bank/       # PCB-specific documentation
"""

    template += f"""```

### Context Switching

Use the `cs-switch-board` command to work on specific PCBs:

```bash
# Switch to specific board context
cs-switch-board {boards[0] if boards else 'board-name'}

# List available boards
cs-switch-board --list

# Check current context
cs-switch-board --status
```

**Important**: `cs-switch-board` will compress Claude's memory and reload the appropriate .claude configuration. This ensures you're working with the right context and memory-bank scope.

### Memory-Bank Files

Each PCB maintains standard memory-bank files:

- **decisions.md**: Component choices, design rationale, alternatives considered
- **fabrication.md**: PCB orders, delivery tracking, assembly notes
- **testing.md**: Test results, measurements, performance validation
- **timeline.md**: Project milestones, key events, deadlines
- **issues.md**: Problems encountered, root causes, solutions

### Automatic Documentation

The system automatically updates memory-bank files when you:
- Make git commits (primary trigger)
- Run circuit-synth commands
- Ask questions about the design
- Perform tests or measurements

**Best Practices for Commits**:
- Use descriptive commit messages explaining **why** changes were made
- Commit frequently to capture incremental design decisions
- Include context about alternatives considered
- Mention any testing or validation performed

Examples:
```bash
# Good commit messages for memory-bank
git commit -m "Switch to buck converter for better efficiency - tested 90% vs 60% with linear reg"
git commit -m "Add external crystal for USB stability - internal RC caused enumeration failures"
git commit -m "Increase decoupling cap to 22uF - scope showed 3.3V rail noise during WiFi tx"
```

### Memory-Bank Commands

```bash
# Initialize memory-bank in existing project
cs-memory-bank-init

# Remove memory-bank system
cs-memory-bank-remove

# Check memory-bank status
cs-memory-bank-status

# Search memory-bank content
cs-memory-bank-search "voltage regulator"
```

### Troubleshooting

**Context Issues**:
- If Claude seems confused about which board you're working on, use `cs-switch-board --status`
- Use `cs-switch-board {{board_name}}` to explicitly set context

**Memory-Bank Updates Not Working**:
- Ensure you're committing through git (primary trigger for updates)
- Check that memory-bank files exist in current board directory
- Verify .claude configuration includes memory-bank instructions

**File Corruption**:
- All memory-bank files are in git - use `git checkout` to recover
- Use `cs-memory-bank-init` to recreate missing template files

## Project-Specific Instructions

{project_specific_instructions}

---

*This CLAUDE.md was generated automatically by circuit-synth memory-bank system*  
*Last updated: {timestamp}*
"""

    return template


# Template file mapping for easy access
TEMPLATE_FILES = {
    "decisions.md": DECISIONS_TEMPLATE,
    "fabrication.md": FABRICATION_TEMPLATE,
    "testing.md": TESTING_TEMPLATE,
    "timeline.md": TIMELINE_TEMPLATE,
    "issues.md": ISSUES_TEMPLATE,
}


def get_template(filename: str) -> str:
    """Get template content for a specific memory-bank file."""
    return TEMPLATE_FILES.get(filename, "")


def get_all_templates() -> Dict[str, str]:
    """Get all template files as a dictionary."""
    return TEMPLATE_FILES.copy()
