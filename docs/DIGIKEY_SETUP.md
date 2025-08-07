# DigiKey API Setup Guide

This guide will help you set up DigiKey API access for circuit-synth.

## Prerequisites

Before you can use the DigiKey integration, you need to obtain API credentials from DigiKey.

## Step 1: Register for a DigiKey Developer Account

1. Go to [DigiKey Developer Portal](https://developer.digikey.com/)
2. Click "Sign Up" and create a developer account
3. Verify your email address

## Step 2: Create an Application

1. Log in to the [DigiKey Developer Portal](https://developer.digikey.com/)
2. Navigate to "My Apps" in your dashboard
3. Click "Create New App"
4. Fill in the application details:
   - **App Name**: Choose a name (e.g., "circuit-synth")
   - **Description**: Brief description of your use case
   - **OAuth Callback URL**: Set to `https://localhost:8139/digikey_callback`
   - **App Type**: Select "Production" for real data or "Sandbox" for testing
5. Accept the terms and conditions
6. Click "Create App"

## Step 3: Get Your Credentials

After creating the app, you'll receive:
- **Client ID**: A unique identifier for your application
- **Client Secret**: A secret key for authentication

⚠️ **Important**: Keep your Client Secret secure and never commit it to version control!

## Step 4: Configure circuit-synth

circuit-synth provides multiple secure methods to store your DigiKey API credentials. Choose the method that best fits your workflow:

### Option A: Interactive Setup (Recommended for First-Time Users)

Run the configuration wizard:

```bash
# Using circuit-synth CLI
python -m circuit_synth.manufacturing.digikey.config_manager

# Or if circuit-synth is installed globally
circuit-synth configure-digikey
```

This will:
1. Prompt for your Client ID and Secret
2. Ask if you want to use sandbox mode
3. Save credentials securely to `~/.circuit_synth/digikey_config.json`
4. Set proper file permissions (owner read/write only)

### Option B: Configuration File (Recommended for Most Users)

Create a configuration file at `~/.circuit_synth/digikey_config.json`:

```json
{
  "client_id": "your_client_id_here",
  "client_secret": "your_client_secret_here",
  "sandbox_mode": false
}
```

Set secure permissions:
```bash
chmod 600 ~/.circuit_synth/digikey_config.json
```

### Option C: Environment Variables (Good for CI/CD)

Set environment variables:

```bash
export DIGIKEY_CLIENT_ID="your_client_id_here"
export DIGIKEY_CLIENT_SECRET="your_client_secret_here"
export DIGIKEY_CLIENT_SANDBOX="False"  # Set to "True" for sandbox mode
export DIGIKEY_STORAGE_PATH="~/.circuit_synth/digikey_cache"  # Optional
```

Add to your shell configuration (`~/.bashrc`, `~/.zshrc`) for persistence.

### Option D: Project-Specific .env File

Install python-dotenv:
```bash
pip install python-dotenv
```

Create `.env` in your project root:
```env
DIGIKEY_CLIENT_ID=your_client_id_here
DIGIKEY_CLIENT_SECRET=your_client_secret_here
DIGIKEY_CLIENT_SANDBOX=False
```

Add to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

The credentials will be loaded automatically when using circuit-synth.

### Option E: Programmatic Configuration

For advanced use cases, configure directly in code:

```python
from circuit_synth.manufacturing.digikey import DigiKeyConfig, DigiKeyAPIClient

config = DigiKeyConfig(
    client_id="your_client_id_here",
    client_secret="your_client_secret_here",
    sandbox_mode=False,
)

client = DigiKeyAPIClient(config)
```

### Configuration Precedence

When multiple configuration sources exist, circuit-synth uses this precedence (highest to lowest):

1. Direct parameters in code
2. Environment variables
3. User config file (`~/.circuit_synth/digikey_config.json`)
4. Project .env file

This allows you to override settings without modifying files.

## Step 5: Test Your Setup

### Quick Test

Run the built-in connection test:

```bash
python -m circuit_synth.manufacturing.digikey.test_connection
```

This will:
- Check all configuration sources
- Verify API credentials
- Test OAuth authentication
- Perform a sample search
- Display cache statistics

### Manual Test

Or test manually with this script:

```python
from circuit_synth.manufacturing.digikey import search_digikey_components

# Search for a common component
results = search_digikey_components("1N4148", max_results=3)

if results:
    print("✅ DigiKey API is working!")
    for comp in results:
        print(f"  - {comp['manufacturer_part']}: ${comp['price']:.2f}")
else:
    print("❌ No results. Check your credentials and network connection.")
```

## Usage Examples

### Quick Component Search

```python
from circuit_synth.manufacturing.digikey import search_digikey_components

# Find STM32 microcontrollers
stm32_parts = search_digikey_components("STM32F407", max_results=10)

for part in stm32_parts:
    print(f"{part['manufacturer_part']} - Stock: {part['stock']}, Price: ${part['price']}")
```

### Detailed Component Information

```python
from circuit_synth.manufacturing.digikey import DigiKeyComponentSearch

searcher = DigiKeyComponentSearch()

# Search with filters
components = searcher.search_components(
    keyword="100nF capacitor",
    max_results=5,
    in_stock_only=True
)

for comp in components:
    print(f"{comp.manufacturer_part_number}")
    print(f"  Manufacturer: {comp.manufacturer}")
    print(f"  Stock: {comp.quantity_available}")
    print(f"  Price: ${comp.unit_price:.3f}")
    print(f"  Score: {comp.manufacturability_score:.1f}/100")
```

### Get Specific Part Details

```python
from circuit_synth.manufacturing.digikey import DigiKeyComponentSearch

searcher = DigiKeyComponentSearch()

# Get details for a specific DigiKey part number
component = searcher.get_component_details("296-1234-ND")

if component:
    print(f"Part: {component.manufacturer_part_number}")
    print(f"Description: {component.description}")
    print(f"Datasheet: {component.datasheet_url}")
    
    # Show price breaks
    for price_break in component.price_breaks:
        qty = price_break['quantity']
        price = price_break['unit_price']
        print(f"  {qty}+ units: ${price:.3f} each")
```

## API Limits

DigiKey API has the following limits:
- **Rate Limit**: 1000 requests per 5-minute window
- **Token Expiry**: Access tokens expire after 30 minutes
- **Caching**: circuit-synth automatically caches responses for 1 hour to minimize API calls

## Troubleshooting

### Common Issues

1. **"DigiKey API credentials not configured"**
   - Ensure environment variables are set correctly
   - Check that credentials are not empty strings

2. **"Failed to obtain access token"**
   - Verify your Client ID and Client Secret are correct
   - Check your network connection
   - Ensure you're using the correct mode (sandbox vs production)

3. **"No results found"**
   - Try a more generic search term
   - Check if sandbox mode is enabled (sandbox has limited data)
   - Verify the component exists on DigiKey's website

### Debug Mode

Enable debug logging to see detailed API interactions:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your DigiKey searches
```

## Security Best Practices

1. **Never commit credentials**: Add `.env` to `.gitignore`
2. **Use environment variables**: Keep credentials out of code
3. **Rotate secrets regularly**: Update your Client Secret periodically
4. **Use sandbox for testing**: Don't use production API for development
5. **Monitor usage**: Check your API usage on the DigiKey developer portal

## Support

- **DigiKey API Documentation**: https://developer.digikey.com/documentation
- **DigiKey Support**: https://developer.digikey.com/support
- **circuit-synth Issues**: https://github.com/circuit-synth/circuit-synth/issues