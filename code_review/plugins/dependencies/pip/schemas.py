from pathlib import Path

from pydantic import BaseModel, Field


class RequirementInfo(BaseModel):
    """Schema for a pip requirement."""

    name: str = ""
    line: str = Field(description="The full line from the requirements file")
    file: Path

    def __eq__(self, other):
        return self.line == other.line and self.name == other.name


class PackageRequirement(BaseModel):
    """Model for a fully pinned parsed package requirement line, conforming to Pydantic structure.

    Fully pinned means it includes the package name and exact version.
    """

    name: str = Field(description="The canonicalized package name (e.g., 'djangorestframework' or 'ddtrace[django]').")
    version: str = Field(
        description="The exact version specified, e.g., '3.16.0'. None if only a specifier (like '>=') or a "
                    "VCS source is used.",
    )
    specifier: str | None = Field(None, description="The full version specifier string, e.g., '==' or '>=, <'.")
    source: str | None = Field(
        None,
        description="The full original source line, primarily used for complex VCS requirements (git+, hg+, etc.).",
    )
    file: Path | None = Field(default=None,
                              description="The path to the requirements file where this package is listed.")
    environment: str = Field(description="The environment to which the package is to be installed.")
