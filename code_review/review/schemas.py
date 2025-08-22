from pathlib import Path

from pydantic import BaseModel


class BranchSchema(BaseModel):
    """
    Schema for branch information.
    """
    name: str
    author: str
    linting_errors: int = -1


class CodeReviewSchema:
    """
    Schema for code review requests.
    """
    name: str
    source_folder: Path
    target_branch: BranchSchema
    base_branch: BranchSchema
