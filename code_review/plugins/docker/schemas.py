from pathlib import Path

from pydantic import BaseModel, Field


class DockerImageSchema(BaseModel):
    name : str = Field(description="The name of the Docker image, e.g., python, node, etc.")
    version : str = Field(description="The version of the Docker image, e.g., 3.9, 14, etc.")
    operating_system : str | None = Field(default=None, description="The operating system variant, e.g., slim, alpine, etc.")


    def __str__(self):
        os_part = f"-{self.operating_system}" if self.operating_system else ""
        return f"{self.name}:{self.version}{os_part}"

    def __lt__(self, other) -> bool:
        if not isinstance(other, DockerImageSchema):
            return NotImplemented

        if self.operating_system != other.operating_system or self.name != other.name :
            return (self.name, self.version, self.operating_system) < (other.name, other.version, other.operating_system)
        version_parts = self.version.split(".")
        other_version_parts = other.version.split(".")

        # Pad the shorter list with "0"s
        max_len = max(len(version_parts), len(other_version_parts))
        version_parts += ["0"] * (max_len - len(version_parts))
        other_version_parts += ["0"] * (max_len - len(other_version_parts))

        for self_part, other_part in zip(version_parts, other_version_parts):
            try:
                self_num = int(self_part)
                other_num = int(other_part)
                if self_num != other_num:
                    return self_num < other_num
            except ValueError:
                if self_part != other_part:
                    return self_part < other_part



class DockerfileSchema(BaseModel):
    version: str = Field(description="The version found in the Dockerfile")
    expected_version: str | None = Field(default=None, description="The expected version to update to, if applicable")
    product: str = Field(description="The product name, e.g., python, node, etc.")
    file: Path = Field(description="Path to the Dockerfile")
