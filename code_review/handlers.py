import os
from pathlib import Path

from code_review.exceptions import SimpleGitToolError
from code_review.settings import CLI_CONSOLE


def ch_dir(folder: Path) -> None:
    if folder:
        if not folder.exists():
            raise SimpleGitToolError(f"Directory does not exist: {folder}")
        if not folder.is_dir():
            raise SimpleGitToolError(f"Not a directory: {folder}")

        CLI_CONSOLE.print(f"Changing to directory: [cyan]{folder}[/cyan]")
        os.chdir(folder)
