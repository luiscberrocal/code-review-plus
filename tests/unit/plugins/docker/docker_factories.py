# factories/docker_schemas.py
import factory
from pathlib import Path

from factory import Iterator, lazy_attribute

from code_review.plugins.docker.schemas import DockerImageSchema, DockerfileSchema

class DockerImageSchemaFactory(factory.Factory):
    class Meta:
        model = DockerImageSchema

    name = Iterator(["python", "postgres", "node"])
    version = Iterator(["3.12.11", "16.10", "20.19.4"])
    operating_system = Iterator(["slim-bookworm", "bookworm", "alpine3"])

class DockerfileSchemaFactory(factory.Factory):
    class Meta:
        model = DockerfileSchema

    file = factory.LazyFunction(lambda: Path("/tmp/Dockerfile"))
    image = factory.SubFactory(DockerImageSchemaFactory)
    expected_image = factory.SubFactory(DockerImageSchemaFactory)

    @lazy_attribute
    def version(self):
        return self.image.version

    @lazy_attribute
    def expected_version(self):
        if self.expected_image:
            return self.expected_image.version
        return "0.0.0"

    @lazy_attribute
    def product(self):
        return self.image.name
