#!/usr/bin/env python3
"""
LiPo/Li-ion Battery Charger Circuit
Safe charging circuit for single-cell lithium batteries with USB-C input
"""

from circuit_synth import *

@circuit(name="LiPo_Battery_Charger")
def lipo_charger(usb_vbus, gnd, battery_plus, battery_minus, charge_status_led):
    """
    Single-cell Li-ion/LiPo battery charger with USB input

    Key features:
    - Constant Current / Constant Voltage (CC/CV) charging
    - 4.2V charge termination voltage (standard for Li-ion/LiPo)
    - Automatic charge termination
    - Status LED indication
    - Thermal regulation
    - Over-temperature protection

    Safety features:
    - Charge current limiting
    - Over-voltage protection (4.2V regulation)
    - Under-voltage lockout
    - Thermal shutdown

    Args:
        usb_vbus: USB power input (5V from USB-C or micro-USB)
        gnd: Ground reference
        battery_plus: Positive battery terminal
        battery_minus: Negative battery terminal (typically connected to GND)
        charge_status_led: LED cathode for charge indication
                          (LED on = charging, LED off = charged/no battery)

    Common charging ICs:
    - MCP73831: 500mA max, SOT-23-5, very popular
    - TP4056: 1A max, SOP-8, cheap and common
    - BQ24040: 500mA max, VSON-10, TI quality
    """

    # LiPo charging IC (MCP73831 as reference)
    # Pin configuration: 1=STAT, 2=VSS/GND, 3=VBAT, 4=VDD, 5=PROG
    charger_ic = Component(
        symbol="Battery_Management:MCP73831-2-OT",  # 4.2V version
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )

    # Charge current programming resistor
    # Charge current (mA) = 1000 / R_prog (kΩ)
    # For 500mA: R_prog = 2kΩ
    # For 100mA: R_prog = 10kΩ
    # For 1A: R_prog = 1kΩ
    r_prog = Component(
        symbol="Device:R",
        ref="R",
        value="2k",  # 500mA charge current
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Status LED (indicates charging state)
    led_status = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric"
    )

    # LED current limiting resistor
    led_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="470",  # ~10mA LED current at 5V
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Input capacitor (on USB side)
    cap_in = Component(
        symbol="Device:C",
        ref="C",
        value="4.7uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Output capacitor (on battery side)
    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="4.7uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connections
    # Power input from USB
    charger_ic["VDD"] += usb_vbus
    charger_ic["VSS"] += gnd
    cap_in[1] += usb_vbus
    cap_in[2] += gnd

    # Battery connection
    charger_ic["VBAT"] += battery_plus
    cap_out[1] += battery_plus
    cap_out[2] += battery_minus
    battery_minus += gnd  # Battery negative to ground

    # Charge current programming
    charger_ic["PROG"] += r_prog[1]
    r_prog[2] += gnd

    # Status LED
    charger_ic["STAT"] += led_resistor[1]
    led_resistor[2] += led_status["A"]  # LED anode
    led_status["K"] += charge_status_led  # LED cathode (active low output)


@circuit(name="LiPo_Charger_with_Load_Sharing")
def lipo_charger_with_load(usb_vbus, gnd, battery_plus, system_vout, charge_led):
    """
    LiPo charger with load sharing capability

    Features:
    - Charges battery while powering the system
    - Automatic power path management
    - USB power prioritized over battery
    - Prevents battery drain during charging

    Use case:
    - Devices that run while charging (e.g., handheld devices)
    - USB power runs system, excess charges battery
    - Battery powers system when USB unplugged
    """

    # Load sharing can be implemented with:
    # 1. Diode OR-ing (simple but has voltage drop)
    # 2. Ideal diode IC (better efficiency)
    # 3. Integrated power path IC (BQ24075, MCP73871)

    # Using simple diode OR-ing for this example
    # Schottky diodes for low forward voltage drop

    # Battery charging circuit
    lipo_charger(usb_vbus, gnd, battery_plus, gnd, charge_led)

    # Diode from USB to system (USB powers system when present)
    diode_usb = Component(
        symbol="Device:D_Schottky",
        ref="D",
        footprint="Diode_SMD:D_SOD-323"
    )

    # Diode from battery to system (battery powers system when USB absent)
    diode_bat = Component(
        symbol="Device:D_Schottky",
        ref="D",
        footprint="Diode_SMD:D_SOD-323"
    )

    # System output capacitor
    cap_sys = Component(
        symbol="Device:C",
        ref="C",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )

    # OR-ing diodes
    diode_usb["A"] += usb_vbus
    diode_usb["K"] += system_vout
    diode_bat["A"] += battery_plus
    diode_bat["K"] += system_vout
    cap_sys[1] += system_vout
    cap_sys[2] += gnd


# Design notes and safety considerations
"""
LiPo/Li-ion Battery Charger Design Notes:

1. **Safety Critical:**
   - Lithium batteries can be DANGEROUS if charged improperly
   - Over-voltage = fire/explosion risk
   - Always use dedicated charging IC (NEVER charge with simple regulator)
   - Temperature monitoring highly recommended

2. **Charge Profile (CC/CV):**
   Phase 1 - Constant Current (CC):
   - Charge at programmed current (e.g., 500mA)
   - Until battery reaches 4.2V

   Phase 2 - Constant Voltage (CV):
   - Hold voltage at 4.2V
   - Current tapers down
   - Terminate when current < C/10 (e.g., 50mA for 500mA rated)

3. **Charge Current Selection:**
   - Safe rate: C/2 (500mA for 1000mAh battery)
   - Fast charge: 1C (1A for 1000mAh battery)
   - Slow/safe: C/10 (100mA for 1000mAh battery)
   - Higher current = faster charge but more heat and stress

4. **Input Protection:**
   - Add reverse polarity protection on USB input
   - TVS diode for ESD protection
   - Fuse or PTC for overcurrent protection

5. **Battery Protection:**
   - Use batteries with built-in protection PCB
   - Protection PCB provides:
     * Over-charge cutoff
     * Over-discharge cutoff
     * Short-circuit protection
     * Over-current protection

6. **Thermal Considerations:**
   - Charger IC will get warm during charging
   - Ensure adequate copper pour for heat dissipation
   - Consider thermal pad connection to ground plane
   - Maximum ambient temperature check

7. **Status Indication:**
   - LED states:
     * ON (solid): Charging in progress
     * OFF: Charge complete or no battery detected
     * Blinking (some ICs): Battery fault condition

8. **Battery Connector:**
   - Use proper Li-Po connector (JST-PH 2.0mm common)
   - Include polarity protection (diode or IC feature)
   - Consider fused connection for safety

9. **Testing and Validation:**
   - Test with power supply (current-limited) first
   - Measure charge voltage accurately (must be 4.20V ±50mV)
   - Verify charge current regulation
   - Test thermal performance (measure IC temperature)
   - Test with actual battery in safe environment

10. **Compliance:**
    - Check local regulations for battery charging
    - UL, CE, FCC requirements for commercial products
    - Consider battery shipping restrictions

11. **Common IC Comparison:**
    MCP73831:
    - Very popular, easy to use
    - 500mA max charge current
    - SOT-23-5 package
    - Status output (open-drain)

    TP4056:
    - Cheap and widely available
    - 1A max charge current
    - SOP-8 package
    - LED drivers built-in (red/green)

    BQ24040:
    - TI quality and reliability
    - 500mA max charge current
    - Programmable charge voltage
    - Better thermal regulation

WARNING: Always follow manufacturer datasheets and safety guidelines
         when designing battery charging circuits!
"""
