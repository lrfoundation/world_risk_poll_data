# World Risk Poll coffee table book

A designed, landscape book of the World Risk Poll reports: 22 reports from the four polls
(2019, 2021, 2023 and 2025), each with its headline finding, a page of numbers, a chart or two
and, for the core reports, a world map. It is built from the files in this repository, so every
number in it can be traced.

```
pip install -r reports/requirements.txt
python reports/book/build.py --pdf
```

This writes `output/book.html` and `output/World_Risk_Poll_22_reports.pdf` (91 pages, 1920 by
1080, the page format of the World Risk Poll 2026 reports) and regenerates
[`FIGURES.md`](FIGURES.md). The first run downloads DM Sans from Google Fonts and the Natural
Earth 1:110m country outlines into `.cache/`. The PDF is printed by a Chrome, Chromium or Edge
that is already installed. Without one, leave off `--pdf`, open `output/book.html` in a browser
and print to PDF with no margins and background graphics switched on.

## The other two books in this folder

- [`redesign/`](redesign/README.md) re-sets the published reports themselves, full text and
  every chart, in the format of the 2026 reports, for one bound book with a report to a chapter.
  Work in progress: the pilot is the second of the four 2019 reports, "Risk at work".
- `bound.py` binds the published PDFs as they are into one landscape volume
  (`python reports/book/bound.py`), with the 2019 report cut into its four parts. It downloads
  the PDFs listed in `../report_inventory.csv` into `.cache/pdfs/`.

## Which reports are in it

| Poll | Reports |
| --- | --- |
| 2019 | The full report, as four parts (see below) |
| 2021 | A Changed World?, A Resilient World?, A Digital World, Safe at Work?, and three Focus On reports: income and migration in violence and harassment at work, fossil fuel dependency, critical infrastructure |
| 2023 | Resilience in a Changing World, A World of Waste, Engineering Safer Workplaces, What the World Worries About, and two Focus On reports: ocean workers, migration in a warming world |
| 2025 | Alone Together, The Quiet Hazards, A resilient life, From alert to agency, After the storm |

*Focus On: Risk and Gender* is left out.

### The 2019 report in four parts

The 2019 poll was published as one full report. The book presents it as four parts, so that it
sits alongside the four or five core reports of each later poll. The parts follow the themes of
the 2021 core reports. The split is defined in `SPLIT_2019` in `content.py`; the reproduction
folder `WRP_2019/core_world_risk_poll_2019` is unchanged and still covers the whole report.

| Part | Title in the book | Chapters of the 2019 report |
| --- | --- | --- |
| 1 | Feeling safe and the sources of risk | 1 *How safe do we feel?*, 2 *The sources of greatest risk in people's lives*, 3 *The risk perception gap*, 4 *Influencing understanding of risk*, 10 *Forecasting risk* |
| 2 | Risk at work | 5 *Risk at work* |
| 3 | Climate change, food and water | 6 *Climate change risk*, 9 *Food and water risk* |
| 4 | Technology and the internet | 7 *Technology-related risk perceptions*, 8 *Internet-related risk perceptions* |

## Where the numbers come from

- **Text and charts** use published figures only. `content.py` refers to a figure by its
  `finding_id` in the report's `published_figures.csv`, written as `{X06_less_2021}`, and
  `build.py` puts the printed value in its place. No figure is typed in by hand. The build stops
  if an ID does not exist.
- **`FIGURES.md`** lists every figure the book uses, with the value the public data gives and its
  status in the report's `RESULTS.md`. Figures that the data contradicts were avoided where the
  report itself looks wrong (for example the 75% in the critical infrastructure Focus On). The
  three that remain `DIFFERENT` are in the ocean workers Focus On, whose definition of an ocean
  worker cannot be matched exactly from the public data; they are shown as published.
- **Maps** are not published figures. `maps.py` computes each one from the public wave file with
  the conventions in [`reports/README.md`](../README.md): `PROJWT` weights, people who were not
  asked left out, don't know and refused kept in the base. Countries with fewer than 100 answers
  are left blank. `python reports/book/maps.py` checks the map values against the country figures
  that the reports also print.

## Design

The book follows the World Risk Poll 2026 report style: DM Sans, ink text `#231F20`, and the
report palette of fuchsia `#E3076E`, green `#00785C` and teal `#00A7B3`, with grey `#BDBDBD` kept
for don't know and refused. Each poll keeps its edition colour throughout: 2021 fuchsia, 2023
green, 2025 teal. The house style gives 2019 no edition colour, so it takes navy `#0D2240`.

Charts follow the report chart rules: axis lines on the left and bottom only, dotted gridlines at
the labelled values, bars with a rounded free end, the key above the plot, value labels in the
heaviest weight and no title inside the image. Value labels take the series colour only where it
is dark enough to read on white (fuchsia, green, navy); teal series are labelled in ink.

## Files

| File | What it is |
| --- | --- |
| `content.py` | The polls, the 22 reports, their text, and which published figures each page shows |
| `figures.py` | Reads published figures and formats them |
| `maps.py` | Country values for the maps, from the public data |
| `charts.py` | The charts, drawn as SVG |
| `worldmap.py` | The world map, in the Equal Earth projection |
| `book.css` | Page layouts |
| `build.py` | Puts the pages together and prints the PDF |
| `FIGURES.md` | Generated: every published figure used |
| `assets/lrf-logo.svg` | The Foundation's logo |

## Adding a report

Add an entry to `REPORTS` in `content.py`: the report's folder, title, a lede, a headline figure,
four to six numbers, one or two charts and, for a core report, a function in `maps.py`. Run
`build.py`; the contents page and page numbers update themselves.

## An InDesign file of a book or report

    python reports/book/indesign.py                                          # the coffee table book
    python reports/book/indesign.py reports/book/output/redesign/2019_risk_at_work.html

writes `output/indesign/<name>/` with an IDML document, a `Links` folder and the
DM Sans files, and zips the folder. IDML is InDesign's interchange format;
InDesign 2020 or later opens it and saves it as `.indd`.

The script opens the built HTML in Chrome three times: once to read where every
block of text and every chart sits, once to print each page without that text
and those charts (the page's artwork), and once to print each chart on its own.
In the IDML each page has its artwork as one placed PDF at the back, each chart
or map as a placed PDF of its own, and the text as live text frames. Paragraph
styles are made from the type in use and named after it ("27 on 41 Regular
231F20"), blocks that follow one another down a column share a frame, and
frames grow with their text.

What to expect on opening:

- Links are relative paths. If InDesign reports them missing, Links > Relink to
  Folder and the `Links` folder puts all of them back at once.
- The text needs DM Sans. The files are in `Document fonts`.
- InDesign breaks lines a little differently from a browser, so a line may turn
  at a different word.
- Text inside a chart is part of the chart's PDF, not live text.

The file was test-opened in Scribus, which reads IDML, and its pages compared
with the PDF. It has not been opened in InDesign itself.

