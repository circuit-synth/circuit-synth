#!/bin/bash
# Circuit-synth session hook for Claude Code

echo "🚀 Circuit-Synth Professional Environment Loading..."

# Check if this is a circuit-synth project
if [[ -f "pyproject.toml" ]] && grep -q "circuit_synth" pyproject.toml; then
    echo "📋 Circuit-Synth project detected"
elif [[ -d "memory-bank" ]] && [[ -d "circuit-synth" ]]; then
    echo "📋 Circuit-Synth PCB project detected"
fi

# Check for memory-bank system
if [[ -d "memory-bank" ]]; then
    echo "🧠 Memory bank available with design history"
fi

# Show available agents
echo "🤖 Specialized agents available:"
echo "   - contributor: Development and contribution assistance (START HERE!)"
echo "   - circuit-architect: Master circuit design coordinator"
echo "   - circuit-synth: Circuit-synth code generation specialist"
echo "   - simulation-expert: SPICE simulation and validation"
echo "   - component-guru: Manufacturing and sourcing specialist"

echo "⚡ Ready for professional circuit design!"
echo ""
echo "💡 Quick start: Ask the 'contributor' agent for help with any task!"
echo "   Example: 'Help me design an ESP32 circuit with IMU and USB-C'"