# <Report title>

Template for a report folder. Copy it to `reports/WRP_YYYY/<core|focus_on>_<short_name>/`
(`WRP_YYYY` is the fieldwork year of the data the report uses) and replace every
placeholder. The example figures in `published_figures.csv` are placeholders, not
published values.

- **Report:** <full title>, Lloyd's Register Foundation, <publication date>
- **PDF:** <link to the report on lrfoundation.org.uk>
- **Data:** `WRP_YYYY/WRP_YYYY.parquet` (World Risk Poll <year>, wave <n>)

## What is reproduced

<One or two sentences: which sections, charts and tables; how many findings.>

## Method notes

- **Weights:** <e.g. PROJWT for global and regional figures; country figures are
  unaffected by the choice between PROJWT and WGT>
- **Base:** <e.g. all respondents, DK/refused included, unless stated>
- **Countries:** <e.g. all 121 countries in the wave; or the subset the report uses>
- **Groupings:** <e.g. GlobalRegion, CountryIncomeLevel, Gender, AgeGroups3>

## Gallup World Poll data

<Either "Every finding uses public World Risk Poll data." or a list of the findings
that need Gallup World Poll items, which items, and why. Those items are not in this
release and must be licensed from Gallup directly; see `reports/README.md`.>

## Findings that do not match

<Every finding marked DIFFERENT in RESULTS.md, with the reason if known.>

## Run

```
python reports/WRP_YYYY/<folder>/reproduce.py
Rscript reports/WRP_YYYY/<folder>/reproduce.R
```
