from pathlib import Path

from code_review.plugins.gitlab.ci.handlers import handle_multi_targets


def validate_ci_rules(file: Path) -> None:
    """Validate GitLab CI rules in the given file.

    Args:
        file: Path to the .gitlab-ci.yml file.

    Raises:
        ValueError: If invalid rules are found.
    """

    rules = handle_multi_targets(file.parent, file.name)
    if not rules:
        return

    for job, conditions in rules.items():
        for condition in conditions:
            if not isinstance(condition, str):
                raise ValueError(f"Invalid condition type in job '{job}': {condition} (type: {type(condition)})")
            if not condition.startswith("refs/heads/"):
                raise ValueError(f"Invalid condition format in job '{job}': {condition}. Must start with 'refs/heads/'")
            branch = condition[len("refs/heads/") :]
            if not branch:
                raise ValueError(f"Empty branch name in job '{job}' condition: {condition}")
            if " " in branch or "\t" in branch:
                raise ValueError(f"Invalid whitespace in branch name for job '{job}': '{branch}'")