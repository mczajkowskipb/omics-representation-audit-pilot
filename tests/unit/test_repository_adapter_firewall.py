from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_fit_manifests_are_physically_label_free() -> None:
    for name in ("feasibility_datasets.json", "air_datasets.json"):
        value = json.loads((ROOT / "data" / "manifests" / name).read_text())
        assert value["label_free"] is True
        serialized = json.dumps(value).lower()
        assert "y_path" not in serialized
        assert "class_label" not in serialized
        assert "positive_label" not in serialized


def test_data_adapter_modules_cannot_import_evaluation_namespace() -> None:
    adapter_root = ROOT / "src" / "rep_audit" / "data" / "adapters"
    for path in adapter_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(name.startswith("rep_audit.evaluation") for name in imported)
