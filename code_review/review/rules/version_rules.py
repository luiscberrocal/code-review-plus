from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import RulesResult


def check(code_review: CodeReviewSchema) -> list[RulesResult]:
    """Check if the target branch has a version in the changelog greater than the base branch.

    Args:
        code_review: The CodeReviewSchema object containing the branches to compare.

    Returns:
        True if the target branch has a greater version in the changelog, False otherwise.
    """
    rules = []
    if len(code_review.base_branch.changelog_versions) == 0:
        rules.append(
            RulesResult(
                name="Versioning",
                passed=False,
                level="WARNING",
                message=f"No versions found in the changelog of the base {code_review.base_branch.name} branch.",
            )
        )
    if len(code_review.target_branch.changelog_versions) == 0:
        rules.append(
            RulesResult(
                name="Versioning",
                passed=False,
                level="WARNING",
                message=f"No versions found in the changelog of the target {code_review.target_branch.name} branch.",
            )
        )
    if len(code_review.base_branch.changelog_versions) > 0 and len(code_review.target_branch.changelog_versions) > 0:
        if code_review.target_branch.changelog_versions[0] > code_review.base_branch.changelog_versions[0]:
            rules.append(
                RulesResult(
                    name="Versioning",
                    passed=True,
                    level="INFO",
                    message=(
                        f"Target branch {code_review.target_branch.name} has a greater version "
                        f"({code_review.target_branch.changelog_versions[0].major}."
                        f"{code_review.target_branch.changelog_versions[0].minor}."
                        f"{code_review.target_branch.changelog_versions[0].patch}) in the changelog "
                        f"than the base branch {code_review.base_branch.name} "
                        f"({code_review.base_branch.changelog_versions[0].major}."
                        f"{code_review.base_branch.changelog_versions[0].minor}."
                        f"{code_review.base_branch.changelog_versions[0].patch})."
                    ),
                )
            )
        else:
            rules.append(
                RulesResult(
                    name="Versioning",
                    passed=False,
                    level="CRITICAL",
                    message=(
                        f"Target branch {code_review.target_branch.name} does not have a greater version "
                        f"in the changelog than the base branch {code_review.base_branch.name}. "
                        f"Current versions are: "
                        f"{code_review.base_branch.name} - {code_review.base_branch.changelog_versions[0].major}."
                        f"{code_review.base_branch.changelog_versions[0].minor}."
                        f"{code_review.base_branch.changelog_versions[0].patch}, "
                        f"{code_review.target_branch.name} - {code_review.target_branch.changelog_versions[0].major}."
                        f"{code_review.target_branch.changelog_versions[0].minor}."
                        f"{code_review.target_branch.changelog_versions[0].patch}."
                    ),
                )
            )
    return rules
