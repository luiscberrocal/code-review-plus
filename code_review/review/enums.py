from enum import Enum


class ReviewRuleLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReviewRuleLevelIcon(Enum):
    INFO = "✅"
    WARNING = "⚠"
    ERROR = "❌"
    CRITICAL = "🔥"
