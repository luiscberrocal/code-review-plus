import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import toml
import tomllib

from code_review.exceptions import ConfigurationError
from code_review.plugins.docker.schemas import DockerImageSchema

logger = logging.getLogger(__name__)
# Define a dictionary of default configuration settings.
# These values will be used if the TOML file is not found or
# specific settings are missing.
DEFAULT_CONFIG = {
    "doc_folder": Path.home() / "Documents" / "code_review_plus",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "max_lines_to_display": 100,
    "docker_images": {
        "python": {"name": "python", "version": "3.12.11", "operating_system": "slim-bookworm"},
        "node": {"name": "node", "version": "20.19.4", "operating_system": "alpine3"},
        "postgres": {"name": "postgres", "version": "16.10", "operating_system": "bookworm"},
    },
    "default_branches": ["master", "develop"],
    "vetted_requirements": {
        "services": [
            {"name": "python-slugify", "version": "8.0.4", "specifier": "==", "source": None},
            {"name": "pillow", "version": "12.0.0", "specifier": "==", "source": None},
            {"name": "argon2-cffi", "version": "25.1.0", "specifier": "==", "source": None},
            {"name": "whitenoise", "version": "6.11.0", "specifier": "==", "source": None},
            {"name": "redis", "version": "6.4.0", "specifier": "==", "source": None},
            {"name": "hiredis", "version": "3.3.0", "specifier": "==", "source": None},
            {"name": "celery", "version": "5.5.3", "specifier": "==", "source": None},
            {"name": "django-celery-beat", "version": "2.8.1", "specifier": "==", "source": None},
            {"name": "django-celery-results", "version": "2.6.0", "specifier": "==", "source": None},
            {"name": "uvicorn[standard]", "version": "0.38.0", "specifier": "==", "source": None},
            {"name": "django", "version": "5.2.7", "specifier": "==", "source": None},
            {"name": "django-environ", "version": "0.12.0", "specifier": "==", "source": None},
            {"name": "django-model-utils", "version": "5.0.0", "specifier": "==", "source": None},
            {"name": "django-allauth", "version": "65.12.1", "specifier": "==", "source": None},
            {"name": "django-crispy-forms", "version": "2.4", "specifier": "==", "source": None},
            {"name": "crispy-bootstrap5", "version": "2025.6", "specifier": "==", "source": None},
            {"name": "django-redis", "version": "6.0.0", "specifier": "==", "source": None},
            {"name": "django-filter", "version": "24.2", "specifier": "==", "source": None},
            {"name": "djangorestframework", "version": "3.16.1", "specifier": "==", "source": None},
            {"name": "django-cors-headers", "version": "4.9.0", "specifier": "==", "source": None},
            {"name": "drf-spectacular", "version": "0.28.0", "specifier": "==", "source": None},
            {"name": "factory-boy", "version": "3.3.3", "specifier": "==", "source": None},
            {"name": "django-import-export", "version": "4.3.12", "specifier": "==", "source": None},
            {"name": "django-widget-tweaks", "version": "1.5.0", "specifier": "==", "source": None},
            {
                "name": "finance-engine-sdk",
                "version": "6.8.0",
                "specifier": "@",
                "source": "git+https://PYPI_READ_TOKEN:${PYPI_TOKEN}@gitlab.com/adelantos-development/finance-engine-sdk.git@v6.8.0",
            },
            {
                "name": "pj_django_payments",
                "version": "21.2.0",
                "specifier": "@",
                "source": "git+https://PYPI_READ_TOKEN:${PYPI_TOKEN}@gitlab.com/adelantos-development/pj_django_payments.git@v21.2.0",
            },
            {"name": "django-htmx", "version": "1.26.0", "specifier": "==", "source": None},
            {"name": "werkzeug[watchdog]", "version": "3.1.3", "specifier": "==", "source": None},
            {"name": "ipdb", "version": "0.13.13", "specifier": "==", "source": None},
            {"name": "psycopg[c]", "version": "3.2.12", "specifier": "==", "source": None},
            {"name": "watchfiles", "version": "1.1.1", "specifier": "==", "source": None},
            {"name": "django-stubs", "version": "5.2.7", "specifier": "==", "source": None},
            {"name": "pytest", "version": "8.4.2", "specifier": "==", "source": None},
            {"name": "pytest-sugar", "version": "1.1.1", "specifier": "==", "source": None},
            {"name": "djangorestframework-stubs", "version": "3.16.5", "specifier": "==", "source": None},
            {"name": "coverage", "version": "7.11.0", "specifier": "==", "source": None},
            {"name": "djlint", "version": "1.36.4", "specifier": "==", "source": None},
            {"name": "pylint-django", "version": "2.6.1", "specifier": "==", "source": None},
            {"name": "pylint-celery", "version": "0.3", "specifier": "==", "source": None},
            {"name": "pre-commit", "version": "4.3.0", "specifier": "==", "source": None},
            {"name": "django-debug-toolbar", "version": "6.0.0", "specifier": "==", "source": None},
            {"name": "django-extensions", "version": "4.1", "specifier": "==", "source": None},
            {"name": "django-coverage-plugin", "version": "3.2.0", "specifier": "==", "source": None},
            {"name": "pytest-django", "version": "4.11.1", "specifier": "==", "source": None},
            {"name": "pur", "version": "7.3.3", "specifier": "==", "source": None},
            {"name": "gunicorn", "version": "23.0.0", "specifier": "==", "source": None},
            {"name": "psycopg[c]", "version": "3.2.12", "specifier": "==", "source": None},
            {"name": "django-storages[boto3]", "version": "1.14.6", "specifier": "==", "source": None},
            {"name": "django-anymail[mailgun]", "version": "13.1", "specifier": "==", "source": None},
            {"name": "watchtower", "version": "3.4.0", "specifier": "==", "source": None},
        ],
    },
}


class TomlConfigManager:
    """A class to manage reading and writing TOML configuration files."""

    def __init__(
        self,
        config_dir: Path = Path.home() / ".config" / "code_review_plus",
        config_file_name: str = "config.toml",
        default_config: dict[str, Any] = None,
    ) -> None:
        """Initializes the TomlConfigManager.

        Args:
            config_dir (Path): The directory where the config file is located.
            config_file_name (str): The name of the main config file.
            default_config (dict[str, Any]): The default configuration dictionary.
        """
        self.config_dir = config_dir
        self.config_file = self.config_dir / config_file_name
        self.config_data: dict[str, Any] = default_config.copy() if default_config else DEFAULT_CONFIG.copy()

    def load_config(self) -> dict[str, Any]:
        """Reads the application's configuration from a TOML file.

        The function looks for a 'config.toml' file in the user's
        recommended configuration directory. It merges the settings from the file
        with a set of default values, ensuring all variables are always set.

        Returns:
            dict: A dictionary containing the complete application configuration.
        """
        if not self.config_file.is_file() or not self.config_file.exists():
            logger.warning("Configuration file not found. Using default settings.")
            return self.config_data

        try:
            with open(self.config_file, "rb") as f:
                toml_data = tomllib.load(f)

            # Extract the settings for our application.
            app_settings = toml_data.get("tool", {}).get("cli_app", {})
            docker_images = (app_settings.get("docker_images", self.config_data["docker_images"]),)
            docker_images_dict = {}
            for image_name, image_info in docker_images[0].items():
                docker_images_dict[image_name] = DockerImageSchema(**image_info)

            # Update the configuration with values from the TOML file.
            self.config_data.update(
                {
                    "doc_folder": Path(app_settings.get("doc_folder", self.config_data["doc_folder"])).expanduser(),
                    "date_format": app_settings.get("date_format", self.config_data["date_format"]),
                    "max_lines_to_display": app_settings.get(
                        "max_lines_to_display",
                        self.config_data["max_lines_to_display"],
                    ),
                    "docker_images": docker_images_dict,
                }
            )

        except tomllib.TOMLDecodeError as e:
            logger.error("Error decoding TOML file: %s. Using default settings.", e)
            raise ConfigurationError(f"Error decoding TOML file: {e}") from e
        except TypeError as e:
            logger.error("Type error in config file: %s. Using default settings.", e)
            raise ConfigurationError(f"Type error in config file: {e}") from e
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise e
            logger.error(
                "An unexpected error occurred while reading the config: %s. Using default settings.",
                e,
            )
            raise ConfigurationError(f"An unexpected error occurred while reading the config: {e}") from e

        return self.config_data

    def save_config(self, data: dict[str, Any] = None, create_backup: bool = True) -> None:
        """Saves the current configuration to a TOML file.

        Args:
            data (dict): The dictionary to save. If None, the current
                         config_data of the instance will be saved.
            create_backup (bool): If True, a timestamped backup file will be created.
        """
        data_to_save = data if data is not None else self.config_data

        # Create a nested dictionary structure for the TOML file
        config_to_write = {"tool": {"cli_app": {}}}
        # Filter out the docker_images from the root level
        root_data = {k: v for k, v in data_to_save.items() if k not in ["docker_images"]}

        config_to_write["tool"]["cli_app"].update(root_data)

        # Add the docker_images section
        config_to_write["tool"]["cli_app"]["docker_images"] = data_to_save.get("docker_images", {})

        self.config_dir.mkdir(parents=True, exist_ok=True)

        if create_backup and self.config_file.is_file():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_file = self.config_dir / f"config-{timestamp}.toml"
            try:
                self.config_file.rename(backup_file)
                logger.info("Created backup file: %s", backup_file)
            except OSError as e:
                logger.error("Error creating backup file: %s", e)

        try:
            with open(self.config_file, "w") as f:
                toml.dump(config_to_write, f)
            logger.info("Configuration saved to %s", self.config_file)
        except Exception as e:
            logger.error("An unexpected error occurred while saving the config: %s", e)


CONFIG_MANAGER = TomlConfigManager()


def get_config(manager: TomlConfigManager = CONFIG_MANAGER) -> dict[str, Any]:
    """Reads the application's configuration from a TOML file.

    The function looks for a 'config.toml' file in the user's
    recommended configuration directory. It merges the settings from the file
    with a set of default values, ensuring all variables are always set.

    Returns:
        dict: A dictionary containing the complete application configuration.
    """
    try:
        config = manager.load_config()
        if not manager.config_file.exists():
            manager.save_config(config, create_backup=True)
        return config
    except ConfigurationError as e:
        logger.error("Failed to load configuration: %s from %s", e, manager.config_file)
        raise e
