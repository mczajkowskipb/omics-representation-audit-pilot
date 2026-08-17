from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "11_generate_grant_pdfs.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("grant_pdf_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_grant_sources_have_frozen_page_contracts() -> None:
    builder = _load_builder()
    for item in builder.SPECS:
        source = builder.SOURCE_DIR / item.source
        assert source.is_file()
        assert source.read_text(encoding="utf-8").count(builder.PAGE_MARKER) + 1 == item.expected_pages


def test_grant_pdf_generation_is_byte_deterministic_and_page_bounded(tmp_path: Path) -> None:
    builder = _load_builder()
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_result = builder.generate_all(first)
    second_result = builder.generate_all(second)

    assert first_result["document_count"] == 4
    assert second_result["document_count"] == 4
    for item in builder.SPECS:
        first_pdf = first / item.output
        second_pdf = second / item.output
        assert _sha(first_pdf) == _sha(second_pdf)
        assert len(PdfReader(first_pdf).pages) == item.expected_pages


def test_scientific_pdfs_preserve_pilot_boundaries(tmp_path: Path) -> None:
    builder = _load_builder()
    builder.generate_all(tmp_path)
    for name in (
        "SONATA_BIS16_SHORT_DESCRIPTION_EN_DRAFT.pdf",
        "SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.pdf",
    ):
        reader = PdfReader(tmp_path / name)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        normalised = " ".join(text.split())
        assert "Gate B: GO" in normalised
        assert "Gate C: STOP" in normalised
        assert "direct regions: NOT TESTED" in normalised
        assert "anchors: NOT TESTED" in normalised
        assert "labels were used only after all source-only" in normalised
        assert "&#8226;" not in text
