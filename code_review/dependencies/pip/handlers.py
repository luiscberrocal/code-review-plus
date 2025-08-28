from code_review.settings import CLI_CONSOLE, LOGGING
import logging
import re
import subprocess
from pathlib import Path
# Ensure configuration is applied
logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
        CLI_CONSOLE.print(f"[red]Error:[/red] The 'requirements' directory was not found at {requirements_folder}")
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
                ["pur", "-r", str(req_file),"--dry-run", "--minor", "*"],
                capture_output=True,
                text=True,
                check=True,  # Raise an exception if the command fails
            )

            # Process the output line by line
            for line in result.stdout.splitlines():
                logger.debug("Pur output line: %s", line)
                match = update_pattern.match(line.strip())
                if match:
                    library, old_version, new_version = match.groups()
                    updated_packages.append(
                        {"library": library, "old_version": old_version, "new_version": new_version}
                    )

        except FileNotFoundError:
            logger.error("Error: 'pur' command not found. Please ensure it is installed and in your PATH.")
            return []
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running 'pur' on file {req_file}:")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return []

    return updated_packages


# --- Example Usage ---

if __name__ == "__main__":
    # Simulate a project directory structure for demonstration
    projects_folder = Path.home() / "adelantos" / "wompi-integration"
    logger.debug(f"Checking for requirements updates in {projects_folder}")
    updated = requirements_updated(projects_folder)
    if updated:
        CLI_CONSOLE.print("[green]Updated packages:[/green]")
        for pkg in updated:
            CLI_CONSOLE.print(f"- {pkg['library']}: {pkg['old_version']} -> {pkg['new_version']}")
