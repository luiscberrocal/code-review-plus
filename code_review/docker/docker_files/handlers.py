import logging
import re
from pathlib import Path

from code_review.docker.schemas import DockerfileSchema
from code_review.settings import CURRENT_CONFIGURATION

logger = logging.getLogger(__name__)


def get_versions_from_dockerfile(dockerfile_content: str) -> dict:
    """Parses a Dockerfile to extract Python, Postgres, and Node.js versions.

    Args:
        dockerfile_content (str): The content of the Dockerfile as a string.

    Returns:
        dict: A dictionary containing the extracted versions. Keys are
              'python_version', 'postgres_version', and 'node_version'.
              Values are the version strings or None if not found.
    """
    versions = {
        "version": None,
        "product": None,
    }

    # Regex patterns for different technologies
    python_arg_pattern = re.compile(r"ARG\s+PYTHON_VERSION=([\d.]+[\w-]*)")
    python_from_pattern = re.compile(r"FROM.*python:([\d.]+[\w-]*)")
    postgres_from_pattern = re.compile(r"FROM.*postgres:([\d.]+[\w-]*)")
    node_from_pattern = re.compile(r"FROM.*node:([\d.]+[\w-]*)")

    # --- Search for Python version ---
    match_python_arg = python_arg_pattern.search(dockerfile_content)
    if match_python_arg:
        versions["version"] = match_python_arg.group(1)
        versions["product"] = "python"
    else:
        # Fallback to checking the FROM statement directly
        match_python_from = python_from_pattern.search(dockerfile_content)
        if match_python_from:
            # Ensure it's not a FROM statement using a variable
            if not re.search(r"FROM.*python:\$\{{0,1}PYTHON_VERSION\}{0,1}", dockerfile_content):
                versions["version"] = match_python_from.group(1)
                versions["product"] = "python"

    # --- Search for Postgres version ---
    match_postgres_from = postgres_from_pattern.search(dockerfile_content)
    if match_postgres_from:
        versions["version"] = match_postgres_from.group(1)
        versions["product"] = "postgres"

    # --- Search for Node.js version ---
    match_node_from = node_from_pattern.search(dockerfile_content)
    if match_node_from:
        versions["version"] = match_node_from.group(1)
        versions["product"] = "node"

    return versions


def parse_dockerfile(dockerfile_path: Path) -> DockerfileSchema | None:
    """Reads a Dockerfile and extracts version information.

    Args:
        dockerfile_path (str): The file path to the Dockerfile.

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
        return None
    except Exception as e:
        logger.error("An error occurred while reading the Dockerfile: %s", e)
        return None
