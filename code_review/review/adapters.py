import json
from datetime import datetime
from pathlib import Path

from code_review.coverage.main import get_makefile, get_minimum_coverage
from code_review.git.handlers import check_out_and_pull, get_author, get_branch_info
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
    base_author = get_branch_info(base_name)
    base_cov = get_minimum_coverage(makefile)
    base_branch = BranchSchema(name=base_name, author=base_author, linting_errors=base_count, min_coverage=base_cov)

    check_out_and_pull(target_branch_name, check=False)
    target_author = get_author(target_branch_name)
    target_count = count_ruff_issues(folder)
    target_cov = get_minimum_coverage(makefile)
    target_branch = BranchSchema(
        name=target_branch_name, author=target_author, linting_errors=target_count, min_coverage=target_cov
    )

    return CodeReviewSchema(
        name=folder.name,
        source_folder=folder,
        makefile_path=makefile,
        target_branch=target_branch,
        base_branch=base_branch,
        date_created=datetime.now(),
    )


if __name__ == "__main__":
    f = Path.home() / "adelantos" / "payment-options-vue"
    tb = "feature/VPOP-284_refactor_installment_detail_update_or_create"
    schema = build_code_review_schema(f, tb)

    file = OUTPUT_FOLDER / f"{schema.name}_code_review.json"
    with open(file, "w") as f:
        json.dump(schema.model_dump(), f, indent=4, default=str)
