from code_review.docker_hub.schemas import ImageTag

import re


def include_by_regex(tag: ImageTag, regex: str) -> bool:
    """
    Check if the image name matches the given regex pattern.

    """
    regexp = re.compile(regex)
    match = regexp.match(tag.name)
    if match:
        return True
    else:
        return False
