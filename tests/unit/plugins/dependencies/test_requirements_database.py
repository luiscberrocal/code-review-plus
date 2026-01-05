"""Tests for the vetted requirements database interface."""

import pytest
from pathlib import Path

from code_review.plugins.dependencies.requirements_database import (
    VettedRequirementsDatabase,
    VettedRequirementDB,
)


@pytest.fixture
def db_interface():
    """Fixture to provide database interface."""
    db_path = Path(__file__).parent.parent.parent.parent.parent / "code_review.db"
    if not db_path.exists():
        pytest.skip(f"Database not found at {db_path}")
    return VettedRequirementsDatabase(db_path)


class TestVettedRequirementsDatabase:
    """Tests for VettedRequirementsDatabase class."""

    def test_get_all_requirements(self, db_interface):
        """Test getting all requirements from database."""
        requirements = db_interface.get_all_requirements()

        assert len(requirements) > 0
        assert all(isinstance(r, VettedRequirementDB) for r in requirements)
        # Should have 70 requirements
        assert len(requirements) == 70

    def test_get_requirement_by_name(self, db_interface):
        """Test getting a specific requirement by name."""
        # Test existing requirement
        django_req = db_interface.get_requirement_by_name("django")

        assert django_req is not None
        assert django_req.name == "django"
        assert django_req.version == "5.2.7"
        assert django_req.specifier == "=="
        assert django_req.environment == "BASE"

        # Test non-existent requirement
        nonexistent = db_interface.get_requirement_by_name("nonexistent-package")
        assert nonexistent is None

    def test_get_requirement_by_name_with_environment(self, db_interface):
        """Test getting requirement with environment filter."""
        # Test with correct environment
        pytest_req = db_interface.get_requirement_by_name("pytest", "DEVELOPMENT")
        assert pytest_req is not None
        assert pytest_req.environment == "DEVELOPMENT"

        # Test with wrong environment
        pytest_prod = db_interface.get_requirement_by_name("pytest", "PRODUCTION")
        assert pytest_prod is None

    def test_get_requirements_by_environment(self, db_interface):
        """Test getting requirements for specific environments."""
        # Test BASE environment
        base_reqs = db_interface.get_requirements_by_environment("BASE")
        assert len(base_reqs) > 0
        assert all(r.environment == "BASE" for r in base_reqs)
        assert len(base_reqs) == 39

        # Test PRODUCTION environment
        prod_reqs = db_interface.get_requirements_by_environment("PRODUCTION")
        assert len(prod_reqs) > 0
        assert all(r.environment == "PRODUCTION" for r in prod_reqs)
        assert len(prod_reqs) == 15

        # Test DEVELOPMENT environment
        dev_reqs = db_interface.get_requirements_by_environment("DEVELOPMENT")
        assert len(dev_reqs) > 0
        assert all(r.environment == "DEVELOPMENT" for r in dev_reqs)
        assert len(dev_reqs) == 16

    def test_get_git_based_requirements(self, db_interface):
        """Test getting git-based requirements."""
        git_reqs = db_interface.get_git_based_requirements()

        assert len(git_reqs) > 0
        # All should have @ specifier and source
        for req in git_reqs:
            assert req.specifier == "@"
            assert req.source is not None
            assert "git+" in req.source

    def test_search_requirements(self, db_interface):
        """Test searching requirements by pattern."""
        # Search for Django packages
        django_reqs = db_interface.search_requirements("django%")
        assert len(django_reqs) > 0
        assert all(r.name.startswith("django") for r in django_reqs)

        # Search for pytest packages
        pytest_reqs = db_interface.search_requirements("pytest%")
        assert len(pytest_reqs) > 0
        assert all(r.name.startswith("pytest") for r in pytest_reqs)

    def test_get_statistics(self, db_interface):
        """Test getting database statistics."""
        stats = db_interface.get_statistics()

        assert "total_requirements" in stats
        assert "by_environment" in stats
        assert "git_based_count" in stats
        assert "django_count" in stats

        assert stats["total_requirements"] == 70
        assert stats["by_environment"]["BASE"] == 39
        assert stats["by_environment"]["DEVELOPMENT"] == 16
        assert stats["by_environment"]["PRODUCTION"] == 15
        assert stats["git_based_count"] > 0
        assert stats["django_count"] > 0

    def test_requirement_exists(self, db_interface):
        """Test checking if requirement exists."""
        assert db_interface.requirement_exists("django") is True
        assert db_interface.requirement_exists("celery") is True
        assert db_interface.requirement_exists("nonexistent") is False

        # Test with environment
        assert db_interface.requirement_exists("pytest", "DEVELOPMENT") is True
        assert db_interface.requirement_exists("pytest", "PRODUCTION") is False

    def test_get_requirements_dict(self, db_interface):
        """Test getting requirements as dictionary."""
        # All requirements
        all_dict = db_interface.get_requirements_dict()
        assert isinstance(all_dict, dict)
        assert "django" in all_dict
        assert isinstance(all_dict["django"], VettedRequirementDB)

        # Filtered by environment
        dev_dict = db_interface.get_requirements_dict("DEVELOPMENT")
        assert all(req.environment == "DEVELOPMENT" for req in dev_dict.values())

    def test_generate_requirements_file(self, db_interface, tmp_path):
        """Test generating requirements file."""
        # Generate for BASE environment
        content = db_interface.generate_requirements_file(["BASE"])
        assert "django==" in content
        assert "celery==" in content

        # Generate for multiple environments
        multi_content = db_interface.generate_requirements_file(["BASE", "DEVELOPMENT"])
        assert "# BASE requirements" in multi_content
        assert "# DEVELOPMENT requirements" in multi_content
        assert "pytest==" in multi_content

        # Test writing to file
        output_file = tmp_path / "requirements.txt"
        written_content = db_interface.generate_requirements_file(["BASE"], output_file)
        assert output_file.exists()
        assert output_file.read_text() == written_content


class TestVettedRequirementDB:
    """Tests for VettedRequirementDB model."""

    def test_from_db_row(self):
        """Test creating VettedRequirementDB from database row."""
        # Standard package
        row = (1, "django", "5.2.7", "==", None, "BASE", "2026-01-05 10:00:00")
        req = VettedRequirementDB.from_db_row(row)

        assert req.id == 1
        assert req.name == "django"
        assert req.version == "5.2.7"
        assert req.specifier == "=="
        assert req.source is None
        assert req.environment == "BASE"
        assert req.created_at == "2026-01-05 10:00:00"

    def test_from_db_row_git_based(self):
        """Test creating VettedRequirementDB for git-based package."""
        row = (
            2,
            "custom-sdk",
            "1.0.0",
            "@",
            "git+https://example.com/repo.git@v1.0.0",
            "PRODUCTION",
            "2026-01-05 10:00:00"
        )
        req = VettedRequirementDB.from_db_row(row)

        assert req.specifier == "@"
        assert req.source is not None
        assert "git+" in req.source

    def test_to_requirement_string_standard(self):
        """Test converting standard package to requirement string."""
        req = VettedRequirementDB(
            id=1,
            name="django",
            version="5.2.7",
            specifier="==",
            environment="BASE"
        )

        req_string = req.to_requirement_string()
        assert req_string == "django==5.2.7"

    def test_to_requirement_string_git_based(self):
        """Test converting git-based package to requirement string."""
        source = "git+https://example.com/repo.git@v1.0.0"
        req = VettedRequirementDB(
            id=1,
            name="custom-sdk",
            version="1.0.0",
            specifier="@",
            source=source,
            environment="PRODUCTION"
        )

        req_string = req.to_requirement_string()
        assert req_string == source


class TestRequirementsIntegration:
    """Integration tests for requirements database."""

    def test_common_packages_present(self, db_interface):
        """Test that common packages are in the database."""
        common_packages = [
            "django", "celery", "pytest", "pydantic",
            "redis", "gunicorn", "pillow"
        ]

        for package in common_packages:
            req = db_interface.get_requirement_by_name(package)
            assert req is not None, f"Common package {package} not found"

    def test_django_ecosystem(self, db_interface):
        """Test Django ecosystem packages."""
        django_packages = db_interface.search_requirements("django%")

        # Should have multiple Django packages
        assert len(django_packages) > 10

        # Check for specific ones
        package_names = [p.name for p in django_packages]
        assert "django" in package_names
        assert "django-allauth" in package_names
        assert "djangorestframework" in package_names

    def test_environment_separation(self, db_interface):
        """Test that environments are properly separated."""
        # Development-only packages
        dev_packages = ["pytest", "pytest-django", "coverage", "ipdb"]
        for package in dev_packages:
            req = db_interface.get_requirement_by_name(package)
            assert req is not None
            assert req.environment == "DEVELOPMENT"

        # Production-only packages
        prod_packages = ["mysqlclient", "watchtower"]
        for package in prod_packages:
            req = db_interface.get_requirement_by_name(package)
            assert req is not None
            assert req.environment == "PRODUCTION"

    def test_git_based_packages_format(self, db_interface):
        """Test that git-based packages have proper format."""
        git_packages = db_interface.get_git_based_requirements()

        for package in git_packages:
            # Should have source URL
            assert package.source is not None
            assert package.source.startswith("git+")

            # Should have version tag
            assert f"@v{package.version}" in package.source or f"@{package.version}" in package.source

            # Source should match expected pattern
            req_string = package.to_requirement_string()
            assert req_string == package.source

    def test_generate_complete_requirements(self, db_interface):
        """Test generating complete requirements for deployment."""
        # Production requirements (BASE + PRODUCTION)
        prod_content = db_interface.generate_requirements_file(["BASE", "PRODUCTION"])

        # Should include base packages
        assert "django==" in prod_content

        # Should include production packages
        assert "mysqlclient==" in prod_content or "psycopg==" in prod_content

        # Should NOT include development packages
        assert "pytest" not in prod_content
        assert "ipdb" not in prod_content

