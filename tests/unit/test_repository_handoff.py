from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "scripts/12_build_handoff_package.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("handoff_builder", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_readme_installs_complete_acceptance_dependencies() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "-r requirements.lock" in readme
    assert "-r requirements-grant.lock" in readme
    assert "docs/GITHUB_SERVER_GUIDE_PL.md" in readme


def test_server_guide_freezes_scientific_status_and_reference_commits() -> None:
    guide = (ROOT / "docs/GITHUB_SERVER_GUIDE_PL.md").read_text(encoding="utf-8")
    required = (
        "Gate B: **GO**",
        "Gate C: **STOP**",
        "direct regions: **NOT TESTED**",
        "anchors: **NOT TESTED**",
        "dc97680a1e944e74924b5e7b151e0c27d5655f22",
        "2dee739f6ee5e001ef1be76df2eb753ca389adb3",
        "58f3cf8f52001f18af547301289304ee74f8988d1c761c6e9fb3c8208dffe0da",
    )
    assert all(value in guide for value in required)
    assert "Gate C: **GO**" not in guide
    assert "direct regions: **TESTED**" not in guide
    assert "anchors: **TESTED**" not in guide


def test_server_reproduction_keeps_prelabel_before_evaluation() -> None:
    guide = (ROOT / "docs/GITHUB_SERVER_GUIDE_PL.md").read_text(encoding="utf-8")
    for script in (
        "scripts/05_run_full630.py",
        "scripts/06_run_real_lung.py",
        "scripts/07_run_real_within.py",
    ):
        occurrences = [match.start() for match in re.finditer(re.escape(script), guide)]
        assert len(occurrences) == 2
        assert "--phase prelabel" in guide[occurrences[0] : occurrences[1]]
        assert "--phase evaluate" in guide[occurrences[1] : occurrences[1] + 200]


def test_deterministic_zip_ignores_source_mtime(tmp_path: Path) -> None:
    builder = load_builder()
    source = tmp_path / "example.txt"
    source.write_text("stable\n", encoding="utf-8")
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    builder.deterministic_zip(first, [(source, "root/example.txt")], root_entry="root")
    source.touch()
    builder.deterministic_zip(second, [(source, "root/example.txt")], root_entry="root")
    assert file_sha(first) == file_sha(second)


def test_release_builder_forces_single_thread_git_pack() -> None:
    builder_source = BUILDER_PATH.read_text(encoding="utf-8")
    assert '"pack.threads=1"' in builder_source


def test_manifest_names_frozen_results_and_local_only_config() -> None:
    manifest = (ROOT / "docs/FILES_AND_ARCHIVES_MANIFEST_PL.md").read_text(
        encoding="utf-8"
    )
    assert "omics-representation-audit-pilot-results-9adae88.tar.gz" in manifest
    assert "configs/datasets.local.yml" in manifest
    assert "Lokalnie trzeba utworzyć, ale nie commitować" in manifest
