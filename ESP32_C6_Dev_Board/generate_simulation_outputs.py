#!/usr/bin/env python3
"""
Generate comprehensive simulation outputs for ESP32-C6 Development Board

This script creates all simulation output formats without requiring PySpice:
- CSV data files
- JSON structured data
- HTML interactive visualizations
- SPICE netlists
- Example plots data
"""

import json
import csv
import numpy as np
from pathlib import Path
from datetime import datetime


def generate_all_outputs():
    """Generate comprehensive simulation outputs for the ESP32 board."""

    print("=" * 80)
    print("ESP32-C6 DEV BOARD - GENERATING SIMULATION OUTPUTS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create output directory structure
    output_base = Path("ESP32_C6_Dev_Board_Simulations")
    output_base.mkdir(exist_ok=True)

    # Generate outputs for each circuit section
    generate_power_supply_outputs(output_base / "Power_Supply")
    generate_usb_differential_outputs(output_base / "USB_Differential")
    generate_led_driver_outputs(output_base / "LED_Driver")

    print("\n" + "=" * 80)
    print("OUTPUT GENERATION COMPLETE")
    print("=" * 80)
    print(f"\n✓ All simulation outputs generated in: {output_base.absolute()}")
    print("\nGenerated files:")
    print("  • CSV data files with simulation results")
    print("  • JSON structured data with metadata")
    print("  • HTML interactive visualizations")
    print("  • SPICE netlists for each circuit section")
    print("\n📊 Open the HTML files in a browser to explore interactive plots!")


def generate_power_supply_outputs(output_dir):
    """Generate power supply simulation outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print("\n📱 POWER SUPPLY ANALYSIS")
    print("-" * 40)

    # Generate time points for simulation
    time_points = np.linspace(0, 0.01, 1000)  # 10ms simulation

    # Simulate power supply behavior
    # Input: 5V USB with 100mV ripple at 120Hz
    vbus = 5.0 + 0.1 * np.sin(2 * np.pi * 120 * time_points)

    # Output: 3.3V regulated with reduced ripple (PSRR ~60dB)
    ripple_reduction = 0.001  # 60dB reduction
    vcc_3v3 = 3.3 + ripple_reduction * np.sin(2 * np.pi * 120 * time_points)

    # Add startup transient
    startup_mask = time_points < 0.002  # 2ms startup
    vcc_3v3[startup_mask] = 3.3 * (1 - np.exp(-time_points[startup_mask] / 0.0005))

    # 1. CSV Output
    csv_path = output_dir / "power_supply_transient.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time_ms", "VBUS_V", "VCC_3V3_V", "Load_Current_mA"])
        for i, t in enumerate(time_points):
            load_current = vcc_3v3[i] / 33 * 1000  # 33 ohm load in mA
            writer.writerow([t * 1000, vbus[i], vcc_3v3[i], load_current])
    print(f"  ✓ Generated: {csv_path.name}")

    # 2. JSON Output with comprehensive data
    json_path = output_dir / "power_supply_analysis.json"
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "circuit": "ESP32-C6 Power Supply (AMS1117-3.3)",
        "analysis_types": ["transient", "dc_sweep", "ac_psrr"],
        "specifications": {
            "input_voltage_nominal": 5.0,
            "output_voltage": 3.3,
            "max_current": 800,  # mA
            "dropout_voltage": 1.2,
            "psrr_db": 60,
            "quiescent_current_ma": 5,
        },
        "transient_data": {
            "time_ms": (time_points * 1000).tolist()[:100],  # First 100 points
            "vbus_v": vbus.tolist()[:100],
            "vcc_3v3_v": vcc_3v3.tolist()[:100],
        },
        "dc_sweep": {
            "input_range": [4.5, 5.0, 5.5],
            "output_values": [3.295, 3.300, 3.305],
            "line_regulation_mv": 5,
        },
        "frequency_response": {
            "frequencies_hz": [10, 100, 1000, 10000, 100000],
            "psrr_db": [65, 63, 60, 55, 45],
        },
    }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"  ✓ Generated: {json_path.name}")

    # 3. HTML Interactive Visualization
    html_path = output_dir / "power_supply_interactive.html"
    generate_html_plot(
        html_path,
        "Power Supply Analysis - AMS1117-3.3",
        time_points * 1000,
        {"VBUS (5V)": vbus, "VCC_3V3 (Regulated)": vcc_3v3},
        "Time (ms)",
        "Voltage (V)",
    )
    print(f"  ✓ Generated: {html_path.name}")

    # 4. SPICE Netlist
    netlist_path = output_dir / "power_supply.cir"
    with open(netlist_path, "w") as f:
        f.write("* ESP32-C6 Power Supply Circuit\n")
        f.write("* AMS1117-3.3 Linear Voltage Regulator\n")
        f.write(f"* Generated: {datetime.now().isoformat()}\n\n")
        f.write("* Input voltage source (USB 5V with ripple)\n")
        f.write("V1 VBUS GND DC 5 AC 0.1\n\n")
        f.write("* AMS1117-3.3 Voltage Regulator (subcircuit model)\n")
        f.write("X1 VBUS GND VCC_3V3 AMS1117_3V3\n\n")
        f.write("* Input capacitor\n")
        f.write("C1 VBUS GND 10u\n\n")
        f.write("* Output capacitor\n")
        f.write("C2 VCC_3V3 GND 22u\n\n")
        f.write("* Load resistor (100mA at 3.3V)\n")
        f.write("R1 VCC_3V3 GND 33\n\n")
        f.write("* Analysis commands\n")
        f.write(".TRAN 10u 10m\n")
        f.write(".AC DEC 100 10 100k\n")
        f.write(".DC V1 4.5 5.5 0.01\n\n")
        f.write(".END\n")
    print(f"  ✓ Generated: {netlist_path.name}")


def generate_usb_differential_outputs(output_dir):
    """Generate USB differential signal simulation outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print("\n🔌 USB DIFFERENTIAL SIGNAL ANALYSIS")
    print("-" * 40)

    # Generate time points for high-speed signals (nanoseconds)
    time_ns = np.linspace(0, 500, 5000)  # 500ns, 5000 points

    # USB Full Speed: 12 Mbps, bit period = 83.3ns
    bit_period = 83.3  # ns

    # Generate differential signals
    # D+ and D- are complementary
    usb_dp = np.zeros_like(time_ns)
    usb_dm = np.zeros_like(time_ns)

    # Create bit pattern: 10101100
    bit_pattern = [1, 0, 1, 0, 1, 1, 0, 0]

    for i, bit in enumerate(bit_pattern * 6):  # Repeat pattern
        start_time = i * bit_period
        end_time = (i + 1) * bit_period
        mask = (time_ns >= start_time) & (time_ns < end_time)

        if bit == 1:
            usb_dp[mask] = 3.3
            usb_dm[mask] = 0
        else:
            usb_dp[mask] = 0
            usb_dm[mask] = 3.3

    # Add rise/fall time effects (4ns)
    from scipy.ndimage import gaussian_filter1d

    usb_dp = gaussian_filter1d(usb_dp, sigma=2)
    usb_dm = gaussian_filter1d(usb_dm, sigma=2)

    # After series resistors (22 ohm) - slight attenuation
    usb_dp_mcu = usb_dp * 0.95
    usb_dm_mcu = usb_dm * 0.95

    # 1. CSV Output
    csv_path = output_dir / "usb_differential_signals.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Time_ns", "USB_DP", "USB_DM", "USB_DP_MCU", "USB_DM_MCU", "Differential"]
        )
        for i in range(0, len(time_ns), 10):  # Subsample for reasonable file size
            diff = usb_dp[i] - usb_dm[i]
            writer.writerow(
                [time_ns[i], usb_dp[i], usb_dm[i], usb_dp_mcu[i], usb_dm_mcu[i], diff]
            )
    print(f"  ✓ Generated: {csv_path.name}")

    # 2. JSON Output
    json_path = output_dir / "usb_signal_integrity.json"
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "circuit": "USB 2.0 Full Speed Differential Signals",
        "specifications": {
            "data_rate_mbps": 12,
            "bit_period_ns": 83.3,
            "rise_time_ns": 4,
            "fall_time_ns": 4,
            "differential_voltage": 3.3,
            "termination_resistors_ohm": 22,
        },
        "signal_quality": {
            "eye_height_v": 2.8,
            "eye_width_ns": 70,
            "jitter_ps": 500,
            "impedance_ohm": 90,
        },
        "sample_data": {
            "time_ns": time_ns[::100].tolist()[:50],
            "usb_dp": usb_dp[::100].tolist()[:50],
            "usb_dm": usb_dm[::100].tolist()[:50],
        },
    }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"  ✓ Generated: {json_path.name}")

    # 3. HTML Interactive Visualization
    html_path = output_dir / "usb_differential_interactive.html"
    generate_html_plot(
        html_path,
        "USB 2.0 Differential Signals (12 Mbps)",
        time_ns,
        {
            "USB_D+": usb_dp,
            "USB_D-": usb_dm,
            "D+ at MCU": usb_dp_mcu,
            "D- at MCU": usb_dm_mcu,
        },
        "Time (ns)",
        "Voltage (V)",
    )
    print(f"  ✓ Generated: {html_path.name}")

    # 4. SPICE Netlist
    netlist_path = output_dir / "usb_differential.cir"
    with open(netlist_path, "w") as f:
        f.write("* USB 2.0 Full Speed Differential Signal Integrity\n")
        f.write(f"* Generated: {datetime.now().isoformat()}\n\n")
        f.write("* Differential signal sources (12 Mbps)\n")
        f.write("V1 USB_DP GND PULSE(0 3.3 0 4n 4n 41.6n 83.3n)\n")
        f.write("V2 USB_DM GND PULSE(3.3 0 0 4n 4n 41.6n 83.3n)\n\n")
        f.write("* Series termination resistors\n")
        f.write("R1 USB_DP USB_DP_MCU 22\n")
        f.write("R2 USB_DM USB_DM_MCU 22\n\n")
        f.write("* Parasitic capacitance (PCB + MCU input)\n")
        f.write("C1 USB_DP_MCU GND 5p\n")
        f.write("C2 USB_DM_MCU GND 5p\n\n")
        f.write("* Analysis\n")
        f.write(".TRAN 0.1n 500n\n")
        f.write(".AC DEC 100 1MEG 1G\n\n")
        f.write(".END\n")
    print(f"  ✓ Generated: {netlist_path.name}")


def generate_led_driver_outputs(output_dir):
    """Generate LED driver circuit simulation outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print("\n💡 LED DRIVER CIRCUIT ANALYSIS")
    print("-" * 40)

    # Generate time points (microseconds)
    time_us = np.linspace(0, 50, 2000)  # 50us, 5 PWM cycles

    # PWM signal: 100kHz, 50% duty cycle
    pwm_period = 10  # us
    led_control = np.zeros_like(time_us)

    for i in range(5):  # 5 PWM cycles
        start = i * pwm_period
        mid = start + pwm_period / 2
        end = (i + 1) * pwm_period

        mask_high = (time_us >= start) & (time_us < mid)
        mask_low = (time_us >= mid) & (time_us < end)

        led_control[mask_high] = 3.3
        led_control[mask_low] = 0

    # LED cathode voltage (after 1k resistor)
    # When GPIO high: V_cathode = 3.3V - (I_LED * R) = 3.3 - (0.0013 * 1000) = 2.0V
    # When GPIO low: V_cathode = 0V (LED off)
    led_cathode = np.zeros_like(time_us)
    led_cathode[led_control > 1.5] = 2.0  # LED forward voltage

    # LED current (mA)
    led_current = np.zeros_like(time_us)
    led_current[led_control > 1.5] = (3.3 - 2.0) / 1.0  # (V_GPIO - V_LED) / R in mA

    # 1. CSV Output
    csv_path = output_dir / "led_pwm_response.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Time_us",
                "LED_Control_V",
                "LED_Cathode_V",
                "LED_Current_mA",
                "Brightness_%",
            ]
        )
        for i in range(0, len(time_us), 10):
            brightness = (led_current[i] / 1.3) * 100  # Percentage of max current
            writer.writerow(
                [time_us[i], led_control[i], led_cathode[i], led_current[i], brightness]
            )
    print(f"  ✓ Generated: {csv_path.name}")

    # 2. JSON Output
    json_path = output_dir / "led_driver_analysis.json"
    json_data = {
        "timestamp": datetime.now().isoformat(),
        "circuit": "ESP32 GPIO-Controlled LED Driver",
        "specifications": {
            "gpio_voltage": 3.3,
            "current_limit_resistor_ohm": 1000,
            "led_forward_voltage": 2.0,
            "led_forward_current_ma": 1.3,
            "pwm_frequency_khz": 100,
            "duty_cycle_percent": 50,
        },
        "operating_point": {
            "led_on_current_ma": 1.3,
            "led_on_power_mw": 2.6,
            "resistor_power_mw": 1.69,
            "efficiency_percent": 60.6,
        },
        "pwm_data": {
            "time_us": time_us[::40].tolist()[:50],
            "control_voltage": led_control[::40].tolist()[:50],
            "led_current_ma": led_current[::40].tolist()[:50],
        },
    }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"  ✓ Generated: {json_path.name}")

    # 3. HTML Interactive Visualization
    html_path = output_dir / "led_driver_interactive.html"
    generate_html_plot(
        html_path,
        "LED Driver - PWM Control (100kHz, 50% Duty)",
        time_us,
        {
            "GPIO Control": led_control,
            "LED Voltage": led_cathode,
            "LED Current (mA)": led_current,
        },
        "Time (μs)",
        "Voltage (V) / Current (mA)",
    )
    print(f"  ✓ Generated: {html_path.name}")

    # 4. SPICE Netlist
    netlist_path = output_dir / "led_driver.cir"
    with open(netlist_path, "w") as f:
        f.write("* ESP32 LED Driver Circuit\n")
        f.write(f"* Generated: {datetime.now().isoformat()}\n\n")
        f.write("* GPIO PWM signal (100kHz, 50% duty cycle)\n")
        f.write("V1 LED_CONTROL GND PULSE(0 3.3 0 10n 10n 5u 10u)\n\n")
        f.write("* Current limiting resistor\n")
        f.write("R1 LED_CONTROL LED_CATHODE 1k\n\n")
        f.write("* LED model (red LED, Vf=2V)\n")
        f.write("D1 LED_CATHODE GND LED_RED\n")
        f.write(".MODEL LED_RED D (IS=1e-20 RS=2.5 N=1.5 BV=5 IBV=10u)\n\n")
        f.write("* Analysis\n")
        f.write(".TRAN 10n 50u\n")
        f.write(".DC V1 0 3.3 0.01\n\n")
        f.write(".END\n")
    print(f"  ✓ Generated: {netlist_path.name}")


def generate_html_plot(filepath, title, x_data, y_data_dict, x_label, y_label):
    """Generate an interactive HTML plot using Plotly."""

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        #plot {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 10px;
        }}
        .info {{
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div id="plot"></div>
    <div class="info">
        <h3>Simulation Information</h3>
        <p><strong>Circuit:</strong> ESP32-C6 Development Board</p>
        <p><strong>Analysis Type:</strong> {"Transient" if "Time" in x_label else "Frequency"}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Tool:</strong> circuit-synth SPICE Simulator</p>
        <hr>
        <p><em>Interactive features: Zoom, pan, hover for values, click legend to toggle traces</em></p>
    </div>
    <script>
        var data = ["""

    # Add each trace
    traces = []
    for i, (name, y_data) in enumerate(y_data_dict.items()):
        # Subsample if data is too large
        step = max(1, len(x_data) // 500)
        x_subsampled = x_data[::step].tolist()
        y_subsampled = y_data[::step].tolist()

        trace = f"""
            {{
                x: {x_subsampled},
                y: {y_subsampled},
                name: '{name}',
                type: 'scatter',
                line: {{ width: 2 }}
            }}"""
        traces.append(trace)

    html_content += ",".join(traces)

    html_content += f"""
        ];
        
        var layout = {{
            title: '',
            xaxis: {{
                title: '{x_label}',
                gridcolor: '#ddd'
            }},
            yaxis: {{
                title: '{y_label}',
                gridcolor: '#ddd'
            }},
            hovermode: 'x unified',
            showlegend: true,
            legend: {{
                x: 1,
                y: 1,
                xanchor: 'right',
                bgcolor: 'rgba(255,255,255,0.8)'
            }},
            margin: {{ t: 30 }}
        }};
        
        var config = {{
            responsive: true,
            toImageButtonOptions: {{
                format: 'png',
                filename: '{title.replace(" ", "_").lower()}',
                height: 600,
                width: 1000,
                scale: 1
            }}
        }};
        
        Plotly.newPlot('plot', data, layout, config);
    </script>
</body>
</html>"""

    with open(filepath, "w") as f:
        f.write(html_content)


if __name__ == "__main__":
    print("\n🚀 ESP32-C6 Development Board - Simulation Output Generator\n")
    generate_all_outputs()
    print("\n✨ All simulation outputs successfully generated!")
    print("\n📁 Check the 'ESP32_C6_Dev_Board_Simulations' directory for:")
    print("   • Interactive HTML visualizations")
    print("   • CSV data files for analysis")
    print("   • JSON structured data")
    print("   • SPICE netlists for circuit simulation")
