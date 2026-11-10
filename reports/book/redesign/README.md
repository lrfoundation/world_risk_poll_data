# Published reports re-set in the format of the 2025 poll's reports

The reports of the 2019, 2021 and 2023 polls were each designed differently. This
folder re-sets them in one format, that of the World Risk Poll 2026 reports (the
reports of the 2025 poll), so that all of them can be bound as one book with a
report to a chapter. The 2019 volume becomes four reports.

    python reports/book/redesign/build.py 2019_risk_at_work

writes `reports/book/output/redesign/2019_risk_at_work.html` and `.pdf`
(1920 by 1080 pt pages, the size of the 2026 reports). It needs the report's
published PDF in `reports/book/.cache/pdfs/` (`python reports/book/bound.py`
downloads them all), Chrome or Chromium, `pymupdf` and `Pillow`.

## What is in a re-set report

- **Text.** The body is the published text, word for word. `extract.py` pulls it
  from the PDF as draft markup; the checked result is `content/<report>.md`.
- **Charts.** Redrawn by `../charts.py` from the values in the report's
  `published_figures.csv`, looked up by finding ID, so a chart cannot show a
  number that differs from the published one. A chart that cannot be redrawn from
  this repository is placed as a picture of the original and says so.
- **New writing.** Only what a stand-alone report needs and the original lacks:
  for the four 2019 reports an "About this report" page, chapter groupings and a
  conclusion. Each new section carries a "New for this edition" tag.
- **Notes on this edition.** Generated at the back of each report: the source,
  the chart renumbering, every wording change, and any query about the original.

## Markup of a content file

A JSON header between `---` lines (title, source PDF, report folder, the
renumbering rule, the list of wording edits), then blocks separated by blank lines:

| Markup | Meaning |
| --- | --- |
| `::front Title`, `::back Title` | A section before or after the chapters |
| `::chapter Title \| 1 in 5 \| caption` | A chapter opener with its headline figure; the paragraphs up to the first `#` go on the opener |
| `::new` … `::endnew` | Text written for this edition |
| `::column` | Start a new column |
| `# Heading`, `## Heading` | Section heading (starts a column) and sub-heading |
| `> text` | A highlighted statement of the original |
| `- text`, `1. **Lead.** text` | Bullets and numbered findings |
| ```` ```chart ```` + JSON | A figure: `hbar`, `grouped`, `vgrouped`, `dumbbell`, `map`, `table` or `original` |
| `[^n]: text` | A footnote of the original, listed under References |

## Files

| File | What it does |
| --- | --- |
| `build.py` | Content file to HTML to PDF |
| `report.css` | The page format, measured from the 2026 report PDFs |
| `paginate.js` | Runs in the page: turns the column flow into pages, numbers them, fills in the contents |
| `extract.py` | Published PDF to draft markup |
| `content/` | One file per re-set report |
