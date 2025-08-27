from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from code_review.git.schemas import BranchSchema


class CodeReviewSchema(BaseModel):
    """Schema for code review requests."""

    name: str = Field(description="Name of the project to code review")
    source_folder: Path
    makefile_path: Path | None
    date_created: datetime | None
    target_branch: BranchSchema
    base_branch: BranchSchema
