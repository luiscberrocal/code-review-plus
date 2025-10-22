from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import RulesResult


def check_image_version(code_review: CodeReviewSchema) -> list[RulesResult]:
    """Check if the Docker images used in the Dockerfiles have the latest versions.

    Args:
        code_review: The code review schema containing Dockerfile information.

    Returns:
        A list of RulesResult indicating whether each Docker image is up to date.
    """
    rules = []
    for dockerfile in code_review.docker_files:

        if dockerfile.image == dockerfile.expected_image:
            rules.append(
                RulesResult(
                    name="Docker Image Version",
                    passed=True,
                    level="INFO",
                    message=(
                        f"Docker image '{dockerfile.image.name}:{dockerfile.image.version}' in"
                        f" '{dockerfile.file.relative_to(code_review.source_folder)}' is up to date."
                    ),
                )
            )
        elif dockerfile.image < dockerfile.expected_image:
            rules.append(
                RulesResult(
                    name="Docker Image Version",
                    passed=False,
                    level="ERROR",
                    message=(
                        f"Docker image '{dockerfile.image.name}:{dockerfile.image.version}' in "
                        f"'{dockerfile.file.relative_to(code_review.source_folder)}' is outdated. "
                        f"Expected version is '{dockerfile.expected_version}'."
                    ),
                )
            )
        else:
            rules.append(
                RulesResult(
                    name="Docker Image Version",
                    passed=False,
                    level="WARNING",
                    message=(
                        f"Docker image '{dockerfile.image.name}:{dockerfile.image.version}' in "
                        f"'{dockerfile.file.relative_to(code_review.source_folder)}' is not the latest version."
                    ),
                )
            )
    return rules