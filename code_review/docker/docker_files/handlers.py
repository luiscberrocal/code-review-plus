import re


def get_versions_from_dockerfile(dockerfile_content):
    """
    Parses a Dockerfile to extract a Python and Postgres version.

    Args:
        dockerfile_content (str): The content of the Dockerfile as a string.

    Returns:
        dict: A dictionary containing the extracted versions.
              Keys are 'python_version' and 'postgres_version'.
              Values are the version strings or None if not found.
    """
    versions = {
        "python_version": None,
        "postgres_version": None,
    }

    # Regex to find ARG statements for PYTHON_VERSION
    python_arg_pattern = re.compile(r"ARG\s+PYTHON_VERSION=([\d.]+[\w-]*)")

    # Regex to find FROM statements for python with a specific version.
    # This acts as a fallback if no ARG is found.
    python_from_pattern = re.compile(r"FROM.*python:([\d.]+[\w-]*)")

    # Regex to find FROM statements for postgres with a specific version.
    # We look for `postgres:` followed by the version string.
    postgres_from_pattern = re.compile(r"FROM.*postgres:([\d.]+[\w-]*)")

    # Search for Python version using ARG first
    match_python_arg = python_arg_pattern.search(dockerfile_content)
    if match_python_arg:
        versions["python_version"] = match_python_arg.group(1)
    else:
        # Fallback to checking the FROM statement directly
        match_python_from = python_from_pattern.search(dockerfile_content)
        if match_python_from:
            # Ensure it's not a FROM statement using a variable, like python:${PYTHON_VERSION}
            if not re.search(r"FROM.*python:\$\{{0,1}PYTHON_VERSION\}{0,1}", dockerfile_content):
                versions["python_version"] = match_python_from.group(1)

    # Search for Postgres version
    match_postgres_from = postgres_from_pattern.search(dockerfile_content)
    if match_postgres_from:
        versions["postgres_version"] = match_postgres_from.group(1)

    return versions



