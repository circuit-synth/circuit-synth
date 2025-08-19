from circuit_synth import *

@circuit(name="motor_driver_circuit")
def motor_driver_circuit(vcc_3v3, gnd):
    """Motor driver circuit for robot control"""
    
    # Motor driver IC
    driver = Component(
        symbol="Driver_Motor:DRV8833",
        ref="U3",
        footprint="Package_SON:WSON-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm"
    )
    
    # Decoupling capacitor
    cap = Component(
        symbol="Device:C",
        ref="C10",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Motor nets
    motor1_a = Net('MOTOR1_A')
    motor1_b = Net('MOTOR1_B') 
    motor2_a = Net('MOTOR2_A')
    motor2_b = Net('MOTOR2_B')
    
    # Control signals from MCU
    ain1 = Net('AIN1')
    ain2 = Net('AIN2')
    bin1 = Net('BIN1')
    bin2 = Net('BIN2')
    
    # Power connections
    driver[1] += vcc_3v3   # VCC
    driver[2] += gnd       # GND
    
    # Control inputs
    driver[5] += ain1      # AIN1
    driver[6] += ain2      # AIN2
    driver[9] += bin1      # BIN1
    driver[10] += bin2     # BIN2
    
    # Motor outputs
    driver[3] += motor1_a  # AOUT1
    driver[4] += motor1_b  # AOUT2
    driver[7] += motor2_a  # BOUT1
    driver[8] += motor2_b  # BOUT2
    
    # Decoupling
    cap[1] += vcc_3v3
    cap[2] += gnd
