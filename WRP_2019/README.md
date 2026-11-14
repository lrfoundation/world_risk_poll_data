# World Risk Poll 2019 (Wave 1)

The first World Risk Poll, with fieldwork in 2019. This folder holds the whole wave as one harmonised file, in three formats, with a data dictionary and notes.

| | |
| --- | --- |
| Wave | 1 |
| Fieldwork | 2019 |
| Respondents | 154,195 |
| Countries and areas | 142 |
| Variables | 245: the 37-variable harmonised block shared with every wave, then 208 from this wave's questionnaire |
| Reports | One full report, published in 2020 ([below](#reports-from-this-wave)) |
| Methodology | [`lrf_wrp_2019_methods.pdf`](../lrf_wrp_2019_methods.pdf) |
| Licence | [CC BY-SA 4.0](../LICENSE) |

## Files

| File | What it is | Size |
| --- | --- | --- |
| [`WRP_2019.parquet`](WRP_2019.parquet) | Apache Parquet. The smallest download, and quick to load in Python, R or DuckDB | 10.3 MB |
| [`WRP_2019.sav`](WRP_2019.sav) | SPSS, with variable and value labels | 14.6 MB |
| [`WRP_2019.csv`](WRP_2019.csv) | CSV of numeric codes (UTF-8 with BOM). The labels are in the data dictionary | 73.8 MB |
| [`WRP_2019_data_dictionary.csv`](WRP_2019_data_dictionary.csv) | One row per variable: label, codes and their labels, coverage, how it was derived | 67 KB |
| [`WRP_2019_README.txt`](WRP_2019_README.txt) | The full notes on this wave and on comparing waves | |
| [`WRP_2019.zip`](WRP_2019.zip) | The five files above, in one download | 38.1 MB |

The three data files hold the same content.

## Before you analyse this wave

- **No resilience.** Resilience was first measured in 2021, so every `resilience_*` field is empty here.
- **Different risk sources.** Worry about traffic accidents and about work, and harm from those two, were not asked in 2019. Worry about electrical power lines and about household appliances was asked in 2019 only.
- **Experience of harm.** The 2019 question asked only whether the respondent had been harmed. From 2021 it also offers "someone you know". `experience_score` is the definition LRF uses to trend the series; `experience_score_self` is the strictly personal one, comparable from 2021 only.
- **Climate change.** The question is `L5` here and `WP20719` in later waves, and in 2019 it asked about the threat "to people in [country]". The [codebook](../docs/CODEBOOK.md#questions-outside-the-harmonised-block) has the mapping, and [`examples/`](../examples/) trends it across all four waves.
- **Household size** is the total number of people in the household, as in 2021 and 2025. 2023 counted only residents aged 15 and over, so don't trend it.
- **Built from** `19_wrp.sav`, with `Age`, `WP5` and the projection weight `PROJWT` merged in on `WPID_RANDOM`. `PROJWT` was not in the original 2019 file.

## Weights

Use `PROJWT`, the population projection weight, for anything that pools countries: global, regional or income-group figures. `WGT` is the within-country weight. Within one country `PROJWT` is proportional to `WGT`, so a country's figures are the same under either ([`reports/README.md`](../reports/README.md) sets out the conventions the reproductions follow).

## Comparing with other waves

The first 37 variables have the same names, codes and labels in every wave, so the four wave files stack directly. [`docs/CODEBOOK.md`](../docs/CODEBOOK.md) documents them.

- For trends, use `worry_score` and `experience_score`, which use the five risk sources asked the same way in every wave.
- `worry_index_published` and `experience_index_published` are the figures LRF published for 2019. Quote them for 2019 on its own, but don't chart them against other waves: the item sets change between waves.
- For a global trend, keep to the countries present in every wave you compare (142 in 2019, 121 in 2021, 142 in 2023, 140 in 2025). Otherwise part of the change is a change in which countries were asked.

## Reports from this wave

| Report | Published | Reproduced in Python and R |
| --- | --- | --- |
| [The Lloyd's Register Foundation World Risk Poll: Full report and analysis of the 2019 poll](https://www.lrfoundation.org.uk/sites/default/files/2024-11/LRF_WorldRiskReport_Book_03.03.22%20Small_0.pdf) | 2020 | [`core_world_risk_poll_2019`](../reports/WRP_2019/core_world_risk_poll_2019/) |

Of the 2,432 numbers checked, 2,302 match the report or come within a point, 41 differ (each listed, with its reason where known, in the report's README), 88 need Gallup World Poll items that are not in this release, and 1 needs outside data. [`reports/REPRODUCTION_SUMMARY.md`](../reports/REPRODUCTION_SUMMARY.md) has the detail.

## Citing

See [`CITATION.cff`](../CITATION.cff) for the dataset, and the [methodology report](../lrf_wrp_2019_methods.pdf) for how the poll was run.
