from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE_DIRECTORIES = (
    "data",
    "preprocessing",
    "representations",
    "distances",
    "clustering",
    "audit",
    "io",
)


def test_core_modules_do_not_import_evaluation_namespace() -> None:
    violations: list[str] = []
    package = ROOT / "src" / "rep_audit"
    for directory in CORE_DIRECTORIES:
        for path in (package / directory).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                imported: list[str] = []
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported = [node.module]
                if any(name.startswith("rep_audit.evaluation") for name in imported):
                    violations.append(str(path.relative_to(ROOT)))
    assert violations == []


def test_top_level_package_does_not_reexport_labels() -> None:
    tree = ast.parse(
        (ROOT / "src" / "rep_audit" / "__init__.py").read_text(encoding="utf-8")
    )
    rendered = ast.dump(tree)
    assert "EvaluationLabels" not in rendered
