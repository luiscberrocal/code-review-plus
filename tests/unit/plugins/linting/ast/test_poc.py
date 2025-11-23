import json
from ast import parse

from ast2json import ast2json


def test_ast_parsing(fixtures_folder):
    file = fixtures_folder / "condo_models.py"
    with open(file) as f:
        content = f.read()
    tree = parse(content)
    ast_json = ast2json(tree)
    assert isinstance(ast_json, dict)

    json_file = fixtures_folder / "condo_models_ast.json"
    with open(json_file, "w") as f:
        json.dump(ast_json, f, indent=4, default=str)


def test_parse_setting(fixtures_folder):
    folder = fixtures_folder / "settings"
    file = folder / "base.py"
    with open(file) as f:
        content = f.read()
    tree = parse(content)
    ast_json = ast2json(tree)
    assert isinstance(ast_json, dict)

    json_file = folder / "settings_ast.json"
    with open(json_file, "w") as f:
        json.dump(ast_json, f, indent=4, default=str)

    body = ast_json.get("body", [])

    assignments = [node for node in body if node.get("_type") == "Assign"]
    assign_file = folder / "settings_assignments.json"
    with open(assign_file, "w") as f:
        json.dump(assignments, f, indent=4, default=str)

    targets = [node.get("targets") for node in assignments]
    target_file = folder / "settings_targets.json"
    with open(target_file, "w") as f:
        json.dump(targets, f, indent=4, default=str)
