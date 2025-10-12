"""Tests for coverage validation functionality.

These tests verify that the validate_coverage_rules function works correctly
with different coverage scenarios and configurations.
"""

import pytest
from pathlib import Path
from hypothesis import given, strategies as st

from code_review.plugins.coverage.handlers import validate_coverage_rules
from code_review.schemas import RulesResult, SeverityLevel, RuleCategory


class TestValidateCoverageRules:
    """Test the validate_coverage_rules function."""

    def test_validate_coverage_rules_meets_threshold(self):
        """Test validation when coverage meets the minimum threshold."""
        coverage_data = {
            "coverage_percentage": 90,
            "test_count": 50,
            "running_time": 2.5
        }
        coverage_config = {
            "minimum_coverage": 85
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Should have at least 2 results: coverage threshold and test execution
        assert len(results) >= 2
        
        # Check coverage threshold result
        coverage_result = next(r for r in results if r.name == "minimum_coverage_threshold")
        assert coverage_result.passed is True
        assert coverage_result.category == RuleCategory.TESTING
        assert coverage_result.severity == SeverityLevel.INFO
        assert "90%" in coverage_result.message
        assert "85%" in coverage_result.message
        
        # Check test execution result
        test_result = next(r for r in results if r.name == "test_execution_success")
        assert test_result.passed is True
        assert test_result.category == RuleCategory.TESTING
        assert test_result.severity == SeverityLevel.INFO
        assert "50 tests" in test_result.message

    def test_validate_coverage_rules_below_threshold(self):
        """Test validation when coverage is below the minimum threshold."""
        coverage_data = {
            "coverage_percentage": 75,
            "test_count": 30,
            "running_time": 1.8
        }
        coverage_config = {
            "minimum_coverage": 85
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Check coverage threshold result
        coverage_result = next(r for r in results if r.name == "minimum_coverage_threshold")
        assert coverage_result.passed is False
        assert coverage_result.category == RuleCategory.TESTING
        assert coverage_result.severity == SeverityLevel.ERROR
        assert "75%" in coverage_result.message
        assert "85%" in coverage_result.message
        assert "10.0%" in coverage_result.details  # Gap calculation

    def test_validate_coverage_rules_no_tests_executed(self):
        """Test validation when no tests were executed."""
        coverage_data = {
            "coverage_percentage": 0,
            "test_count": 0
        }
        coverage_config = {
            "minimum_coverage": 85
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Check test execution result
        test_result = next(r for r in results if r.name == "test_execution_success")
        assert test_result.passed is False
        assert test_result.category == RuleCategory.TESTING
        assert test_result.severity == SeverityLevel.WARNING
        assert "No tests were executed" in test_result.message

    def test_validate_coverage_rules_with_regression_check(self):
        """Test validation with coverage regression checking."""
        coverage_data = {
            "coverage_percentage": 82,
            "test_count": 40
        }
        coverage_config = {
            "minimum_coverage": 80,
            "previous_coverage": 85,
            "max_coverage_drop": 5
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Check regression result (within allowed drop)
        regression_result = next(r for r in results if r.name == "coverage_regression_check")
        assert regression_result.passed is False
        assert regression_result.category == RuleCategory.TESTING
        assert regression_result.severity == SeverityLevel.WARNING
        assert "3.0%" in regression_result.details  # Drop calculation

    def test_validate_coverage_rules_excessive_regression(self):
        """Test validation with excessive coverage regression."""
        coverage_data = {
            "coverage_percentage": 75,
            "test_count": 40
        }
        coverage_config = {
            "minimum_coverage": 70,
            "previous_coverage": 85,
            "max_coverage_drop": 5
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Check regression result (exceeds allowed drop)
        regression_result = next(r for r in results if r.name == "coverage_regression_check")
        assert regression_result.passed is False
        assert regression_result.category == RuleCategory.TESTING
        assert regression_result.severity == SeverityLevel.ERROR
        assert "10.0%" in regression_result.details  # Drop calculation

    def test_validate_coverage_rules_improvement(self):
        """Test validation when coverage has improved."""
        coverage_data = {
            "coverage_percentage": 88,
            "test_count": 45
        }
        coverage_config = {
            "minimum_coverage": 85,
            "previous_coverage": 85
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Check regression result (improvement)
        regression_result = next(r for r in results if r.name == "coverage_regression_check")
        assert regression_result.passed is True
        assert regression_result.category == RuleCategory.TESTING
        assert regression_result.severity == SeverityLevel.INFO
        assert "3.0%" in regression_result.details  # Improvement

    def test_validate_coverage_rules_invalid_input_types(self):
        """Test validation with invalid input types."""
        with pytest.raises(TypeError, match="coverage_data must be a dictionary"):
            validate_coverage_rules("invalid", {})
        
        with pytest.raises(TypeError, match="coverage_config must be a dictionary"):
            validate_coverage_rules({}, "invalid")

    def test_validate_coverage_rules_missing_test_count(self):
        """Test validation when test_count is missing or -1."""
        coverage_data = {
            "coverage_percentage": 90,
            "test_count": -1  # Indicates not checked
        }
        coverage_config = {
            "minimum_coverage": 85
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Should only have coverage threshold result, no test execution result
        result_names = [r.name for r in results]
        assert "minimum_coverage_threshold" in result_names
        assert "test_execution_success" not in result_names

    @given(
        coverage_percentage=st.floats(min_value=0, max_value=100),
        minimum_coverage=st.floats(min_value=0, max_value=100),
        test_count=st.integers(min_value=0, max_value=1000)
    )
    def test_property_based_coverage_validation(self, coverage_percentage, minimum_coverage, test_count):
        """Property-based test for coverage validation logic."""
        coverage_data = {
            "coverage_percentage": coverage_percentage,
            "test_count": test_count
        }
        coverage_config = {
            "minimum_coverage": minimum_coverage
        }
        
        results = validate_coverage_rules(coverage_data, coverage_config)
        
        # Should always have at least one result (coverage threshold)
        assert len(results) >= 1
        
        # Check coverage threshold logic
        coverage_result = next(r for r in results if r.name == "minimum_coverage_threshold")
        assert coverage_result.passed == (coverage_percentage >= minimum_coverage)
        assert coverage_result.category == RuleCategory.TESTING
        
        if coverage_result.passed:
            assert coverage_result.severity == SeverityLevel.INFO
        else:
            assert coverage_result.severity == SeverityLevel.ERROR
        
        # Check test execution logic if test_count > 0
        if test_count > 0:
            test_result = next(r for r in results if r.name == "test_execution_success")
            assert test_result.passed is True
            assert test_result.category == RuleCategory.TESTING
            assert test_result.severity == SeverityLevel.INFO
        elif test_count == 0:
            test_result = next(r for r in results if r.name == "test_execution_success")
            assert test_result.passed is False
            assert test_result.category == RuleCategory.TESTING
            assert test_result.severity == SeverityLevel.WARNING