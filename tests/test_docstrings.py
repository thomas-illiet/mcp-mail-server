from __future__ import annotations

import ast
from pathlib import Path


def python_files() -> list[Path]:
    """Return all Python files that belong to the project."""
    source_files = Path("src/email_mcp").rglob("*.py")
    test_files = Path("tests").rglob("*.py")
    return sorted([*source_files, *test_files])


def test_all_source_functions_have_docstrings() -> None:
    """Ensure every project function and method has an explicit docstring."""
    missing: list[str] = []
    for source_file in python_files():
        tree = ast.parse(source_file.read_text(), filename=str(source_file))
        missing.extend(
            f"{source_file}:{node.lineno}:{node.name}"
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and ast.get_docstring(node) is None
        )

    assert missing == []
