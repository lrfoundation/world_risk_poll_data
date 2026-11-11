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
| `::chapter Title \| 1 in 5 \| caption` | A chapter opener with its headline figure; the paragraphs up to the first `#` or `::flow` go on the opener |
| `::flow` | Start a chapter's text where the original has no heading over it |
| `::new` … `::endnew` | Text written for this edition |
| `::column` | Start a new column |
| `# Heading`, `## Heading`, `### Heading` | Section heading (starts a column) and two levels of sub-heading |
| `> text` | A highlighted statement of the original |
| `::box Title` … `::endbox` | Text the original sets in a box on a grey ground |
| `>> text`, `>-- source` | A sentence or quotation the original sets large, and the line that names its source |
| `^ text` | A note the original sets at the foot of a column, placed under its paragraph |
| `?1. text`, `?> text` | A question of a questionnaire with its number, and an instruction to the interviewer |
| ```` ```grid ```` + JSON | A table of words (`columns`, `rows`, an optional `title`): answer codes, a list of regions, a scoring table |
| ```` ```roll ```` + JSON | A list of names in columns, coloured by status, with a key |
| `- text`, `-- text`, `1. **Lead.** text` | Bullets, points under a bullet, and numbered findings |
| ```` ```chart ```` + JSON | A figure: `hbar`, `grouped`, `stacked`, `stacked_pair` (two sets of stacked bars side by side), `vgrouped`, `dumbbell`, `diverging` (differences either side of nought), `parts` (several drawings under one title), `matrix` (a table of shaded values), `lists` (ranked lists side by side), `line` (values over the years of the poll), `map`, `region_map` (part of the world, a few countries shaded), `table`, `heading` (a table that is only a title over the text that follows) or `original` |
| `[^n]: text` | A footnote of the original, listed under References |

## Files

| File | What it does |
| --- | --- |
| `build.py` | Content file to HTML to PDF |
| `report.css` | The page format, measured from the 2026 report PDFs |
| `paginate.js` | Runs in the page: turns the column flow into pages, numbers them, fills in the contents |
| `extract.py` | Published PDF to draft markup |
| `assemble_2019.py` | Draft markup of the 2019 chapters, plus a plan per report (chapters, chart specifications, new writing), to a content file |
| `core_2021.py` | Reads the typed items (headings, paragraphs, chart labels, small print, footnotes) of a core report of the 2021 poll from its PDF |
| `assemble_2021.py` | Those items, plus a plan per report (opener figures, chart specifications), to a content file |
| `focus_2021.py` | The same two steps for the Focus On reports of the 2021 poll, which share another design |
| `appendix_2021.py` | Reads the appendices of a core report of the 2021 poll: questions, tables of answer codes, regions, references by chapter, methodology |
| `core_2023.py` | Reads the typed items of a report of the 2023 poll (core or Focus On) from its PDF |
| `assemble_2023.py` | Those items, plus the report's plan in `plans_2023.py`, to a content file |
| `plans_2023.py` | A plan per report of the 2023 poll: pages, opener figures, chart specifications, edits and queries |
| `check.py` | Compares a content file with its pages of the PDF, both ways: every sentence set must be in the original, and every block of running text in the original must be set |
| `bind.py` | The re-set reports and the published reports of the 2025 poll, bound as one book |
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

## The four core reports of the 2021 poll

    python reports/book/redesign/assemble_2021.py 2021_a_resilient_world
    python reports/book/redesign/check.py 2021_a_resilient_world 3 46
    python reports/book/redesign/build.py 2021_a_resilient_world

| Report | Pages of the PDF (from 0) | Charts and tables |
| --- | --- | --- |
| `2021_a_changed_world` | 3 to 50, appendices 51 to 57 | 26, of which 4 are pictures of the original |
| `2021_a_resilient_world` | 3 to 46, appendices 47 to 70 | 29, of which 4 are pictures of the original |
| `2021_a_digital_world` | 3 to 35, appendices 36 to 42 | 23, of which 1 is a picture of the original |
| `2021_safe_at_work` | 3 to 37, appendices 38 to 48 | 25 |

These four share one design, so nothing in their content files is written by
hand. `core_2021.py` tells a block's role from its type (the report's fonts and
sizes are listed in `kind_of`), and finds each chart's extent from the two pink
rules that bracket it; what lies between them is the chart's lettering, which
the specification redraws, and its small print (the survey question and notes),
which is kept. Each report keeps its own preface, executive summary, chapters
and conclusion in the original order, and its charts keep their original
numbers. A plan in `assemble_2021.py` gives the pages, the headline figure for
each chapter opener and one specification per chart; a chart with no
specification is placed as a picture of the original, so a first run is already
a complete draft.

Conventions added for these reports:

- A stacked bar with one segment the original draws without a figure (under 5%)
  draws it in its place at what is left of 100%, without a figure (`"gaps"`).
  With two or more such segments in a row the space is one pale segment at the
  end of the bar.
- `"zero": "<0.5"` prints a value that rounds to nought as the original does;
  `"decimals"` may be a number or `"g"` (each value as published).
- A `matrix` row with no values is a heading over the rows below it.
- Type that the PDF holds in white inside a paragraph (a leftover chart label)
  is dropped, since it does not print.

The appendices follow the conclusion, as in the originals: the questionnaire,
the list of regions, the references by chapter, and in two reports a
methodology. `appendix_2021.py` reads them (`appendices=(first, last)` in a
plan). Their tables are drawn as grids of pale rules under a pink band, so a
table is read from its rules: the rules give the rows and columns, and the type
that falls in a cell is the cell's text. Questions, instructions to the
interviewer and paragraphs are told apart by their type. A table or chart that
cannot be set as a table of words is placed as a picture of the original
(`appendix_pictures` in the plan: a page, a rectangle and a specification;
`bare` for one the original sets without a number or title), and the report's
"Notes on this edition" names each one.

## The Focus On reports of the 2021 poll

    python reports/book/redesign/focus_2021.py 2021_focus_critical_infrastructure
    python reports/book/redesign/check.py 2021_focus_critical_infrastructure 0 9
    python reports/book/redesign/build.py 2021_focus_critical_infrastructure

| Report | Pages of the PDF (from 0) | Charts and tables |
| --- | --- | --- |
| `2021_focus_critical_infrastructure` | 0 to 9 | 8, of which 1 is a picture of the original |
| `2021_focus_fossil_fuels` | 0 to 12 | 8, all pictures of the original |
| `2021_focus_violence_and_harassment` | 0 to 13 | 10 |

*Focus On: Risk and Gender* is not part of the book.

These reports are short, have no chapters, and are designed as pages of 1920 by
1280 points in two columns. `focus_2021.py` reads them by type, as `core_2021.py`
does the core reports, and arranges each one the same way:

- the summary on the original's cover ("What the data tells us", "What we can do
  about it") is the front section;
- the introduction takes the opening page, with the headline figure the original
  prints beside it (`plain_opener` in the header: no chapter number);
- the rest runs on as one text under the original's headings, which are listed
  in the contents (`contents_h2`);
- the numbered references of the last page are the notes, under the original's
  title "References and endnotes", and the "About" texts are the back section.

The PDF sometimes holds neighbouring lines of two columns as one block, so the
reader splits blocks where a line jumps sideways, and puts back together the
paragraphs that a column, a page or a chart divides.

Conventions added for these reports:

- `"plate": true` gives a figure that is too wide for a column a page of its
  own. `paginate.js` starts it on the next page and brings the text that follows
  forward to fill the page before it; figures keep their order.
- `"blank"` paints out page furniture that falls inside the rectangle of a
  picture of the original (the logo in the corner of the page, the question
  text that is set again underneath).
- A difference that the original prints without a sign, with the colour saying
  which group is higher, is drawn on that group's side (`"signless"`, and a
  fourth entry of -1 in the row).
- A map of regions or a pie chart whose values are printed is drawn as bars;
  each report's "Notes on this edition" says where.
- The charts of the fossil fuels report plot a value for every country against
  figures from Our World in Data and the World Bank, and print none of them.
  All eight are pictures of the original until those values are in the repository.

`check.py` reports two differences that are not errors: a sentence the original
breaks across two pages (fossil fuels), and the quotation whose bracketed words
the PDF holds apart from the rest (critical infrastructure). The lettering
inside a picture of the original is also reported, since it is not set as text.

## The reports of the 2023 poll

    python reports/book/redesign/assemble_2023.py 2023_a_world_of_waste
    python reports/book/redesign/check.py 2023_a_world_of_waste 1 40 41 41
    python reports/book/redesign/build.py 2023_a_world_of_waste

| Report | Pages of the PDF (from 0) | Charts and tables | Pages re-set |
| --- | --- | --- | --- |
| `2023_resilience_in_a_changing_world` | 1 to 34, 44 | 33, of which 4 are pictures of the original | 52 |
| `2023_a_world_of_waste` | 1 to 40, 41 | 35, of which 2 are pictures | 51 |
| `2023_engineering_safer_workplaces` | 1 to 29, 30 | 25, of which 4 are pictures | 38 |
| `2023_what_the_world_worries_about` | 1 to 34, 35 | 29, of which 4 are pictures | 43 |
| `2023_focus_ocean_workers` | 1 to 10 | 10, of which 1 is a picture | 18 |
| `2023_focus_migration` | 1 to 18 | 17, of which 4 are pictures | 30 |

The appendices of the core reports (questionnaire, regions, the method of the
Resilience Index) are not re-set yet; each report's "Notes on this edition"
says so.

All six are designed as landscape pages of 842 by 595 points in two columns,
set in DM Sans. `core_2023.py` types each line by size and face: text in 8
point, headings in pink, chart titles in 10 point bold, small print in 5 or 6
point, page notes marked with roman numerals. The font is a variable one, so
bold is told from the width of the letters. A chart runs from its title to its
small print, and the lettering between the two is left out of the text; a chart
that is redrawn takes its values from `published_figures.csv` as in the other
reports.

A plan in `plans_2023.py` gives, for each report:

- `pages`, the opener figure of each chapter (`chapters`), and the chart
  specifications (a function that returns them by chart number);
- `numbers`: charts the original prints without a number, or under a heading
  instead of a title, mapped to the label they take (*Engineering safer
  workplaces* prints its Chart 4.6 without one; the ocean workers report numbers
  none of its charts);
- `small_text`: pages whose text is set in 7 point (the closing page of a
  Focus On); `box_gap`: the line spacing of the boxes, where it is not the 11
  points of the core reports;
- `replace`, `drop`, `after`, `inside`, `as_chapters`: corrections to the
  reading order where the page design departs from the two columns;
- `edits` and `queries`: every change to the wording and every doubt about the
  original, both printed in the "Notes on this edition".

Conventions added for these reports:

- A chart the original sets as a map of states or countries with its values
  printed is drawn as sorted bars. Scatter plots, the chord diagrams of the
  migration report and charts whose values are not printed stay pictures of the
  original, each with its reason.
- `hbar` takes heading rows (a row with no finding), a `texts` column for
  changes printed as words ("+3pp", "No change") and one `colour` for all bars.
  `diverging` takes heading rows too, and scores between nought and one get a
  finer axis. `dumbbell` rows may have no figure at the right.
- The parts of a `parts` figure stay whole across a column break.
- `check.py` leaves the roman note marks out on both sides, checks small notes
  that start "Note" or "*" whatever their size, and exempts the lettering inside
  the rectangle of a picture of the original.

`check.py` still reports the lines of the list of charts on a contents page for
the charts that are pictures, and one or two blocks of chart lettering (a note
set between two charts in the ocean workers report). None is missing text.

## Binding the book

    python reports/book/redesign/bind.py --screen

writes `output/redesign/World_Risk_Poll_reports_2019_to_2025.pdf` (782 pages of
1920 by 1080 points) and, with `--screen`, a copy with its pictures at 110 dpi.
Build every report first; the five reports of the 2025 poll come from
`.cache/pdfs/` as published and are placed page for page.

The book is a title page, "About this book", the contents, and four parts, one
for each poll. A part opens with a page of its own and its reports follow whole,
cover first, in the order of `BOOK` in `bind.py`. Each report keeps its own page
numbers. The book's page number ("Book page 123") is added in the middle of the
foot of every page but the covers, where all the reports leave the footer
empty; this is the only mark made on the pages of the 2025 poll's reports. The
PDF has a bookmark for each part and report.

With `--indesign` the book is also written as a set of InDesign documents, one
for each part of it (see "An InDesign file of a book or report" in the README
one folder up).

The pages have no bleed and no trim marks, and parts and reports start on the
next page whichever side it falls on. Both are for the printer's specification
to settle.
