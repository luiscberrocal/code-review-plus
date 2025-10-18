import pytest
from code_review.plugins.docker.docker_files.adapters import (
    content_to_python_adapter,
    content_to_postgres_adapter,
    content_to_node_adapter,
)
from code_review.plugins.docker.schemas import DockerImageSchema

class TestContentToPythonAdapter:
    @pytest.mark.parametrize(
        "content,expected",
        [
            ("ARG PYTHON_VERSION=3.10.5-slim", DockerImageSchema(name="python", version="3.10.5", operating_system="unknown")),
            ("FROM python:3.11.2-alpine", DockerImageSchema(name="python", version="3.11.2", operating_system="unknown")),
            ("FROM python:3.9", DockerImageSchema(name="python", version="3.9", operating_system="unknown")),
            ("FROM node:18.0.0", None),
            ("", None),
        ]
    )
    def test_python_adapter(self, content, expected):
        result = content_to_python_adapter(content)
        if expected is None:
            assert result is None
        else:
            assert result.name == expected.name
            assert result.version == expected.version
            assert result.operating_system == expected.operating_system

class TestContentToPostgresAdapter:
    @pytest.mark.parametrize(
        "content,expected",
        [
            ("FROM postgres:17.1-alpine", DockerImageSchema(name="postgres", version="17.1", operating_system="unknown")),
            ("FROM postgres:15", DockerImageSchema(name="postgres", version="15", operating_system="unknown")),
            ("FROM python:3.10.5-slim", None),
            ("", None),
        ]
    )
    def test_postgres_adapter(self, content, expected):
        result = content_to_postgres_adapter(content)
        if expected is None:
            assert result is None
        else:
            assert result.name == expected.name
            assert result.version == expected.version
            assert result.operating_system == expected.operating_system

class TestContentToNodeAdapter:
    @pytest.mark.parametrize(
        "content,expected",
        [
            ("FROM node:18.0.0-alpine", DockerImageSchema(name="node", version="18.0.0", operating_system="unknown")),
            ("FROM node:20", DockerImageSchema(name="node", version="20", operating_system="unknown")),
            ("FROM postgres:17.1-alpine", None),
            ("", None),
        ]
    )
    def test_node_adapter(self, content, expected):
        result = content_to_node_adapter(content)
        if expected is None:
            assert result is None
        else:
            assert result.name == expected.name
            assert result.version == expected.version
            assert result.operating_system == expected.operating_system