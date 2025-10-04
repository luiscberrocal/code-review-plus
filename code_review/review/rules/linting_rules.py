from code_review.schemas import BranchSchema, RulesResult


def compare_linting_rules(base_branch: BranchSchema, target_branch: BranchSchema, linting_attribute:str) -> list[RulesResult]:
    """Compare linting rules between two branches.

    Args:
        base_branch: The base branch schema.
        target_branch: The target branch schema.

    Returns:
        A dictionary with the comparison results.
    """

    rules = []
    if getattr(target_branch, linting_attribute) == 0:
        rules.append(
            RulesResult(
                name="Ruff Linting",
                level="INFO",
                passed=True,
                message="Base branch has no versions in the changelog.",
            )
        )
    # if target_branch.formatting_errors == 0:
    #     rules.append(
    #         RulesResult(
    #             name="Ruff Formatting",
    #             level="INFO",
    #             passed=True,
    #             message="Target branch has no formatting errors.",
    #         )
    #     )

    if getattr(target_branch, linting_attribute) > getattr(base_branch, linting_attribute):
        rules.append(
            RulesResult(
                name="Ruff Linting",
                passed=False,
                level="ERROR",
                message="Target branch has more linting errors than the base branch.",
                details=(
                    f"Base branch has {base_branch.linting_errors} linting errors, "
                    f"while target branch has {target_branch.linting_errors}."
                ),
            )
        )
    elif getattr(target_branch, linting_attribute) < getattr(base_branch, linting_attribute):
        rules.append(
            RulesResult(
                name="Ruff Linting",
                passed=True,
                level="INFO",
                message="Target branch has fewer linting errors than the base branch.",
                details=(
                    f"Base branch has {base_branch.linting_errors} linting errors, "
                    f"while target branch has {target_branch.linting_errors}."
                ),
            )
        )
    else:
        rules.append(
            RulesResult(
                name="Ruff Linting",
                level="WARNING",
                passed=True,
                message="Target branch has the same number of linting errors as the base branch.",
                details=(
                    f"Both branches have {base_branch.linting_errors} linting errors."
                ),
            )
        )
    return rules