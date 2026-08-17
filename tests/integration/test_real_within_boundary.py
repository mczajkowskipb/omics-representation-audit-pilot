from __future__ import annotations

import ast
import builtins
import json
from pathlib import Path

import pytest
import yaml

from rep_audit.experiments.real_within import run_within_evaluation


ROOT = Path(__file__).parents[2]


def test_real_within_has_no_module_scope_evaluation_import() -> None:
    path = ROOT / "src/rep_audit/experiments/real_within.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations = []
    for node in tree.body:
        imported = []
        if isinstance(node, ast.Import):
            imported = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported = [node.module]
        if any(name.startswith("rep_audit.evaluation") for name in imported):
            violations.append(name)
    assert violations == []


def test_evaluation_loader_is_not_imported_before_global_marker_validates(
    tmp_path, monkeypatch
) -> None:
    config = yaml.safe_load((ROOT / "configs/real_within.yml").read_text())
    (tmp_path / "WITHIN_PRELABEL_COMPLETE.json").write_text(
        json.dumps({"schema": "invalid"}), encoding="utf-8"
    )
    real_import = builtins.__import__
    imported_evaluation_loader = False

    def guarded_import(name, *args, **kwargs):
        nonlocal imported_evaluation_loader
        if name == "rep_audit.evaluation.repository_labels":
            imported_evaluation_loader = True
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    with pytest.raises(ValueError, match="incomplete prelabel boundary"):
        run_within_evaluation(
            config,
            dataset_config={},
            output_root=tmp_path,
        )
    assert imported_evaluation_loader is False
