#!/usr/bin/env python3
"""
Test runner for the banking application test suite
Executes all test modules and provides a comprehensive report
"""

import sys
import os
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestRunner:
    """Orchestrates test execution and reporting"""
    
    def __init__(self):
        self.test_modules = [
            "test_auth",
            "test_users", 
            "test_transactions",
            "test_accounts",
            "test_budgets",
            "test_cards",
            "test_savings",
            "test_business",
            "test_subscriptions",
            "test_notifications",
            "test_messages"
        ]
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self, verbose: bool = False) -> Dict:
        """Run all test modules and collect results"""
        print("=" * 70)
        print("BANKING APPLICATION TEST SUITE")
        print("=" * 70)
        print(f"Starting test run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing {len(self.test_modules)} modules...\n")
        
        self.start_time = time.time()
        
        for module in self.test_modules:
            self.run_test_module(module, verbose)
            
        self.end_time = time.time()
        
        return self.generate_report()
    
    def run_test_module(self, module: str, verbose: bool = False) -> Tuple[bool, str]:
        """Run a single test module"""
        print(f"Running {module}...", end=" ", flush=True)
        
        cmd = ["pytest", f"{module}.py", "-v" if verbose else "-q", "--tb=short"]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            # Parse test results
            passed = failed = skipped = 0
            for line in result.stdout.split('\n'):
                if 'passed' in line and 'failed' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'passed' in part and i > 0:
                            passed = int(parts[i-1])
                        elif 'failed' in part and i > 0:
                            failed = int(parts[i-1])
                        elif 'skipped' in part and i > 0:
                            skipped = int(parts[i-1])
            
            self.results[module] = {
                "success": success,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "output": output,
                "duration": 0  # Would need to parse from pytest output
            }
            
            if success:
                print(f"✅ PASSED ({passed} tests)")
            else:
                print(f"❌ FAILED ({failed} failures)")
                
            return success, output
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            self.results[module] = {
                "success": False,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "output": str(e),
                "error": True
            }
            return False, str(e)
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_passed = sum(r["passed"] for r in self.results.values())
        total_failed = sum(r["failed"] for r in self.results.values())
        total_skipped = sum(r["skipped"] for r in self.results.values())
        total_tests = total_passed + total_failed + total_skipped
        
        duration = self.end_time - self.start_time if self.end_time else 0
        
        success_modules = [m for m, r in self.results.items() if r["success"]]
        failed_modules = [m for m, r in self.results.items() if not r["success"]]
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Modules: {len(self.test_modules)}")
        print(f"Successful: {len(success_modules)} ✅")
        print(f"Failed: {len(failed_modules)} ❌")
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")
        print(f"Skipped: {total_skipped} ⏭️")
        print(f"\nDuration: {duration:.2f} seconds")
        print(f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        if failed_modules:
            print("\n" + "=" * 70)
            print("FAILED MODULES:")
            print("=" * 70)
            for module in failed_modules:
                print(f"  - {module}")
                if self.results[module]["failed"] > 0:
                    print(f"    Failed tests: {self.results[module]['failed']}")
        
        print("=" * 70)
        
        return {
            "summary": {
                "total_modules": len(self.test_modules),
                "successful_modules": len(success_modules),
                "failed_modules": len(failed_modules),
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "duration": duration,
                "success_rate": (total_passed/total_tests*100) if total_tests > 0 else 0
            },
            "modules": self.results,
            "failed_modules": failed_modules,
            "timestamp": datetime.now().isoformat()
        }
    
    def save_report(self, report: Dict, filename: str = "test_report.json"):
        """Save test report to file"""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {filename}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run banking application test suite")
    parser.add_argument("-v", "--verbose", action="store_true", 
                      help="Verbose output")
    parser.add_argument("-m", "--module", type=str, 
                      help="Run specific test module")
    parser.add_argument("-s", "--save-report", action="store_true",
                      help="Save detailed report to file")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.module:
        # Run single module
        if args.module.startswith("test_"):
            module = args.module
        else:
            module = f"test_{args.module}"
            
        if module not in runner.test_modules:
            print(f"Error: Unknown test module '{module}'")
            print(f"Available modules: {', '.join(runner.test_modules)}")
            sys.exit(1)
            
        runner.test_modules = [module]
    
    # Run tests
    report = runner.run_all_tests(verbose=args.verbose)
    
    # Save report if requested
    if args.save_report:
        runner.save_report(report)
    
    # Exit with appropriate code
    sys.exit(0 if report["summary"]["failed"] == 0 else 1)


if __name__ == "__main__":
    main()