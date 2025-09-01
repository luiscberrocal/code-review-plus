from code_review.review.schemas import CodeReviewSchema

from code_review.settings import OUTPUT_FOLDER, CLI_CONSOLE

def display_review(review: CodeReviewSchema):
    """Display the details of a code review."""
    CLI_CONSOLE.print(f"[bold blue]Code Review for Project:[/bold blue] {review.name}")
    CLI_CONSOLE.print(f"[bold blue]Branch: {review.target_branch.name}[/bold blue]")
    if  review.target_branch.linting_errors > review.base_branch.linting_errors:
        CLI_CONSOLE.print(f"[bold red]Linting Issues Increased![/bold red] base has "
                          f"{review.base_branch.linting_errors} while {review.target_branch.name} "
                          f"has {review.target_branch.linting_errors}" )