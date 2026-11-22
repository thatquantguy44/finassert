/** Build the deterministic P-05 monthly performance audit workbook. */

import fs from "node:fs/promises";
import path from "node:path";

import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(process.cwd());
const fixture = path.join(
  root,
  "specs/0020/artifacts/fixtures/monthly_returns_2024_seeded.csv",
);
const output = path.resolve(
  process.argv[2] ?? path.join(root, "examples/monthly-performance/monthly-performance-audit.xlsx"),
);

const colors = {
  navy: "#1F4E78",
  blue: "#1F4E79",
  lightBlue: "#D9EAF7",
  lightYellow: "#FFF2CC",
  lightRed: "#FCE4D6",
  lightGreen: "#E2F0D9",
  gray: "#F2F2F2",
  border: "#D9E2F3",
  text: "#1F2937",
  red: "#9C0006",
};

function parseCsv(text) {
  const [header, ...lines] = text.trim().split(/\r?\n/);
  const fields = header.split(",");
  return lines.map((line) => {
    const values = line.split(",");
    return Object.fromEntries(fields.map((field, index) => [field, values[index]]));
  });
}

function dateValue(isoDate) {
  return new Date(`${isoDate}T00:00:00Z`);
}

function formatTitle(sheet, title, subtitle, width) {
  sheet.mergeCells(`A1:${width}1`);
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1").format = {
    fill: colors.navy,
    font: { name: "Arial", size: 15, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
  sheet.getRange("A1").format.rowHeight = 28;
  sheet.mergeCells(`A2:${width}2`);
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format = {
    font: { name: "Arial", size: 10, italic: true, color: colors.text },
    verticalAlignment: "center",
  };
  sheet.getRange("A2").format.rowHeight = 22;
}

function formatHeader(range) {
  range.format = {
    fill: colors.blue,
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: "#FFFFFF" },
  };
}

function formatSection(range) {
  range.format = {
    fill: colors.lightBlue,
    font: { name: "Arial", size: 10, bold: true, color: colors.text },
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: colors.border },
  };
}

function formatBody(range) {
  range.format = {
    font: { name: "Arial", size: 10, color: colors.text },
    verticalAlignment: "center",
  };
}

const sourceRows = parseCsv(await fs.readFile(fixture, "utf8"));
const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const assumptions = workbook.worksheets.add("Assumptions");
const reference = workbook.worksheets.add("Reference");
const audit = workbook.worksheets.add("Audit input");

for (const sheet of [summary, assumptions, reference, audit]) {
  sheet.showGridLines = false;
  sheet.tabColor = colors.navy;
}

formatTitle(
  summary,
  "Monthly Performance Audit",
  "Synthetic 2024 strategy and benchmark example with an intentionally seeded June discrepancy.",
  "G",
);
summary.getRange("A4:B4").values = [["Current formula tie-out", ""]];
formatSection(summary.getRange("A4:B4"));
summary.getRange("B4").formulas = [
  [
    '=IF(COUNTIF(\'Audit input\'!$K$6:$K$17,"FAIL")>0,"Correction required","All workbook formula tie-outs pass")',
  ],
];
summary.getRange("B4").format = {
  fill: colors.lightRed,
  font: { name: "Arial", size: 10, bold: true, color: colors.red },
  verticalAlignment: "center",
};
summary.getRange("A6:B6").values = [["Correction walkthrough", ""]];
formatSection(summary.getRange("A6:B6"));
summary.getRange("A7:B13").values = [
  ["Seeded source row", "src-2024-06"],
  ["Seeded source cell", "Audit input!E15"],
  ["Expected strategy cumulative", null],
  ["Reported strategy cumulative", null],
  ["Difference", null],
  ["Allowed absolute difference", null],
  ["Correction", "Replace Audit input!E15 with 0.061520150601. Save, then rerun."],
];
summary.getRange("B9:B12").formulas = [
  ["='Audit input'!G15"],
  ["='Audit input'!E15"],
  ["=B10-B9"],
  ["=Assumptions!$B$15"],
];
summary.getRange("A15:B15").values = [["Reproduce the audit", ""]];
formatSection(summary.getRange("A15:B15"));
summary.getRange("A16:B18").values = [
  ["Python", "python examples/monthly-performance/run_audit.py --expect failed"],
  [
    "CLI",
    "finassert check --config examples/monthly-performance/policy.yml --input examples/monthly-performance/monthly-performance-audit.xlsx --format xlsx --sheet 'Audit input' --header-row 5 --max-row 17",
  ],
  [
    "Scope",
    "This is synthetic method evidence. Review the policy declarations before applying the workflow to a production return series.",
  ],
];
formatBody(summary.getRange("A4:B18"));
summary.getRange("A4:A18").format.font = { name: "Arial", size: 10, bold: true, color: colors.text };
summary.getRange("B7:B8").format.fill = colors.gray;
summary.getRange("B13").format = {
  fill: colors.lightYellow,
  font: { name: "Arial", size: 10, color: colors.text },
  wrapText: true,
  verticalAlignment: "center",
};
summary.getRange("B16:B18").format = {
  fill: colors.gray,
  font: { name: "Arial", size: 10, color: colors.text },
  wrapText: true,
  verticalAlignment: "top",
};
summary.getRange("B9:B12").format.numberFormat = "0.000000000000%";
summary.getRange("A1:A18").format.columnWidth = 34;
summary.getRange("B1:B18").format.columnWidth = 78;
summary.getRange("A16:B18").format.rowHeight = 34;

formatTitle(
  assumptions,
  "Audit Assumptions",
  "The declared comparison and mapped fields used by the starter policy.",
  "D",
);
assumptions.getRange("A4:C4").values = [["Declaration", "Value", "Policy field"]];
formatHeader(assumptions.getRange("A4:C4"));
assumptions.getRange("A5:C19").values = [
  ["Strategy identifier", "strategy-demo", "strategy_id"],
  ["Benchmark identifier", "benchmark-demo", "benchmark_id"],
  ["Base currency", "USD", "base_currency"],
  ["Periodic return unit", "fraction", "periodic_return_unit"],
  ["Reported return unit", "fraction", "reported_return_unit"],
  ["First month end", dateValue("2024-01-31"), "window_start"],
  ["Last month end", dateValue("2024-12-31"), "window_end"],
  ["Valuation convention", "calendar month-end total return", "valuation_convention"],
  ["Strategy fee treatment", "net of management and transaction costs", "strategy_fee_treatment"],
  ["Benchmark fee treatment", "gross of fees", "benchmark_fee_treatment"],
  ["Allowed absolute difference", 0.0001, "tolerance"],
  ["Source snapshot", "monthly_returns_2024_seeded.csv", "fixture source"],
  ["Input worksheet", "Audit input", "--sheet"],
  ["Header row", 5, "--header-row"],
  ["Last input row", 17, "--max-row"],
];
formatBody(assumptions.getRange("A5:C19"));
assumptions.getRange("B5:B19").format = {
  fill: colors.lightYellow,
  font: { name: "Arial", size: 10, color: colors.blue },
  verticalAlignment: "center",
  wrapText: true,
};
assumptions.getRange("C5:C19").format = {
  fill: colors.gray,
  font: { name: "Arial", size: 10, color: colors.text },
  verticalAlignment: "center",
};
assumptions.getRange("B10:B11").format.numberFormat = "yyyy-mm-dd";
assumptions.getRange("B14").format.numberFormat = "0.0000%";
assumptions.getRange("A4:C19").format.borders = {
  preset: "all",
  style: "thin",
  color: colors.border,
};
assumptions.getRange("A1:A19").format.columnWidth = 30;
assumptions.getRange("B1:B19").format.columnWidth = 42;
assumptions.getRange("C1:C19").format.columnWidth = 24;
assumptions.getRange("A21:D21").values = [["Source mapping", "", "", ""]];
formatSection(assumptions.getRange("A21:D21"));
assumptions.getRange("A22:D22").values = [
  ["Policy field", "Workbook column", "Purpose", "Required"],
];
formatHeader(assumptions.getRange("A22:D22"));
assumptions.getRange("A23:D28").values = [
  ["row_key", "Source row ID", "Stable source identity", "Yes"],
  ["period_end", "Period end", "Calendar month-end", "Yes"],
  ["strategy_return", "Strategy monthly return", "Monthly simple return", "Yes"],
  ["benchmark_return", "Benchmark monthly return", "Monthly simple return", "Yes"],
  ["reported_strategy_cumulative", "Reported strategy cumulative", "Candidate tie-out", "Yes"],
  ["reported_benchmark_cumulative", "Reported benchmark cumulative", "Candidate tie-out", "Yes"],
];
formatBody(assumptions.getRange("A23:D28"));
assumptions.getRange("A22:D28").format.borders = {
  preset: "all",
  style: "thin",
  color: colors.border,
};
assumptions.getRange("D1:D28").format.columnWidth = 18;

formatTitle(
  reference,
  "Independent Reference Calculation",
  "Chronological monthly linking ignores reported cumulative figures, so a reported error cannot affect later expected values.",
  "G",
);
reference.getRange("A5:G5").values = [
  [
    "Source row ID",
    "Period end",
    "Strategy monthly return",
    "Benchmark monthly return",
    "Active return",
    "Strategy reference cumulative",
    "Benchmark reference cumulative",
  ],
];
formatHeader(reference.getRange("A5:G5"));
const chronologicalDates = [
  "2024-01-31",
  "2024-02-29",
  "2024-03-31",
  "2024-04-30",
  "2024-05-31",
  "2024-06-30",
  "2024-07-31",
  "2024-08-31",
  "2024-09-30",
  "2024-10-31",
  "2024-11-30",
  "2024-12-31",
];
reference.getRange("B6:B17").values = chronologicalDates.map((value) => [dateValue(value)]);
for (let row = 6; row <= 17; row += 1) {
  const formulas = [
    `=INDEX('Audit input'!$A$6:$A$17,MATCH(B${row},'Audit input'!$B$6:$B$17,0))`,
    `=INDEX('Audit input'!$C$6:$C$17,MATCH(B${row},'Audit input'!$B$6:$B$17,0))`,
    `=INDEX('Audit input'!$D$6:$D$17,MATCH(B${row},'Audit input'!$B$6:$B$17,0))`,
    `=C${row}-D${row}`,
    row === 6 ? `=C${row}` : `=(1+F${row - 1})*(1+C${row})-1`,
    row === 6 ? `=D${row}` : `=(1+G${row - 1})*(1+D${row})-1`,
  ];
  reference.getRange(`A${row}:A${row}`).formulas = [[formulas[0]]];
  reference.getRange(`C${row}:G${row}`).formulas = [[...formulas.slice(1)]];
}
reference.getRange("A19:G19").values = [["Reference summary", "", "", "", "", "", ""]];
formatSection(reference.getRange("A19:G19"));
reference.getRange("A20:G21").values = [
  ["Strategy cumulative return", "", "", "", "", null, ""],
  ["Benchmark cumulative return", "", "", "", "", "", null],
];
reference.getRange("F20").formulas = [["=F17"]];
reference.getRange("G21").formulas = [["=G17"]];
formatBody(reference.getRange("A6:G21"));
reference.getRange("B6:B17").format.numberFormat = "yyyy-mm-dd";
reference.getRange("C6:G17").format.numberFormat = "0.0000000000%";
reference.getRange("F20:G21").format.numberFormat = "0.0000000000%";
reference.getRange("A20:A21").format.font = { name: "Arial", size: 10, bold: true, color: colors.text };
reference.getRange("A5:G17").format.borders = {
  preset: "inside",
  style: "thin",
  color: colors.border,
};
reference.getRange("A1:A21").format.columnWidth = 18;
reference.getRange("B1:B21").format.columnWidth = 14;
reference.getRange("C1:G21").format.columnWidth = 24;
reference.freezePanes.freezeRows(5);

formatTitle(
  audit,
  "Audit Input",
  "Raw source order is deliberately non-chronological. June's reported strategy cumulative value is intentionally incorrect.",
  "K",
);
audit.getRange("A5:K5").values = [
  [
    "Source row ID",
    "Period end",
    "Strategy monthly return",
    "Benchmark monthly return",
    "Reported strategy cumulative",
    "Reported benchmark cumulative",
    "Expected strategy cumulative",
    "Strategy difference",
    "Expected benchmark cumulative",
    "Benchmark difference",
    "Formula status",
  ],
];
formatHeader(audit.getRange("A5:K5"));
audit.getRange("A6:F17").values = sourceRows.map((row) => [
  row.source_row_id,
  dateValue(row.period_end),
  Number(row.strategy_return),
  Number(row.benchmark_return),
  Number(row.reported_strategy_cumulative),
  Number(row.reported_benchmark_cumulative),
]);
for (let row = 6; row <= 17; row += 1) {
  audit.getRange(`G${row}:K${row}`).formulas = [[
    `=INDEX(Reference!$F$6:$F$17,MATCH(B${row},Reference!$B$6:$B$17,0))`,
    `=E${row}-G${row}`,
    `=INDEX(Reference!$G$6:$G$17,MATCH(B${row},Reference!$B$6:$B$17,0))`,
    `=F${row}-I${row}`,
    `=IF(AND(ABS(H${row})<=Assumptions!$B$15,ABS(J${row})<=Assumptions!$B$15),"PASS","FAIL")`,
  ]];
}
formatBody(audit.getRange("A6:K17"));
audit.getRange("A6:F17").format.font = { name: "Arial", size: 10, color: colors.blue };
audit.getRange("G6:K17").format.font = { name: "Arial", size: 10, color: colors.text };
audit.getRange("B6:B17").format.numberFormat = "yyyy-mm-dd";
audit.getRange("C6:J17").format.numberFormat = "0.0000000000%";
audit.getRange("K6:K17").format.horizontalAlignment = "center";
audit.getRange("K6:K17").conditionalFormats.add("containsText", {
  text: "FAIL",
  format: { fill: colors.lightRed, font: { bold: true, color: colors.red } },
});
audit.getRange("K6:K17").conditionalFormats.add("containsText", {
  text: "PASS",
  format: { fill: colors.lightGreen, font: { bold: true, color: "#006100" } },
});
audit.getRange("A5:K17").format.borders = {
  preset: "inside",
  style: "thin",
  color: colors.border,
};
audit.tables.add("A5:K17", true, "MonthlyPerformanceAuditInput");
audit.getRange("A1:A17").format.columnWidth = 18;
audit.getRange("B1:B17").format.columnWidth = 14;
audit.getRange("C1:J17").format.columnWidth = 22;
audit.getRange("K1:K17").format.columnWidth = 14;
audit.freezePanes.freezeRows(5);

workbook.recalculate();
await fs.mkdir(path.dirname(output), { recursive: true });
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(output);
console.log(output);
