import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path, PosixPath
from typing import Any

import yaml

from code_review import settings
from code_review.handlers.file_handlers import change_directory
from code_review.plugins.coverage.schemas import TestConfiguration, TestResult


def run_tests_and_get_coverage(
    unit_tests: str, minimum_coverage: float, settings_module: str = "config.settings.test"
) -> dict[str, str]:
    """Runs djanndo manage.py test.

    Changes to a specified folder, runs a Django test suite with coverage,
    reports the coverage, and extracts the coverage percentage.

    Args:
        unit_tests (str): A string of space-separated paths to unit tests.
        minimum_coverage (int|float): The minimum acceptable code coverage percentage.

    Returns:
        dict[str, str]: A dictionary containing the test output, coverage output, and running time.

    Raises:
        subprocess.CalledProcessError: If either the test or coverage report command fails.
        subprocess.TimeoutExpired: If the command takes longer than 3 minutes.
        ValueError: If the coverage percentage cannot be extracted from the output.
    """
    start_time = time.time()
    try:
        timeout_seconds = 180  # 3 minutes
        # Command to run unit tests with coverage
        test_command = (
            f"docker-compose -f local.yml run --rm django coverage run "
            f"manage.py test {unit_tests} --settings={settings_module} "
            f"--exclude-tag=INTEGRATION --exclude-tag=TDD"
        )
        print(f"Running command: {test_command}")
        test_results = subprocess.run(
            test_command, shell=True, check=True, text=True, capture_output=True, timeout=timeout_seconds
        )
        test_output = test_results.stdout

        # Command to report coverage and check against minimum
        report_command = (
            f"docker-compose -f local.yml run --rm django coverage report -m --fail-under={minimum_coverage}"
        )
        print(f"Running command: {report_command}")
        cov_results = subprocess.run(
            report_command, shell=True, check=False, text=True, capture_output=True, timeout=timeout_seconds
        )

        # Extract coverage from the output
        coverage_output = cov_results.stdout

        return {
            "test_output": test_output,
            "coverage_output": coverage_output,
            "running_time": time.time() - start_time,
        }
    except subprocess.TimeoutExpired as e:
        print(f"Error: Command exceeded timeout of {timeout_seconds} seconds.")
        raise TimeoutError(f"run_tests_and_get_coverage exceeded 3 minutes: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error during command execution: {e}")
        raise


def handle_test_output(test_output: str, coverage_output) -> Any:
    """Process the test output as needed.

    Args:
        test_output (str): The output from the test command.
        coverage_output (str): The output from the coverage report.

    Returns:
        Any: Processed test output.
    """
    # Implement any specific processing logic here
    test_count = -1
    coverage_percentage = -1.0

    test_count_regex = re.compile(r"Found (\d+) test\(s\)\.")
    cov_regex = re.compile(r"TOTAL\s+(\d+)\s+(\d+)\s+(?P<coverage>\d+)%")
    test_match = test_count_regex.search(test_output)
    if test_match:
        test_count = int(test_match.group(1))
    cov_match = cov_regex.search(coverage_output)
    if cov_match:
        coverage_percentage = float(cov_match.group("coverage"))
    return {
        "test_count": test_count,
        "coverage_percentage": coverage_percentage,
    }


def run_coverage(test_configuration: TestConfiguration) -> TestResult:
    """Run tests and get coverage based on the provided test configuration.

    Args:
        test_configuration (TestConfiguration): The configuration for running tests.

    Returns:
        dict[str, Any]: A dictionary containing test output and coverage output.
    """
    results = run_tests_and_get_coverage(
        unit_tests=" ".join(test_configuration.unit_tests),
        minimum_coverage=test_configuration.min_coverage,
        settings_module=test_configuration.settings_module,
    )
    processed_output = handle_test_output(results["test_output"], results["coverage_output"])
    processed_output["running_time"] = results["running_time"]

    return TestResult(**processed_output)


# Example Usage:
if __name__ == "__main__":
    original_cwd = Path(os.getcwd())
    base_project_folder = Path.home() / "adelantos"
    try:
        # Replace these with your actual folder, test paths, and desired coverage
        min_coverage = 85

        target_folder = base_project_folder / "payment-options-vue"
        tests_to_run = "pay_options_middleware.middleware.tests.unit pay_options_middleware.users.tests"
        unit_tests_to_run = tests_to_run.split(" ")
        unit_tests_to_run = []

        target_folder = base_project_folder / "six_payment_provider"
        # print(f"\nGenerating test configuration for folder: {target_folder} {target_folder.exists()}")
        # tests_to_run = ""
        unit_tests_to_run = []

        change_directory(target_folder)
        # target_folder = Path.home() / "adelantos" / "wu-integration"
        # tests_to_run = "wu_integration.rest.tests.unit"
        # min_coverage = 85

        # target_folder = Path.home() / "adelantos" / "payment-collector"
        # tests_to_run = [
        #     "payment_collector.api.tests.unit payment_collector.users.tests",
        #     " payment_collector.reconciliation.tests",
        # ]
        # min_coverage = 85.0

        settings_module_t = "config.settings.local"

        test_config = TestConfiguration(
            folder=target_folder,
            unit_tests=unit_tests_to_run,
            min_coverage=min_coverage,
            settings_module=settings_module_t,
        )

        config_data = test_config.model_dump()
        timestamp2 = datetime.now().strftime("%Y%m%d-%H%M%S")
        yaml_file_path: PosixPath = settings.OUTPUT_FOLDER / f"{target_folder.stem}_{timestamp2}_test_configuration.yml"

        with open(yaml_file_path, "w") as file:
            # `sort_keys=False` is often used to maintain the order from the model/dictionary
            # `default_flow_style=False` ensures a block-style (multi-line) YAML output for readability
            yaml.dump(config_data, file, sort_keys=False, default_flow_style=False)
        print(f"Test configuration saved to: {yaml_file_path}")

        # coverage = run_tests_and_get_coverage(
        #     target_folder, tests_to_run, min_coverage, settings_module=settings_module_t
        # )
        coverage = run_coverage(test_configuration=test_config)
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
    finally:
        change_directory(original_cwd)
