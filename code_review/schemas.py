import logging
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from code_review.dependencies.pip.schemas import RequirementInfo

logger = logging.getLogger(__name__)


class SeverityLevel(str, Enum):
    """Standardized severity levels for rule validation results."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


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


class SemanticVersion(BaseModel):
    """Schema for semantic versioning."""

    name: str = Field(title="Name of the library or application")
    major: int
    minor: int
    patch: int
    source: Path

    def __str__(self):  # noqa D105
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse_version(cls, version: str, name: str, file_path: Path, raise_error: bool = False) -> "SemanticVersion":
        """Parse a version string into a SemanticVersion object."""
        logger.debug("Parsing version '%s' from file '%s'", version, file_path)
        parts = version.split(".")

        if len(parts) != 3:
            logger.error("Invalid version '%s'", version)
            if raise_error:
                raise ValueError(f"Invalid version format: {version}")
            major, minor, patch = 0, 0, 0
            return cls(major=major, minor=minor, patch=patch, source=file_path, name=name)
        try:
            major, minor, patch = map(int, parts)
        except ValueError:
            major, minor, patch = 0, 0, 0
        return cls(major=major, minor=minor, patch=patch, source=file_path, name=name)

    def __lt__(self, other):
        if not isinstance(other, SemanticVersion):
            return NotImplemented

        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch


class BranchSchema(BaseModel):
    """Schema for branch information."""

    name: str
    author: str
    email: str
    hash: str
    date: datetime | None = None
    linting_errors: int = Field(default=-1, description="Number of linting errors found by ruff. -1 means not checked")
    min_coverage: float | None = Field(default=None, description="Minimum coverage based on the Makefile")
    version: SemanticVersion | None = Field(default=None, description="Semantic version from the version file")
    changelog_versions: list[SemanticVersion] = Field(
        default_factory=list, description="List of last 5 semantic versions found in the changelog"
    )
    requirements_to_update: list[RequirementInfo] = Field(
        default_factory=list, description="List of dependencies that can be updated"
    )
    formatting_errors: int = Field(
        default=-1, description="Number of formatting errors found by black. -1 means not checked"
    )

    def __lt__(self, other) -> bool:
        if not isinstance(other, BranchSchema):
            return NotImplemented

        # Handle cases where dates are None
        self_date = self.date if self.date is not None else datetime.min
        other_date = other.date if other.date is not None else datetime.min

        return self_date < other_date


class RulesResult(BaseModel):
    """Enhanced schema for rules result with categorization and standardized severity levels."""

    name: str = Field(description="Name of the rule")
    passed: bool = Field(description="Indicates if the rule passed or failed", default=False)
    message: str
    details: str | None = None
    
    # NEW FIELDS - Enhanced validation system
    category: RuleCategory = Field(default=RuleCategory.GENERAL, description="Logical grouping of related rules")
    severity: SeverityLevel = Field(default=SeverityLevel.WARNING, description="Standardized severity level")
    
    # Backward compatibility for existing 'level' field
    @property
    def level(self) -> str:
        """Backward compatibility property mapping severity to old level field."""
        return self.severity.value
    
    def is_violation(self) -> bool:
        """Check if this result represents a rule violation."""
        return not self.passed
    
    def is_blocking(self) -> bool:
        """Check if this result should block builds/merges."""
        return not self.passed and self.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]
