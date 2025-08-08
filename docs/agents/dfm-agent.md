# DFM Agent - Design for Manufacturing Specialist

## Overview

The DFM (Design for Manufacturing) agent is a specialized AI assistant that analyzes circuit designs for manufacturability, identifies production risks, and optimizes designs for cost-effective, high-yield manufacturing.

## Capabilities

### Core Functions
- **Manufacturability Analysis**: Evaluate designs against production constraints
- **Cost Optimization**: Identify opportunities to reduce BOM and assembly costs
- **Supply Chain Assessment**: Analyze component availability and sourcing risks
- **Issue Detection**: Find and prioritize manufacturing problems
- **Alternative Recommendations**: Suggest component substitutions and design improvements

### Key Features
- Integrates with `circuit_synth.design_for_manufacturing.DFMAnalyzer`
- Supports JLCPCB, PCBWay, and generic manufacturing constraints
- Provides volume pricing analysis
- Generates comprehensive DFM reports
- Offers actionable optimization recommendations

## Usage

### Invoking the DFM Agent

```python
# Using Claude Code Task tool
Task(
    subagent_type="dfm-agent",
    description="Analyze circuit DFM",
    prompt="Analyze my ESP32 development board design for manufacturability at 1000 unit volume with JLCPCB"
)
```

### Direct Integration

```python
from circuit_synth.design_for_manufacturing import DFMAnalyzer
from circuit_synth import Circuit

# Create or load your circuit
circuit = Circuit("my_design")
# ... add components ...

# Run DFM analysis
analyzer = DFMAnalyzer()
report = analyzer.analyze_circuit(
    circuit_data=circuit.to_dict(),
    volume=1000,
    target_cost=50.00,
    manufacturing_site="jlcpcb"
)

# Get results
print(report.get_executive_summary())
```

## Analysis Workflow

### 1. Initial Assessment (30 seconds)
- Component count and diversity analysis
- Technology mix evaluation (SMT, THT, mixed)
- Complexity scoring
- Manufacturing process determination

### 2. Component Analysis (60 seconds)
- Package manufacturability scoring
- Availability verification
- Lifecycle status checking
- Cost analysis per component
- Alternative component identification

### 3. Issue Detection (45 seconds)

#### Issue Severity Levels
- **CRITICAL**: Will prevent manufacturing
  - Obsolete/unavailable components
  - Incompatible footprints
  - Design rule violations
  
- **HIGH**: Significant yield/cost impact
  - Low availability components
  - Challenging packages (0201, µBGA)
  - Mixed technology requirements
  
- **MEDIUM**: Moderate impact
  - Non-optimal selections
  - Inefficient panelization
  - Limited testability

### 4. Cost Analysis (30 seconds)
- Component cost calculation
- PCB fabrication cost
- Assembly cost estimation
- Volume pricing breakdowns
- Cost reduction opportunities

## DFM Metrics

### Scoring System
```python
{
    "overall_manufacturability_score": 0-100,  # Higher is better
    "cost_optimization_score": 0-100,          # Higher is better
    "supply_chain_risk_score": 0-100,          # Lower is better
    "component_availability": 0-100,           # Higher is better
    "assembly_complexity": 0-100               # Lower is better
}
```

### Manufacturing Constraints
```python
{
    "min_trace_width_mm": 0.127,      # 5 mil standard
    "min_via_size_mm": 0.2,           # 8 mil standard
    "min_hole_size_mm": 0.15,         # 6 mil minimum
    "min_solder_mask_clearance": 0.05,
    "min_component_spacing": 0.25      # Keep-out zone
}
```

## Best Practices

### Component Selection
1. **Prefer JLCPCB Basic Parts**: No sourcing delay, lower assembly cost
2. **Ensure High Stock Levels**: Target >10k inventory
3. **Multiple Sources**: Choose components with 2+ suppliers
4. **Standard Packages**: Use common footprints (0603, 0805, SOIC)
5. **Avoid EOL Parts**: Check lifecycle status

### Design Optimization
1. **Minimize Unique Parts**: Consolidate component values
2. **Standardize Footprints**: Use consistent package sizes
3. **Single-Side SMT**: Place all SMT on one side if possible
4. **Testability**: Include test points on critical signals
5. **Panelization**: Design for efficient panel utilization

### Cost Reduction
1. **Component Consolidation**: Reduce BOM line items
2. **Value Engineering**: Find cost-effective alternatives
3. **Volume Optimization**: Balance price breaks vs. inventory
4. **Technology Standardization**: Minimize assembly processes

## Example Analysis Output

```
DFM Analysis Executive Summary
==============================
Circuit: ESP32_DevBoard_v1
Date: 2025-01-28T10:30:00Z

Key Metrics:
- Total Components: 47
- Unique Parts: 23
- Manufacturability Score: 85.3/100
- Cost Optimization Score: 78.2/100
- Supply Chain Risk: 15.7/100

Cost Analysis:
- Component Cost: $12.45
- PCB Cost: $3.20
- Assembly Cost: $4.85
- Total Unit Cost: $20.50

Issues Summary:
- Critical Issues: 0
- High Priority Issues: 2
- Total Issues: 8

Top Recommendations:
1. Replace THT headers with SMT variants
   Recommendation: Use SMT pin headers to reduce assembly cost
2. Consolidate resistor values
   Recommendation: Standardize on E12 series values
3. Update voltage regulator selection
   Recommendation: Use AMS1117-3.3 (JLCPCB basic part)
```

## Integration with Other Agents

The DFM agent works well with:
- **component-guru**: For detailed component sourcing
- **jlc-parts-finder**: For JLCPCB availability verification
- **circuit-architect**: For design-level optimizations
- **circuit-generation-agent**: For implementing DFM feedback

## Common Issues and Solutions

### Issue: Low Availability Components
**Solution**: Use the agent to find alternatives with better stock levels

### Issue: Mixed Technology Assembly
**Solution**: Convert THT components to SMT where possible

### Issue: High BOM Cost
**Solution**: Run value engineering analysis for cost-effective alternatives

### Issue: Poor Testability
**Solution**: Add test points following IPC standards

## Advanced Features

### Custom Manufacturing Rules
```python
custom_rules = {
    "manufacturer": "custom_fab",
    "min_trace_width_mm": 0.1,
    "preferred_packages": ["0603", "0805", "SOIC"],
    "assembly_capabilities": ["SMT", "selective_wave"]
}
analyzer.set_manufacturing_rules(custom_rules)
```

### Batch Analysis
```python
# Analyze multiple design variants
variants = ["design_v1", "design_v2", "design_v3"]
results = []
for variant in variants:
    report = analyzer.analyze_circuit(
        circuit_data=load_circuit(variant),
        volume=1000
    )
    results.append(report)

# Compare results
best_design = min(results, key=lambda r: r.total_unit_cost)
```

## Related Documentation

- [DFMAnalyzer API Reference](../api/dfm_analyzer.md)
- [Manufacturing Integration Guide](../manufacturing/README.md)
- [Component Sourcing Best Practices](../best_practices/component_sourcing.md)
- [JLCPCB Integration](../manufacturing/jlcpcb.md)