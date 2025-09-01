import configparser
import os
from collections import defaultdict
from pathlib import Path

from code_review.settings import OUTPUT_FOLDER


def parse_bumpversion_config(file_path: Path) -> dict:
    """Parses a setup.cfg file to extract bumpversion configuration.

    Args:
        file_path (str): The path to the setup.cfg file.

    Returns:
        dict: A dictionary containing the parsed bumpversion configuration.
              Returns an empty dictionary if the file doesn't exist or
              the bumpversion section is not found.
    """
    if not file_path.exists():
        print(f"Error: The file '{file_path}' was not found.")
        raise FileNotFoundError(f"The file '{file_path}' was not found.")
        # return {}

    config = configparser.ConfigParser()
    try:
        config.read(file_path)
    except configparser.MissingSectionHeaderError:
        print(f"Error: The file '{file_path}' is not a valid INI-style file.")
        return {}

    parsed_config = defaultdict(dict)

    return dict(parsed_config)


def temp():
    # For demonstration, create a temporary setup.cfg file content
    cfg_content = """
[bumpversion]
current_version = 11.3.0
tag = False
commit = True

[bumpversion:file:pay_options_middleware/__init__.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"

[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"
"""

    # Write the content to a dummy file to simulate reading from disk
    dummy_file_path = OUTPUT_FOLDER / "setup.cfg"
    with open(dummy_file_path, "w") as f:
        f.write(cfg_content)

    # Call the function with the dummy file path
    bump_config = parse_bumpversion_config(dummy_file_path)

    # Print the resulting dictionary
    if bump_config:
        import json

        print(json.dumps(bump_config, indent=4))

    # Clean up the dummy file
    os.remove(dummy_file_path)


import json
from pathlib import Path
from typing import Any


def setup_to_dict(file_path: Path) -> dict[str, Any]:
    """Parses a .cfg file and extracts all sections and their key-value pairs
    into a nested dictionary.

    Args:
        file_path (Path): The path to the .cfg file.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed configuration.
                        Returns an empty dictionary if the file doesn't exist.
    """
    if not file_path.exists():
        print(f"Error: The file '{file_path}' was not found.")
        return {}

    config = configparser.ConfigParser()
    try:
        config.read(file_path)
    except configparser.MissingSectionHeaderError:
        print(f"Error: The file '{file_path}' is not a valid INI-style file.")
        return {}

    # Convert the configparser object to a standard nested dictionary
    parsed_config = {section: dict(config[section]) for section in config.sections()}

    # Check if 'bumpversion' section exists and try to parse boolean values
    if "bumpversion" in parsed_config:
        try:
            # Note: configparser.getboolean() is needed for correct parsing,
            # so we'll re-read those specific keys from the original parser.
            parsed_config["bumpversion"]["tag"] = config.getboolean("bumpversion", "tag", fallback=False)
            parsed_config["bumpversion"]["commit"] = config.getboolean("bumpversion", "commit", fallback=False)
        except (ValueError, configparser.NoOptionError):
            pass  # Keep original string values if parsing fails

    return parsed_config


if __name__ == "__main__":
    # For demonstration, create a temporary setup.cfg file content
    cfg_content = """
[bumpversion]
current_version = 11.3.0
tag = False
commit = True

[bumpversion:file:pay_options_middleware/__init__.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"

[bumpversion:file:package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"

[flake8]
max-line-length = 119
exclude = .tox,.git,*/migrations/*,*/static/CACHE/*,docs,node_modules,venv,.venv
extend-ignore = E203

[pycodestyle]
max-line-length = 119
exclude = .tox,.git,*/migrations/*,*/static/CACHE/*,docs,node_modules,venv,.venv
"""

    # Write the content to a dummy file to simulate reading from disk
    dummy_file_path = Path("setup.cfg")
    with open(dummy_file_path, "w") as f:
        f.write(cfg_content)

    # Call the function with the dummy file path
    full_config = setup_to_dict(dummy_file_path)

    # Print the resulting dictionary
    if full_config:
        print(json.dumps(full_config, indent=4))

    # Clean up the dummy file
    os.remove(dummy_file_path)
