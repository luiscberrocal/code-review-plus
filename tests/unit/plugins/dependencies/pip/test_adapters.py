from code_review.plugins.dependencies.pip.adapters import parse_requirements
from code_review.enums import EnvironmentType
from pathlib import Path


class TestParseRequirements:
    def test_standard_requirements(self):
        content = """
        requests==2.31.0
        numpy>=1.25.0
        # Commented line
        pandas
        """
        results = parse_requirements(
            content,
            EnvironmentType.DEVELOPMENT,
            Path("requirements.txt"),
        )
        assert any(r.name == "requests" and r.version == "2.31.0" for r in results)
        assert any(r.name == "numpy" and r.specifier == ">=" for r in results)
        assert any(r.name == "pandas" for r in results)
        assert all(not r.name.startswith("#") for r in results)

    def test_unpinned_standard_requirements(self):
        content = """
        pandas
        """
        results = parse_requirements(
            content,
            EnvironmentType.DEVELOPMENT,
            Path("requirements.txt"),
        )
        assert any(r.name == "pandas" for r in results)
        assert all(not r.name.startswith("#") for r in results)
    def test_standard_requirements_greater_than(self):
        content = """
        numpy>=1.25.0
        """
        results = parse_requirements(
            content,
            EnvironmentType.DEVELOPMENT,
            Path("requirements.txt"),
        )
        assert any(r.name == "numpy" and r.specifier == ">=" for r in results)

    def test_extras_and_comments(self):
        content = """
        uvicorn[standard]>=0.35.0  # with extras
        ddtrace[django]==3.16.0
        """
        results = parse_requirements(
            content,
            EnvironmentType.DEVELOPMENT,
            Path("requirements.txt"),
        )
        assert any(r.name == "uvicorn[standard]" and ">=" in r.specifier for r in results)
        assert any(r.name == "ddtrace[django]" and r.version == "3.16.0" for r in results)

    def test_vcs_requirement(self):
        content = """
        git+https://@gitlab.com/example/repo.git@v1.2.3
        git+https://TOKEN:${SECRET_TOKEN}@gitlab.com/development/my-sdk.git@v9.2.1
        """
        results = parse_requirements(
            content,
            EnvironmentType.DEVELOPMENT,
            Path("requirements.txt"),
        )
        assert results[0].source == "git+https://@gitlab.com/example/repo.git@v1.2.3"
        assert results[0].version == "1.2.3"
        assert results[0].name == "repo"
        assert results[1].source == "git+https://TOKEN:${SECRET_TOKEN}@gitlab.com/development/my-sdk.git@v9.2.1"
        assert results[1].version == "9.2.1"
        assert results[1].name == "my-sdk"

    def test_mixed_content(self):
        content = """
        requests==2.31.0
        git+https://github.com/example/repo.git@v1.2.3
        # comment
        """
        results = parse_requirements(
            content,
            EnvironmentType.DEVELOPMENT,
            Path("requirements.txt"),
        )
        assert len(results) == 2
        assert any(r.name == "requests" for r in results)
        assert any(r.source and "git+" in r.source for r in results)
