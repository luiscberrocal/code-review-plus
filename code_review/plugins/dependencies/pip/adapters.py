from pathlib import Path

from pydantic.v1.validators import max_str_int

from code_review.plugins.dependencies.pip.schemas import RequirementInfo


def parser_requirement_file(requirement_file: Path) -> list[RequirementInfo]:
    """Parses a pip requirements file and returns a list of requirement lines.

    Args:
        requirement_file (Path): The path to the requirements file.

    Returns:
        list[str]: A list of requirement lines.
    """
    requirements = []
    try:
        with requirement_file.open("r") as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#"):
                    requirements.append(stripped_line)
    except Exception as e:
        logger.error("Error reading requirements file %s: %s", requirement_file, e)
    return requirements


import re


def parse_requirements(content):
    """
    Parses a string containing pip requirements, extracting the package name
    and version/specifier.
    """
    # Regex to capture:
    # 1. Start of the line (optional whitespace)
    # 2. Package name (can include letters, numbers, hyphens, underscores, dots, and optional extras like [standard])
    # 3. Version specifier (==, >=, <=, etc., followed by version number)
    # 4. End of the line before a comment (#) or end of the string.
    # It ignores lines starting with '#'

    # Pattern explanation:
    # ^\s* -> Start of line, optional whitespace
    # (?!#)         -> Negative lookahead, ensures the line doesn't start with '#' (skips full-line comments)
    # (             -> Start of capturing group for the requirement
    #   [\w.\-\[\]]+ -> Package name and optional extras (e.g., uvicorn[standard])
    #   \s* -> Optional whitespace
    #   [<>=!~]+    -> Version operator(s) (==, >=, <, etc.)
    #   \s* -> Optional whitespace
    #   [\w.]+      -> Version number
    # )             -> End of capturing group
    # \s* -> Optional whitespace
    # (?:\s*#.*)?   -> Optional non-capturing group for comments: optional whitespace, '#', and rest of line

    pattern = re.compile(r'^\s*(?!#)([\w.\-\[\]]+\s*[<>=!~]+\s*[\w.]+)\s*(?:\s*#.*)?$', re.MULTILINE)

    # Find all matches (the entire requirement string)
    requirements = pattern.findall(content)

    # A cleaner regex for just name and version:
    # Captures:
    # Group 1: Package name ([\w.\-\[\]]+)
    # Group 2: Version specifier and number ([<>=!~]+\s*[\w.]+)
    clean_pattern = re.compile(r'^\s*([\w.\-\[\]]+)\s*([<>=!~]+\s*[\w.]+)\s*(?:\s*#.*)?$', re.MULTILINE)

    parsed_data = []
    for line in content.splitlines():
        match = clean_pattern.match(line)
        if match:
            package_name = match.group(1).strip()
            specifier_and_version = match.group(2).strip()

            # Split specifier_and_version to separate the operator and version number
            # This is a bit more complex than a simple split, so we'll just keep the full specifier
            # For simplicity, let's look for the first non-numeric/non-dot character after the name.

            # Example to further separate name, operator, and version:
            specifier_match = re.match(r'([<>=!~]+)\s*([\w.]+)', specifier_and_version)
            if specifier_match:
                operator = specifier_match.group(1)
                version = specifier_match.group(2)
            else:
                operator = None
                version = specifier_and_version  # Keep as is if separation fails

            parsed_data.append({
                "package": package_name,
                "full_specifier": specifier_and_version,
                "operator": operator,
                "version": version
            })

    return parsed_data

def main():
    requirements_content = """
    whitenoise==6.9.0  # https://github.com/evansd/whitenoise
    redis==6.4.0  # https://github.com/redis/redis-py
    hiredis==3.2.1  # https://github.com/redis/hiredis-py
    celery==5.5.3  # pyup: < 6.0  # https://github.com/celery/celery
    django-celery-beat==2.8.1  # https://github.com/celery/django-celery-beat
    uvicorn[standard]==0.35.0  # https://github.com/encode/uvicorn
    # This is a full-line comment and should be skipped
    # uwsgi==2.0.24  # Example of a fully commented-out line
    """


    # Run the parser and display the results
    parsed_requirements = parse_requirements(requirements_content)

    print(f"{'Package':<25} | {'Operator':<10} | {'Version':<10} | {'Full Specifier':<20}")
    print("-" * 68)
    for req in parsed_requirements:
        print(f"{req['package']:<25} | {req['operator']:<10} | {req['version']:<10} | {req['full_specifier']:<20}")


if __name__ == '__main__':
    main()