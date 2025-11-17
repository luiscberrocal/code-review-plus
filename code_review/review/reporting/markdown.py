from datetime import datetime
from pathlib import Path

from code_review.review.schemas import CodeReviewSchema


def write_review(review: CodeReviewSchema, folder: Path) -> Path:
    """Writes the code review report to a markdown file in the specified folder.

    Args:
        review: The CodeReviewSchema object containing the review data.
        folder: The Path object for the directory to write the report to.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = folder / f"{review.ticket}_{review.name}_code_review_report_{timestamp}.md"
    with report_path.open("w", encoding="utf-8") as report_file:
        report_file.write(f"# Code Review Report: {review.name}\n\n")
        report_file.write(f"## Target Branch: {review.target_branch.name}\n")
        report_file.write(f"## Base Branch: {review.base_branch.name}\n\n")

        report_file.write("### Summary\n")
        report_file.write(f"- Target Branch Linting Errors: {review.target_branch.linting_errors}\n")
        report_file.write(f"- Base Branch Linting Errors: {review.base_branch.linting_errors}\n\n")

        report_file.write("### Rules Validated\n")
        for rule in review.rules_validated:
            status = "Passed" if rule.passed else "Failed"
            report_file.write(f"- **{rule.name}**: {status} - {rule.message}\n")

    return report_path
