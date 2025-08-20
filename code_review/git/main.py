import subprocess
import sys
import click
from rich.console import Console

import os
from pathlib import Path

from code_review.exceptions import SimpleGitToolError
from code_review.git.handlers import _are_there_uncommited_changes, _get_git_version, _compare_versions, _get_latest_tag

# Initialize the console for rich
console = Console()


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

@git.command()
@click.option("--folder", "-f", type=Path, help="Path to the git repository", default=None)
@click.option("--merged", is_flag=True, help="List branches that are merged into master", default=False)
@click.option("--un-merged", is_flag=True, help="List branches that are not merged into master", default=False)
@click.option("--delete", is_flag=True, help="Delete merged branches (use with --merged)", default=False)
@click.option("--interactive", is_flag=True, help="Ask before deleting (use with --merged --delete)", default=False)
@click.option("--base", help="Base branch to compare against", default="master")
def branch(folder: Path, merged: bool, un_merged: bool, delete: bool, base: str, interactive: bool):
    """
    Lists merged or unmerged branches relative to a base branch (default: master).
    Can also delete merged branches.

    Args:
        folder: Path to the git repository. If not provided, uses current directory.
        merged: List branches that are merged into the base branch.
        interactive: Ask before deleting branches (only works with --merged and --delete).
        un_merged: List branches that are not merged into the base branch.
        delete: Delete merged branches (only works with --merged flag).
        base: Base branch to compare against (default: master).
    """
    # Store original directory to return to it later
    original_dir = os.getcwd()
    try:
        # Validate options
        if not merged and not un_merged:
            raise SimpleGitToolError("Please specify either --merged or --un-merged")

        if delete and not merged:
            raise SimpleGitToolError("--delete option requires --merged flag")

        # Change to the specified directory if provided
        if folder:
            if not folder.exists():
                raise SimpleGitToolError(f"Directory does not exist: {folder}")
            if not folder.is_dir():
                raise SimpleGitToolError(f"Not a directory: {folder}")

            console.print(f"Changing to directory: [cyan]{folder}[/cyan]")
            os.chdir(folder)

        # Check if the base branch exists
        try:
            subprocess.run(
                ["git", "rev-parse", "--verify", base],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            raise SimpleGitToolError(f"Base branch '{base}' does not exist")

        # Get current branch to restore it later
        current_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        # Handle merged branches
        if merged:
            console.print(
                f"[bold cyan]Listing branches merged into [green]{base}[/green]:[/bold cyan]"
            )
            merged_branches = _get_merged_branches(base)
            for i, branch_name in enumerate(merged_branches, 1):
                console.print(f" {i}  [yellow]{branch_name}[/yellow]")

            # Delete merged branches if requested
            if delete and merged_branches:
                console.print("[bold]Deleting merged branches...[/bold]")
                for branch in merged_branches:
                    # Don't delete the current branch or protected branches
                    if branch != current_branch and branch != 'master' and branch != 'develop':
                        try:
                            do_delete = True
                            if interactive:
                                do_delete = click.confirm(f"Do you want to delete branch {branch}?", default=True)
                            if do_delete:
                                console.print(f"Deleting branch: [red]{branch}[/red]")
                                subprocess.run(
                                    ["git", "push", "origin", "--delete", branch],
                                    check=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL
                                )
                        except subprocess.CalledProcessError:
                            console.print(f"[yellow]Warning: Could not delete branch {branch}[/yellow]")
                    elif branch == current_branch:
                        console.print(f"[yellow]Skipping current branch: {branch}[/yellow]")
                    else:
                        console.print(f"[yellow]Skipping protected branch: {branch}[/yellow]")

            if not merged_branches:
                console.print("[bold green]No merged branches found.[/bold green]")

        # Handle unmerged branches
        if un_merged:
            console.print(f"[bold cyan]Listing branches not merged into [green]{base}[/green]:[/bold cyan]")
            result = subprocess.run(
                ["git", "branch", "--no-merged", base],
                capture_output=True,
                text=True,
                check=True
            )

            unmerged_branches = []
            for line in result.stdout.strip().split('\n'):
                branch_name = line.strip()
                if branch_name:
                    # Remove the asterisk from the current branch if present
                    branch_name = branch_name.replace('* ', '')
                    unmerged_branches.append(branch_name)
                    console.print(f" - [yellow]{branch_name}[/yellow]")

            if not unmerged_branches:
                console.print("[bold green]No unmerged branches found.[/bold green]")

    except subprocess.CalledProcessError as e:
        console.print("[bold red]Error:[/bold red] Git command failed.")
        console.print(f"[red]Details:[/red]\n{e.stderr.strip()}")
        sys.exit(1)
    except SimpleGitToolError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    finally:
        # Change back to the original directory if we changed it
        if folder:
            os.chdir(original_dir)


def _get_merged_branches(base: str) -> list:
    result = subprocess.run(
        ["git", "branch", "-r", "--merged", base],
        capture_output=True,
        text=True,
        check=True,
    )
    # Process and display merged branches
    merged_branches = []
    for line in result.stdout.strip().split('\n'):
        branch_name = line.strip()
        if branch_name and not branch_name.startswith('*') and f"origin/{base}" not in branch_name:
            # Remove the asterisk from the current branch if present
            branch_name = branch_name.replace('* ', '')
            branch_name = branch_name.replace('origin/', '')
            merged_branches.append(branch_name)
    return merged_branches


if __name__ == '__main__':
    # The `cli` entry point is handled by the click library,
    # so we just need to call it.
    cli()
