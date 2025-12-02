from pathlib import Path

from code_review.plugins.readme.handlers import check_admin_console_urls
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import RulesResult


def check(code_review: CodeReviewSchema) -> list[RulesResult]:
    """Check if there are requirements to update in the code review schema.

    Args:
        code_review: The CodeReviewSchema object containing branch information.
    """
    readme_file = code_review.readme_file
    if not readme_file.exists():
        return [
            RulesResult(
                name="README Admin Console URL Check",
                passed=False,
                level="ERROR",
                message=f"README file not found at {readme_file}",
            )
        ]

    readme_content = readme_file.read_text()
    results = []
    urls = check_admin_console_urls(readme_content)
    if urls:
        for url in urls:
            results.append(
                RulesResult(
                    name="README Admin Console URL Check",
                    passed=True,
                    level="INFO",
                    message=f"Found Admin Console URL: {url}",
                )
            )
    else:
        results.append(
            RulesResult(
                name="README Admin Console URL Check",
                passed=False,
                level="WARNING",
                message="No Production or Staging Admin Console URLs found in the README.",
            )
        )
    if len(results) == 1:
        results.append(
            RulesResult(
                name="README Admin Console URL Check",
                passed=False,
                level="WARNING",
                message="Missing either Production or Staging Admin Console URL in the README.",
            )
        )
    return results


def check_urls_in_readme_legacy(readme_file: Path) -> list[RulesResult]:
    """Checks for Production and Staging Admin Console URLs in the README content."""
    if not readme_file.exists():
        return [
            RulesResult(
                name="README Admin Console URL Check",
                passed=False,
                level="ERROR",
                message=f"README file not found at {readme_file}",
            )
        ]

    readme_content = readme_file.read_text()
    results = []
    urls = check_admin_console_urls(readme_content)
    if urls:
        for url in urls:
            results.append(
                RulesResult(
                    name="README Admin Console URL Check",
                    passed=True,
                    level="INFO",
                    message=f"Found Admin Console URL: {url}",
                )
            )
    else:
        results.append(
            RulesResult(
                name="README Admin Console URL Check",
                passed=False,
                level="WARNING",
                message="No Production or Staging Admin Console URLs found in the README.",
            )
        )
    if len(results) == 1:
        results.append(
            RulesResult(
                name="README Admin Console URL Check",
                passed=False,
                level="WARNING",
                message="Missing either Production or Staging Admin Console URL in the README.",
            )
        )
    return results
