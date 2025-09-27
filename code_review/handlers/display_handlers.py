
from rich.align import Align
from rich.text import Text

from code_review.settings import BANNER, CLI_CONSOLE, TAGLINE


def show_banner():
    """Display the ASCII art banner."""
    # Create gradient effect with different colors
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    CLI_CONSOLE.print(Align.center(styled_banner))
    CLI_CONSOLE.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    CLI_CONSOLE.print()