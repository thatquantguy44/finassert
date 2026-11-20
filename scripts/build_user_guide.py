"""Build the complete searchable user guide and its verified download identity.

Build-only dependencies: reportlab==4.4.9 and Markdown==3.11.
Use --update-reference after catalog/template changes. No PDF library is imported
by the core package, add-in builder or documentation download server.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import textwrap
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from user_guide import (  # noqa: E402
    ASSETS,
    PDF_NAME,
    PDF_PATH,
    SOURCE,
    catalog_document,
    catalog_sha256,
)

START = "<!-- finassert-generated-reference:start -->"
END = "<!-- finassert-generated-reference:end -->"
DOCS_URL = "https://github.com/thatquantguy44/finassert/blob/main/docs/"


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def reference_markdown() -> str:
    """Render every registered rule/parameter and starter template from its catalog."""
    catalog = catalog_document()
    lines = [
        "## Appendix A. Complete built-in rule reference",
        "",
        f"This reference covers all {len(catalog['rules'])} registered built-in policy factories.",
        "Required means the policy must supply the parameter. None means an optional",
        "setting is unused by default. Defaults below are the catalog's declared values;",
        "review the applicability and each field's units before changing them.",
        "",
    ]
    for index, rule in enumerate(catalog["rules"], 1):
        lines.extend(
            [
                f"### A{index}. {rule['name']}",
                "",
                f"**{rule['title']}**. Stable rule ID: `{rule['rule_id']}`.",
                "",
                rule["summary"],
                "",
                f"**Why use it:** {rule['rationale']}",
                "",
                f"**Do not use when:** {rule['inappropriate_when']}",
                "",
                "| Parameter | Required / default | Meaning and allowed values |",
                "| --- | --- | --- |",
            ]
        )
        for parameter in rule["parameters"]:
            default = (
                "Required"
                if parameter["required"]
                else "None"
                if parameter["default"] is None
                else parameter["default"]
            )
            description = f"{parameter['description']} Type: {parameter['kind']}."
            if parameter["choices"]:
                description += " Choices: " + ", ".join(parameter["choices"]) + "."
            if parameter["minimum"] is not None:
                description += f" Minimum: {parameter['minimum']}."
            if parameter["kind"] == "tolerance" and not parameter["allow_relative"]:
                description += " Absolute allowance only; relative must be zero."
            if parameter["kind"] == "number":
                description += (
                    " Negative values allowed."
                    if parameter["allow_negative"]
                    else " Nonnegative values."
                )
            lines.append(f"| `{parameter['name']}` | {_cell(default)} | {_cell(description)} |")
        lines.append("")
    lines.extend(
        [
            "## Appendix B. Complete starter-template reference",
            "",
            f"All {len(catalog['templates'])} current templates are ordinary policies.",
            "Use finassert init to emit the full YAML. Replace sample schema/scope/date",
            "settings, confirm proposed matches, and review every assumption. Templates",
            "do not supply a mandate limit or establish required-control completeness.",
            "",
        ]
    )
    for index, template in enumerate(catalog["templates"], 1):
        lines.extend(
            [
                f"### B{index}. {template['name']}",
                "",
                f"**{template['title']}**. {template['summary']}",
                "",
                f"Create with `finassert init --template {template['name']} --output policy.yml`.",
                "",
                "Included checks: "
                + ", ".join(f"`{r['rule']}`" for r in template["document"]["rules"])
                + ".",
                "",
                "**Adapt before use:**",
                "",
                *("- " + note for note in template["adapt"]),
                "",
                "**Assumptions:**",
                "",
                *("- " + note for note in template["document"]["assumptions"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def resolved_source(text: str, *, update_reference: bool = False) -> str:
    """Validate or update exactly one generated reference block."""
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("Guide must contain one generated-reference block")
    before, remainder = text.split(START)
    _, after = remainder.split(END)
    resolved = before + START + "\n\n" + reference_markdown() + "\n" + END + after
    if not update_reference and resolved != text:
        raise ValueError("Guide catalog reference is stale; rerun with --update-reference")
    return resolved


def _plain(text: str) -> str:
    return text.translate(
        str.maketrans({"\u2011": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-"})
    )


def build_pdf(text: str, target: Path, version: str, revision: str) -> int:
    """Render a linked, searchable PDF with tables, code, bookmarks and contents."""
    try:
        import markdown
        import reportlab
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.platypus import (
            BaseDocTemplate,
            CondPageBreak,
            Frame,
            ListFlowable,
            ListItem,
            LongTable,
            PageBreak,
            PageTemplate,
            Paragraph,
            Preformatted,
            Spacer,
            TableStyle,
        )
        from reportlab.platypus.tableofcontents import TableOfContents
    except ImportError as exc:
        raise ValueError("Build guide with reportlab==4.4.9 and Markdown==3.11") from exc

    fonts = Path(reportlab.__file__).parent / "fonts"
    for name, filename in (
        ("GuideSans", "Vera.ttf"),
        ("GuideSans-Bold", "VeraBd.ttf"),
        ("GuideSans-Italic", "VeraIt.ttf"),
        ("GuideSans-BoldItalic", "VeraBI.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily(
        "GuideSans",
        normal="GuideSans",
        bold="GuideSans-Bold",
        italic="GuideSans-Italic",
        boldItalic="GuideSans-BoldItalic",
    )
    navy = colors.HexColor("#14283F")
    teal = colors.HexColor("#087F8C")
    muted = colors.HexColor("#526479")
    pale = colors.HexColor("#F0F5F9")
    width, height = letter
    margin = 55
    available = width - 2 * margin
    body = ParagraphStyle(
        "GuideBody",
        fontName="GuideSans",
        fontSize=9.2,
        leading=12.5,
        textColor=navy,
        spaceAfter=6,
        splitLongWords=True,
        allowWidows=0,
        allowOrphans=0,
    )
    h2 = ParagraphStyle(
        "GuideChapter",
        parent=body,
        fontName="GuideSans-Bold",
        fontSize=20,
        leading=25,
        spaceAfter=15,
        keepWithNext=True,
    )
    h3 = ParagraphStyle(
        "GuideSection",
        parent=body,
        fontName="GuideSans-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=7,
        keepWithNext=True,
    )
    cell = ParagraphStyle(
        "GuideCell",
        parent=body,
        fontSize=7.9,
        leading=11.3,
        spaceAfter=0,
        allowWidows=1,
        allowOrphans=1,
    )
    cell_header = ParagraphStyle(
        "GuideCellHeader",
        parent=cell,
        fontName="GuideSans-Bold",
        textColor=colors.white,
    )
    code = ParagraphStyle(
        "GuideCode",
        fontName="Courier",
        fontSize=7.5,
        leading=10.5,
        textColor=navy,
        backColor=pale,
        borderPadding=9,
        spaceBefore=5,
        spaceAfter=14,
    )
    bullet = ParagraphStyle("GuideBullet", parent=body, spaceAfter=4)
    html = markdown.markdown(
        _plain(text),
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.toc",
        ],
        output_format="xhtml",
    )
    document = ET.fromstring("<guide>" + html + "</guide>")

    def inline(node: ET.Element) -> str:
        result = escape(node.text or "")
        for child in node:
            content = inline(child)
            if child.tag in {"strong", "b"}:
                result += f"<b>{content}</b>"
            elif child.tag in {"em", "i"}:
                result += f"<i>{content}</i>"
            elif child.tag == "code":
                result += f'<font name="Courier">{content}</font>'
            elif child.tag == "a":
                href = child.get("href", "")
                if href and not href.startswith("#"):
                    href = urljoin(DOCS_URL, href)
                result += f'<a href="{escape(href, quote=True)}" color="#087F8C">{content}</a>'
            elif child.tag == "br":
                result += "<br/>"
            else:
                result += content
            result += escape(child.tail or "")
        return result

    class GuideDocument(BaseDocTemplate):
        """Add stable named destinations and a clickable chapter contents page."""

        chapter = ""

        def afterFlowable(self, flowable: Any) -> None:
            """Record a heading's page after layout for contents and bookmarks."""
            heading = getattr(flowable, "guide_heading", None)
            if heading is not None:
                level, title, key = heading
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(title, key, level=level, closed=True)
                if level == 0:
                    self.chapter = title
                    self.notify("TOCEntry", (0, title, self.page, key))

    def chrome(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        if doc.page == 1:
            canvas.setFillColor(navy)
            canvas.rect(0, 0, width, height, fill=1, stroke=0)
            canvas.setFillColor(teal)
            canvas.rect(margin, height - 180, 6, 84, fill=1, stroke=0)
            canvas.setFillColor(colors.HexColor("#BDD4E5"))
        else:
            canvas.setFillColor(muted)
            canvas.setFont("GuideSans-Bold", 7)
            canvas.drawString(margin, height - 29, "FINASSERT  /  USER GUIDE")
            canvas.setStrokeColor(colors.HexColor("#DCE5ED"))
            canvas.line(margin, height - 37, width - margin, height - 37)
            canvas.setFont("GuideSans", 6.7)
            canvas.drawRightString(width - margin, height - 29, f"Product version {version}")
            canvas.setFillColor(muted)
        canvas.setFont("GuideSans", 7)
        canvas.drawString(margin, 28, f"finassert {version}  |  Guide revision {revision}")
        canvas.drawRightString(width - margin, 28, str(doc.page))
        canvas.restoreState()

    doc = GuideDocument(
        str(target),
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=59,
        bottomMargin=48,
        title="finassert User Guide",
        author="finassert",
        subject="Excel, browser, Python, CLI, policies, rules and documentation download API",
    )
    frame = Frame(margin, 48, available, height - 107, leftPadding=0, rightPadding=0)
    doc.addPageTemplates(PageTemplate(id="Guide", frames=[frame], onPage=chrome))
    cover = ParagraphStyle(
        "GuideCover",
        parent=body,
        fontSize=36,
        leading=44,
        fontName="GuideSans-Bold",
        textColor=colors.white,
        spaceAfter=15,
    )
    cover_body = ParagraphStyle(
        "GuideCoverBody",
        parent=body,
        fontSize=13,
        leading=21,
        textColor=colors.HexColor("#E0EBF3"),
        spaceAfter=18,
    )
    story: list[Any] = [
        Spacer(1, 40),
        Paragraph("finassert", cover),
        Paragraph("User Guide", cover),
        Spacer(1, 20),
        Paragraph(
            "Financial data validation,<br/>from workbook checks to reproducible evidence.",
            cover_body,
        ),
        Spacer(1, 35),
        Paragraph("EXCEL  /  BROWSER  /  PYTHON  /  CLI", cover_body),
        Paragraph(f"Product version {version}<br/>Guide revision {revision}", cover_body),
        Spacer(1, 35),
        Paragraph(
            "Set the source. Review the policy.<br/>Find the break. Keep the evidence.", cover_body
        ),
        PageBreak(),
        Paragraph("Contents", h2),
        Paragraph(
            "Choose a workflow, then use the complete rule and template appendices for settings.",
            body,
        ),
    ]
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "GuideContents",
            fontName="GuideSans",
            fontSize=9.3,
            leading=18,
            leftIndent=0,
            firstLineIndent=0,
            rightIndent=20,
            alignment=TA_LEFT,
        )
    ]
    story.extend([toc, Spacer(1, 12)])

    def nodes(elements: list[ET.Element]) -> list[Any]:
        out: list[Any] = []
        for index, node in enumerate(elements):
            tag = node.tag
            if tag == "h1":
                continue
            if tag in {"h2", "h3", "h4"}:
                title = "".join(node.itertext())
                if tag == "h2":
                    if title.startswith(("1. ", "Appendix ")):
                        out.append(PageBreak())
                    else:
                        out.extend([CondPageBreak(210), Spacer(1, 16)])
                elif title.startswith(("A", "B")) and re.match(r"[AB]\d+\.", title):
                    out.append(CondPageBreak(160))
                paragraph = Paragraph(inline(node), h2 if tag == "h2" else h3)
                paragraph.guide_heading = (0 if tag == "h2" else 1, title, node.get("id"))
                out.append(paragraph)
            elif tag == "p":
                paragraph = Paragraph(inline(node), body)
                if (
                    index
                    and elements[index - 1].tag == "h3"
                    and re.match(r"[AB]\d+\.", "".join(elements[index - 1].itertext()))
                ):
                    paragraph.keepWithNext = True
                out.append(paragraph)
            elif tag in {"ul", "ol"}:
                items = []
                for item in node:
                    nested = list(item)
                    if nested and nested[0].tag == "p":
                        content = nodes(nested)
                    else:
                        content = [Paragraph(inline(item), bullet)]
                    items.append(ListItem(content, leftIndent=0))
                out.extend(
                    [
                        ListFlowable(
                            items,
                            bulletType="1" if tag == "ol" else "bullet",
                            start="1" if tag == "ol" else "-",
                            leftIndent=15,
                            bulletFontName="GuideSans",
                            bulletFontSize=9,
                            spaceAfter=9,
                        ),
                    ]
                )
            elif tag == "pre":
                value = "".join(node.itertext()).rstrip()
                wrapped = "\n".join(
                    "\n".join(
                        textwrap.wrap(
                            line,
                            width=100,
                            replace_whitespace=False,
                            drop_whitespace=False,
                            break_on_hyphens=False,
                        )
                    )
                    if line
                    else ""
                    for line in value.splitlines()
                )
                out.append(Preformatted(wrapped, code))
            elif tag == "table":
                rows = []
                for row in node.iter("tr"):
                    rows.append(
                        [
                            Paragraph(inline(item), cell_header if item.tag == "th" else cell)
                            for item in row
                        ]
                    )
                count = len(rows[0])
                if count == 2:
                    ratios = [0.35, 0.65]
                elif count == 3:
                    parameter = "Parameter" in "".join(node.itertext())[:80]
                    ratios = [0.25, 0.18, 0.57] if parameter else [0.22, 0.39, 0.39]
                elif count == 6:
                    ratios = [0.15, 0.12, 0.13, 0.22, 0.12, 0.26]
                else:
                    ratios = [1 / count] * count
                table = LongTable(
                    rows,
                    colWidths=[available * r for r in ratios],
                    repeatRows=1,
                    hAlign="LEFT",
                    spaceAfter=13,
                )
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), navy),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 7),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ("LINEBELOW", (0, 0), (-1, 0), 0.7, teal),
                        ]
                    )
                )
                out.append(table)
            elif tag == "blockquote":
                out.extend(nodes(list(node)))
        return out

    # The cover already owns the title/version introduction; start the body at chapter 1.
    start = next(i for i, node in enumerate(document) if node.tag == "h2")
    story.extend(nodes(list(document)[start:]))

    def canvas_maker(*args: Any, **kwargs: Any) -> Any:
        kwargs["invariant"] = 1
        kwargs["pageCompression"] = 1
        return Canvas(*args, **kwargs)

    previous_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if previous_epoch is None:
        stamp = datetime.strptime(revision, "%Y-%m-%d").replace(tzinfo=UTC)
        os.environ["SOURCE_DATE_EPOCH"] = str(int(stamp.timestamp()))
    try:
        doc.multiBuild(story, canvasmaker=canvas_maker)
    finally:
        if previous_epoch is None:
            del os.environ["SOURCE_DATE_EPOCH"]
    return doc.page


def main(argv: list[str] | None = None) -> int:
    """Build source-current PDF/metadata without changing runtime dependencies."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=ASSETS / PDF_NAME)
    parser.add_argument("--update-reference", action="store_true")
    args = parser.parse_args(argv)
    from finassert import __version__

    try:
        original = args.source.read_text(encoding="utf-8")
        text = resolved_source(original, update_reference=args.update_reference)
        revision = re.search(r"<!-- finassert-guide-revision: (\d{4}-\d{2}-\d{2}) -->", text)
        if revision is None:
            raise ValueError("Guide requires an explicit revision date")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="guide-", dir=args.output.parent) as temp:
            pdf_path = Path(temp) / PDF_NAME
            pages = build_pdf(text, pdf_path, __version__, revision[1])
            pdf = pdf_path.read_bytes()
            metadata = {
                "schema_version": 1,
                "title": "finassert User Guide",
                "tool": {"name": "finassert", "version": __version__},
                "revision": revision[1],
                "filename": PDF_NAME,
                "content_type": "application/pdf",
                "download_url": PDF_PATH,
                "bytes": len(pdf),
                "pages": pages,
                "sha256": hashlib.sha256(pdf).hexdigest(),
                "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "catalog_sha256": catalog_sha256(),
                "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "rule_count": len(catalog_document()["rules"]),
                "template_count": len(catalog_document()["templates"]),
            }
            sidecar = Path(temp) / "metadata.json"
            sidecar.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            if text != original:
                args.source.write_text(text, encoding="utf-8")
            pdf_path.replace(args.output)
            sidecar.replace(args.output.with_suffix(".json"))
        print(f"Built {pages}-page user guide: {args.output} ({len(pdf):,} bytes)")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"build_user_guide: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
