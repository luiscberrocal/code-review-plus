# In code_review/__main__.py or similar
from code_review.cli import cli
import code_review.git.main  # This imports the git commands
import code_review.linting.ruff.main  # This imports the ruff commands

if __name__ == "__main__":
    cli()