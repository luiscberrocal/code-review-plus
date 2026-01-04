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
            keywords = {kw.arg: kw.value for kw in node.keywords}

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
                if isinstance(val, (ast.Constant, ast.Str)):
                    self.errors.append(
                        f"[{model_name}.{field_name}] 'help_text' should be wrapped in gettext_lazy (_) for translations."
                    )
            else:
                self.errors.append(
                    f"[{model_name}.{field_name}] Missing 'help_text'. It is recommended for better Admin UX."
                )

def lint_django_models(file_path):
    with open(file_path, "r") as source:
        tree = ast.parse(source.read())

    visitor = DjangoModelVisitor()
    visitor.visit(tree)
    return visitor.errors

# Example usage:
# report = lint_django_models('myapp/models.py')
# for error in report:
#     print(error)

if __name__ == '__main__':
    model_file = Path(__file__).parent.parent.parent.parent / "tests/fixtures/django/models.py"
    if model_file.exists():
        report = lint_django_models(model_file)
        for error in report:
            print(error)

    else:
        print(f"Model file not found: {model_file}")