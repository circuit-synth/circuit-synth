# BOM Property Management

Find and fix components missing PartNumber (or any property) in your KiCad schematics.

## Quick Start

```bash
# Find components missing PartNumber
python manage_bom_properties.py audit ~/path/to/designs --output report.csv

# Open report.csv in Excel to see what's missing
```

## Bulk Update (Optional)

```bash
# Set PartNumber for all 10k resistors (preview first)
python manage_bom_properties.py update ~/designs \
  --match "value=10k" \
  --set "PartNumber=RC0805FR-0710KL" \
  --dry-run

# Remove --dry-run to apply changes
```

## Pattern Matching

Match by any field:
- `value=10k` - exact match
- `footprint=*0805*` - wildcard
- `value=10k,lib_id=Device:R` - multiple criteria

## Commands

**Audit** - Find missing properties
```bash
manage_bom_properties.py audit <dir> --check PartNumber --output report.csv
```

**Update** - Bulk property changes
```bash
manage_bom_properties.py update <dir> --match <criteria> --set <properties> --dry-run
```

**Transform** - Copy properties
```bash
manage_bom_properties.py transform <dir> --copy "MPN->PartNumber" --only-if-empty
```

Always use `--dry-run` first to preview changes.
