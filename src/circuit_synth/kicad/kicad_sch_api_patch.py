"""
Monkey-patch for kicad-sch-api v0.3.0 bug.

Bug: kicad-sch-api incorrectly compares sexpdata.Symbol objects with strings,
causing (in_bom yes) and (on_board yes) to be parsed as False.

Issue: Symbol('yes') == 'yes' returns False
Fix: Convert Symbol to string before comparison

This patch should be applied before any kicad-sch-api usage.

See: KICAD_SCH_API_BUG_IN_BOM_PROPERTY.md for full bug analysis.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_PATCH_APPLIED = False


def apply_kicad_sch_api_patch():
    """
    Apply monkey-patch to fix kicad-sch-api v0.3.0 Symbol comparison bug.

    This fixes the bug where (in_bom yes) is parsed as False because
    Symbol('yes') != 'yes'.

    Safe to call multiple times - only patches once.
    """
    global _PATCH_APPLIED

    if _PATCH_APPLIED:
        return

    try:
        import kicad_sch_api.core.parser as parser_module
        import sexpdata

        # Get the original _parse_symbol method
        original_parse_symbol = parser_module.SExpressionParser._parse_symbol

        def patched_parse_symbol(self, sexp_data):
            """Patched version that correctly handles Symbol comparisons."""
            # Call original
            symbol_data = original_parse_symbol(self, sexp_data)

            if symbol_data is None:
                return None

            # Post-process to fix Symbol comparisons
            # The original code does: sub_item[1] == "yes"
            # But sub_item[1] is Symbol('yes'), not string 'yes'
            # So we need to re-parse these properties correctly

            try:
                for sub_item in sexp_data:
                    if not isinstance(sub_item, list) or len(sub_item) < 2:
                        continue

                    element_type = str(sub_item[0]) if isinstance(sub_item[0], sexpdata.Symbol) else sub_item[0]

                    if element_type == "in_bom":
                        # Fix: Convert Symbol to string before comparison
                        value = str(sub_item[1]) if isinstance(sub_item[1], sexpdata.Symbol) else sub_item[1]
                        symbol_data["in_bom"] = value == "yes"

                    elif element_type == "on_board":
                        # Fix: Convert Symbol to string before comparison
                        value = str(sub_item[1]) if isinstance(sub_item[1], sexpdata.Symbol) else sub_item[1]
                        symbol_data["on_board"] = value == "yes"

            except Exception as e:
                logger.warning(f"Error in kicad-sch-api patch: {e}")
                # Don't fail - return what we have

            return symbol_data

        # Apply the patch
        parser_module.SExpressionParser._parse_symbol = patched_parse_symbol

        _PATCH_APPLIED = True
        logger.info("Applied kicad-sch-api v0.3.0 Symbol comparison patch")

    except ImportError:
        logger.warning("kicad-sch-api not installed, patch not applied")
    except Exception as e:
        logger.error(f"Failed to apply kicad-sch-api patch: {e}")


def is_patch_applied() -> bool:
    """Check if the patch has been applied."""
    return _PATCH_APPLIED
