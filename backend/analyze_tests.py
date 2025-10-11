#!/usr/bin/env python3
"""Systematically run all tests and capture results"""

import subprocess
import json
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and capture results"""
    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest', test_file, '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=90,
            cwd='tests'
        )
        return {
            'file': test_file,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'passed': result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            'file': test_file,
            'returncode': -1,
            'stdout': '',
            'stderr': 'TIMEOUT after 90 seconds',
            'passed': False
        }
    except Exception as e:
        return {
            'file': test_file,
            'returncode': -2,
            'stdout': '',
            'stderr': str(e),
            'passed': False
        }

def main():
    test_dir = Path('tests')
    test_files = sorted(test_dir.glob('test_*.py'))

    results = []
    passed_files = []
    failed_files = []
    error_files = []

    print("=" * 80)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()

    for i, test_file in enumerate(test_files, 1):
        test_name = test_file.name
        print(f"[{i}/{len(test_files)}] Testing {test_name}...", end=' ', flush=True)

        result = run_test_file(test_name)
        results.append(result)

        # Parse output for summary
        if result['passed']:
            print("✓ PASSED")
            passed_files.append(test_name)
        elif 'TIMEOUT' in result['stderr']:
            print("✗ TIMEOUT")
            error_files.append(test_name)
        elif 'ERROR collecting' in result['stdout'] or 'ModuleNotFoundError' in result['stdout']:
            print("✗ IMPORT ERROR")
            error_files.append(test_name)
        else:
            print("✗ FAILED")
            failed_files.append(test_name)

        # Show brief summary from output
        lines = result['stdout'].split('\n')
        for line in lines:
            if 'passed' in line or 'failed' in line or 'error' in line.lower():
                if '=====' in line:
                    print(f"    {line.strip()}")
                    break

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total test files: {len(test_files)}")
    print(f"Passed: {len(passed_files)}")
    print(f"Failed: {len(failed_files)}")
    print(f"Errors: {len(error_files)}")
    print()

    if passed_files:
        print("PASSED FILES:")
        for f in passed_files:
            print(f"  ✓ {f}")
        print()

    if failed_files:
        print("FAILED FILES:")
        for f in failed_files:
            print(f"  ✗ {f}")
        print()

    if error_files:
        print("ERROR FILES (import/timeout):")
        for f in error_files:
            print(f"  ✗ {f}")
        print()

    # Write detailed results to file
    with open('test_results_detailed.txt', 'w') as f:
        f.write("COMPREHENSIVE TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")

        for result in results:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"FILE: {result['file']}\n")
            f.write(f"STATUS: {'PASSED' if result['passed'] else 'FAILED'}\n")
            f.write(f"{'=' * 80}\n")
            f.write(result['stdout'])
            if result['stderr']:
                f.write(f"\nSTDERR:\n{result['stderr']}\n")
            f.write("\n\n")

    print(f"Detailed results written to: test_results_detailed.txt")

    return 0 if len(failed_files) == 0 and len(error_files) == 0 else 1

if __name__ == '__main__':
    exit(main())
