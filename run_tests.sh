#!/bin/bash
# Main test runner script for Resume Customizer

# Set error handling
set -e

# Show help message
show_help() {
    echo "Resume Customizer Test Runner"
    echo ""
    echo "Usage: ./run_tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all            Run all tests (unit, integration, contract)"
    echo "  --unit           Run only unit tests"
    echo "  --integration    Run only integration tests"
    echo "  --contract       Run only contract tests"
    echo "  --e2e            Run end-to-end tests"
    echo "  --coverage       Generate coverage report"
    echo "  --performance    Run performance tests (requires Locust)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh --unit            # Run unit tests"
    echo "  ./run_tests.sh --all --coverage  # Run all tests with coverage"
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Parse arguments
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_CONTRACT=false
RUN_E2E=false
RUN_COVERAGE=false
RUN_PERFORMANCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            RUN_CONTRACT=true
            shift
            ;;
        --unit)
            RUN_UNIT=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --contract)
            RUN_CONTRACT=true
            shift
            ;;
        --e2e)
            RUN_E2E=true
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --performance)
            RUN_PERFORMANCE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to run tests with or without coverage
run_tests() {
    local test_path=$1
    local test_name=$2
    
    echo "===== Running $test_name Tests ====="
    
    if [ "$RUN_COVERAGE" = true ]; then
        python -m pytest $test_path -v --cov=app --cov-append
    else
        python -m pytest $test_path -v
    fi
    
    echo "===== $test_name Tests Completed ====="
    echo ""
}

# Check if test data exists, generate if needed
check_test_data() {
    if [ ! -f "test_data/test_resume.pdf" ]; then
        echo "Generating test PDF resume..."
        python create_test_pdf.py
    fi
    
    if [ ! -f "test_data/test_resume.docx" ]; then
        echo "Generating test DOCX resume..."
        python create_test_docx.py
    fi
}

# Main execution
check_test_data

# Run unit tests
if [ "$RUN_UNIT" = true ]; then
    run_tests "tests/unit" "Unit"
fi

# Run integration tests
if [ "$RUN_INTEGRATION" = true ]; then
    run_tests "tests/integration" "Integration"
fi

# Run contract tests
if [ "$RUN_CONTRACT" = true ]; then
    run_tests "tests/contract" "Contract"
    
    # Generate API contract documentation
    echo "Generating API contract documentation..."
    mkdir -p docs
    python tests/contract/generate_contract_docs.py
    echo "API contract documentation generated at: docs/api_contracts.md"
    echo ""
fi

# Run end-to-end tests
if [ "$RUN_E2E" = true ]; then
    run_tests "tests/integration/test_end_to_end_flow.py" "End-to-End"
fi

# Generate final coverage report
if [ "$RUN_COVERAGE" = true ]; then
    echo "===== Generating Coverage Report ====="
    python -m pytest --cov=app --cov-report=term --cov-report=html:coverage_html
    echo "HTML coverage report generated at: coverage_html/index.html"
    echo ""
fi

# Run performance tests
if [ "$RUN_PERFORMANCE" = true ]; then
    echo "===== Running Performance Tests ====="
    # Check if Locust is installed
    if ! python -c "import locust" &> /dev/null; then
        echo "Error: Locust is not installed. Install it with: pip install locust"
        exit 1
    fi
    
    # Run performance tests
    python tests/performance/run_performance_tests.py --users 10 --spawn-rate 2 --run-time 1m
    echo ""
fi

echo "All tests completed successfully!"
