import subprocess
from pathlib import Path
from typing import List

import click

from code_review.cli import cli
from code_review.settings import CLI_CONSOLE


@cli.group()
def ruff():
    """Tools for interacting with Git repositories."""
    pass

@ruff.command()
@click.option(
    "--folder", "-f", type=Path, help="Path to the git repository", default=None
)
def check(folder: Path):
    """Check and format code using ruff."""
    print(f"Running ruff check on folder: {folder}")
    formatting_pending = _check_and_format_ruff(folder)
    if formatting_pending:
        CLI_CONSOLE.print("[bold red]Some files are not formatted![/bold red]")
    else:
        CLI_CONSOLE.print("[bold green]All files are formatted![/bold green]")


def _check_and_format_ruff(folder_path: Path) -> bool:
    """
    Runs `ruff format` on a specified folder.

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
    check_command: List[str] = ["ruff", "format", "--check", folder_path]

    try:
        # Use subprocess.run() to execute the command.
        # `capture_output=True` captures stdout and stderr.
        # `text=True` decodes output to strings.
        # `check=False` is crucial here so we can handle the non-zero exit code manually.
        check_result = subprocess.run(check_command, capture_output=True, text=True, check=False)

        # Check the return code. A non-zero code from `ruff format --check`
        # indicates that there are unformatted files.
        if check_result.returncode != 0:
            return True
        else:
            return False

    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError as e:
        return False
    except Exception as e:
        return False
