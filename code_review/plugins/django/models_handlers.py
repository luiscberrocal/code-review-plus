import ast
from pathlib import Path


class DjangoModelVisitor(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    def visit_ClassDef(self, node):
        # We check if the class looks like a Django Model
        # (Simplified: checks if it inherits from something)
        for base in node.bases:
            # Look for field definitions within the class
            for item in node.body:
                if isinstance(item, ast.Assign):
                    self.check_field(item, node.name)
        self.generic_visit(node)

    def check_field(self, node, model_name):
        # A field is usually an assignment to a Call (e.g., models.CharField(...))
        if isinstance(node.value, ast.Call):
            field_name = node.targets[0].id if isinstance(node.targets[0], ast.Name) else "Unknown"
            keywords = {kw.arg: kw.value for kw in node.value.keywords}

            # 1. Check for db_index=True
            if "db_index" in keywords:
                val = keywords["db_index"]
                if isinstance(val, ast.Constant) and val.value is True:
                    self.errors.append(
                        f"[{model_name}.{field_name}] Use 'indexes' in class Meta instead of 'db_index=True' for better naming control."
                    )

            # 2. Check for help_text translatability
            if "help_text" in keywords:
                val = keywords["help_text"]
                # Check if it's a raw string instead of a function call like _("...")
                if isinstance(val, ast.Constant):
                    self.errors.append(
                        f"[{model_name}.{field_name}] 'help_text' should be wrapped in gettext_lazy (_) for translations."
                    )
            else:
                self.errors.append(
                    f"[{model_name}.{field_name}] Missing 'help_text'. It is recommended for better Admin UX."
                )

class DjangoModelInheritanceVisitor(ast.NodeVisitor):
    """Visitor to check that all Django models inherit from required base classes."""

    def __init__(self, required_bases=None):
        self.errors = []
        self.required_bases = required_bases or ["AuditableModel", "TimeStampedModel"]

    def visit_ClassDef(self, node):
        # Check if this is a Django model by looking for models.Model or other base classes
        if self._is_django_model(node):
            # Get the names of all base classes
            base_names = self._get_base_names(node)

            # Check for missing required bases
            missing_bases = [base for base in self.required_bases if base not in base_names]

            if missing_bases:
                self.errors.append(
                    f"[{node.name}] Missing required base class(es): {', '.join(missing_bases)}"
                )

        self.generic_visit(node)

    def _is_django_model(self, node):
        """Check if a class appears to be a Django model."""
        # Look for inheritance from models.Model or common base classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                # Direct inheritance like: class MyModel(Model):
                if "Model" in base.id:
                    return True
            elif isinstance(base, ast.Attribute):
                # models.Model style: class MyModel(models.Model):
                if base.attr == "Model":
                    return True

        # Also check if it has any base classes at all (could be abstract base)
        # This catches cases where models inherit from custom base classes
        if node.bases:
            # Check if any fields that look like Django fields exist
            for item in node.body:
                if isinstance(item, ast.Assign) and isinstance(item.value, ast.Call):
                    # Check if it's a models.XxxField call
                    call = item.value
                    if isinstance(call.func, ast.Attribute):
                        if hasattr(call.func.value, 'id') and call.func.value.id == 'models':
                            return True

        return False

    def _get_base_names(self, node):
        """Extract the names of all base classes."""
        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                # For models.Model, we get "Model"
                base_names.append(base.attr)
        return base_names


def lint_django_models(file_path):
    with open(file_path, "r") as source:
        tree = ast.parse(source.read())

    visitor = DjangoModelVisitor()
    visitor.visit(tree)
    return visitor.errors


def check_model_inheritance(file_path, required_bases=None):
    """Check that all Django models inherit from required base classes.

    Args:
        file_path: Path to the Python file containing Django models
        required_bases: List of required base class names (default: ["AuditableModel", "TimeStampedModel"])

    Returns:
        List of error messages for models missing required base classes
    """
    with open(file_path, "r") as source:
        tree = ast.parse(source.read())

    visitor = DjangoModelInheritanceVisitor(required_bases)
    visitor.visit(tree)
    return visitor.errors

# Example usage:
# report = lint_django_models('myapp/models.py')
# for error in report:
#     print(error)

if __name__ == '__main__':
    model_file = Path(__file__).parent.parent.parent.parent / "tests/fixtures/django/models.py"
    if model_file.exists():
        print("=" * 80)
        print("FIELD LINTING REPORT")
        print("=" * 80)
        report = lint_django_models(model_file)
        for error in report:
            print(error)

        print("\n" + "=" * 80)
        print("INHERITANCE CHECK REPORT")
        print("=" * 80)
        inheritance_report = check_model_inheritance(model_file)
        for error in inheritance_report:
            print(error)

        if not inheritance_report:
            print("✓ All models inherit from required base classes")
    else:
        print(f"Model file not found: {model_file}")