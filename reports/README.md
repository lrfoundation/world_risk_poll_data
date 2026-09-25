# Reproducing the World Risk Poll reports

This folder re-creates the findings of every World Risk Poll core report and
Focus On report from the public data in this repository. Each report has its own
folder with Python and R scripts, the report's published figures, and a
generated comparison of published and reproduced values.

> **Status:** the shared tooling below is in place, and report folders are being
> added. [`report_inventory.csv`](report_inventory.csv) lists every report and
> its progress. The list is provisional until it has been checked against the
> reports on lrfoundation.org.uk.

## Quick start

From the repository root:

```
pip install -r reports/requirements.txt           # pandas, pyarrow
Rscript -e 'install.packages(c("arrow", "dplyr"))' # for the R scripts

python reports/WRP_2021/<report>/reproduce.py      # one report, Python
Rscript reports/WRP_2021/<report>/reproduce.R      # the same report, R

Rscript reports/run_all.R                          # every report, R
python reports/run_all.py                          # every report, Python; writes the summary
```

Run the R scripts before `run_all.py` if you want the R column filled in each
`RESULTS.md`. `run_all.py` also writes `REPRODUCTION_SUMMARY.md`, with one row
per report.

## Layout

```
reports/
  wrp/                 shared Python helpers (import wrp)
  R/wrp.R              the same helpers in R, with the same function names
  external/            snapshots of public non-poll data some reports use (World Bank
                       indicators and similar), named <report_folder>__<source>.csv; each
                       report's README gives the source, licence and download date
  _template/           starting point for a new report folder
  WRP_2019/ … WRP_2025/
    <core|focus_on>_<name>/
      README.md              the report, its link, method notes, Gallup caveats
      published_figures.csv  every published finding, with its page
      reproduce.py           one function per finding, chart or table
      reproduce.R            the same findings in R
      RESULTS.md             generated: published vs Python vs R
```

Each wave folder is named after the fieldwork year of the data it uses, the same
as the data folders at the repository root. Reports are often branded with their
publication year: for example, the *World Risk Poll 2024* reports use the 2023
data and live in `WRP_2023/`.

## Conventions

- **Weights.** `PROJWT` (population projection weight) by default. Within a
  country it is proportional to `WGT`, so country figures are the same under
  either weight. Global and regional figures are population-weighted, as in the
  reports.
- **Base.** Respondents who were not asked a question (missing values) are always
  excluded. "Don't know" and "refused" answers stay in the denominator unless a
  script says otherwise. This is Gallup's reporting convention, and it is why the
  figures can differ from a simple share of substantive answers (see
  `examples/quickstart.py`).
- **Country coverage.** Coverage differs by wave (142, 121, 142 and 140
  countries). Trend findings use the country set the report states.
- **Matching.** A finding is `MATCH` when the reproduced value rounds to the
  published figure. It is `WITHIN_TOLERANCE` when it is within the row's
  `tolerance` (default ±1 point, to allow for rounding in the published charts).
  `DIFFERENT` findings stay in the table, with the reason in the report's README
  where it is known.

## `published_figures.csv`

| Column | Meaning |
| --- | --- |
| `finding_id` | `F01`, `F02` …; a chart or table with several values uses `F07_<key>` (for example `F07_1` for group code 1) |
| `page`, `section` | Where the figure appears in the report |
| `description` | What the figure is, in words |
| `published_value` | The number as printed (percentages as 0–100), or a text answer for rankings |
| `unit` | `pct`, `mean`, `count`, `rank`, `text` … |
| `tolerance` | Optional; the default is 1 |
| `source` | `text`, `chart` or `table` |
| `requires_gallup`, `gallup_items` | `Y` and the item names if the finding needs Gallup World Poll data |
| `note` | Anything a reader needs to interpret the comparison |

## Gallup World Poll data

The World Risk Poll is fielded as part of the Gallup World Poll. Some report
findings combine World Risk Poll questions with core Gallup World Poll items that
are **not in this public release**. Those items are Gallup's proprietary data and
must be obtained from Gallup directly:
https://www.gallup.com/analytics/318875/global-research.aspx

The code for those findings is included, and each report's README names the items
it needs. Without the Gallup data, those findings are reported as `GALLUP_ONLY`
and every other finding still runs. If you have licensed the items, set
`GALLUP_WP_PATH` to a file holding `WPID_RANDOM` plus the items (Parquet or CSV;
Python also reads `.sav` and `.dta`):

```
GALLUP_WP_PATH=/path/to/gallup_items.parquet python reports/WRP_2021/<report>/reproduce.py
```

Rows are matched on `WPID_RANDOM`, so the file must carry the same respondent IDs
as this release. Confirm this with Gallup when you request the data.

## Adding a report

1. Copy `_template/` to `WRP_YYYY/<core|focus_on>_<short_name>/`.
2. Enter every numeric finding from the report text, charts and tables in
   `published_figures.csv`, with page numbers.
3. Write one function per finding in `reproduce.py` and the same in `reproduce.R`,
   using the variable names and codes in `WRP_YYYY/WRP_YYYY_data_dictionary.csv`.
4. Run both scripts, then fill in the README: method notes, Gallup caveats, and a
   reason for any `DIFFERENT` finding.
5. Update `report_inventory.csv`.
