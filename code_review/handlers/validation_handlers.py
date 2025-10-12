"""
Validation result filtering and processing handlers.

This module provides filtering functionality for validation results,
supporting severity-based filtering and violation filtering for CI/CD integration.
"""

from typing import List, Optional, Union
from code_review.schemas import RulesResult, SeverityLevel


def filter_validation_results(
    results: List[RulesResult],
    *,
    min_severity: Optional[SeverityLevel] = None,
    severities: Optional[List[SeverityLevel]] = None,
    violations_only: bool = False
) -> List[RulesResult]:
    """
    Filter validation results based on severity levels and violation status.
    
    This function supports multiple filtering modes:
    1. Minimum severity level filtering (min_severity)
    2. Specific severity levels filtering (severities)
    3. Violations-only filtering (violations_only)
    4. Combined filtering
    
    Args:
        results: List of validation results to filter
        min_severity: Minimum severity level to include (inclusive)
        severities: Specific severity levels to include
        violations_only: If True, only return failed validation results (passed=False)
        
    Returns:
        Filtered list of validation results
        
    Examples:
        # Filter for ERROR and above
        errors = filter_validation_results(results, min_severity=SeverityLevel.ERROR)
        
        # Filter for specific severity levels
        warnings_and_errors = filter_validation_results(
            results, 
            severities=[SeverityLevel.WARNING, SeverityLevel.ERROR]
        )
        
        # Filter for violations only
        violations = filter_validation_results(results, violations_only=True)
        
        # Combined: violations at ERROR level and above
        critical_violations = filter_validation_results(
            results,
            min_severity=SeverityLevel.ERROR,
            violations_only=True
        )
    """
    if not results:
        return []
    
    filtered_results = results.copy()
    
    # Apply severity filtering
    if min_severity is not None:
        severity_order = {
            SeverityLevel.INFO: 0,
            SeverityLevel.WARNING: 1,
            SeverityLevel.ERROR: 2,
            SeverityLevel.CRITICAL: 3
        }
        min_level = severity_order[min_severity]
        filtered_results = [
            result for result in filtered_results
            if severity_order[result.severity] >= min_level
        ]
    
    # Apply specific severities filtering
    if severities is not None:
        severity_set = set(severities)
        filtered_results = [
            result for result in filtered_results
            if result.severity in severity_set
        ]
    
    # Apply violations-only filtering
    if violations_only:
        filtered_results = [
            result for result in filtered_results
            if not result.passed
        ]
    
    return filtered_results


def get_blocking_violations(results: List[RulesResult]) -> List[RulesResult]:
    """
    Get validation results that should block CI/CD pipelines.
    
    Returns violations at ERROR and CRITICAL severity levels.
    
    Args:
        results: List of validation results to filter
        
    Returns:
        List of blocking violations
    """
    return filter_validation_results(
        results,
        min_severity=SeverityLevel.ERROR,
        violations_only=True
    )


def get_critical_violations(results: List[RulesResult]) -> List[RulesResult]:
    """
    Get critical violations that require immediate attention.
    
    Returns violations at CRITICAL severity level only.
    
    Args:
        results: List of validation results to filter
        
    Returns:
        List of critical violations
    """
    return filter_validation_results(
        results,
        severities=[SeverityLevel.CRITICAL],
        violations_only=True
    )


def get_violations_by_severity(results: List[RulesResult]) -> dict[SeverityLevel, List[RulesResult]]:
    """
    Group violations by severity level.
    
    Args:
        results: List of validation results to group
        
    Returns:
        Dictionary mapping severity levels to lists of violations
    """
    violations = filter_validation_results(results, violations_only=True)
    
    grouped = {severity: [] for severity in SeverityLevel}
    
    for violation in violations:
        grouped[violation.severity].append(violation)
    
    return grouped


def get_summary_stats(results: List[RulesResult]) -> dict:
    """
    Get summary statistics for validation results.
    
    Args:
        results: List of validation results to analyze
        
    Returns:
        Dictionary with summary statistics
    """
    total_count = len(results)
    violations = filter_validation_results(results, violations_only=True)
    violations_count = len(violations)
    passed_count = total_count - violations_count
    
    # Count by severity
    severity_counts = {}
    for severity in SeverityLevel:
        severity_results = filter_validation_results(results, severities=[severity])
        severity_counts[severity.value] = len(severity_results)
    
    # Count violations by severity
    violation_severity_counts = {}
    for severity in SeverityLevel:
        severity_violations = filter_validation_results(
            results,
            severities=[severity],
            violations_only=True
        )
        violation_severity_counts[severity.value] = len(severity_violations)
    
    return {
        "total": total_count,
        "passed": passed_count,
        "violations": violations_count,
        "pass_rate": (passed_count / total_count * 100) if total_count > 0 else 0,
        "severity_counts": severity_counts,
        "violation_severity_counts": violation_severity_counts,
        "blocking_violations": len(get_blocking_violations(results)),
        "critical_violations": len(get_critical_violations(results))
    }