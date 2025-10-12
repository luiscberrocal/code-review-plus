# Quickstart: Rule Validation Reporting System

**Feature**: 003-rule-validation-reporting  
**Date**: October 12, 2025

## Overview

This feature enhances the existing `RulesResult` object to provide comprehensive rule validation reporting with categorization, standardized severity levels, and detailed context information while maintaining 100% backward compatibility.

## Quick Implementation Steps

### 1. Update Existing RulesResult Schema (code_review/schemas.py)

```python
# Add these enums to the top of the file
from enum import Enum

class SeverityLevel(str, Enum):
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

class RuleCategory(str, Enum):
    TYPE_SAFETY = "type_safety"
    CODE_STYLE = "code_style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPENDENCIES = "dependencies"
    COMPLEXITY = "complexity"
    GENERAL = "general"

# Enhance the existing RulesResult class
class RulesResult(BaseModel):
    """Schema for rules result."""

    name: str = Field(description="Name of the rule")
    passed: bool = Field(description="Indicates if the rule passed or failed", default=False)
    message: str
    details: str | None = None
    
    # NEW FIELDS
    category: RuleCategory = Field(default=RuleCategory.GENERAL, description="Logical grouping of related rules")
    severity: SeverityLevel = Field(default=SeverityLevel.WARNING, description="Standardized severity level")
    
    # Backward compatibility for existing 'level' field
    @property
    def level(self) -> str:
        """Backward compatibility property."""
        return self.severity.value
    
    def is_violation(self) -> bool:
        """Check if this result represents a rule violation."""
        return not self.passed
    
    def is_blocking(self) -> bool:
        """Check if this result should block builds/merges."""
        return not self.passed and self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]
```

### 2. Add Validation Function to Coverage Handlers

Add this function to `code_review/plugins/coverage/handlers.py`:

```python
from typing import List
from code_review.schemas import RulesResult, SeverityLevel, RuleCategory

def validate_coverage_rules(
    coverage_data: dict[str, Any],
    coverage_config: dict[str, Any],
    file_path: Path | None = None
) -> List[RulesResult]:
    """
    Validate coverage-related rules and return structured validation results.
    
    Args:
        coverage_data: Coverage analysis results containing percentages and file info
        coverage_config: Configuration for coverage thresholds and requirements  
        file_path: Optional path to the analyzed file for context
        
    Returns:
        List of enhanced rule validation results
    """
    results = []
    
    # Validate minimum coverage threshold
    coverage_percentage = coverage_data.get("coverage_percentage", 0)
    min_threshold = coverage_config.get("minimum_coverage", 85)
    
    if coverage_percentage >= min_threshold:
        results.append(RulesResult(
            name="minimum_coverage_threshold",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.INFO,
            passed=True,
            message=f"Coverage {coverage_percentage}% meets minimum threshold of {min_threshold}%",
            details=f"Current coverage: {coverage_percentage}%, Required: {min_threshold}%"
        ))
    else:
        results.append(RulesResult(
            name="minimum_coverage_threshold",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.ERROR,
            passed=False,
            message=f"Coverage {coverage_percentage}% below minimum threshold of {min_threshold}%",
            details=f"Current coverage: {coverage_percentage}%, Required: {min_threshold}%. Add {min_threshold - coverage_percentage}% more coverage."
        ))
    
    # Validate test count if available
    test_count = coverage_data.get("test_count", -1)
    if test_count > 0:
        results.append(RulesResult(
            name="test_execution_success",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.INFO,
            passed=True,
            message=f"Successfully executed {test_count} tests",
            details=f"Test count: {test_count}, Running time: {coverage_data.get('running_time', 'unknown')}s"
        ))
    elif test_count == 0:
        results.append(RulesResult(
            name="test_execution_success",
            category=RuleCategory.TESTING,
            severity=SeverityLevel.WARNING,
            passed=False,
            message="No tests were executed",
            details="Consider adding unit tests to improve code coverage and quality"
        ))
    
    return results
```

### 3. Update Imports and Usage

Update any existing code that uses RulesResult:

```python
# Existing usage continues to work (backward compatible)
result = RulesResult(
    name="existing_rule",
    passed=True,
    message="Rule passed"
)

# Enhanced usage with new fields
result = RulesResult(
    name="enhanced_rule",
    category=RuleCategory.SECURITY,
    severity=SeverityLevel.CRITICAL,
    passed=False,
    message="Security vulnerability detected",
    details="SQL injection risk in user input validation. Use parameterized queries."
)

# Filtering examples
violations = [r for r in results if not r.passed]  # Get violations only
critical_issues = [r for r in results if r.severity == SeverityLevel.CRITICAL]
security_results = [r for r in results if r.category == RuleCategory.SECURITY]
```

## Testing Strategy

### 1. Backward Compatibility Tests

```python
def test_backward_compatibility():
    """Ensure existing usage patterns continue working."""
    # Old constructor pattern
    result = RulesResult(name="test", passed=True, message="Success")
    assert result.name == "test"
    assert result.passed is True
    assert result.level == "warning"  # Default severity mapping
    
def test_level_property_compatibility():
    """Ensure level property provides backward compatibility."""
    result = RulesResult(
        name="test",
        severity=SeverityLevel.ERROR,
        passed=False,
        message="Error"
    )
    assert result.level == "error"
```

### 2. Enhanced Functionality Tests

```python
def test_validation_function():
    """Test the new coverage validation function."""
    coverage_data = {"coverage_percentage": 90, "test_count": 50}
    coverage_config = {"minimum_coverage": 85}
    
    results = validate_coverage_rules(coverage_data, coverage_config)
    
    assert len(results) == 2
    assert results[0].category == RuleCategory.TESTING
    assert results[0].passed is True
```

### 3. Property-Based Tests with Hypothesis

```python
from hypothesis import given, strategies as st

@given(
    coverage=st.floats(min_value=0, max_value=100),
    threshold=st.floats(min_value=0, max_value=100)
)
def test_coverage_validation_logic(coverage, threshold):
    """Property-based test for coverage validation logic."""
    results = validate_coverage_rules(
        {"coverage_percentage": coverage},
        {"minimum_coverage": threshold}
    )
    
    coverage_result = results[0]
    assert coverage_result.passed == (coverage >= threshold)
    assert coverage_result.category == RuleCategory.TESTING
```

## Migration Checklist

- [ ] Update RulesResult schema with new fields and enums
- [ ] Add validation function to coverage handlers
- [ ] Update imports in affected modules
- [ ] Add backward compatibility tests
- [ ] Add enhanced functionality tests
- [ ] Add property-based tests with hypothesis
- [ ] Update configuration files to support new categories/severities
- [ ] Test CLI integration with enhanced results
- [ ] Verify reporting formats work with new fields
- [ ] Document migration guide for users

## Performance Considerations

- New fields add minimal memory overhead (~32 bytes per result)
- Enum lookups are O(1) operations
- Backward compatibility property access is O(1)
- Filtering operations remain O(n) but benefit from enum comparisons
- JSON serialization includes new fields but maintains compatibility

## Next Steps

1. Implement the schema changes
2. Add the validation function
3. Write comprehensive tests
4. Update any CLI commands to support filtering
5. Enhance reporting to utilize new categorization
6. Add configuration support for category/severity rules