import pytest

from code_review.plugins.docker.docker_files.adapters import (
    content_to_node_adapter,
    content_to_postgres_adapter,
    content_to_python_adapter,
)
from code_review.plugins.docker.schemas import DockerImageSchema


class TestContentToPythonAdapter:
    @pytest.mark.parametrize(
        "content,expected",
        [
            (
                "ARG PYTHON_VERSION=3.10.5-slim",
                DockerImageSchema(name="python", version="3.10.5", operating_system="slim"),
            ),
            (
                "ARG PYTHON_VERSION=3.10.5-slim-bookworm",
                DockerImageSchema(name="python", version="3.10.5", operating_system="slim-bookworm"),
            ),
            (
                "FROM python:3.11.2-alpine",
                DockerImageSchema(name="python", version="3.11.2", operating_system="alpine"),
            ),
            (
                "FROM python:3.11.2-alpine3",
                DockerImageSchema(name="python", version="3.11.2", operating_system="alpine3"),
            ),
            ("FROM python:3.9", DockerImageSchema(name="python", version="3.9", operating_system=None)),
            ("FROM node:18.0.0", None),
            ("", None),
        ],
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
            (
                "FROM postgres:17.1-alpine",
                DockerImageSchema(name="postgres", version="17.1", operating_system="alpine"),
            ),
            (
                "FROM postgres:17.1-alpine3",
                DockerImageSchema(name="postgres", version="17.1", operating_system="alpine3"),
            ),
            ("FROM postgres:15", DockerImageSchema(name="postgres", version="15", operating_system=None)),
            ("FROM python:3.10.5-slim", None),
            ("", None),
        ],
    )
    def test_postgres_adapter(self, content, expected):
        result = content_to_postgres_adapter(content)
        if expected is None:
            assert result is None
        else:
            assert result.name == expected.name, f"Expected name {expected} but got {result}"
            assert result.version == expected.version
            assert result.operating_system == expected.operating_system


class TestContentToNodeAdapter:
    @pytest.mark.parametrize(
        "content,expected",
        [
            ("FROM node:18.0.0-alpine", DockerImageSchema(name="node", version="18.0.0", operating_system="alpine")),
            (
                "FROM node:18.0.0-alpine3.1",
                DockerImageSchema(name="node", version="18.0.0", operating_system="alpine3.1"),
            ),
            ("FROM node:20", DockerImageSchema(name="node", version="20", operating_system=None)),
            ("FROM postgres:17.1-alpine", None),
            ("", None),
        ],
    )
    def test_node_adapter(self, content, expected):
        result = content_to_node_adapter(content)
        if expected is None:
            assert result is None
        else:
            assert result.name == expected.name
            assert result.version == expected.version
            assert result.operating_system == expected.operating_system
