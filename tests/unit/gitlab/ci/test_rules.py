from pathlib import Path

from code_review.plugins.gitlab.ci.rules import validate_ci_rules


def test_validate_ci_rules(fixtures_folder: Path) -> None:
    
    ci_file_path = fixtures_folder / "gitlab-ci.yml"
    result = validate_ci_rules(ci_file_path)
    assert len(result) == 2