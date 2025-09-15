import re

def get_versions_from_dockerfile(dockerfile_content):
    """
    Parses a Dockerfile to extract Python, Postgres, and Node.js versions.

    Args:
        dockerfile_content (str): The content of the Dockerfile as a string.

    Returns:
        dict: A dictionary containing the extracted versions. Keys are
              'python_version', 'postgres_version', and 'node_version'.
              Values are the version strings or None if not found.
    """
    versions = {
        'version': None,
        'product': None,
    }

    # Regex patterns for different technologies
    python_arg_pattern = re.compile(r'ARG\s+PYTHON_VERSION=([\d.]+[\w-]*)')
    python_from_pattern = re.compile(r'FROM.*python:([\d.]+[\w-]*)')
    postgres_from_pattern = re.compile(r'FROM.*postgres:([\d.]+[\w-]*)')
    node_from_pattern = re.compile(r'FROM.*node:([\d.]+[\w-]*)')

    # --- Search for Python version ---
    match_python_arg = python_arg_pattern.search(dockerfile_content)
    if match_python_arg:
        versions['version'] = match_python_arg.group(1)
        versions['product'] = 'python'
    else:
        # Fallback to checking the FROM statement directly
        match_python_from = python_from_pattern.search(dockerfile_content)
        if match_python_from:
            # Ensure it's not a FROM statement using a variable
            if not re.search(r'FROM.*python:\$\{{0,1}PYTHON_VERSION\}{0,1}', dockerfile_content):
                versions['version'] = match_python_from.group(1)
                versions['product'] = 'python'

    # --- Search for Postgres version ---
    match_postgres_from = postgres_from_pattern.search(dockerfile_content)
    if match_postgres_from:
        versions['version'] = match_postgres_from.group(1)
        versions['product'] = 'postgres'

    # --- Search for Node.js version ---
    match_node_from = node_from_pattern.search(dockerfile_content)
    if match_node_from:
        versions['version'] = match_node_from.group(1)
        versions['product'] = 'node'

    return versions



