@echo off
:: Resume Customizer Test Runner for Windows
setlocal enabledelayedexpansion

:: Show help message function
:ShowHelp
    echo Resume Customizer Test Runner
    echo.
    echo Usage: run_tests.bat [OPTIONS]
    echo.
    echo Options:
    echo   --all            Run all tests (unit, integration, contract)
    echo   --unit           Run only unit tests
    echo   --integration    Run only integration tests
    echo   --contract       Run only contract tests
    echo   --e2e            Run end-to-end tests
    echo   --coverage       Generate coverage report
    echo   --performance    Run performance tests (requires Locust)
    echo   --help           Show this help message
    echo.
    echo Examples:
    echo   run_tests.bat --unit            # Run unit tests
    echo   run_tests.bat --all --coverage  # Run all tests with coverage
    goto :eof

:: Check if no arguments provided
if "%~1"=="" (
    call :ShowHelp
    exit /b 1
)

:: Parse arguments
set RUN_UNIT=false
set RUN_INTEGRATION=false
set RUN_CONTRACT=false
set RUN_E2E=false
set RUN_COVERAGE=false
set RUN_PERFORMANCE=false

:ParseArgs
if "%~1"=="" goto :EndParse
    if "%~1"=="--all" (
        set RUN_UNIT=true
        set RUN_INTEGRATION=true
        set RUN_CONTRACT=true
        shift
        goto :ParseArgs
    )
    if "%~1"=="--unit" (
        set RUN_UNIT=true
        shift
        goto :ParseArgs
    )
    if "%~1"=="--integration" (
        set RUN_INTEGRATION=true
        shift
        goto :ParseArgs
    )
    if "%~1"=="--contract" (
        set RUN_CONTRACT=true
        shift
        goto :ParseArgs
    )
    if "%~1"=="--e2e" (
        set RUN_E2E=true
        shift
        goto :ParseArgs
    )
    if "%~1"=="--coverage" (
        set RUN_COVERAGE=true
        shift
        goto :ParseArgs
    )
    if "%~1"=="--performance" (
        set RUN_PERFORMANCE=true
        shift
        goto :ParseArgs
    )
    if "%~1"=="--help" (
        call :ShowHelp
        exit /b 0
    )
    echo Unknown option: %~1
    call :ShowHelp
    exit /b 1
:EndParse

:: Function to run tests with or without coverage
:RunTests
    set test_path=%~1
    set test_name=%~2
    
    echo ===== Running %test_name% Tests =====
    
    if "%RUN_COVERAGE%"=="true" (
        python -m pytest %test_path% -v --cov=app --cov-append
    ) else (
        python -m pytest %test_path% -v
    )
    
    echo ===== %test_name% Tests Completed =====
    echo.
    goto :eof

:: Check if test data exists, generate if needed
:CheckTestData
    if not exist "test_data\test_resume.pdf" (
        echo Generating test PDF resume...
        python create_test_pdf.py
    )
    
    if not exist "test_data\test_resume.docx" (
        echo Generating test DOCX resume...
        python create_test_docx.py
    )
    goto :eof

:: Main execution
call :CheckTestData

:: Run unit tests
if "%RUN_UNIT%"=="true" (
    call :RunTests "tests/unit" "Unit"
)

:: Run integration tests
if "%RUN_INTEGRATION%"=="true" (
    call :RunTests "tests/integration" "Integration"
)

:: Run contract tests
if "%RUN_CONTRACT%"=="true" (
    call :RunTests "tests/contract" "Contract"
    
    :: Generate API contract documentation
    echo Generating API contract documentation...
    if not exist "docs" mkdir docs
    python tests/contract/generate_contract_docs.py
    echo API contract documentation generated at: docs/api_contracts.md
    echo.
)

:: Run end-to-end tests
if "%RUN_E2E%"=="true" (
    call :RunTests "tests/integration/test_end_to_end_flow.py" "End-to-End"
)

:: Generate final coverage report
if "%RUN_COVERAGE%"=="true" (
    echo ===== Generating Coverage Report =====
    python -m pytest --cov=app --cov-report=term --cov-report=html:coverage_html
    echo HTML coverage report generated at: coverage_html/index.html
    echo.
)

:: Run performance tests
if "%RUN_PERFORMANCE%"=="true" (
    echo ===== Running Performance Tests =====
    
    :: Check if Locust is installed
    python -c "import locust" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Locust is not installed. Install it with: pip install locust
        exit /b 1
    )
    
    :: Run performance tests
    python tests/performance/run_performance_tests.py --users 10 --spawn-rate 2 --run-time 1m
    echo.
)

echo All tests completed successfully!
