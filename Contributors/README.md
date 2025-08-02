# Circuit-Synth Contributors Guide

**Welcome to the most contributor-friendly EE design tool ever built!** 🚀

Circuit-synth is designed from the ground up to make PCB design easier for electrical engineers while making development on the project as seamless as possible for contributors. We've built extensive AI agent integration, automated tooling, and comprehensive documentation to ensure you can make meaningful contributions quickly.

## 🤖 AI-First Development Experience

### Claude Code Integration (Recommended)

We **strongly recommend** using [Claude Code](https://claude.ai/code) for the best development experience. Claude Code has specialized agents that understand circuit-synth deeply:

```bash
# Install Claude Code (if not already installed)
# Visit: https://claude.ai/code for installation

# Our specialized agents will automatically:
# ✅ Navigate the codebase architecture
# ✅ Find relevant files and components
# ✅ Follow our coding conventions
# ✅ Generate tests using TDD approach
# ✅ Handle Rust/Python integration
# ✅ Review your code before submission
```

### GitHub MCP Server Integration

For the ultimate development workflow, use the [GitHub MCP Server](https://github.com/anthropics/mcp-servers/tree/main/src/github) with Claude Code:

```bash
# Setup GitHub MCP for seamless issue/PR management
# This enables Claude Code to:
# ✅ Create and manage GitHub issues
# ✅ Review pull requests automatically
# ✅ Check CI status and test results
# ✅ Navigate project structure and history
```

### Alternative AI Tools

While we optimize for Claude Code, other AI tools can help too:
- **ChatGPT/GPT-4**: Read our documentation and CLAUDE.md for context
- **Cursor**: Works well with our codebase structure
- **GitHub Copilot**: Good for code completion and basic assistance
- **Any LLM**: Use our extensive documentation in `Contributors/` and `CLAUDE.md`

## 🎯 Project Mission

**Make EE PCB designer life easier through Python-based circuit definition**

### Core Philosophy
- **Adapt to current EE workflows** - Don't force change, enhance existing processes
- **Everything should be simple** - Very, very simple Python syntax
- **Test-driven development is key** - Every feature needs comprehensive tests
- **Infrastructure for AI/LLM integration** - Make this library easy for AI agents to use

### Technical Evolution
- **Started as pure Python** - Simple, readable, maintainable
- **Converting to Rust for performance** - All logic where performance matters
- **Goal: Full bi-directional import/export** - Seamless KiCad ↔ circuit-synth workflow
- **Canonical matching for updates** - Handle user modifications intelligently

## 🚀 Getting Started (5-Minute Setup)

### 1. Environment Setup
```bash
# Clone and setup
git clone https://github.com/circuit-synth/circuit-synth.git
cd circuit-synth
uv sync

# Verify installation
uv run python example_project/circuit-synth/main.py
```

### 2. AI Agent Setup (Optional but Recommended)
```bash
# Register our specialized Claude Code agents
uv run register-agents

# Now Claude Code has access to:
# - Circuit design agents
# - Component search agents  
# - KiCad integration agents
# - Code review agents
```

### 3. Development Verification
```bash
# Test that everything works
./scripts/run_all_tests.sh --python-only
```

## 🏗️ Development Areas

### High-Priority: Rust Integration
We're actively converting performance-critical parts to Rust. **Perfect for contributors who want high impact!**

Current Rust integration points needing help:
- **[Issue #36](https://github.com/circuit-synth/circuit-synth/issues/36)**: Netlist processor (HIGH PRIORITY)
- **[Issue #37](https://github.com/circuit-synth/circuit-synth/issues/37)**: KiCad integration (HIGH PRIORITY)  
- **[Issue #38](https://github.com/circuit-synth/circuit-synth/issues/38)**: Core circuit engine
- **[Issue #39](https://github.com/circuit-synth/circuit-synth/issues/39)**: Force-directed placement
- **[Issue #40](https://github.com/circuit-synth/circuit-synth/issues/40)**: Component processing
- **[Issue #41](https://github.com/circuit-synth/circuit-synth/issues/41)**: S-expression formatting

### Medium-Priority: Feature Development
- **Bi-directional sync improvements** - Better KiCad ↔ Python synchronization
- **Component search enhancements** - More manufacturing integrations
- **Simulation integration** - SPICE and other simulation tools
- **Documentation and examples** - Always needed!

### Easy Entry Points
- **Examples and tutorials** - Help other EEs get started
- **Component library expansion** - Add more verified components
- **Test coverage** - Find and test edge cases
- **Documentation improvements** - Make things clearer

## 🛠️ Our Development Infrastructure

### Automated Development Commands

We've built extensive tooling to make development effortless:

```bash
# Claude Code can use these commands automatically:
/dev-review-branch    # Review your branch before PR
/dev-review-repo      # Review entire repository for issues  
/find-symbol STM32    # Search KiCad symbols
/find-footprint LQFP  # Search KiCad footprints
/jlc-search "ESP32"   # Search JLCPCB for components
```

### STM32 Integration Example

We have deep STM32 integration through modm-devices:

```python
# Claude Code agents can automatically:
from circuit_synth.component_info.microcontrollers.modm_device_search import search_stm32

# Find STM32 with specific peripherals and JLCPCB availability
mcus = search_stm32("3 spi's and 2 uarts available on jlcpcb")
```

### Comprehensive Testing Infrastructure

```bash
# Automated testing (what CI uses)
./scripts/run_all_tests.sh

# Test just your changes
./scripts/run_all_tests.sh --python-only --fail-fast

# Test Rust modules
./scripts/test_rust_modules.sh --verbose
```

## 📚 Learning Resources

### Start Here (in order):
1. **[Architecture Overview](Architecture-Overview.md)** - How everything fits together
2. **[Development Setup](Development-Setup.md)** - Detailed environment configuration  
3. **[Rust Integration Guide](Rust-Integration-Guide.md)** - Working with our Rust modules
4. **[Testing Guidelines](Testing-Guidelines.md)** - TDD approach and test patterns
5. **[Code Review Process](Code-Review-Process.md)** - How we maintain quality

### Specialized Guides:
- **[AI Agent Development](AI-Agent-Development.md)** - Building new Claude Code agents
- **[KiCad Integration](KiCad-Integration.md)** - Working with KiCad APIs
- **[Component Integration](Component-Integration.md)** - Adding new component types
- **[Manufacturing Integration](Manufacturing-Integration.md)** - JLCPCB, Digi-Key, etc.

## 🤝 Community & Support

### Getting Help
- **GitHub Discussions** - General questions and ideas
- **GitHub Issues** - Bug reports and feature requests
- **Claude Code Agents** - Built-in help and guidance
- **Code Review** - Automated feedback on pull requests

### Communication Guidelines
- **Be welcoming** - Everyone was new once
- **Share knowledge** - Help others learn
- **Ask questions** - No question is too basic
- **Collaborate** - Great ideas come from working together

## 🎉 Recognition

Contributors get recognition through:
- **GitHub Contributors page** - Automatic recognition
- **Release notes** - Major contributions highlighted
- **Documentation credits** - Attribution for significant help
- **Community showcase** - Examples of great contributions

---

**Ready to start contributing?** Pick an issue, set up your environment, and let our AI agents guide you through the process! 

**Questions?** Open a GitHub Discussion or ask Claude Code - our agents are designed to help you succeed! 🚀