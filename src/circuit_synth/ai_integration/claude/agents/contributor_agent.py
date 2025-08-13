"""
Circuit-Synth Contributor Agent

A specialized Claude Code agent designed to help contributors understand the codebase,
follow conventions, and make meaningful contributions to circuit-synth.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..agent_registry import register_agent


@register_agent("contributor")
class ContributorAgent:
    """
    Specialized Claude Code agent for circuit-synth contributors.

    This agent helps new and existing contributors:
    - Understand the project architecture and codebase
    - Follow coding conventions and best practices
    - Write proper tests using TDD approach
    - Use development tools and commands effectively
    """

    def __init__(self):
        self.name = "contributor"
        self.description = (
            "Circuit-synth contributor onboarding and development assistant"
        )
        self.version = "1.0.0"

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "codebase_navigation",
            "architecture_explanation",
            "coding_conventions",
            "testing_guidance",
            "development_workflow",
            "code_review_preparation",
            "issue_analysis",
            "contribution_planning",
        ]

    def get_system_prompt(self) -> str:
        """
        Return the system prompt that defines this agent's behavior.

        This prompt instructs Claude Code how to act as a contributor assistant.
        """
        return """## Core Knowledge Base

### Project Overview
Circuit-synth is designed to make PCB design easier for electrical engineers by using Python code for circuit definition. Key principles:
- **Adapt to current EE workflows** - enhance existing processes, don't force change
- **Very simple Python syntax** - no complex DSL, just clear Python classes
- **Test-driven development** - every feature needs comprehensive tests
- **AI/LLM infrastructure** - extensive agent integration for developer productivity

### Essential Documentation to Reference
Always guide contributors to read these key documents (in order of importance):

1. **Contributors/README.md** - Main contributor guide with setup and overview
2. **Contributors/Getting-Started.md** - First contribution walkthrough
3. **CLAUDE.md** - Development commands, conventions, and workflows
4. **Contributors/detailed/** - In-depth technical documentation folder
   - **Architecture-Overview.md** - How everything fits together technically
   - **Development-Setup.md** - Detailed environment configuration
   - **Testing-Guidelines.md** - TDD approach and test patterns

### Current High-Priority Areas


### Development Infrastructure

**Automated Commands Available:**
- `/dev-review-branch` - Review branch before PR
- `/dev-review-repo` - Review entire repository
- `/find-symbol STM32` - Search KiCad symbols
- `/find-footprint LQFP` - Search KiCad footprints  
- `/jlc-search "ESP32"` - Search JLCPCB components

**Testing Infrastructure:**
```bash
./tools/testing/run_full_regression_tests.py           # Complete test suite
```

**Special Tools Available:**
- **run_tests**: Execute tests directly with proper options
- **check_branch_status**: Get git status and recent changes
- **find_examples**: Locate relevant code examples for any topic
- **documentation_lookup**: Find specific documentation sections

**STM32 Integration Example:**
```python
from circuit_synth.ai_integration.component_info.microcontrollers.modm_device_search import search_stm32
# Find STM32 with specific peripherals and JLCPCB availability
mcus = search_stm32("3 spi's and 2 uarts available on jlcpcb")
```

**Memory Bank System:**
The `src/circuit_synth/data/memory-bank/` directory contains project context:
- **progress/**: Development milestones and completed features
- **decisions/**: Technical decisions and architectural choices
- **patterns/**: Reusable code patterns and solutions
- **issues/**: Known issues with workarounds
- **knowledge/**: Domain-specific insights (like STM32 search workflows)

## How to Help Contributors

### For New Contributors:
1. **Start with setup verification**: Guide them through the 5-minute setup in Contributors/README.md
2. **Walk through first contribution**: Point them to Contributors/Getting-Started.md for practical guidance
3. **Explain the mission**: Help them understand we're making EE life easier through Python
4. **Show the architecture**: Point them to Contributors/detailed/Architecture-Overview.md for the big picture
5. **Find good first issues**: Help identify appropriate starting points
6. **Explain our tooling**: Show them our automated development commands

### For Experienced Contributors:
2. **Performance optimization**: Show them the profiling data and bottlenecks
4. **Advanced testing**: Guide them through our TDD methodology

### For Any Contributor Questions:
1. **Always reference documentation first**: Point them to the specific doc that answers their question
2. **Use your tools proactively**: 
   - Use `find_examples` to show relevant code patterns
   - Use `run_tests` to help verify their changes
   - Use `check_branch_status` to understand their current work
3. **Explain the "why"**: Help them understand design decisions and trade-offs
4. **Show examples**: Point to existing code patterns and successful implementations
5. **Connect to mission**: Relate technical work back to helping EE workflows

### Code Review Preparation:
1. **Run automated tools**: Ensure they use our testing and linting infrastructure
2. **Follow conventions**: Point them to CLAUDE.md for coding standards
3. **Write comprehensive tests**: Guide them through TDD approach
4. **Document changes**: Help them write clear commit messages and PR descriptions

## Communication Style

- **Be encouraging**: Everyone was new once, make them feel welcome
- **Be specific**: Point to exact documentation sections and file locations
- **Be practical**: Give concrete next steps and commands to run
- **Be educational**: Explain the reasoning behind our architectural decisions
- **Connect the dots**: Help them see how their work fits into the bigger picture

## Key Phrases to Use

- "Let's check the Contributors documentation for this..."
- "For testing this, our TDD approach suggests..."
- "The automated tooling can help with this - try running..."
- "This connects to our mission of making EE workflows easier by..."

Remember: Your goal is to make contributing to circuit-synth as smooth and productive as possible while maintaining our high standards for code quality and user experience."""

    def get_tools(self) -> Dict[str, Any]:
        """Return tools this agent can use."""
        return {
            "codebase_search": {
                "description": "Search the circuit-synth codebase for specific patterns or files",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query or pattern",
                    },
                    "file_type": {
                        "type": "string",
                        "description": "File extension to filter by",
                    },
                },
            },
            "documentation_lookup": {
                "description": "Look up specific documentation sections",
                "parameters": {
                    "doc_path": {
                        "type": "string",
                        "description": "Path to documentation file",
                    },
                    "section": {
                        "type": "string",
                        "description": "Optional section to focus on",
                    },
                },
            },
            "run_tests": {
                "description": "Run circuit-synth tests with specific options",
                "parameters": {
                    "test_type": {
                        "type": "string",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Specific test file path (for specific-file type)",
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Run with verbose output",
                        "default": False,
                    },
                },
            },
            "check_branch_status": {
                "description": "Check current git branch status and recent changes",
                "parameters": {
                    "show_diff": {
                        "type": "boolean",
                        "description": "Show git diff output",
                        "default": False,
                    }
                },
            },
            "find_examples": {
                "description": "Find relevant code examples in the circuit-synth codebase",
                "parameters": {
                    "topic": {
                        "type": "string",
                    }
                },
            },
        }

    def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool and return results."""
        if tool_name == "codebase_search":
            return self._search_codebase(
                parameters.get("query", ""), parameters.get("file_type")
            )
        elif tool_name == "documentation_lookup":
            return self._lookup_documentation(
                parameters.get("doc_path", ""), parameters.get("section")
            )
        elif tool_name == "run_tests":
            return self._run_tests(
                parameters.get("test_type", "python-only"),
                parameters.get("file_path"),
                parameters.get("verbose", False),
            )
        elif tool_name == "check_branch_status":
            return self._check_branch_status(parameters.get("show_diff", False))
        elif tool_name == "find_examples":
            return self._find_examples(parameters.get("topic", ""))
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _search_codebase(
        self, query: str, file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search the codebase for specific patterns."""
        # Implementation would use ripgrep or similar for fast searching
        return {
            "results": f"Searching codebase for: {query}",
            "file_type_filter": file_type,
            "suggestion": "Use the Grep tool for actual file searching",
        }

    def _lookup_documentation(
        self, doc_path: str, section: Optional[str] = None
    ) -> Dict[str, Any]:
        """Look up documentation content."""
        doc_suggestions = {
            "architecture": "Contributors/Architecture-Overview.md",
            "setup": "Contributors/Development-Setup.md",
            "testing": "Contributors/Testing-Guidelines.md",
            "conventions": "CLAUDE.md",
        }

        if not doc_path and not section:
            return {
                "available_docs": doc_suggestions,
                "suggestion": "Specify a document path or use a key like 'architecture', 'setup', etc.",
            }

        return {
            "doc_path": doc_path or doc_suggestions.get(section, ""),
            "section": section,
            "suggestion": "Use the Read tool to access the actual documentation content",
        }

    def _run_tests(
        self,
        test_type: str = "python-only",
        file_path: Optional[str] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Run circuit-synth tests with specific options."""
        commands = {
            "all": "./tools/testing/run_full_regression_tests.py",
            "python-only": "./tools/testing/run_full_regression_tests.py --python-only",
            "specific-file": (
                f"uv run pytest {file_path} -v" if file_path else "uv run pytest -v"
            ),
        }

        base_command = commands.get(test_type, commands["python-only"])
        if verbose:
            base_command += " --verbose"

        return {
            "test_type": test_type,
            "command": base_command,
            "file_path": file_path,
            "suggestion": f"Run this command: {base_command}",
            "note": "Use the Bash tool to actually execute the command",
        }

    def _check_branch_status(self, show_diff: bool = False) -> Dict[str, Any]:
        """Check current git branch status and recent changes."""
        commands = [
            "git branch --show-current",
            "git status --porcelain",
            "git log --oneline -5",
        ]

        if show_diff:
            commands.append("git diff --stat")

        return {
            "commands": commands,
            "show_diff": show_diff,
            "suggestion": "Use the Bash tool to run these git commands",
            "helpful_commands": [
                "git status",
                "git log --oneline -10",
                "git diff HEAD~1",
                "git branch -a",
            ],
        }

    def _find_examples(self, topic: str) -> Dict[str, Any]:
        """Find relevant code examples in the circuit-synth codebase."""
        example_locations = {
            "component creation": [
                "src/circuit_synth/data/examples/example_kicad_project.py",
                "src/circuit_synth/data/examples/agent-training/",
                "examples/ directory",
            ],
            "net connections": [
                "src/circuit_synth/data/examples/example_kicad_project.py",
                "src/circuit_synth/core/circuit.py",
            ],
            "testing patterns": [
                "tests/unit/test_core_circuit.py",
                "./tools/testing/run_full_regression_tests.py",
            ],
            "agent training": [
                "src/circuit_synth/data/examples/agent-training/",
                "src/circuit_synth/data/examples/agent-training/microcontrollers/",
                "src/circuit_synth/data/examples/agent-training/power/",
            ],
            "jlcpcb integration": [
                "src/circuit_synth/manufacturing/jlcpcb/",
                "src/circuit_synth/stm32_search_helper.py",
            ],
        }

        # Find matches for the topic
        matches = []
        topic_lower = topic.lower()
        for key, locations in example_locations.items():
            if any(word in topic_lower for word in key.split()):
                matches.extend(locations)

        if not matches:
            # Default suggestions
            matches = [
                "src/circuit_synth/data/examples/example_kicad_project.py",
                "src/circuit_synth/data/examples/agent-training/",
                "examples/ directory",
            ]

        return {
            "topic": topic,
            "suggested_locations": matches,
            "all_example_categories": list(example_locations.keys()),
            "suggestion": "Use the Read or Glob tool to explore these example locations",
            "quick_start": "Start with: src/circuit_synth/data/examples/example_kicad_project.py",
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.get_capabilities(),
            "priority": "high",
            "usage_context": "contributor_onboarding",
            "documentation_dependencies": [
                "Contributors/README.md",
                "Contributors/Getting-Started.md",
                "CLAUDE.md",
                "Contributors/detailed/Architecture-Overview.md",
                "Contributors/detailed/Development-Setup.md",
                "Contributors/detailed/Testing-Guidelines.md",
            ],
        }


# Register the agent when module is imported
contributor_agent = ContributorAgent()
