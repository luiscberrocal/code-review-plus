from code_review.docker_hub.schemas import ImageTag


def exclude_by_content(tag:ImageTag, exclusion_criteria: list[str]) -> bool:
    """
    Exclude images based on specific content criteria.
    
    """
    for criterion in exclusion_criteria:
        if criterion in tag.name:
            return True
    return False