#!/usr/bin/env python3
"""
BB-8 Audio System
I2S audio amplifier for sound effects
"""

from circuit_synth import *

@circuit(name="bb8_audio")
def audio_system():
    """
    Audio amplifier system for BB-8 sound effects
    
    Features:
    - MAX98357A I2S Class-D amplifier
    - Speaker connection with protection
    - I2S interface from ESP32
    - Volume and gain control
    """
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3') 
    gnd = Net('GND')
    
    # I2S interface nets
    i2s_bclk = Net('I2S_BCLK')   # Bit clock
    i2s_lrclk = Net('I2S_LRCLK') # Left/Right clock
    i2s_din = Net('I2S_DIN')     # Data input
    
    # MAX98357A I2S Audio Amplifier
    audio_amp = Component(
        ref="U1",
        symbol="Audio:MAX98357A",
        footprint="Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm",
        value="MAX98357A"
    )
    
    # Power connections
    audio_amp['VDD'] += vcc_5v      # Main supply
    audio_amp['PVDD'] += vcc_5v     # Power stage
    audio_amp['AVDD'] += vcc_3v3    # Analog supply  
    audio_amp['GND'] += gnd
    audio_amp['PGND'] += gnd        # Power ground
    audio_amp['PAD'] += gnd         # Thermal pad
    
    # I2S connections
    audio_amp['BCLK'] += i2s_bclk
    audio_amp['LRC'] += i2s_lrclk
    audio_amp['DIN'] += i2s_din
    
    # Control pins
    audio_amp['SD'] += vcc_3v3      # Shutdown (high = enabled)
    audio_amp['GAIN0'] += gnd       # Gain setting
    audio_amp['GAIN1'] += gnd       # 9dB gain (moderate)
    
    # Speaker outputs
    speaker_pos = Net('SPEAKER+')
    speaker_neg = Net('SPEAKER-')
    audio_amp['OUTP'] += speaker_pos
    audio_amp['OUTN'] += speaker_neg
    
    # Speaker connector
    speaker_conn = Component(
        ref="J1",
        symbol="Connector:Screw_Terminal_01x02",
        footprint="TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal",
        value="SPEAKER"
    )
    speaker_conn[1] += speaker_pos
    speaker_conn[2] += speaker_neg
    
    # Power supply decoupling
    c_vdd_bulk = Component(
        ref="C1",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_1206_3216Metric",
        value="100uF"
    )
    c_vdd_bulk[1] += vcc_5v
    c_vdd_bulk[2] += gnd
    
    c_vdd_ceramic = Component(
        ref="C2",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_vdd_ceramic[1] += vcc_5v
    c_vdd_ceramic[2] += gnd
    
    c_pvdd_bulk = Component(
        ref="C3",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_1210_3225Metric",
        value="220uF"
    )
    c_pvdd_bulk[1] += vcc_5v
    c_pvdd_bulk[2] += gnd
    
    c_avdd = Component(
        ref="C4",
        symbol="Device:C", 
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_avdd[1] += vcc_3v3
    c_avdd[2] += gnd
    
    # Speaker output filtering (optional)
    c_speaker_filter = Component(
        ref="C5",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="1nF"
    )
    c_speaker_filter[1] += speaker_pos
    c_speaker_filter[2] += speaker_neg
    
    # I2S signal termination
    r_bclk_term = Component(
        ref="R1",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="33"
    )
    
    r_lrclk_term = Component(
        ref="R2",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="33"
    )
    
    r_din_term = Component(
        ref="R3",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="33"
    )
    
    # Audio activity LED
    led_audio = Component(
        ref="D1",
        symbol="Device:LED",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="ORANGE"
    )
    
    r_led_audio = Component(
        ref="R4",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    r_led_audio[1] += i2s_din  
    r_led_audio[2] += led_audio[1]  # Anode
    led_audio[2] += gnd  # Cathode
    
    # Audio enable/disable control
    audio_enable = Net('AUDIO_ENABLE')
    audio_amp['SD'] += audio_enable
    
    return {
        'audio_nets': {
            'I2S_BCLK': i2s_bclk,
            'I2S_LRCLK': i2s_lrclk,
            'I2S_DIN': i2s_din,
            'AUDIO_ENABLE': audio_enable
        }
    }