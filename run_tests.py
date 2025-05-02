#!/usr/bin/env python3
"""
Test Runner Script for Resume Customizer

This script provides a convenient way to run different types of tests
for the Resume Customizer application. It supports running unit tests,
integration tests, contract tests, end-to-end tests, and performance tests.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path


def show_banner(message):
    """Display a banner message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80 + "\n")


def check_test_data():
    """Check if test data exists, generate if needed."""
    test_data_dir = Path("test_data")
    test_data_dir.mkdir(exist_ok=True)
    
    # Check for PDF test resume
    pdf_path = test_data_dir / "test_resume.pdf"
    if not pdf_path.exists():
        print("Generating test PDF resume...")
        subprocess.run([sys.executable, "create_test_pdf.py"], check=True)
    
    # Check for DOCX test resume
    docx_path = test_data_dir / "test_resume.docx"
    if not docx_path.exists():
        print("Generating test DOCX resume...")
        subprocess.run([sys.executable, "create_test_docx.py"], check=True)


def run_tests(test_path, test_name, coverage=False):
    """Run tests with or without coverage."""
    show_banner(f"Running {test_name} Tests")
    
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
    if coverage:
        cmd.extend(["--cov=app", "--cov-append"])
    
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n{test_name} tests failed with return code: {result.returncode}")
        if not args.continue_on_error:
            sys.exit(result.returncode)
    else:
        print(f"\n{test_name} tests completed successfully!")


def generate_contract_docs():
    """Generate API contract documentation."""
    print("\nGenerating API contract documentation...")
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    subprocess.run([sys.executable, "tests/contract/generate_contract_docs.py"], check=True)
    print("API contract documentation generated at: docs/api_contracts.md")


def run_performance_tests(users=10, spawn_rate=2, run_time="1m"):
    """Run performance tests with Locust."""
    show_banner("Running Performance Tests")
    
    # Check if Locust is installed
    try:
        import locust
    except ImportError:
        print("Error: Locust is not installed. Install it with: pip install locust")
        return False
    
    # Run performance tests
    cmd = [
        sys.executable, 
        "tests/performance/run_performance_tests.py",
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time
    ]
    
    result = subprocess.run(cmd)
    return result.returncode == 0


def generate_coverage_report():
    """Generate a comprehensive coverage report."""
    show_banner("Generating Coverage Report")
    
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=app",
        "--cov-report=term",
        "--cov-report=html:coverage_html"
    ]
    
    subprocess.run(cmd, check=True)
    print("\nHTML coverage report generated at: coverage_html/index.html")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Resume Customizer Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all tests (unit, integration, contract)")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--contract", action="store_true", help="Run only contract tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--users", type=int, default=10, help="Number of users for performance tests")
    parser.add_argument("--spawn-rate", type=int, default=2, help="User spawn rate for performance tests")
    parser.add_argument("--run-time", default="1m", help="Duration for performance tests (e.g., 30s, 1m)")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue running tests if some fail")
    
    global args
    args = parser.parse_args()
    
    # If no test types specified, show help
    if not (args.all or args.unit or args.integration or args.contract or args.e2e or args.performance):
        parser.print_help()
        return 1
    
    # Check/generate test data
    check_test_data()
    
    # Determine which tests to run
    if args.all:
        args.unit = args.integration = args.contract = True
    
    # Run selected tests
    if args.unit:
        run_tests("tests/unit", "Unit", args.coverage)
    
    if args.integration:
        run_tests("tests/integration", "Integration", args.coverage)
    
    if args.contract:
        run_tests("tests/contract", "Contract", args.coverage)
        generate_contract_docs()
    
    if args.e2e:
        run_tests("tests/integration/test_end_to_end_flow.py", "End-to-End", args.coverage)
    
    # Generate final coverage report if requested
    if args.coverage:
        generate_coverage_report()
    
    # Run performance tests if requested
    if args.performance:
        if not run_performance_tests(args.users, args.spawn_rate, args.run_time):
            return 1
    
    print("\nAll tests completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
