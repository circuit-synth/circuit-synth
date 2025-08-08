---
name: fmea-analyze
description: Perform comprehensive FMEA analysis on circuit design
---

# FMEA Comprehensive Analysis

Performs complete Failure Mode and Effects Analysis using specialized agents and knowledge base.

## Usage

```bash
/fmea-analyze <circuit_path> [options]
```

## Options

- `--industry <type>`: Specify industry (automotive, aerospace, medical, consumer, industrial)
- `--standard <name>`: Apply specific standard (AIAG-VDA, MIL-STD-1629A, IEC-60812)
- `--depth <level>`: Analysis depth (basic, standard, detailed, exhaustive)
- `--focus <area>`: Focus area (reliability, safety, manufacturing, environmental)
- `--threshold <rpn>`: RPN threshold for high-risk items (default: 125)

## What it does

1. **Orchestrates Multi-Agent Analysis**
   - Deploys fmea-orchestrator to coordinate analysis
   - Engages specialized agents based on circuit complexity
   - Queries comprehensive knowledge base

2. **Performs Deep Analysis**
   - Component-level failure modes
   - System-level interactions
   - Environmental stress factors
   - Manufacturing considerations
   - Safety implications

3. **Generates Comprehensive Report**
   - Executive summary
   - Detailed FMEA worksheets
   - Risk matrices
   - Pareto analysis
   - Mitigation strategies
   - Implementation roadmap

## Examples

```bash
# Basic analysis for consumer product
/fmea-analyze my_circuit.py --industry consumer --depth standard

# Detailed automotive analysis with AIAG-VDA standard
/fmea-analyze ESP32_Board/ --industry automotive --standard AIAG-VDA --depth detailed

# Safety-focused analysis for medical device
/fmea-analyze medical_device.json --industry medical --focus safety --threshold 100

# Exhaustive aerospace analysis
/fmea-analyze flight_controller/ --industry aerospace --depth exhaustive --standard MIL-STD-1629A
```

## Output

Generates:
- `<circuit>_FMEA_Report.pdf` - Complete analysis report
- `<circuit>_FMEA_Data.json` - Structured data for further processing
- `<circuit>_Actions.csv` - Action items with priorities
- `<circuit>_Risk_Matrix.html` - Interactive risk visualization

## Integration

This command integrates with:
- FMEA knowledge base at `/knowledge_base/fmea/`
- Specialized FMEA agents
- Circuit-synth design files
- Manufacturing databases
- Reliability standards

Use this for comprehensive reliability analysis before design release.