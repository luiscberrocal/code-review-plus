from pathlib import Path

from code_review.plugins.dependencies.pip.handlers import fiend_requirements_to_update


def test_requirements_handler(fixtures_folder: Path) -> None:
    results = fiend_requirements_to_update(fixtures_folder)
    assert len(results) > 1
