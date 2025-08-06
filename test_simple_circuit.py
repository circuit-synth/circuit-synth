#!/usr/bin/env python3
"""
Test the universal FMEA analyzer with different circuit examples
"""

from circuit_synth.quality_assurance import analyze_any_circuit
import json
import os

def test_simple_power_supply():
    """Test with a simple power supply circuit"""
    
    print("\n" + "="*60)
    print("TEST 1: Simple Power Supply Circuit")
    print("="*60)
    
    # Create a simple power supply circuit
    os.makedirs('test_circuits', exist_ok=True)
    
    circuit = {
        'components': {
            'J1': {'symbol': 'Connector:Barrel_Jack', 'footprint': 'Connector:BarrelJack'},
            'U1': {'symbol': 'Regulator_Linear:L7805', 'footprint': 'Package_TO:TO-220'},
            'C1': {'symbol': 'Device:C', 'value': '100uF', 'footprint': 'Capacitor:CP_Radial'},
            'C2': {'symbol': 'Device:C', 'value': '10uF', 'footprint': 'Capacitor_SMD:C_1206'},
            'D1': {'symbol': 'Diode:1N4007', 'footprint': 'Diode:D_DO-41'},
            'LED1': {'symbol': 'Device:LED', 'footprint': 'LED_THT:LED_D5.0mm'},
            'R1': {'symbol': 'Device:R', 'value': '470', 'footprint': 'Resistor_THT:R_Axial'},
        },
        'nets': {
            'VIN': ['J1.1', 'D1.A', 'C1.1', 'U1.VI'],
            'GND': ['J1.2', 'C1.2', 'U1.GND', 'C2.2', 'R1.2'],
            'VOUT': ['U1.VO', 'C2.1', 'LED1.A'],
            'LED_NET': ['LED1.K', 'R1.1']
        }
    }
    
    with open('test_circuits/power_supply.json', 'w') as f:
        json.dump(circuit, f)
    
    # Analyze it
    report = analyze_any_circuit('test_circuits/power_supply.json', 
                                 'Simple_Power_Supply_FMEA.pdf')
    print(f"✅ Generated: {report}")


def test_sensor_interface():
    """Test with a sensor interface circuit"""
    
    print("\n" + "="*60)
    print("TEST 2: I2C Sensor Interface Circuit")
    print("="*60)
    
    circuit = {
        'components': {
            'U1': {'symbol': 'Sensor:BME280', 'footprint': 'Package_LGA:LGA-8'},
            'U2': {'symbol': 'MCU_Microchip:ATmega328P-AU', 'footprint': 'Package_QFP:TQFP-32'},
            'C1': {'symbol': 'Device:C', 'value': '100nF', 'footprint': 'Capacitor_SMD:C_0603'},
            'C2': {'symbol': 'Device:C', 'value': '100nF', 'footprint': 'Capacitor_SMD:C_0603'},
            'R1': {'symbol': 'Device:R', 'value': '4.7k', 'footprint': 'Resistor_SMD:R_0603'},
            'R2': {'symbol': 'Device:R', 'value': '4.7k', 'footprint': 'Resistor_SMD:R_0603'},
            'J1': {'symbol': 'Connector:Conn_01x04', 'footprint': 'Connector_PinHeader:1x04'},
        },
        'nets': {
            'VCC': ['U1.VDD', 'U2.VCC', 'C1.1', 'C2.1', 'R1.1', 'R2.1', 'J1.1'],
            'GND': ['U1.GND', 'U2.GND', 'C1.2', 'C2.2', 'J1.4'],
            'SDA': ['U1.SDA', 'U2.PC4', 'R1.2', 'J1.2'],
            'SCL': ['U1.SCL', 'U2.PC5', 'R2.2', 'J1.3']
        }
    }
    
    with open('test_circuits/sensor_interface.json', 'w') as f:
        json.dump(circuit, f)
    
    # Analyze it
    report = analyze_any_circuit('test_circuits/sensor_interface.json',
                                 'Sensor_Interface_FMEA.pdf')
    print(f"✅ Generated: {report}")


def test_motor_driver():
    """Test with a motor driver circuit"""
    
    print("\n" + "="*60)
    print("TEST 3: H-Bridge Motor Driver Circuit")
    print("="*60)
    
    circuit = {
        'components': {
            'U1': {'symbol': 'Driver_Motor:L298N', 'footprint': 'Package_TO:Multiwatt-15'},
            'Q1': {'symbol': 'Transistor:2N3904', 'footprint': 'Package_TO:TO-92'},
            'Q2': {'symbol': 'Transistor:2N3904', 'footprint': 'Package_TO:TO-92'},
            'D1': {'symbol': 'Diode:1N4148', 'footprint': 'Diode:D_DO-35'},
            'D2': {'symbol': 'Diode:1N4148', 'footprint': 'Diode:D_DO-35'},
            'D3': {'symbol': 'Diode:1N4148', 'footprint': 'Diode:D_DO-35'},
            'D4': {'symbol': 'Diode:1N4148', 'footprint': 'Diode:D_DO-35'},
            'C1': {'symbol': 'Device:C', 'value': '100nF', 'footprint': 'Capacitor_SMD:C_0805'},
            'C2': {'symbol': 'Device:CP', 'value': '470uF', 'footprint': 'Capacitor:CP_Radial_D10'},
            'J1': {'symbol': 'Connector:Screw_Terminal_01x02', 'footprint': 'TerminalBlock:TB_1x2'},
            'J2': {'symbol': 'Connector:Screw_Terminal_01x02', 'footprint': 'TerminalBlock:TB_1x2'},
        },
        'nets': {
            'VCC_MOTOR': ['U1.VS', 'C2.1', 'J1.1'],
            'VCC_LOGIC': ['U1.VSS', 'C1.1'],
            'GND': ['U1.GND', 'C1.2', 'C2.2', 'J1.2'],
            'MOTOR_A': ['U1.OUT1', 'D1.K', 'D2.A', 'J2.1'],
            'MOTOR_B': ['U1.OUT2', 'D3.K', 'D4.A', 'J2.2']
        }
    }
    
    with open('test_circuits/motor_driver.json', 'w') as f:
        json.dump(circuit, f)
    
    # Analyze it
    report = analyze_any_circuit('test_circuits/motor_driver.json',
                                 'Motor_Driver_FMEA.pdf')
    print(f"✅ Generated: {report}")


if __name__ == "__main__":
    print("="*60)
    print("UNIVERSAL FMEA ANALYZER TEST SUITE")
    print("Testing with various circuit types")
    print("="*60)
    
    # Run all tests
    test_simple_power_supply()
    test_sensor_interface()
    test_motor_driver()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("Generated PDF reports:")
    print("  - Simple_Power_Supply_FMEA.pdf")
    print("  - Sensor_Interface_FMEA.pdf")
    print("  - Motor_Driver_FMEA.pdf")
    print("="*60)