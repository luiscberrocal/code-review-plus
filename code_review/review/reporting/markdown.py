from datetime import datetime
from pathlib import Path

from code_review.enums import ReviewRuleLevelIcon
from code_review.review.schemas import CodeReviewSchema


def write_review(review: CodeReviewSchema, folder: Path) -> tuple[Path, Path | None]:
    """Writes the code review report to a markdown file in the specified folder.

    Args:
        review: The CodeReviewSchema object containing the review data.
        folder: The Path object for the directory to write the report to.
    """
    report_path = folder / f"{review.ticket}-{review.name}_code_review.md"
    backup_file = None
    if report_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = folder / f"{review.ticket}-{review.name}_code_review_{timestamp}.json"
        report_path.rename(backup_file)

    errors_and_warnings = [rule for rule in review.rules_validated if not rule.passed or rule.level == "WARNING"]
    passed_rules = [rule for rule in review.rules_validated if rule.passed and rule.level != "WARNING"]

    with report_path.open("w", encoding="utf-8") as report_file:
        report_file.write(f"# Code Review Report: {review.name}\n\n")
        report_file.write(f"**Engineer**: {review.target_branch.author}\n\n")
        report_file.write(f"**Ticket**: {review.ticket}\n\n")
        report_file.write(f"**Branch**: {review.target_branch.name}\n\n")


        report_file.write("## Rules Validated\n")
        report_file.write("### To Fix\n")
        for rule in errors_and_warnings:
            status = f"{ReviewRuleLevelIcon.WARNING.value}" if rule.passed else f"{ReviewRuleLevelIcon.ERROR.value}"
            report_file.write(f"- **{status} {rule.name}**: - {rule.message}\n")

        report_file.write("### Passed\n")
        for rule in passed_rules:
            status = f"{ReviewRuleLevelIcon.INFO.value}" if rule.passed else f"{ReviewRuleLevelIcon.ERROR.value}"
            report_file.write(f"- **{status} {rule.name}**: - {rule.message}\n")

    return report_path, backup_file
