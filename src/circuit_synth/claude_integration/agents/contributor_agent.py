"""
Circuit-Synth Contributor Agent

A specialized Claude Code agent designed to help contributors understand the codebase,
follow conventions, and make meaningful contributions to circuit-synth.
"""

from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

from ..agent_registry import register_agent


@register_agent("contributor")
class ContributorAgent:
    """
    Specialized Claude Code agent for circuit-synth contributors.
    
    This agent helps new and existing contributors:
    - Understand the project architecture and codebase
    - Follow coding conventions and best practices
    - Navigate the Rust/Python integration
    - Write proper tests using TDD approach
    - Use development tools and commands effectively
    """
    
    def __init__(self):
        self.name = "contributor"
        self.description = "Circuit-synth contributor onboarding and development assistant"
        self.version = "1.0.0"
        
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "codebase_navigation",
            "architecture_explanation", 
            "coding_conventions",
            "testing_guidance",
            "rust_integration_help",
            "development_workflow",
            "code_review_preparation",
            "issue_analysis",
            "contribution_planning"
        ]
    
    def get_system_prompt(self) -> str:
        """
        Return the system prompt that defines this agent's behavior.
        
        This prompt instructs Claude Code how to act as a contributor assistant.
        """
        return """You are a specialized contributor agent for the circuit-synth project. Your role is to help developers contribute effectively to this EE design tool that combines Python simplicity with Rust performance.

## Core Knowledge Base

### Project Overview
Circuit-synth is designed to make PCB design easier for electrical engineers by using Python code for circuit definition. Key principles:
- **Adapt to current EE workflows** - enhance existing processes, don't force change
- **Very simple Python syntax** - no complex DSL, just clear Python classes
- **Test-driven development** - every feature needs comprehensive tests
- **Python + Rust hybrid** - Python for API/flexibility, Rust for performance
- **AI/LLM infrastructure** - extensive agent integration for developer productivity

### Essential Documentation to Reference
Always guide contributors to read these key documents (in order of importance):

1. **Contributors/README.md** - Main contributor guide with setup and overview
2. **Contributors/Architecture-Overview.md** - How everything fits together technically  
3. **CLAUDE.md** - Development commands, conventions, and workflows
4. **Contributors/Development-Setup.md** - Detailed environment configuration
5. **Contributors/Rust-Integration-Guide.md** - Working with our Rust modules
6. **Contributors/Testing-Guidelines.md** - TDD approach and test patterns

### Current High-Priority Areas

**Rust Integration (Perfect for High-Impact Contributions):**
- Issue #36: rust_netlist_processor module missing (HIGH PRIORITY)
- Issue #37: rust_kicad_integration not compiled (HIGH PRIORITY)  
- Issue #38: rust_core_circuit_engine missing
- Issue #39: rust_force_directed_placement missing
- Issue #40: rust component acceleration missing (97% of generation time!)
- Issue #41: rust S-expression formatting missing

### Development Infrastructure

**Automated Commands Available:**
- `/dev-review-branch` - Review branch before PR
- `/dev-review-repo` - Review entire repository
- `/find-symbol STM32` - Search KiCad symbols
- `/find-footprint LQFP` - Search KiCad footprints  
- `/jlc-search "ESP32"` - Search JLCPCB components

**Testing Infrastructure:**
```bash
./scripts/run_all_tests.sh           # Complete test suite
./scripts/run_all_tests.sh --python-only  # Skip Rust compilation
./scripts/test_rust_modules.sh       # Rust module testing
```

**STM32 Integration Example:**
```python
from circuit_synth.component_info.microcontrollers.modm_device_search import search_stm32
# Find STM32 with specific peripherals and JLCPCB availability
mcus = search_stm32("3 spi's and 2 uarts available on jlcpcb")
```

## How to Help Contributors

### For New Contributors:
1. **Start with setup verification**: Guide them through the 5-minute setup in Contributors/README.md
2. **Explain the mission**: Help them understand we're making EE life easier through Python
3. **Show the architecture**: Point them to Architecture-Overview.md for the big picture
4. **Find good first issues**: Help identify appropriate starting points
5. **Explain our tooling**: Show them our automated development commands

### For Experienced Contributors:
1. **Dive into Rust integration**: These are our highest-impact opportunities
2. **Performance optimization**: Show them the profiling data and bottlenecks
3. **Architecture decisions**: Help them understand the Python+Rust hybrid approach
4. **Advanced testing**: Guide them through our TDD methodology

### For Any Contributor Questions:
1. **Always reference documentation first**: Point them to the specific doc that answers their question
2. **Explain the "why"**: Help them understand design decisions and trade-offs
3. **Show examples**: Point to existing code patterns and successful implementations
4. **Connect to mission**: Relate technical work back to helping EE workflows

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
- "This relates to our Python+Rust hybrid architecture because..."
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
                    "query": {"type": "string", "description": "Search query or pattern"},
                    "file_type": {"type": "string", "description": "File extension to filter by"}
                }
            },
            "documentation_lookup": {
                "description": "Look up specific documentation sections",
                "parameters": {
                    "doc_path": {"type": "string", "description": "Path to documentation file"},
                    "section": {"type": "string", "description": "Optional section to focus on"}
                }
            },
            "rust_module_status": {
                "description": "Check status of Rust modules and compilation",
                "parameters": {
                    "module_name": {"type": "string", "description": "Specific Rust module to check"}
                }
            }
        }
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        if tool_name == "codebase_search":
            return self._search_codebase(parameters.get("query", ""), parameters.get("file_type"))
        elif tool_name == "documentation_lookup":
            return self._lookup_documentation(parameters.get("doc_path", ""), parameters.get("section"))
        elif tool_name == "rust_module_status":
            return self._check_rust_module_status(parameters.get("module_name"))
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def _search_codebase(self, query: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """Search the codebase for specific patterns."""
        # Implementation would use ripgrep or similar for fast searching
        return {
            "results": f"Searching codebase for: {query}",
            "file_type_filter": file_type,
            "suggestion": "Use the Grep tool for actual file searching"
        }
    
    def _lookup_documentation(self, doc_path: str, section: Optional[str] = None) -> Dict[str, Any]:
        """Look up documentation content."""
        doc_suggestions = {
            "architecture": "Contributors/Architecture-Overview.md",
            "setup": "Contributors/Development-Setup.md", 
            "testing": "Contributors/Testing-Guidelines.md",
            "rust": "Contributors/Rust-Integration-Guide.md",
            "conventions": "CLAUDE.md"
        }
        
        if not doc_path and not section:
            return {
                "available_docs": doc_suggestions,
                "suggestion": "Specify a document path or use a key like 'architecture', 'setup', etc."
            }
        
        return {
            "doc_path": doc_path or doc_suggestions.get(section, ""),
            "section": section,
            "suggestion": "Use the Read tool to access the actual documentation content"
        }
    
    def _check_rust_module_status(self, module_name: Optional[str] = None) -> Dict[str, Any]:
        """Check the status of Rust modules."""
        rust_modules = [
            "rust_core_circuit_engine",
            "rust_kicad_integration", 
            "rust_netlist_processor",
            "rust_force_directed_placement",
            "rust_symbol_cache"
        ]
        
        return {
            "available_modules": rust_modules,
            "module_requested": module_name,
            "high_priority_issues": [
                "Issue #36: rust_netlist_processor module missing",
                "Issue #37: rust_kicad_integration not compiled",
                "Issue #40: rust component acceleration (97% performance impact)"
            ],
            "suggestion": "Use 'uv run python example_project/circuit-synth/main.py' to see current fallback status"
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
                "Contributors/Architecture-Overview.md", 
                "CLAUDE.md",
                "Contributors/Development-Setup.md",
                "Contributors/Rust-Integration-Guide.md",
                "Contributors/Testing-Guidelines.md"
            ]
        }


# Register the agent when module is imported
contributor_agent = ContributorAgent()