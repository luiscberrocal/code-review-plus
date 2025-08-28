import json
from pathlib import Path

import click

from code_review.cli import cli
from code_review.dependencies.pip.handlers import requirements_updated
from code_review.git.handlers import _get_unmerged_branches, display_branches
from code_review.handlers import ch_dir
from code_review.review.adapters import build_code_review_schema
from code_review.settings import OUTPUT_FOLDER, CLI_CONSOLE


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
    if not unmerged_branches:
        click.echo("No unmerged branches found.")
        return
    display_branches(unmerged_branches)
    branch_num = click.prompt("Select a branch by number", type=int)
    selected_branch = unmerged_branches[branch_num - 1]
    click.echo(f"You selected branch: {selected_branch.name}")
    schema = build_code_review_schema(folder, selected_branch.name)
    ticket= click.prompt("Select a ticket by number", type=str)
    schema.ticket = ticket
    updated = requirements_updated(folder)
    if updated:
        CLI_CONSOLE.print("[green]Updated packages:[/green]")
        for pkg in updated:
            CLI_CONSOLE.print(f"- {pkg['library']}: {pkg['old_version']} -> {pkg['new_version']}")

    file = OUTPUT_FOLDER / f"{schema.name}_code_review.json"
    with open(file, "w") as f:
        json.dump(schema.model_dump(), f, indent=4, default=str)
    print(f"Wrote code review schema to {file}")
