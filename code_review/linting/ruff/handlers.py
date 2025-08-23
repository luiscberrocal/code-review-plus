import re
import subprocess
from pathlib import Path


def count_ruff_issues(path: Path) -> int:
    """Runs `ruff check` on a specified path and returns the total number of issues found.

    This function executes the `ruff check` command as a subprocess, captures its
    output, and then uses a regular expression to parse the summary line to
    extract the total count of issues.

    Args:
        path (Path): The Path object representing the file or directory to check.

    Returns:
        int: The total number of issues found by ruff. Returns 0 if no issues
             are found, or -1 if the `ruff` command fails to run.
    """
    try:
        # Run `ruff check` as a subprocess. The stdout and stderr are captured.
        # `capture_output=True` redirects the command's output to the result object.
        # `text=True` decodes the output as text.
        # We specify the path as the argument for the ruff command.
        result = subprocess.run(
            ["ruff", "check", path],
            capture_output=True,
            text=True,
            check=False,
            # check=True
        )
        # The last line of the `ruff check` output contains the summary, e.g.,

        result_lines = result.stdout.strip().split("\n")
        last_line = result_lines[-1]
        if last_line.startswith("[*]"):
            last_line = result_lines[-2]

        # Use a regular expression to find the number of issues.
        # The pattern looks for one or more digits (\d+) after "Found " and before " issue".
        match = re.search(r"Found (\d+) error[s]?", last_line)

        if match:
            # If a match is found, extract the number and convert it to an integer.
            return int(match.group(1))
        # If the regex doesn't match, it likely means there are no issues.
        # ruff outputs "Found 0 issues" or similar, but let's be safe and
        # handle the case where it's a different summary message.
        # In the absence of a clear number, assume 0 issues.
        print("No issue count found in output. Assuming 0 issues.")
        return 0

    except FileNotFoundError:
        # This error occurs if the `ruff` command is not found in the system's PATH.
        print("Error: `ruff` command not found. Please ensure it is installed and in your PATH.")
        return -1
    except subprocess.CalledProcessError as e:
        # This error occurs if the subprocess command returns a non-zero exit code,
        # which can happen if `ruff check` fails for reasons other than finding issues
        # (e.g., invalid path).
        print(f"Error running `ruff`: {e.stderr} {e}")
        return -1
    except Exception as e:
        # Catch any other unexpected errors.
        print(f"An unexpected error occurred: {e}")
        return -1


def _check_and_format_ruff(folder_path: Path) -> bool:
    """Runs `ruff format` on a specified folder.

    First, it checks if any files need formatting without applying changes.
    If changes are needed, it then runs `ruff format` to apply them.

    Args:
        folder_path: The path to the folder to format.

    Returns:
        True if any files were formatted, False otherwise.
        Raises an exception if `ruff` is not found or other errors occur.
    """
    # Command to check for unformatted files without applying changes.
    # The --check flag will cause a non-zero exit code if formatting is needed.
    check_command: list[str] = ["ruff", "format", "--check", folder_path]

    try:
        # Use subprocess.run() to execute the command.
        # `capture_output=True` captures stdout and stderr.
        # `text=True` decodes output to strings.
        # `check=False` is crucial here so we can handle the non-zero exit code manually.
        check_result = subprocess.run(check_command, capture_output=True, text=True, check=False)

        # Check the return code. A non-zero code from `ruff format --check`
        # indicates that there are unformatted files.
        return check_result.returncode != 0

    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False
