import re
from collections.abc import Callable
from typing import TypeAlias

from code_review.plugins.docker.schemas import DockerImageSchema


def content_to_python_adapter(content: str) -> DockerImageSchema | None:
    """Adapter to convert content to a Python dictionary."""
    python_patterns = [
        re.compile(r"ARG\s.+=(?P<version>\d\.\d+[\.\d]*)\-?(?P<os>[a-z\-\d\.]+)?"),
        re.compile(r"python:(?P<version>\d\.\d+[\.\d]*)\-?(?P<os>[a-z\-\d\.]+)?"),
    ]

    for pattern in python_patterns:
        match = pattern.search(content)
        if match:
            version = match.group(1)
            operating_system = match.group(2)
            return DockerImageSchema(name="python", version=version, operating_system=operating_system)
    return None


def content_to_postgres_adapter(content: str) -> DockerImageSchema | None:
    """Adapter to convert content to a Postgres dictionary."""
    postgres_patterns = [re.compile(r"postgres:(?P<version>\d+\.?\d*[\.\d]*)\-?(?P<os>[a-z\-\d\.]+)?")]

    for postgres_pattern in postgres_patterns:
        match = postgres_pattern.search(content)
        if match:
            version = match.group(1)
            operating_system = match.group(2)
            return DockerImageSchema(name="postgres", version=version, operating_system=operating_system)
    return None


def content_to_node_adapter(content: str) -> DockerImageSchema | None:
    """Adapter to convert content to a Node.js dictionary."""
    node_patterns = [re.compile(r"node:(?P<version>\d+[\.\d]*)\-?(?P<os>[a-z\-\d\.]+)?")]

    for node_pattern in node_patterns:
        match = node_pattern.search(content)
        if match:
            version = match.group(1)
            operating_system = match.group(2)
            return DockerImageSchema(name="node", version=version, operating_system=operating_system)
    return None


ContentAdapter: TypeAlias = Callable[[str], DockerImageSchema | None]

content_to_image_adapters: dict[str, ContentAdapter] = {
    "python": content_to_python_adapter,
    "postgres": content_to_postgres_adapter,
    "node": content_to_node_adapter,
}
