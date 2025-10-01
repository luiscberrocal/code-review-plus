from pathlib import Path

import pytest


@pytest.fixture
def fixtures_folder() -> Path:
    """Return the path to the fixtures folder."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def requirements_folder() -> Path:
    """Return the path to the requirement_folders folder."""
    return Path(__file__).parent / "fixtures" / "requirements"


@pytest.fixture
def load_environment_vars():
    """Load environment variables for testing."""
    load_environment_variables("local.txt")


def load_environment_variables(environment_filename: str, source_folder_name: str = ".envs"):
    from pathlib import Path

    from dotenv import load_dotenv

    def find_envs_folder(current_dir: Path):
        env_folder = current_dir / source_folder_name
        if env_folder.exists():
            return env_folder
        return find_envs_folder(current_dir.parent)

    environment_folder = find_envs_folder(Path(__file__).parent)
    environment_file = environment_folder / environment_filename
    load_dotenv(dotenv_path=environment_file)
