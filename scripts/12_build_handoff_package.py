#!/usr/bin/env python3
"""Build a deterministic all-in-one repository and pilot handoff package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
RESULTS_ARCHIVE_NAME = "omics-representation-audit-pilot-results-9adae88.tar.gz"
RESULTS_ARCHIVE_SHA256 = (
    "58f3cf8f52001f18af547301289304ee74f8988d1c761c6e9fb3c8208dffe0da"
)
PROTOCOL_SHA256 = (
    "5104901b66403ab29bbad24f7fdc48dda10121b1a584740ec47af02790d6a704"
)
ZIP_TIMESTAMP = (2026, 8, 17, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(*args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=text,
    )
    return completed.stdout


def tracked_files(prefix: str) -> tuple[Path, ...]:
    output = str(run_git("ls-files", prefix))
    return tuple(ROOT / line for line in output.splitlines() if line)


def copy_file(source: Path, target: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def deterministic_zip(
    output: Path, entries: Iterable[tuple[Path, str]], *, root_entry: str | None = None
) -> None:
    """Write sorted regular files with stable metadata and byte output."""

    materialized = sorted(
        ((source, archive_name.replace(os.sep, "/")) for source, archive_name in entries),
        key=lambda item: item[1],
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        if root_entry is not None:
            name = root_entry.rstrip("/") + "/"
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.create_system = 3
            info.external_attr = (stat.S_IFDIR | 0o755) << 16
            archive.writestr(info, b"")
        for source, archive_name in materialized:
            if not source.is_file():
                raise FileNotFoundError(source)
            info = zipfile.ZipInfo(archive_name, ZIP_TIMESTAMP)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, source.read_bytes(), compresslevel=9)


def package_files(package_dir: Path, *, include_checksums: bool) -> list[Path]:
    files = sorted(path for path in package_dir.rglob("*") if path.is_file())
    if include_checksums:
        return files
    return [path for path in files if path.name != "CHECKSUMS.sha256"]


def write_contents(package_dir: Path) -> None:
    excluded = {"CHECKSUMS.sha256", "CONTENTS.txt"}
    lines = []
    for path in package_files(package_dir, include_checksums=True):
        relative = path.relative_to(package_dir).as_posix()
        if relative in excluded:
            continue
        lines.append(f"{relative}\t{path.stat().st_size} bytes")
    (package_dir / "CONTENTS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_checksums(package_dir: Path) -> None:
    lines = []
    for path in package_files(package_dir, include_checksums=False):
        relative = path.relative_to(package_dir).as_posix()
        lines.append(f"{sha256(path)}  ./{relative}")
    (package_dir / "CHECKSUMS.sha256").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def ensure_clean_tracked_worktree() -> None:
    status_output = str(run_git("status", "--porcelain", "--untracked-files=no"))
    if status_output.strip():
        raise RuntimeError(
            "tracked worktree is dirty; commit or restore changes before packaging"
        )


def build_package(results_archive: Path, output_dir: Path) -> dict[str, object]:
    ensure_clean_tracked_worktree()
    results_archive = results_archive.resolve()
    output_dir = output_dir.resolve()
    try:
        output_dir.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise ValueError("output directory must be outside the repository")

    if results_archive.name != RESULTS_ARCHIVE_NAME:
        raise ValueError(f"results archive must be named {RESULTS_ARCHIVE_NAME}")
    if sha256(results_archive) != RESULTS_ARCHIVE_SHA256:
        raise ValueError("results archive SHA-256 does not match the frozen artifact")
    if sha256(ROOT / "docs/SONATA_BIS_PILOT_PROTOCOL_v1.md") != PROTOCOL_SHA256:
        raise ValueError("protocol SHA-256 does not match the frozen protocol")

    commit = str(run_git("rev-parse", "HEAD")).strip()
    short_commit = commit[:7]
    package_name = f"SONATA_BIS16_TRPP_ALL_IN_ONE-{short_commit}"
    package_dir = output_dir / package_name
    outer_zip = output_dir / f"{package_name}.zip"
    outer_sha = output_dir / f"{package_name}.zip.sha256"
    for path in (package_dir, outer_zip, outer_sha):
        if path.exists():
            raise FileExistsError(path)

    archives = package_dir / "05_ARCHIVES"
    archives.mkdir(parents=True)
    source_name = f"omics-representation-audit-pilot-{short_commit}.zip"
    bundle_name = f"omics-representation-audit-pilot-history-{short_commit}.bundle"
    evidence_name = f"SONATA_BIS16_EVIDENCE_AND_REPORTS-{short_commit}.zip"
    source_path = archives / source_name
    bundle_path = archives / bundle_name
    evidence_path = archives / evidence_name

    subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "archive",
            "--format=zip",
            f"--prefix=omics-representation-audit-pilot/",
            f"--output={source_path}",
            "HEAD",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "-c",
            "pack.threads=1",
            "bundle",
            "create",
            str(bundle_path),
            "--all",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "archive",
            "--format=zip",
            f"--prefix=SONATA_BIS16_EVIDENCE_AND_REPORTS/",
            f"--output={evidence_path}",
            "HEAD",
            "docs",
            "output/pdf",
        ],
        check=True,
    )
    copy_file(results_archive, archives / RESULTS_ARCHIVE_NAME)

    copy_file(ROOT / "docs/package/ALL_IN_ONE_README_PL.md", package_dir / "README_FIRST.md")
    start_here = package_dir / "01_START_HERE"
    copy_file(ROOT / "docs/grant/README_FIRST_PL.md", start_here / "README_FIRST_PL.md")
    copy_file(
        ROOT / "docs/SONATA_BIS16_COMPLETION_REPORT.md",
        start_here / "SONATA_BIS16_COMPLETION_REPORT.md",
    )
    copy_file(
        ROOT / "docs/REPOSITORY_PUBLICATION_HANDOFF_REPORT.md",
        start_here / "REPOSITORY_PUBLICATION_HANDOFF_REPORT.md",
    )
    copy_file(
        ROOT / "docs/GITHUB_SERVER_GUIDE_PL.md",
        start_here / "GITHUB_SERVER_GUIDE_PL.md",
    )
    copy_file(
        ROOT / "docs/FILES_AND_ARCHIVES_MANIFEST_PL.md",
        start_here / "FILES_AND_ARCHIVES_MANIFEST_PL.md",
    )

    grant_pdf_names = (
        "SONATA_BIS16_SHORT_DESCRIPTION_EN_DRAFT.pdf",
        "SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.pdf",
        "SONATA_BIS16_POPULAR_SUMMARY_PL.pdf",
        "SONATA_BIS16_POPULAR_SUMMARY_EN.pdf",
    )
    for name in grant_pdf_names:
        copy_file(ROOT / "output/pdf" / name, package_dir / "02_GRANT_PDFS" / name)
    copy_file(
        ROOT / "output/pdf/SONATA_BIS_PILOT_CLOSEOUT_REPORT.pdf",
        package_dir / "03_PILOT_REPORT/SONATA_BIS_PILOT_CLOSEOUT_REPORT.pdf",
    )

    for source in tracked_files("docs/grant"):
        relative = source.relative_to(ROOT / "docs/grant")
        copy_file(source, package_dir / "04_GRANT_SOURCES" / relative)
    copy_file(
        ROOT / "docs/SONATA_BIS_PILOT_PROTOCOL_v1.md",
        package_dir / "06_PROTOCOL/SONATA_BIS_PILOT_PROTOCOL_v1.md",
    )

    archive_rows = []
    for name in (source_name, bundle_name, evidence_name, RESULTS_ARCHIVE_NAME):
        path = archives / name
        archive_rows.append((name, path.stat().st_size, sha256(path)))
    release_lines = [
        "# Dokładne pliki bieżącego wydania",
        "",
        f"- pełny commit: `{commit}`;",
        f"- skrócony commit: `{short_commit}`;",
        f"- paczka główna: `{package_name}.zip`;",
        f"- plik sumy paczki głównej: `{package_name}.zip.sha256`.",
        "",
        "## Archiwa wewnętrzne",
        "",
        "| Nazwa | Rozmiar w bajtach | SHA-256 |",
        "| --- | ---: | --- |",
    ]
    release_lines.extend(
        f"| `{name}` | {size} | `{digest}` |"
        for name, size, digest in archive_rows
    )
    release_lines.extend(
        [
            "",
            "Do publikacji pełnej historii na GitHub użyj pliku `.bundle`.",
            "Do przekazania całego projektu innej osobie użyj paczki głównej ZIP.",
            "Ciężkiego archiwum wyników nie commituj do zwykłej historii Git.",
            "",
        ]
    )
    (start_here / "RELEASE_FILES_EXACT_PL.md").write_text(
        "\n".join(release_lines), encoding="utf-8"
    )

    write_contents(package_dir)
    write_checksums(package_dir)
    entries = [
        (path, f"{package_name}/{path.relative_to(package_dir).as_posix()}")
        for path in package_files(package_dir, include_checksums=True)
    ]
    deterministic_zip(outer_zip, entries, root_entry=package_name)
    outer_digest = sha256(outer_zip)
    outer_sha.write_text(f"{outer_digest}  {outer_zip.name}\n", encoding="utf-8")

    return {
        "schema": "RepositoryHandoffPackage/v1",
        "commit": commit,
        "short_commit": short_commit,
        "package_directory": str(package_dir),
        "package_zip": str(outer_zip),
        "package_zip_size_bytes": outer_zip.stat().st_size,
        "package_zip_sha256": outer_digest,
        "package_zip_sha256_file": str(outer_sha),
        "results_archive_sha256": RESULTS_ARCHIVE_SHA256,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = build_package(args.results_archive, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
