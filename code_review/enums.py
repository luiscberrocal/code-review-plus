from enum import Enum


class ReviewRuleLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ReviewRuleLevelIcon(Enum):
    INFO = "✅"
    WARNING = "⚠"
    ERROR = "❌"
    CRITICAL = "🔥"


class SeverityLevel(int, Enum):
    """Standardized severity levels for rule validation results."""

    INFO = 100
    WARNING = 200
    ERROR = 300
    CRITICAL = 400


class RuleCategory(str, Enum):
    """Logical groupings for rule organization and filtering."""

    TYPE_SAFETY = "type_safety"
    CODE_STYLE = "code_style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPENDENCIES = "dependencies"
    COMPLEXITY = "complexity"
    GENERAL = "general"
