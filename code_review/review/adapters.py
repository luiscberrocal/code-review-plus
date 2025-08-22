from pathlib import Path

from code_review.git.handlers import get_author
from code_review.review.schemas import BranchSchema


def build_code_review_schema(folder: Path, target_branch_name: str):
    base_name = "master"
    base_author = get_author(base_name)
    base_branch = BranchSchema(name=base_name, author=base_author)

    target_author = get_author(target_branch_name)
    target_branch = BranchSchema(name=target_branch_name, author=target_author)

