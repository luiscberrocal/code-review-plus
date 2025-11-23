import json
from datetime import datetime
from pathlib import Path

from code_review.review.schemas import CodeReviewSchema


def write_review(review: CodeReviewSchema, folder: Path) -> tuple[Path, Path | None]:
    """Write the code review details to a JSON file."""
    file = folder / f"{review.ticket}-{review.name}_code_review.json"
    backup_file = None
    if file.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = folder / f"{review.ticket}-{review.name}_code_review_{timestamp}.json"
        file.rename(backup_file)

    with open(file, "w") as f:
        json.dump(review.model_dump(), f, indent=4, default=str)

    return file, backup_file
