# World Risk Poll 2021 (Wave 2)

The second World Risk Poll, with fieldwork in 2021. This folder holds the whole wave as one harmonised file, in three formats, with a data dictionary and notes.

| | |
| --- | --- |
| Wave | 2 |
| Fieldwork | 2021 |
| Respondents | 125,911 |
| Countries and areas | 121 |
| Variables | 270: the 37-variable harmonised block shared with every wave, then 233 from this wave's questionnaire |
| Reports | Four core reports (2022 to 2023) and four Focus On reports (2023), published as *World Risk Poll 2021* ([below](#reports-from-this-wave)) |
| Methodology | [`lrf_wrp_2021_methods.pdf`](../lrf_wrp_2021_methods.pdf) |
| Licence | [CC BY-SA 4.0](../LICENSE) |

## Files

| File | What it is | Size |
| --- | --- | --- |
| [`WRP_2021.parquet`](WRP_2021.parquet) | Apache Parquet. The smallest download, and quick to load in Python, R or DuckDB | 7.1 MB |
| [`WRP_2021.sav`](WRP_2021.sav) | SPSS, with variable and value labels | 8.8 MB |
| [`WRP_2021.csv`](WRP_2021.csv) | CSV of numeric codes (UTF-8 with BOM). The labels are in the data dictionary | 70.7 MB |
| [`WRP_2021_data_dictionary.csv`](WRP_2021_data_dictionary.csv) | One row per variable: label, codes and their labels, coverage, how it was derived | 99 KB |
| [`WRP_2021_README.txt`](WRP_2021_README.txt) | The full notes on this wave and on comparing waves | |
| [`WRP_2021.zip`](WRP_2021.zip) | The five files above, in one download | 24.2 MB |

The three data files hold the same content.

## Before you analyse this wave

- **Resilience starts here.** 2021 is the first wave to measure resilience: `resilience_index` (0 to 1), `resilience_index_100` (0 to 100) and its four dimensions, individual, household, community and society.
- **Jamaica.** For its 505 respondents, the six-category `Urbanicity` and the four resilience dimensions are missing. `Urbanicity2` and `resilience_index` do cover them.
- **New risk sources.** Worry about traffic accidents and about work, and harm from them, are asked from 2021. `worry_score_core7` and `experience_score_core7` include them, so they trend from 2021 to 2025 only.
- **Experience of harm** now offers "someone you know" as well as the respondent. `experience_score` counts both; `experience_score_self` counts only the respondent, and is comparable from 2021 to 2025.
- **Household size** is the total number of people in the household, as in 2019 and 2025. 2023 counted only residents aged 15 and over, so don't trend it.
- **Built from** the 2021 rows of `21_wrp.sav`, with the published wave 2 worry and experience indices and the resilience scores merged in from the trend files. `21_wrp.sav` also holds the 2019 rows, which are in [`WRP_2019/`](../WRP_2019/) instead.

## Weights

Use `PROJWT`, the population projection weight, for anything that pools countries: global, regional or income-group figures. `WGT` is the within-country weight. Within one country `PROJWT` is proportional to `WGT`, so a country's figures are the same under either ([`reports/README.md`](../reports/README.md) sets out the conventions the reproductions follow).

## Comparing with other waves

The first 37 variables have the same names, codes and labels in every wave, so the four wave files stack directly. [`docs/CODEBOOK.md`](../docs/CODEBOOK.md) documents them, and [`examples/`](../examples/) shows the stacking in Python, R, SQL and Julia.

- For trends across all four waves, use `worry_score` and `experience_score`, which use the five risk sources asked the same way in every wave.
- `worry_index_published` and `experience_index_published` are the figures LRF published for 2021. Quote them for 2021 on its own, but don't chart them against other waves: the item sets change, and 2025 changed how the worry index is scored.
- For a global trend, keep to the countries present in every wave you compare (142 in 2019, 121 in 2021, 142 in 2023, 140 in 2025). Otherwise part of the change is a change in which countries were asked. 2021 has the fewest.

## Reports from this wave

| Report | Type | Published | Reproduced in Python and R |
| --- | --- | --- | --- |
| [A Changed World? Perceptions and experiences of risk in the Covid age](https://www.lrfoundation.org.uk/sites/default/files/2024-06/LRF_2021_report_risk-in-the-covid-age_online_version_2.pdf) | Core | July 2022 | [`core_a_changed_world`](../reports/WRP_2021/core_a_changed_world/) |
| [A Resilient World? Understanding vulnerability in a changing climate](https://www.lrfoundation.org.uk/sites/default/files/2024-06/LRF_2021_report2-resilience_online_version.pdf) | Core | September 2022 | [`core_a_resilient_world`](../reports/WRP_2021/core_a_resilient_world/) |
| [A Digital World: Perceptions of risk from AI and misuse of personal data](https://www.lrfoundation.org.uk/sites/default/files/2024-04/LRF_2021_report_a-digital-world-ai-and-personal-data_online_version_1.pdf) | Core | November 2022 | [`core_a_digital_world`](../reports/WRP_2021/core_a_digital_world/) |
| [Safe at Work? Global experiences of violence and harassment](https://www.lrfoundation.org.uk/sites/default/files/2024-06/LRF_2021_report_safe-at-work.pdf) | Core | January 2023 | [`core_safe_at_work`](../reports/WRP_2021/core_safe_at_work/) |
| [Focus On: Risk and Gender](https://www.lrfoundation.org.uk/sites/default/files/2024-04/WRP2021_FocusOn_Gender_0.pdf) | Focus On | March 2023 | [`focus_on_risk_and_gender`](../reports/WRP_2021/focus_on_risk_and_gender/) |
| [Focus On: The impact of income and migration on violence and harassment at work](https://www.lrfoundation.org.uk/sites/default/files/2024-05/WRP_FocusOn_VH%20%281%29_1%20%282%29.pdf) | Focus On | April 2023 | [`focus_on_violence_and_harassment_income_migration`](../reports/WRP_2021/focus_on_violence_and_harassment_income_migration/) |
| [Focus On: Fossil fuel dependency and perceptions of climate change](https://www.lrfoundation.org.uk/sites/default/files/2024-05/WRP_FocusOn_Climate%20%281%29.pdf) | Focus On | June 2023 | [`focus_on_fossil_fuels_and_climate_change`](../reports/WRP_2021/focus_on_fossil_fuels_and_climate_change/) |
| [Focus On: Critical infrastructure resilience and perceptions of disaster preparedness](https://www.lrfoundation.org.uk/sites/default/files/2024-05/Focus-On-Resilience.pdf) | Focus On | October 2023 | [`focus_on_critical_infrastructure`](../reports/WRP_2021/focus_on_critical_infrastructure/) |

Across the eight reports, of the 3,679 numbers checked, 3,213 match the report or come within a point, 37 differ (each listed, with its reason where known, in the report's README), and 429 need Gallup World Poll items that are not in this release. [`reports/REPRODUCTION_SUMMARY.md`](../reports/REPRODUCTION_SUMMARY.md) has the detail.

## Citing

See [`CITATION.cff`](../CITATION.cff) for the dataset, and the [methodology report](../lrf_wrp_2021_methods.pdf) for how the poll was run.
