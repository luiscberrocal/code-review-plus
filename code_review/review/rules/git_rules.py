from code_review.plugins.git.handlers import compare_branches
from code_review.schemas import RulesResult


def validate_master_develop_sync(default_branches: list[str]) -> list[RulesResult]:
    """Validates that 'master' and 'develop' branches are included in the default branches.

    This function checks if both 'master' and 'develop' branches are present
    in the list of default branches specified in the configuration dictionary.
    It returns True if both branches are found, otherwise it returns False.

    Args:
        config (dict): A configuration dictionary containing a key
                       'default_branches' which is a list of branch names.

    Returns:
        bool: True if both 'master' and 'develop' are in the default branches,
              False otherwise.
    """
    rules = []
    results = compare_branches(*default_branches)

    if results.get("ahead") == 0 and results.get("behind") == 0:
        rules.append(
            RulesResult(
                name="Git",
                level="INFO",
                passed=True,
                message="'master' and 'develop' branches are in sync.",
            )
        )
    else:
        rules.append(
            RulesResult(
                name="Git",
                level="ERROR",
                passed=False,
                message="'master' and 'develop' branches are not in sync.",
                details=(
                    f"'master' is ahead by {results.get('ahead', 0)} commits and behind by {results.get('behind', 0)} commits compared to 'develop'."
                ),
            )
        )
    return rules