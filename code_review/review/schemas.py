from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from code_review.docker.schemas import DockerfileSchema
from code_review.schemas import BranchSchema


class CodeReviewSchema(BaseModel):
    """Schema for code review requests."""

    name: str = Field(description="Name of the project to code review")
    is_rebased: bool = Field(
        default=False, description="Indicates if the target branch has been rebased onto the base branch"
    )
    source_folder: Path
    makefile_path: Path | None
    date_created: datetime | None
    ticket: str | None = Field(default=None, description="Ticket associated with the code review")
    target_branch: BranchSchema
    base_branch: BranchSchema
    docker_files: list[DockerfileSchema] | None = Field(
        default_factory=list, description="List of Dockerfiles found in the project"
    )
