import logging
import re
from pathlib import Path

from code_review.plugins.docker.schemas import DockerfileSchema
from code_review.settings import CURRENT_CONFIGURATION

logger = logging.getLogger(__name__)



def get_versions_from_dockerfile(dockerfile_content: str) -> dict:
    """Parses a Dockerfile to extract product and version information using multiple patterns per product."""
    versions = {
        "version": None,
        "product": None,
    }

    # Define patterns for each product
    product_patterns = {
        "python": [
            re.compile(r"ARG\s+PYTHON_VERSION=([\d.]+[\w-]*)"),
            re.compile(r"FROM.*python:([\d.]+[\w-]*)"),
        ],
        "postgres": [
            re.compile(r"FROM.*postgres:([\d.]+[\w-]*)"),
        ],
        "node": [
            re.compile(r"FROM.*node:([\d.]+[\w-]*)"),
        ],
    }

    for product, patterns in product_patterns.items():
        for pattern in patterns:
            match = pattern.search(dockerfile_content)
            if match:
                # For python, skip FROM with variable
                if product == "python" and "FROM" in pattern.pattern:
                    if re.search(r"FROM.*python:\$\{{0,1}PYTHON_VERSION\}{0,1}", dockerfile_content):
                        continue
                versions["version"] = match.group(1)
                versions["product"] = product
                return versions  # Return on first match

    return versions


def extract_using_from(dockerfile_content: str, product: str) -> dict | None:
    """Extracts version using a FROM pattern for a specific product."""
    pattern = re.compile(r"FROM\s(?P<source>.+)/(?P<product>\w+):(?P<version>[\w\.-]+)")
    match = pattern.search(dockerfile_content)
    if match:
        return {"source": match.group("source"), "product": match.group("product"), "version": match.group("version")}

    return None


def parse_dockerfile(dockerfile_path: Path, raise_error: bool = False) -> DockerfileSchema | None:
    """Reads a Dockerfile and extracts version information.

    Args:
        dockerfile_path (Path): The file path to the Dockerfile.
        raise_error (bool, optional): Whether to raise an exception when parsing errors.

    Returns:
        dict: A dictionary containing the extracted versions.
    """
    try:
        content = dockerfile_path.read_text()
        version_info = get_versions_from_dockerfile(content)
        version_info["file"] = dockerfile_path
        images = CURRENT_CONFIGURATION.get("docker_images", {})

        version_info["expected_version"] = images.get(version_info["product"], None)
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
