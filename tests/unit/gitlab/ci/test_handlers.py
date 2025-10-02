from code_review.plugins.gitlab.ci.handlers import handle_multi_targets


def test_handle_mult_targets(fixtures_folder) -> None:
    result = handle_multi_targets(fixtures_folder, "gitlab-ci.yml")

    assert result is not None, "The function should return a dictionary for a valid .gitlab-ci.yml file."
    assert isinstance(result, dict), "The function should return a dictionary."
