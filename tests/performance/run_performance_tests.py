#!/usr/bin/env python3
"""
Performance test runner for Resume Customizer API.

This script provides a CLI for running performance tests using Locust
and analyzing the results against defined benchmarks.
"""
import os
import sys
import time
import signal
import argparse
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import benchmark analysis functions
from tests.performance.benchmarks import (
    analyze_performance_results,
    generate_performance_report,
    save_performance_report
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("performance_tests")


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import locust
        logger.info(f"Using Locust version: {locust.__version__}")
    except ImportError:
        logger.error("Locust not installed. Please install it with: pip install locust")
        sys.exit(1)


def is_server_running(host, port=8000):
    """Check if the API server is running."""
    import socket
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def start_test_server():
    """Start the API server for testing."""
    logger.info("Starting test server...")
    
    # Check if server is already running
    if is_server_running("localhost", 8000):
        logger.info("A server is already running on port 8000")
        return None
    
    # Start the server in a subprocess
    server_process = subprocess.Popen(
        ["python", str(project_root / "start_server.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    # Wait for server to start
    for _ in range(10):  # Try for 10 seconds
        if is_server_running("localhost", 8000):
            logger.info("Test server started successfully")
            return server_process
        time.sleep(1)
    
    # If we got here, server didn't start
    logger.error("Failed to start test server")
    if server_process:
        server_process.terminate()
    return None


def stop_test_server(server_process):
    """Stop the API server."""
    if server_process:
        logger.info("Stopping test server...")
        server_process.terminate()
        server_process.wait()
        logger.info("Test server stopped")


def run_locust_tests(host, users, spawn_rate, run_time, headless=True):
    """Run Locust performance tests."""
    logger.info(f"Running Locust tests against {host} with {users} users...")
    
    # Prepare output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "test_results" / "performance" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Locust command
    locust_file = Path(__file__).parent / "locustfile.py"
    csv_prefix = str(output_dir / "locust_stats")
    
    cmd = [
        "locust",
        "-f", str(locust_file),
        "--host", host,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time,
        "--csv", csv_prefix
    ]
    
    if headless:
        cmd.append("--headless")
    
    # Run Locust
    try:
        process = subprocess.Popen(cmd)
        process.wait()
        
        # Check if CSV files were created
        history_csv = Path(f"{csv_prefix}_stats_history.csv")
        if not history_csv.exists():
            logger.error(f"Locust did not generate expected output file: {history_csv}")
            return None
        
        logger.info(f"Locust tests completed, results saved to: {output_dir}")
        return history_csv
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Locust process failed with error: {e}")
        return None
    except KeyboardInterrupt:
        logger.info("Locust tests interrupted")
        return None


def analyze_and_report(results_csv, report_path=None):
    """Analyze test results and generate a report."""
    if not results_csv or not results_csv.exists():
        logger.error("No results file to analyze")
        return False
    
    logger.info(f"Analyzing results from: {results_csv}")
    
    # Generate report path if not provided
    if not report_path:
        report_path = results_csv.parent / "performance_report.md"
    
    # Analyze results
    try:
        analysis = analyze_performance_results(results_csv)
        report = generate_performance_report(analysis)
        save_performance_report(report, report_path)
        
        logger.info(f"Performance report generated: {report_path}")
        
        # Check for failures
        failures = False
        for name, metrics in analysis["endpoints"].items():
            if metrics["threshold_status"] == "failed":
                failures = True
                logger.warning(f"Endpoint '{name}' failed performance thresholds:")
                for failure in metrics["threshold_failures"]:
                    logger.warning(f"  - {failure}")
        
        if failures:
            logger.warning("Some performance thresholds were not met!")
            return False
        else:
            logger.info("All performance thresholds passed!")
            return True
            
    except Exception as e:
        logger.error(f"Error analyzing results: {e}")
        return False


def main():
    """Main entry point for the performance test runner."""
    parser = argparse.ArgumentParser(description="Run performance tests for Resume Customizer API")
    parser.add_argument("--host", default="http://localhost:8000", help="API host URL")
    parser.add_argument("--users", type=int, default=10, help="Number of simulated users")
    parser.add_argument("--spawn-rate", type=int, default=5, help="User spawn rate per second")
    parser.add_argument("--run-time", default="1m", help="Test duration (e.g., 30s, 5m)")
    parser.add_argument("--no-headless", action="store_true", help="Run with Locust UI")
    parser.add_argument("--start-server", action="store_true", help="Start the API server")
    parser.add_argument("--analyze-only", help="Path to existing results file to analyze")
    parser.add_argument("--report-path", help="Path for the output report")
    
    args = parser.parse_args()
    
    # Check if just analyzing existing results
    if args.analyze_only:
        results_path = Path(args.analyze_only)
        return 0 if analyze_and_report(results_path, args.report_path) else 1
    
    # Check dependencies
    check_dependencies()
    
    # Start server if requested
    server_process = None
    if args.start_server:
        server_process = start_test_server()
        if not server_process:
            return 1
    
    try:
        # Run tests
        results_csv = run_locust_tests(
            args.host,
            args.users,
            args.spawn_rate,
            args.run_time,
            not args.no_headless
        )
        
        # Analyze results
        if results_csv:
            success = analyze_and_report(results_csv, args.report_path)
            return 0 if success else 1
        return 1
        
    except KeyboardInterrupt:
        logger.info("Tests interrupted")
        return 130
        
    finally:
        # Stop server if we started it
        if server_process:
            stop_test_server(server_process)


if __name__ == "__main__":
    sys.exit(main())
