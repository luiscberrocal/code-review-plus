from pathlib import Path

import click

from code_review.adapters.generics import parse_for_ticket
from code_review.cli import cli
from code_review.git.adapters import is_rebased
from code_review.git.handlers import _get_unmerged_branches, display_branches
from code_review.handlers.file_handlers import ch_dir
from code_review.review.adapters import build_code_review_schema
from code_review.review.handlers import display_review, write_review_to_file
from code_review.settings import CLI_CONSOLE, OUTPUT_FOLDER


@cli.group()
def review() -> None:
    """Tools for code review."""
    pass


@review.command()
@click.option("--folder", "-f", type=Path, help="Path to the git repository", default=None)
@click.option("--author", "-a", type=str, help="Name of the author", default=None)
def make(folder: Path, author:str) -> None:
    """List branches in the specified Git repository."""
    ch_dir(folder)
    unmerged_branches = _get_unmerged_branches("master", author_pattern=author)
    if not unmerged_branches:
        click.echo("No unmerged branches found.")
        return
    display_branches(unmerged_branches)
    branch_num = click.prompt("Select a branch by number", type=int)
    selected_branch = unmerged_branches[branch_num - 1]
    click.echo(f"You selected branch: {selected_branch.name}")

    code_review_schema = build_code_review_schema(folder, selected_branch.name)

    ticket_number = parse_for_ticket(selected_branch.name)

    ticket = ticket_number or click.prompt("Select a ticket by number", type=str)

    code_review_schema.ticket = ticket
    base_branch_to_check = "develop"
    if code_review_schema.target_branch.name.startswith("hotfix"):
        base_branch_to_check = "master"

    code_review_schema.is_rebased = is_rebased(code_review_schema.target_branch.name, base_branch_to_check)

    display_review(code_review_schema, base_branch_name=base_branch_to_check)

    new_file, backup_file = write_review_to_file(review=code_review_schema, folder=OUTPUT_FOLDER)
    CLI_CONSOLE.print("[bold blue]Code review written to:[/bold blue] " + str(new_file))
