# API Contracts: Rule Validation Reporting System

**Feature**: 003-rule-validation-reporting  
**Date**: October 12, 2025

## Enhanced RulesResult Schema Contract

### Pydantic Model Definition

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator

class SeverityLevel(str, Enum):
    """Standardized severity levels for rule validation results."""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

class RuleCategory(str, Enum):
    """Logical groupings for rule organization."""
    TYPE_SAFETY = "type_safety"
    CODE_STYLE = "code_style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPENDENCIES = "dependencies"
    COMPLEXITY = "complexity"
    GENERAL = "general"  # Default for uncategorized

class EnhancedRulesResult(BaseModel):
    """Enhanced rule validation result with categorization and standardized severity."""
    
    name: str = Field(description="Descriptive unique identifier for the rule")
    passed: bool = Field(description="Indicates if the rule passed (True) or failed/violated (False)", default=False)
    message: str = Field(description="Clear, actionable description of validation result")
    details: Optional[str] = Field(default=None, description="Enhanced contextual information including location and remediation guidance")
    category: RuleCategory = Field(default=RuleCategory.GENERAL, description="Logical grouping of related rules")
    severity: SeverityLevel = Field(default=SeverityLevel.WARNING, description="Standardized severity level")
    
    # Backward compatibility property for existing 'level' field usage
    @property
    def level(self) -> str:
        """Backward compatibility property mapping severity to old level field."""
        return self.severity.value
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Rule name must be non-empty')
        return v.strip()
    
    @validator('message')
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message must be non-empty')
        return v.strip()
    
    def is_violation(self) -> bool:
        """Check if this result represents a rule violation."""
        return not self.passed
    
    def is_blocking(self) -> bool:
        """Check if this result should block builds/merges."""
        return not self.passed and self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]
```

### Validation Function Contract

```python
from typing import List, Dict, Any, Optional
from pathlib import Path

def validate_coverage_rules(
    coverage_data: Dict[str, Any],
    coverage_config: Dict[str, Any],
    file_path: Optional[Path] = None
) -> List[EnhancedRulesResult]:
    """
    Validate coverage-related rules and return structured validation results.
    
    Args:
        coverage_data: Coverage analysis results containing percentages and file info
        coverage_config: Configuration for coverage thresholds and requirements  
        file_path: Optional path to the analyzed file for context
        
    Returns:
        List of enhanced rule validation results
        
    Raises:
        ValueError: If coverage_data is invalid or missing required fields
        TypeError: If arguments are not of expected types
    """
    pass

def filter_validation_results(
    results: List[EnhancedRulesResult],
    severity_filter: Optional[List[SeverityLevel]] = None,
    category_filter: Optional[List[RuleCategory]] = None,
    violations_only: bool = False
) -> List[EnhancedRulesResult]:
    """
    Filter validation results by severity, category, and violation status.
    
    Args:
        results: List of validation results to filter
        severity_filter: Only include results with these severity levels
        category_filter: Only include results from these categories
        violations_only: If True, only include failed validations (passed=False)
        
    Returns:
        Filtered list of validation results
    """
    pass

def generate_validation_summary(
    results: List[EnhancedRulesResult]
) -> Dict[str, Any]:
    """
    Generate aggregated summary of validation results.
    
    Args:
        results: List of validation results to summarize
        
    Returns:
        Dictionary containing summary statistics and breakdowns
    """
    pass
```

## JSON Schema (for external integrations)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "Enhanced Rules Result",
  "description": "Enhanced rule validation result with categorization and standardized severity",
  "properties": {
    "name": {
      "type": "string",
      "description": "Descriptive unique identifier for the rule",
      "minLength": 1
    },
    "passed": {
      "type": "boolean", 
      "description": "Indicates if the rule passed (true) or failed/violated (false)",
      "default": false
    },
    "message": {
      "type": "string",
      "description": "Clear, actionable description of validation result",
      "minLength": 1
    },
    "details": {
      "type": ["string", "null"],
      "description": "Enhanced contextual information including location and remediation guidance"
    },
    "category": {
      "type": "string",
      "enum": ["type_safety", "code_style", "security", "performance", "documentation", "testing", "dependencies", "complexity", "general"],
      "default": "general",
      "description": "Logical grouping of related rules"
    },
    "severity": {
      "type": "string", 
      "enum": ["info", "warning", "error", "critical"],
      "default": "warning",
      "description": "Standardized severity level"
    }
  },
  "required": ["name", "passed", "message"],
  "additionalProperties": false
}
```

## CLI Interface Contract

### Command Extensions

```bash
# Enhanced validation with filtering
code-review validate --severity error,critical --category security,type_safety

# Backward compatible usage (existing commands continue working)
code-review analyze --coverage-min 85

# Generate validation summary
code-review validate --summary --format json

# Filter violations only
code-review validate --violations-only --category security
```

### Configuration Schema

```yaml
# Enhanced validation configuration
validation:
  default_severity: warning
  default_category: general
  
  # Category-specific severity overrides
  category_severity:
    security: critical
    type_safety: error
    performance: warning
    
  # Severity-based behaviors
  blocking_severities: [error, critical]
  report_severities: [warning, error, critical]
  
coverage:
  minimum_threshold: 85
  rules:
    - name: "minimum_coverage"
      category: "testing" 
      severity: "error"
      threshold: 85
    - name: "coverage_regression"
      category: "testing"
      severity: "warning"
      max_drop: 5
```

## Migration Contract

### Backward Compatibility Guarantees

1. **Existing RulesResult constructors continue working**
2. **All existing properties and methods preserved**
3. **JSON serialization maintains existing fields**
4. **Legacy 'level' field accessible via property**
5. **Default values provide sensible fallbacks**

### Migration Utilities

```python
def migrate_legacy_results(legacy_results: List[Dict]) -> List[EnhancedRulesResult]:
    """Convert legacy RulesResult dictionaries to enhanced format."""
    pass

def map_legacy_level_to_severity(level: str) -> SeverityLevel:
    """Map legacy level strings to standardized severity enum."""
    pass
```