#!/usr/bin/env python3
"""
Boost Converter (Step-Up Switching Regulator) Circuit
Efficient voltage step-up from lower input voltage to higher output voltage
"""

from circuit_synth import *

@circuit(name="Boost_Converter_5V")
def boost_converter(vin, vout, gnd, output_voltage="5V", max_current="1A"):
    """
    Boost converter for efficient step-up voltage regulation

    Key features:
    - Steps up input voltage to higher output voltage
    - High efficiency (typically 85-92%)
    - Integrated switching MOSFET
    - Adjustable output voltage

    Common applications:
    - 3.3V/3.7V battery to 5V USB
    - 1.2V-1.5V battery to 3.3V/5V
    - LED driver (constant current boost)
    - Portable electronics power management

    Args:
        vin: Input voltage (must be lower than output)
        vout: Regulated output voltage
        gnd: Ground reference
        output_voltage: Desired output voltage ("5V", "12V", etc.)
        max_current: Maximum output current ("500mA", "1A", "2A", etc.)

    Example specs:
        Input: 2.5V-5.5V (e.g., single Li-ion cell)
        Output: 5V @ 1A
        Efficiency: ~88%
        Switching frequency: 1.2MHz

    Common boost converter ICs:
    - TPS61070: 2A switch, 1.8-5.5V in, adjustable out, SOT-23-5
    - MT3608: 4A switch, 2-24V in, adjustable out, SOT-23-6
    - LM2733: 1.6A switch, 1.6-5.5V in, 5V fixed out, SOT-23-5
    - TPS61040: 350mA, 1.8-6V in, 5V fixed out, SOT-23-5
    """

    # Boost converter IC (using TPS61070 as reference)
    # Adjustable output with external feedback divider
    boost_ic = Component(
        symbol="Regulator_Switching:TPS61070",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Input capacitor (low ESR ceramic)
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",  # X7R/X5R ceramic, 10V+
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Inductor (stores energy during switching)
    # For boost: L = (Vin × (Vout - Vin)) / (ΔIL × f × Vout)
    # Typical: 4.7uH-22uH for 1MHz switching
    inductor = Component(
        symbol="Device:L",
        ref="L",
        value="10uH",  # 2A rated, low DCR (<100mΩ)
        footprint="Inductor_SMD:L_1210_3225Metric"
    )

    # Schottky diode (rectifies inductor current)
    # Critical: Must be fast recovery, low Vf
    # Current rating: >1.5× max output current
    # Voltage rating: >1.5× max output voltage
    diode = Component(
        symbol="Device:D_Schottky",
        ref="D",
        value="SS14",  # 1A, 40V Schottky
        footprint="Diode_SMD:D_SMA"
    )

    # Output capacitor (filters output ripple)
    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",  # Low ESR, voltage rating >Vout
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )

    # Additional output capacitor for better filtering
    cap_out2 = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # Feedback resistor divider (sets output voltage)
    # Vout = Vref × (1 + R1/R2)
    # For TPS61070 (Vref = 0.5V):
    # 5V output: R1/R2 = (5/0.5) - 1 = 9
    # Choose R2 = 10kΩ, R1 = 90kΩ (or 91kΩ standard value)

    r_fb_top = Component(
        symbol="Device:R",
        ref="R",
        value="91k",  # 1% tolerance
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r_fb_bottom = Component(
        symbol="Device:R",
        ref="R",
        value="10k",  # 1% tolerance
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Enable control (optional - tie to VIN if always-on)
    r_en = Component(
        symbol="Device:R",
        ref="R",
        value="100k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connections
    # Input power
    boost_ic["VIN"] += vin
    boost_ic["GND"] += gnd
    cap_in[1] += vin
    cap_in[2] += gnd

    # Inductor connection
    boost_ic["SW"] += inductor[1]   # Switch to inductor
    inductor[2] += vin              # Inductor to input (boost topology)

    # Schottky diode (catch diode)
    diode["A"] += boost_ic["SW"]    # Anode to switch node
    diode["K"] += vout              # Cathode to output

    # Output filtering
    cap_out[1] += vout
    cap_out[2] += gnd
    cap_out2[1] += vout
    cap_out2[2] += gnd

    # Feedback network
    r_fb_top[1] += vout
    r_fb_top[2] += boost_ic["FB"]   # Feedback pin
    r_fb_bottom[1] += boost_ic["FB"]
    r_fb_bottom[2] += gnd

    # Enable control
    boost_ic["EN"] += r_en[1]
    r_en[2] += vin  # Pull-up to enable


@circuit(name="Boost_3V_to_5V_USB")
def boost_3v_to_5v_usb(battery_3v7, usb_5v_out, gnd):
    """
    Boost converter for single Li-ion battery to USB 5V

    Application: Power bank, USB charging from single cell
    Specifications:
    - Input: 2.7V-4.2V (Li-ion discharge curve)
    - Output: 5V @ 1A (USB power)
    - Efficiency: ~88%
    """
    boost_converter(battery_3v7, usb_5v_out, gnd, output_voltage="5V", max_current="1A")


# Design notes and calculations
"""
Boost Converter Design Notes:

1. **Basic Operation:**
   - Switch ON: Inductor connected to ground, stores energy
   - Switch OFF: Inductor voltage reverses, pushes current through diode to output
   - Energy stored in inductor during ON time is transferred to output during OFF time
   - Output voltage > Input voltage (boost)
   - Duty cycle D = (Vout - Vin) / Vout (ideal case)

2. **Component Selection:**

   Inductor (L):
   - Higher L = less ripple current, better efficiency at light load
   - Lower L = faster transient response, smaller size
   - Typical: 4.7uH-22uH for 1MHz switching
   - Current rating: Must handle peak inductor current
     Ipeak = Iout × (Vout/Vin) + ΔIL/2
   - DCR: <100mΩ for good efficiency

   Schottky Diode (D):
   - CRITICAL COMPONENT - affects efficiency significantly
   - Low forward voltage (Vf): <0.4V for best efficiency
   - Fast recovery: <20ns for high-frequency operation
   - Current rating: >1.5× max output current
   - Voltage rating: >1.5× max output voltage
   - Common parts: SS14 (1A, 40V), SS24 (2A, 40V)

   Input Capacitor (Cin):
   - Low ESR ceramic (X7R or X5R)
   - Handles pulsed input current
   - Typical: 10-22uF
   - Voltage rating: >1.5× max input voltage

   Output Capacitor (Cout):
   - Filters output ripple
   - Low ESR important
   - Typical: 22-47uF total
   - Voltage rating: >1.5× output voltage

3. **Key Differences from Buck Converter:**
   - Inductor connects to INPUT instead of output
   - Requires external Schottky diode (buck often has synchronous rectifier)
   - Input current is pulsed (needs good input filtering)
   - Cannot limit output current directly (current limit is on input side)

4. **PCB Layout (CRITICAL):**
   - Minimize high-frequency current loops
   - Keep SW node traces short (high dV/dt node)
   - Place diode very close to SW pin
   - Place output cap close to diode cathode
   - Input cap close to VIN/GND pins
   - Use solid ground plane

   Critical loop: SW pin → Diode → Cout → GND → IC GND
   Keep this loop SMALL and direct.

5. **Thermal Management:**
   - Power dissipation sources:
     * IC switch resistance
     * Diode forward drop (biggest contributor)
     * Inductor DCR
     * ESR in capacitors
   - Example: 3.7V→5V @ 1A, 88% eff: ~0.7W total dissipation
   - Diode gets hot: May need heatsinking for >1A
   - Use thermal vias under IC

6. **Feedback Resistor Calculation:**
   Vout = Vref × (1 + R1/R2)

   Example for TPS61070 (Vref = 0.5V):
   - For 5V: R1/R2 = (5/0.5) - 1 = 9
     Choose R2 = 10kΩ, R1 = 91kΩ
   - For 12V: R1/R2 = (12/0.5) - 1 = 23
     Choose R2 = 10kΩ, R1 = 237kΩ (use 237k or 240k)

   Use 1% tolerance resistors for accuracy.

7. **Efficiency Calculation:**
   Efficiency = Pout / Pin = (Vout × Iout) / (Vin × Iin)

   At 100% efficiency: Iin = Iout × (Vout / Vin)
   Actual efficiency: 85-92% typical

   Example: 3.7V → 5V @ 1A
   Pin (ideal) = 5W / 0.88 = 5.68W
   Iin = 5.68W / 3.7V = 1.54A

8. **Output Current Limitation:**
   - Boost converter input current = output current × (Vout/Vin)
   - As input voltage drops, input current increases
   - IC current limit is on INPUT side
   - Output current can exceed rated value if Vin drops too low
   - Add output current sensing if protection needed

9. **Input Current Ripple:**
   ΔIin = (Vout - Vin) / (L × f × (Vin / Vout))
   - Higher than buck converter
   - Needs good input filtering
   - Can cause problems with battery protection circuits

10. **Common Issues:**
    - Low efficiency: Check diode Vf, inductor DCR, layout
    - High output ripple: Increase output capacitance
    - Thermal issues: Check diode and IC temperature, improve cooling
    - Unstable output: Check feedback loop compensation
    - Won't start: Check enable pin, input voltage, inductor saturation

11. **Startup Behavior:**
    - Boost converters have "inrush" current at startup
    - Soft-start feature helps reduce inrush
    - May affect battery protection circuits
    - Consider external soft-start if needed

12. **Output Disconnect:**
    - When boost IC is disabled, output may backfeed to input through diode
    - Add disconnect switch if true shutoff needed
    - Some ICs have internal disconnect

13. **Design Checklist:**
    □ Input voltage range covers battery discharge curve
    □ Output voltage and current meet requirements
    □ Inductor saturation current > peak current
    □ Diode current and voltage ratings adequate
    □ Diode Vf as low as possible for efficiency
    □ Output capacitors rated for ripple current
    □ PCB layout minimizes high-frequency loops
    □ Thermal analysis completed (especially diode)
    □ Input filtering adequate
    □ Enable/shutdown control considered
"""
