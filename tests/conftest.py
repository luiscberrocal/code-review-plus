from pathlib import Path

import pytest


@pytest.fixture
def fixtures_folder() -> Path:
    """Return the path to the fixtures folder."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def requirements_folder() ->Path:
    """Return the path to the requirement_folders folder."""
    return Path(__file__).parent / "fixtures" / "requirements"