# Reproducing the World Risk Poll reports

This folder re-creates the findings of every World Risk Poll core report and
Focus On report from the public data in this repository. Each report has its own
folder with Python and R scripts, the report's published figures, and a
generated comparison of published and reproduced values.

## Reports

All 16 World Risk Poll core and Focus On reports published up to September 2026 are
reproduced, one folder per report inside one folder per poll wave:

| Wave | Reports |
| --- | --- |
| [`WRP_2019/`](WRP_2019/README.md) | The 2019 full report |
| [`WRP_2021/`](WRP_2021/README.md) | 4 core reports and 4 Focus On reports |
| [`WRP_2023/`](WRP_2023/README.md) | 4 core reports (the *World Risk Poll 2024* reports) and 1 Focus On report |
| [`WRP_2025/`](WRP_2025/README.md) | 2 core reports (the *World Risk Poll 2026* reports) |

Across the 16 reports, 11,131 published numbers are checked. 10,060 of them (90%)
match or come within a point. 114 differ, and each one is explained in its report's
README; many are errors in the report itself. 956 need Gallup World Poll data that is
not public, and 1 needs a safety index that is no longer published. The Python and R
scripts agree on every value.
[`REPRODUCTION_SUMMARY.md`](REPRODUCTION_SUMMARY.md) has the result for every report,
and [`report_inventory.csv`](report_inventory.csv) lists each report with its PDF link.

## Quick start

From the repository root:

```
pip install -r reports/requirements.txt           # pandas, pyarrow, statsmodels, openpyxl
Rscript -e 'install.packages(c("arrow", "dplyr"))' # for the R scripts
python reports/external/fetch_external.py          # optional: non-poll data that is not committed

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
  external/            public non-poll data some reports use (World Bank indicators and
                       similar), named <report_folder>__<source>.csv, plus
                       fetch_external.py for sources whose licence does not allow
                       committing them; see external/README.md
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
- **Regions and income groups in trends.** Several reports compare waves using each
  country's region and income group in the latest wave, and the scripts do the same
  where that is what reproduces the report. `GlobalRegion` is the same in every wave
  for every country except Iran: Middle East in 2019 and 2021, Southern Asia in 2023.
- **Rounding.** Some reports compute gaps, sums or ratios from already-rounded
  percentages. Where that is what reproduces the report, the script does the same and
  the report's README says so.
- **Statuses.** Each finding in a `RESULTS.md` has one of these statuses:
  - `MATCH`: the reproduced value rounds to the published figure.
  - `WITHIN_TOLERANCE`: within the row's `tolerance` (default ±1 point, to allow for
    rounding in the published charts), but not an exact match.
  - `DIFFERENT`: further off. These stay in the table, and every one has a reason (or
    "not explained") in the report's README. Many are errors in the report itself,
    such as swapped chart labels or text that contradicts its own chart.
  - `GALLUP_ONLY`: needs Gallup World Poll data that is not public (see below).
  - `EXTERNAL_ONLY`: needs non-poll data that is not committed. Run
    `reports/external/fetch_external.py` to download it.

## `published_figures.csv`

| Column | Meaning |
| --- | --- |
| `finding_id` | `X..` for numbers in the text, `C<chapter>_<n>_<key>` for chart values and `T<chapter>_<n>_<key>` for table values, where the key is readable (`women_very`, `high_income`, `KEN`). A function that returns several values (a dict in Python, a named vector in R) fills `<id>_<key>` |
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
