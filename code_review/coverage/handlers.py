import os
import subprocess
import re
from pathlib import Path


def run_tests_and_get_coverage(
    folder: Path,
    unit_tests: str,
    minimum_coverage: int
) -> float:
    """
    Changes to a specified folder, runs a Django test suite with coverage,
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
        os.chdir(folder)

        # Command to run unit tests with coverage
        test_command = (
            f"docker-compose -f local.yml run --rm django coverage run "
            f"manage.py test {unit_tests} --settings=config.settings.test "
            f"--exclude-tag=INTEGRATION"
        )
        print(f"Running command: {test_command}")
        subprocess.run(test_command, shell=True, check=True)

        # Command to report coverage and check against minimum
        report_command = (
            f"docker-compose -f local.yml run --rm django coverage report -m "
            f"--fail-under={minimum_coverage}"
        )
        print(f"Running command: {report_command}")
        result = subprocess.run(
            report_command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )

        # Extract coverage from the output
        coverage_output = result.stdout
        # Regular expression to find the total coverage percentage
        # It looks for a line with "TOTAL" and a number ending with "%"
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%', coverage_output)
        if match:
            coverage_percentage = float(match.group(1))
            print(f"Coverage extracted: {coverage_percentage}%")
            return coverage_percentage
        else:
            raise ValueError("Could not find coverage percentage in the output.")

    finally:
        os.chdir(original_cwd)

# Example Usage:
if __name__ == "__main__":
    try:
        # Replace these with your actual folder, test paths, and desired coverage
        target_folder = Path.home() / "adelantos" / "payment-options-vue"
        tests_to_run = "pay_options_middleware.middleware.tests.unit pay_options_middleware.users.tests"
        min_coverage = 85

        target_folder = Path.home() / "adelantos" / "payment-collector"
        tests_to_run = "payment_collector.api.tests.unit payment_collector.users.tests payment_collector.reconciliation.tests"
        min_coverage = 85


        coverage = run_tests_and_get_coverage(target_folder, tests_to_run, min_coverage)
        print(f"\nSuccessfully completed. Final coverage: {coverage}%")

    except subprocess.CalledProcessError as e:
        print(f"\nAn error occurred during a command execution:")
        print(f"Return code: {e.returncode}")
        print(f"Command: {e.cmd}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        print("\nTests failed or coverage was below the minimum. Exiting.")
    except FileNotFoundError:
        print(f"\nError: The specified folder '{target_folder}' does not exist.")
    except ValueError as e:
        print(f"\nError: {e}")