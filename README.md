# World Risk Poll Data

At Lloyd’s Register Foundation, we are committed to the principles of open and accessible data, as it gives the research we fund the best possible chance to have a positive impact on safety.

All World Risk Poll data is freely available to download and use (with attribution). The dataset currently includes data from the 2019, 2021, 2023 and 2025 polls (Waves 1 to 4). Data associated with future reports will be added to the dataset as and when they are published. We actively encourage third party reuse of this data for secondary analysis to create deeper insights.

With over 20 million datapoints, the World Risk Poll dataset can be challenging to work with for those who are not data specialists. However, with the interactive World Risk Poll Data Explorer, it is possible to easily identify global or regional trends from all respondents within and across the datasets, or drill down and perform highly focused comparisons at country or demographic levels.

## Files in this repository

### Poll data

Each wave has its own folder containing the harmonised single-wave file in three identical formats (SPSS `.sav` with labels, Apache Parquet, and CSV of numeric codes), a data dictionary, a per-wave README, and a `.zip` bundling all of the above. The first 37 variables in every wave are a harmonised block with matching names, codes and labels, so the waves stack directly.

| Folder | Wave | Fieldwork | Respondents | Countries and areas |
| --- | --- | --- | --- | --- |
| `WRP_2019/` | Wave 1 | 2019 | 154,195 | 142 |
| `WRP_2021/` | Wave 2 | 2021 | 125,911 | 121 |
| `WRP_2023/` | Wave 3 | 2023 | 146,910 | 142 |
| `WRP_2025/` | Wave 4 | 2025 | 143,459 | 140 |

Per folder (`YYYY` = 2019, 2021, 2023, 2025):

| File | Description |
| --- | --- |
| `WRP_YYYY.sav` | SPSS file with variable and value labels |
| `WRP_YYYY.parquet` | Apache Parquet, same content |
| `WRP_YYYY.csv` | CSV of numeric codes, UTF-8 with BOM |
| `WRP_YYYY_data_dictionary.csv` | One row per variable: label, codes, coverage, derivation |
| `WRP_YYYY_README.txt` | Notes on the wave and cross-wave comparability |
| `WRP_YYYY.zip` | The five files above, bundled |

### Methodology reports

| File | Description |
| --- | --- |
| `lrf_wrp_2019_methods.pdf` | Methodology report for the 2019 World Risk Poll |
| `lrf_wrp_2021_methods.pdf` | Methodology report for the 2021 World Risk Poll |
| `lrf_wrp_2023_methods.pdf` | Methodology report for the 2023 World Risk Poll |
| `lrf_wrp_2025_methods.pdf` | Methodology report for the 2025 World Risk Poll |

Note on trends: country coverage differs by wave, and some questions and published indices are not comparable across waves. See any wave's `_README.txt` for details before combining waves.

## Getting started

- [`docs/CODEBOOK.md`](docs/CODEBOOK.md) — the 37-variable harmonised block that lets the four waves stack into one trend file, documented once with value labels and cross-wave comparability notes.
- `examples/quickstart.*` — load one wave, stack all four into a pooled weighted trend, and trend one question that sits outside the harmonised block (climate-change threat). Same worked example in [Python](examples/quickstart.py), [R](examples/quickstart.R), [SQL / DuckDB](examples/quickstart.sql) and [Julia](examples/quickstart.jl).

## More information

For more information about Lloyd’s Register Foundation, please visit lrfoundation.org.uk.

To learn more about the World Risk Poll, please visit wrp.lrfoundation.org.uk.

This work is licensed under [CC BY-SA 4.0](LICENSE). See [`CITATION.cff`](CITATION.cff) for how to cite this dataset.
