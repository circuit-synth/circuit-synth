# Test Plan: test_plan_demo_circuit

## Executive Summary

- **Total Test Points**: 8
- **Test Procedures**: 8
- **Estimated Duration**: 107 minutes
- **Component Types**: power_regulator, microcontroller, timing, usb_interface

## Required Test Equipment


### ESD Simulator
- **Type**: esd_gun
- **Voltage Range**: ±30kV
- **Discharge Modes**: Contact and Air
- **Standards**: IEC 61000-4-2
- **Discharge Network**: 150pF/330Ω
- **Recommended Models**: Teseq NSG 435, EM Test Dito, NoiseKen ESS-2000

### Digital Multimeter
- **Type**: multimeter
- **Voltage Range**: 0-1000V DC/AC
- **Current Range**: 0-10A
- **Resistance Range**: 0-100MΩ
- **Accuracy**: 0.5%
- **Resolution**: 6.5 digits
- **Recommended Models**: Fluke 87V, Keysight 34461A, Rigol DM3068

### Programmable Power Supply
- **Type**: power_supply
- **Channels**: 2-3
- **Voltage Range**: 0-30V
- **Current Range**: 0-5A
- **Resolution**: 1mV/1mA
- **Ripple**: <5mVpp
- **Recommended Models**: Rigol DP832, Keysight E36313A, Siglent SPD3303X

### Logic Analyzer
- **Type**: logic_analyzer
- **Channels**: 16 minimum
- **Sample Rate**: 100MSa/s
- **Memory**: 1M samples/channel
- **Protocol Decode**: I2C, SPI, UART, CAN
- **Recommended Models**: Saleae Logic Pro 16, Keysight 16850A, Digilent Digital Discovery

### Digital Oscilloscope
- **Type**: oscilloscope
- **Bandwidth**: 100MHz minimum
- **Channels**: 4
- **Sample Rate**: 1GSa/s
- **Memory Depth**: 10Mpts
- **Probes**: 10:1 passive probes
- **Recommended Models**: Rigol DS1054Z, Keysight DSOX1204A, Tektronix TBS1104

## Test Points

| ID | Net | Component | Signal Type | Nominal | Tolerance | Equipment |
|---|---|---|---|---|---|---|
| TP_VCC_3V3 | VCC_3V3 | N/A | power | 3.3V | ±5.0% | multimeter |
| TP_VCC_5V | VCC_5V | N/A | power | 5.0V | ±5.0% | multimeter |
| TP_GND | GND | N/A | ground | 0.0V | ±5.0% | multimeter |
| TP_MCU_RESET | NRST | U1 | digital | 3.3V | ±10.0% | oscilloscope |
| TP_MCU_CLOCK | HSE_IN | U1 | analog | N/A | ±2.0% | oscilloscope |
| TP_USB_VBUS | VBUS | J1 | power | 5.0V | ±5.0% | multimeter |
| TP_USB_DP | USB_DP | J1 | digital | N/A | ±10.0% | oscilloscope |
| TP_USB_DM | USB_DM | J1 | digital | N/A | ±10.0% | oscilloscope |

## Test Procedures


### Functional Tests


#### PWR-001: Power-On Sequence Test

**Description**: Verify proper power-on sequence and voltage levels

**Duration**: 10 minutes

**Required Equipment**: multimeter, oscilloscope, power_supply

**⚠️ Safety Warnings**:
- Ensure current limit is set before power-on
- Check for hot components during test

**Setup**:
1. Connect power supply to input connector
2. Set current limit to 500mA initially
3. Connect oscilloscope to power rail test points
4. Connect multimeter for DC measurements

**Test Steps**:
1. Apply input voltage slowly from 0V to nominal
2. Monitor inrush current (should be < 2A peak)
3. Verify power rail sequencing timing
4. Measure each power rail voltage: VCC_3V3, VCC_5V, VBUS
5. Check for oscillation or instability
6. Measure ripple voltage on each rail

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| VCC_3V3 | 3.3 | ±5.0% | multimeter |
| VCC_5V | 5.0 | ±5.0% | multimeter |
| VBUS | 5.0 | ±5.0% | multimeter |

**Pass Criteria**:
- Voltages In Spec: True
- Ripple Max Mv: 50
- Sequencing Correct: True
- No Oscillation: True

**If Test Fails**:
- Check power supply connections
- Verify input voltage and current limit
- Inspect voltage regulator components
- Check decoupling capacitors

#### FUNC-001: Microcontroller Functional Test

**Description**: Verify microcontroller basic functionality

**Duration**: 15 minutes

**Required Equipment**: oscilloscope, logic_analyzer

**Setup**:
1. Power on the circuit
2. Connect programmer/debugger
3. Load test firmware

**Test Steps**:
1. Verify reset functionality (pull NRST low, then release)
2. Check crystal oscillator frequency
3. Test GPIO toggle on all available pins
4. Verify UART communication at 115200 baud
5. Test I2C/SPI interfaces if present

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| Crystal frequency | 8MHz/16MHz/25MHz | ±50ppm | oscilloscope |
| GPIO high level | 3.3 | ±10% | multimeter |

**Pass Criteria**:
- Reset Works: True
- Clock Stable: True
- Gpio Functional: True
- Communication Works: True

**If Test Fails**:
- Check crystal and loading capacitors
- Verify power supply to MCU
- Check reset circuit components
- Verify programmer connections

#### FUNC-002: USB Interface Test

**Description**: Verify USB communication and compliance

**Duration**: 10 minutes

**Required Equipment**: oscilloscope, multimeter

**Setup**:
1. Connect USB cable to host computer
2. Install USB protocol analyzer software
3. Connect oscilloscope to D+ and D- lines

**Test Steps**:
1. Measure VBUS voltage (should be 5V ±5%)
2. Verify device enumeration on host
3. Check D+ pull-up resistor (1.5kΩ for full-speed)
4. Measure differential signal quality
5. Test data transfer at maximum speed

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| VBUS voltage | 5.0 | ±5% | multimeter |
| D+/D- differential | 400mV | ±10% | oscilloscope |

**Pass Criteria**:
- Enumeration Success: True
- Vbus In Spec: True
- Signal Quality Good: True
- Data Transfer Works: True

**If Test Fails**:
- Check USB connector soldering
- Verify series resistors on data lines
- Check ESD protection components
- Verify firmware USB stack

### Performance Tests


#### PERF-001: Power Consumption Test

**Description**: Measure power consumption in various operating modes

**Duration**: 20 minutes

**Required Equipment**: multimeter, power_supply

**Setup**:
1. Connect ammeter in series with power input
2. Set up automated test sequence if available
3. Prepare thermal imaging camera if available

**Test Steps**:
1. Measure idle current consumption
2. Measure active mode current (all peripherals on)
3. Measure sleep/low-power mode current
4. Calculate total power consumption
5. Check for thermal hotspots

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| Idle current | 50mA | ±20% | multimeter |
| Active current | 200mA | ±20% | multimeter |
| Sleep current | 1mA | ±50% | multimeter |

**Pass Criteria**:
- Current Within Spec: True
- No Thermal Issues: True
- Efficiency Acceptable: True

**If Test Fails**:
- Check for shorts or leakage paths
- Verify component values
- Check firmware power management
- Inspect thermal design

### Safety Tests


#### SAFE-001: ESD Protection Test

**Description**: Verify ESD protection per IEC 61000-4-2

**Duration**: 30 minutes

**Required Equipment**: esd_gun, oscilloscope

**⚠️ Safety Warnings**:
- ESD testing can damage unprotected circuits
- Ensure proper PPE when using ESD gun
- Keep sensitive equipment away from test area

**Setup**:
1. Configure ESD gun for contact discharge
2. Set initial voltage to ±2kV
3. Connect oscilloscope to monitor critical signals
4. Ensure proper grounding of test setup

**Test Steps**:
1. Apply ±2kV contact discharge to exposed connectors
2. Apply ±4kV contact discharge to ground planes
3. Apply ±8kV air discharge to plastic enclosure
4. Verify circuit functionality after each discharge
5. Check for latch-up conditions

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| Recovery time | <1s | N/A | oscilloscope |
| Functionality | Normal operation | No permanent damage | functional_test |

**Pass Criteria**:
- No Permanent Damage: True
- Auto Recovery: True
- Data Integrity: True

**If Test Fails**:
- Add TVS diodes on exposed signals
- Improve PCB grounding
- Add ferrite beads on cables
- Review ESD protection components

#### SAFE-002: Overvoltage Protection Test

**Description**: Verify circuit protection against overvoltage

**Duration**: 15 minutes

**Required Equipment**: power_supply, multimeter, oscilloscope

**⚠️ Safety Warnings**:
- Overvoltage testing may damage components
- Use current limiting for safety
- Have replacement components ready

**Setup**:
1. Connect variable power supply
2. Set current limit to safe value
3. Monitor critical component voltages

**Test Steps**:
1. Gradually increase input voltage to 110% of maximum
2. Monitor protection circuit activation
3. Verify no damage to downstream components
4. Test auto-recovery when voltage returns to normal
5. Check protection response time

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| Protection threshold | 110% of Vmax | ±5% | multimeter |
| Response time | <100µs | N/A | oscilloscope |

**Pass Criteria**:
- Protection Activates: True
- No Component Damage: True
- Auto Recovery Works: True

**If Test Fails**:
- Check TVS diode specifications
- Verify crowbar circuit operation
- Review input protection design
- Add redundant protection

### Manufacturing Tests


#### MFG-001: In-Circuit Test (ICT)

**Description**: Automated bed-of-nails testing for production

**Duration**: 2 minutes

**Required Equipment**: ICT_fixture, multimeter

**Setup**:
1. Load board into ICT fixture
2. Ensure all test points make contact
3. Load test program into ICT system

**Test Steps**:
1. Test continuity of all nets
2. Verify component presence and orientation
3. Measure passive component values (R, C, L)
4. Check for shorts between adjacent nets
5. Verify power supply isolation

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| Net continuity | <1Ω | N/A | ICT_system |
| Component values | Per BOM | ±5% | ICT_system |

**Pass Criteria**:
- All Nets Connected: True
- No Shorts: True
- Components Correct: True
- Values In Tolerance: True

**If Test Fails**:
- Inspect solder joints
- Check component placement
- Verify PCB fabrication
- Review assembly process

#### MFG-002: Boundary Scan Test (JTAG)

**Description**: JTAG boundary scan for digital connectivity

**Duration**: 5 minutes

**Required Equipment**: JTAG_programmer, boundary_scan_software

**Setup**:
1. Connect JTAG adapter to test points
2. Load boundary scan description files
3. Configure scan chain

**Test Steps**:
1. Verify JTAG chain integrity
2. Run interconnect test
3. Test pull-up/pull-down resistors
4. Verify crystal connections
5. Program device ID for traceability

**Measurements**:
| Parameter | Nominal | Tolerance | Equipment |
|---|---|---|---|
| Chain integrity | Complete | N/A | JTAG_tester |
| Interconnect test | 100% pass | N/A | JTAG_tester |

**Pass Criteria**:
- Chain Complete: True
- Interconnect Pass: True
- Device Id Programmed: True

**If Test Fails**:
- Check JTAG connector soldering
- Verify MCU power and ground
- Inspect BGA balls if applicable
- Review JTAG signal integrity

## Test Execution Summary

| Test ID | Test Name | Category | Duration | Status | Notes |
|---|---|---|---|---|---|
| PWR-001 | Power-On Sequence Test | functional | 10 min | [ ] Pass [ ] Fail | |
| FUNC-001 | Microcontroller Functional Test | functional | 15 min | [ ] Pass [ ] Fail | |
| FUNC-002 | USB Interface Test | functional | 10 min | [ ] Pass [ ] Fail | |
| PERF-001 | Power Consumption Test | performance | 20 min | [ ] Pass [ ] Fail | |
| SAFE-001 | ESD Protection Test | safety | 30 min | [ ] Pass [ ] Fail | |
| SAFE-002 | Overvoltage Protection Test | safety | 15 min | [ ] Pass [ ] Fail | |
| MFG-001 | In-Circuit Test (ICT) | manufacturing | 2 min | [ ] Pass [ ] Fail | |
| MFG-002 | Boundary Scan Test (JTAG) | manufacturing | 5 min | [ ] Pass [ ] Fail | |

## Sign-off

- **Tested By**: _________________________ Date: _____________
- **Reviewed By**: _______________________ Date: _____________
- **Approved By**: _______________________ Date: _____________