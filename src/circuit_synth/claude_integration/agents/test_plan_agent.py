"""
Circuit-Synth Test Plan Creation Agent

A specialized Claude Code agent for generating comprehensive test plans 
for circuit designs, ensuring thorough validation before manufacturing.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..agent_registry import register_agent


@dataclass
class CircuitTestPoint:
    """Represents a test point in the circuit"""
    net_name: str
    position: Tuple[float, float]
    expected_value: Optional[str] = None
    test_type: str = "voltage"  # voltage, current, frequency, etc.
    tolerance: Optional[str] = None


@dataclass
class CircuitTestProcedure:
    """Represents a single test procedure"""
    name: str
    category: str  # functional, performance, safety, manufacturing
    test_points: List[CircuitTestPoint]
    equipment: List[str]
    steps: List[str]
    pass_criteria: List[str]
    fail_criteria: List[str]
    notes: Optional[str] = None


@register_agent("test-plan-creator")
class TestPlanCreatorAgent:
    """
    Specialized Claude Code agent for test plan creation.
    
    This agent helps engineers create comprehensive test plans for their circuit designs,
    including functional testing, performance validation, safety verification, and
    manufacturing test procedures.
    """
    
    def __init__(self):
        self.name = "test-plan-creator"
        self.description = "Circuit test plan generation and validation specialist"
        self.version = "1.0.0"
        self.expertise_area = "Test Plan Creation & Circuit Validation"
        
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return [
            "test_plan_generation",
            "test_point_identification", 
            "performance_test_design",
            "safety_test_procedures",
            "manufacturing_test_creation",
            "equipment_recommendations",
            "pass_fail_criteria_definition",
            "test_coverage_analysis",
            "validation_checklist_creation",
            "integration_test_planning"
        ]
        
    def get_system_prompt(self) -> str:
        """
        Return the system prompt that defines this agent's behavior.
        """
        return """You are a specialized test plan creation agent for the circuit-synth project. Your role is to generate comprehensive test plans that ensure circuit designs are thoroughly validated before manufacturing.

## Core Expertise Areas

### 1. Test Plan Generation
You excel at creating structured test plans that cover:
- **Functional Testing**: Verify all circuit functions work as designed
- **Performance Testing**: Validate specifications like power, frequency, timing
- **Safety Testing**: Ensure protection circuits and safety features function
- **Manufacturing Testing**: Create procedures for production validation

### 2. Test Point Identification
You can analyze circuit topology to identify:
- Critical voltage/current measurement points
- Signal integrity test locations
- Power rail monitoring points
- Communication interface test points
- Protection circuit validation points

### 3. Test Procedure Development
You create detailed test procedures including:
- Step-by-step test instructions
- Required test equipment specifications
- Measurement techniques and methods
- Expected values and tolerances
- Pass/fail criteria for each test

### 4. Equipment Recommendations
You provide guidance on:
- Oscilloscopes and specifications needed
- Multimeters and measurement accuracy
- Power supplies and electronic loads
- Signal generators and analyzers
- Specialized test fixtures and probes

## Test Plan Categories

### Functional Testing
- Power-on sequence verification
- Reset and initialization testing
- GPIO pin functionality validation
- Communication protocol testing (I2C, SPI, UART, USB)
- Analog circuit performance verification
- Digital logic state validation

### Performance Testing
- Power consumption measurement (active/sleep modes)
- Frequency response and bandwidth testing
- Rise/fall time measurements
- Jitter and timing analysis
- Temperature coefficient testing
- Load regulation testing

### Safety and Compliance
- ESD protection circuit validation
- Overvoltage/overcurrent protection testing
- Thermal shutdown verification
- EMI/EMC pre-compliance testing
- Isolation barrier testing
- Ground continuity verification

### Manufacturing Testing
- In-circuit testing (ICT) procedures
- Boundary scan/JTAG testing
- Functional test procedures
- Burn-in test specifications
- Visual inspection checklists
- First article inspection plans

## Working with Circuit-Synth Code

When analyzing circuit-synth Python code:
1. Parse the circuit structure to identify components and connections
2. Extract net names and component references
3. Identify power rails, signals, and interfaces
4. Determine critical paths and test points
5. Map component specifications to test parameters

## Output Formats

You can generate test plans in multiple formats:
- **Markdown**: Human-readable test procedures
- **JSON**: Structured test data for automation
- **CSV**: Test parameter matrices and limits
- **Checklist**: Quick validation checklists

## Example Test Plan Structure

```markdown
# Test Plan: [Circuit Name]

## 1. Overview
- Circuit description
- Test objectives
- Required equipment

## 2. Test Setup
- Connection diagram
- Equipment configuration
- Safety precautions

## 3. Test Procedures
### 3.1 Power-On Testing
- Steps...
- Expected results...
- Pass/fail criteria...

### 3.2 Functional Testing
- Steps...
- Measurements...
- Validation criteria...

## 4. Test Results Recording
- Data collection forms
- Measurement tables
- Pass/fail summary
```

## Integration with Circuit-Synth Workflow

1. **Analyze circuit code**: Parse the Python circuit definition
2. **Identify test requirements**: Based on circuit function and components
3. **Generate test procedures**: Create comprehensive test steps
4. **Define validation criteria**: Set clear pass/fail conditions
5. **Recommend equipment**: Specify required test instruments
6. **Create documentation**: Generate test plan in requested format

## Best Practices

- Always include safety warnings for high voltage/current tests
- Specify test equipment accuracy requirements
- Include ambient condition specifications (temperature, humidity)
- Define clear pass/fail criteria with tolerances
- Create both development and production test procedures
- Consider test time and cost optimization
- Include troubleshooting guidance for common failures

Remember: Your goal is to create test plans that ensure circuits work reliably in real-world conditions while being practical to execute in both development and manufacturing environments."""

    def get_tools(self) -> Dict[str, Any]:
        """Return tools this agent can use."""
        return {
            "analyze_circuit": {
                "description": "Analyze a circuit-synth Python file to identify test points",
                "parameters": {
                    "circuit_file": {
                        "type": "string", 
                        "description": "Path to circuit-synth Python file"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis: 'test_points', 'power_rails', 'interfaces'"
                    }
                }
            },
            "generate_test_procedure": {
                "description": "Generate a specific test procedure",
                "parameters": {
                    "test_type": {
                        "type": "string",
                        "description": "Type of test: 'functional', 'performance', 'safety', 'manufacturing'"
                    },
                    "circuit_info": {
                        "type": "object",
                        "description": "Circuit information and requirements"
                    }
                }
            },
            "recommend_equipment": {
                "description": "Recommend test equipment for specific measurements",
                "parameters": {
                    "measurement_type": {
                        "type": "string",
                        "description": "Type of measurement needed"
                    },
                    "specifications": {
                        "type": "object",
                        "description": "Required specifications (frequency, voltage, etc.)"
                    }
                }
            },
            "create_validation_checklist": {
                "description": "Create a validation checklist for the circuit",
                "parameters": {
                    "circuit_type": {
                        "type": "string",
                        "description": "Type of circuit (power, mcu, analog, etc.)"
                    },
                    "requirements": {
                        "type": "array",
                        "description": "List of requirements to validate"
                    }
                }
            },
            "export_test_plan": {
                "description": "Export test plan in specified format",
                "parameters": {
                    "format": {
                        "type": "string",
                        "description": "Output format: 'markdown', 'json', 'csv', 'checklist'"
                    },
                    "test_procedures": {
                        "type": "array",
                        "description": "List of test procedures to export"
                    }
                }
            }
        }
        
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        if tool_name == "analyze_circuit":
            return self._analyze_circuit(
                parameters.get("circuit_file", ""),
                parameters.get("analysis_type", "test_points")
            )
        elif tool_name == "generate_test_procedure":
            return self._generate_test_procedure(
                parameters.get("test_type", "functional"),
                parameters.get("circuit_info", {})
            )
        elif tool_name == "recommend_equipment":
            return self._recommend_equipment(
                parameters.get("measurement_type", ""),
                parameters.get("specifications", {})
            )
        elif tool_name == "create_validation_checklist":
            return self._create_validation_checklist(
                parameters.get("circuit_type", ""),
                parameters.get("requirements", [])
            )
        elif tool_name == "export_test_plan":
            return self._export_test_plan(
                parameters.get("format", "markdown"),
                parameters.get("test_procedures", [])
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}
            
    def _analyze_circuit(self, circuit_file: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze a circuit file to identify test points and requirements."""
        analysis_types = {
            "test_points": {
                "description": "Identify key test points in the circuit",
                "example_points": [
                    "Power rail voltages (VCC, VDD, analog supplies)",
                    "Clock signals and frequencies", 
                    "Communication interfaces (TX/RX, SDA/SCL, MISO/MOSI)",
                    "Analog inputs/outputs",
                    "Reset and control signals"
                ]
            },
            "power_rails": {
                "description": "Identify all power rails and their specifications",
                "example_rails": [
                    "Main supply voltage",
                    "Regulated outputs",
                    "Reference voltages",
                    "Analog power supplies"
                ]
            },
            "interfaces": {
                "description": "Identify communication and I/O interfaces",
                "example_interfaces": [
                    "USB connections",
                    "Serial interfaces (UART, SPI, I2C)",
                    "GPIO pins",
                    "Analog interfaces"
                ]
            }
        }
        
        return {
            "circuit_file": circuit_file,
            "analysis_type": analysis_type,
            "analysis_info": analysis_types.get(analysis_type, {}),
            "suggestion": "Use the Read tool to analyze the actual circuit file",
            "next_steps": [
                "Parse the circuit structure",
                "Identify components and nets",
                "Extract test point candidates",
                "Determine measurement requirements"
            ]
        }
        
    def _generate_test_procedure(self, test_type: str, circuit_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a specific test procedure."""
        test_templates = {
            "functional": {
                "name": "Functional Test Procedure",
                "sections": [
                    "Power-on sequence verification",
                    "Reset and initialization testing",
                    "Communication interface validation",
                    "GPIO functionality testing",
                    "Basic operation verification"
                ],
                "equipment": ["Multimeter", "Oscilloscope", "Power supply", "Logic analyzer"]
            },
            "performance": {
                "name": "Performance Test Procedure",
                "sections": [
                    "Power consumption measurement",
                    "Frequency response testing",
                    "Timing analysis",
                    "Load regulation testing",
                    "Temperature testing"
                ],
                "equipment": ["Oscilloscope", "Spectrum analyzer", "Electronic load", "Temperature chamber"]
            },
            "safety": {
                "name": "Safety Test Procedure", 
                "sections": [
                    "ESD protection testing",
                    "Overvoltage protection validation",
                    "Overcurrent protection testing",
                    "Thermal protection verification",
                    "Isolation testing"
                ],
                "equipment": ["ESD gun", "High voltage supply", "Insulation tester", "Thermal camera"]
            },
            "manufacturing": {
                "name": "Manufacturing Test Procedure",
                "sections": [
                    "In-circuit testing (ICT)",
                    "Boundary scan testing",
                    "Functional testing",
                    "Burn-in specifications",
                    "Visual inspection"
                ],
                "equipment": ["ICT fixture", "Boundary scan tester", "Automated test equipment"]
            }
        }
        
        template = test_templates.get(test_type, test_templates["functional"])
        
        return {
            "test_type": test_type,
            "procedure_template": template,
            "circuit_info": circuit_info,
            "customization_needed": [
                "Add circuit-specific test points",
                "Define exact measurement values",
                "Set appropriate tolerances",
                "Specify test conditions"
            ]
        }
        
    def _recommend_equipment(self, measurement_type: str, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend test equipment for specific measurements."""
        equipment_db = {
            "voltage": {
                "basic": "Digital multimeter (DMM) with 0.1% accuracy",
                "precision": "6.5 digit bench DMM (Keithley, Keysight)",
                "high_voltage": "High voltage probe with appropriate rating"
            },
            "current": {
                "basic": "Current clamp meter",
                "precision": "Precision current shunt with DMM",
                "high_current": "Hall effect current probe"
            },
            "frequency": {
                "basic": "Frequency counter",
                "precision": "Spectrum analyzer or high-bandwidth oscilloscope",
                "rf": "Vector network analyzer (VNA)"
            },
            "timing": {
                "basic": "Digital oscilloscope with math functions",
                "precision": "High-bandwidth oscilloscope with jitter analysis",
                "specialized": "Time interval analyzer"
            },
            "temperature": {
                "basic": "Thermocouple with meter",
                "precision": "RTD sensor with precision meter",
                "imaging": "Thermal imaging camera"
            }
        }
        
        equipment = equipment_db.get(measurement_type, {})
        
        return {
            "measurement_type": measurement_type,
            "specifications": specifications,
            "recommended_equipment": equipment,
            "selection_criteria": [
                "Measurement accuracy requirements",
                "Frequency/bandwidth needs",
                "Safety ratings",
                "Budget constraints"
            ]
        }
        
    def _create_validation_checklist(self, circuit_type: str, requirements: List[str]) -> Dict[str, Any]:
        """Create a validation checklist for the circuit."""
        checklist_templates = {
            "power": [
                "Input voltage range verified",
                "Output voltage accuracy within spec",
                "Load regulation tested",
                "Ripple and noise within limits",
                "Thermal performance validated",
                "Protection circuits functional"
            ],
            "mcu": [
                "Power supplies within tolerance",
                "Clock frequency accurate",
                "Reset circuit functional",
                "Programming interface working",
                "GPIO pins tested",
                "Communication interfaces validated"
            ],
            "analog": [
                "Supply voltages correct",
                "Reference voltages stable",
                "Gain/attenuation accurate",
                "Frequency response meets spec",
                "Noise levels acceptable",
                "Offset/drift within limits"
            ],
            "rf": [
                "Frequency accuracy verified",
                "Power output within spec",
                "Impedance matching confirmed",
                "Spurious emissions checked",
                "Sensitivity meets requirements",
                "Antenna performance validated"
            ]
        }
        
        base_checklist = checklist_templates.get(circuit_type, [])
        
        return {
            "circuit_type": circuit_type,
            "base_checklist": base_checklist,
            "custom_requirements": requirements,
            "checklist_format": {
                "item": "Test description",
                "result": "Pass/Fail/NA",
                "value": "Measured value",
                "notes": "Additional observations"
            }
        }
        
    def _export_test_plan(self, format: str, test_procedures: List[Any]) -> Dict[str, Any]:
        """Export test plan in specified format."""
        export_formats = {
            "markdown": {
                "extension": ".md",
                "description": "Human-readable markdown format",
                "features": ["Headers", "Tables", "Checklists", "Code blocks"]
            },
            "json": {
                "extension": ".json",
                "description": "Machine-readable JSON format",
                "features": ["Structured data", "Easy parsing", "API integration"]
            },
            "csv": {
                "extension": ".csv",
                "description": "Spreadsheet-compatible CSV format",
                "features": ["Test matrices", "Parameter tables", "Import to Excel"]
            },
            "checklist": {
                "extension": ".txt",
                "description": "Simple checklist format",
                "features": ["Quick reference", "Print-friendly", "Easy marking"]
            }
        }
        
        format_info = export_formats.get(format, export_formats["markdown"])
        
        return {
            "format": format,
            "format_info": format_info,
            "procedures_count": len(test_procedures),
            "export_steps": [
                f"Format procedures for {format} output",
                f"Create file with {format_info['extension']} extension",
                "Include all test procedures and criteria",
                "Add metadata and revision information"
            ]
        }
        
    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "expertise_area": self.expertise_area,
            "capabilities": self.get_capabilities(),
            "priority": "medium",
            "usage_context": "test_plan_creation",
            "integration_points": [
                "Circuit topology analysis",
                "Component specification extraction",
                "Manufacturing requirements",
                "Simulation result integration"
            ],
            "output_formats": ["markdown", "json", "csv", "checklist"]
        }


# Register the agent when module is imported  
test_plan_agent = TestPlanCreatorAgent()