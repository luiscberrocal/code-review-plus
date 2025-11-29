from code_review.config import CONFIG_MANAGER
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import RulesResult


def check(code_review: CodeReviewSchema) -> list[RulesResult]:
    """Check if there are unvetted requirements in the code review schema.

    Args:
        code_review: The CodeReviewSchema object containing branch information.
    """
    results = []
    vetted_names = [req["name"] for req in CONFIG_MANAGER.config_data["vetted_requirements"]["services"]]

    for req in code_review.target_branch.requirements:
        if req.name not in vetted_names:
            if "psycopg" in req.name:
                # Special case: psycopg can have extras, so we consider it vetted
                print(f">>>>>>>>>>> Requirement '{req.name}' is considered vetted due to special case handlinf, "
                      f"Found: {req.name in vetted_names}.")
            results.append(RulesResult(
                name="Unvetted Requirements Detail",
                level="ERROR",
                passed=False,
                message=(
                    f"Requirement '{req.name}' is unvetted. "
                    "Please review it to ensure it meets the project's standards."
                ),
            ))
    return results