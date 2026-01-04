"""Handlers for validating Django settings modules against vetted variables."""

import ast
import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class VettedVariable(BaseModel):
    """Schema for a vetted Django settings variable."""

    name: str = Field(description="Variable name")
    type: str = Field(description="Python type of the variable")
    vetted: bool = Field(default=True, description="Whether the variable is vetted")
    modules: list[str] = Field(default_factory=list, description="Modules where this variable should appear")


class VariableIssue(BaseModel):
    """Schema for a variable validation issue."""

    variable_name: str = Field(description="Name of the variable")
    issue_type: str = Field(description="Type of issue (unknown, wrong_module, missing)")
    module_name: str = Field(description="Name of the settings module")
    line_number: int | None = Field(default=None, description="Line number where the issue occurs")
    message: str = Field(description="Detailed message about the issue")


class SettingsValidationResult(BaseModel):
    """Schema for settings validation results."""

    module_path: Path = Field(description="Path to the settings module")
    module_name: str = Field(description="Name of the module (e.g., 'base.py', 'local.py')")
    total_variables: int = Field(default=0, description="Total number of variables found")
    vetted_variables: int = Field(default=0, description="Number of vetted variables")
    issues: list[VariableIssue] = Field(default_factory=list, description="List of validation issues")

    @property
    def has_issues(self) -> bool:
        """Check if there are any validation issues."""
        return len(self.issues) > 0

    @property
    def unknown_variables_count(self) -> int:
        """Count of unknown variables."""
        return len([i for i in self.issues if i.issue_type == "unknown"])

    @property
    def wrong_module_count(self) -> int:
        """Count of variables in wrong module."""
        return len([i for i in self.issues if i.issue_type == "wrong_module"])

    @property
    def missing_variables_count(self) -> int:
        """Count of missing expected variables."""
        return len([i for i in self.issues if i.issue_type == "missing"])


class DjangoSettingsVisitor(ast.NodeVisitor):
    """AST Node Visitor to extract and validate Django settings variables."""

    def __init__(self, module_name: str, vetted_variables: dict[str, VettedVariable]):
        """Initialize the visitor.

        Args:
            module_name: Name of the module being parsed (e.g., 'base.py', 'local.py')
            vetted_variables: Dictionary of vetted variables keyed by variable name
        """
        self.module_name = module_name
        self.vetted_variables = vetted_variables
        self.found_variables: dict[str, int] = {}  # variable_name -> line_number
        self.issues: list[VariableIssue] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment nodes to extract variable definitions."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                line_number = node.lineno

                # Skip private variables (starting with _) unless they're Django-specific
                if var_name.startswith("_") and not var_name.startswith("_AWS"):
                    continue

                # Record the variable
                self.found_variables[var_name] = line_number

                # Validate against vetted variables
                self._validate_variable(var_name, line_number)

        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Visit augmented assignment nodes (e.g., INSTALLED_APPS += [...])."""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            line_number = node.lineno

            # Don't record augmented assigns as new variables, just validate
            if var_name not in self.found_variables:
                self.found_variables[var_name] = line_number
                self._validate_variable(var_name, line_number)

        self.generic_visit(node)

    def _validate_variable(self, var_name: str, line_number: int) -> None:
        """Validate a variable against the vetted variables list.

        Args:
            var_name: Name of the variable
            line_number: Line number where the variable is defined
        """
        if var_name not in self.vetted_variables:
            # Unknown variable - not in vetted list
            self.issues.append(
                VariableIssue(
                    variable_name=var_name,
                    issue_type="unknown",
                    module_name=self.module_name,
                    line_number=line_number,
                    message=f"Variable '{var_name}' is not in the vetted variables list",
                )
            )
        else:
            # Variable is vetted, check if it's in the right module
            vetted_var = self.vetted_variables[var_name]
            if self.module_name not in vetted_var.modules:
                self.issues.append(
                    VariableIssue(
                        variable_name=var_name,
                        issue_type="wrong_module",
                        module_name=self.module_name,
                        line_number=line_number,
                        message=f"Variable '{var_name}' found in '{self.module_name}' but expected in: {', '.join(vetted_var.modules)}",
                    )
                )

    def check_missing_variables(self) -> None:
        """Check for variables that should be in this module but are missing."""
        for var_name, vetted_var in self.vetted_variables.items():
            if self.module_name in vetted_var.modules:
                if var_name not in self.found_variables:
                    self.issues.append(
                        VariableIssue(
                            variable_name=var_name,
                            issue_type="missing",
                            module_name=self.module_name,
                            line_number=None,
                            message=f"Expected variable '{var_name}' is missing from '{self.module_name}'",
                        )
                    )


def load_vetted_variables(json_path: Path) -> dict[str, VettedVariable]:
    """Load vetted variables from JSON file.

    Args:
        json_path: Path to the vetted_variables.json file

    Returns:
        Dictionary of VettedVariable objects keyed by variable name

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON is invalid
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Vetted variables file not found: {json_path}")

    with open(json_path, "r") as f:
        data = json.load(f)

    vetted_vars = {}
    for item in data:
        var = VettedVariable(**item)
        vetted_vars[var.name] = var

    logger.info(f"Loaded {len(vetted_vars)} vetted variables from {json_path}")
    return vetted_vars


def validate_settings_module(
    module_path: Path,
    vetted_variables: dict[str, VettedVariable],
    check_missing: bool = True,
) -> SettingsValidationResult:
    """Validate a Django settings module against vetted variables.

    Args:
        module_path: Path to the settings module file
        vetted_variables: Dictionary of vetted variables
        check_missing: Whether to check for missing expected variables

    Returns:
        SettingsValidationResult with validation details

    Raises:
        FileNotFoundError: If the module file doesn't exist
        SyntaxError: If the module has syntax errors
    """
    if not module_path.exists():
        raise FileNotFoundError(f"Settings module not found: {module_path}")

    module_name = module_path.name

    # Parse the module
    try:
        with open(module_path, "r") as f:
            tree = ast.parse(f.read(), filename=str(module_path))
    except SyntaxError as e:
        logger.error(f"Syntax error in {module_path}: {e}")
        raise

    # Visit the AST
    visitor = DjangoSettingsVisitor(module_name, vetted_variables)
    visitor.visit(tree)

    # Check for missing variables if requested
    if check_missing:
        visitor.check_missing_variables()

    # Create result
    result = SettingsValidationResult(
        module_path=module_path,
        module_name=module_name,
        total_variables=len(visitor.found_variables),
        vetted_variables=len([v for v in visitor.found_variables if v in vetted_variables]),
        issues=visitor.issues,
    )

    logger.info(
        f"Validated {module_name}: {result.total_variables} variables, "
        f"{result.vetted_variables} vetted, {len(result.issues)} issues"
    )

    return result


def validate_settings_directory(
    settings_dir: Path,
    vetted_json_path: Path,
    check_missing: bool = True,
) -> list[SettingsValidationResult]:
    """Validate all Python settings modules in a directory.

    Args:
        settings_dir: Path to the settings directory
        vetted_json_path: Path to the vetted_variables.json file
        check_missing: Whether to check for missing expected variables

    Returns:
        List of SettingsValidationResult objects for each module

    Raises:
        FileNotFoundError: If the settings directory or vetted JSON doesn't exist
    """
    if not settings_dir.exists() or not settings_dir.is_dir():
        raise FileNotFoundError(f"Settings directory not found: {settings_dir}")

    # Load vetted variables
    vetted_variables = load_vetted_variables(vetted_json_path)

    results = []
    for module_path in sorted(settings_dir.glob("*.py")):
        # Skip __init__.py
        if module_path.name == "__init__.py":
            continue

        try:
            result = validate_settings_module(module_path, vetted_variables, check_missing)
            results.append(result)
        except Exception as e:
            logger.error(f"Error validating {module_path}: {e}")
            # Continue with other modules

    return results


def print_validation_report(results: list[SettingsValidationResult]) -> None:
    """Print a formatted validation report.

    Args:
        results: List of validation results to report
    """
    from rich.console import Console
    from rich.table import Table

    console = Console()

    for result in results:
        console.print(f"\n[bold cyan]Module: {result.module_name}[/bold cyan]")
        console.print(f"  Total variables: {result.total_variables}")
        console.print(f"  Vetted variables: {result.vetted_variables}")
        console.print(f"  Issues: {len(result.issues)}")

        if result.has_issues:
            console.print(f"    - Unknown variables: {result.unknown_variables_count}")
            console.print(f"    - Wrong module: {result.wrong_module_count}")
            console.print(f"    - Missing variables: {result.missing_variables_count}")

            # Create table for issues
            table = Table(title=f"Issues in {result.module_name}", show_header=True, header_style="bold magenta")
            table.add_column("Line", style="dim", width=6)
            table.add_column("Variable", style="cyan")
            table.add_column("Issue Type", style="yellow")
            table.add_column("Message", style="white")

            for issue in result.issues:
                line_str = str(issue.line_number) if issue.line_number else "N/A"
                table.add_row(
                    line_str,
                    issue.variable_name,
                    issue.issue_type,
                    issue.message,
                )

            console.print(table)
        else:
            console.print("  [bold green]✓ No issues found[/bold green]")

if __name__ == '__main__':
    settings_folder = Path(__file__).parent.parent.parent.parent / "tests/fixtures/django/config/settings"
    vetted_file = Path(__file__).parent / "vetted_variables.json"
    if settings_folder.exists() and vetted_file.exists():
        results = validate_settings_directory(settings_folder, vetted_file)
        print_validation_report(results)
    else:
        print(f"Settings folder or vetted variables file not found.")
        print(f"Settings folder: {settings_folder} exists: {settings_folder.exists()}")
        print(f"Vetted variables file: {vetted_file} exists: {vetted_file.exists()}")