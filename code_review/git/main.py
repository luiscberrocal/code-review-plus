import subprocess
import re
import sys
import click
from rich.console import Console

import os
from pathlib import Path
# Initialize the console for rich
console = Console()

class SimpleGitToolError(Exception):
    """
    A custom exception class for handling errors in the simple git tool.
    This provides more specific and user-friendly error messages.
    """
    pass

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

@click.group()
def cli():
    """A simple command-line tool for git operations."""
    pass

@cli.group()
def git():
    """Tools for interacting with Git repositories."""
    pass

@git.command()
@click.option('--version', 'min_version', help='The minimum required git version.', default=None)
def check(min_version: str):
    """
    Checks if git is installed and meets the minimum version requirement.
    """
    try:
        current_version = _get_git_version()
        if min_version:
            if not _compare_versions(current_version, min_version):
                # If the version is less than the minimum, raise an error
                raise SimpleGitToolError(
                    f"Git version {current_version} is less than the required minimum version {min_version}."
                )
            console.print("[bold green]Git is installed and meets the minimum version requirement.[/bold green]")
        else:
            console.print("[bold green]Git is installed.[/bold green]")

        console.print(f"Current version: [cyan]{current_version}[/cyan]")

    except SimpleGitToolError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@git.command()
@click.option(
    "--folder", "-f", type=Path, help="Path to the git repository", default=None
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed diff information", default=False)
def sync(folder: Path, verbose: bool):
    """
    Syncs the master and develop branches, ensuring consistency.

    Args:
        folder: Path to the git repository. If not provided, uses current directory.
        verbose: If True, shows detailed diff information.
    """
    # Store original directory to return to it later
    original_dir = os.getcwd()
    try:

        console.print("[bold cyan]Starting branch synchronization...[/bold cyan]")
        # Change to the specified directory if provided
        if folder:
            if not folder.exists():
                raise SimpleGitToolError(f"Directory does not exist: {folder}")
            if not folder.is_dir():
                raise SimpleGitToolError(f"Not a directory: {folder}")

            console.print(f"Changing to directory: [cyan]{folder}[/cyan]")
            os.chdir(folder)

        uncommited_changes = _are_there_uncommited_changes()
        if uncommited_changes:
            console.print(
                "[bold red]ERROR: There are uncommitted changes in the repository.[/bold red]"
            )
            sys.exit(1)

        # Define the branches to sync
        master_branch = "master"
        develop_branch = "develop"

        # 1. Checkout master and pull
        console.print(
            f"[bold]Checking out and pulling [green]{master_branch}[/green]...[/bold]"
        )
        subprocess.run(["git", "checkout", master_branch], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "pull", "origin", master_branch], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        latest_tag = _get_latest_tag()
        # 2. Checkout develop and pull
        console.print(
            f"[bold]Checking out and pulling [green]{develop_branch}[/green]...[/bold]"
        )
        subprocess.run(["git", "checkout", develop_branch], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "pull", "origin", develop_branch], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Do a git diff and check for differences
        console.print(
            "[bold]Checking for differences between develop and master...[/bold]"
        )
        result = subprocess.run(
            ["git", "diff", "--name-only", master_branch, develop_branch],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip():
            # If the diff command returns any output, it means there are differences.
            diff_files = result.stdout.strip().split("\n")
            console.print(
                "[bold red]ERROR: Differences found between develop and master.[/bold red]"
            )
            if verbose:
                for file in diff_files:
                    console.print(f" - [yellow]{file}[/yellow]")
            raise SimpleGitToolError(
                "Please merge changes from master into develop before syncing."
            )

        console.print(
            "[bold green]develop and master branches are in sync.[/bold green]"
        )

        # 4. Get the latest tag
        # console.print("[bold]Getting the latest tag...[/bold]")
        console.print(f"Latest tag: [bold cyan]{latest_tag}[/bold cyan]")

        console.print("[bold green]Synchronization complete![/bold green]")

    except subprocess.CalledProcessError as e:
        # Catch any git command failures and raise a custom error
        console.print(
            "[bold red]Error:[/bold red] Git command failed. Check the repository state."
        )
        console.print(f"[red]Command:[/red] {e}")
        console.print(f"[red]Details:[/red]\n{e.stderr.strip()}")
        sys.exit(1)
    except SimpleGitToolError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    finally:
        # Change back to the original directory if we changed it
        if folder:
            os.chdir(original_dir)


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


if __name__ == '__main__':
    # The `cli` entry point is handled by the click library,
    # so we just need to call it.
    cli()
