"""Tests for Django settings handlers."""

import pytest
from pathlib import Path

from code_review.plugins.django.settings_handlers import (
    DjangoSettingsVisitor,
    load_vetted_variables,
    validate_settings_module,
    validate_settings_directory,
    VettedVariable,
    VariableIssue,
)


class TestLoadVettedVariables:
    """Tests for loading vetted variables from JSON."""

    def test_load_vetted_variables(self, fixtures_folder):
        """Test loading vetted variables from JSON file."""
        json_path = fixtures_folder / "django" / "config" / "settings" / "vetted_variables.json"

        vetted_vars = load_vetted_variables(json_path)

        assert len(vetted_vars) > 0
        assert "BASE_DIR" in vetted_vars
        assert "DEBUG" in vetted_vars
        assert "DATABASES" in vetted_vars

        # Check structure
        base_dir_var = vetted_vars["BASE_DIR"]
        assert isinstance(base_dir_var, VettedVariable)
        assert base_dir_var.name == "BASE_DIR"
        assert base_dir_var.type == "Path"
        assert base_dir_var.vetted is True
        assert "base.py" in base_dir_var.modules

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_vetted_variables(Path("/nonexistent/file.json"))


class TestValidateSettingsModule:
    """Tests for validating individual settings modules."""

    def test_validate_base_settings(self, fixtures_folder):
        """Test validating base.py settings module."""
        settings_dir = fixtures_folder / "django" / "config" / "settings"
        json_path = settings_dir / "vetted_variables.json"
        module_path = settings_dir / "base.py"

        vetted_vars = load_vetted_variables(json_path)
        result = validate_settings_module(module_path, vetted_vars, check_missing=True)

        assert result.module_name == "base.py"
        assert result.total_variables > 0
        assert result.module_path == module_path

    def test_validate_local_settings(self, fixtures_folder):
        """Test validating local.py settings module."""
        settings_dir = fixtures_folder / "django" / "config" / "settings"
        json_path = settings_dir / "vetted_variables.json"
        module_path = settings_dir / "local.py"

        vetted_vars = load_vetted_variables(json_path)
        result = validate_settings_module(module_path, vetted_vars, check_missing=True)

        assert result.module_name == "local.py"
        assert result.total_variables > 0

    def test_validate_production_settings(self, fixtures_folder):
        """Test validating production.py settings module."""
        settings_dir = fixtures_folder / "django" / "config" / "settings"
        json_path = settings_dir / "vetted_variables.json"
        module_path = settings_dir / "production.py"

        vetted_vars = load_vetted_variables(json_path)
        result = validate_settings_module(module_path, vetted_vars, check_missing=True)

        assert result.module_name == "production.py"
        assert result.total_variables > 0

    def test_validate_test_settings(self, fixtures_folder):
        """Test validating test.py settings module."""
        settings_dir = fixtures_folder / "django" / "config" / "settings"
        json_path = settings_dir / "vetted_variables.json"
        module_path = settings_dir / "test.py"

        vetted_vars = load_vetted_variables(json_path)
        result = validate_settings_module(module_path, vetted_vars, check_missing=True)

        assert result.module_name == "test.py"
        assert result.total_variables > 0

    def test_validate_nonexistent_module(self):
        """Test validating non-existent module raises error."""
        vetted_vars = {}
        with pytest.raises(FileNotFoundError):
            validate_settings_module(Path("/nonexistent/module.py"), vetted_vars)


class TestValidateSettingsDirectory:
    """Tests for validating entire settings directory."""

    def test_validate_all_settings(self, fixtures_folder):
        """Test validating all settings modules in directory."""
        settings_dir = fixtures_folder / "django" / "config" / "settings"
        json_path = settings_dir / "vetted_variables.json"

        results = validate_settings_directory(settings_dir, json_path, check_missing=True)

        # Should have results for base.py, local.py, production.py, test.py
        assert len(results) >= 4

        module_names = [r.module_name for r in results]
        assert "base.py" in module_names
        assert "local.py" in module_names
        assert "production.py" in module_names
        assert "test.py" in module_names

        # __init__.py should be skipped
        assert "__init__.py" not in module_names

    def test_validate_nonexistent_directory(self, fixtures_folder):
        """Test validating non-existent directory raises error."""
        json_path = fixtures_folder / "django" / "config" / "settings" / "vetted_variables.json"

        with pytest.raises(FileNotFoundError):
            validate_settings_directory(Path("/nonexistent/dir"), json_path)


class TestDjangoSettingsVisitor:
    """Tests for the AST visitor."""

    def test_visitor_finds_variables(self, fixtures_folder):
        """Test that visitor correctly identifies variables."""
        import ast

        settings_dir = fixtures_folder / "django" / "config" / "settings"
        json_path = settings_dir / "vetted_variables.json"
        module_path = settings_dir / "base.py"

        vetted_vars = load_vetted_variables(json_path)

        with open(module_path, "r") as f:
            tree = ast.parse(f.read())

        visitor = DjangoSettingsVisitor("base.py", vetted_vars)
        visitor.visit(tree)

        # Should find common Django settings
        assert "DEBUG" in visitor.found_variables
        assert "DATABASES" in visitor.found_variables
        assert "INSTALLED_APPS" in visitor.found_variables
        assert "MIDDLEWARE" in visitor.found_variables

    def test_visitor_detects_unknown_variables(self):
        """Test that visitor detects unknown variables."""
        import ast

        code = """
DEBUG = True
UNKNOWN_VARIABLE = "test"
ANOTHER_UNKNOWN = 123
"""

        vetted_vars = {
            "DEBUG": VettedVariable(name="DEBUG", type="bool", vetted=True, modules=["base.py"])
        }

        tree = ast.parse(code)
        visitor = DjangoSettingsVisitor("base.py", vetted_vars)
        visitor.visit(tree)

        # Should have issues for unknown variables
        unknown_issues = [i for i in visitor.issues if i.issue_type == "unknown"]
        assert len(unknown_issues) == 2
        assert any(i.variable_name == "UNKNOWN_VARIABLE" for i in unknown_issues)
        assert any(i.variable_name == "ANOTHER_UNKNOWN" for i in unknown_issues)

    def test_visitor_detects_wrong_module(self):
        """Test that visitor detects variables in wrong module."""
        import ast

        code = """
DEBUG = True
SECRET_KEY = "test-key"
"""

        vetted_vars = {
            "DEBUG": VettedVariable(name="DEBUG", type="bool", vetted=True, modules=["base.py"]),
            "SECRET_KEY": VettedVariable(name="SECRET_KEY", type="str", vetted=True, modules=["local.py", "production.py"]),
        }

        tree = ast.parse(code)
        visitor = DjangoSettingsVisitor("base.py", vetted_vars)
        visitor.visit(tree)

        # Should have issue for SECRET_KEY in wrong module
        wrong_module_issues = [i for i in visitor.issues if i.issue_type == "wrong_module"]
        assert len(wrong_module_issues) == 1
        assert wrong_module_issues[0].variable_name == "SECRET_KEY"

    def test_visitor_detects_missing_variables(self):
        """Test that visitor detects missing expected variables."""
        import ast

        code = """
DEBUG = True
"""

        vetted_vars = {
            "DEBUG": VettedVariable(name="DEBUG", type="bool", vetted=True, modules=["base.py"]),
            "DATABASES": VettedVariable(name="DATABASES", type="dict", vetted=True, modules=["base.py"]),
            "SECRET_KEY": VettedVariable(name="SECRET_KEY", type="str", vetted=True, modules=["local.py"]),
        }

        tree = ast.parse(code)
        visitor = DjangoSettingsVisitor("base.py", vetted_vars)
        visitor.visit(tree)
        visitor.check_missing_variables()

        # Should have issue for missing DATABASES
        missing_issues = [i for i in visitor.issues if i.issue_type == "missing"]
        assert len(missing_issues) == 1
        assert missing_issues[0].variable_name == "DATABASES"

    def test_visitor_ignores_private_variables(self):
        """Test that visitor ignores private variables except AWS ones."""
        import ast

        code = """
_private_var = "test"
_AWS_EXPIRY = 3600
__double_private = "test"
"""

        vetted_vars = {
            "_AWS_EXPIRY": VettedVariable(name="_AWS_EXPIRY", type="int", vetted=True, modules=["production.py"])
        }

        tree = ast.parse(code)
        visitor = DjangoSettingsVisitor("production.py", vetted_vars)
        visitor.visit(tree)

        # Should only find _AWS_EXPIRY
        assert "_AWS_EXPIRY" in visitor.found_variables
        assert "_private_var" not in visitor.found_variables
        assert "__double_private" not in visitor.found_variables


class TestValidationResult:
    """Tests for validation result properties."""

    def test_has_issues_property(self):
        """Test has_issues property."""
        from code_review.plugins.django.settings_handlers import SettingsValidationResult

        result = SettingsValidationResult(
            module_path=Path("/test/base.py"),
            module_name="base.py",
            total_variables=10,
            vetted_variables=8,
            issues=[],
        )
        assert result.has_issues is False

        result.issues.append(
            VariableIssue(
                variable_name="TEST",
                issue_type="unknown",
                module_name="base.py",
                message="Test issue",
            )
        )
        assert result.has_issues is True

    def test_issue_counts(self):
        """Test issue count properties."""
        from code_review.plugins.django.settings_handlers import SettingsValidationResult

        result = SettingsValidationResult(
            module_path=Path("/test/base.py"),
            module_name="base.py",
            total_variables=10,
            vetted_variables=8,
            issues=[
                VariableIssue(
                    variable_name="UNKNOWN1",
                    issue_type="unknown",
                    module_name="base.py",
                    message="Unknown variable",
                ),
                VariableIssue(
                    variable_name="UNKNOWN2",
                    issue_type="unknown",
                    module_name="base.py",
                    message="Unknown variable",
                ),
                VariableIssue(
                    variable_name="WRONG",
                    issue_type="wrong_module",
                    module_name="base.py",
                    message="Wrong module",
                ),
                VariableIssue(
                    variable_name="MISSING",
                    issue_type="missing",
                    module_name="base.py",
                    message="Missing variable",
                ),
            ],
        )

        assert result.unknown_variables_count == 2
        assert result.wrong_module_count == 1
        assert result.missing_variables_count == 1

