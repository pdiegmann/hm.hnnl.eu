#!/usr/bin/env python3

import os
import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hm-cli-test")

def run_test(test_name, command):
    """Run a test command and log the result."""
    logger.info(f"Running test: {test_name}")
    logger.info(f"Command: {command}")
    
    exit_code = os.system(command)
    
    if exit_code == 0:
        logger.info(f"Test '{test_name}' passed!")
        return True
    else:
        logger.error(f"Test '{test_name}' failed with exit code {exit_code}")
        return False

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Test the hm-cli tool")
    parser.add_argument("--install", action="store_true", help="Install the CLI tool before testing")
    args = parser.parse_args()
    
    # Get the project root directory
    project_dir = Path(__file__).parent.parent.absolute()
    
    # Install the CLI tool if requested
    if args.install:
        logger.info("Installing hm-cli...")
        os.chdir(project_dir)
        if os.system("pip install -e .") != 0:
            logger.error("Failed to install hm-cli")
            return 1
    
    # Run tests
    tests = [
        ("Version Check", "hm-cli --version"),
        ("Help Command", "hm-cli --help"),
        ("Cluster Help", "hm-cli cluster --help"),
        ("Service Help", "hm-cli service --help"),
        ("GitOps Help", "hm-cli gitops --help"),
        ("Config Show", "hm-cli config show"),
        ("Config Set", "hm-cli config set test.key test_value"),
        ("Config Show After Set", "hm-cli config show"),
    ]
    
    passed = 0
    failed = 0
    
    for name, cmd in tests:
        if run_test(name, cmd):
            passed += 1
        else:
            failed += 1
    
    # Print summary
    logger.info("=" * 50)
    logger.info(f"Test Summary: {passed} passed, {failed} failed")
    logger.info("=" * 50)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
