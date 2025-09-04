import tomllib
from pathlib import Path

# Define the default path for the documentation folder.
# This value will be used if the TOML file is not found or the setting is not present.
DEFAULT_DOC_FOLDER = Path.home() / "Documents" / "code_review"


def get_doc_folder() -> Path:
    """
    Reads the configuration from a TOML file.

    The function checks for a configuration file in the user's home directory,
    specifically following the XDG Base Directory Specification for user-specific
    configuration files on Linux.

    Returns:
        pathlib.Path: The configured documentation folder path.
    """
    config_dir = Path.home() / ".config" / "code_review_plus"
    config_file = config_dir / "config.toml"

    # Ensure the config directory exists to avoid errors later.
    config_dir.mkdir(parents=True, exist_ok=True)

    print(f"Checking for config file at: {config_file}")

    # Check if the TOML file exists
    if not config_file.is_file():
        print(f"Configuration file not found. Using default path.")
        return DEFAULT_DOC_FOLDER

    try:
        with open(config_file, "rb") as f:
            config_data = tomllib.load(f)
            # The setting is nested under [tool.cli_app]
            doc_folder_str = config_data.get("tool", {}).get("cli_app", {}).get("doc_folder")

            if doc_folder_str:
                # Expand the user home directory if '~' is used in the config file.
                return Path(doc_folder_str).expanduser()
            else:
                print("Setting 'doc_folder' not found in TOML file. Using default path.")
                return DEFAULT_DOC_FOLDER

    except tomllib.TOMLDecodeError as e:
        # Handle the case where the TOML file is invalid.
        print(f"Error decoding TOML file: {e}. Using default path.")
        return DEFAULT_DOC_FOLDER


if __name__ == "__main__":
    final_doc_folder = get_doc_folder()
    print(f"\nFinal DOC_FOLDER is set to: {final_doc_folder}")
    print(f"Does the path exist? {final_doc_folder.exists()}")

    # Example: create the directory if it doesn't exist
    final_doc_folder.mkdir(parents=True, exist_ok=True)
