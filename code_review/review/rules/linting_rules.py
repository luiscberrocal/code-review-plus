from code_review.schemas import BranchSchema, RulesResult

def check_and_format_ruff(base_branch: BranchSchema, target_branch: BranchSchema) -> list[RulesResult]:
    results = compare_linting_error_rules(base_branch, target_branch, "linting_errors")
    results.extend(compare_linting_error_rules(base_branch, target_branch, "formatting_errors"))
    return results

def compare_linting_error_rules(base_branch: BranchSchema, target_branch: BranchSchema, linting_attribute:str) -> list[RulesResult]:
    """Compare linting rules between two branches.

    Args:
        base_branch: The base branch schema.
        target_branch: The target branch schema.
        linting_attribute: The attribute name to compare (e.g., 'linting_errors').

    Returns:
        A dictionary with the comparison results.
    """

    rules = []
    target_count = getattr(target_branch, linting_attribute)
    name = linting_attribute.replace("_", " ").title()
    if target_count == 0:
        rules.append(
            RulesResult(
                name=name,
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

    base_count = getattr(base_branch, linting_attribute)
    if target_count > base_count:
        rules.append(
            RulesResult(
                name=name,
                passed=False,
                level="ERROR",
                message="Target branch has more linting errors than the base branch.",
                details=(
                    f"Base branch has {base_branch.linting_errors} linting errors, "
                    f"while target branch has {target_branch.linting_errors}."
                ),
            )
        )
    elif target_count < base_count:
        rules.append(
            RulesResult(
                name=name,
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
                name=name,
                level="WARNING",
                passed=True,
                message="Target branch has the same number of linting errors as the base branch.",
                details=(
                    f"Both branches have {base_branch.linting_errors} linting errors."
                ),
            )
        )
    return rules