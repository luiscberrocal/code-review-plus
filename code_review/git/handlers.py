import re
import subprocess

from code_review.exceptions import SimpleGitToolError


def _are_there_uncommited_changes() -> bool:
    """
    Check if there are any committed changes in the current git repository.

    Returns:
        bool: True if there are committed changes, False otherwise.
    """
    try:
        # Run the git log command to check for commits
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        # If the output is not empty, there are committed changes
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        # If git command fails, we assume there are no committed changes
        return False


def _get_git_version() -> str:
    """
    Internal helper function to get the current git version.

    Returns:
        str: The version of git as a string (e.g., '2.3.4').

    Raises:
        SimpleGitToolError: If git is not installed or cannot be found.
    """
    try:
        # Run the git --version command and capture its output
        result = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)
        # The output is typically "git version X.Y.Z", so we split to get the version number
        return result.stdout.strip().split()[-1]
    except FileNotFoundError:
        # This error occurs if the 'git' command is not found on the system
        raise SimpleGitToolError("Git is not installed or not in the system's PATH.")
    except subprocess.CalledProcessError:
        # This handles any other issues with running the command
        raise SimpleGitToolError("An unexpected error occurred while checking the git version.")


def _compare_versions(current_version: str, min_version: str) -> bool:
    """
    Internal helper function to compare two version strings.

    Args:
        current_version (str): The version of git currently installed.
        min_version (str): The minimum required version.

    Returns:
        bool: True if current_version is greater than or equal to min_version,
              False otherwise.
    """
    # Split the versions into a list of integers for comparison
    current_parts = [int(v) for v in re.findall(r'\d+', current_version)]
    min_parts = [int(v) for v in re.findall(r'\d+', min_version)]

    # Pad the shorter list with zeros to ensure they have the same length for comparison
    max_len = max(len(current_parts), len(min_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    min_parts.extend([0] * (max_len - len(min_parts)))

    return tuple(current_parts) >= tuple(min_parts)


def _get_latest_tag() -> str:
    latest_tag = "No tags found"
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
        )
        latest_tag = result.stdout.strip()
        #console.print(f"Latest tag: [bold cyan]{latest_tag}[/bold cyan]")

    except subprocess.CalledProcessError:
        #console.print("[bold yellow]No tags found in the repository.[/bold yellow]")
        pass
    return latest_tag

def get_current_git_branch() -> str:
    """Gets the currently checked out Git branch.

    This function executes a Git command to determine the name of the current
    branch. It assumes that the current working directory is inside a Git
    repository.

    Returns:
        str: The name of the currently checked out Git branch, or an empty
             string if an error occurs.
    """
    try:
        # Check if we are inside a git repository
        subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'],
                       check=True,
                       capture_output=True,
                       text=True)

        # Get the branch name
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            check=True,
            capture_output=True,
            text=True,
            # The shell=True argument can be a security risk if the command
            # string comes from untrusted user input, but here it's
            # a hardcoded command so it's safe.
            shell=False
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        # Return an empty string or handle the error as appropriate
        return ""
    except FileNotFoundError:
        print("Git command not found. Please ensure Git is installed and in your system's PATH.")
        return ""


