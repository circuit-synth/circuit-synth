#!/usr/bin/env python3
"""
DigiKey Integration Example for Circuit-Synth

This example demonstrates how to use the DigiKey integration to:
1. Search for components
2. Get detailed component information
3. Find alternatives for a component
4. Generate circuit-synth code with DigiKey parts

Before running this example, make sure you have:
1. Registered for a DigiKey developer account
2. Created an application and obtained credentials
3. Set up environment variables (see docs/DIGIKEY_SETUP.md)
"""

import logging
import os
from pathlib import Path

# Check if credentials are configured
if not os.environ.get("DIGIKEY_CLIENT_ID"):
    print("⚠️  DigiKey credentials not configured!")
    print("Please follow the setup guide in docs/DIGIKEY_SETUP.md")
    print("\nQuick setup:")
    print("1. Go to https://developer.digikey.com/")
    print("2. Create an app and get your Client ID and Secret")
    print("3. Set environment variables:")
    print("   export DIGIKEY_CLIENT_ID='your_client_id'")
    print("   export DIGIKEY_CLIENT_SECRET='your_client_secret'")
    exit(1)

from circuit_synth import Circuit, Component, Net
from circuit_synth.manufacturing.digikey import (
    DigiKeyComponentSearch,
    search_digikey_components,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)


def example_1_quick_search():
    """Example 1: Quick component search."""
    print("\n" + "="*60)
    print("Example 1: Quick Component Search")
    print("="*60)
    
    # Search for common components
    print("\nSearching for 100nF capacitors...")
    capacitors = search_digikey_components(
        "100nF 0603 capacitor",
        max_results=5,
        in_stock_only=True
    )
    
    if capacitors:
        print(f"\nFound {len(capacitors)} capacitors:")
        for cap in capacitors:
            print(f"\n  {cap['manufacturer_part']} by {cap['manufacturer']}")
            print(f"    Stock: {cap['stock']:,} units")
            print(f"    Price: ${cap['price']:.4f}")
            print(f"    Min Order: {cap['min_qty']} units")
            print(f"    Score: {cap['score']:.1f}/100")
    else:
        print("No capacitors found. Check your connection and credentials.")


def example_2_detailed_search():
    """Example 2: Detailed component search with filtering."""
    print("\n" + "="*60)
    print("Example 2: Detailed Component Search")
    print("="*60)
    
    searcher = DigiKeyComponentSearch()
    
    # Search for STM32 microcontrollers
    print("\nSearching for STM32F4 microcontrollers...")
    stm32_parts = searcher.search_components(
        keyword="STM32F407",
        max_results=5,
        in_stock_only=True
    )
    
    if stm32_parts:
        print(f"\nFound {len(stm32_parts)} STM32 parts:")
        
        for mcu in stm32_parts:
            print(f"\n  {mcu.manufacturer_part_number}")
            print(f"    Description: {mcu.description[:60]}...")
            print(f"    Package: {mcu.parameters.get('Package / Case', 'Unknown')}")
            print(f"    Stock: {mcu.quantity_available:,} units")
            print(f"    Price: ${mcu.unit_price:.2f}")
            
            # Show price breaks
            if mcu.price_breaks:
                print("    Price Breaks:")
                for pb in mcu.price_breaks[:3]:  # Show first 3 price breaks
                    qty = pb['quantity']
                    price = pb['unit_price']
                    print(f"      {qty:4}+ units: ${price:.3f} each")
    else:
        print("No STM32 parts found.")


def example_3_find_alternatives():
    """Example 3: Find alternative components."""
    print("\n" + "="*60)
    print("Example 3: Finding Alternative Components")
    print("="*60)
    
    searcher = DigiKeyComponentSearch()
    
    # First, find a reference component
    print("\nFinding a reference resistor...")
    resistors = searcher.search_components(
        keyword="10k 0603 resistor",
        max_results=1,
        in_stock_only=True
    )
    
    if resistors:
        reference = resistors[0]
        print(f"\nReference component: {reference.manufacturer_part_number}")
        print(f"  Manufacturer: {reference.manufacturer}")
        print(f"  Price: ${reference.unit_price:.4f}")
        
        # Find alternatives
        print("\nSearching for alternatives...")
        alternatives = searcher.find_alternatives(
            reference_component=reference,
            max_results=5
        )
        
        if alternatives:
            print(f"\nFound {len(alternatives)} alternatives:")
            for alt in alternatives:
                print(f"\n  {alt.manufacturer_part_number} by {alt.manufacturer}")
                print(f"    Stock: {alt.quantity_available:,}")
                print(f"    Price: ${alt.unit_price:.4f}")
                print(f"    Score: {alt.manufacturability_score:.1f}/100")
        else:
            print("No alternatives found.")
    else:
        print("Could not find reference resistor.")


def example_4_circuit_with_digikey_parts():
    """Example 4: Create a circuit using DigiKey components."""
    print("\n" + "="*60)
    print("Example 4: Circuit Design with DigiKey Components")
    print("="*60)
    
    # Search for specific components
    print("\nSearching for components to build a voltage divider...")
    
    # Find resistors
    resistors = search_digikey_components("10k 0603 resistor", max_results=1)
    
    if resistors:
        r1_part = resistors[0]
        print(f"\nSelected R1: {r1_part['manufacturer_part']}")
        print(f"  DigiKey PN: {r1_part['digikey_part']}")
        print(f"  Price: ${r1_part['price']:.4f}")
        
        # Create circuit with DigiKey part information
        circuit = Circuit()
        
        # Create components with DigiKey part numbers as properties
        r1 = Component(
            symbol="Device:R",
            ref="R1",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            properties={
                "DigiKey_PN": r1_part['digikey_part'],
                "Manufacturer": r1_part['manufacturer'],
                "MPN": r1_part['manufacturer_part'],
                "Unit_Price": str(r1_part['price']),
            }
        )
        
        r2 = Component(
            symbol="Device:R",
            ref="R2",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            properties={
                "DigiKey_PN": r1_part['digikey_part'],
                "Manufacturer": r1_part['manufacturer'],
                "MPN": r1_part['manufacturer_part'],
                "Unit_Price": str(r1_part['price']),
            }
        )
        
        # Create nets
        vin = Net("VIN")
        vout = Net("VOUT")
        gnd = Net("GND")
        
        # Connect components
        r1[1] += vin
        r1[2] += vout
        r2[1] += vout
        r2[2] += gnd
        
        print("\n✅ Created voltage divider circuit with DigiKey components!")
        print("\nCircuit BOM:")
        print(f"  R1: {r1_part['manufacturer_part']} - ${r1_part['price']:.4f}")
        print(f"  R2: {r1_part['manufacturer_part']} - ${r1_part['price']:.4f}")
        print(f"  Total: ${2 * r1_part['price']:.4f}")
        
        return circuit
    else:
        print("Could not find resistors on DigiKey.")
        return None


def example_5_cache_management():
    """Example 5: Cache management."""
    print("\n" + "="*60)
    print("Example 5: Cache Management")
    print("="*60)
    
    from circuit_synth.manufacturing.digikey import get_digikey_cache
    
    cache = get_digikey_cache()
    
    # Get cache statistics
    stats = cache.get_cache_stats()
    
    print("\nCache Statistics:")
    print(f"  Search cache: {stats['search_cache']['valid_files']} valid, "
          f"{stats['search_cache']['expired_files']} expired")
    print(f"  Product cache: {stats['product_cache']['valid_files']} valid, "
          f"{stats['product_cache']['expired_files']} expired")
    print(f"  Total size: {stats['total_size_mb']:.2f} MB")
    print(f"  TTL: {stats['ttl_seconds']} seconds")
    
    # Example: Clear expired cache entries
    # cache.clear_cache("search")  # Clear search cache
    # cache.clear_cache("product")  # Clear product cache
    # cache.clear_cache()  # Clear all cache


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("DigiKey Integration Examples for Circuit-Synth")
    print("="*60)
    
    try:
        # Run examples
        example_1_quick_search()
        example_2_detailed_search()
        example_3_find_alternatives()
        example_4_circuit_with_digikey_parts()
        example_5_cache_management()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify your DigiKey credentials are correct")
        print("3. Try setting DIGIKEY_CLIENT_SANDBOX=True for testing")
        print("4. Enable debug logging for more details")


if __name__ == "__main__":
    main()