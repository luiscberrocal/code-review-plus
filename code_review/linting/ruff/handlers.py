import subprocess
import re
from pathlib import Path

def count_ruff_issues(path: Path) -> int:
    """
    Runs `ruff check` on a specified path and returns the total number of issues found.

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
            ['ruff', 'check', str(path)],
            capture_output=True,
            text=True,
            check=True
        )

        # The last line of the `ruff check` output contains the summary, e.g.,
        # "Found 12 issues."
        last_line = result.stdout.strip().split('\n')[-1]

        # Use a regular expression to find the number of issues.
        # The pattern looks for one or more digits (\d+) after "Found " and before " issue".
        match = re.search(r"Found (\d+) issue", last_line)

        if match:
            # If a match is found, extract the number and convert it to an integer.
            issue_count = int(match.group(1))
            return issue_count
        else:
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
        print(f"Error running `ruff`: {e.stderr}")
        return -1
    except Exception as e:
        # Catch any other unexpected errors.
        print(f"An unexpected error occurred: {e}")
        return -1

if __name__ == "__main__":
    # --- Example Usage ---
    # To run this example, save the code as a Python file (e.g., `count_issues.py`)
    # and then run it from your terminal: `python count_issues.py`

    # Create a dummy file with a common ruff issue (unused import)
    # The `with` statement ensures the file is properly closed.
    dummy_file_path = Path("test_code.py")
    with open(dummy_file_path, "w") as f:
        f.write("import os\n\ndef my_func():\n    return 'hello world'\n")

    print(f"Checking for issues in '{dummy_file_path}'...")

    # Call the function with the path to the dummy file.
    issue_count = count_ruff_issues(dummy_file_path)

    if issue_count > -1:
        print(f"Found {issue_count} issue(s).")

    # Clean up the dummy file
    dummy_file_path.unlink()

    # Example for a directory (assuming you have some python files in it)
    # The current directory '.' is a common test case.
    current_directory = Path('.')
    print(f"\nChecking for issues in the current directory '{current_directory}'...")
    directory_issue_count = count_ruff_issues(current_directory)

    if directory_issue_count > -1:
        print(f"Found {directory_issue_count} issue(s).")
