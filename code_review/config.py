from pathlib import Path
from typing import Any

import tomllib

# Define a dictionary of default configuration settings.
# These values will be used if the TOML file is not found or
# specific settings are missing.
DEFAULT_CONFIG = {
    "doc_folder": Path.home() / "Documents" / "code_review_plus",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "max_lines_to_display": 100,
    "docker_images": {
        "python": "3.12.11-slim-bookworm",
        "node": "20.19.4-alpine3",
        "postgres": "postgres:16.10-bookworm",
    },
}


def get_config() -> dict[str, Any]:
    """Reads the application's configuration from a TOML file.

    The function looks for a 'config.toml' file in the user's
    recommended configuration directory (~/.config/my_cli_app).
    It merges the settings from the file with a set of default
    values, ensuring all variables are always set.

    Returns:
        dict: A dictionary containing the complete application configuration.
    """
    config_dir = Path.home() / ".config" / "code_review_plus"
    config_file = config_dir / "config.toml"

    # Use a copy of the defaults to avoid modifying the original dictionary.
    config = DEFAULT_CONFIG.copy()

    # Check if the TOML file exists
    if not config_file.is_file():
        print("Configuration file not found. Using default settings.")
        return config

    try:
        with open(config_file, "rb") as f:
            toml_data = tomllib.load(f)

            # Extract the settings for our application.
            app_settings = toml_data.get("tool", {}).get("cli_app", {})

            # Update the configuration with values from the TOML file.
            # Using get() with a default value prevents KeyErrors if a setting is missing.
            config["doc_folder"] = Path(app_settings.get("doc_folder", config["doc_folder"])).expanduser()
            config["date_format"] = app_settings.get("date_format", config["date_format"])
            config["max_lines_to_display"] = app_settings.get("max_lines_to_display", config["max_lines_to_display"])

    except tomllib.TOMLDecodeError as e:
        print(f"Error decoding TOML file: {e}. Using default settings.")

    except Exception as e:
        print(f"An unexpected error occurred while reading the config: {e}. Using default settings.")

    return config
