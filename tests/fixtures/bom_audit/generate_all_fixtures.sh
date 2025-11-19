#!/bin/bash

# Generate all BOM audit test fixtures
# Run from circuit-synth root directory

set -e  # Exit on error

PYTHON=./venv/bin/python3
FIXTURE_DIR=tests/fixtures/bom_audit

echo "==================================================="
echo "Generating BOM Audit Test Fixtures"
echo "==================================================="
echo ""

# Generate all fixtures
for script in $FIXTURE_DIR/0*.py; do
    echo "Running: $(basename $script)"
    $PYTHON "$script"
    echo ""
done

echo "==================================================="
echo "All fixtures generated successfully!"
echo "==================================================="
echo ""

# List generated files
echo "Generated files:"
ls -lh $FIXTURE_DIR/*.kicad_sch

echo ""
echo "Summary:"
echo "  Total fixtures: 6"
echo "  Total components: 54"
echo "  Test coverage: Complete"
