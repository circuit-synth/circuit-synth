# Circuit Project

**Description**: BB-8 droid controller

## Generated Files
- main.py
- power_supply.py
- mcu.py
- imu_1.py
- motor_driver.py
- leds.py
- audio.py

## Architecture
- Type: microcontroller_board
- Components: 5 main components

## Usage
```bash
# Generate KiCad project
uv run python main.py
```

## Components Selected
- mcu: ESP32-S3-MINI-1
- imu: MPU6050
- motor_driver: DRV8833
- leds: Standard_LED
- buzzer: Buzzer
- regulator: NCP1117-3.3

Generated with circuit-synth fast generator integrating with Claude Code agents.
