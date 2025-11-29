import json
from datetime import datetime
from pathlib import Path
from typing import Any

from code_review.config import DEFAULT_CONFIG
from code_review.settings import OUTPUT_FOLDER


def sort_configuration(json_file: Path) -> Path:
    """
    Reads a configuration from a JSON file, sorts the list of service
    requirements within the 'vetted_requirements' section by 'name',
    and saves the content back to the file.

    Args:
        json_file: The Path object pointing to the JSON configuration file.

    Returns:
        The Path object of the modified JSON file.
    """

    # 1. Load the content from the JSON file
    try:
        with open(json_file) as f:
            config: dict[str, Any] = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {json_file}")
        return json_file
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file}")
        return json_file
    except Exception as e:
        print(f"An unexpected error occurred during file reading: {e}")
        return json_file

    # 2. Access the 'services' list and sort it
    try:
        services_list = config["vetted_requirements"]["services"]

        # Sort the list of dictionaries by the value of the 'name' key
        services_list.sort(key=lambda req: req["name"])

        # The 'services_list' is a reference to the list inside 'config',
        # so 'config' is now sorted.

    except KeyError as e:
        print(f"Error: Missing expected key in the configuration: {e}")
        return json_file

    # 3. Save the sorted content back to the same JSON file
    # 'indent=4' makes the file human-readable, and 'default=str' is
    # necessary to serialize the Path object (if it exists in the config)
    timestamp = datetime.now().strftime("%Y%m%d%_H%M%S")
    new_json_file = json_file.parent / f"{json_file.stem}_{timestamp}.json"
    try:
        with open(new_json_file, "w") as f:
            json.dump(config, f, indent=4, default=str)
    except Exception as e:
        print(f"An unexpected error occurred during file writing: {e}")
        return json_file

    return new_json_file


# Helper function to write the initial config (converting Path to string)
def write_initial_config(path: Path, config: dict[str, Any]):
    with open(path, "w") as f:
        # Use default=str to handle the Path object in 'doc_folder'
        json.dump(config, f, indent=4, default=str)

def main():
    example_config_file = OUTPUT_FOLDER / "example_config.json"
    write_initial_config(example_config_file, DEFAULT_CONFIG)
    print(f"✅ Created initial configuration file at: {example_config_file.resolve()}")

    # 2. Call the function to sort the requirements
    sorted_file_path = sort_configuration(example_config_file)
    print(f"🔄 Sorted configuration saved to: {sorted_file_path.resolve()}")

    # 3. Verify the result (optional)
    with open(sorted_file_path) as f:
        sorted_config = json.load(f)
        sorted_names = [req["name"] for req in sorted_config["vetted_requirements"]["services"]]

    print("\n📋 Names in the sorted 'services' list:")
    print(sorted_names)

    # Expected sorted order: ['argon2-cffi', 'django', 'pillow', 'python-slugify']

    # 4. Clean up the test file
    # import os
    # os.remove(test_file_path)
    # print(f"\n🗑️ Cleaned up test file: {test_file_path}")
if __name__ == '__main__':
    main()