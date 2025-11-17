from datetime import datetime
from pathlib import Path

from code_review.enums import ReviewRuleLevelIcon
from code_review.review.schemas import CodeReviewSchema


def write_review(review: CodeReviewSchema, folder: Path) -> Path:
    """Writes the code review report to a markdown file in the specified folder.

    Args:
        review: The CodeReviewSchema object containing the review data.
        folder: The Path object for the directory to write the report to.
    """
    errors_and_warnings = [rule for rule in review.rules_validated if not rule.passed or rule.level == "WARNING"]
    passed_rules = [rule for rule in review.rules_validated if rule.passed and rule.level != "WARNING"]

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = folder / f"{review.ticket}_{review.name}_code_review_report_{timestamp}.md"
    with report_path.open("w", encoding="utf-8") as report_file:
        report_file.write(f"# Code Review Report: {review.name}\n\n")
        report_file.write(f"**Engineer**: {review.target_branch.author}\n")
        report_file.write(f"**Ticket**: {review.ticket}\n")


        report_file.write("### Summary\n")
        report_file.write(f"- Target Branch Linting Errors: {review.target_branch.linting_errors}\n")
        report_file.write(f"- Base Branch Linting Errors: {review.base_branch.linting_errors}\n\n")

        report_file.write("## Rules Validated\n")
        report_file.write(f"### To Fix\n")
        for rule in errors_and_warnings:
            status = f"{ReviewRuleLevelIcon.WARNING.value}" if rule.passed else f"{ReviewRuleLevelIcon.ERROR.value}"
            report_file.write(f"- **{status} {rule.name}**: - {rule.message}\n")

        report_file.write(f"### Passed\n")
        for rule in passed_rules:
            status = f"{ReviewRuleLevelIcon.INFO.value}" if rule.passed else f"{ReviewRuleLevelIcon.ERROR.value}"
            report_file.write(f"- **{status} {rule.name}**: - {rule.message}\n")

    return report_path
