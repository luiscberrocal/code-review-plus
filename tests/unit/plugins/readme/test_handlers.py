import pytest

from code_review.plugins.readme.handlers import check_admin_console_urls


class TestAdminConsoleUrlExtractor:
    """
    Test suite for the check_admin_console_urls function.
    Tests various scenarios including valid links, no links, and edge cases.
    """

    @pytest.mark.parametrize("link_type", ["Production", "Staging"])
    def test_single_valid_url(self, link_type):
        """Tests extraction of a single, correctly formatted Production or Staging link."""
        # Note: The expected output is the URL *after* 'https://' due to match[2]
        url_suffix = "prod-admin.example.com/dashboard"
        readme_content = f"Some text here.\n[{link_type} Admin Console](https://{url_suffix})\nMore text."

        expected = [url_suffix]
        actual = check_admin_console_urls(readme_content)

        assert actual == expected, f"Failed to extract correct URL suffix for {link_type} link."

    def test_multiple_urls_mixed_types(self):
        """Tests extraction of multiple Production and Staging links in one content block."""

        prod_url_suffix = "production.admin.example.com/home"
        stage_url_suffix = "staging-console.example.net/users"
        other_url_suffix = "test-console.example.org/stats"

        readme_content = (
            f"Here is the [Production Admin Console](https://{prod_url_suffix}).\n"
            f"And the [Staging Admin Console](https://{stage_url_suffix}).\n"
            f"A different link [Other Console](https://{other_url_suffix}) is ignored."
        )

        expected = [prod_url_suffix, stage_url_suffix]
        actual = check_admin_console_urls(readme_content)

        assert actual == expected, "Failed to extract all correct URL suffixes from mixed content."

    def test_no_urls_present(self):
        """Tests content with no matching Admin Console links."""
        readme_content = "Just some plain text. No links here. [Regular Link](http://example.com)"
        expected = []
        actual = check_admin_console_urls(readme_content)
        assert actual == expected, "Should return an empty list when no matching links are present."

    def test_malformed_urls_are_ignored(self):
        """Tests that improperly formatted links are ignored."""
        readme_content = (
            "[Production Admin Console](http://not-https.com)\n"  # Fails 'https://'
            "[Production Admin Console](https://)\n"  # Fails the '.*' capture after https://
            "[Test Admin Console](https://test.com)"  # Fails '(Production|Staging)'
        )
        expected = [""]
        actual = check_admin_console_urls(readme_content)
        assert actual == expected, "Should ignore links that do not perfectly match the regex pattern."

    def test_url_with_path_and_query(self):
        """Tests a URL that includes a path and query parameters."""
        url_suffix = "admin.example.com/details?user=123&env=prod"
        readme_content = f"Link: [Production Admin Console](https://{url_suffix})"
        expected = [url_suffix]
        actual = check_admin_console_urls(readme_content)
        assert actual == expected, "Failed to correctly extract URL with path and query parameters."

    def test_empty_input(self):
        """Tests the function with an empty input string."""
        readme_content = ""
        expected = []
        actual = check_admin_console_urls(readme_content)
        assert actual == expected, "Should return an empty list for empty input."

    def test_incorrect_spacing_is_ignored(self):
        """Tests that links with incorrect internal spacing are ignored."""
        readme_content = (
            "[ProductionAdmin Console](https://a.com)\n"  # Missing space
            "[ Production Admin Console ](https://b.com)\n"  # Extra space
            "[Production Admin Console]( https://c.com )"  # Extra space in link
        )
        expected = []
        actual = check_admin_console_urls(readme_content)
        assert actual == expected, "Should ignore links that do not have the exact 'X Admin Console' format."
