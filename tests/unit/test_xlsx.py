import io
import zipfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook

import finassert as fa
from finassert._xlsx import column_letter, sheet_names
from finassert.core.exceptions import InvalidDataError
from finassert.loaders import load_input, parse_csv, parse_xlsx
from finassert.policy import parse_policy

MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def workbook_bytes(*sheets: tuple[str, list[list[object]]], **formats: str) -> bytes:
    book = Workbook()
    book.remove(book.active)
    for title, rows in sheets:
        sheet = book.create_sheet(title)
        for row in rows:
            sheet.append(row)
        for reference, number_format in formats.items():
            sheet[reference].number_format = number_format
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def raw_workbook(
    sheet_data: str,
    *,
    shared: list[str] | None = None,
    styles: str | None = None,
    date1904: bool = False,
) -> bytes:
    """Build a minimal .xlsx by hand, for cell forms openpyxl does not write."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            f'<workbook xmlns="{MAIN}" xmlns:r="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships">'
            + ('<workbookPr date1904="1"/>' if date1904 else "")
            + '<sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
            'relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" '
            'Type="worksheet"/></Relationships>',
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet xmlns="{MAIN}"><sheetData>{sheet_data}</sheetData></worksheet>',
        )
        if shared is not None:
            items = "".join(f"<si>{item}</si>" for item in shared)
            archive.writestr("xl/sharedStrings.xml", f'<sst xmlns="{MAIN}">{items}</sst>')
        if styles is not None:
            archive.writestr("xl/styles.xml", f'<styleSheet xmlns="{MAIN}">{styles}</styleSheet>')
    return buffer.getvalue()


def test_values_keep_exact_decimals_and_sheet_row_numbers() -> None:
    data = workbook_bytes(
        (
            "Positions",
            [
                ["ticker", "weight", "Mkt Val (USD)"],
                ["AAA", 0.3, 3000000],
                [None, None, None],
                ["BBB", 0.7, -5.25],
            ],
        )
    )
    table = parse_xlsx(data)

    assert table.column_names == ("ticker", "weight", "Mkt Val (USD)")
    assert table.column("weight") == ([Decimal("0.3"), Decimal("0.7")], [2, 4])
    assert table.column("Mkt Val (USD)")[0] == [3000000, Decimal("-5.25")]
    assert type(table.column("Mkt Val (USD)")[0][0]) is int


def test_excel_and_csv_exports_of_the_same_table_agree() -> None:
    rows = [["weight", "mv"], [0.1, 10], [0.2, 20], [0.7, -1.5]]
    from_excel = parse_xlsx(workbook_bytes(("Sheet", rows)))
    from_csv = parse_csv("weight,mv\n0.1,10\n0.2,20\n0.7,-1.5\n")
    policy = parse_policy(
        {
            "version": 1,
            "rules": [
                {"rule": "weights_sum_to_one", "tolerance": "0"},
                {"rule": "non_negative", "column": "mv"},
            ],
        }
    )
    assert policy.check(from_excel) == policy.check(from_csv)
    assert policy.check(from_excel).results[0].observed == Decimal("1.0")


def test_percentage_cells_keep_their_stored_fraction() -> None:
    data = workbook_bytes(("Sheet", [["weight"], [0.4], [0.6]]), A2="0%", A3="0.0%")
    assert parse_xlsx(data).column("weight")[0] == [Decimal("0.4"), Decimal("0.6")]


def test_date_cells_become_dates_not_day_counts() -> None:
    data = workbook_bytes(
        ("Sheet", [["as_of", "stamp"], [date(2026, 1, 2), datetime(2026, 1, 2, 9, 30)]]),
    )
    table = parse_xlsx(data)
    assert table.column("as_of")[0] == [date(2026, 1, 2)]
    assert table.column("stamp")[0] == [datetime(2026, 1, 2, 9, 30)]
    report = fa.check(table, [fa.non_negative(column="as_of")])
    assert not report.passed


def test_custom_date_formats_and_1904_dates_are_recognised() -> None:
    styles = (
        '<numFmts count="2"><numFmt numFmtId="164" formatCode="dd/mm/yyyy"/>'
        '<numFmt numFmtId="165" formatCode="#,##0.00 &quot;days&quot;"/></numFmts>'
        '<cellXfs count="3"><xf numFmtId="0"/><xf numFmtId="164"/><xf numFmtId="165"/></cellXfs>'
    )
    sheet = (
        '<row r="1"><c r="A1" t="inlineStr"><is><t>d</t></is></c>'
        '<c r="B1" t="inlineStr"><is><t>n</t></is></c></row>'
        '<row r="2"><c r="A2" s="1"><v>0</v></c><c r="B2" s="2"><v>12.5</v></c></row>'
    )
    table = parse_xlsx(raw_workbook(sheet, styles=styles, date1904=True))
    assert table.column("d")[0] == [date(1904, 1, 1)]
    assert table.column("n")[0] == [Decimal("12.5")]


def test_saved_formula_results_and_cell_types() -> None:
    sheet = (
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>'
        '<c r="C1" t="s"><v>2</v></c><c r="D1" t="s"><v>3</v></c></row>'
        '<row r="2"><c r="A2"><f>B2*2</f><v>0.30000000000000004</v></c>'
        '<c r="B2" t="b"><v>1</v></c><c r="C2" t="e"><f>1/0</f><v>#DIV/0!</v></c>'
        '<c r="D2" t="str"><f>"x"</f><v>x</v></c></row>'
    )
    shared = ["<t>total</t>", "<r><t>fl</t></r><r><t>ag</t></r>", "<t>err</t>", "<t>txt</t>"]
    table = parse_xlsx(raw_workbook(sheet, shared=shared))

    assert table.column_names == ("total", "flag", "err", "txt")
    assert table.column("total")[0] == [Decimal("0.30000000000000004")]
    assert table.column("flag")[0] == [True]
    assert table.column("err")[0] == ["#DIV/0!"]
    assert table.column("txt")[0] == ["x"]


def test_formula_without_saved_result_is_an_error() -> None:
    # openpyxl writes formulas without cached values, like many export tools.
    data = workbook_bytes(("Sheet", [["weight"], ["=0.5+0.5"]]))
    with pytest.raises(InvalidDataError, match=r"Sheet!A2 holds a formula with no saved result"):
        parse_xlsx(data)


def test_several_sheets_require_a_choice() -> None:
    data = workbook_bytes(("Notes", [["text"], ["x"]]), ("Positions", [["weight"], [1]]))
    assert sheet_names(data) == ("Notes", "Positions")
    with pytest.raises(InvalidDataError, match="has 2 sheets \\('Notes', 'Positions'\\)"):
        parse_xlsx(data)
    with pytest.raises(InvalidDataError, match="no sheet 'Missing'"):
        parse_xlsx(data, sheet="Missing")
    assert parse_xlsx(data, sheet="Positions").column("weight")[0] == [1]


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([], "is empty"),
        ([["a", "a"], [1, 2]], "appears more than once"),
        ([["a", " "], [1, 2]], "B1 has no header text"),
        ([["a"], [1, 2]], "B2 has a value but its column has no header"),
    ],
)
def test_header_problems_are_reported(rows: list[list[object]], message: str) -> None:
    with pytest.raises(InvalidDataError, match=message):
        parse_xlsx(workbook_bytes(("Sheet", rows)))


def test_numeric_headers_become_text_and_gaps_are_ignored() -> None:
    table = parse_xlsx(workbook_bytes(("Sheet", [[2026, None, "b"], [1, None, 2]])))
    assert table.column_names == ("2026", "b")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"not a zip", "not an .xlsx workbook"),
        (b"PK\x05\x06" + b"\x00" * 18, "missing 'xl/workbook.xml'"),
    ],
)
def test_unreadable_workbooks_are_rejected(content: bytes, message: str) -> None:
    with pytest.raises(InvalidDataError, match=message):
        parse_xlsx(content)


def test_load_input_reads_workbooks_with_a_sheet(tmp_path: Path) -> None:
    path = tmp_path / "book.xlsm"
    path.write_bytes(workbook_bytes(("A", [["w"], [1]]), ("B", [["w"], [2]])))
    assert load_input(path, sheet="B").column("w")[0] == [2]


@pytest.mark.parametrize(("index", "letters"), [(0, "A"), (25, "Z"), (26, "AA"), (701, "ZZ")])
def test_column_letters(index: int, letters: str) -> None:
    assert column_letter(index) == letters
