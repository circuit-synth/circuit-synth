#!/usr/bin/env python3
"""
STM32 Search Helper

Direct implementation for STM32 peripheral search with JLCPCB availability.
Designed to handle queries like "find STM32 with 3 SPIs available on JLCPCB".
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def detect_stm32_peripheral_query(query: str) -> Optional[Dict[str, Any]]:
    """
    Detect if query is asking for STM32 with specific peripherals.

    Args:
        query: User query string

    Returns:
        Parsed query information or None if not STM32 peripheral query
    """
    query_lower = query.lower()

    # Check for STM32 mention
    stm32_keywords = ["stm32", "st micro", "st microelectronics"]
    has_stm32 = any(kw in query_lower for kw in stm32_keywords)

    # Check for availability mention (optional for STM32 queries)
    availability_keywords = ["jlcpcb", "jlc", "available", "stock", "in stock"]
    has_availability = any(kw in query_lower for kw in availability_keywords)

    # For STM32 queries, we'll assume they want JLCPCB availability
    if not has_stm32:
        return None

    # Extract peripheral requirements (handle plurals)
    peripheral_patterns = {
        "spi": r"(\d+)\s*spis?",  # spi or spis
        "uart": r"(\d+)\s*uarts?",  # uart or uarts
        "usart": r"(\d+)\s*usarts?",  # usart or usarts
        "i2c": r"(\d+)\s*i2cs?",  # i2c or i2cs
        "usb": r"usbs?",  # usb or usbs
        "can": r"cans?",  # can or cans
        "adc": r"(\d+)\s*adcs?",  # adc or adcs
        "timer": r"(\d+)\s*timers?",  # timer or timers
        "gpio": r"(\d+)\s*gpios?",  # gpio or gpios
    }

    peripherals = {}
    for peripheral, pattern in peripheral_patterns.items():
        match = re.search(pattern, query_lower)
        if match:
            if match.groups():
                peripherals[peripheral] = int(match.group(1))
            else:
                peripherals[peripheral] = 1  # Just presence required

    if not peripherals:
        return None

    return {
        "peripherals": peripherals,
        "has_availability_requirement": True,
        "original_query": query,
    }


def find_stm32_with_peripherals(
    peripheral_requirements: Dict[str, int],
    stock_threshold: int = 20,
    max_candidates: int = 10,
) -> Optional[Dict[str, Any]]:
    """
    Find STM32 MCU matching peripheral requirements with JLCPCB availability.

    Args:
        peripheral_requirements: Dict of peripheral -> count requirements
        stock_threshold: Minimum stock level required
        max_candidates: Maximum MCUs to check for availability

    Returns:
        Best matching MCU with complete information
    """
    try:
        # Import here to avoid circular imports
        from circuit_synth.manufacturing.jlcpcb import (
            cached_jlcpcb_search,
            search_jlc_components_web,
        )

        from .component_info.microcontrollers import search_by_peripherals

        # Step 1: Search for STM32s with required peripherals
        required_peripherals = list(peripheral_requirements.keys())
        logger.info(f"Searching for STM32s with peripherals: {required_peripherals}")

        candidates = search_by_peripherals(
            required_peripherals,
            family="stm32",
            max_results=max_candidates * 2,  # Get more to filter
        )

        if not candidates:
            logger.warning("No STM32 candidates found for peripheral requirements")
            return None

        # Step 2: Filter by peripheral counts
        filtered_candidates = []
        for candidate in candidates:
            meets_requirements = True

            for peripheral, required_count in peripheral_requirements.items():
                # Count instances of this peripheral (handle UART/USART equivalence)
                peripheral_upper = peripheral.upper()

                if peripheral_upper == "UART":
                    # For UART, count both UART and USART peripherals
                    actual_count = sum(
                        1
                        for p in candidate.peripherals
                        if (p.startswith("UART") and (p == "UART" or p[4:].isdigit()))
                        or (p.startswith("USART") and (p == "USART" or p[5:].isdigit()))
                    )
                else:
                    # Standard peripheral counting
                    actual_count = sum(
                        1
                        for p in candidate.peripherals
                        if p.startswith(peripheral_upper)
                        and (
                            p == peripheral_upper
                            or p[len(peripheral_upper) :].isdigit()
                        )
                    )

                if actual_count < required_count:
                    meets_requirements = False
                    break

            if meets_requirements:
                filtered_candidates.append(candidate)

        logger.info(
            f"Found {len(filtered_candidates)} candidates matching peripheral counts"
        )

        if not filtered_candidates:
            return None

        # Step 3: Check JLCPCB availability for each candidate
        for candidate in filtered_candidates[:max_candidates]:
            try:
                # Use cached search to avoid repeated API calls
                jlc_results = cached_jlcpcb_search(
                    candidate.part_number, lambda term: search_jlc_components_web(term)
                )

                if jlc_results and len(jlc_results) > 0:
                    best_result = jlc_results[0]
                    stock = best_result.get("stock", 0)

                    if stock >= stock_threshold:
                        # Found a good match - but only if KiCad symbol exists
                        recommendation = _format_stm32_recommendation(
                            candidate, best_result, peripheral_requirements
                        )
                        if recommendation:  # Only return if KiCad symbol exists
                            return recommendation

            except Exception as e:
                logger.warning(
                    f"Error checking JLCPCB for {candidate.part_number}: {e}"
                )
                continue

        # If no candidates with good stock, don't return anything
        logger.warning(
            f"No candidates found with stock >= {stock_threshold} and valid KiCad symbols"
        )

        return None

    except Exception as e:
        logger.error(f"Error in find_stm32_with_peripherals: {e}")
        return None


def _format_stm32_recommendation(
    mcu_result,
    jlc_result: Optional[Dict[str, Any]],
    peripheral_requirements: Dict[str, int],
) -> Optional[Dict[str, Any]]:
    """Format STM32 recommendation with complete information."""

    # Check KiCad symbol availability - no fallback, either it exists or we reject
    kicad_symbol = mcu_result.kicad_symbol
    if not kicad_symbol:
        return None  # Reject if no KiCad symbol available

    # Get peripheral list for the specific requirements
    matched_peripherals = {}
    for peripheral, required_count in peripheral_requirements.items():
        peripheral_upper = peripheral.upper()

        if peripheral_upper == "UART":
            # For UART, collect both UART and USART peripherals
            matching_peripherals = [
                p
                for p in mcu_result.peripherals
                if (p.startswith("UART") and (p == "UART" or p[4:].isdigit()))
                or (p.startswith("USART") and (p == "USART" or p[5:].isdigit()))
            ]
        else:
            # Standard peripheral matching
            matching_peripherals = [
                p for p in mcu_result.peripherals if p.startswith(peripheral_upper)
            ]

        matched_peripherals[peripheral] = matching_peripherals[:required_count]

    recommendation = {
        "part_number": mcu_result.part_number,
        "description": mcu_result.description,
        "flash_size": mcu_result.flash_size,
        "ram_size": mcu_result.ram_size,
        "package": mcu_result.package,
        "pin_count": mcu_result.pin_count,
        "kicad_symbol": kicad_symbol,
        "kicad_footprint": mcu_result.kicad_footprint,
        "matched_peripherals": matched_peripherals,
        "availability": None,
    }

    if jlc_result:
        recommendation["availability"] = {
            "supplier": "JLCPCB",
            "part_number": jlc_result.get("lcsc_part", ""),
            "stock": jlc_result.get("stock", 0),
            "price": jlc_result.get("price", 0),
            "url": jlc_result.get("url", ""),
        }

    return recommendation


def handle_stm32_peripheral_query(query: str) -> Optional[str]:
    """
    Handle STM32 peripheral search query directly.

    Args:
        query: User query string

    Returns:
        Formatted response string or None if not applicable
    """
    # Detect if this is an STM32 peripheral query
    parsed_query = detect_stm32_peripheral_query(query)
    if not parsed_query:
        return None

    logger.info(f"Detected STM32 peripheral query: {parsed_query['peripherals']}")

    # Find matching STM32
    recommendation = find_stm32_with_peripherals(parsed_query["peripherals"])
    if not recommendation:
        return "❌ No STM32 MCUs found matching your peripheral requirements with sufficient JLCPCB stock."

    # Format response
    response = f"🎯 **{recommendation['part_number']}** - Perfect match found!\n\n"

    # Add availability info
    if recommendation["availability"]:
        avail = recommendation["availability"]
        response += f"📊 Stock: {avail['stock']:,} units | Price: {avail['price']} | LCSC: {avail['part_number']}\n"

    # Add peripheral info
    response += "✅ Peripherals: "
    peripheral_strs = []
    for peripheral, instances in recommendation["matched_peripherals"].items():
        peripheral_strs.append(
            f"{len(instances)} {peripheral.upper()}s: {', '.join(instances)}"
        )
    response += " | ".join(peripheral_strs) + "\n"

    # Add specs
    response += f"📦 {recommendation['package']} package | {recommendation['flash_size']}KB Flash, {recommendation['ram_size']}KB RAM\n\n"

    # Add circuit-synth code
    response += "📋 Ready Circuit-Synth Code:\n```python\n"
    var_name = recommendation["part_number"].lower().replace("-", "_")
    response += f"""{var_name} = Component(
    symbol="{recommendation['kicad_symbol']}",
    ref="U",
    footprint="{recommendation['kicad_footprint'] or 'Package_QFP:LQFP-48_7x7mm_P0.5mm'}"
)
```"""

    return response
