#!/bin/bash
# Updated session hook for circuit-synth with correct agent names

echo "🚀 Circuit-Synth Professional Environment Loading..."

# Check if this is a circuit-synth project
if [[ -f "pyproject.toml" ]] && grep -q "circuit_synth" pyproject.toml; then
    echo "📋 Circuit-Synth project detected"
    
    # Load memory bank context
    if [[ -d "src/circuit_synth/data/memory-bank" ]]; then
        echo "🧠 Memory bank available with design history"
    fi
    
    # Check manufacturing integrations
    python -c "
try:
    from circuit_synth.manufacturing.jlcpcb import find_component
    print('🏭 JLCPCB integration: Available')
except ImportError:
    print('⚠️  JLCPCB integration: Not available')

try:
    from circuit_synth.component_info.microcontrollers.modm_device_search import search_stm32
    print('🔧 STM32 integration: Available')
except ImportError:
    print('⚠️  STM32 integration: Not available')
" 2>/dev/null
    
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
else
    echo "ℹ️  General development environment (not circuit-synth project)"
fi