#!/usr/bin/env python3
"""
Quick manual test of token budget functionality
"""
import sys
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, '.')

# Test 1: Import modules
print("Test 1: Importing modules...")
try:
    from adws.adw_modules.token_budget import (
        parse_token_budget_config,
        get_monthly_token_usage,
        calculate_budget_status,
        get_budget_info
    )
    from dashboard.budget_monitor import BudgetMonitor
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Parse budget config
print("\nTest 2: Parse budget config...")
with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
    f.write('MONTHLY_TOKEN_BUDGET=2000000\n')
    env_file = Path(f.name)

try:
    config = parse_token_budget_config(env_file)
    assert config['monthly_budget'] == 2000000
    print(f"✓ Config parsed correctly: {config['monthly_budget']:,} tokens")
finally:
    env_file.unlink()

# Test 3: Calculate token usage
print("\nTest 3: Calculate token usage...")
with tempfile.TemporaryDirectory() as tmpdir:
    log_dir = Path(tmpdir)
    current_month = datetime.now().strftime('%Y-%m')
    log_file = log_dir / f'api-calls-{current_month}-01.jsonl'

    # Write test data
    with open(log_file, 'w') as f:
        f.write(json.dumps({'tokens_total': 1000}) + '\n')
        f.write(json.dumps({'tokens_total': 2500}) + '\n')
        f.write(json.dumps({'tokens_total': 500}) + '\n')

    usage = get_monthly_token_usage(log_dir)
    assert usage == 4000
    print(f"✓ Usage calculated correctly: {usage:,} tokens")

# Test 4: Calculate budget status - green
print("\nTest 4: Calculate budget status (green)...")
status = calculate_budget_status(500000, 1000000)
assert status['alert_level'] == 'green'
assert status['percentage'] == 50.0
print(f"✓ Green status: {status['percentage']}% used - {status['alert_level']}")

# Test 5: Calculate budget status - yellow
print("\nTest 5: Calculate budget status (yellow)...")
status = calculate_budget_status(800000, 1000000)
assert status['alert_level'] == 'yellow'
assert status['percentage'] == 80.0
print(f"✓ Yellow status: {status['percentage']}% used - {status['alert_level']}")

# Test 6: Calculate budget status - orange
print("\nTest 6: Calculate budget status (orange)...")
status = calculate_budget_status(920000, 1000000)
assert status['alert_level'] == 'orange'
assert status['percentage'] == 92.0
print(f"✓ Orange status: {status['percentage']}% used - {status['alert_level']}")

# Test 7: Calculate budget status - red
print("\nTest 7: Calculate budget status (red)...")
status = calculate_budget_status(980000, 1000000)
assert status['alert_level'] == 'red'
assert status['percentage'] == 98.0
print(f"✓ Red status: {status['percentage']}% used - {status['alert_level']}")

# Test 8: BudgetMonitor integration
print("\nTest 8: BudgetMonitor integration...")
with tempfile.TemporaryDirectory() as tmpdir:
    repo_root = Path(tmpdir)

    # Create .env
    env_file = repo_root / '.env'
    with open(env_file, 'w') as f:
        f.write('MONTHLY_TOKEN_BUDGET=1000000\n')

    # Create logs
    log_dir = repo_root / 'logs' / 'api'
    log_dir.mkdir(parents=True)

    current_month = datetime.now().strftime('%Y-%m')
    log_file = log_dir / f'api-calls-{current_month}-01.jsonl'
    with open(log_file, 'w') as f:
        f.write(json.dumps({'tokens_total': 750000}) + '\n')

    monitor = BudgetMonitor(repo_root=repo_root)
    status = monitor.get_budget_status()

    assert status['tokens_used'] == 750000
    assert status['monthly_budget'] == 1000000
    assert status['percentage'] == 75.0
    assert status['alert_level'] == 'yellow'
    print(f"✓ BudgetMonitor: {status['tokens_used']:,} / {status['monthly_budget']:,} tokens ({status['percentage']}%)")

# Test 9: BudgetMonitor display formatting
print("\nTest 9: BudgetMonitor display formatting...")
monitor = BudgetMonitor()
status = {
    'monthly_budget': 1000000,
    'tokens_used': 500000,
    'remaining': 500000,
    'percentage': 50.0,
    'alert_level': 'green'
}
display = monitor.format_budget_display(status)
assert '1,000,000' in display
assert '500,000' in display
assert 'GREEN' in display
print(f"✓ Display format includes all required elements")

# All tests passed!
print("\n" + "="*50)
print("✅ All tests passed!")
print("="*50)
