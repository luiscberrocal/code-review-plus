import pytest

from code_review.plugins.docker.docker_files.handlers import (
    extract_using_from,
    parse_dockerfile,
)
from code_review.plugins.docker.schemas import DockerfileSchema


class TestExtractUsingFrom:
    @pytest.mark.parametrize(
        "dockerfile_content,expected",
        [
            ("FROM python:3.10.5-slim", None),
            (
                "FROM docker.io/postgres:17",
                {"source": "docker.io", "product": "postgres", "version": "17"},
            ),
            (
                "FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS python",
                {"source": "ghcr.io/astral-sh", "product": "uv", "version": "python3.13-bookworm-slim"},
            ),
            (
                "FROM docker.io/traefik:2.11.2",
                {"source": "docker.io", "product": "traefik", "version": "2.11.2"},
            ),
            (
                "FROM docker.io/nginx:1.17.8-alpine",
                {"source": "docker.io", "product": "nginx", "version": "1.17.8-alpine"},
            ),
            ("FROM node:18.0.0", None),
        ],
    )
    def test_extract_using_from(self, dockerfile_content, expected):
        result = extract_using_from(dockerfile_content, product=None)
        assert result == expected


class TestParseDockerfile:
    def test_parse_dockerfile(self, fixtures_folder):
        compose_folder = fixtures_folder / "compose"
        dockerfiles = list(compose_folder.glob("**/Dockerfile"))
        for dockerfile in dockerfiles:
            dockerfile_schema = parse_dockerfile(dockerfile)
            print(dockerfile, " schema:", dockerfile_schema)

    def test_parse_dockerfile_using_from(self, fixtures_folder):
        compose_folder = fixtures_folder / "compose_from"

        dockerfiles = list(compose_folder.glob("**/Dockerfile"))

        for dockerfile in dockerfiles:
            dockerfile_schema = parse_dockerfile(dockerfile)
            print(dockerfile, " schema:", dockerfile_schema)

    def test_parse_valid_dockerfile(self, tmp_path):
        # Create a sample Dockerfile
        dockerfile_content = "FROM python:3.12.11-slim-bookworm"
        dockerfile_path = tmp_path / "Dockerfile"
        dockerfile_path.write_text(dockerfile_content)

        result = parse_dockerfile(dockerfile_path)
        assert isinstance(result, DockerfileSchema)
        assert result.product == "python"
        assert result.version == "3.12.11"
        assert result.image.name == "python"
        assert result.image.version == "3.12.11"

    def test_parse_missing_dockerfile(self, tmp_path):
        missing_path = tmp_path / "missing.Dockerfile"
        result = parse_dockerfile(missing_path)
        assert result is None

    def test_parse_missing_dockerfile_raise(self, tmp_path):
        missing_path = tmp_path / "missing.Dockerfile"
        with pytest.raises(FileNotFoundError):
            parse_dockerfile(missing_path, raise_error=True)

    def test_parse_dockerfile_with_invalid_content(self, tmp_path):
        dockerfile_path = tmp_path / "Dockerfile"
        dockerfile_path.write_text("INVALID CONTENT")
        result = parse_dockerfile(dockerfile_path)
        assert result is None
