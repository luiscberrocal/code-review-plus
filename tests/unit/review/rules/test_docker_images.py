import pytest
from unittest.mock import MagicMock
from code_review.review.rules.docker_images import check_image_version
from code_review.schemas import RulesResult
from hypothesis import given, strategies as st

from tests.unit.plugins.coverage.coverage_factories import DockerfileSchemaFactory


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
        code_review.docker_files = [docker_file]
        results = check_image_version(code_review)
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].level == "INFO"

    def test_image_outdated(self):
        docker_file = DockerfileSchemaFactory.create(image__version="3.10")
        docker_file.expected_image = docker_file.image.model_copy()
        docker_file.expected_image.version = "3.12"

        code_review = MagicMock()
        code_review.docker_files = [docker_file]
        results = check_image_version(code_review)
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].level == "ERROR"

    def test_image_not_latest(self):
        image = MagicMock()
        image.name = "python"
        image.version = "3.11"
        expected_image = MagicMock()
        expected_image.name = "python"
        expected_image.version = "3.10"
        # image < expected_version is False, but not equal
        dockerfile = self.make_dockerfile(image, expected_image, expected_image)
        image.__lt__.return_value = False
        code_review = MagicMock()
        code_review.dockerfiles = [dockerfile]
        results = check_image_version(code_review)
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].level == "WARNING"

    @given(
        image_name=st.text(min_size=1, max_size=10),
        image_version=st.text(min_size=1, max_size=10),
        path=st.text(min_size=1, max_size=20)
    )
    def test_hypothesis_up_to_date(self, image_name, image_version, path):
        image = MagicMock()
        image.name = image_name
        image.version = image_version
        dockerfile = self.make_dockerfile(image, image, image_version, path)
        code_review = MagicMock()
        code_review.dockerfiles = [dockerfile]
        results = check_image_version(code_review)
        assert results[0].passed is True
        assert results[0].level == "INFO"