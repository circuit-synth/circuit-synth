#!/usr/bin/env python3
"""
Thermistor Temperature Sensing Circuit
Uses NTC thermistor in voltage divider configuration for temperature measurement
"""

from circuit_synth import *

@circuit(name="Thermistor_Temperature_Sensor")
def thermistor_sensor(vcc, adc_input, gnd, thermistor_type="NTC_10k"):
    """
    Thermistor-based temperature sensor circuit

    Uses a voltage divider with thermistor and fixed resistor.
    ADC reads the voltage, which varies with temperature.

    Common thermistor types:
    - NTC (Negative Temperature Coefficient): Resistance decreases with temperature
    - Most common for temperature sensing

    Args:
        vcc: Supply voltage (typically 3.3V or 5V)
        adc_input: ADC input pin for temperature reading
        gnd: Ground reference
        thermistor_type: Type of thermistor (e.g., "NTC_10k", "NTC_100k")

    Circuit topology:
        VCC --- [R_fixed] --- [ADC_input] --- [Thermistor] --- GND

    Voltage at ADC = VCC * (R_thermistor / (R_fixed + R_thermistor))

    Temperature calculation (simplified Steinhart-Hart):
        T = 1 / (A + B*ln(R) + C*ln(R)^3)
    where R is thermistor resistance, A/B/C are calibration constants

    Typical values at 25°C:
    - NTC 10k: 10kΩ at 25°C, Beta = 3950K
    - NTC 100k: 100kΩ at 25°C, Beta = 4250K
    """

    # Parse thermistor type
    if thermistor_type == "NTC_10k":
        thermistor_value = "10k"
        fixed_resistor_value = "10k"  # Match thermistor value for best range
    elif thermistor_type == "NTC_100k":
        thermistor_value = "100k"
        fixed_resistor_value = "100k"
    else:
        thermistor_value = "10k"  # Default
        fixed_resistor_value = "10k"

    # Fixed resistor (top of divider)
    r_fixed = Component(
        symbol="Device:R",
        ref="R",
        value=fixed_resistor_value,
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # NTC Thermistor (bottom of divider)
    # Using generic thermistor symbol
    thermistor = Component(
        symbol="Device:Thermistor_NTC",
        ref="TH",
        value=thermistor_value,
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Optional: Filtering capacitor to reduce ADC noise
    cap_filter = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connections
    r_fixed[1] += vcc          # Fixed resistor to VCC
    r_fixed[2] += adc_input    # Junction point to ADC
    thermistor[1] += adc_input # Thermistor to junction/ADC
    thermistor[2] += gnd       # Thermistor to GND
    cap_filter[1] += adc_input # Filter cap across ADC input
    cap_filter[2] += gnd       # Filter cap to GND


@circuit(name="Multi_Channel_Temperature_Monitor")
def multi_temp_monitor(vcc, adc_ch1, adc_ch2, adc_ch3, gnd):
    """
    Example: Monitor multiple temperature points
    Useful for monitoring ambient, board, and component temperatures
    """
    # Ambient temperature sensor
    thermistor_sensor(vcc, adc_ch1, gnd, thermistor_type="NTC_10k")

    # Board temperature sensor
    thermistor_sensor(vcc, adc_ch2, gnd, thermistor_type="NTC_10k")

    # Component temperature sensor
    thermistor_sensor(vcc, adc_ch3, gnd, thermistor_type="NTC_10k")


# Temperature conversion reference (for firmware implementation)
"""
Firmware temperature calculation example (Python/C):

# Steinhart-Hart equation coefficients for NTC 10k thermistor (Beta=3950K)
A = 0.001129148
B = 0.000234125
C = 0.0000000876741

def read_temperature(adc_value, vcc=3.3, r_fixed=10000, adc_max=4095):
    # Convert ADC reading to voltage
    v_adc = (adc_value / adc_max) * vcc

    # Calculate thermistor resistance
    if v_adc >= vcc:  # Avoid division by zero
        return None
    r_thermistor = r_fixed * (v_adc / (vcc - v_adc))

    # Steinhart-Hart equation
    import math
    ln_r = math.log(r_thermistor)
    temp_k = 1.0 / (A + B * ln_r + C * ln_r**3)
    temp_c = temp_k - 273.15  # Convert Kelvin to Celsius

    return temp_c

# Example usage:
adc_reading = 2048  # Example 12-bit ADC reading
temperature = read_temperature(adc_reading)
print(f"Temperature: {temperature:.1f}°C")
"""
