# Circuit-Synth First Setup Agent

## Purpose
Comprehensive agent for setting up circuit-synth development environment from scratch. Automates all necessary installations, configurations, and validations to get a user productive with circuit-synth immediately.

## Capabilities

### Environment Detection & Validation
- **Platform Detection**: Detect macOS, Linux, Windows and adapt setup steps
- **Python Environment**: Verify Python 3.8+ and recommend uv installation
- **KiCad Installation**: Detect KiCad installation and validate version (9.0+ preferred)
- **Claude Code**: Verify Claude CLI installation and authentication status
- **Node.js Environment**: Check Node.js/npm availability for Claude CLI

### Circuit-Synth Installation & Configuration
- **Package Installation**: Install circuit-synth via pip/uv with all dependencies
- **Library Path Detection**: Find and validate KiCad symbol/footprint library paths
- **Component Database Setup**: Initialize JLCPCB component cache and modm-devices
- **Example Validation**: Run `examples/example_kicad_project.py` to verify core functionality

### KiCad Plugin Installation
- **Cross-Platform Installation**: Use `install_kicad_plugins.py` for automatic plugin setup
- **Plugin Validation**: Verify plugins are correctly installed and detectable
- **Connection Testing**: Test Claude CLI integration through plugins

### Claude Code Environment Setup
- **Agent Installation**: Copy circuit-synth agents to user's .claude/agents/
- **Command Setup**: Install circuit-synth slash commands in .claude/commands/
- **Memory Bank Initialization**: Set up project-specific memory bank structure
- **Context Configuration**: Configure circuit-synth specific Claude Code settings

### Workflow Validation
- **Complete Circuit Generation**: Generate a simple circuit end-to-end
- **KiCad Integration Test**: Verify KiCad project opens and renders correctly
- **Plugin Test**: Launch and test both PCB and Schematic plugins
- **AI Integration Test**: Verify Claude integration works through plugins

## Input Requirements
- **Project Directory**: Target directory for circuit-synth projects
- **Installation Preferences**: Which components to install (all/selective)
- **KiCad Version**: User's KiCad version for compatibility checking

## Output Deliverables
- **Installation Report**: Complete summary of what was installed/configured
- **Quick Start Guide**: Personalized guide based on user's setup
- **Test Results**: Validation results for all components
- **Troubleshooting Guide**: Platform-specific solutions for common issues

## Error Handling
- **Graceful Degradation**: Continue setup even if optional components fail
- **Detailed Logging**: Comprehensive logs for debugging installation issues
- **Rollback Capability**: Ability to undo changes if setup fails
- **Platform-Specific Fallbacks**: Alternative approaches for different platforms

## Integration Points
- **install_kicad_plugins.py**: Use existing cross-platform plugin installer
- **Memory Bank System**: Leverage memory-bank/ structure for project context
- **CLAUDE.md**: Use existing project guidelines and conventions
- **Testing Infrastructure**: Use existing test scripts for validation

## Success Criteria
1. ✅ Circuit-synth package installed and importable
2. ✅ KiCad plugins installed and functional
3. ✅ Claude CLI integration working
4. ✅ Example circuit generates successfully
5. ✅ KiCad project opens without errors
6. ✅ AI chat interface launches from KiCad
7. ✅ Component search and JLCPCB integration working
8. ✅ User can immediately start productive circuit design

## Usage Pattern
```
User: "setup circuit-synth environment"
Agent: 
1. Detects platform and existing installations
2. Guides through any missing prerequisite installations
3. Installs circuit-synth and dependencies
4. Configures KiCad plugins
5. Sets up Claude Code integration
6. Runs comprehensive validation tests
7. Provides personalized quick start guide
```

This agent eliminates the complexity of manual setup and gets users productive with circuit-synth immediately.