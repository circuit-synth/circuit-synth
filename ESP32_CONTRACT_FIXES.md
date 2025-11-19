# ESP32 Contract Work - Fixes Needed

## Issues to Address

### 1. Power Symbols Placement
- **Issue**: Need power symbols placed instead of hierarchical labels
- **Status**: TODO
- **Priority**: HIGH
- **Notes**: Should default to auto-detecting and placing power symbols even if user doesn't set flag on Net. Currently requires explicit `is_power=True` or auto-detection based on common names (GND, VCC, etc.). Should scan all nets and apply power symbols more broadly.

### 2. Sheet Rectangle Grid Alignment
- **Issue**: Sheet rectangles not grid aligned
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**:

---

### 3. Sheet Filename Display
- **Issue**: Do not show sheet file on sheets, just Sheetname
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**:

### 4. No Sheet Pins for Power Nets
- **Issue**: No need for sheet pins for power nets if we have the power symbols placed
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Related to issue #1 - power symbols placement

### 5. Component Properties Showing on Sub-sheets
- **Issue**: Parts after the top level have all of the hierarchy_path, project_name, and root_uuid showing
- **Status**: TODO
- **Priority**: HIGH
- **Notes**: These properties should be hidden on sub-sheet components

### 6. Schematic Images/Pictures Support
- **Issue**: Should add pictures and graphics to schematics more often
- **Status**: TODO
- **Priority**: LOW
- **Notes**: Would be easy to implement once, learn the mechanism, and would make schematics look professional/cool. KiCad supports images in schematics.

### 7. Schematic Title Block Details
- **Issue**: Need to fill in schematic title block details: Issue Date, Revision, Title, Company
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Professional schematics should have proper title block metadata filled in

### 8. Top Sheet with Sub-sheet Index
- **Issue**: Need to add top sheet with index of sub sheets
- **Status**: TODO
- **Priority**: HIGH
- **Notes**: This is what all professionals do - top level sheet should show table of contents/index of all sub-sheets in the project

### 9. Duplicate Labels on Same Pin
- **Issue**: Multiple labels on a USB VBUS pin had to be manually deleted
- **Status**: TODO
- **Priority**: HIGH
- **Notes**: Should only place one label per pin, not multiple duplicate labels

### 10. Small Subcircuit Reference Schematics for ICs
- **Issue**: Need to make small subcircuit reference schematics for certain ICs like tscircuit does
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Create visual reference diagrams showing typical application circuits for common ICs embedded in schematics

### 11. Tiny Wire Stub from Pin to Label
- **Issue**: Should add a tiny amount of wire from pin to label to ensure they are visually connected
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Visual connection confirmation - small wire stub between pin and label makes the connection explicit and clear

### 12. Utility to Convert Hierarchical Labels to Local Labels
- **Issue**: Need a utility to convert hierarchical labels to local labels
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Conversion utility for simplifying schematics by replacing hierarchical labels with local labels where appropriate

### 13. Add X to Unused Pins
- **Issue**: Add X symbol to unused pins
- **Status**: TODO
- **Priority**: LOW
- **Notes**: Professional practice - mark unused pins with X symbol to clearly indicate they are intentionally not connected

### 14. Flattened Schematic Option
- **Issue**: Need an option for flattened schematics (no hierarchy)
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: A lot of people prefer flattened schematics for simple designs. Should add flag to generate_kicad_project() to flatten hierarchy into single sheet

### 15. Component Text Size Control
- **Issue**: Change size of component text - want refs to be small and descriptions to be small
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Need control over reference designator and value/description text sizes for cleaner schematics

### 16. GND Symbol Orientation and Routing
- **Issue**: GND always points down, even on a weird sideways pin - requires up and down horseshoe routing
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Need smart routing to handle GND symbols that must point down even when connecting to sideways/horizontal pins

### 17. Differential Pair Naming Support
- **Issue**: Don't handle differential pair naming (e.g., USB_DP/USB_DN, ETH_TX+/ETH_TX-)
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: KiCad auto-detects differential pairs by naming conventions (_P/_N, +/-, etc.). Need to ensure proper naming is preserved/generated for diff pairs

### 18. Auto-add Test Points with Labels
- **Issue**: Automatically add and place test points, and add labels by test points
- **Status**: TODO
- **Priority**: LOW
- **Notes**: Professional boards have test points on key signals for debugging/testing. Should auto-generate or have option to add test point components with proper placement and labeling

### 19. MFG# Display Instead of Value
- **Issue**: Add MFG# instead of where value is
- **Status**: TODO
- **Priority**: MEDIUM
- **Notes**: Show manufacturer part number in value field for professional schematics

---

## Additional Notes

Power symbols are automatically generated when a Net has `is_power=True` or auto-detected (e.g., "GND", "VCC").
The Net object accepts `power_symbol` parameter to specify which power symbol to use (e.g., "power:GND").

No flag exists in `generate_kicad_project()` to control power symbol placement.
Power symbol behavior is controlled at the Net level in circuit definition:
- `Net(name="GND")` - Auto-detects as power net, places power symbol
- `Net(name="GND", is_power=False)` - Explicitly prevents power symbol
- `Net(name="CUSTOM", is_power=True, power_symbol="power:+3V3")` - Explicit power symbol

## References

- KDT Hierarchical KiBot: https://github.com/nguyen-v/KDT_Hierarchical_KiBot

---

*Created: 2025-11-17*
*Branch: contract-work/esp32-board-fixes*
