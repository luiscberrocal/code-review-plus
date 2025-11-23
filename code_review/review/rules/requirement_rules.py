from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import RulesResult


def check(code_review: CodeReviewSchema) -> list[RulesResult]:
    """Check if there are requirements to update in the code review schema.

    Args:
        code_review: The CodeReviewSchema object containing branch information.
    """
    requirements_to_update = len(code_review.target_branch.requirements_to_update)
    if requirements_to_update == 0:
        return [
            RulesResult(
                name="Requirements Update Check",
                level="INFO",
                passed=True,
                message="No requirements need to be updated.",
            )
        ]
    return [
        RulesResult(
            name="Requirements Update Check",
            level="ERROR",
            passed=False,
            message=f"{requirements_to_update} requirement(s) need to be updated",
        )
    ]
