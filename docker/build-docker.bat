@echo off
setlocal enabledelayedexpansion

REM Circuit Synth Docker Build Script for Windows
REM This script builds and optionally runs the circuit-synth Docker container

set IMAGE_NAME=circuit-synth
set TAG=latest
set BUILD_ONLY=false
set RUN_TESTS=false
set DEV_MODE=false

REM Parse command line arguments
:parse_args
if "%1"=="" goto :check_docker
if "%1"=="--build-only" (
    set BUILD_ONLY=true
    shift
    goto :parse_args
)
if "%1"=="--run-tests" (
    set RUN_TESTS=true
    shift
    goto :parse_args
)
if "%1"=="--dev" (
    set DEV_MODE=true
    shift
    goto :parse_args
)
if "%1"=="--tag" (
    set TAG=%2
    shift
    shift
    goto :parse_args
)
if "%1"=="--help" (
    echo Usage: %0 [OPTIONS]
    echo.
    echo Options:
    echo   --build-only    Only build the image, don't run
    echo   --run-tests     Run tests after building
    echo   --dev           Run in development mode with interactive shell
    echo   --tag TAG       Specify image tag ^(default: latest^)
    echo   --help          Show this help message
    exit /b 0
)
echo [ERROR] Unknown option: %1
echo Use --help for usage information
exit /b 1

:check_docker
echo [INFO] Checking if Docker is running...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Create necessary directories
echo [INFO] Creating output and cache directories...
if not exist "output" mkdir output
if not exist "cache" mkdir cache
if not exist "test_output" mkdir test_output

REM Build the Docker image
echo [INFO] Building Docker image: %IMAGE_NAME%:%TAG%
docker build -t "%IMAGE_NAME%:%TAG%" .

if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    exit /b 1
)

echo [SUCCESS] Docker image built successfully!

REM If build-only mode, exit here
if "%BUILD_ONLY%"=="true" (
    echo [SUCCESS] Build completed. Use 'docker run' to run the container.
    exit /b 0
)

REM Run the container based on mode
if "%RUN_TESTS%"=="true" (
    echo [INFO] Running tests...
    docker run --rm -v "%cd%\src:/app/src" -v "%cd%\tests:/app/tests" -v "%cd%\test_output:/app/test_output" -e PYTHONPATH=/app/src -e RUST_LOG=info "%IMAGE_NAME%:%TAG%" python -m pytest tests/ -v
) else if "%DEV_MODE%"=="true" (
    echo [INFO] Starting development container with interactive shell...
    echo [WARNING] Press Ctrl+C to exit the container
    docker run --rm -it -v "%cd%\src:/app/src" -v "%cd%\examples:/app/examples" -v "%cd%\tests:/app/tests" -v "%cd%\output:/app/output" -v "%cd%\cache:/app/cache" -e PYTHONPATH=/app/src -e RUST_LOG=debug "%IMAGE_NAME%:%TAG%" /bin/bash
) else (
    echo [INFO] Running circuit-synth container...
    docker run --rm -v "%cd%\src:/app/src" -v "%cd%\examples:/app/examples" -v "%cd%\output:/app/output" -v "%cd%\cache:/app/cache" -e PYTHONPATH=/app/src -e RUST_LOG=info "%IMAGE_NAME%:%TAG%"
)

echo [SUCCESS] Done! 