#!/usr/bin/env python3
"""Build deterministic, page-bounded SONATA BIS scientific PDFs from Markdown.

The source files use ``<!-- PAGE_BREAK -->`` as an explicit layout contract.
The builder verifies that no section spills onto an extra page.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "docs" / "grant"
DEFAULT_OUTPUT_DIR = ROOT / "output" / "pdf"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "GRANT_PDF_VALIDATION.json"
PAGE_MARKER = "<!-- PAGE_BREAK -->"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
BUILD_DATE = "2026-08-17"

NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#3E75A6")
GRAY = colors.HexColor("#5B6573")
LIGHT = colors.HexColor("#E8EEF4")


@dataclass(frozen=True)
class DocumentSpec:
    source: str
    output: str
    short_header: str
    expected_pages: int
    body_size: float
    leading: float


SPECS = (
    DocumentSpec(
        source="SONATA_BIS16_SHORT_DESCRIPTION_EN.md",
        output="SONATA_BIS16_SHORT_DESCRIPTION_EN_DRAFT.pdf",
        short_header="TRPP - short project description",
        expected_pages=6,
        body_size=8.8,
        leading=10.65,
    ),
    DocumentSpec(
        source="SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.md",
        output="SONATA_BIS16_DETAILED_DESCRIPTION_EN_DRAFT.pdf",
        short_header="TRPP - detailed project description",
        expected_pages=15,
        body_size=8.7,
        leading=10.55,
    ),
    DocumentSpec(
        source="SONATA_BIS16_POPULAR_SUMMARY_PL.md",
        output="SONATA_BIS16_POPULAR_SUMMARY_PL.pdf",
        short_header="TRPP - streszczenie popularnonaukowe",
        expected_pages=1,
        body_size=10.2,
        leading=13.4,
    ),
    DocumentSpec(
        source="SONATA_BIS16_POPULAR_SUMMARY_EN.md",
        output="SONATA_BIS16_POPULAR_SUMMARY_EN.pdf",
        short_header="TRPP - popular-science summary",
        expected_pages=1,
        body_size=10.2,
        leading=13.4,
    ),
)


def _register_fonts() -> None:
    fonts = {
        "DejaVuSans": "DejaVuSans.ttf",
        "DejaVuSans-Bold": "DejaVuSans-Bold.ttf",
        "DejaVuSansMono": "DejaVuSansMono.ttf",
    }
    for name, filename in fonts.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, FONT_DIR / filename))


class InvariantCanvas(canvas.Canvas):
    """ReportLab canvas with deterministic timestamps and document identifiers."""

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["invariant"] = 1
        super().__init__(*args, **kwargs)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inline_markup(value: str) -> str:
    """Convert the small Markdown subset used by the grant sources."""

    escaped = html.escape(value, quote=True)
    escaped = re.sub(
        r"&lt;(https?://[^<]+?)&gt;",
        lambda match: (
            '<link href="{}" color="#315F8C" underline="1">{}</link>'.format(
                match.group(1), match.group(1)
            )
        ),
        escaped,
    )
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda match: (
            '<link href="{}" color="#315F8C" underline="1">{}</link>'.format(
                match.group(2), match.group(1)
            )
        ),
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", escaped)
    escaped = re.sub(
        r"`([^`]+)`", r'<font name="DejaVuSansMono" size="8">\1</font>', escaped
    )
    return escaped


def _styles(spec: DocumentSpec) -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "GrantTitle",
            fontName="DejaVuSans-Bold",
            fontSize=15.5,
            leading=18.5,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=5 * mm,
        ),
        "h2": ParagraphStyle(
            "GrantH2",
            fontName="DejaVuSans-Bold",
            fontSize=11.2,
            leading=13.4,
            textColor=NAVY,
            spaceBefore=2.0 * mm,
            spaceAfter=1.5 * mm,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "GrantH3",
            fontName="DejaVuSans-Bold",
            fontSize=9.35,
            leading=11.2,
            textColor=BLUE,
            spaceBefore=1.3 * mm,
            spaceAfter=0.8 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "GrantBody",
            fontName="DejaVuSans",
            fontSize=spec.body_size,
            leading=spec.leading,
            textColor=colors.HexColor("#20242A"),
            alignment=TA_JUSTIFY,
            spaceAfter=1.45 * mm,
            splitLongWords=True,
        ),
        "lead": ParagraphStyle(
            "GrantLead",
            fontName="DejaVuSans",
            fontSize=spec.body_size,
            leading=spec.leading,
            textColor=GRAY,
            alignment=TA_LEFT,
            spaceAfter=2.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "GrantBullet",
            fontName="DejaVuSans",
            fontSize=spec.body_size,
            leading=spec.leading,
            textColor=colors.HexColor("#20242A"),
            leftIndent=4.5 * mm,
            firstLineIndent=-3.3 * mm,
            spaceAfter=0.75 * mm,
        ),
        "reference": ParagraphStyle(
            "GrantReference",
            fontName="DejaVuSans",
            fontSize=min(spec.body_size, 8.35),
            leading=min(spec.leading, 10.0),
            textColor=colors.HexColor("#20242A"),
            leftIndent=4 * mm,
            firstLineIndent=-4 * mm,
            spaceAfter=0.9 * mm,
            splitLongWords=True,
        ),
    }


def _blocks(markdown_page: str) -> Iterable[tuple[str, str]]:
    pending: list[str] = []
    pending_kind = "paragraph"

    def flush() -> Iterable[tuple[str, str]]:
        nonlocal pending_kind
        if pending:
            value = " ".join(part.strip() for part in pending).strip()
            pending.clear()
            if value:
                yield (pending_kind, value)
        pending_kind = "paragraph"

    for raw in markdown_page.splitlines():
        line = raw.strip()
        if not line:
            yield from flush()
            continue
        if line.startswith("### "):
            yield from flush()
            yield ("h3", line[4:])
        elif line.startswith("## "):
            yield from flush()
            yield ("h2", line[3:])
        elif line.startswith("# "):
            yield from flush()
            yield ("title", line[2:])
        elif re.match(r"^[-*] ", line):
            yield from flush()
            pending_kind = "bullet"
            pending.append(line[2:])
        elif re.match(r"^\d+[.)] ", line):
            yield from flush()
            match = re.match(r"^(\d+[.)])\s+(.*)$", line)
            assert match is not None
            pending_kind = "number"
            pending.append(f"{match.group(1)} {match.group(2)}")
        else:
            pending.append(line)
    yield from flush()


def _story(markdown: str, spec: DocumentSpec) -> list[object]:
    styles = _styles(spec)
    pages = markdown.split(PAGE_MARKER)
    story: list[object] = []
    references_started = False

    for page_index, page in enumerate(pages):
        for kind, value in _blocks(page):
            if kind == "h2" and value.startswith("12. References"):
                references_started = True
            if kind == "h2" and value.startswith("6. References"):
                references_started = True
            if kind == "title":
                style = styles["title"]
            elif kind == "h2":
                style = styles["h2"]
            elif kind == "h3":
                style = styles["h3"]
            elif kind in {"bullet", "number"} or references_started:
                style = styles["reference"] if references_started else styles["bullet"]
                prefix = "" if kind == "number" or references_started else "• "
                value = prefix + value
            else:
                style = styles["lead"] if value.startswith("**") and page_index == 0 else styles["body"]
            story.append(Paragraph(_inline_markup(value), style))
        if page_index + 1 < len(pages):
            story.append(PageBreak())
    return story


def _header_footer(header: str):  # type: ignore[no-untyped-def]
    def draw(pdf: canvas.Canvas, doc: SimpleDocTemplate) -> None:
        pdf.saveState()
        width, height = A4
        pdf.setStrokeColor(LIGHT)
        pdf.setLineWidth(0.6)
        pdf.line(18 * mm, height - 11.7 * mm, width - 18 * mm, height - 11.7 * mm)
        pdf.setFont("DejaVuSans", 7.2)
        pdf.setFillColor(GRAY)
        pdf.drawString(18 * mm, height - 9.4 * mm, header)
        pdf.drawRightString(width - 18 * mm, height - 9.4 * mm, "SONATA BIS 16 | scientific draft")
        pdf.line(18 * mm, 10.2 * mm, width - 18 * mm, 10.2 * mm)
        pdf.drawString(18 * mm, 7.2 * mm, "TRPP | source/target boundary preserved")
        pdf.drawRightString(width - 18 * mm, 7.2 * mm, f"Page {doc.page}")
        pdf.restoreState()

    return draw


def build_pdf(spec: DocumentSpec, output_dir: Path) -> dict[str, object]:
    _register_fonts()
    source_path = SOURCE_DIR / spec.source
    output_path = output_dir / spec.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = source_path.read_text(encoding="utf-8")
    expected_from_source = markdown.count(PAGE_MARKER) + 1
    if expected_from_source != spec.expected_pages:
        raise ValueError(
            f"{spec.source}: layout contract has {expected_from_source} pages, "
            f"expected {spec.expected_pages}"
        )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15.5 * mm,
        bottomMargin=14 * mm,
        title=spec.short_header,
        author="TRPP project team",
        subject="SONATA BIS 16 scientific application draft",
        creator="deterministic ReportLab builder",
        pageCompression=1,
    )
    decoration = _header_footer(spec.short_header)
    doc.build(
        _story(markdown, spec),
        onFirstPage=decoration,
        onLaterPages=decoration,
        canvasmaker=InvariantCanvas,
    )

    reader = PdfReader(output_path)
    actual_pages = len(reader.pages)
    if actual_pages != spec.expected_pages:
        raise ValueError(
            f"{spec.output}: content overflow produced {actual_pages} pages; "
            f"layout contract requires {spec.expected_pages}"
        )
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    if PAGE_MARKER in extracted:
        raise ValueError(f"{spec.output}: raw layout marker leaked into PDF")

    return {
        "source": str(source_path.relative_to(ROOT)),
        "source_sha256": _sha256(source_path),
        "output": str(output_path.relative_to(ROOT))
        if output_path.is_relative_to(ROOT)
        else str(output_path),
        "pdf_sha256": _sha256(output_path),
        "pages": actual_pages,
        "bytes": output_path.stat().st_size,
    }


def generate_all(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, object]:
    records = [build_pdf(spec, output_dir) for spec in SPECS]
    return {
        "schema": "GrantPdfValidation/v1",
        "build_date": BUILD_DATE,
        "deterministic_canvas": True,
        "document_count": len(records),
        "documents": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--evidence-path",
        type=Path,
        default=EVIDENCE_PATH,
        help="Use an empty value only through the Python API; CLI always writes evidence.",
    )
    args = parser.parse_args()
    result = generate_all(args.output_dir.resolve())
    args.evidence_path.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
