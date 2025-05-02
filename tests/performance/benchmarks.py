"""
Performance benchmarks for the Resume Customizer API.

This module defines performance thresholds and analysis functions
for evaluating the API's performance characteristics.
"""
from typing import Dict, List, Any, Tuple
import json
import csv
import statistics
from pathlib import Path


# Define performance thresholds
PERFORMANCE_THRESHOLDS = {
    # Endpoint thresholds (milliseconds)
    "endpoints": {
        "Health Check": {
            "median": 50,      # Median response time threshold (ms)
            "p95": 200,        # 95th percentile response time threshold (ms)
            "failure_rate": 1  # Maximum allowed failure rate (%)
        },
        "Upload Resume": {
            "median": 500,
            "p95": 2000,
            "failure_rate": 5
        },
        "Check Resume Status": {
            "median": 100,
            "p95": 500,
            "failure_rate": 2
        },
        "Get Resume Text": {
            "median": 200,
            "p95": 800,
            "failure_rate": 2
        },
        "Customize Resume": {
            "median": 300,
            "p95": 1000,
            "failure_rate": 5
        },
        "Check Customization Status": {
            "median": 100,
            "p95": 500,
            "failure_rate": 2
        },
        "Get Customization Result": {
            "median": 300,
            "p95": 1000,
            "failure_rate": 2
        },
        # Workflow endpoints
        "Workflow - Upload Resume": {
            "median": 500,
            "p95": 2000,
            "failure_rate": 5
        },
        "Workflow - Poll Resume Status": {
            "median": 100,
            "p95": 500,
            "failure_rate": 2
        },
        "Workflow - Customize Resume": {
            "median": 300, 
            "p95": 1000,
            "failure_rate": 5
        },
        "Workflow - Poll Customization Status": {
            "median": 100,
            "p95": 500,
            "failure_rate": 2
        },
        "Workflow - Get Result": {
            "median": 300,
            "p95": 1000,
            "failure_rate": 2
        }
    },
    
    # System load thresholds
    "system": {
        "cpu_usage": 80,     # Maximum CPU usage (%)
        "memory_usage": 80,  # Maximum memory usage (%)
        "network_errors": 1, # Maximum network error rate (%)
        "timeouts": 1        # Maximum timeout rate (%)
    },
    
    # Concurrency thresholds
    "concurrency": {
        "max_users": 50,        # Maximum concurrent users
        "rps_per_user": 0.5,    # Expected requests per second per user
        "max_rps": 25           # Maximum total requests per second
    }
}


def analyze_performance_results(csv_file: Path) -> Dict[str, Any]:
    """
    Analyze performance test results from a CSV file.
    
    Args:
        csv_file: Path to the CSV file with test results
        
    Returns:
        Dict containing analysis results
    """
    # Check if the file exists
    if not csv_file.exists():
        return {"error": f"Results file {csv_file} not found"}
    
    # Read CSV data
    results = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except Exception as e:
        return {"error": f"Failed to read results file: {str(e)}"}
    
    # Group by endpoint name
    endpoints = {}
    for row in results:
        name = row.get('Name', 'Unknown')
        if name not in endpoints:
            endpoints[name] = []
        endpoints[name].append(row)
    
    # Process each endpoint
    analysis = {
        "endpoints": {},
        "overall": {
            "median_response_time": 0,
            "p95_response_time": 0,
            "failure_rate": 0,
            "requests_per_second": 0,
            "total_requests": 0,
            "total_failures": 0
        }
    }
    
    total_requests = 0
    total_failures = 0
    total_response_time = 0
    response_times = []
    
    for name, data in endpoints.items():
        # Skip aggregates
        if name == 'Total' or name == 'Aggregated':
            continue
        
        # Extract metrics
        response_times_for_endpoint = [float(row.get('Response Time', 0)) for row in data]
        request_count = sum(int(row.get('Request Count', 0)) for row in data)
        failure_count = sum(int(row.get('Failure Count', 0)) for row in data)
        
        # Skip if no requests
        if not request_count:
            continue
        
        # Calculate statistics
        failure_rate = (failure_count / request_count) * 100 if request_count else 0
        median = statistics.median(response_times_for_endpoint) if response_times_for_endpoint else 0
        
        # Calculate P95 (95th percentile)
        p95 = 0
        if response_times_for_endpoint:
            sorted_times = sorted(response_times_for_endpoint)
            p95_index = int(len(sorted_times) * 0.95)
            p95 = sorted_times[p95_index]
        
        # Store results
        analysis["endpoints"][name] = {
            "request_count": request_count,
            "failure_count": failure_count,
            "failure_rate": failure_rate,
            "median_response_time": median,
            "p95_response_time": p95,
            "threshold_status": "unknown"  # Will be evaluated later
        }
        
        # Update totals
        total_requests += request_count
        total_failures += failure_count
        total_response_time += sum(response_times_for_endpoint)
        response_times.extend(response_times_for_endpoint)
    
    # Calculate overall statistics
    if total_requests > 0:
        analysis["overall"]["total_requests"] = total_requests
        analysis["overall"]["total_failures"] = total_failures
        analysis["overall"]["failure_rate"] = (total_failures / total_requests) * 100
        analysis["overall"]["median_response_time"] = statistics.median(response_times) if response_times else 0
        
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        analysis["overall"]["p95_response_time"] = sorted_times[p95_index] if sorted_times else 0
        
        # Calculate requests per second (assuming test duration from first to last request)
        analysis["overall"]["requests_per_second"] = total_requests / (total_response_time / 1000)
    
    # Compare with thresholds
    for name, metrics in analysis["endpoints"].items():
        threshold = PERFORMANCE_THRESHOLDS["endpoints"].get(name)
        
        if not threshold:
            metrics["threshold_status"] = "no_threshold"
            continue
        
        # Evaluate against thresholds
        passed = True
        failures = []
        
        if metrics["median_response_time"] > threshold["median"]:
            passed = False
            failures.append(f"Median {metrics['median_response_time']:.2f}ms > {threshold['median']}ms")
        
        if metrics["p95_response_time"] > threshold["p95"]:
            passed = False
            failures.append(f"P95 {metrics['p95_response_time']:.2f}ms > {threshold['p95']}ms")
        
        if metrics["failure_rate"] > threshold["failure_rate"]:
            passed = False
            failures.append(f"Failure rate {metrics['failure_rate']:.2f}% > {threshold['failure_rate']}%")
        
        metrics["threshold_status"] = "passed" if passed else "failed"
        if not passed:
            metrics["threshold_failures"] = failures
    
    return analysis


def generate_performance_report(analysis: Dict[str, Any]) -> str:
    """
    Generate a readable performance report from analysis data.
    
    Args:
        analysis: Analysis data from analyze_performance_results
        
    Returns:
        String containing formatted performance report
    """
    if "error" in analysis:
        return f"ERROR: {analysis['error']}\n"
    
    report = []
    report.append("# Resume Customizer API Performance Report\n")
    
    # Overall summary
    report.append("## Overall Performance\n")
    overall = analysis["overall"]
    report.append(f"- **Total Requests:** {overall['total_requests']}")
    report.append(f"- **Total Failures:** {overall['total_failures']} ({overall['failure_rate']:.2f}%)")
    report.append(f"- **Median Response Time:** {overall['median_response_time']:.2f}ms")
    report.append(f"- **P95 Response Time:** {overall['p95_response_time']:.2f}ms")
    report.append(f"- **Requests Per Second:** {overall['requests_per_second']:.2f}\n")
    
    # Endpoint details
    report.append("## Endpoint Performance\n")
    report.append("| Endpoint | Requests | Failures | Median (ms) | P95 (ms) | Status |")
    report.append("|----------|----------|----------|-------------|----------|--------|")
    
    for name, metrics in sorted(analysis["endpoints"].items()):
        status = metrics["threshold_status"]
        if status == "passed":
            status_str = "✓ PASS"
        elif status == "failed":
            status_str = "❌ FAIL"
        else:
            status_str = "⚠️ N/A"
        
        report.append(
            f"| {name} | {metrics['request_count']} | "
            f"{metrics['failure_count']} ({metrics['failure_rate']:.2f}%) | "
            f"{metrics['median_response_time']:.2f} | {metrics['p95_response_time']:.2f} | "
            f"{status_str} |"
        )
    
    report.append("\n")
    
    # Threshold failures
    failures_found = False
    for name, metrics in analysis["endpoints"].items():
        if metrics["threshold_status"] == "failed":
            if not failures_found:
                report.append("## Threshold Failures\n")
                failures_found = True
            
            report.append(f"### {name}\n")
            for failure in metrics["threshold_failures"]:
                report.append(f"- {failure}")
            report.append("")
    
    if not failures_found:
        report.append("## All Performance Thresholds Passed! ✓\n")
    
    # Recommendations
    report.append("## Recommendations\n")
    
    # Generate recommendations based on analysis
    recommendations = []
    
    # Check for slow endpoints
    slow_endpoints = []
    for name, metrics in analysis["endpoints"].items():
        threshold = PERFORMANCE_THRESHOLDS["endpoints"].get(name)
        if threshold and metrics["median_response_time"] > threshold["median"] * 1.5:
            slow_endpoints.append((name, metrics["median_response_time"], threshold["median"]))
    
    if slow_endpoints:
        report.append("### Performance Optimizations\n")
        for name, actual, expected in slow_endpoints:
            report.append(f"- **{name}**: Response time ({actual:.2f}ms) significantly exceeds the target ({expected}ms)")
            
            # Add specific recommendations based on endpoint
            if "Upload" in name:
                report.append("  - Consider implementing chunked uploads for large files")
                report.append("  - Optimize file processing with async I/O")
            elif "Customize" in name:
                report.append("  - Review CrewAI agent configuration and optimization")
                report.append("  - Consider implementing cached responses for similar job descriptions")
            elif "Text" in name or "Result" in name:
                report.append("  - Add response caching")
                report.append("  - Optimize database/storage access patterns")
            
            report.append("")
    
    # Check for high failure rates
    high_failure_endpoints = []
    for name, metrics in analysis["endpoints"].items():
        threshold = PERFORMANCE_THRESHOLDS["endpoints"].get(name)
        if threshold and metrics["failure_rate"] > threshold["failure_rate"]:
            high_failure_endpoints.append((name, metrics["failure_rate"], threshold["failure_rate"]))
    
    if high_failure_endpoints:
        report.append("### Reliability Improvements\n")
        for name, actual, expected in high_failure_endpoints:
            report.append(f"- **{name}**: Failure rate ({actual:.2f}%) exceeds the target ({expected}%)")
            report.append("  - Implement retry mechanisms with exponential backoff")
            report.append("  - Add circuit breakers for dependent services")
            report.append("  - Improve error handling and logging")
            report.append("")
    
    # Check overall throughput against threshold
    concurrency_threshold = PERFORMANCE_THRESHOLDS["concurrency"]
    if overall["requests_per_second"] > concurrency_threshold["max_rps"] * 0.8:
        report.append("### Scaling Recommendations\n")
        report.append(f"- Current throughput ({overall['requests_per_second']:.2f} RPS) is approaching the limit ({concurrency_threshold['max_rps']} RPS)")
        report.append("  - Implement horizontal scaling")
        report.append("  - Add caching layer")
        report.append("  - Consider database/storage optimizations")
        report.append("")
    
    return "\n".join(report)


def save_performance_report(report: str, output_path: Path):
    """
    Save the performance report to a file.
    
    Args:
        report: The performance report text
        output_path: Path to save the report
    """
    with open(output_path, "w") as f:
        f.write(report)
    print(f"Performance report saved to: {output_path}")


# When running directly, generate a report from the latest results
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze performance test results")
    parser.add_argument("--input", help="Path to the input CSV file", default="locust_stats_history.csv")
    parser.add_argument("--output", help="Path to save the output report", default="performance_report.md")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        analysis = analyze_performance_results(input_path)
        report = generate_performance_report(analysis)
        save_performance_report(report, output_path)
    except Exception as e:
        print(f"Error generating performance report: {str(e)}")
        raise
