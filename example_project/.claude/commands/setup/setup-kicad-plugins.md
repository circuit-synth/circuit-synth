# Setup KiCad Plugins

You are tasked with helping the user set up KiCad plugins for circuit-synth AI integration.

## Available Actions

1. **Check Installation Status**
   - Verify if KiCad is installed on the system
   - Check if circuit-synth plugins are already installed
   - Show current plugin directory locations

2. **Automatic Installation**
   - Run the built-in plugin installer: `uv run cs-setup-kicad-plugins`
   - This will automatically copy plugin files to the correct KiCad directory
   - Works on macOS, Windows, and Linux

3. **Manual Installation Guidance**
   - Provide platform-specific manual installation instructions
   - Show exact file paths and commands needed
   - Help troubleshoot installation issues

4. **Plugin Usage Instructions**
   - Explain how to use the plugins once installed
   - Show the menu locations in KiCad (PCB Editor and Schematic Editor)
   - Provide examples of plugin capabilities

## Implementation Steps

When the user asks about KiCad plugin setup:

1. **First, run the automatic installer:**
   ```bash
   uv run cs-setup-kicad-plugins
   ```

2. **If automatic installation fails, provide manual instructions:**
   - Check the output of `uv run cs-setup-kicad-plugins --manual`
   - Guide the user through platform-specific manual installation

3. **Verify installation:**
   - Ask user to restart KiCad
   - Help them locate the plugins in KiCad menus
   - Test basic plugin functionality

## Key Plugin Features

The circuit-synth KiCad plugins provide:
- **AI-powered BOM analysis** - Intelligent component analysis and suggestions
- **Component availability checking** - Real-time JLCPCB stock verification  
- **Design optimization** - Automated component selection and cost optimization
- **Manufacturing readiness** - Assembly and sourcing recommendations

## Troubleshooting

Common issues and solutions:
- **KiCad not found**: Help user verify KiCad installation
- **Permission errors**: Guide user through admin/sudo installation
- **Plugin not appearing**: Check KiCad version compatibility and restart
- **File not found errors**: Verify circuit-synth installation and plugin source files

Always provide clear, step-by-step instructions and be ready to troubleshoot platform-specific issues.