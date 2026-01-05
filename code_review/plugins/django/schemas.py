from pathlib import Path

from pydantic import BaseModel, Field


class VettedVariableSchema(BaseModel):
    """Schema for a vetted Django settings variable."""

    name: str = Field(description="Variable name")
    type: str = Field(description="Python type of the variable")
    vetted: bool = Field(default=True, description="Whether the variable is vetted")
    modules: list[str] = Field(default_factory=list, description="Modules where this variable should appear")


class VariableIssueSchema(BaseModel):
    """Schema for a variable validation issue."""

    variable_name: str = Field(description="Name of the variable")
    issue_type: str = Field(description="Type of issue (unknown, wrong_module, missing)")
    module_name: str = Field(description="Name of the settings module")
    line_number: int | None = Field(default=None, description="Line number where the issue occurs")
    message: str = Field(description="Detailed message about the issue")


class SettingsValidationResultSchema(BaseModel):
    """Schema for settings validation results."""

    module_path: Path = Field(description="Path to the settings module")
    module_name: str = Field(description="Name of the module (e.g., 'base.py', 'local.py')")
    total_variables: int = Field(default=0, description="Total number of variables found")
    vetted_variables: int = Field(default=0, description="Number of vetted variables")
    issues: list[VariableIssueSchema] = Field(default_factory=list, description="List of validation issues")

    @property
    def has_issues(self) -> bool:
        """Check if there are any validation issues."""
        return len(self.issues) > 0

    @property
    def unknown_variables_count(self) -> int:
        """Count of unknown variables."""
        return len([i for i in self.issues if i.issue_type == "unknown"])

    @property
    def wrong_module_count(self) -> int:
        """Count of variables in wrong module."""
        return len([i for i in self.issues if i.issue_type == "wrong_module"])

    @property
    def missing_variables_count(self) -> int:
        """Count of missing expected variables."""
        return len([i for i in self.issues if i.issue_type == "missing"])
