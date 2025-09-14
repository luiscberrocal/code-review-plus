import logging
import re
import subprocess
import sys
from datetime import datetime

from code_review.schemas import BranchSchema

logger = logging.getLogger(__name__)


def create_branch_schema(git_line: str) -> BranchSchema:
    """Create a BranchSchema instance.

    Luis C. Berrocal Wed Jun 11 13:33:34 2025 -0500 Merge branch 'feature/vpop-211_refactoring' into develop
    """
    regex_pattern = re.compile(
        r"^(?P<name>[\w\s.]+) "  # Match the name (one or more words and spaces, with periods)
        r"(?P<date>[A-Za-z]{3}\s+[A-Za-z]{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\d{4}\s+[-+]\d{4}) "  # Match the full date format
        r"Merge\s+(?:branch|tag)\s+'?(?P<branch>[^']+)'?\s+into\s+'?(?P<target_branch>.*)'?$"
        # Match 'Merge branch/tag 'branch' into 'target''
    )
    match = regex_pattern.match(git_line)
    if match:
        data = match.groupdict()
        name = match.group("name").strip()
        date = match.group("date").strip()
        branch = match.group("branch").strip()
        date_string = data["date"]
        try:
            # Use strptime to parse the date string based on the known format.
            parsed_date = datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y %z")
        except ValueError as e:
            logger.error(f"Error parsing date string '%s': %s",
                         date_string, e)
            parsed_date = None
        return BranchSchema(name=branch, author=name, date=parsed_date)
    raise ValueError(f"Invalid git line format: {git_line}")


def parse_git_date(date_str: str) -> datetime | None:
    """Parses a Git date string with a timezone offset into a datetime object.

    Args:
        date_str: A string in the format 'Mon Apr 21 10:20:20 2025 -0400'.

    Returns:
        A datetime object if the parsing is successful, otherwise None.
    """
    # The format string for datetime.strptime to match the Git date format.
    # %a: Weekday as locale’s abbreviated name (e.g., 'Mon').
    # %b: Month as locale’s abbreviated name (e.g., 'Apr').
    # %d: Day of the month as a zero-padded decimal number (e.g., '21').
    # %H:%M:%S: Hour, minute, and second.
    # %Y: Year with century (e.g., '2025').
    # %z: UTC offset in the form ±HHMM (e.g., '-0400').
    format_string = "%a %b %d %H:%M:%S %Y %z"

    try:
        # Attempt to parse the date string using the specified format.
        parsed_date = datetime.strptime(date_str, format_string)
        return parsed_date
    except ValueError as e:
        # If parsing fails, print an error message and return None.
        logger.debug("Error parsing date string '%s': %s", date_str, e)
        return None


def is_rebased(target_branch: str, base_branch: str) -> bool:
    """Verifies if a target Git branch has been rebased against a base branch.

    This is determined by checking if the merge base (common ancestor) of the
    two branches is the same as the head of the base branch. If they are the
    same, it means all commits on the target branch are descendants of the
    base branch's current head, which is the result of a successful rebase.

    Args:
        target_branch: The name of the branch to check (e.g., 'feature/my-branch').
        base_branch: The name of the base branch (e.g., 'develop').

    Returns:
        True if the target branch has been rebased against the base branch,
        False otherwise.
    """
    try:
        # Get the commit hash of the merge base between the two branches.
        # This is the most recent common ancestor.
        merge_base_result = subprocess.run(
            ["git", "merge-base", target_branch, base_branch], capture_output=True, text=True, check=True
        )
        merge_base_hash = merge_base_result.stdout.strip()

        # Get the commit hash of the head of the base branch.
        base_branch_head_result = subprocess.run(
            ["git", "rev-parse", base_branch], capture_output=True, text=True, check=True
        )
        base_branch_head_hash = base_branch_head_result.stdout.strip()

        # The branch is considered rebased if the merge base is the same as
        # the head of the base branch.
        return merge_base_hash == base_branch_head_hash

    except subprocess.CalledProcessError as e:
        # Handle cases where a branch does not exist or git command fails.
        logger.error(f"Error executing git command: %s",
                     e)
        return False
    except FileNotFoundError:
        logger.error("Error: 'git' command not found. Please ensure Git is installed and in your PATH.")
        return False
