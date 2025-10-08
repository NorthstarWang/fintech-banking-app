"""
Run all tests and collect results.
"""
import os
import subprocess
import sys

os.environ["USE_MOCK_DB"] = "true"

# List of test files
test_files = [
    "tests/test_auth.py",
    "tests/test_accounts.py",
    "tests/test_transactions.py",
    "tests/test_budgets.py",
    "tests/test_cards.py",
    "tests/test_messages.py",
    "tests/test_notifications.py",
    "tests/test_savings.py",
    "tests/test_subscriptions.py",
    "tests/test_business.py",
    "tests/test_users.py"
]

results = {}
total_passed = 0
total_failed = 0

print("Running all test suites...\n")

for test_file in test_files:
    print(f"Running {test_file}...")

    cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--tb=no", "-q"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)

    # Parse output to get pass/fail counts
    output_lines = result.stdout.strip().split('\n')
    for line in output_lines:
        if "passed" in line or "failed" in line:
            # Extract numbers
            parts = line.split()
            passed = 0
            failed = 0

            for i, part in enumerate(parts):
                if "passed" in part and i > 0:
                    passed = int(parts[i-1])
                if "failed" in part and i > 0:
                    failed = int(parts[i-1])

            results[test_file] = {"passed": passed, "failed": failed, "total": passed + failed}
            total_passed += passed
            total_failed += failed

            status = "✓" if failed == 0 else "✗"
            print(f"  {status} {passed} passed, {failed} failed")
            break

print("\n" + "="*50)
print("SUMMARY:")
print("="*50)

for test_file, result in results.items():
    status = "✓" if result["failed"] == 0 else "✗"
    print(f"{status} {test_file:40} {result['passed']:3d}/{result['total']:3d} passed")

print("="*50)
print(f"TOTAL: {total_passed} passed, {total_failed} failed")
print(f"SUCCESS RATE: {(total_passed/(total_passed+total_failed)*100):.1f}%")
