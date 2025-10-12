"""
Tests for CLI filtering integration.

This module tests CLI commands with severity filtering for User Story 2.
Tests integration between CLI commands and the validation filtering system.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from code_review.schemas import RulesResult, SeverityLevel, RuleCategory
from code_review.cli import cli


class TestCLIFiltering:
    """Test suite for CLI integration with validation filtering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Sample validation results for testing
        self.sample_results = [
            RulesResult(
                name="coverage_check",
                passed=False,
                message="Coverage below threshold",
                category=RuleCategory.TESTING,
                severity=SeverityLevel.ERROR,
                details="Coverage is 70%, required 85%"
            ),
            RulesResult(
                name="style_check",
                passed=False,
                message="Code style violation",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.WARNING,
                details="Line too long"
            ),
            RulesResult(
                name="security_check",
                passed=False,
                message="Security vulnerability detected",
                category=RuleCategory.SECURITY,
                severity=SeverityLevel.CRITICAL,
                details="SQL injection risk"
            ),
            RulesResult(
                name="documentation_check",
                passed=True,
                message="Documentation complete",
                category=RuleCategory.DOCUMENTATION,
                severity=SeverityLevel.INFO,
                details="All functions documented"
            )
        ]

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')
    def test_cli_coverage_with_severity_filter(self, mock_validate):
        """Test coverage command with severity filtering."""
        # Mock the coverage analysis to return our sample results
        mock_validate.return_value = self.sample_results
        
        # Test with minimum severity filter
        result = self.runner.invoke(cli, [
            'coverage',
            '--min-severity', 'error',
            '--violations-only'
        ])
        
        # Should complete successfully
        assert result.exit_code == 0
        
        # Should only show ERROR and CRITICAL violations
        output = result.output
        assert "coverage_check" in output  # ERROR violation
        assert "security_check" in output  # CRITICAL violation
        assert "style_check" not in output  # WARNING (filtered out)
        assert "documentation_check" not in output  # INFO and passed

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')  
    def test_cli_coverage_with_specific_severities(self, mock_validate):
        """Test coverage command with specific severity levels."""
        mock_validate.return_value = self.sample_results
        
        # Test with specific severities
        result = self.runner.invoke(cli, [
            'coverage',
            '--severity', 'warning',
            '--severity', 'critical'
        ])
        
        assert result.exit_code == 0
        
        output = result.output
        assert "style_check" in output  # WARNING
        assert "security_check" in output  # CRITICAL
        assert "coverage_check" not in output  # ERROR (filtered out)
        assert "documentation_check" not in output  # INFO (filtered out)

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')
    def test_cli_coverage_violations_only(self, mock_validate):
        """Test coverage command with violations-only filter."""
        mock_validate.return_value = self.sample_results
        
        result = self.runner.invoke(cli, [
            'coverage',
            '--violations-only'
        ])
        
        assert result.exit_code == 0
        
        output = result.output
        # Should show all violations
        assert "coverage_check" in output
        assert "style_check" in output  
        assert "security_check" in output
        # Should not show passed results
        assert "documentation_check" not in output

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')
    def test_cli_coverage_combined_filters(self, mock_validate):
        """Test coverage command with combined filtering options."""
        mock_validate.return_value = self.sample_results
        
        # Combine minimum severity and violations-only
        result = self.runner.invoke(cli, [
            'coverage',
            '--min-severity', 'warning',
            '--violations-only',
            '--output-format', 'json'
        ])
        
        assert result.exit_code == 0
        
        # Verify JSON output contains filtered results
        import json
        try:
            output_data = json.loads(result.output)
            assert isinstance(output_data, list)
            # Should have 3 violations (WARNING, ERROR, CRITICAL)
            assert len(output_data) == 3
        except json.JSONDecodeError:
            # If not JSON format, check text output
            output = result.output
            assert "coverage_check" in output  # ERROR violation
            assert "style_check" in output    # WARNING violation
            assert "security_check" in output # CRITICAL violation
            assert "documentation_check" not in output  # Passed result

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')
    def test_cli_coverage_no_results_matching_filter(self, mock_validate):
        """Test CLI behavior when no results match filter criteria."""
        # Return only INFO level passed results
        mock_validate.return_value = [
            RulesResult(
                name="info_check",
                passed=True,
                message="All good",
                category=RuleCategory.GENERAL,
                severity=SeverityLevel.INFO,
                details="Everything looks fine"
            )
        ]
        
        result = self.runner.invoke(cli, [
            'coverage',
            '--min-severity', 'critical',
            '--violations-only'
        ])
        
        # Should complete successfully but with no results shown
        assert result.exit_code == 0
        output = result.output.lower()
        assert "no results found" in output or "0 result" in output

    def test_cli_invalid_severity_level(self):
        """Test CLI behavior with invalid severity level."""
        result = self.runner.invoke(cli, [
            'coverage',
            '--min-severity', 'invalid_level'
        ])
        
        # Should fail with error
        assert result.exit_code != 0
        assert "invalid choice" in result.output.lower() or "error" in result.output.lower()

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')
    def test_cli_performance_with_large_dataset(self, mock_validate):
        """Test CLI performance with large filtered datasets."""
        # Create large dataset
        large_results = []
        for i in range(1000):
            severity = [SeverityLevel.INFO, SeverityLevel.WARNING, SeverityLevel.ERROR, SeverityLevel.CRITICAL][i % 4]
            large_results.append(
                RulesResult(
                    name=f"rule_{i}",
                    passed=i % 2 == 0,  # 50% pass rate
                    message=f"Message {i}",
                    category=list(RuleCategory)[i % len(list(RuleCategory))],
                    severity=severity,
                    details=f"Details {i}"
                )
            )
        
        mock_validate.return_value = large_results
        
        import time
        start_time = time.time()
        
        result = self.runner.invoke(cli, [
            'coverage',
            '--min-severity', 'error',
            '--violations-only'
        ])
        
        end_time = time.time()
        
        # Should complete within reasonable time (< 5 seconds for CLI)
        assert (end_time - start_time) < 5.0
        assert result.exit_code == 0

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')
    def test_cli_output_format_with_filtering(self, mock_validate):
        """Test different output formats work with filtering."""
        mock_validate.return_value = self.sample_results
        
        # Test JSON output with filtering
        result = self.runner.invoke(cli, [
            'coverage',
            '--violations-only',
            '--output-format', 'json'
        ])
        
        assert result.exit_code == 0
        # Should be valid JSON
        import json
        output_data = json.loads(result.output)
        assert isinstance(output_data, list)
        assert len(output_data) == 3  # 3 violations

    @patch('code_review.plugins.coverage.handlers.validate_coverage_rules')
    def test_cli_exit_codes_with_violations(self, mock_validate):
        """Test CLI exit codes based on filtered violations."""
        mock_validate.return_value = self.sample_results
        
        # Test exit code with blocking violations (ERROR/CRITICAL)
        result = self.runner.invoke(cli, [
            'coverage',
            '--min-severity', 'error',
            '--violations-only',
            '--fail-on-violations'
        ])
        
        # Should fail because there are ERROR and CRITICAL violations
        assert result.exit_code == 1


class TestCLIFilteringHelpers:
    """Test helper functions for CLI filtering integration."""

    def test_severity_level_parsing(self):
        """Test parsing severity levels from CLI arguments."""
        from code_review.handlers.validation_handlers import filter_validation_results
        
        # Test case-insensitive parsing
        assert SeverityLevel.ERROR == SeverityLevel('error')
        assert SeverityLevel.WARNING == SeverityLevel('warning')
        assert SeverityLevel.CRITICAL == SeverityLevel('critical')
        assert SeverityLevel.INFO == SeverityLevel('info')

    def test_filter_result_formatting(self):
        """Test formatting of filtered results for CLI output."""
        from code_review.handlers.validation_handlers import get_summary_stats
        
        results = [
            RulesResult(
                name="test_rule",
                passed=False,
                message="Test violation",
                category=RuleCategory.CODE_STYLE,
                severity=SeverityLevel.ERROR,
                details="Test details"
            )
        ]
        
        stats = get_summary_stats(results)
        
        assert stats["total"] == 1
        assert stats["violations"] == 1
        assert stats["blocking_violations"] == 1
        assert stats["critical_violations"] == 0