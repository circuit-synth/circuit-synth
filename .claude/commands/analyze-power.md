---
allowed-tools: ['*']
description: Analyze power requirements and suggest power supply design\nargument-hint: [optional: target voltage/current requirements]\n---\n\nAnalyze the power requirements for the current circuit design and suggest optimal power supply solutions.

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
- Manufacturing-ready component list with availability status