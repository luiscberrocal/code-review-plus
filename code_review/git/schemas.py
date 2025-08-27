from datetime import datetime

from pydantic import BaseModel, Field


class BranchSchema(BaseModel):
    """Schema for branch information."""

    name: str
    author: str
    email: str
    hash: str
    date: datetime | None = None
    linting_errors: int = Field(default=-1, description="Number of linting errors found by ruff. -1 means not checked")
    min_coverage: float | None =  Field(default=None, description="Minimum coverage based on the Makefile")


