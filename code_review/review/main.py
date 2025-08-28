from pathlib import Path

import click

from code_review.cli import cli
from code_review.git.handlers import _get_unmerged_branches, display_branches
from code_review.handlers import ch_dir


@cli.group()
def review() -> None:
    """Tools for code review."""
    pass

@review.command()
@click.option("--folder", "-f", type=Path, help="Path to the git repository", default=None)
def make(folder: Path) -> None:
    """List branches in the specified Git repository."""
    ch_dir(folder)
    unmerged_branches = _get_unmerged_branches("master")
    display_branches(unmerged_branches)
    branch_num = click.prompt("Select a branch by number", type=int)
    selected_branch = unmerged_branches[branch_num - 1]
    click.echo(f"You selected branch: {selected_branch}")
