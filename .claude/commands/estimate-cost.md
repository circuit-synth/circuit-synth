---
allowed-tools: ['*']
description: Real-time BOM cost analysis with quantity breaks and alternatives\nargument-hint: [quantity: e.g., 100, 1000, 10000]\n---\n\nGenerate comprehensive cost analysis for the current circuit design.

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
```