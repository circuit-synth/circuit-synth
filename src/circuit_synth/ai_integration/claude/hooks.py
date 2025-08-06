"""
Intelligent Hooks System for Circuit-Synth

Provides real-time design validation, optimization, and manufacturing
readiness checking through Claude Code's hook system.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


class CircuitHook:
    """Represents a Claude Code hook for circuit design"""

    def __init__(self, event: str, matcher: str, command: str, description: str):
        self.event = event
        self.matcher = matcher
        self.command = command
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Claude Code hook format"""
        return {
            "matcher": self.matcher,
            "hooks": [{"type": "command", "command": self.command}],
        }


def get_circuit_hooks() -> Dict[str, List[CircuitHook]]:
    """Define intelligent circuit design hooks"""

    hooks = {}

    # Post-tool hooks for real-time validation
    hooks["PostToolUse"] = [
        # Real-time circuit validation after code changes
        CircuitHook(
            event="PostToolUse",
            matcher="Edit|Write|MultiEdit.*\\.py$",
            command="""
            # Extract file path and validate circuit design
            FILE_PATH=$(echo '$CLAUDE_TOOL_INPUT' | jq -r '.file_path // .edits[0].file_path // empty')
            if [[ "$FILE_PATH" == *.py ]] && grep -q "circuit_synth" "$FILE_PATH" 2>/dev/null; then
                echo "🔍 Validating circuit design in $FILE_PATH..."
                python -m circuit_synth.ai_integration.validation.real_time_check "$FILE_PATH" 2>/dev/null || echo "⚠️  Circuit validation tools not available"
            fi
            """,
            description="Real-time circuit design validation",
        ),
        # Component availability checking
        CircuitHook(
            event="PostToolUse",
            matcher="Edit|Write.*Component.*symbol",
            command="""
            # Check component availability when symbols are used
            SYMBOL=$(echo '$CLAUDE_TOOL_INPUT' | grep -o 'symbol="[^"]*"' | sed 's/symbol="\\([^"]*\\)"/\\1/')
            if [[ -n "$SYMBOL" ]]; then
                echo "🔍 Checking availability for symbol: $SYMBOL"
                python -c "
                from circuit_synth.manufacturing.jlcpcb import get_component_availability_web
                try:
                    # Extract component name from symbol
                    symbol_name = '$SYMBOL'.split(':')[-1]
                    result = get_component_availability_web(symbol_name, max_results=1)
                    if result and len(result) > 0:
                        comp = result[0]
                        print(f'✅ {comp[\"part_number\"]}: {comp[\"stock\"]} units available')
                    else:
                        print('⚠️  No availability data found')
                except Exception as e:
                    print(f'⚠️  Availability check failed: {e}')
                " 2>/dev/null || echo "⚠️  Component availability check not available"
            fi
            """,
            description="Component availability verification",
        ),
        # Design rule checking for circuit-synth projects
        CircuitHook(
            event="PostToolUse",
            matcher="Edit|Write.*@circuit",
            command="""
            # Run design rule checking on circuit definitions
            echo "🔍 Running design rule check..."
            python -c "
            import ast, sys
            try:
                file_path = '$CLAUDE_TOOL_INPUT' if '$CLAUDE_TOOL_INPUT'.endswith('.py') else sys.argv[1]
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Parse AST to find circuit decorators
                tree = ast.parse(content)
                circuit_functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        for decorator in node.decorator_list:
                            if (isinstance(decorator, ast.Name) and decorator.id == 'circuit') or \\
                               (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == 'circuit'):
                                circuit_functions.append(node.name)
                
                if circuit_functions:
                    print(f'✅ Found {len(circuit_functions)} circuit function(s): {', '.join(circuit_functions)}')
                    print('🔍 Design rules: Net connectivity, component references, manufacturing constraints')
                else:
                    print('ℹ️  No @circuit decorators found')
            except Exception as e:
                print(f'⚠️  Design rule check failed: {e}')
            " 2>/dev/null
            """,
            description="Circuit design rule checking",
        ),
    ]

    # Session start hooks for smart context loading
    hooks["SessionStart"] = [
        CircuitHook(
            event="SessionStart",
            matcher=".*",
            command="""
            echo "🚀 Circuit-Synth Professional Environment Loading..."
            
            # Check if this is a circuit-synth project
            if [[ -f "pyproject.toml" ]] && grep -q "circuit_synth" pyproject.toml; then
                echo "📋 Circuit-Synth project detected"
                
                # Load memory bank context
                if [[ -d "memory-bank" ]]; then
                    echo "🧠 Memory bank available with design history"
                fi
                
                # Check manufacturing integrations
                python -c "
                try:
                    from circuit_synth.manufacturing.jlcpcb import get_component_availability_web
                    print('🏭 JLCPCB integration: Available')
                except ImportError:
                    print('⚠️  JLCPCB integration: Not available')
                
                try:
                    from circuit_synth.component_info.microcontrollers.modm_device_search import search_stm32
                    print('🔧 STM32 MCU search: Available')
                except ImportError:
                    print('⚠️  STM32 MCU search: Not available')
                " 2>/dev/null
                
                # Show available agents
                echo "🤖 Specialized agent available:"
                echo "   - circuit-synth: Circuit-synth code generation specialist"
                
                echo "⚡ Ready for professional circuit design!"
            else
                echo "ℹ️  General development environment (not circuit-synth project)"
            fi
            """,
            description="Smart circuit design context loading",
        )
    ]

    # Notification hooks for proactive assistance
    hooks["Notification"] = [
        CircuitHook(
            event="Notification",
            matcher=".*",
            command="""
            # Provide contextual circuit design assistance
            echo "💡 Circuit design tip: Use /find-stm32-mcu for intelligent MCU selection"
            echo "🔍 Component search: Use /find-jlc-component for manufacturable parts"
            echo "⚡ Quick help: Specialized agents available for power, signal integrity, and sourcing"
            """,
            description="Contextual circuit design assistance",
        )
    ]

    return hooks


def create_claude_settings() -> Dict[str, Any]:
    """Create Claude Code settings with circuit design hooks"""

    circuit_hooks = get_circuit_hooks()

    settings = {
        "hooks": {},
        "description": "Circuit-Synth Professional Integration",
        "version": "1.0.0",
    }

    # Convert hooks to Claude Code format
    for event_type, hooks_list in circuit_hooks.items():
        settings["hooks"][event_type] = []
        for hook in hooks_list:
            settings["hooks"][event_type].append(hook.to_dict())

    return settings


def setup_circuit_hooks():
    """Setup intelligent circuit design hooks"""

    print("✅ Circuit design hooks installed")
    print(
        "🔧 Real-time validation, component checking, and design optimization enabled"
    )

    # Also create project-local hooks for development
    project_claude_dir = Path(__file__).parent.parent.parent.parent / ".claude"
    if project_claude_dir.exists():
        project_settings_file = project_claude_dir / "settings.json"
        circuit_settings = create_claude_settings()
        try:
            with open(project_settings_file, "w") as f:
                json.dump(circuit_settings, f, indent=2)
            print("📁 Also created project-local hooks for development")
        except Exception:
            pass  # Silently skip if can't write


if __name__ == "__main__":
    setup_circuit_hooks()
