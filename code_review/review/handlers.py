import json
from datetime import datetime
from pathlib import Path

from code_review.review.schemas import CodeReviewSchema
from code_review.settings import CLI_CONSOLE

import logging
logger = logging.getLogger(__name__)


def display_review(review: CodeReviewSchema, base_branch_name: str = "develop") -> None:
    """Display the details of a code review."""
    CLI_CONSOLE.print(f"[bold blue]Code Review for Project:[/bold blue] {review.name}")
    CLI_CONSOLE.print(f"[bold blue]Branch: {review.target_branch.name}[/bold blue]")
    if review.is_rebased:
        CLI_CONSOLE.print(
            f"[bold green]Branch {review.target_branch.name} is rebased on {base_branch_name}.[/bold green]"
        )
    else:
        CLI_CONSOLE.print(
            f"[bold red]Branch {review.target_branch.name} is not rebased on {base_branch_name}![/bold red]"
        )

    if review.target_branch.linting_errors > review.base_branch.linting_errors:
        CLI_CONSOLE.print(
            f"[bold red]Linting Issues Increased![/bold red] base has "
            f"{review.base_branch.linting_errors} while {review.target_branch.name} "
            f"has {review.target_branch.linting_errors}"
        )
    elif review.target_branch.linting_errors == review.base_branch.linting_errors and review.target_branch.linting_errors != 0:
        CLI_CONSOLE.print(
            f"[bold yellow]Linting Issues Stayed the Same![/bold yellow] base has "
            f"{review.base_branch.linting_errors} while {review.target_branch.name} "
            f"has {review.target_branch.linting_errors}"
        )
    else:
        CLI_CONSOLE.print(
            f"[bold green]Linting Issues Decreased or Stayed the Same.[/bold green] base has "
            f"{review.base_branch.linting_errors} while {review.target_branch.name} "
            f"has {review.target_branch.linting_errors}"
        )

    requirements_pending_update_count = len(review.target_branch.requirements_to_update)
    if requirements_pending_update_count > 0:
        CLI_CONSOLE.print(
            f"[bold red]Dependencies to Update:[/bold red] {requirements_pending_update_count} need updates."
        )
    else:
        CLI_CONSOLE.print("[bold green]No Dependencies to Update![/bold green]")

    for dockerfile in review.docker_files or []:
        if dockerfile.version != dockerfile.expected_version:
            CLI_CONSOLE.print(
                f"[bold red]Dockerfile {dockerfile.file.relative_to(review.source_folder)} need to be "
                f"updated {dockerfile.version} -> {dockerfile.expected_version}:[/bold red]"
            )
        else:
            CLI_CONSOLE.print(f"[bold green]Dockerfile {dockerfile.file.relative_to(review.source_folder)} has "
                              f"is up to date ![/bold green]")

    if review.target_branch.formatting_errors != 0:
        CLI_CONSOLE.print(
            f"[bold red]Code Formatting Issues Detected![/bold red] {review.target_branch.formatting_errors} files need formatting."
        )
    else:
        CLI_CONSOLE.print("[bold green]All Files Properly Formatted![/bold green]")


    logger.info("Review Details: %s", review.target_branch.changelog_versions)
    logger.info("Review version: %s", review.target_branch.version)

    if len(review.target_branch.changelog_versions) == 0 or review.target_branch.version is None:
        logger.error("Skipping version check due to missing information")
        return

    changelog_latest_version = review.target_branch.changelog_versions[0]
    logger.debug("Latest changelog version: %s", changelog_latest_version)
    if review.target_branch.version < changelog_latest_version:
        CLI_CONSOLE.print(f"[bold green]Versioning is correct expected to move from {review.target_branch.version} "
                          f"to {changelog_latest_version}![/bold green] ")
    else:
        CLI_CONSOLE.print(f"[bold red]Versioning is not correct expected to move from {review.target_branch.version} "
                          f"to {changelog_latest_version}![/bold red] ")


def write_review_to_file(review: CodeReviewSchema, folder: Path) -> tuple[Path, Path | None]:
    """Write the code review details to a JSON file."""
    file = folder / f"{review.ticket}-{review.name}_code_review.json"
    backup_file = None
    if file.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = folder / f"{review.ticket}-{review.name}_code_review_{timestamp}.json"
        file.rename(backup_file)

    with open(file, "w") as f:
        json.dump(review.model_dump(), f, indent=4, default=str)

    return file, backup_file
