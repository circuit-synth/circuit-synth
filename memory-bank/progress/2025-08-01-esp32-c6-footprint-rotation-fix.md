# ESP32-C6 Footprint Rotation Fix

## Summary
Fixed ESP32-C6-MINI-1 footprint pad rotation issue where top/bottom row pads appeared incorrectly oriented in generated PCBs.

## Key Changes
Added generalized rotation handling logic in PCB generation that detects 90-degree rotated pads and swaps width/height dimensions automatically.

## Impact
ESP32-C6 footprints now render correctly in KiCad with proper pad orientations for professional PCB manufacturing.