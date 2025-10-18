import re

from code_review.plugins.docker.schemas import DockerImageSchema


def content_to_python_adapter(content: str) -> DockerImageSchema | None:
    """Adapter to convert content to a Python dictionary."""

    python_pattern = [re.compile(r"ARG\s.+=(?P<version>\d\.\d+[\.\d]*)\-?([a-z\-]+)"),
                      re.compile(r"python:(?P<version>\d\.\d+[\.\d]*)\-?([a-z\-]+)")]

    for pattern in python_pattern:
        match = pattern.search(content)
        if match:
            version = match.group(1)
            return DockerImageSchema(name="python", version=version, operating_system="unknown")
    return None

def content_to_postgres_adapter(content: str) -> DockerImageSchema | None:
    """Adapter to convert content to a Postgres dictionary."""

    postgres_pattern = re.compile(r"postgres:(?P<version>\d\.\d+[\.\d]*)\-?(?P<os>[a-z\-]+)")

    match = postgres_pattern.search(content)
    if match:
        version = match.group(1)
        return DockerImageSchema(name="postgres", version=version, operating_system="unknown")
    return None
