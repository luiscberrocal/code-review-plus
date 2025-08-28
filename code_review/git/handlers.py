import json
import logging
import re
import subprocess
from datetime import datetime
from typing import Any

from code_review.exceptions import SimpleGitToolError
from code_review.git.adapters import parse_git_date
from code_review.git.schemas import BranchSchema
from code_review.settings import CLI_CONSOLE

logger = logging.getLogger(__name__)


def _are_there_uncommited_changes() -> bool:
    """Check if there are any committed changes in the current git repository.

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
    """Internal helper function to get the current git version.

    Returns:
        str: The version of git as a string (e.g., '2.3.4').

    Raises:
        SimpleGitToolError: If git is not installed or cannot be found.
    """
    try:
        # Run the git --version command and capture its output
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        # The output is typically "git version X.Y.Z", so we split to get the version number
        return result.stdout.strip().split()[-1]
    except FileNotFoundError:
        # This error occurs if the 'git' command is not found on the system
        raise SimpleGitToolError("Git is not installed or not in the system's PATH.")
    except subprocess.CalledProcessError:
        # This handles any other issues with running the command
        raise SimpleGitToolError("An unexpected error occurred while checking the git version.")


def _compare_versions(current_version: str, min_version: str) -> bool:
    """Internal helper function to compare two version strings.

    Args:
        current_version (str): The version of git currently installed.
        min_version (str): The minimum required version.

    Returns:
        bool: True if current_version is greater than or equal to min_version,
              False otherwise.
    """
    # Split the versions into a list of integers for comparison
    current_parts = [int(v) for v in re.findall(r"\d+", current_version)]
    min_parts = [int(v) for v in re.findall(r"\d+", min_version)]

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
        # console.print(f"Latest tag: [bold cyan]{latest_tag}[/bold cyan]")

    except subprocess.CalledProcessError:
        # console.print("[bold yellow]No tags found in the repository.[/bold yellow]")
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
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, capture_output=True, text=True)

        # Get the branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            # The shell=True argument can be a security risk if the command
            # string comes from untrusted user input, but here it's
            # a hardcoded command so it's safe.
            shell=False,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        # Return an empty string or handle the error as appropriate
        return ""
    except FileNotFoundError:
        print("Git command not found. Please ensure Git is installed and in your system's PATH.")
        return ""


def get_branch_info(branch_name: str) -> str:
    """Retrieves the author of the most recent commit on a given Git branch."""
    try:
        # Step 1: Check if the branch exists and get its latest commit hash.
        # `check=True` will raise an exception if the command fails (e.g., branch not found).
        # `capture_output=True` captures stdout and stderr.
        # `text=True` decodes the output as a string.
        commit_hash_result = subprocess.run(
            ["git", "rev-parse", branch_name],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = commit_hash_result.stdout.strip()

        # Step 2: Get the author of the commit.
        # The `--pretty=format:'%an'` flag formats the output to just the author's name.
        formatting = '{"hash": "%h", "author": "%an", "email": "%ce", "date": "%ad"}'
        author_result = subprocess.run(
            ["git", "log", "-1", f"--pretty=format:{formatting}", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )
        return author_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        # If `git rev-parse` failed, it's likely because the branch doesn't exist.
        # The stderr output usually contains "unknown revision or path not in the working tree".
        if "unknown revision" in e.stderr or "not in the working tree" in e.stderr:
            raise ValueError(f"Error: The branch '{branch_name}' does not exist.") from e
        # Re-raise the exception if the error is for another reason.
        raise e


def get_author(branch_name: str) -> str:
    """Retrieves the author of the most recent commit on a given Git branch.

    This function uses subprocess calls to execute Git commands on the local
    repository. It first checks if the branch exists and then retrieves the
    author of the last commit.

    Args:
        branch_name: The name of the Git branch (e.g., "main", "feature/my-branch").

    Returns:
        The name of the author as a string.

    Raises:
        ValueError: If the specified branch does not exist in the repository.
        subprocess.CalledProcessError: If a Git command fails for another reason
                                      (e.g., not a Git repository, Git not installed).
    """
    try:
        # Step 1: Check if the branch exists and get its latest commit hash.
        # `check=True` will raise an exception if the command fails (e.g., branch not found).
        # `capture_output=True` captures stdout and stderr.
        # `text=True` decodes the output as a string.
        commit_hash_result = subprocess.run(
            ["git", "rev-parse", branch_name],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = commit_hash_result.stdout.strip()

        # Step 2: Get the author of the commit.
        # The `--pretty=format:'%an'` flag formats the output to just the author's name.
        formatting = "%an"
        author_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%an", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )
        return author_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        # If `git rev-parse` failed, it's likely because the branch doesn't exist.
        # The stderr output usually contains "unknown revision or path not in the working tree".
        if "unknown revision" in e.stderr or "not in the working tree" in e.stderr:
            raise ValueError(f"Error: The branch '{branch_name}' does not exist.") from e
        # Re-raise the exception if the error is for another reason.
        raise e


def check_out_and_pull(branch: str, check: bool = True) -> None:
    subprocess.run(["git", "checkout", branch], check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "pull", "origin", branch], check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _get_merged_branches(base: str) -> list:
    result = subprocess.run(
        ["git", "branch", "-r", "--merged", base],
        capture_output=True,
        text=True,
        check=True,
    )
    # Process and display merged branches
    merged_branches = []
    for line in result.stdout.strip().split("\n"):
        branch_name = line.strip()
        if branch_name and not branch_name.startswith("*") and f"origin/{base}" not in branch_name:
            # Remove the asterisk from the current branch if present
            branch_name = branch_name.replace("* ", "")
            branch_name = branch_name.replace("origin/", "")
            merged_branches.append(branch_name)
    return merged_branches


def _get_unmerged_branches(base: str) -> list[BranchSchema]:
    unmerged_branches = []
    result = subprocess.run(
        ["git", "branch", "-r", "--no-merged", base],
        capture_output=True,
        text=True,
        check=True,
    )
    # Process and display unmerged branches
    try:
        for line in result.stdout.strip().split("\n"):
            clean_line = line.strip()
            branch_dict = branch_line_to_dict(clean_line)

            unmerged_branches.append(BranchSchema(**branch_dict))
    except ValueError as e:
        logger.debug("Branch not found: %s", e)
    sorted_branches = sorted(
        unmerged_branches, reverse=True
    )
    return sorted_branches


def branch_line_to_dict(branch_name: str) -> dict[str, Any]:
    logger.debug("Branch found: %s", branch_name)
    branch_info = get_branch_info(branch_name)
    logger.debug("Branch info: %s", branch_info)
    branch_dict = json.loads(branch_info)
    branch_dict["name"] = branch_name.replace("origin/", "")
    branch_dict["date"] = parse_git_date(branch_dict["date"])
    logger.debug("Branch info: %s", branch_dict)
    return branch_dict

def display_branches(branches: list[BranchSchema]) -> None:
    for i, branch in enumerate(branches, 1):

        CLI_CONSOLE.print(f" {i} [yellow]{branch.name}[/yellow] {branch.date}(by [blue]{branch.author}[/blue])")