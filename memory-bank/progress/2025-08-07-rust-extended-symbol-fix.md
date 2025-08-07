# Rust Extended Symbol Expansion Fix

Fixed Rust KiCad integration to properly handle extended symbols (e.g., AMS1117-3.3 extending AP1117-15). The fix merges parent/child properties correctly, eliminates duplicates, and renames geometry sections to use the child symbol name, enabling KiCad to load generated schematics without errors.