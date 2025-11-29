import pytest
from code_review.review.rules import unvetted_requirements_rules
from code_review.schemas import RulesResult

class MockRequirement:
    def __init__(self, name):
        self.name = name

class MockBranch:
    def __init__(self, requirements):
        self.requirements = requirements

class MockCodeReviewSchema:
    def __init__(self, requirements):
        self.target_branch = MockBranch(requirements)

class TestUnvettedRequirementsCheck:
    def setup_method(self):
        # Patch CONFIG_MANAGER for tests
        unvetted_requirements_rules.CONFIG_MANAGER.config_data = {
            "vetted_requirements": {
                "services": [
                    {"name": "numpy"},
                    {"name": "psycopg"},
                    {"name": "psycopg[c, pool]"},
                    {"name": "pytest"}

                ]
            }
        }

    def test_all_vetted(self):
        code_review = MockCodeReviewSchema([
            MockRequirement("numpy"),
            MockRequirement("pytest"),
            MockRequirement("psycopg[c, pool]")
        ])
        results = unvetted_requirements_rules.check(code_review)
        assert results == []

    def test_some_unvetted(self):
        code_review = MockCodeReviewSchema([
            MockRequirement("numpy"),
            MockRequirement("unknown_package")
        ])
        results = unvetted_requirements_rules.check(code_review)
        assert len(results) == 1
        assert isinstance(results[0], RulesResult)
        assert results[0].name == "Unvetted Requirements Detail"
        assert results[0].level == "ERROR"
        assert not results[0].passed
        assert "unknown_package" in results[0].message

    def test_all_unvetted(self):
        code_review = MockCodeReviewSchema([
            MockRequirement("foo"),
            MockRequirement("bar")
        ])
        results = unvetted_requirements_rules.check(code_review)
        assert len(results) == 2
        for result in results:
            assert isinstance(result, RulesResult)
            assert result.name == "Unvetted Requirements Detail"
            assert result.level == "ERROR"
            assert not result.passed
            assert result.message.startswith("Requirement '")

