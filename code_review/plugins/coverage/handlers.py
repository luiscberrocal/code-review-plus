import os
import re
import subprocess
from pathlib import Path, PosixPath
from typing import Any, List

import yaml

from code_review.plugins.coverage.schemas import TestConfiguration
from code_review.handlers.file_handlers import change_directory
from code_review.schemas import RulesResult, SeverityLevel, RuleCategory


def run_tests_and_get_coverage(
    folder: Path, unit_tests: str, minimum_coverage: int, settings_module: str = "config.settings.test"
) -> dict[str, Any]:
    """Changes to a specified folder, runs a Django test suite with coverage,
    reports the coverage, and extracts the coverage percentage.

    Args:
        folder (str): The path to the directory containing the docker-compose file.
        unit_tests (str): A string of space-separated paths to unit tests.
        minimum_coverage (int): The minimum acceptable code coverage percentage.

    Returns:
        float: The extracted code coverage percentage.

    Raises:
        subprocess.CalledProcessError: If either the test or coverage report command fails.
        ValueError: If the coverage percentage cannot be extracted from the output.
    """
    original_cwd = os.getcwd()
    try:
        change_directory(folder)

        # Command to run unit tests with coverage
        test_command = (
            f"docker-compose -f local.yml run --rm django coverage run "
            f"manage.py test {unit_tests} --settings={settings_module} "
            f"--exclude-tag=INTEGRATION"
        )
        print(f"Running command: {test_command}")
        subprocess.run(test_command, shell=True, check=True)

        # Command to report coverage and check against minimum
        report_command = (
            f"docker-compose -f local.yml run --rm django coverage report -m --fail-under={minimum_coverage}"
        )
        print(f"Running command: {report_command}")
        result = subprocess.run(report_command, shell=True, check=False, text=True, capture_output=True)

        # Extract coverage from the output
        coverage_output = result.stdout
        with open(os.path.join(folder, "__coverage.txt"), "w") as f:
            f.write(coverage_output)

        test_count_match = re.search(
            r"Ran\s+(?P<test_count>\d+)\s+tests\s+in\s+(?P<running_time>[\d\.]+)s", coverage_output
        )

        test_count = -1
        running_time = -1.0
        coverage_percentage = -1.0

        if test_count_match:
            test_count = int(test_count_match.group("test_count"))
            running_time = float(test_count_match.group("running_time"))
        # Regular expression to find the total coverage percentage
        # It looks for a line with "TOTAL" and a number ending with "%"
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%", coverage_output)
        if match:
            coverage_percentage = float(match.group(1))

        return {"test_count": test_count, "running_time": running_time, "coverage_percentage": coverage_percentage}
    finally:
        os.chdir(original_cwd)


# Example Usage:
if __name__ == "__main__":
    try:
        # Replace these with your actual folder, test paths, and desired coverage
        target_folder = Path.home() / "adelantos" / "payment-options-vue"
        tests_to_run = "pay_options_middleware.middleware.tests.unit pay_options_middleware.users.tests"
        min_coverage = 85

        target_folder = Path.home() / "adelantos" / "wu-integration"
        tests_to_run = "wu_integration.rest.tests.unit"
        min_coverage = 85

        target_folder = Path.home() / "adelantos" / "payment-collector"
        tests_to_run = [
            "payment_collector.api.tests.unit payment_collector.users.tests",
            " payment_collector.reconciliation.tests",
        ]
        min_coverage = 85.0
        settings_module_t = "config.settings.local"

        test_configuration = TestConfiguration(
            folder=target_folder, unit_tests=tests_to_run, min_coverage=min_coverage, settings_module=settings_module_t
        )

        config_data = test_configuration.model_dump()
        yaml_file_path: PosixPath = Path("test_configuration.yml")

        with open(yaml_file_path, "w") as file:
            # `sort_keys=False` is often used to maintain the order from the model/dictionary
            # `default_flow_style=False` ensures a block-style (multi-line) YAML output for readability
            yaml.dump(config_data, file, sort_keys=False, default_flow_style=False)

        coverage = run_tests_and_get_coverage(
            target_folder, tests_to_run, min_coverage, settings_module=settings_module_t
        )
        print(f"\n>>>>>>>>>>>>>>>>>>>> Successfully completed. Final coverage: {coverage}%")

    except subprocess.CalledProcessError as e:
        print("\nXXXXXXXXXXXXX An error occurred during a command execution:")
        print(f"Return code: {e.returncode}")
        print(f"Command: {e.cmd}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        print("\nTests failed or coverage was below the minimum. Exiting.")
    except FileNotFoundError:
        print(f"\nError: The specified folder '{target_folder}' does not exist.")
    except ValueError as e:
        print(f"\nError: {e}")


def validate_coverage_rules(
    coverage_data: dict[str, Any],
    coverage_config: dict[str, Any],
    file_path: Path | None = None
) -> List[RulesResult]:
    """
    Validate coverage-related rules and return structured validation results.
    
    Args:
        coverage_data: Coverage analysis results containing percentages and file info
        coverage_config: Configuration for coverage thresholds and requirements  
        file_path: Optional path to the analyzed file for context
        
    Returns:
        List of enhanced rule validation results
        
    Raises:
        ValueError: If coverage_data is invalid or missing required fields
        TypeError: If arguments are not of expected types
    """
    if not isinstance(coverage_data, dict):
        raise TypeError("coverage_data must be a dictionary")
    
    if not isinstance(coverage_config, dict):
        raise TypeError("coverage_config must be a dictionary")
    
    results = []
    
    # Validate minimum coverage threshold
    coverage_percentage = coverage_data.get("coverage_percentage", 0)
    min_threshold = coverage_config.get("minimum_coverage", 85)
    
    if coverage_percentage >= min_threshold:
        results.append(RulesResult(
            name="minimum_coverage_threshold",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.INFO,
            passed=True,
            message=f"Coverage {coverage_percentage}% meets minimum threshold of {min_threshold}%",
            details=f"Current coverage: {coverage_percentage}%, Required: {min_threshold}%. Excellent test coverage maintained."
        ))
    else:
        coverage_gap = min_threshold - coverage_percentage
        results.append(RulesResult(
            name="minimum_coverage_threshold",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.ERROR,
            passed=False,
            message=f"Coverage {coverage_percentage}% below minimum threshold of {min_threshold}%",
            details=f"Current coverage: {coverage_percentage}%, Required: {min_threshold}%. Need to add {coverage_gap:.1f}% more coverage. Focus on uncovered code paths and edge cases."
        ))
    
    # Validate test count if available
    test_count = coverage_data.get("test_count", -1)
    if test_count > 0:
        running_time = coverage_data.get("running_time", "unknown")
        results.append(RulesResult(
            name="test_execution_success",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.INFO,
            passed=True,
            message=f"Successfully executed {test_count} tests",
            details=f"Test count: {test_count}, Running time: {running_time}s. All tests completed successfully."
        ))
    elif test_count == 0:
        results.append(RulesResult(
            name="test_execution_success",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.WARNING,
            passed=False,
            message="No tests were executed",
            details="No test files found or executed. Consider adding unit tests to improve code coverage and quality. Start with testing core functionality and edge cases."
        ))
    # If test_count is -1 (not checked), we don't add a result
    
    # Validate coverage regression (if previous coverage provided)
    previous_coverage = coverage_config.get("previous_coverage")
    if previous_coverage is not None:
        coverage_change = coverage_percentage - previous_coverage
        if coverage_change >= 0:
            results.append(RulesResult(
                name="coverage_regression_check",
                category=RuleCategory.TESTING,
                severity=SeverityLevel.INFO,
                passed=True,
                message=f"Coverage maintained or improved by {coverage_change:.1f}%",
                details=f"Previous: {previous_coverage}%, Current: {coverage_percentage}%, Change: +{coverage_change:.1f}%"
            ))
        else:
            max_allowed_drop = coverage_config.get("max_coverage_drop", 5)
            if abs(coverage_change) <= max_allowed_drop:
                results.append(RulesResult(
                    name="coverage_regression_check",
                    category=RuleCategory.TESTING,
                    severity=SeverityLevel.WARNING,
                    passed=False,
                    message=f"Coverage decreased by {abs(coverage_change):.1f}% but within allowed limit",
                    details=f"Previous: {previous_coverage}%, Current: {coverage_percentage}%, Drop: {coverage_change:.1f}%, Max allowed: {max_allowed_drop}%"
                ))
            else:
                results.append(RulesResult(
                    name="coverage_regression_check",
                    category=RuleCategory.TESTING,
                    severity=SeverityLevel.ERROR,
                    passed=False,
                    message=f"Coverage decreased by {abs(coverage_change):.1f}% exceeding allowed limit",
                    details=f"Previous: {previous_coverage}%, Current: {coverage_percentage}%, Drop: {coverage_change:.1f}%, Max allowed: {max_allowed_drop}%. Investigate removed or modified tests."
                ))
    
    return results
