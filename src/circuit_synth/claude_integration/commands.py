"""
Context-Aware Slash Commands for Circuit-Synth

Provides intelligent slash commands that understand circuit design context
and provide rapid development capabilities.
"""

import os
from pathlib import Path
from typing import Dict, List


class CircuitCommand:
    """Represents a context-aware circuit design slash command"""

    def __init__(
        self,
        name: str,
        description: str,
        content: str,
        allowed_tools: List[str] = None,
        argument_hint: str = None,
    ):
        self.name = name
        self.description = description
        self.content = content
        self.allowed_tools = allowed_tools or ["*"]
        self.argument_hint = argument_hint

    def to_markdown(self) -> str:
        """Convert to Claude Code slash command format"""
        frontmatter = f"""---
allowed-tools: {self.allowed_tools if isinstance(self.allowed_tools, str) else str(self.allowed_tools)}
description: {self.description}"""

        if self.argument_hint:
            frontmatter += f"\\nargument-hint: {self.argument_hint}"

        frontmatter += "\\n---\\n\\n"

        return frontmatter + self.content


def get_circuit_commands() -> Dict[str, CircuitCommand]:
    """Define intelligent circuit design slash commands"""

    commands = {}

    # Circuit Analysis Commands
    commands["analyze-power"] = CircuitCommand(
        name="analyze-power",
        description="Analyze power requirements and suggest power supply design",
        argument_hint="[optional: target voltage/current requirements]",
        content="""Analyze the power requirements for the current circuit design and suggest optimal power supply solutions.

🔍 **Power Analysis for**: $ARGUMENTS

**Analysis Process:**
1. **Scan Current Design**: Analyze existing circuit-synth code for power consumption patterns
2. **Component Power Assessment**: Evaluate power requirements of all components
3. **Rail Analysis**: Identify required voltage levels and current demands
4. **Efficiency Optimization**: Suggest optimal regulator topologies
5. **Manufacturing Integration**: Verify component availability through JLC integration

**Use the power-expert agent** to provide detailed power supply recommendations with:
- Complete circuit-synth code for power management
- Component selection with JLC availability verification
- Thermal analysis and protection circuit design
- BOM cost optimization and alternative suggestions

**Output Format:**
- Power budget analysis with safety margins
- Recommended power supply topology (linear/switching)
- Complete circuit-synth implementation with proper decoupling
- Manufacturing-ready component list with availability status""",
    )

    commands["optimize-routing"] = CircuitCommand(
        name="optimize-routing",
        description="Analyze signal integrity and suggest optimal routing strategies",
        content="""Analyze the current circuit design for signal integrity and provide routing optimization recommendations.

🚀 **Signal Integrity Analysis**

**Analysis Scope:**
1. **Critical Signal Identification**: Find high-speed, clock, and sensitive analog signals
2. **Layer Stack Recommendations**: Suggest optimal PCB stackup for signal integrity
3. **Impedance Control**: Calculate trace impedance requirements
4. **EMI/EMC Considerations**: Identify potential interference sources
5. **Routing Constraints**: Generate circuit-synth placement constraints

**Use the signal-integrity agent** to provide expert recommendations including:
- Critical signal path analysis and routing guidelines
- PCB stackup recommendations with cost considerations
- Component placement optimization for signal integrity
- Design rule constraints integrated into circuit-synth code

**Deliverables:**
- Signal integrity analysis report
- Routing guidelines and constraints
- Updated circuit-synth code with placement requirements
- Critical signal documentation and test point recommendations""",
    )

    commands["check-manufacturing"] = CircuitCommand(
        name="check-manufacturing",
        description="Validate design for manufacturing readiness and DFM compliance",
        content="""Comprehensive manufacturing readiness assessment for the current circuit design.

🏭 **Manufacturing Validation**

**Assessment Areas:**
1. **Component Availability**: Real-time JLC stock verification for all components
2. **Assembly Capability**: Validate against JLC assembly process capabilities
3. **Design for Manufacturing**: Check DFM rules and constraints
4. **Cost Optimization**: Analyze BOM costs across quantity breaks
5. **Lead Time Analysis**: Assess supply chain risks and delivery timelines

**Use the component-guru agent** to provide detailed manufacturing analysis:
- Complete component availability report with alternatives
- DFM compliance checking and recommendations
- Cost optimization suggestions with quantity break analysis
- Supply chain risk assessment and mitigation strategies

**Manufacturing Report Includes:**
- ✅/❌ Manufacturing readiness status for each component
- Alternative component suggestions with equivalent specs
- Cost analysis across different quantity tiers
- Lead time estimates and supply chain risk factors
- PCBA assembly feasibility and any special requirements""",
    )

    commands["estimate-cost"] = CircuitCommand(
        name="estimate-cost",
        description="Real-time BOM cost analysis with quantity breaks and alternatives",
        argument_hint="[quantity: e.g., 100, 1000, 10000]",
        content="""Generate comprehensive cost analysis for the current circuit design.

💰 **BOM Cost Analysis** for quantity: $ARGUMENTS

**Cost Analysis Process:**
1. **Component Extraction**: Parse circuit-synth code to extract all components
2. **Real-time Pricing**: Query JLC pricing for current availability
3. **Quantity Break Analysis**: Calculate costs across different volumes
4. **Alternative Assessment**: Find lower-cost equivalent components
5. **Total Cost Modeling**: Include PCB, assembly, and testing costs

**Use the component-guru agent** to provide detailed cost breakdown:
- Per-component cost analysis with quantity breaks
- Alternative component suggestions for cost optimization
- Total BOM cost including PCB and assembly
- Cost sensitivity analysis and optimization opportunities

**Cost Report Format:**
```
Component          | Qty | Cost@100 | Cost@1K | Cost@10K | Availability
-------------------|-----|----------|---------|----------|-------------
STM32G431CBT6     | 1   | $2.50    | $2.25   | $2.10    | ✅ 83K units
AMS1117-3.3       | 1   | $0.15    | $0.12   | $0.10    | ✅ 156K units
...

Total BOM Cost: $X.XX @ 100pcs | $X.XX @ 1Kpcs | $X.XX @ 10Kpcs
PCB Cost Est: $X.XX | Assembly: $X.XX | Total: $X.XX per unit
```""",
    )

    commands["generate-test-plan"] = CircuitCommand(
        name="generate-test-plan",
        description="Create comprehensive test procedures and fixture requirements",
        content="""Generate a complete test plan and procedures for the current circuit design.

🔬 **Test Plan Generation**

**Test Strategy Development:**
1. **Functional Testing**: Core circuit functionality verification
2. **Parametric Testing**: Component specifications and performance limits
3. **Manufacturing Testing**: In-circuit test (ICT) and boundary scan
4. **Environmental Testing**: Temperature, humidity, and stress testing
5. **Compliance Testing**: Regulatory and safety standard verification

**Use the circuit-architect agent** to coordinate test plan development:
- Analyze circuit functions and identify critical test points
- Generate test procedures for each circuit subsystem
- Recommend test equipment and fixture requirements
- Create automated test scripts where applicable

**Test Plan Deliverables:**
- **Test Point Placement**: Optimal locations for manufacturing test access
- **Functional Test Procedures**: Step-by-step verification protocols
- **Automated Test Scripts**: Python scripts for parameter verification
- **Fixture Requirements**: Mechanical and electrical test fixture specs
- **Pass/Fail Criteria**: Quantitative specifications for each test
- **Compliance Matrix**: Regulatory requirements and verification methods

**Integration with Circuit Design:**
- Test points added to circuit-synth code with proper net access
- Documentation of critical signals and measurement requirements
- Manufacturing-friendly design modifications for testability""",
    )

    commands["compliance-check"] = CircuitCommand(
        name="compliance-check",
        description="Validate design against safety and regulatory standards",
        argument_hint="[region: CE, FCC, UL, etc.]",
        content="""Comprehensive regulatory compliance assessment for target markets.

📋 **Compliance Validation** for region: $ARGUMENTS

**Regulatory Assessment:**
1. **Safety Standards**: UL, IEC, EN safety requirements analysis
2. **EMC Compliance**: Electromagnetic compatibility for target regions
3. **Environmental**: RoHS, REACH, conflict minerals compliance
4. **Wireless**: RF emissions and SAR requirements if applicable
5. **Industry Specific**: Medical, automotive, industrial standards

**Compliance Analysis Process:**
- Review circuit design against applicable standards
- Identify potential compliance risks and mitigation strategies
- Suggest design modifications for regulatory compliance
- Provide documentation requirements and test procedures

**Compliance Report Includes:**
- ✅/⚠️/❌ Compliance status for each applicable standard
- Required design modifications for compliance
- Test procedures and certification requirements
- Documentation and labeling requirements
- Estimated compliance testing costs and timelines

**Design Modifications:**
- Updated circuit-synth code with compliance constraints
- Component selection changes for regulatory compliance
- PCB layout requirements for EMC compliance
- Additional protection circuits if required""",
    )

    # Project Management Commands
    commands["clone-circuit"] = CircuitCommand(
        name="clone-circuit",
        description="Clone successful circuit patterns into new designs",
        argument_hint="[circuit_name or pattern_type]",
        content="""Clone proven circuit patterns from the memory-bank or existing designs.

🔄 **Circuit Pattern Cloning**: $ARGUMENTS

**Pattern Library Access:**
1. **Memory Bank Patterns**: Access documented successful designs
2. **Standard Circuit Blocks**: Power supplies, communication interfaces, etc.
3. **Application Specific**: Motor control, sensor interfaces, communication
4. **Custom Patterns**: User-defined reusable circuit blocks

**Cloning Process:**
- Search memory-bank for matching circuit patterns
- Extract and adapt circuit-synth code for current design
- Update component references and net names for integration
- Verify component availability and suggest alternatives if needed

**Available Pattern Categories:**
- **Power Management**: Linear/switching regulators, battery charging
- **Microcontroller Cores**: STM32, ESP32, Arduino-compatible designs
- **Communication**: UART, SPI, I2C, USB, Ethernet interfaces
- **Sensor Interfaces**: ADC, DAC, amplifiers, filters
- **Motor Control**: BLDC, stepper, servo motor drive circuits
- **Protection**: ESD, overvoltage, overcurrent protection

**Output:**
- Adapted circuit-synth code ready for integration
- Component list with current availability status
- Integration notes and connection requirements
- Performance specifications and design constraints""",
    )

    commands["benchmark-design"] = CircuitCommand(
        name="benchmark-design",
        description="Compare current design against industry best practices",
        content="""Comprehensive benchmarking of the current circuit design against industry standards.

📊 **Design Benchmarking Analysis**

**Benchmarking Categories:**
1. **Performance Metrics**: Speed, power consumption, accuracy
2. **Design Quality**: Component selection, circuit topology
3. **Manufacturing Excellence**: DFM compliance, cost optimization
4. **Reliability**: Derating, protection circuits, environmental robustness
5. **Innovation**: Use of modern components and design techniques

**Use the circuit-architect agent** to provide expert benchmarking:
- Compare design choices against industry best practices
- Identify opportunities for performance improvement
- Suggest modern alternatives to legacy approaches
- Provide quantitative metrics where possible

**Benchmarking Report:**
- **Performance Score**: Quantitative assessment vs industry standards
- **Design Quality Grade**: A-F rating with specific improvement areas
- **Cost Competitiveness**: Comparison with similar commercial designs
- **Manufacturing Readiness**: Assessment of production scalability
- **Innovation Index**: Use of modern components and techniques

**Improvement Recommendations:**
- Specific design modifications for better performance
- Component upgrades with cost/benefit analysis
- Manufacturing optimization opportunities
- Reliability enhancements and protection improvements""",
    )

    commands["suggest-improvements"] = CircuitCommand(
        name="suggest-improvements",
        description="AI-powered design optimization suggestions",
        content="""Generate intelligent design improvement suggestions using AI analysis.

🤖 **AI-Powered Design Optimization**

**Optimization Analysis:**
1. **Performance Enhancement**: Identify bottlenecks and improvement opportunities
2. **Cost Reduction**: Find lower-cost alternatives without compromising performance
3. **Reliability Improvement**: Suggest additional protection and robustness measures
4. **Manufacturing Optimization**: Improve DFM and reduce assembly complexity
5. **Future-Proofing**: Recommend design changes for scalability and upgrades

**AI Analysis Process:**
- Use circuit-architect agent for high-level optimization strategy
- Employ specialized agents (power-expert, signal-integrity, component-guru)
- Cross-reference with memory-bank patterns and best practices
- Generate ranked improvement suggestions with impact analysis

**Improvement Categories:**
- **Quick Wins**: Low-effort, high-impact improvements
- **Performance Upgrades**: Significant performance gains with moderate effort
- **Cost Optimizations**: Reduce BOM cost while maintaining functionality
- **Reliability Enhancements**: Improve robustness and fault tolerance
- **Future Enhancements**: Prepare for next-generation requirements

**Suggestion Format:**
For each improvement:
- **Impact**: Quantitative benefit (cost savings, performance gain, etc.)
- **Effort**: Implementation complexity and required changes
- **Risk**: Assessment of potential negative impacts
- **Implementation**: Specific circuit-synth code changes required
- **Verification**: How to validate the improvement effectiveness""",
    )

    return commands


def register_circuit_commands():
    """Register intelligent circuit design slash commands"""

    # Get user's Claude config directory
    claude_dir = Path.home() / ".claude" / "commands"
    claude_dir.mkdir(parents=True, exist_ok=True)

    commands = get_circuit_commands()

    for cmd_name, command in commands.items():
        cmd_file = claude_dir / f"{cmd_name}.md"

        # Write command definition
        with open(cmd_file, "w") as f:
            f.write(command.to_markdown())

        print(f"✅ Registered command: /{cmd_name}")

    print(f"⚡ Registered {len(commands)} intelligent circuit commands")

    # Also create project-local commands for development
    project_commands_dir = (
        Path(__file__).parent.parent.parent.parent / ".claude" / "commands"
    )
    if project_commands_dir.exists():
        for cmd_name, command in commands.items():
            cmd_file = project_commands_dir / f"{cmd_name}.md"
            with open(cmd_file, "w") as f:
                f.write(command.to_markdown())
        print(f"📁 Also created project-local commands for development")


if __name__ == "__main__":
    register_circuit_commands()
