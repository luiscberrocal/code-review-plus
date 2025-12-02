from code_review.enums import ReviewRuleLevel
from code_review.exceptions import CodeReviewError
from code_review.plugins.gitlab.ci.handlers import handle_multi_targets
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import RulesResult


def check(code_review: CodeReviewSchema) -> list[RulesResult]:
    """Validate GitLab CI rules in the given file.

    Args:
        code_review: The CodeReviewSchema object containing the CI file.
    """
    file = code_review.ci_file
    results = []

    try:
        rules = handle_multi_targets(file.parent, file.name)
        for key, item in rules.items():
            if not isinstance(item, list):
                results.append(
                    RulesResult(
                        name="gitlab-ci",
                        passed=False,
                        level=ReviewRuleLevel.CRITICAL.value,
                        message=f"Invalid 'only' condition for job '{key}': {item}",
                    )
                )
                break
            if len(item) > 1:
                results.append(
                    RulesResult(
                        name="gitlab-ci",
                        passed=False,
                        level=ReviewRuleLevel.CRITICAL.value,
                        message=f"Multiple 'only' conditions for job '{key}': {item}",
                    )
                )
        if not results:
            return [
                RulesResult(
                    name="gitlab-ci", passed=True, level=ReviewRuleLevel.INFO.value, message="All CI rules are valid."
                )
            ]

    except CodeReviewError as e:
        results.append(RulesResult(name="gitlab-ci", passed=False, level=ReviewRuleLevel.ERROR.value, message=str(e)))
    except Exception as e:
        results.append(
            RulesResult(
                name="gitlab-ci", passed=False, level=ReviewRuleLevel.CRITICAL.value, message=f"Unexpected error: {e}"
            )
        )
    return results
