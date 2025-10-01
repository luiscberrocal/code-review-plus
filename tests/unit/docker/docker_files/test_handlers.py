from code_review.docker.docker_files.handlers import get_versions_from_dockerfile, parse_dockerfile


def test_dockerfile_handler(fixtures_folder):
    compose_folder = fixtures_folder / "compose"
    dockerfiles = list(compose_folder.glob("**/Dockerfile"))
    for dockerfile in dockerfiles:
        content = dockerfile.read_text()
        version = get_versions_from_dockerfile(content)
        print(dockerfile, " version:", version)


def test_parse_dockerfile(fixtures_folder):
    compose_folder = fixtures_folder / "compose"
    dockerfiles = list(compose_folder.glob("**/Dockerfile"))
    for dockerfile in dockerfiles:
        dockerfile_schema = parse_dockerfile(dockerfile)
        print(dockerfile, " schema:", dockerfile_schema)


def test_parse_dockerfile_using_from(fixtures_folder):
    compose_folder = fixtures_folder / "compose_from"

    dockerfiles = list(compose_folder.glob("**/Dockerfile"))

    for dockerfile in dockerfiles:
        dockerfile_schema = parse_dockerfile(dockerfile)
        print(dockerfile, " schema:", dockerfile_schema)


import pytest


class TestGetVersionsFromDockerfile:
    @pytest.mark.parametrize(
        "dockerfile_content,expected",
        [
            (
                "FROM python:3.10.5-slim",
                {"version": "3.10.5-slim", "product": "python"},
            ),
            (
                "ARG PYTHON_VERSION=3.9.7\nFROM python:${PYTHON_VERSION}",
                {"version": "3.9.7", "product": "python"},
            ),
            (
                "FROM postgres:14.2",
                {"version": "14.2", "product": "postgres"},
            ),
            (
                "FROM node:18.0.0",
                {"version": "18.0.0", "product": "node"},
            ),
            (
                "FROM ubuntu:20.04",
                {"version": None, "product": None},
            ),
        ],
    )
    def test_get_versions(self, dockerfile_content, expected):
        result = get_versions_from_dockerfile(dockerfile_content)
        assert result == expected
