import tomllib
from pathlib import Path
from typing import Dict, Any

# Define a dictionary of default configuration settings.
# These values will be used if the TOML file is not found or
# specific settings are missing.
DEFAULT_CONFIG = {
    "doc_folder": Path.home() / "Documents" / "code_review",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "max_lines_to_display": 100,
}


def get_config() -> Dict[str, Any]:
    """
    Reads the application's configuration from a TOML file.

    The function looks for a 'config.toml' file in the user's
    recommended configuration directory (~/.config/my_cli_app).
    It merges the settings from the file with a set of default
    values, ensuring all variables are always set.

    Returns:
        dict: A dictionary containing the complete application configuration.
    """
    config_dir = Path.home() / ".config" / "my_cli_app"
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


if __name__ == "__main__":
    # Get the complete application configuration
    settings = get_config()

    print("Final configuration loaded:")
    print(f"  - DOC_FOLDER: {settings['doc_folder']}")
    print(f"  - DATE_FORMAT: {settings['date_format']}")
    print(f"  - MAX_LINES_TO_DISPLAY: {settings['max_lines_to_display']}")

    # Example: create the documentation directory if it doesn't exist
    settings["doc_folder"].mkdir(parents=True, exist_ok=True)
