import logging
from datetime import datetime
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from code_review import settings
from code_review.adapters.changelog import parse_changelog
from code_review.adapters.setup_adapters import setup_to_dict
from code_review.handlers.file_handlers import change_directory, get_not_ignored
from code_review.plugins.coverage.handlers import run_coverage
from code_review.plugins.coverage.main import get_makefile, get_minimum_coverage
from code_review.plugins.coverage.schemas import TestConfiguration
from code_review.plugins.dependencies.pip.handlers import find_requirements_to_update, get_requirements
from code_review.plugins.docker.docker_files.handlers import parse_dockerfile
from code_review.plugins.git.adapters import get_git_flow_source_branch, is_rebased
from code_review.plugins.git.handlers import branch_line_to_dict, check_out_and_pull, get_branch_info
from code_review.plugins.linting.ruff.handlers import _check_and_format_ruff, count_ruff_issues
from code_review.review.rules import (
    ci_file_rules,
    docker_image_rules,
    linting_rules,
    readme_rules,
    requirement_rules,
    unvetted_requirements_rules,
version_rules,
)
from code_review.review.rules.git_rules import (
    rebase_rule,
    validate_master_develop_sync_legacy,
)
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import BranchSchema, SemanticVersion, RulesResult
from code_review.settings import CLI_CONSOLE

logger = logging.getLogger(__name__)


def _process_branch_info(
    branch_name: str,
    folder: Path,
    makefile: Path,
    progress: Progress,
    main_task,
    is_target: bool = False,
) -> BranchSchema:
    """Process branch information for base or target branch.

    Args:
        branch_name: Name of the branch to process
        folder: Path to the folder containing the code
        makefile: Path to the makefile
        progress: Progress object for displaying progress
        main_task: Main task for updating progress
        is_target: Whether this is the target branch (enables additional processing)

    Returns:
        BranchSchema with all the branch information populated
    """
    # Checkout and pull branch
    progress.update(main_task, advance=1, description=f"[yellow]Checkout and pull {branch_name}[/yellow]")
    check_out_and_pull(branch_name, check=False)

    # Run ruff to count linting issues
    progress.update(main_task, advance=1, description=f"[yellow]Running ruff on {branch_name}[/yellow]")
    linting_count = count_ruff_issues(folder)

    # Get branch info
    progress.update(main_task, advance=1, description=f"[yellow]Get branch info for {branch_name}[/yellow]")
    get_branch_info(branch_name)
    branch_info = branch_line_to_dict(branch_name)

    # Get minimum coverage
    progress.update(main_task, advance=1, description=f"[yellow]Get min coverage for {branch_name}[/yellow]")
    min_coverage = get_minimum_coverage(makefile)

    # Populate branch info dictionary
    branch_info["linting_errors"] = linting_count
    branch_info["min_coverage"] = min_coverage

    # Get requirements for target branch only
    if is_target:
        progress.update(main_task, advance=1, description="[yellow]Getting requirements[/yellow]")
        branch_info["requirements"] = get_requirements(folder)

    # Create BranchSchema
    branch = BranchSchema(**branch_info)

    # Get version from config file
    progress.update(main_task, advance=1, description=f"[yellow]Getting version from config for {branch_name}[/yellow]")
    branch.version = get_version_from_config_file(folder, folder.stem)

    # Parse changelog
    progress.update(main_task, advance=1, description=f"[yellow]Parsing changelog for {branch_name}[/yellow]")
    branch.changelog_versions = parse_changelog(folder / "CHANGELOG.md", folder.stem)
    if settings.EXPERIMENTAL_COVERAGE:
        test_config = TestConfiguration(
            folder=folder,
            unit_tests=[],
            min_coverage=min_coverage,
            settings_module="config.settings.local",
        )
        progress.update(main_task, advance=1, description=f"[yellow]Getting coverage for {branch_name}[/yellow]")
        coverage = run_coverage(test_configuration=test_config)
        branch.coverage = coverage

    # Additional processing for target branch
    if is_target:
        progress.update(main_task, advance=1, description="[yellow]Finding requirements to update[/yellow]")
        branch.requirements_to_update = find_requirements_to_update(folder)

        progress.update(main_task, advance=1, description="[yellow]Checking and formatting ruff[/yellow]")
        branch.formatting_errors = _check_and_format_ruff(folder)


    return branch


def build_code_review_schema(folder: Path, target_branch_name: str) -> CodeReviewSchema:
    """Build a CodeReviewSchema for the given folder and target branch.

    Args:
        folder: Path to the folder containing the code review data.
        target_branch_name: Name of the target branch to compare against the base branch.
    """
    total_work = 22

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=CLI_CONSOLE,
            transient=True,
    ) as progress:
        main_task = progress.add_task("[cyan]Total Sync Progress[/cyan]", total=total_work)

        # Change to project directory
        progress.update(main_task, description="[yellow]Change folder[/yellow]")
        change_directory(folder)

        # Get makefile
        progress.update(main_task, advance=1, description="[yellow]Get makefile[/yellow]")
        makefile = get_makefile(folder)

        # Process base branch (master)
        base_name = "master"
        base_branch = _process_branch_info(base_name, folder, makefile, progress, main_task, is_target=False)

        # Process target branch
        target_branch = _process_branch_info(target_branch_name, folder, makefile, progress, main_task, is_target=True)

        # Parse Dockerfiles
        docker_files = get_not_ignored(folder, "Dockerfile")
        progress.update(main_task, advance=1, description="[yellow]Parsing dockerfiles[/yellow]")
        docker_info_list = []
        for file in docker_files:
            docker_info = parse_dockerfile(file)
            if docker_info:
                docker_info_list.append(docker_info)

        # Get source branch
        progress.update(main_task, advance=1, description="[yellow]Getting source branch[/yellow]")
        source_branch_name = get_git_flow_source_branch(target_branch.name)
        if not source_branch_name:
            logger.warning("No source branch in target branch for target branch. %s", target_branch.name)

        # Create code review schema
        rules = []
        code_review_schema = CodeReviewSchema(
            name=folder.name,
            source_folder=folder,
            makefile_path=makefile,
            target_branch=target_branch,
            source_branch_name=source_branch_name,
            base_branch=base_branch,
            date_created=datetime.now(),
            docker_files=docker_info_list,
            rules_validated=rules,
            readme_file=folder / "README.md",
            ci_file=folder / ".gitlab-ci.yml",
        )

        # Check if rebased
        progress.update(main_task, advance=1, description="[yellow]Checking for rebase[/yellow]")
        code_review_schema.is_rebased = is_rebased(code_review_schema.target_branch.name, source_branch_name)

        # Check master and develop sync
        progress.update(main_task, advance=1, description="[yellow]Checking sync between master and develop[/yellow]")
        git_rules = validate_master_develop_sync_legacy(["master", "develop"])
        if git_rules:
            rules.extend(git_rules)

    # Run all validation rules
    rules_list = check_all_rules(code_review_schema)
    rules.extend(rules_list)

    code_review_schema.rules_validated = rules
    return code_review_schema

def check_all_rules(code_review_schema: CodeReviewSchema)-> list[RulesResult]:
    """Run all validation rules against the code review schema.

    Args:
        code_review_schema: The CodeReviewSchema object to validate

    Returns:
        List of RulesResult objects containing validation results
    """
    rules = []
    checks = [
        ci_file_rules.check,
        linting_rules.check,
        rebase_rule,
        version_rules.check,
        docker_image_rules.check,
        readme_rules.check,
        requirement_rules.check,
        unvetted_requirements_rules.check,

    ]
    total_work = len(checks)

    with Progress(
            SpinnerColumn(),  # Use a spinner column for dynamic status updates
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=CLI_CONSOLE,
            transient=True,
    ) as progress:
        # Add a single task that covers the entire process
        main_task = progress.add_task("[cyan]Total Sync Progress[/cyan]", total=total_work)
        for check in checks:
            progress.update(main_task,advance=1, description=f"[yellow]Running {check.__name__}[/yellow]")
            result = check(code_review_schema)
            if result:
                rules.extend(result)
    return rules

def get_version_from_config_file(folder: Path, app_name: str) -> SemanticVersion | None:
    """Extract the version string from a given file."""
    setup_file = folder / "setup.cfg"
    if not setup_file.exists():
        setup_file = folder / ".bumpversion.cfg"

    setup_dict = setup_to_dict(setup_file)
    if setup_dict.get("bumpversion", {}).get("current_version"):
        version_str = setup_dict["bumpversion"]["current_version"]
        return SemanticVersion.parse_version(version_str, app_name, setup_file)

    return None
