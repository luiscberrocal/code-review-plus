from code_review.git.handlers import compare_branches


class TestCompareBranches:
    def test_compare_handler(self):
        result = compare_branches("master", "develop")
        assert result is not None