# Circuit Implementation ERD (Entity-Relationship Diagram)

## Overview
This document defines the data architecture and relationships for implementing professional-grade circuits across the Circuit-Synth ecosystem (Circuit-Synth, Circuit-Simulation, Circuit-Intelligence).

## Target Circuits
1. **USB-C PD Negotiator** - Power delivery negotiation with STUSB4500
2. **Precision DAQ Board** - 24-bit ADC with anti-aliasing filters
3. **Isolated Industrial IoT Gateway** - ESP32-C6 + Ethernet W5500 + RS485/CAN + LoRa
4. **Battery Management System** - Multi-cell monitoring and protection
5. **I2C/SPI Sensor Hub** - Environmental and motion sensing
6. **PMSM Motor Controller** - STM32G4 with FOC control
7. **Automotive CAN Gateway** - CAN-FD/LIN/OBD-II interface
8. **PoE Powered Device** - 25W isolated power extraction

## Core Entities

### 1. Circuit Project
```
CircuitProject {
    id: UUID
    name: String
    type: Enum[USB_PD, DAQ, IoT_GATEWAY, BMS, SENSOR_HUB, MOTOR_CTRL, CAN_GW, POE]
    description: String
    version: String
    status: Enum[DESIGN, SIMULATION, TESTED, PRODUCTION]
    created_at: DateTime
    updated_at: DateTime
    metadata: JSON {
        voltage_levels: Array[Float]
        current_rating: Float
        power_budget: Float
        communication_protocols: Array[String]
        certification_targets: Array[String]
    }
}
```

### 2. Component
```
Component {
    id: UUID
    circuit_id: UUID (FK -> CircuitProject)
    reference_designator: String (e.g., "U1", "R1")
    part_number: String
    manufacturer: String
    value: String
    package: String
    category: Enum[IC, PASSIVE, CONNECTOR, MECHANICAL, POWER]
    jlcpcb_part: String (nullable)
    datasheet_url: String
    specifications: JSON {
        tolerance: String
        voltage_rating: Float
        current_rating: Float
        temperature_range: String
        key_parameters: Object
    }
}
```

### 3. Net
```
Net {
    id: UUID
    circuit_id: UUID (FK -> CircuitProject)
    name: String
    type: Enum[POWER, GROUND, SIGNAL, DIFFERENTIAL, HIGH_CURRENT]
    voltage_nominal: Float
    voltage_tolerance: Float
    current_max: Float
    impedance_target: Float (nullable)
    length_matched_group: String (nullable)
}
```

### 4. Connection
```
Connection {
    id: UUID
    net_id: UUID (FK -> Net)
    component_id: UUID (FK -> Component)
    pin_number: String
    pin_name: String
    pin_type: Enum[INPUT, OUTPUT, BIDIRECTIONAL, POWER, GROUND, PASSIVE]
    electrical_characteristics: JSON {
        voltage_levels: Object
        current_capability: Float
        impedance: Float
        rise_time: Float
    }
}
```

### 5. Power Domain
```
PowerDomain {
    id: UUID
    circuit_id: UUID (FK -> CircuitProject)
    name: String
    voltage: Float
    tolerance_percent: Float
    current_budget: Float
    source_type: Enum[EXTERNAL, BUCK, BOOST, LDO, ISOLATED, POE, USB_PD]
    parent_domain_id: UUID (nullable, FK -> PowerDomain)
    efficiency: Float
    sequencing_order: Integer
}
```

### 6. Simulation Model
```
SimulationModel {
    id: UUID
    component_id: UUID (FK -> Component)
    model_type: Enum[SPICE, IBIS, S_PARAMETER, BEHAVIORAL]
    model_source: Enum[MANUFACTURER, GENERIC, MEASURED, DERIVED]
    model_data: TEXT
    valid_frequency_range: JSON {min: Float, max: Float}
    temperature_range: JSON {min: Float, max: Float}
    validation_status: Enum[UNVALIDATED, VALIDATED, SUSPECT]
}
```

### 7. Test Point
```
TestPoint {
    id: UUID
    circuit_id: UUID (FK -> CircuitProject)
    net_id: UUID (FK -> Net)
    designator: String (e.g., "TP1")
    purpose: String
    expected_value: JSON {
        nominal: Float
        tolerance: Float
        units: String
        conditions: String
    }
    measurement_type: Enum[DC, AC, DIGITAL, WAVEFORM]
    accessibility: Enum[TOP, BOTTOM, EDGE, INTERNAL]
}
```

### 8. Simulation Scenario
```
SimulationScenario {
    id: UUID
    circuit_id: UUID (FK -> CircuitProject)
    name: String
    type: Enum[DC_OP, AC_SWEEP, TRANSIENT, MONTE_CARLO, THERMAL]
    description: String
    configuration: JSON {
        temperature: Float
        input_conditions: Object
        load_conditions: Object
        parameter_sweeps: Array
    }
    pass_criteria: JSON {
        measurements: Array[{
            test_point_id: UUID
            condition: String
            limits: Object
        }]
    }
}
```

### 9. Simulation Result
```
SimulationResult {
    id: UUID
    scenario_id: UUID (FK -> SimulationScenario)
    timestamp: DateTime
    status: Enum[PASS, FAIL, WARNING, ERROR]
    simulator: String
    simulator_version: String
    results_data: JSON {
        measurements: Object
        waveforms: Object
        statistics: Object
    }
    convergence_info: JSON
    warnings: Array[String]
}
```

### 10. DFM Check
```
DFMCheck {
    id: UUID
    circuit_id: UUID (FK -> CircuitProject)
    manufacturer: String
    check_type: Enum[COMPONENT_AVAILABILITY, ASSEMBLY, TESTABILITY, COST]
    timestamp: DateTime
    results: JSON {
        issues: Array[{
            severity: Enum[ERROR, WARNING, INFO]
            component_id: UUID
            message: String
            suggestion: String
        }]
        cost_estimate: Float
        lead_time_days: Integer
    }
}
```

### 11. Intelligence Query
```
IntelligenceQuery {
    id: UUID
    circuit_id: UUID (FK -> CircuitProject)
    query_type: Enum[DESIGN_REVIEW, OPTIMIZATION, TROUBLESHOOTING, ALTERNATIVE]
    query_text: String
    context: JSON {
        focus_components: Array[UUID]
        focus_nets: Array[UUID]
        constraints: Object
    }
    timestamp: DateTime
}
```

### 12. Intelligence Response
```
IntelligenceResponse {
    id: UUID
    query_id: UUID (FK -> IntelligenceQuery)
    response_text: TEXT
    recommendations: JSON {
        changes: Array[{
            type: String
            target: Object
            rationale: String
            impact: String
        }]
        alternatives: Array[Object]
        risks: Array[String]
    }
    confidence_score: Float
    references: Array[String]
}
```

## Relationships

### Primary Relationships
- CircuitProject (1) -> (N) Component
- CircuitProject (1) -> (N) Net
- CircuitProject (1) -> (N) PowerDomain
- CircuitProject (1) -> (N) TestPoint
- CircuitProject (1) -> (N) SimulationScenario
- Net (1) -> (N) Connection
- Component (1) -> (N) Connection
- Component (1) -> (1) SimulationModel
- PowerDomain (1) -> (N) PowerDomain (hierarchical)
- SimulationScenario (1) -> (N) SimulationResult
- CircuitProject (1) -> (N) DFMCheck
- CircuitProject (1) -> (N) IntelligenceQuery
- IntelligenceQuery (1) -> (N) IntelligenceResponse

### Circuit-Specific Extensions

#### USB-C PD Negotiator
```
USBPDProfile {
    circuit_id: UUID (FK -> CircuitProject)
    profile_number: Integer
    voltage: Float
    current: Float
    pps_enabled: Boolean
    pps_voltage_range: JSON
}
```

#### Precision DAQ
```
FilterStage {
    circuit_id: UUID (FK -> CircuitProject)
    stage_number: Integer
    filter_type: Enum[BUTTERWORTH, CHEBYSHEV, BESSEL]
    order: Integer
    cutoff_frequency: Float
    gain: Float
}
```

#### IoT Gateway
```
CommunicationInterface {
    circuit_id: UUID (FK -> CircuitProject)
    interface_type: Enum[ETHERNET, WIFI, LORA, RS485, CAN]
    transceiver_ic: String
    max_data_rate: Float
    isolation_voltage: Float
}
```

#### Battery Management
```
BatteryCell {
    circuit_id: UUID (FK -> CircuitProject)
    cell_number: Integer
    chemistry: Enum[LIION, LIPO, LIFEPO4, NIMH]
    nominal_voltage: Float
    capacity_ah: Float
    max_charge_current: Float
    balancing_current: Float
}
```

#### Motor Controller
```
MotorPhase {
    circuit_id: UUID (FK -> CircuitProject)
    phase: Enum[U, V, W]
    high_side_fet: UUID (FK -> Component)
    low_side_fet: UUID (FK -> Component)
    current_sense_resistor: UUID (FK -> Component)
    gate_driver_channel: String
}
```

## Implementation Workflow

### Phase 1: Circuit Definition
1. Create CircuitProject entity
2. Define PowerDomains hierarchy
3. Import/create Components
4. Establish Nets and Connections
5. Add TestPoints for validation

### Phase 2: Simulation Setup
1. Attach SimulationModels to Components
2. Define SimulationScenarios
3. Run simulations and store Results
4. Validate against pass criteria

### Phase 3: Manufacturing Validation
1. Run DFMChecks against JLCPCB database
2. Verify component availability
3. Check assembly constraints
4. Generate cost estimates

### Phase 4: Intelligence Integration
1. Submit design for IntelligenceQuery review
2. Process recommendations
3. Iterate design based on feedback
4. Document design decisions

## Data Storage Strategy

### Primary Database (PostgreSQL)
- All entity tables with proper indexing
- Foreign key constraints for relationships
- JSON columns for flexible metadata

### Time-Series Database (InfluxDB)
- Simulation waveform data
- Test measurement results
- Real-time monitoring data

### Document Store (MongoDB)
- Simulation models (SPICE netlists)
- Intelligence conversation history
- Design documentation

### File Storage (S3/Local)
- KiCad project files
- PDF datasheets
- Gerber/production files
- Simulation output files

## API Design

### RESTful Endpoints
```
/api/circuits                    # CRUD for CircuitProject
/api/circuits/{id}/components    # Component management
/api/circuits/{id}/simulate      # Trigger simulation
/api/circuits/{id}/dfm-check    # Run DFM validation
/api/circuits/{id}/intelligence # Query intelligence system
```

### GraphQL Schema
```graphql
type CircuitProject {
    id: ID!
    name: String!
    components: [Component!]!
    nets: [Net!]!
    powerDomains: [PowerDomain!]!
    simulationScenarios: [SimulationScenario!]!
    latestDFMCheck: DFMCheck
}
```

## Performance Considerations

### Indexing Strategy
- Index on circuit_id for all child entities
- Composite index on (component_id, pin_number) for Connections
- Full-text search on Intelligence queries/responses

### Caching Strategy
- Cache component library data (rarely changes)
- Cache simulation models
- Cache DFM check results (TTL: 24 hours)

### Optimization Targets
- Sub-second circuit loading
- Parallel simulation execution
- Incremental DFM checking
- Streaming intelligence responses

## Version Control Integration

### Git Integration
- Track ERD schema versions
- Link commits to CircuitProject versions
- Store circuit snapshots at key milestones

### Migration Strategy
- Use Alembic/Flyway for schema migrations
- Maintain backward compatibility
- Version all API endpoints

## Success Metrics

### Design Quality
- Component reuse rate > 60%
- First-pass simulation success > 80%
- DFM check pass rate > 90%

### Performance
- Circuit load time < 1s
- Simulation setup < 5s
- Intelligence query response < 10s

### Manufacturing
- BOM cost accuracy ±5%
- Assembly yield prediction > 95%
- Lead time estimation ±2 days

## Next Steps
1. Review and refine entity definitions
2. Create database schema SQL
3. Implement ORM models (SQLAlchemy)
4. Build API layer
5. Create first circuit implementation
6. Validate with simulation
7. Test intelligence integration