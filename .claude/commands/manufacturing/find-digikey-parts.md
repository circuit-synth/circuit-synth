---
allowed-tools: Bash, Read, Write
description: Search DigiKey for components using existing circuit-synth integration
argument-hint: [component specification]
---

Search DigiKey component database using circuit-synth's integrated DigiKey functionality: **$ARGUMENTS**

## Quick Start

This command uses circuit-synth's built-in DigiKey integration with OAuth2 authentication and response caching.

### First-Time Setup (Required)
```bash
# Configure DigiKey API credentials (one-time setup)
uv run python -m circuit_synth.manufacturing.digikey.config_manager

# Test your connection
uv run python -m circuit_synth.manufacturing.digikey.test_connection
```

### Environment Variables (Alternative Setup)
```bash
export DIGIKEY_CLIENT_ID="your_client_id"
export DIGIKEY_CLIENT_SECRET="your_client_secret"
```

## Usage Examples

```bash
# Basic component search
/find-digikey-parts STM32F407VET6

# Op-amp search
/find-digikey-parts "op-amp rail-to-rail soic-8"

# Passive component search  
/find-digikey-parts "10uF ceramic capacitor 0805"

# Power component search
/find-digikey-parts "LDO regulator 3.3V 500mA"

# Microcontroller with specifications
/find-digikey-parts "ARM Cortex-M4 microcontroller LQFP"
```

## Search Implementation

This command leverages the existing DigiKey integration at:
`circuit_synth.manufacturing.digikey.component_search.search_digikey_components()`

### Core Features
- **OAuth2 Authentication**: Secure API access with token caching
- **Response Caching**: Fast repeated searches with cache management
- **Manufacturability Scoring**: Components ranked by availability, price, and stock
- **Comprehensive Parsing**: Handles DigiKey API v3 and v4 responses
- **KiCad Integration**: Ready for symbol/footprint verification

## Python Integration

Use the existing DigiKey search functions directly in Python:

```python
from circuit_synth.manufacturing.digikey import search_digikey_components
from circuit_synth.manufacturing.digikey import DigiKeyComponentSearch

# Quick search function (returns simplified results)
results = search_digikey_components(
    keyword="STM32F407VET6", 
    max_results=10,
    in_stock_only=True
)

# Advanced search with filters
searcher = DigiKeyComponentSearch()
components = searcher.search_components(
    keyword="op-amp rail-to-rail",
    filters={"Package": "SOIC-8", "Supply Voltage": "3.3V"},
    max_results=25,
    in_stock_only=True
)

# Get detailed component information
component_details = searcher.get_component_details("296-1395-1-ND")

# Find alternatives to existing component
alternatives = searcher.find_alternatives(reference_component, max_results=10)
```

## Expected Output Format

The search returns components with manufacturability scoring and complete specifications:

```python
{
    'digikey_part': '497-11767-1-ND',
    'manufacturer_part': 'STM32F407VET6TR', 
    'manufacturer': 'STMicroelectronics',
    'description': 'ARM® Cortex®-M4 STM32F4 Microcontroller IC...',
    'stock': 15847,
    'price': 8.21,
    'min_qty': 1,
    'datasheet': 'https://www.st.com/resource/en/datasheet/stm32f407ve.pdf',
    'score': 95.5  # Manufacturability score (0-100)
}
```

## Command Implementation

When you use this command, it should:

1. **Parse the search terms** from the user's input
2. **Call the existing search function**:
   ```python
   from circuit_synth.manufacturing.digikey import search_digikey_components
   results = search_digikey_components(keyword=user_input)
   ```
3. **Format and display results** with:
   - Component details (part numbers, manufacturer, description)
   - Stock levels and pricing information  
   - Manufacturability scores
   - Datasheet links
   - KiCad integration suggestions (if applicable)

## Integration Notes

- **Authentication**: Uses cached OAuth2 tokens from config setup
- **Caching**: Automatically caches API responses for performance
- **Error Handling**: Graceful fallback for API failures
- **Rate Limiting**: Built-in API rate limit management

This leverages circuit-synth's existing DigiKey integration rather than implementing new functionality.