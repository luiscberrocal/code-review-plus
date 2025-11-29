import logging
import re
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from code_review.enums import EnvironmentType
from code_review.plugins.dependencies.pip.schemas import PackageRequirement

logger = logging.getLogger(__name__)


def parser_requirement_file(requirement_file: Path) -> str:
    """Parses a pip requirements file and returns a list of requirement lines.

    Args:
        requirement_file (Path): The path to the requirements file.

    Returns:
        str: A string containing all non-comment, non-empty lines from the requirements file,
    """
    requirements = []
    try:
        with requirement_file.open("r") as file:
            for line_number, line in enumerate(file, 1):
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#"):
                    requirements.append(stripped_line)
    except FileNotFoundError:
        logger.error("Requirements file %s not found.", requirement_file)
    except Exception as e:
        logger.error("Error reading requirements file %s in line %s: %s", requirement_file, line_number, e)
    return "\n".join(requirements)


# --- Parsing Function ---
def parse_requirements(
    requirements_content: str, environment: EnvironmentType, source_file: Path
) -> list[PackageRequirement]:
    """Parses a string containing pip requirements in a txt formant.

    It handles comments, whitespace, standard package specifiers, and attempting to parse complex VCS URLs.

    Args:
        requirements_content: A string containing the content of a requirements file.
        environment: The environment type (e.g., development, production).
        source_file: The path to the source requirements file.

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
            repo_match_regexp = re.compile(
                "\s*git\+https\:\/\/.*@gitlab\.com\/.+\/(?P<name>[\w_\-]+)\.git@v(?P<version>[\w\.]+)"
            )
            # repo_match = re.search(r"\/([^\/]+)(?:\.git)?(?:\@|\Z)", clean_line)
            # name = repo_match.group(1).split("@")[0] if repo_match else "VCS_Unknown"
            repo_match = re.match(repo_match_regexp, clean_line)
            name = "VCS_Unknown"
            version = None
            if repo_match:
                name = repo_match.group("name")
                version = repo_match.group("version")

            # Best effort: Extract version from the tag/commit reference (@vX.Y.Z)

            # Note: For VCS, the name should ideally be specified with #egg=packagename,
            # but since the example lacks it, we use the repo name and store the full line as source.
            parsed_requirements.append(
                PackageRequirement(
                    name=name,
                    version=version,
                    specifier="@",
                    source=source,
                    environment=environment.value,
                    file=source_file,
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
            operator = "?????"

            if len(req.specifier) == 1:
                spec = next(iter(req.specifier))
                # if spec.operator == "==":
                version_str = spec.version
                operator = spec.operator

            parsed_requirements.append(
                PackageRequirement(
                    name=full_name,
                    version=version_str,
                    specifier=operator if spec_str else None,
                    source=clean_line,
                    environment=environment.value,
                    file=source_file,
                )
            )

        except Exception as e:
            # Skip lines that are unparseable (e.g., plain URLs not starting with a VCS scheme, invalid syntax)
            logger.debug("Warning: Skipping unparseable requirement line: '%s'. Error: %s", clean_line, e)
            continue

    return parsed_requirements


def get_environment(source_file: Path) -> EnvironmentType | None:
    """Determine the environment based on the filename.

    Args:
        source_file (Path): The path to the requirements file.

    Returns:
        str: The environment name derived from the filename.
    """
    if source_file.suffix != ".txt":
        return None
    filename = source_file.stem.lower()  # Get the filename without extension and convert to lowercase
    if "local" in filename:
        return EnvironmentType.DEVELOPMENT
    if "base" in filename:
        return EnvironmentType.PRODUCTION
    if "production" in filename:
        return EnvironmentType.PRODUCTION
    return None


def parse_dependencies(source_file: Path) -> list[PackageRequirement]:
    """Parse a pip requirements file into a list of PackageRequirement models.

    Args:
        source_file (Path): The path to the requirements file.

    Returns:
        list[PackageRequirement]: A list of parsed package requirements.
    """
    requirement_content = parser_requirement_file(source_file)
    environment = get_environment(source_file)
    parsed_packages = parse_requirements(requirement_content, environment or EnvironmentType.PRODUCTION.value,
                                         source_file)

    # Update the file attribute for each parsed package
    for package in parsed_packages:
        package.file = source_file

    return parsed_packages
