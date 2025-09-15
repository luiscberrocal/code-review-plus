import re


def get_python_version_from_dockerfile(dockerfile_content:str) -> str | None:
    """Parses a Dockerfile to extract the Python version.

    Args:
        dockerfile_content (str): The content of the Dockerfile as a string.

    Returns:
        str or None: The Python version string if found, otherwise None.
    """
    # Regex to find ARG statements that define PYTHON_VERSION
    arg_pattern = re.compile(r"ARG\s+PYTHON_VERSION=([\d.]+[\w-]*)")

    # Regex to find the FROM statement that uses PYTHON_VERSION
    from_pattern = re.compile(r"FROM.*python:\$\{{0,1}PYTHON_VERSION\}{0,1}")

    # Check for the ARG PYTHON_VERSION first
    match_arg = arg_pattern.search(dockerfile_content)
    if match_arg:
        return match_arg.group(1)

    # If ARG is not found, check for a direct FROM statement with a version
    # This is a fallback for cases where the version isn't in an ARG.
    # This is a more general pattern, but the ARG is more specific and reliable
    # for the user's example.
    from_with_version_pattern = re.compile(r"FROM.*python:([\d.]+[\w-]*)")
    match_from = from_with_version_pattern.search(dockerfile_content)
    if match_from:
        # We need to make sure this isn't the FROM statement using the variable
        if not from_pattern.search(dockerfile_content):
            return match_from.group(1)

    return None



