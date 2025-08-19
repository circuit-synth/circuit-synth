from circuit_synth import *

@circuit(name="audio_circuit")
def audio_circuit(vcc_3v3, gnd):
    """Audio/buzzer circuit for sound generation"""
    
    # Buzzer component
    buzzer = Component(
        symbol="Device:Buzzer",
        ref="BZ1",
        footprint="Buzzer_Beeper:Buzzer_12x9.5RM7.6"
    )
    
    # Transistor for amplification
    transistor = Component(
        symbol="Device:Q_NPN_BCE",
        ref="Q1",
        footprint="Package_TO_SOT_SMD:SOT-23"
    )
    
    # Base resistor
    r_base = Component(
        symbol="Device:R",
        ref="R20",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Control signal from MCU
    buzzer_ctrl = Net('BUZZER_CTRL')
    
    # Connections
    r_base[1] += buzzer_ctrl      # MCU control signal
    r_base[2] += transistor[1]    # Base
    transistor[2] += gnd          # Emitter
    transistor[3] += buzzer[2]    # Collector to buzzer negative
    buzzer[1] += vcc_3v3         # Buzzer positive to VCC
