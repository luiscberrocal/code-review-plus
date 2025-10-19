import logging
import re
from pathlib import Path

from code_review.plugins.docker.docker_files.adapters import ContentAdapter, content_to_image_adapters
from code_review.plugins.docker.schemas import DockerfileSchema, DockerImageSchema
from code_review.settings import CURRENT_CONFIGURATION

logger = logging.getLogger(__name__)


def extract_using_from(dockerfile_content: str, product: str) -> dict | None:
    """Extracts version using a FROM pattern for a specific product."""
    pattern = re.compile(r"FROM\s(?P<source>.+)/(?P<product>\w+):(?P<version>[\w\.-]+)")
    match = pattern.search(dockerfile_content)
    if match:
        return {"source": match.group("source"), "product": match.group("product"), "version": match.group("version")}

    return None


def get_image_info_from_dockerfile_content(dockerfile_content: str,
                                           parsers: dict[str, ContentAdapter]) -> DockerImageSchema | None:
    """Gets Docker image information from Dockerfile content using provided parsers."""
    for product, parser in parsers.items():
        image_info = parser(dockerfile_content)
        if image_info:
            return image_info
    return None


def parse_dockerfile(dockerfile_path: Path, raise_error: bool = False) -> DockerfileSchema | None:
    """Reads a Dockerfile and extracts version information.

    Args:
        dockerfile_path (Path): The file path to the Dockerfile.
        raise_error (bool, optional): Whether to raise an exception when parsing errors.

    Returns:
        DockerfileSchema: Dockerfile schema with extracted version information.
    """
    try:
        content = dockerfile_path.read_text()
        version_info = {"file": dockerfile_path}
        docker_image_schema = get_image_info_from_dockerfile_content(content, parsers=content_to_image_adapters)
        if docker_image_schema:
            version_info["product"] = docker_image_schema.name
            version_info["version"] = docker_image_schema.version
            version_info["image"] = docker_image_schema

        images = CURRENT_CONFIGURATION.get("docker_images", {})

        image = images.get(version_info["product"], None)
        version_info["expected_version"] = image.version
        version_info["expected_image"] = image
        return DockerfileSchema(**version_info)
    except FileNotFoundError:
        logger.error("Dockerfile not found at path: %s", dockerfile_path)
        if raise_error:
            raise FileNotFoundError(f"Error: The file '{dockerfile_path}' was not found.")
        return None
    except Exception as e:
        logger.error("An error occurred while reading the Dockerfile %s: %s", dockerfile_path, e)
        if raise_error:
            raise e
        return None
