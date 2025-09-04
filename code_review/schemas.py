import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SemanticVersion(BaseModel):
    """Schema for semantic versioning."""

    major: int
    minor: int
    patch: int
    source: Path

    def __str__(self): # noqa D105
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse_version(cls, version: str, file_path: Path) -> "SemanticVersion":
        """Parse a version string into a SemanticVersion object."""
        logger.debug("Parsing version '%s' from file '%s'", version, file_path)
        parts = version.split(".")

        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        try:
            major, minor, patch = map(int, parts)
        except ValueError:
            major, minor, patch = 0, 0, 0
        return cls(major=major, minor=minor, patch=patch, source=file_path)


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

    def __lt__(self, other) -> bool:
        if not isinstance(other, BranchSchema):
            return NotImplemented

        # Handle cases where dates are None
        self_date = self.date if self.date is not None else datetime.min
        other_date = other.date if other.date is not None else datetime.min

        return self_date < other_date
