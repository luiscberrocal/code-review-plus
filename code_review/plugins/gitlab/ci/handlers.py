import logging
from pathlib import Path

from code_review.handlers.file_handlers import get_not_ignored
from code_review.yaml.adapters import parse_yaml_file

logger = logging.getLogger(__name__)


def handle_mult_targets(folder: Path, filename: str = ".gitlab-ci,tml") -> dict[str, list] | None:
    """

    Args:
        folder:
        filename:

    Returns:

    """
    files = get_not_ignored(folder, filename)
    if not files:
        return None
    if len(files) > 1:
        logger.error("Multiple .gitlab-ci.yml files found in the directory: %s", folder)
        return None
    ci_file = files[0]
    result = parse_yaml_file(ci_file)
    data = {}
    for key, value in result.items():
        if isinstance(value, dict) and "only" in value and isinstance(value["only"], list):
            data[key] = value["only"]
    return data
