from pathlib import Path

import pytest


@pytest.fixture
def fixtures_folder() -> Path:
    """Return the path to the fixtures folder."""
    return Path(__file__).parent / "fixtures"
