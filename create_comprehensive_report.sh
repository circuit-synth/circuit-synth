#!/bin/bash

# Create report directory
mkdir -p test_failure_reports_detailed

# Extract all failures
grep "^FAILED" test_results_full.txt > test_failure_reports_detailed/raw_failures.txt

# Categorize by test directory
grep "^FAILED tests/unit/" test_results_full.txt > test_failure_reports_detailed/unit_failures.txt
grep "^FAILED tests/integration/" test_results_full.txt > test_failure_reports_detailed/integration_failures.txt
grep "^FAILED tests/e2e/" test_results_full.txt > test_failure_reports_detailed/e2e_failures.txt
grep "^FAILED tests/bidirectional/" test_results_full.txt > test_failure_reports_detailed/bidirectional_failures.txt
grep "^FAILED tests/pcb_generation/" test_results_full.txt > test_failure_reports_detailed/pcb_generation_failures.txt
grep "^FAILED tests/kicad_to_python/" test_results_full.txt > test_failure_reports_detailed/kicad_to_python_failures.txt
grep "^FAILED tests/test_bidirectional_automated/" test_results_full.txt > test_failure_reports_detailed/bidirectional_automated_failures.txt

# Extract errors
grep "^ERROR" test_results_full.txt > test_failure_reports_detailed/errors.txt

# Count failures by category
echo "# Test Failure Breakdown" > test_failure_reports_detailed/BREAKDOWN.md
echo "" >> test_failure_reports_detailed/BREAKDOWN.md
echo "## By Category" >> test_failure_reports_detailed/BREAKDOWN.md
echo "" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- Unit Tests: $(wc -l < test_failure_reports_detailed/unit_failures.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- Integration Tests: $(wc -l < test_failure_reports_detailed/integration_failures.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- E2E Tests: $(wc -l < test_failure_reports_detailed/e2e_failures.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- Bidirectional Tests: $(wc -l < test_failure_reports_detailed/bidirectional_failures.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- PCB Generation Tests: $(wc -l < test_failure_reports_detailed/pcb_generation_failures.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- KiCad-to-Python Tests: $(wc -l < test_failure_reports_detailed/kicad_to_python_failures.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- Bidirectional Automated Tests: $(wc -l < test_failure_reports_detailed/bidirectional_automated_failures.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md
echo "- Errors: $(wc -l < test_failure_reports_detailed/errors.txt | tr -d ' ')" >> test_failure_reports_detailed/BREAKDOWN.md

echo ""  >> test_failure_reports_detailed/BREAKDOWN.md
echo "## Unit Test Failures (Detailed)" >> test_failure_reports_detailed/BREAKDOWN.md
echo "" >> test_failure_reports_detailed/BREAKDOWN.md
cat test_failure_reports_detailed/unit_failures.txt >> test_failure_reports_detailed/BREAKDOWN.md

echo "Done! Check test_failure_reports_detailed/"
