from pathlib import Path
from typing import Any

import yaml


def parse_yaml_file(file_path: Path) -> dict[str, Any] | None:
    """Parses a YAML file and returns a Python dictionary.

    Args:
      file_path: The path to the YAML file.

    Returns:
      A dictionary representing the parsed YAML content.
    """
    try:
        with open(file_path) as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return None
