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
| ```` ```chart ```` + JSON | A figure: `hbar`, `grouped`, `stacked`, `vgrouped`, `dumbbell`, `matrix` (a table of shaded values), `map`, `table`, `heading` (a table that is only a title over the text that follows) or `original` |
| `[^n]: text` | A footnote of the original, listed under References |

## Files

| File | What it does |
| --- | --- |
| `build.py` | Content file to HTML to PDF |
| `report.css` | The page format, measured from the 2026 report PDFs |
| `paginate.js` | Runs in the page: turns the column flow into pages, numbers them, fills in the contents |
| `extract.py` | Published PDF to draft markup |
| `assemble_2019.py` | Draft markup of the 2019 chapters, plus a plan per report (chapters, chart specifications, new writing), to a content file |
| `check.py` | Compares a content file with its pages of the PDF, both ways: every sentence set must be in the original, and every block of running text in the original must be set |
| `content/` | One file per re-set report |

## The four reports of the 2019 volume

    python reports/book/redesign/assemble_2019.py 2019_technology
    python reports/book/redesign/check.py 2019_technology 126 140 141 152
    python reports/book/redesign/build.py 2019_technology

| Report | Chapters of the 2019 volume | Pages of the PDF (from 0) |
| --- | --- | --- |
| `2019_feeling_safe` | 1 to 4 and 10 | 17 to 86, 171 to 182 |
| `2019_risk_at_work` | 5 | 87 to 111 |
| `2019_climate_food_water` | 6 and 9 | 112 to 125, 153 to 170 |
| `2019_technology` | 7 and 8 | 126 to 140, 141 to 152 |

`2019_risk_at_work` was the pilot and its content file was written by hand; the
others come from `assemble_2019.py`. A plan there lists, for each report, its
chapters, a specification for every chart and table, the new writing, and the
repairs the PDF's reading order needs: wording changes (`replace`), chart
furniture to leave out of the text (`drop`), small print to put back (`insert`,
`note_from`) and headings to move (`move`). The assembler also rejoins
paragraphs that a chart or a column break splits, and numbers the footnotes of
a report's chapters in one sequence from 1.

Three conventions for charts that the published figures cannot fully supply:

- A segment that the original draws without a figure has no finding ID. It is
  drawn as part of one pale segment, without a number (`"rest"` in the
  specification), and segments too narrow for their figure carry a note.
- A chart that plots the poll against another source, or values that were never
  printed, is placed as a picture of the original (`original`), and the notes
  at the back of the report say why.
- Map shading is computed from the public data by `../maps.py` and checked
  against the country figures the report prints; the countries named beside a
  map are the published figures. The check reports the headings and the
cross-references that were changed on purpose ("Chapter 3 of the 2019 volume"),
which are also listed in each report's "Notes on this edition".
