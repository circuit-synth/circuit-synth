# Circuit-Synth AI Plugin for KiCad 9

An AI-powered circuit design assistant plugin for KiCad 9, integrated with the circuit-synth framework.

## Features

- **AI Chat Interface**: Natural language interaction for circuit design assistance
- **Circuit Analysis**: Analyze existing PCB designs and get intelligent feedback  
- **Layout Optimization**: Get suggestions for component placement and routing
- **Integration with Circuit-Synth**: Seamless integration with the circuit-synth Python framework

## Installation

The plugin has been installed to your KiCad plugins directory:
```
~/Documents/KiCad/9.0/plugins/circuit_synth_ai/
```

## Usage

1. **Start KiCad**: Open KiCad PCB Editor
2. **Open or Create a PCB**: Load an existing PCB or create a new one
3. **Launch Plugin**: Look for "Circuit-Synth AI" in the Tools menu or toolbar
4. **Chat with AI**: Use the chat interface to ask questions about your design

## Dependencies

The plugin requires:
- KiCad 9.0+  
- Python with wxPython (usually provided by KiCad)
- Circuit-Synth framework (optional, for advanced features)

## Examples

Try asking the AI assistant:
- "Analyze the component density on this board"
- "What's the trace routing efficiency?" 
- "Suggest improvements for thermal management"
- "Help me optimize this power supply layout"

## Development

This plugin is part of the Circuit-Synth project. For development and customization:

```bash
cd /path/to/circuit-synth
python kicad_plugins/install_plugin.py
```

## Support

- GitHub: https://github.com/circuit-synth/circuit-synth
- Documentation: See the circuit-synth project documentation

## License

MIT License - See the main circuit-synth project for full license details.