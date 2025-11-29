import json
import os
from pathlib import Path

from gitignore_parser import parse_gitignore

from code_review.exceptions import SimpleGitToolError
from code_review.settings import OUTPUT_FOLDER, CLI_CONSOLE


def get_not_ignored(folder: Path, global_patten: str) -> list[Path]:
    """Finds all Dockerfiles in a given folder and its subdirectories,
    excluding those that are listed in a .gitignore file.

    Args:
        folder: The Path object for the root directory to search.
        global_patten: The glob pattern to search for Dockerfiles (e.g., "Dockerfile" or "**/Dockerfile").

    Returns:
        A list of Path objects for the Dockerfiles that are not ignored.
    """
    if not folder.is_dir():
        raise FileNotFoundError(f"The specified folder does not exist: {folder}")

    gitignore_path: Path = folder / ".gitignore"
    if gitignore_path.exists():
        matches = parse_gitignore(gitignore_path)
    else:

        def matches(x) -> bool:
            return False  # No .gitignore file, so nothing is ignored

    files_found = []
    for dockerfile_path in folder.rglob(global_patten):
        if not matches(dockerfile_path):
            files_found.append(dockerfile_path)

    return files_found


def change_directory(folder: Path) -> None:
    """Change the current working directory to the specified folder.

    Args:
        folder: The Path object for the directory to change to.
    """
    if folder:
        if not folder.exists():
            raise SimpleGitToolError(f"Directory does not exist: {folder}")
        if not folder.is_dir():
            raise SimpleGitToolError(f"Not a directory: {folder}")

        # CLI_CONSOLE.print(f"Changing to directory: [cyan]{folder}[/cyan]")
        os.chdir(folder)


def get_all_project_folder(base_folder: Path, exclusion_list: list[str] = None) -> list[Path]:
    """Get all project folders in the base folder that have a .git folder in them.

    Args:
        base_folder: The Path object for the base directory to search.
        exclusion_list: A list of folder names to exclude from the results.
    """
    if exclusion_list is None:
        exclusion_list = []
    project_folders = []
    for item in base_folder.iterdir():
        if item.is_dir() and (item / ".git").exists() and item.name not in exclusion_list:
            project_folders.append(item)
    return project_folders

def quick_save(file_path: Path | str, content: str | list | dict ) -> None:
    """Quickly saves content to a file.

    Args:
        file_path: The Path object for the file to save.
        content: The content to write to the file.
    """
    if isinstance(file_path, str):
        file_path = OUTPUT_FOLDER / file_path

    if isinstance(content, list | dict) and file_path.suffix == ".json":
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(content, file, indent=4, default=str)
    elif file_path.suffix == ".txt":
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

    CLI_CONSOLE.print(f"[red]>> Saved content to [/red][cyan]{file_path}[/cyan]")
