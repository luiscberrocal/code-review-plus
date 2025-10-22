import re


def check_admin_console_urls(readme_content: str) -> list[str]:
    regexp = re.compile(r"\[(Production|Staging)\s+Admin\s+Console\]\((?P<url>https://(.*))\)")
    matches = regexp.findall(readme_content)
    urls = [match[2] for match in matches]
    return urls
