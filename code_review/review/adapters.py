import json
from datetime import datetime
from pathlib import Path

from code_review.adapters.changelog import parse_changelog
from code_review.adapters.setup_adapters import setup_to_dict
from code_review.coverage.main import get_makefile, get_minimum_coverage
from code_review.git.handlers import branch_line_to_dict, check_out_and_pull, get_branch_info
from code_review.handlers import ch_dir
from code_review.linting.ruff.handlers import count_ruff_issues
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import BranchSchema, SemanticVersion
from code_review.settings import OUTPUT_FOLDER


def build_code_review_schema(folder: Path, target_branch_name: str):
    ch_dir(folder)
    makefile = get_makefile(folder)  # Assuming this function is defined elsewhere to get the makefile path
    base_name = "master"
    check_out_and_pull(base_name, check=False)
    base_count = count_ruff_issues(folder)
    base_line = get_branch_info(base_name)
    base_branch_info = branch_line_to_dict(base_name)
    base_cov = get_minimum_coverage(makefile)
    base_branch_info["linting_errors"] = base_count
    base_branch_info["min_coverage"] = base_cov

    base_branch = BranchSchema(**base_branch_info)
    base_branch.version = get_version_from_file(folder)
    base_branch.changelog_versions = parse_changelog(folder / "CHANGELOG.md")

    check_out_and_pull(target_branch_name, check=False)
    target_line = get_branch_info(target_branch_name)
    target_branch_info = branch_line_to_dict(target_branch_name)
    target_count = count_ruff_issues(folder)
    target_cov = get_minimum_coverage(makefile)
    target_branch_info["linting_errors"] = target_count
    target_branch_info["min_coverage"] = target_cov

    target_branch = BranchSchema(**target_branch_info)
    target_branch.version = get_version_from_file(folder)
    target_branch.changelog_versions = parse_changelog(folder / "CHANGELOG.md")

    return CodeReviewSchema(
        name=folder.name,
        source_folder=folder,
        makefile_path=makefile,
        target_branch=target_branch,
        base_branch=base_branch,
        date_created=datetime.now(),
    )



def get_version_from_file(folder: Path) -> SemanticVersion | None:
    """Extract the version string from a given file."""
    setup_file = folder / "setup.cfg"


    setup_dict = setup_to_dict(setup_file)
    if setup_dict.get("bumpversion", {}).get("current_version"):
        version_str =  setup_dict["bumpversion"]["current_version"]
        return SemanticVersion.parse_version(version_str, setup_file)

    return None

