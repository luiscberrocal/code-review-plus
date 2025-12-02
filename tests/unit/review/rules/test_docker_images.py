from unittest.mock import MagicMock

from code_review.review.rules.docker_image_rules import check
from tests.unit.plugins.docker.docker_factories import DockerfileSchemaFactory


class TestCheckImageVersion:
    def make_dockerfile(self, image, expected_image, expected_version, path="Dockerfile"):
        dockerfile = MagicMock()
        dockerfile.image = image
        dockerfile.expected_image = expected_image
        dockerfile.expected_version = expected_version
        dockerfile.path = path
        return dockerfile

    def test_image_up_to_date(self):
        docker_file = DockerfileSchemaFactory.create()
        docker_file.expected_image = docker_file.image

        code_review = MagicMock()
        code_review.source_folder = docker_file.file.parent
        code_review.docker_files = [docker_file]
        results = check(code_review)
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].level == "INFO"

    def test_image_outdated(self):
        docker_file = DockerfileSchemaFactory.create(image__version="3.10")
        docker_file.expected_image = docker_file.image.model_copy()
        docker_file.expected_image.version = "3.12"

        code_review = MagicMock()
        code_review.source_folder = docker_file.file.parent
        code_review.docker_files = [docker_file]
        results = check(code_review)
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].level == "ERROR"

    def test_image_newer_than_expected(self):
        docker_file = DockerfileSchemaFactory.create(image__version="3.12")
        docker_file.expected_image = docker_file.image.model_copy()
        docker_file.expected_image.version = "3.11"

        code_review = MagicMock()
        code_review.source_folder = docker_file.file.parent
        code_review.docker_files = [docker_file]
        results = check(code_review)
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].level == "WARNING"
