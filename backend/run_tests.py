#!/usr/bin/env python3
"""
Automated test runner script for RAG Document Processing API
Provides comprehensive test execution with reporting and validation.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run automated tests for RAG API")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't cleanup test databases")
    
    args = parser.parse_args()
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    print("RAG Document Processing API - Automated Test Runner")
    print("=" * 60)
    
    # Check if pytest is installed
    if not run_command("python -m pytest --version", "Checking pytest installation"):
        print("ERROR: pytest is not installed. Please run: pip install pytest pytest-asyncio httpx")
        return 1
    
    # Install test dependencies if needed
    test_deps = ["pytest", "pytest-asyncio", "httpx", "pytest-cov"]
    print(f"Installing test dependencies: {', '.join(test_deps)}")
    if not run_command(f"pip install {' '.join(test_deps)}", "Installing test dependencies"):
        print("WARNING: Could not install some test dependencies")
    
    success = True
    
    # Run tests based on arguments
    if args.unit:
        success &= run_command(
            "python -m pytest tests/test_document_retrieval.py -v -m 'not integration'",
            "Unit Tests for Document Retrieval"
        )
    elif args.integration:
        success &= run_command(
            "python -m pytest tests/test_query_integration.py -v -m 'not unit'",
            "Integration Tests for Query Handling"
        )
    else:
        # Run all tests
        success &= run_command(
            "python -m pytest tests/test_document_retrieval.py -v",
            "Unit Tests for Document Retrieval"
        )
        
        success &= run_command(
            "python -m pytest tests/test_query_integration.py -v",
            "Integration Tests for Query Handling"
        )
    
    # Generate coverage report if requested
    if args.coverage:
        success &= run_command(
            "python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing",
            "Generating Coverage Report"
        )
        print("\nCoverage report generated in htmlcov/ directory")
    
    # Cleanup test databases unless disabled
    if not args.no_cleanup:
        cleanup_files = ["test.db", "test_integration.db"]
        for file in cleanup_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"Cleaned up {file}")
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("✅ Test validation completed successfully")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("❌ Please check the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
