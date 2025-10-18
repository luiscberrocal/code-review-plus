import pytest
from code_review.plugins.docker.schemas import DockerImageSchema

class TestDockerImageSchema:
    def test_initialization(self):
        img = DockerImageSchema(name="python", version="3.10.5", operating_system="slim")
        assert img.name == "python"
        assert img.version == "3.10.5"
        assert img.operating_system == "slim"

    @pytest.mark.parametrize(
        "img1,img2,expected",
        [
            # Different names
            (DockerImageSchema(name="python", version="3.10", operating_system="slim"),
             DockerImageSchema(name="node", version="3.10", operating_system="slim"),
             False),
            # Same name, different version
            (DockerImageSchema(name="python", version="3.9", operating_system="slim"),
             DockerImageSchema(name="python", version="3.10", operating_system="slim"),
             True),
            # Same name and version, different OS
            (DockerImageSchema(name="python", version="3.10", operating_system="alpine"),
             DockerImageSchema(name="python", version="3.10", operating_system="slim"),
             True),
            # Same everything
            (DockerImageSchema(name="python", version="3.10", operating_system="slim"),
             DockerImageSchema(name="python", version="3.10", operating_system="slim"),
             False),
            # Version with more parts
            (DockerImageSchema(name="python", version="3.10.1", operating_system="slim"),
             DockerImageSchema(name="python", version="3.10.2", operating_system="slim"),
             True),
            # Non-numeric version parts
            (DockerImageSchema(name="python", version="3.10-beta", operating_system="slim"),
             DockerImageSchema(name="python", version="3.10-rc", operating_system="slim"),
             True),
        ]
    )
    def test_lt(self, img1, img2, expected):
        assert (img1 < img2) == expected, f"Failed for {img1} < {img2}"

    def test_lt_version_specificity(self):
        img1 = DockerImageSchema(name="python", version="3.10", operating_system="slim")
        img2 = DockerImageSchema(name="python", version="3.10.1", operating_system="slim")
        assert (img1 < img2) is True

    def test_equals(self):
        img1 = DockerImageSchema(name="python", version="3.10", operating_system="slim")
        img2 = DockerImageSchema(name="python", version="3.10", operating_system="slim")
        assert (img1 < img2) is False

    def test_lt_node_python(self):
        img1 = DockerImageSchema(name="python", version="3.10", operating_system="slim")
        img2 = DockerImageSchema(name="node", version="3.10", operating_system="slim")

        image_list = [img1, img2]
        image_list.sort()
        assert image_list[0] == img2
        assert image_list[1] == img1

        assert (img1 < img2) is False

    def test_lt_not_implemented(self):
        img = DockerImageSchema(name="python", version="3.10", operating_system="slim")
        assert img.__lt__("not_a_schema") is NotImplemented