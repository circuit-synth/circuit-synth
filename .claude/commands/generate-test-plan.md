---
allowed-tools: ['*']
description: Create comprehensive test procedures and fixture requirements\n---\n\nGenerate a complete test plan and procedures for the current circuit design.

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
- Manufacturing-friendly design modifications for testability