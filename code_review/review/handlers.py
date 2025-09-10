import json
from datetime import datetime
from pathlib import Path

from code_review.review.schemas import CodeReviewSchema
from code_review.settings import CLI_CONSOLE


def display_review(review: CodeReviewSchema):
    """Display the details of a code review."""
    CLI_CONSOLE.print(f"[bold blue]Code Review for Project:[/bold blue] {review.name}")
    CLI_CONSOLE.print(f"[bold blue]Branch: {review.target_branch.name}[/bold blue]")
    if review.is_rebased:
        CLI_CONSOLE.print(f"[bold green]Branch {review.target_branch.name} is rebased on develop.[/bold green]")
    else:
        CLI_CONSOLE.print(f"[bold red]Branch {review.target_branch.name} is not rebased on develop![/bold red]")
        
    if  review.target_branch.linting_errors > review.base_branch.linting_errors:
        CLI_CONSOLE.print(f"[bold red]Linting Issues Increased![/bold red] base has "
                          f"{review.base_branch.linting_errors} while {review.target_branch.name} "
                          f"has {review.target_branch.linting_errors}" )
    else:
        CLI_CONSOLE.print(f"[bold green]Linting Issues Decreased or Stayed the Same.[/bold green] base has "
                          f"{review.base_branch.linting_errors} while {review.target_branch.name} "
                          f"has {review.target_branch.linting_errors}" )

    requirements_pending_update_count = len(review.target_branch.requirements_to_update)
    if requirements_pending_update_count > 0:
        CLI_CONSOLE.print(f"[bold red]Dependencies to Update:[/bold red] "
                          f"{requirements_pending_update_count} need updates.")
    else:
        CLI_CONSOLE.print(f"[bold green]No Dependencies to Update![/bold green]")


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
