from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from code_review.schemas import BranchSchema


class CodeReviewSchema(BaseModel):
    """Schema for code review requests."""

    name: str = Field(description="Name of the project to code review")
    source_folder: Path
    makefile_path: Path | None
    date_created: datetime | None
    ticket: str | None = Field(default=None, description="Ticket associated with the code review")
    target_branch: BranchSchema
    base_branch: BranchSchema
