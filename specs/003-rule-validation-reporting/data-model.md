# Data Model: Rule Validation Reporting System

**Feature**: 003-rule-validation-reporting  
**Date**: October 12, 2025

## Core Entities

### Enhanced RulesResult (Primary Entity)

**Purpose**: Enhanced version of the existing RulesResult object with categorization and standardized severity levels.

**Fields**:
- `name`: str - Descriptive unique identifier for the rule (existing field)
- `passed`: bool - Indicates if the rule passed (True) or failed/violated (False) (existing field) 
- `message`: str - Clear, actionable description of validation result (existing field)
- `details`: str | None - Enhanced contextual information including location, suggestions, and remediation guidance (existing field, enhanced content)
- `category`: str - NEW - Logical grouping of related rules (e.g., "type_safety", "security", "performance")
- `severity`: str - NEW - Standardized severity level ("info", "warning", "error", "critical") replacing flexible "level" field

**Validation Rules**:
- `name` must be non-empty string
- `category` must be one of predefined categories
- `severity` must be one of ["info", "warning", "error", "critical"]
- `message` must be non-empty string
- `details` can be None or non-empty string
- `passed` determines if result represents a violation (False) or success (True)

**State Transitions**:
- Validation results are immutable once created
- No state changes after instantiation
- Filtering creates new collections without modifying original objects

### SeverityLevel (Enumeration)

**Purpose**: Standardized severity levels for consistent handling across the system.

**Values**:
- `INFO`: Informational messages, lowest priority
- `WARNING`: Issues that should be addressed but don't block
- `ERROR`: Serious issues that should block builds/merges  
- `CRITICAL`: Security or critical functionality issues requiring immediate attention

**Hierarchy**: CRITICAL > ERROR > WARNING > INFO

### RuleCategory (Enumeration)

**Purpose**: Logical groupings for rule organization and filtering.

**Categories**:
- `TYPE_SAFETY`: Type hints, annotations, mypy-related rules
- `CODE_STYLE`: Formatting, naming conventions, style guide compliance
- `SECURITY`: Security vulnerabilities, unsafe patterns
- `PERFORMANCE`: Performance issues, inefficient code patterns
- `DOCUMENTATION`: Docstrings, comments, documentation coverage
- `TESTING`: Test coverage, test quality, test organization
- `DEPENDENCIES`: Dependency management, version compatibility
- `COMPLEXITY`: Code complexity, maintainability metrics

### ValidationContext (Data Structure)

**Purpose**: Structured information for the enhanced details field.

**Components**:
- `file_path`: str | None - Location of the validation issue
- `line_number`: int | None - Specific line where issue occurs
- `column_number`: int | None - Specific column position
- `code_snippet`: str | None - Relevant code context
- `suggested_fix`: str | None - Recommended remediation
- `related_rules`: list[str] - Related validation rules
- `external_links`: list[str] - Documentation or reference links

### ValidationSummary (Aggregate Entity)

**Purpose**: Aggregated view of validation results for reporting and decision-making.

**Fields**:
- `total_results`: int - Total number of validation results
- `passed_count`: int - Number of successful validations
- `failed_count`: int - Number of failed validations (violations)
- `by_category`: dict[str, int] - Count of results per category
- `by_severity`: dict[str, int] - Count of results per severity level
- `violation_rate`: float - Percentage of failed validations
- `critical_violations`: int - Count of critical severity violations

## Relationships

```
RulesResult (enhanced)
├── has severity: SeverityLevel
├── belongs to category: RuleCategory  
├── contains details: ValidationContext (structured)
└── aggregates into: ValidationSummary

ValidationSummary
└── summarizes: Collection[RulesResult]
```

## Migration Strategy

### Backward Compatibility
- Existing `level` field mapping to `severity` with default transformation
- New fields added with sensible defaults for existing data
- Constructor overloads to support both old and new usage patterns

### Default Values
- `category`: "general" for uncategorized rules
- `severity`: "warning" for unmapped levels
- Enhanced `details`: Preserve existing string content as base context

## Usage Patterns

### Creating Enhanced Results
```python
# New enhanced usage
result = RulesResult(
    name="missing_type_hints",
    category="type_safety", 
    severity="warning",
    passed=False,
    message="Function 'calculate_total' is missing type hints",
    details="Add type hints: def calculate_total(items: List[Item]) -> Decimal"
)

# Backward compatible usage (still works)
result = RulesResult(
    name="style_check",
    passed=True,
    message="Code style compliance verified"
)
```

### Filtering and Analysis
```python
# Filter by severity
critical_issues = [r for r in results if r.severity == "critical" and not r.passed]

# Group by category  
by_category = defaultdict(list)
for result in results:
    by_category[result.category].append(result)

# Get violations only
violations = [r for r in results if not r.passed]
```