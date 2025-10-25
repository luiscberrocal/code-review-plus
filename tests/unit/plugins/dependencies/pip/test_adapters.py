import pytest
from code_review.plugins.dependencies.pip.adapters import parse_requirements
from code_review.plugins.dependencies.pip.schemas import PackageRequirement

class TestParseRequirements:
    def test_standard_requirements(self):
        content = """
        requests==2.31.0
        numpy>=1.25.0
        # Commented line
        pandas
        """
        results = parse_requirements(content)
        assert any(r.name == "requests" and r.version == "2.31.0" for r in results)
        assert any(r.name == "numpy" and r.specifier == ">=" for r in results)
        assert any(not r.name == "pandas" for r in results)
        assert all(not r.name.startswith("#") for r in results)

    def test_standard_requirements_greater_than(self):
        content = """
        numpy>=1.25.0
        """
        results = parse_requirements(content)
        assert any(r.name == "numpy" and r.specifier == ">=" for r in results)

    def test_extras_and_comments(self):
        content = """
        uvicorn[standard]>=0.35.0  # with extras
        ddtrace[django]==3.16.0
        """
        results = parse_requirements(content)
        assert any(r.name == "uvicorn[standard]" and ">=" in r.specifier for r in results)
        assert any(r.name == "ddtrace[django]" and r.version == "3.16.0" for r in results)

    def test_vcs_requirement(self):
        content = """
        git+https://github.com/example/repo.git@v1.2.3
        """
        results = parse_requirements(content)
        assert any(r.source and "git+" in r.source and r.version == "v1.2.3" for r in results)

    def test_invalid_lines_are_skipped(self):
        content = """
        not_a_valid_requirement_line
        """
        results = parse_requirements(content)
        assert results == []

    def test_mixed_content(self):
        content = """
        requests==2.31.0
        git+https://github.com/example/repo.git@v1.2.3
        # comment
        """
        results = parse_requirements(content)
        assert len(results) == 2
        assert any(r.name == "requests" for r in results)
        assert any(r.source and "git+" in r.source for r in results)