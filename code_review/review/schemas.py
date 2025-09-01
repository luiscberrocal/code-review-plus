from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from code_review.schemas import BranchSchema

class SemanticVersion(BaseModel):
    """Schema for semantic versioning."""

    major: int
    minor: int
    patch: int
    source: Path

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse_version(cls, version: str, file_path: Path) -> "SemanticVersion":
        """Parse a version string into a SemanticVersion object."""
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        major, minor, patch = map(int, parts)
        return cls(major=major, minor=minor, patch=patch, source=file_path)

class CodeReviewSchema(BaseModel):
    """Schema for code review requests."""

    name: str = Field(description="Name of the project to code review")
    source_folder: Path
    makefile_path: Path | None
    date_created: datetime | None
    ticket: str | None = Field(default=None, description="Ticket associated with the code review")
    target_branch: BranchSchema
    base_branch: BranchSchema
