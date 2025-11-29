import logging
from datetime import datetime
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from code_review.adapters.changelog import parse_changelog
from code_review.adapters.setup_adapters import setup_to_dict
from code_review.handlers.file_handlers import change_directory, get_not_ignored
from code_review.plugins.coverage.main import get_makefile, get_minimum_coverage
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


def build_code_review_schema(folder: Path, target_branch_name: str) -> CodeReviewSchema:
    """Build a CodeReviewSchema for the given folder and target branch.

    Args:
        folder: Path to the folder containing the code review data.
        target_branch_name: Name of the target branch to compare against the base branch.
    """
    total_work = 10

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

        # ----------------------------------------------------
        # 2. Execute Refresh from Remote (The first unit of work)
        # ----------------------------------------------------
        progress.update(main_task, description="[yellow]Change folder[/yellow]")
        change_directory(folder)

        progress.update(main_task,advance=1, description="[yellow]Get maka file[/yellow]")
        makefile = get_makefile(folder)  # Assuming this function is defined elsewhere to get the makefile path
        base_name = "master"
        progress.update(main_task, advance=1, description="[yellow]Checkout and pull[/yellow]")
        check_out_and_pull(base_name, check=False)
        progress.update(main_task, advance=1, description="[yellow]Running ruff[/yellow]")
        base_count = count_ruff_issues(folder)
        progress.update(main_task, advance=1, description="[yellow]Get branch info[/yellow]")
        get_branch_info(base_name)
        base_branch_info = branch_line_to_dict(base_name)
        progress.update(main_task, advance=1, description="[yellow]Gwt min cov[/yellow]")
        base_cov = get_minimum_coverage(makefile)
        base_branch_info["linting_errors"] = base_count
        base_branch_info["min_coverage"] = base_cov

        base_branch = BranchSchema(**base_branch_info)
        base_branch.version = get_version_from_config_file(folder, folder.stem)
        base_branch.changelog_versions = parse_changelog(folder / "CHANGELOG.md", folder.stem)

        check_out_and_pull(target_branch_name, check=False)
        get_branch_info(target_branch_name)
        target_branch_info = branch_line_to_dict(target_branch_name)
        target_count = count_ruff_issues(folder)
        target_cov = get_minimum_coverage(makefile)
        target_branch_info["linting_errors"] = target_count
        target_branch_info["min_coverage"] = target_cov

        target_branch_info["requirements"] = get_requirements(folder)

        target_branch = BranchSchema(**target_branch_info)
        target_branch.version = get_version_from_config_file(folder, folder.stem)
        target_branch.changelog_versions = parse_changelog(folder / "CHANGELOG.md", folder.stem)
        target_branch.requirements_to_update = find_requirements_to_update(folder)

        target_branch.formatting_errors = _check_and_format_ruff(folder)

        # Dockerfiles
        docker_files = get_not_ignored(folder, "Dockerfile")
        docker_info_list = []
        for file in docker_files:
            docker_info = parse_dockerfile(file)
            if docker_info:
                docker_info_list.append(docker_info)
        source_branch_name = get_git_flow_source_branch(target_branch.name)
        if not source_branch_name:
            logger.warning("No source branch in target branch for target branch. %s", target_branch.name)

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

        code_review_schema.is_rebased = is_rebased(code_review_schema.target_branch.name, source_branch_name)

        # Master amd develop sync rules
        git_rules = validate_master_develop_sync_legacy(["master", "develop"])
        if git_rules:
            rules.extend(git_rules)

        rules_list = check_all_rules(code_review_schema)
        rules.extend(rules_list)

        code_review_schema.rules_validated = rules
        return code_review_schema

def check_all_rules(code_review_schema: CodeReviewSchema)-> list[RulesResult]:
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
    for check in checks:
        result = check(code_review_schema)
        if result:
            rules.extend(result)
    return rules

def check_all_rules2(code_review_schema: CodeReviewSchema):
    rules = []
    # CI rules
    ci_rules = ci_file_rules.check(code_review_schema)
    if ci_rules:
        rules.extend(ci_rules)
    # Ruff linting rules
    lint_rules = linting_rules.check(code_review_schema)
    if lint_rules:
        rules.extend(lint_rules)
    # Git rules
    # Git sync rules
    git_sync_rules = rebase_rule(code_review_schema)
    if git_sync_rules:
        rules.extend(git_sync_rules)
    # Changelog version rules
    change_log_rules = version_rules.check(code_review_schema)
    if change_log_rules:
        rules.extend(change_log_rules)
    # Dockerfile rules
    docker_rules = docker_image_rules.check(code_review=code_review_schema)
    if docker_rules:
        rules.extend(docker_rules)
    # README rules
    admin_url_check = readme_rules.check(code_review_schema)
    if admin_url_check:
        rules.extend(admin_url_check)

    # Requirements update rules
    req_rules = requirement_rules.check(code_review_schema)
    if req_rules:
        rules.extend(req_rules)
    # Unvetted libraries
    unvetted_library_rules = unvetted_requirements_rules.check(code_review_schema)
    if unvetted_library_rules:
        rules.extend(unvetted_library_rules)
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
