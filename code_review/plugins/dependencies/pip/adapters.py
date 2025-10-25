import logging
import re
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from code_review.plugins.dependencies.pip.schemas import RequirementInfo, PackageRequirement

logger = logging.getLogger(__name__)


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


def parse_requirements_old(content):
    """Parses a string containing pip requirements, extracting the package name
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

    pattern = re.compile(r"^\s*(?!#)([\w.\-\[\]]+\s*[<>=!~]+\s*[\w.]+)\s*(?:\s*#.*)?$", re.MULTILINE)

    # Find all matches (the entire requirement string)
    requirements = pattern.findall(content)

    # A cleaner regex for just name and version:
    # Captures:
    # Group 1: Package name ([\w.\-\[\]]+)
    # Group 2: Version specifier and number ([<>=!~]+\s*[\w.]+)
    clean_pattern = re.compile(r"^\s*([\w.\-\[\]]+)\s*([<>=!~]+\s*[\w.]+)\s*(?:\s*#.*)?$", re.MULTILINE)

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
            specifier_match = re.match(r"([<>=!~]+)\s*([\w.]+)", specifier_and_version)
            if specifier_match:
                operator = specifier_match.group(1)
                version = specifier_match.group(2)
            else:
                operator = None
                version = specifier_and_version  # Keep as is if separation fails

            parsed_data.append(
                {
                    "package": package_name,
                    "full_specifier": specifier_and_version,
                    "operator": operator,
                    "version": version,
                }
            )

    return parsed_data


# --- Parsing Function ---
def parse_requirements(requirements_content: str) -> list[PackageRequirement]:
    """Parses a string containing pip requirements, handling comments, whitespace,
    standard package specifiers, and attempting to parse complex VCS URLs.

    Args:
        requirements_content: A string containing the content of a requirements file.

    Returns:
        A list of PackageRequirement models for all successfully parsed requirements.
    """
    parsed_requirements: list[PackageRequirement] = []
    # Regex to detect common VCS schemes
    vcs_pattern = re.compile(r"^(git\+|hg\+|svn\+|bzr\+)")

    for line in requirements_content.splitlines():
        # 1. Clean line: remove everything after a '#' comment character and strip whitespace
        clean_line = line.split("#", 1)[0].strip()

        # 2. Skip empty lines
        if not clean_line:
            continue

        # 3. Handle VCS URLs (git+, hg+, etc.)
        if vcs_pattern.match(clean_line):
            source = clean_line

            # Best effort: Extract name from the repository path
            # Looks for /repo_name.git or /repo_name at the end
            repo_match = re.search(r"\/([^\/]+)(?:\.git)?(?:\@|\Z)", clean_line)
            name = repo_match.group(1).split("@")[0] if repo_match else "VCS_Unknown"

            # Best effort: Extract version from the tag/commit reference (@vX.Y.Z)
            tag_match = re.search(r"@([^\s]+)$", clean_line)
            version = tag_match.group(1) if tag_match else None

            # Note: For VCS, the name should ideally be specified with #egg=packagename,
            # but since the example lacks it, we use the repo name and store the full line as source.
            parsed_requirements.append(
                PackageRequirement(
                    name=name,
                    version=version,
                    specifier=f"VCS reference: {version}" if version else "VCS reference",
                    source=source,
                )
            )
            continue

        # 4. Handle standard requirements using the packaging library
        try:
            req = Requirement(clean_line)

            # Determine the package name, including extras (e.g., ddtrace[django])
            full_name = canonicalize_name(req.name)
            if req.extras:
                full_name += f"[{','.join(sorted(req.extras))}]"

            # Extract the version string (e.g., '3.16.0') if it's an exact match specifier (==)
            version_str = None
            spec_str = str(req.specifier)

            if len(req.specifier) == 1:
                spec = next(iter(req.specifier))
                if spec.operator == "==":
                    version_str = spec.version

            parsed_requirements.append(
                PackageRequirement(
                    name=full_name, version=version_str, specifier=spec_str if spec_str else None, source=None
                )
            )

        except Exception:
            # Skip lines that are unparseable (e.g., plain URLs not starting with a VCS scheme, invalid syntax)
            print(f"Warning: Skipping unparseable requirement line: '{clean_line}'")
            continue

    return parsed_requirements


def main2():
    requirements_content = """
    djangorestframework==3.16.0  # https://github.com/encode/django-rest-framework
    django-cors-headers==4.7.0  # https://github.com/adamchainz/django-cors-headers
    # DRF-spectacular for api documentation
    drf-spectacular==0.28.0  # https://github.com/tfranzel/drf-spectacular
    pytz==2025.2  # https://github.com/stub42/pytz

    drf-pydantic==2.7.1  # https://pypi.org/project/drf-pydantic/
    # email-validator==2.2.0  <-- This line is commented out and will be skipped
    django-fsm==3.0.0
    Deprecated==1.2.18

    # Datadog APM and Logging
    # ------------------------------------------------------------------------------
    ddtrace[django]==3.16.0  # https://github.com/DataDog/dd-trace-py
    django-datadog-logger==0.7.3  # https://github.com/Mtsohetra/django-datadog-logger

    # VCS Requirements without #egg=, name is inferred from repo
    git+https://PYPI_READ_TOKEN:${PYPI_TOKEN}@gitlab.com/adelantos-development/pj-slack-sdk.git@v1.0.1
    git+https://PYPI_READ_TOKEN:${PYPI_TOKEN}@gitlab.com/adelantos-development/oxxo-direct-sdk.git@v2.1.0
    """

    results = parse_requirements(requirements_content)

    print("--- Parsed Requirements ---")
    for result in results:
        print(f"Name: {result.name}")
        print(f"  Version: {result.version}")
        print(f"  Specifier: {result.specifier}")
        if result.source:
            print(f"  Source: {result.source}")
        print("-" * 20)

    # Example of accessing a specific field
    print(f"\nTotal packages found: {len(results)}")
    ddtrace_req = next((r for r in results if r.name == "ddtrace[django]"), None)
    if ddtrace_req:
        print(f"ddtrace[django] found with exact version: {ddtrace_req.version}")


def main():
    requirements_content = """
    whitenoise==6.9.0  # https://github.com/evansd/whitenoise
    redis==6.4.0  # https://github.com/redis/redis-py
    hiredis==3.2.1  # https://github.com/redis/hiredis-py
    celery==5.5.3  # pyup: < 6.0  # https://github.com/celery/celery
    django-celery-beat==2.8.1  # https://github.com/celery/django-celery-beat
    uvicorn[standard]>=0.35.0  # https://github.com/encode/uvicorn
    # This is a full-line comment and should be skipped
    # uwsgi==2.0.24  # Example of a fully commented-out line
    """

    # Run the parser and display the results
    parsed_requirements = parse_requirements_old(requirements_content)

    print(f"{'Package':<25} | {'Operator':<10} | {'Version':<10} | {'Full Specifier':<20}")
    print("-" * 68)
    for req in parsed_requirements:
        print(f"{req['package']:<25} | {req['operator']:<10} | {req['version']:<10} | {req['full_specifier']:<20}")


if __name__ == "__main__":
    main2()
