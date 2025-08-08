# Multi-Unit Component Support Fix

Fixed Rust KiCad integration to properly handle multi-unit components (like dual op-amps LM358, TL072) by correctly extracting and renaming geometry unit suffixes. Now handles complex parent symbol names (e.g., STM32F103C_8-B_Tx) and ensures all unit sections are renamed to child symbol names.