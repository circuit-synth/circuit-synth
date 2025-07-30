# STM32 Peripheral Search Pattern

## Detection Rules

**Trigger Pattern**: `stm32 + peripheral count + availability`

**Examples:**
- "find stm32 mcu that has 3 spi's and is available on jlcpcb"
- "stm32 with 2 uarts available on jlc"
- "find stm32 with usb and 4 timers in stock"

**Detection Logic:**
```python
# Detect STM32 peripheral search pattern
keywords = {
    'stm32': ['stm32', 'st micro'],
    'peripherals': ['spi', 'i2c', 'uart', 'usart', 'usb', 'gpio', 'timer', 'adc', 'dac', 'can'],
    'availability': ['jlcpcb', 'jlc', 'available', 'stock', 'in stock']
}

def is_stm32_peripheral_query(text):
    text_lower = text.lower()
    has_stm32 = any(kw in text_lower for kw in keywords['stm32'])
    has_peripheral = any(kw in text_lower for kw in keywords['peripherals'])
    has_availability = any(kw in text_lower for kw in keywords['availability'])
    return has_stm32 and has_peripheral and has_availability
```

## Workflow Steps

1. **Use modm-devices search** for STM32 with peripheral requirements
2. **Filter by peripheral count** (extract numbers: "3 spi's" → 3)
3. **Check JLCPCB availability** until we find ≥20 stock
4. **Verify KiCad symbol** with fallback logic
5. **Return single best match** with complete info

## Efficiency Optimizations

- **Cache JLCPCB results** to avoid repeated API calls
- **Limit candidates** to top 5-10 from modm-devices
- **Smart symbol mapping** (STM32G431CBT6 → STM32G431CBTx)
- **Stock threshold** minimum 20 units for production viability