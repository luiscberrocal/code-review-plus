"""Comprehensive tests for enhanced RulesResult functionality.

These tests verify that the enhanced RulesResult class works correctly
with the new fields while maintaining full backward compatibility.
"""

import pytest
from hypothesis import given, strategies as st

from code_review.schemas import RulesResult, SeverityLevel, RuleCategory


class TestEnhancedRulesResult:
    """Test the enhanced RulesResult functionality."""

    def test_enhanced_constructor_with_all_fields(self):
        """Test creating RulesResult with all enhanced fields."""
        result = RulesResult(
            name="test_rule",
            category=RuleCategory.SECURITY,
            severity=SeverityLevel.CRITICAL,
            passed=False,
            message="Security vulnerability detected",
            details="SQL injection risk in user input validation"
        )
        
        assert result.name == "test_rule"
        assert result.category == RuleCategory.SECURITY
        assert result.severity == SeverityLevel.CRITICAL
        assert result.passed is False
        assert result.message == "Security vulnerability detected"
        assert result.details == "SQL injection risk in user input validation"

    def test_default_values_for_new_fields(self):
        """Test that new fields have appropriate default values."""
        result = RulesResult(
            name="test_rule",
            message="Test message"
        )
        
        assert result.category == RuleCategory.GENERAL
        assert result.severity == SeverityLevel.WARNING
        assert result.passed is False  # Existing default

    def test_level_property_backward_compatibility(self):
        """Test that level property correctly maps to severity value."""
        result = RulesResult(
            name="test_rule",
            severity=SeverityLevel.ERROR,
            message="Test message"
        )
        
        assert result.level == "error"
        assert result.level == result.severity.value

    def test_is_violation_method(self):
        """Test the is_violation utility method."""
        passed_result = RulesResult(
            name="test_rule",
            passed=True,
            message="Test passed"
        )
        
        failed_result = RulesResult(
            name="test_rule",
            passed=False,
            message="Test failed"
        )
        
        assert not passed_result.is_violation()
        assert failed_result.is_violation()

    def test_is_blocking_method(self):
        """Test the is_blocking utility method."""
        # Non-blocking: passed=True
        passed_result = RulesResult(
            name="test_rule",
            passed=True,
            severity=SeverityLevel.CRITICAL,
            message="Test passed"
        )
        
        # Non-blocking: failed but low severity
        warning_result = RulesResult(
            name="test_rule",
            passed=False,
            severity=SeverityLevel.WARNING,
            message="Test warning"
        )
        
        # Blocking: failed with high severity
        error_result = RulesResult(
            name="test_rule",
            passed=False,
            severity=SeverityLevel.ERROR,
            message="Test error"
        )
        
        critical_result = RulesResult(
            name="test_rule",
            passed=False,
            severity=SeverityLevel.CRITICAL,
            message="Test critical"
        )
        
        assert not passed_result.is_blocking()
        assert not warning_result.is_blocking()
        assert error_result.is_blocking()
        assert critical_result.is_blocking()

    def test_serialization_includes_new_fields(self):
        """Test that serialization includes new fields."""
        result = RulesResult(
            name="test_rule",
            category=RuleCategory.TYPE_SAFETY,
            severity=SeverityLevel.WARNING,
            passed=False,
            message="Type hint missing"
        )
        
        data = result.model_dump()
        
        # New fields should be present
        assert "category" in data
        assert "severity" in data
        assert data["category"] == "type_safety"
        assert data["severity"] == "warning"
        
        # Existing fields still present
        assert "name" in data
        assert "passed" in data
        assert "message" in data
        assert "details" in data

    @given(
        name=st.text(min_size=1),
        passed=st.booleans(),
        message=st.text(min_size=1),
        category=st.sampled_from(RuleCategory),
        severity=st.sampled_from(SeverityLevel)
    )
    def test_property_based_rulesresult_creation(self, name, passed, message, category, severity):
        """Property-based test for RulesResult creation with hypothesis."""
        result = RulesResult(
            name=name,
            passed=passed,
            message=message,
            category=category,
            severity=severity
        )
        
        assert result.name == name
        assert result.passed == passed
        assert result.message == message
        assert result.category == category
        assert result.severity == severity
        
        # Test property relationships
        assert result.level == severity.value
        assert result.is_violation() == (not passed)
        
        if not passed and severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]:
            assert result.is_blocking()
        else:
            assert not result.is_blocking()

    def test_enum_values_are_correct(self):
        """Test that enum values match expected strings."""
        assert SeverityLevel.INFO.value == "info"
        assert SeverityLevel.WARNING.value == "warning"
        assert SeverityLevel.ERROR.value == "error"
        assert SeverityLevel.CRITICAL.value == "critical"
        
        assert RuleCategory.TYPE_SAFETY.value == "type_safety"
        assert RuleCategory.CODE_STYLE.value == "code_style"
        assert RuleCategory.SECURITY.value == "security"
        assert RuleCategory.PERFORMANCE.value == "performance"
        assert RuleCategory.DOCUMENTATION.value == "documentation"
        assert RuleCategory.TESTING.value == "testing"
        assert RuleCategory.DEPENDENCIES.value == "dependencies"
        assert RuleCategory.COMPLEXITY.value == "complexity"
        assert RuleCategory.GENERAL.value == "general"