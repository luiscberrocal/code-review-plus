"""Backward compatibility tests for RulesResult enhancements.

These tests ensure that existing code using RulesResult continues to work
without modification after the enhancements are implemented.
"""

import pytest
from code_review.schemas import RulesResult


class TestBackwardCompatibility:
    """Test backward compatibility of RulesResult enhancements."""

    def test_existing_constructor_pattern_works(self):
        """Test that existing RulesResult constructor pattern continues to work."""
        # This is how RulesResult is currently used in the codebase
        result = RulesResult(
            name="test_rule",
            passed=True,
            message="Rule passed successfully"
        )
        
        assert result.name == "test_rule"
        assert result.passed is True
        assert result.message == "Rule passed successfully"
        assert result.details is None

    def test_existing_constructor_with_details(self):
        """Test existing constructor pattern with details field."""
        result = RulesResult(
            name="test_rule",
            passed=False,
            message="Rule failed",
            details="Some error details"
        )
        
        assert result.name == "test_rule"
        assert result.passed is False
        assert result.message == "Rule failed"
        assert result.details == "Some error details"

    def test_existing_level_field_compatibility(self):
        """Test that the level field remains accessible for backward compatibility."""
        result = RulesResult(
            name="test_rule",
            passed=False,
            message="Rule failed"
        )
        
        # The level property should be available for backward compatibility
        # Default should be "warning" based on the design
        assert hasattr(result, 'level')

    def test_serialization_includes_existing_fields(self):
        """Test that serialization includes all existing fields."""
        result = RulesResult(
            name="test_rule",
            passed=True,
            message="Rule passed"
        )
        
        data = result.model_dump()
        
        # Existing fields must be present
        assert "name" in data
        assert "passed" in data
        assert "message" in data
        assert "details" in data

    def test_field_defaults_work_as_expected(self):
        """Test that field defaults work for existing usage patterns."""
        result = RulesResult(
            name="test_rule",
            message="Test message"
        )
        
        # passed should default to False (as per existing schema)
        assert result.passed is False
        assert result.details is None