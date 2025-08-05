"""
Test Plan Generation Slash Commands

Provides /create-test-plan and /generate-manufacturing-tests commands
for generating comprehensive test procedures for circuit designs.
"""

import os
from pathlib import Path
from typing import Optional

import click

from ..claude_integration.agent_registry import create_agent_instance


@click.command()
@click.argument("circuit_file", required=False)
@click.option(
    "--include-performance",
    is_flag=True,
    help="Include detailed performance testing procedures"
)
@click.option(
    "--include-safety",
    is_flag=True,
    help="Include safety and compliance testing"
)
@click.option(
    "--format",
    type=click.Choice(["markdown", "json", "csv", "checklist"]),
    default="markdown",
    help="Output format for the test plan"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path (default: prints to console)"
)
def create_test_plan(
    circuit_file: Optional[str],
    include_performance: bool,
    include_safety: bool,
    format: str,
    output: Optional[str]
):
    """
    Generate a comprehensive test plan for a circuit design.
    
    Examples:
    
        /create-test-plan ESP32_power_board.py
        
        /create-test-plan USB_interface.py --include-performance --include-safety
        
        /create-test-plan my_circuit.py --format json --output test_plan.json
    """
    click.echo("🧪 Test Plan Generator")
    click.echo("=" * 50)
    
    # Check if circuit file exists
    if circuit_file:
        circuit_path = Path(circuit_file)
        if not circuit_path.exists():
            click.echo(f"❌ Error: Circuit file '{circuit_file}' not found")
            click.echo("\nPlease provide a valid circuit-synth Python file.")
            return
            
        click.echo(f"📄 Analyzing circuit: {circuit_file}")
    else:
        click.echo("📋 Creating general test plan template")
        
    # Build test categories based on options
    test_categories = ["functional"]  # Always include functional
    if include_performance:
        test_categories.append("performance")
    if include_safety:
        test_categories.append("safety")
    test_categories.append("manufacturing")  # Always include manufacturing
    
    click.echo(f"📊 Test categories: {', '.join(test_categories)}")
    click.echo(f"📄 Output format: {format}")
    
    # Generate agent prompt
    prompt = f"""Generate a comprehensive test plan for {'the circuit in ' + circuit_file if circuit_file else 'a generic circuit design'}.

Include the following test categories:
{chr(10).join(f'- {cat.capitalize()} testing' for cat in test_categories)}

The test plan should include:
1. Overview and test objectives
2. Required test equipment
3. Test setup instructions
4. Detailed test procedures with steps
5. Expected results and tolerances
6. Pass/fail criteria
7. Test results recording format
8. Troubleshooting guide

Output format: {format}
"""

    if circuit_file:
        # Read the circuit file content
        with open(circuit_file, 'r') as f:
            circuit_code = f.read()
        prompt += f"\n\nCircuit code to analyze:\n```python\n{circuit_code}\n```"
    
    # Display the prompt that would be sent to the agent
    click.echo("\n📝 Agent prompt:")
    click.echo("-" * 50)
    click.echo(prompt)
    click.echo("-" * 50)
    
    # Show how to use with Claude Code
    click.echo("\n💡 To generate the test plan, use this with Claude Code:")
    click.echo(f'Task(subagent_type="test-plan-creator", description="Generate test plan", prompt="""{prompt}""")')
    
    if output:
        click.echo(f"\n📁 Results should be saved to: {output}")


@click.command()
@click.argument("circuit_file", required=False)
@click.option(
    "--ict",
    is_flag=True,
    help="Include in-circuit testing (ICT) procedures"
)
@click.option(
    "--boundary-scan",
    is_flag=True,
    help="Include boundary scan/JTAG testing"
)
@click.option(
    "--fixture",
    is_flag=True,
    help="Include test fixture specifications"
)
def generate_manufacturing_tests(
    circuit_file: Optional[str],
    ict: bool,
    boundary_scan: bool,
    fixture: bool
):
    """
    Generate manufacturing test procedures for production.
    
    Examples:
    
        /generate-manufacturing-tests power_supply.py --ict
        
        /generate-manufacturing-tests mcu_board.py --boundary-scan --fixture
    """
    click.echo("🏭 Manufacturing Test Generator")
    click.echo("=" * 50)
    
    if circuit_file and not Path(circuit_file).exists():
        click.echo(f"❌ Error: Circuit file '{circuit_file}' not found")
        return
        
    # Build test types
    test_types = []
    if ict:
        test_types.append("ICT (In-Circuit Testing)")
    if boundary_scan:
        test_types.append("Boundary Scan/JTAG")
    if fixture:
        test_types.append("Test Fixture Design")
    if not test_types:
        test_types = ["Basic Functional Testing"]
        
    click.echo(f"🔧 Test types: {', '.join(test_types)}")
    
    prompt = f"""Generate manufacturing test procedures for {'the circuit in ' + circuit_file if circuit_file else 'production testing'}.

Focus on:
{chr(10).join(f'- {test_type}' for test_type in test_types)}

Include:
1. Test point identification for probe access
2. Test sequence and timing
3. Measurement specifications
4. Go/no-go criteria
5. Fixture requirements (if applicable)
6. Test program pseudo-code
7. Typical failure modes and diagnosis

Optimize for:
- Fast test execution time
- High fault coverage
- Minimal false failures
- Easy operator use
"""

    if circuit_file:
        with open(circuit_file, 'r') as f:
            circuit_code = f.read()
        prompt += f"\n\nCircuit code:\n```python\n{circuit_code}\n```"
    
    click.echo("\n📝 Manufacturing test prompt:")
    click.echo("-" * 50)
    click.echo(prompt)
    click.echo("-" * 50)
    
    click.echo("\n💡 To generate manufacturing tests, use:")
    click.echo(f'Task(subagent_type="test-plan-creator", description="Manufacturing tests", prompt="""{prompt}""")')


# CLI command group
@click.group()
def test_plan_cli():
    """Test plan generation commands"""
    pass


test_plan_cli.add_command(create_test_plan, name="create-test-plan")
test_plan_cli.add_command(generate_manufacturing_tests, name="generate-manufacturing-tests")


if __name__ == "__main__":
    test_plan_cli()