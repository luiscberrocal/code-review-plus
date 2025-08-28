import json
from datetime import datetime
from pathlib import Path

from code_review.coverage.main import get_makefile, get_minimum_coverage
from code_review.git.handlers import check_out_and_pull, get_author, get_branch_info, branch_line_to_dict
from code_review.handlers import ch_dir
from code_review.linting.ruff.handlers import count_ruff_issues
from code_review.review.schemas import CodeReviewSchema
from code_review.git.schemas import BranchSchema
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

    check_out_and_pull(target_branch_name, check=False)
    target_line = get_branch_info(target_branch_name)
    target_branch_info = branch_line_to_dict(target_branch_name)
    target_count = count_ruff_issues(folder)
    target_cov = get_minimum_coverage(makefile)
    target_branch_info["linting_errors"] = target_count
    target_branch_info["min_coverage"] = target_cov

    target_branch = BranchSchema(**target_branch_info)

    return CodeReviewSchema(
        name=folder.name,
        source_folder=folder,
        makefile_path=makefile,
        target_branch=target_branch,
        base_branch=base_branch,
        date_created=datetime.now(),
    )


if __name__ == "__main__":
    f = Path.home() / "adelantos" / "red-activa-integration"
    tb = "feature/PAYTSA-423_send_payments_async"

    f = Path.home() / "adelantos" / "payment-options-vue"
    tb = "feature/PAYTSA-423_send_payments_async"

    f = Path.home() / "adelantos" / "wompi-integration"
    tb = "feature/wompi-48_update_mdc"
    schema = build_code_review_schema(f, tb)

    file = OUTPUT_FOLDER / f"{schema.name}_code_review.json"
    with open(file, "w") as f:
        json.dump(schema.model_dump(), f, indent=4, default=str)
    print(f"Wrote code review schema to {file}")
