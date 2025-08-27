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
    min_coverage: float | None = Field(default=None, description="Minimum coverage based on the Makefile")

    def __lt__(self, other):
        if not isinstance(other, BranchSchema):
            return NotImplemented

        # Handle cases where dates are None
        self_date = self.date if self.date is not None else datetime.min
        other_date = other.date if other.date is not None else datetime.min

        return self_date < other_date
