#!/usr/bin/env python3
"""
Claude Code Integration Setup Script

Sets up Claude Code agents, commands, and hooks for professional
circuit design workflow after pip installation.
"""

import sys
from pathlib import Path


def main():
    """Setup Claude Code integration for circuit-synth"""

    print("🚀 Setting up Claude Code integration for circuit-synth...")

    try:
        from circuit_synth import setup_claude_integration

        setup_claude_integration()

        print("\\n🤖 Available specialized agents:")
        print("   - circuit-architect: Master circuit design coordinator")
        print("   - power-expert: Power supply and regulation specialist")
        print("   - signal-integrity: High-speed PCB design expert")
        print("   - component-guru: Manufacturing and sourcing specialist")

        print("\\n⚡ Available intelligent commands:")
        print("   - /analyze-power: Power requirements analysis")
        print("   - /optimize-routing: Signal integrity optimization")
        print("   - /check-manufacturing: Manufacturing readiness validation")
        print("   - /estimate-cost: Real-time BOM cost analysis")
        print("   - /generate-test-plan: Comprehensive test procedures")
        print("   - /compliance-check: Regulatory compliance validation")
        print("   - /clone-circuit: Clone proven circuit patterns")
        print("   - /benchmark-design: Compare against industry standards")
        print("   - /suggest-improvements: AI-powered optimization")

        print("\\n🔧 Real-time validation enabled:")
        print("   - Component availability checking")
        print("   - Circuit design rule validation")
        print("   - STM32 pin assignment verification")
        print("   - Manufacturing readiness assessment")

        print("\\n🎯 Ready for professional circuit design!")
        print("\\nTry: /analyze-power or ask a circuit-architect for help")

    except ImportError as e:
        print(f"⚠️  Claude Code integration not fully available: {e}")
        print("\\n💡 For complete AI-powered circuit design experience:")
        print("   pip install circuit-synth[claude]")
        print("\\n✅ Basic circuit-synth functionality is still available!")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\\nPlease report this issue at:")
        print("https://github.com/circuit-synth/circuit-synth/issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
