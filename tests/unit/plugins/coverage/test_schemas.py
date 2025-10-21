import io
from pathlib import PosixPath

import yaml

from code_review import settings
from code_review.plugins.coverage.schemas import TestConfiguration

# --- 1. Define the YAML content with the custom tag ---
yaml_content = """
project_folder: !!python/object/apply:pathlib.PosixPath
- /
- home
- luiscberrocal
- PycharmProjects
- code-review-plus
- output
- project_folder
unit_tests:
- middleware.middleware.tests.unit
- middleware.users.tests
min_coverage: 85.0
settings_module: config.settings.local
tags_to_exclude:
- INTEGRATION
"""


# --- 2. Define the Custom Constructor Function ---
# This function tells PyYAML how to handle the specific tag.
# Define the custom constructor function with type hints
def posixpath_constructor(loader: yaml.loader.SafeLoader, node: yaml.nodes.Node) -> PosixPath:
    """
    Constructs a pathlib.PosixPath object from a YAML sequence node.
    The sequence node contains a list of path components (strings).

    Args:
        loader: The PyYAML loader instance (SafeLoader in this case).
        node: The YAML node containing the sequence of path components.

    Returns:
        A fully constructed pathlib.PosixPath object.
    """
    # Use the loader to construct the sequence of strings from the node
    path_components: list[str] = loader.construct_sequence(node)

    # Unpack the list of path components and pass them as arguments
    # to the PosixPath constructor to create the final path object.
    return PosixPath(*path_components)


# --- 3. Register the Constructor with SafeLoader ---
# The tag in the YAML is: !!python/object/apply:pathlib.PosixPath
# When resolved to a full YAML tag URI, it becomes:
# tag:yaml.org,2002:python/object/apply:pathlib.PosixPath
tag_to_register = "tag:yaml.org,2002:python/object/apply:pathlib.PosixPath"
yaml.add_constructor(tag_to_register, posixpath_constructor, Loader=yaml.SafeLoader)



class TestTestConfiguration:
    
    def test_write(self, tmp_path):
        target_folder = settings.OUTPUT_FOLDER / "project_folder"
        # target_folder = tmp_path  / "project_folder"
        tests_to_run = "middleware.middleware.tests.unit middleware.users.tests"
        min_coverage = 85


        settings_module_t = "config.settings.local"
        unit_tests_to_run = tests_to_run.split(" ")

        test_config = TestConfiguration(
            folder=target_folder, unit_tests=unit_tests_to_run, min_coverage=min_coverage, settings_module=settings_module_t
        )
        yaml_file_path = settings.OUTPUT_FOLDER  / "__test_config.yaml"
        with open(yaml_file_path, "w") as file:
            # `sort_keys=False` is often used to maintain the order from the model/dictionary
            # `default_flow_style=False` ensures a block-style (multi-line) YAML output for readability
            yaml.dump(test_config.model_dump(), file, sort_keys=False, default_flow_style=False)

        assert yaml_file_path.exists()

        with open(yaml_file_path) as file:
            loaded_config = yaml.safe_load(io.StringIO(yaml_content))

        assert loaded_config["folder"] == str(target_folder)
        assert loaded_config["unit_tests"] == unit_tests_to_run
        assert loaded_config["min_coverage"] == min_coverage
        assert loaded_config["settings_module"] == settings_module_t

        loaded_data = TestConfiguration(**loaded_config)
        assert loaded_data == test_config


    def test_read_config(self):

        yaml_content = """
        folder: !!python/object/apply:pathlib.PosixPath
        - /
        - home
        - luiscberrocal
        - PycharmProjects
        - code-review-plus
        - output
        - code-review-plus
        unit_tests:
        - middleware.middleware.tests.unit
        - middleware.users.tests
        min_coverage: 85.0
        settings_module: config.settings.local
        tags_to_exclude:
        - INTEGRATION
        """

        data = yaml.safe_load(io.StringIO(yaml_content))
        test_config = TestConfiguration(**data)
        assert test_config.folder == PosixPath("/home/luiscberrocal/PycharmProjects/code-review-plus/output/code-review-plus")




