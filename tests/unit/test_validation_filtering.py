"""
Tests for validation result filtering functionality.

This module tests User Story 2: Severity-Based Filtering for CI/CD Integration.
Provides comprehensive test coverage for filtering validation results by severity
levels and violation status.
"""

import pytest
from typing import List
from hypothesis import given, strategies as st
import random

from code_review.schemas import RulesResult, SeverityLevel, RuleCategory


class TestValidationFiltering:
    """Test suite for validation result filtering functionality."""

    def test_filter_by_single_severity_level(self):
        """Test filtering by a single severity level."""
        # Create sample validation results with different severity levels
        results = [
            RulesResult(
                name="test_rule_1",
                passed=False,
                message="Error message",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.ERROR,
                details="Error details"
            ),
            RulesResult(
                name="test_rule_2", 
                passed=True,
                message="Warning message",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Warning details"
            ),
            RulesResult(
                name="test_rule_3",
                passed=False,
                message="Critical message",
                category=RuleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                details="Critical details"
            )
        ]
        
        # Import the filtering function - we'll implement this next
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Filter for ERROR level only
        error_results = filter_validation_results(results, min_severity=SeverityLevel.ERROR)
        assert len(error_results) == 2  # ERROR and CRITICAL
        
        # Filter for CRITICAL level only
        critical_results = filter_validation_results(results, min_severity=SeverityLevel.CRITICAL)
        assert len(critical_results) == 1
        assert critical_results[0].severity == SeverityLevel.CRITICAL

    def test_filter_by_multiple_severity_levels(self):
        """Test filtering by multiple severity levels."""
        results = [
            RulesResult(
                name="info_rule",
                passed=True,
                message="Info message",
                category=RuleCategory.GENERAL,
                severity=SeverityLevel.INFO,
                details="Info details"
            ),
            RulesResult(
                name="warning_rule",
                passed=False,
                message="Warning message", 
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Warning details"
            ),
            RulesResult(
                name="error_rule",
                passed=False,
                message="Error message",
                category=RuleCategory.TYPE_SAFETY,
                severity=SeverityLevel.ERROR,
                details="Error details"
            )
        ]
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Filter for WARNING and above (WARNING, ERROR, CRITICAL)
        filtered = filter_validation_results(
            results, 
            severities=[SeverityLevel.WARNING, SeverityLevel.ERROR, SeverityLevel.CRITICAL]
        )
        assert len(filtered) == 2
        assert all(r.severity in [SeverityLevel.WARNING, SeverityLevel.ERROR] for r in filtered)

    def test_filter_violations_only(self):
        """Test filtering for violations only (passed=False)."""
        results = [
            RulesResult(
                name="passing_rule",
                passed=True,
                message="All good",
                category=RuleCategory.TESTING,
                severity=SeverityLevel.INFO,
                details="Passed details"
            ),
            RulesResult(
                name="failing_rule",
                passed=False,
                message="Issue found",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Failed details"
            )
        ]
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Filter for violations only
        violations = filter_validation_results(results, violations_only=True)
        assert len(violations) == 1
        assert not violations[0].passed

    def test_combined_filtering(self):
        """Test combined severity and violation filtering."""
        results = [
            RulesResult(
                name="passing_warning",
                passed=True,
                message="Warning but passing",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Passing details"
            ),
            RulesResult(
                name="failing_warning",
                passed=False,
                message="Warning and failing",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Failing details"
            ),
            RulesResult(
                name="failing_info",
                passed=False,
                message="Info level failure",
                category=RuleCategory.GENERAL,
                severity=SeverityLevel.INFO,
                details="Info failure details"
            )
        ]
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Filter for violations at WARNING level and above
        filtered = filter_validation_results(
            results,
            min_severity=SeverityLevel.WARNING,
            violations_only=True
        )
        assert len(filtered) == 1
        assert filtered[0].name == "failing_warning"

    def test_ci_cd_integration_scenarios(self):
        """Test filtering scenarios typical for CI/CD pipelines."""
        results = [
            RulesResult(
                name="style_check",
                passed=False,
                message="Code style violation",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Style violation details"
            ),
            RulesResult(
                name="security_check",
                passed=False,
                message="Security vulnerability",
                category=RuleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                details="Security vulnerability details"
            ),
            RulesResult(
                name="type_check",
                passed=False,
                message="Type error",
                category=RuleCategory.TYPE_SAFETY,
                severity=SeverityLevel.ERROR,
                details="Type error details"
            ),
            RulesResult(
                name="documentation",
                passed=True,
                message="Good documentation",
                category=RuleCategory.DOCUMENTATION,
                severity=SeverityLevel.INFO,
                details="Documentation check details"
            )
        ]
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # CI/CD Scenario 1: Only blocking issues (ERROR and CRITICAL)
        blocking_issues = filter_validation_results(
            results,
            min_severity=SeverityLevel.ERROR,
            violations_only=True
        )
        assert len(blocking_issues) == 2
        assert all(r.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL] for r in blocking_issues)
        
        # CI/CD Scenario 2: All violations for reporting
        all_violations = filter_validation_results(results, violations_only=True)
        assert len(all_violations) == 3
        
        # CI/CD Scenario 3: Critical issues only for immediate action
        critical_only = filter_validation_results(
            results,
            severities=[SeverityLevel.CRITICAL]
        )
        assert len(critical_only) == 1
        assert critical_only[0].category == RuleCategory.SECURITY

    def test_empty_results_list(self):
        """Test filtering with empty results list."""
        from code_review.handlers.validation_handlers import filter_validation_results
        
        empty_results = []
        filtered = filter_validation_results(empty_results, min_severity=SeverityLevel.ERROR)
        assert filtered == []

    def test_no_matching_results(self):
        """Test filtering when no results match criteria."""
        results = [
            RulesResult(
                name="info_rule",
                passed=True,
                message="Info message",
                category=RuleCategory.GENERAL,
                severity=SeverityLevel.INFO,
                details="Info details"
            )
        ]
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Filter for CRITICAL when only INFO exists
        filtered = filter_validation_results(results, min_severity=SeverityLevel.CRITICAL)
        assert len(filtered) == 0


class TestPropertyBasedFiltering:
    """Property-based tests for filtering logic using hypothesis."""

    @given(
        results_count=st.integers(min_value=0, max_value=100),
        min_severity=st.sampled_from(list(SeverityLevel))
    )
    def test_min_severity_filtering_property(self, results_count: int, min_severity: SeverityLevel):
        """Property: All filtered results should have severity >= min_severity."""
        # Generate random results
        results = []
        for i in range(results_count):
            severity = random.choice(list(SeverityLevel))
            category = random.choice(list(RuleCategory))
            passed = random.choice([True, False])
            results.append(
                RulesResult(
                    name=f"rule_{i}",
                    passed=passed,
                    message=f"Message {i}",
                    category=category,
                    severity=severity,
                    details=f"Details {i}"
                )
            )
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Filter by minimum severity
        filtered = filter_validation_results(results, min_severity=min_severity)
        
        # Property: All filtered results should have severity >= min_severity
        severity_order = {
            SeverityLevel.INFO: 0,
            SeverityLevel.WARNING: 1,
            SeverityLevel.ERROR: 2,
            SeverityLevel.CRITICAL: 3
        }
        
        min_level = severity_order[min_severity]
        for result in filtered:
            assert severity_order[result.severity] >= min_level

    @given(
        violations_count=st.integers(min_value=0, max_value=50),
        passed_count=st.integers(min_value=0, max_value=50)
    )
    def test_violations_only_property(self, violations_count: int, passed_count: int):
        """Property: violations_only filter should return only failed results."""
        # Create results with known pass/fail status
        results = []
        
        # Add violations (passed=False)
        for i in range(violations_count):
            category = random.choice(list(RuleCategory))
            severity = random.choice(list(SeverityLevel))
            results.append(
                RulesResult(
                    name=f"violation_{i}",
                    passed=False,
                    message=f"Violation {i}",
                    category=category,
                    severity=severity,
                    details=f"Violation details {i}"
                )
            )
        
        # Add passed results (passed=True)
        for i in range(passed_count):
            category = random.choice(list(RuleCategory))
            severity = random.choice(list(SeverityLevel))
            results.append(
                RulesResult(
                    name=f"passed_{i}",
                    passed=True,
                    message=f"Passed {i}",
                    category=category,
                    severity=severity,
                    details=f"Passed details {i}"
                )
            )
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Filter for violations only
        violations = filter_validation_results(results, violations_only=True)
        
        # Property: All results should have passed=False
        for result in violations:
            assert not result.passed
        
        # Property: Count should match expected violations
        assert len(violations) == violations_count


class TestFilteringPerformance:
    """Test filtering performance with large datasets."""

    def test_large_dataset_filtering(self):
        """Test filtering performance with large validation result sets."""
        # Create 10,000 test results
        large_results = []
        for i in range(10000):
            severity = [SeverityLevel.INFO, SeverityLevel.WARNING, SeverityLevel.ERROR, SeverityLevel.CRITICAL][i % 4]
            large_results.append(
                RulesResult(
                    name=f"rule_{i}",
                    passed=i % 3 != 0,  # ~33% violations
                    message=f"Message {i}",
                    category=list(RuleCategory)[i % len(list(RuleCategory))],
                    severity=severity,
                    details=f"Details {i}"
                )
            )
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Test filtering performance (should complete quickly)
        import time
        start_time = time.time()
        
        filtered = filter_validation_results(
            large_results,
            min_severity=SeverityLevel.ERROR,
            violations_only=True
        )
        
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second)
        assert (end_time - start_time) < 1.0
        
        # Verify correct filtering
        assert len(filtered) > 0
        for result in filtered:
            assert result.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]
            assert not result.passed

    def test_mixed_severity_category_combinations(self):
        """Test filtering with various severity and category combinations."""
        results = [
            # High severity across different categories
            RulesResult(
                name="security_critical",
                passed=False,
                message="Critical security issue",
                category=RuleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                details="Critical security details"
            ),
            RulesResult(
                name="type_error",
                passed=False,
                message="Type safety error",
                category=RuleCategory.TYPE_SAFETY,
                severity=SeverityLevel.ERROR,
                details="Type error details"
            ),
            # Lower severity issues
            RulesResult(
                name="style_warning",
                passed=False,
                message="Style warning",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Style warning details"
            ),
            RulesResult(
                name="doc_info",
                passed=True,
                message="Documentation complete",
                category=RuleCategory.DOCUMENTATION,
                severity=SeverityLevel.INFO,
                details="Documentation details"
            )
        ]
        
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Test various combinations work correctly
        high_severity = filter_validation_results(
            results,
            min_severity=SeverityLevel.ERROR
        )
        assert len(high_severity) == 2
        
        violations_only = filter_validation_results(
            results,
            violations_only=True
        )
        assert len(violations_only) == 3
        
        # Combined filtering
        high_severity_violations = filter_validation_results(
            results,
            min_severity=SeverityLevel.ERROR,
            violations_only=True
        )
        assert len(high_severity_violations) == 2
        assert all(not r.passed for r in high_severity_violations)
        assert all(r.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL] for r in high_severity_violations)