#!/usr/bin/env python3
"""
Buck Converter (Step-Down Switching Regulator) Circuit
Efficient voltage step-down from higher input voltage to lower output voltage
"""

from circuit_synth import *

@circuit(name="Buck_Converter_3A")
def buck_converter(vin, vout, gnd, output_voltage="3.3V", max_current="3A"):
    """
    Synchronous buck converter for efficient step-down regulation

    Key features:
    - High efficiency (typically 85-95%)
    - Low heat dissipation compared to linear regulators
    - Adjustable output voltage via feedback resistors
    - Integrated switching MOSFETs (synchronous design)

    Common applications:
    - 12V/24V to 5V/3.3V conversion
    - Battery power management
    - Automotive electronics
    - Industrial power supplies
    - POE (Power over Ethernet) step-down

    Args:
        vin: Input voltage (must be higher than output)
        vout: Regulated output voltage
        gnd: Ground reference
        output_voltage: Desired output voltage ("3.3V", "5V", "12V", etc.)
        max_current: Maximum output current ("1A", "3A", "5A", etc.)

    Example specs:
        Input: 7V-36V
        Output: 3.3V @ 3A
        Efficiency: ~90%
        Switching frequency: 400kHz-2MHz

    Common buck converter ICs:
    - TPS54331: 3A, 3.5-28V in, adjustable out, SOIC-8
    - LM2596: 3A, 4.5-40V in, adjustable out, TO-220/TO-263
    - MP2307: 3A, 4.75-23V in, adjustable out, SOIC-8
    - TPS62172: 500mA, 3-17V in, fixed 3.3V, SOT-23-5
    """

    # Buck converter IC (using TPS54331 as reference - popular 3A buck)
    # This is a synchronous buck with integrated high/low-side MOSFETs
    buck_ic = Component(
        symbol="Regulator_Switching:TPS54331",
        ref="U",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )

    # Input capacitor (low ESR ceramic)
    # Handles input ripple current
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",  # X7R/X5R ceramic, 25V+ rated
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )

    # Bootstrap capacitor (for high-side gate drive)
    cap_boot = Component(
        symbol="Device:C",
        ref="C",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Inductor (stores energy during switching)
    # Value depends on switching frequency and current
    # Typical: 10uH-47uH for 400kHz-1MHz switching
    inductor = Component(
        symbol="Device:L",
        ref="L",
        value="10uH",  # 3A rated, low DCR (<50mΩ)
        footprint="Inductor_SMD:L_1210_3225Metric"
    )

    # Output capacitor (filters output ripple)
    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="47uF",  # X7R/X5R ceramic, low ESR
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )

    # Additional output capacitor for better filtering
    cap_out2 = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Feedback resistor divider (sets output voltage)
    # Vout = Vref * (1 + R1/R2)
    # For Vref = 0.8V (TPS54331):
    # 3.3V output: R1=31.2kΩ, R2=10kΩ (use 31.6k + 10k standard values)
    # 5V output: R1=52.5kΩ, R2=10kΩ (use 52.3k + 10k)

    # Choosing values for 3.3V output
    r_fb_top = Component(
        symbol="Device:R",
        ref="R",
        value="31.6k",  # 1% tolerance recommended
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r_fb_bottom = Component(
        symbol="Device:R",
        ref="R",
        value="10k",  # 1% tolerance recommended
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Enable resistor (pull-up to enable converter)
    r_en = Component(
        symbol="Device:R",
        ref="R",
        value="100k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Soft-start capacitor (controls ramp-up time)
    cap_ss = Component(
        symbol="Device:C",
        ref="C",
        value="10nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connections
    # Input power
    buck_ic["VIN"] += vin
    buck_ic["GND"] += gnd
    buck_ic["PGND"] += gnd  # Power ground
    cap_in[1] += vin
    cap_in[2] += gnd

    # Switching node and inductor
    buck_ic["SW"] += inductor[1]  # Switch output to inductor
    inductor[2] += vout           # Inductor to output

    # Bootstrap capacitor (high-side gate drive)
    buck_ic["BOOT"] += cap_boot[1]
    cap_boot[2] += inductor[1]  # Referenced to SW node

    # Output filtering
    cap_out[1] += vout
    cap_out[2] += gnd
    cap_out2[1] += vout
    cap_out2[2] += gnd

    # Feedback network
    r_fb_top[1] += vout
    r_fb_top[2] += buck_ic["FB"]  # Feedback pin
    r_fb_bottom[1] += buck_ic["FB"]
    r_fb_bottom[2] += gnd

    # Enable control
    buck_ic["EN"] += r_en[1]
    r_en[2] += vin  # Pull-up to enable

    # Soft-start
    buck_ic["SS"] += cap_ss[1]
    cap_ss[2] += gnd


@circuit(name="Buck_Converter_Simple_5V")
def buck_converter_simple_5v(vin_12v, vout_5v, gnd):
    """
    Simplified 12V to 5V buck converter example

    Application: Automotive/industrial 12V to 5V logic supply
    Specifications:
    - Input: 9-18V (typical 12V nominal)
    - Output: 5V @ 3A
    - Efficiency: ~90%
    """
    buck_converter(vin_12v, vout_5v, gnd, output_voltage="5V", max_current="3A")


# Design notes and calculations
"""
Buck Converter Design Notes:

1. **Basic Operation:**
   - High-side switch turns ON: Current flows through inductor to output
   - High-side switch turns OFF: Inductor current freewheels through low-side switch
   - Inductor smooths current, capacitors filter voltage
   - Duty cycle D = Vout / Vin (ideal case)

2. **Component Selection:**

   Inductor (L):
   - Higher L = less ripple current, but slower transient response
   - Lower L = faster response, but more ripple
   - Typical: 10uH-47uH for most applications
   - Current rating: 1.2-1.5× max load current
   - DCR (DC resistance): <50mΩ for efficiency

   Input Capacitor (Cin):
   - Handles input ripple current
   - Low ESR ceramic (X7R or X5R)
   - Typical: 10-47uF per amp of output current
   - Voltage rating: >1.5× max input voltage

   Output Capacitor (Cout):
   - Filters output voltage ripple
   - Low ESR critical for low ripple
   - Typical: 22-100uF total (use multiple caps in parallel)
   - Voltage rating: >1.5× output voltage

   Bootstrap Capacitor:
   - 100nF ceramic, 16V+ rating
   - Provides gate drive for high-side MOSFET

3. **PCB Layout (CRITICAL):**
   - Minimize high-frequency current loops
   - Keep SW node traces short and thick
   - Place input cap close to VIN/GND pins
   - Place bootstrap cap close to BOOT/SW pins
   - Use ground plane for PGND and GND
   - Keep feedback traces away from SW node

   Critical loop 1: Input cap → IC → SW node → low-side switch → input cap
   Critical loop 2: Bootstrap cap → high-side switch → SW node → bootstrap cap

4. **Thermal Management:**
   - Power dissipation = (Vin - Vout) × Iout × (1 - efficiency)
   - Example: 12V→5V @ 3A, 90% eff: ~2W dissipation
   - Use thermal vias under IC power pad
   - Copper pour for heat spreading
   - Check junction temperature under max load

5. **Feedback Resistor Calculation:**
   Vout = Vref × (1 + R1/R2)

   Example for TPS54331 (Vref = 0.8V):
   - For 3.3V: R1/R2 = (3.3/0.8) - 1 = 3.125
     Choose R2 = 10kΩ, R1 = 31.6kΩ
   - For 5V: R1/R2 = (5/0.8) - 1 = 5.25
     Choose R2 = 10kΩ, R1 = 52.3kΩ

   Use 1% tolerance resistors for accuracy.

6. **Efficiency Optimization:**
   - Choose IC with low Rds(on) MOSFETs
   - Minimize inductor DCR
   - Use low ESR capacitors
   - Optimize switching frequency (higher = smaller L, lower = higher efficiency)

7. **Output Ripple:**
   Vripple ≈ (Vout × (1 - D)) / (8 × L × C × f²)
   where D = duty cycle, L = inductance, C = capacitance, f = frequency

8. **Inductor Current:**
   Iavg = Iout
   Ipeak = Iout + ΔIL/2
   where ΔIL = (Vout × (1 - D)) / (L × f)

9. **Common Issues:**
   - High output ripple: Increase output capacitance or switching frequency
   - Thermal shutdown: Improve cooling or reduce load current
   - Unstable output: Check feedback network, add compensation if needed
   - EMI problems: Improve layout, add input filtering, shield inductor

10. **Protection Features:**
    - Over-current protection (cycle-by-cycle current limiting)
    - Thermal shutdown (prevents damage from overheating)
    - Under-voltage lockout (UVLO) (prevents startup at low input voltage)
    - Soft-start (prevents inrush current at startup)

11. **Design Checklist:**
    □ Input voltage range covers application
    □ Output current rating sufficient (with margin)
    □ Inductor saturation current > peak inductor current
    □ Capacitors rated for ripple current
    □ PCB layout follows best practices
    □ Thermal analysis completed
    □ Enable/shutdown control considered
    □ EMI filtering if needed
"""
