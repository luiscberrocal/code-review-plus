import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def requirements_updated(folder: Path) -> list[dict[str, str]]:
    """Updates minor version dependencies in requirement files within a specified folder
    and returns a list of updated packages.

    This function looks for a 'requirements' subdirectory inside the provided folder
    and processes all '.txt' files found there. It runs the 'pur --minor' command
    on each file, and then parses the command's output to identify which
    packages were updated.

    Args:
        folder (Path): The path to the root directory containing the 'requirements' folder.

    Returns:
        list[dict[str, str]]: A list of dictionaries, where each dictionary
                              represents an updated package. Each dictionary
                              has the following keys:
                              - 'library': The name of the updated package.
                              - 'old_version': The previous version.
                              - 'new_version': The new updated version.
                              Returns an empty list if no packages were updated or
                              if the 'requirements' folder does not exist.
    """
    updated_packages = []
    requirements_folder = folder / "requirements"

    # Check if the requirements folder exists
    if not requirements_folder.is_dir():
        print(f"Error: The 'requirements' directory was not found at {requirements_folder}")
        return []

    # Regex to parse the output line from `pur`
    # Example line: Updated mypy: 1.16.1 -> 1.17.1
    update_pattern = re.compile(r"Updated (.+): (.+) -> (.+)")

    # Iterate over all .txt files in the requirements directory
    for req_file in requirements_folder.glob("*.txt"):
        try:
            # Run the pur command to update minor versions
            # `capture_output=True` gets the stdout and stderr
            # `text=True` decodes the output as text
            result = subprocess.run(
                ["pur", "-r", str(req_file), "--minor"],
                capture_output=True,
                text=True,
                check=True,  # Raise an exception if the command fails
            )

            # Process the output line by line
            for line in result.stdout.splitlines():
                match = update_pattern.match(line.strip())
                if match:
                    library, old_version, new_version = match.groups()
                    updated_packages.append(
                        {"library": library, "old_version": old_version, "new_version": new_version}
                    )

        except FileNotFoundError:
            print("Error: 'pur' command not found. Please ensure it is installed and in your PATH.")
            return []
        except subprocess.CalledProcessError as e:
            print(f"Error running 'pur' on file {req_file}:")
            print(f"Stdout: {e.stdout}")
            print(f"Stderr: {e.stderr}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    return updated_packages


# --- Example Usage ---

if __name__ == "__main__":
    # Simulate a project directory structure for demonstration
    dummy_folder = Path("./dummy_project")
    dummy_requirements_folder = dummy_folder / "requirements"
    dummy_requirements_folder.mkdir(parents=True, exist_ok=True)

    # Create a dummy requirements.txt file with some content
    with open(dummy_requirements_folder / "base.txt", "w") as f:
        f.write("""
Werkzeug[watchdog]==3.1.3
ipdb==0.13.13
psycopg2==2.9.10
watchfiles==0.24.0
mypy==1.16.1
django-stubs==5.2.1
""")

    # Mock the subprocess run function to return the user's provided output.
    # In a real-world scenario, this would be a live call to the pur command.
    mock_pur_output = """
Updated pytz: 2023.4 -> 2025.2
Updated argon2-cffi: 23.1.0 -> 25.1.0
Updated redis: 5.3.0 -> 6.4.0
Updated hiredis: 2.4.0 -> 3.2.1
Updated django: 4.2.23 -> 5.2.5
Updated django-model-utils: 4.5.1 -> 5.0.0
Updated django-allauth: 65.9.0 -> 65.10.0
Updated crispy-bootstrap5: 2024.10 -> 2025.6
Updated django-redis: 5.4.0 -> 6.0.0
Updated djangorestframework: 3.16.0 -> 3.16.1
Updated hypothesis: 6.135.26 -> 6.138.0
Updated watchfiles: 0.24.0 -> 1.1.0
Updated mypy: 1.16.1 -> 1.17.1
Updated django-stubs: 5.2.1 -> 5.2.2
Updated djangorestframework-stubs: 3.16.0 -> 3.16.1
Updated sphinx: 7.4.7 -> 8.2.3
Updated coverage: 7.9.2 -> 7.10.3
Updated black: 24.10.0 -> 25.1.0
Updated pre-commit: 3.8.0 -> 4.3.0
Updated django-debug-toolbar: 4.4.6 -> 6.0.0
Updated django-extensions: 3.2.3 -> 4.
"""

    # Replace the actual subprocess.run call with a mock for the example
    def mock_run(*args, **kwargs):
        class MockResult:
            def __init__(self, stdout, returncode=0) -> None:
                self.stdout = stdout
                self.returncode = returncode

        print("--- Simulating 'pur' command output ---")
        return MockResult(mock_pur_output)

    # Temporarily replace the function
    original_run = subprocess.run
    subprocess.run = mock_run

    # Run the function with the dummy folder
    print("Running requirements_updated function...")
    updated = requirements_updated(dummy_folder)

    # Restore the original function
    subprocess.run = original_run

    # Print the results in a readable format
    print("\n--- List of Updated Packages ---")
    if updated:
        for pkg in updated:
            print(
                f"Library: {pkg['library']:<25} | Old Version: {pkg['old_version']:<10} | New Version: {pkg['new_version']}"
            )
    else:
        print("No packages were updated.")

    # Clean up the dummy directory
    import shutil

    shutil.rmtree(dummy_folder)
