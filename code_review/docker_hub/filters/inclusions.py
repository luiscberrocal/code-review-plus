

def include_by_regex(image_name: str, regex: str) -> bool:
    """
    Check if the image name matches the given regex pattern.

    :param image_name: The name of the Docker image.
    :param regex: The regex pattern to match against the image name.
    :return: True if the image name matches the regex, False otherwise.
    """
    import re
    return re.search(regex, image_name) is not None