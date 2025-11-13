import re


def check_admin_console_urls(readme_content: str) -> list[str]:
    """Checks for Production and Staging Admin Console URLs in the README content."""
    regexp = re.compile(r"\[(Production|Staging)\s+Admin\s+Console\]\((?P<url>https://(.*))\)")
    matches = regexp.findall(readme_content)
    return [match[2] for match in matches]
