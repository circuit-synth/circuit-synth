# Circuit Project

**Description**: make a circuit board with stm32 with 3 spi peripherals and 1 imu on each spi

## Generated Files
- main.py
- power_supply.py
- mcu.py
- imu_1.py

## Architecture
- Type: microcontroller_board
- Components: 2 main components

## Usage
```bash
# Generate KiCad project
uv run python main.py
```

## Components Selected
- mcu: STM32F407VET6
- imu: MPU6050
- regulator: NCP1117-3.3

Generated with circuit-synth fast generator integrating with Claude Code agents.
