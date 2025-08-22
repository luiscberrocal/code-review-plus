from pathlib import Path

from code_review.git.handlers import get_author
from code_review.handlers import ch_dir
from code_review.review.schemas import BranchSchema, CodeReviewSchema


def build_code_review_schema(folder: Path, target_branch_name: str):
    ch_dir(folder)
    base_name = "master"
    base_author = get_author(base_name)
    base_branch = BranchSchema(name=base_name, author=base_author)

    target_author = get_author(target_branch_name)
    target_branch = BranchSchema(name=target_branch_name, author=target_author)
    
    code_review_schema = CodeReviewSchema(
        name=folder.name,
        source_folder=folder,
        target_branch=target_branch,
        base_branch=base_branch
    )
    return code_review_schema

if __name__ == '__main__':
    f = Path.home() / "adelantos" / "wompi-integration"
    tb = "feature/wompi-48_update_mdc"
    schema = build_code_review_schema(f, tb)
    print(schema)
