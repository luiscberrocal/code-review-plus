from code_review.enums import ReviewRuleLevel


def check_multiple_targets(ci_data: dict):
    """Check if there are multiple targets in the CI configuration.

    Args:
        ci_data: Dictionary containing CI job configurations.

    Returns:
        True if multiple targets are found, False otherwise.
    """
    if not ci_data:
        return {"level": ReviewRuleLevel.CRITICAL.value, "message": "No CI configuration data found."}
    for _job, conditions in ci_data.items():
        if isinstance(conditions, list) and len(conditions) > 1:
            return {
                "level": ReviewRuleLevel.ERROR.value,
                "message": f"We have more than one ci targets ({len(conditions)}).",
            }

    return {"level": ReviewRuleLevel.INFO.value, "message": "CI configuration is Oke."}
