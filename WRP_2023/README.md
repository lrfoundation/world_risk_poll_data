# World Risk Poll 2023 (Wave 3)

The third World Risk Poll, with fieldwork in 2023. Its reports were published in 2024 as the *World Risk Poll 2024* reports, so look here for the data behind them. This folder holds the whole wave as one harmonised file, in three formats, with a data dictionary and notes.

| | |
| --- | --- |
| Wave | 3 |
| Fieldwork | 2023 |
| Respondents | 146,910 |
| Countries and areas | 142 |
| Variables | 325: the 37-variable harmonised block shared with every wave, then 288 from this wave's questionnaire |
| Reports | Four core reports (2024), published as *World Risk Poll 2024*, and two Focus On reports (2025 and 2026) ([below](#reports-from-this-wave)) |
| Methodology | [`lrf_wrp_2023_methods.pdf`](../lrf_wrp_2023_methods.pdf) |
| Licence | [CC BY-SA 4.0](../LICENSE) |

## Files

| File | What it is | Size |
| --- | --- | --- |
| [`WRP_2023.parquet`](WRP_2023.parquet) | Apache Parquet. The smallest download, and quick to load in Python, R or DuckDB | 12.9 MB |
| [`WRP_2023.sav`](WRP_2023.sav) | SPSS, with variable and value labels | 16.9 MB |
| [`WRP_2023.csv`](WRP_2023.csv) | CSV of numeric codes (UTF-8 with BOM). The labels are in the data dictionary | 100.8 MB |
| [`WRP_2023_data_dictionary.csv`](WRP_2023_data_dictionary.csv) | One row per variable: label, codes and their labels, coverage, how it was derived | 117 KB |
| [`WRP_2023_README.txt`](WRP_2023_README.txt) | The full notes on this wave and on comparing waves | |
| [`WRP_2023.zip`](WRP_2023.zip) | The five files above, in one download | 46.0 MB |

The three data files hold the same content.

## Before you analyse this wave

- **Household size** counts only residents aged 15 and over, not the whole household as in 2019, 2021 and 2025. Don't trend `HouseholdSize` across waves.
- **Resilience** is held on two scales, `resilience_index` (0 to 1) and `resilience_index_100` (0 to 100), with its four dimensions: individual, household, community and society.
- **Built from** `LRF_WAVE_3_WITH_INDICES_FOR_PUBLIC_RELEASE_10082024_v2.sav`, unchanged apart from the harmonised block at the front.

## Weights

Use `PROJWT`, the population projection weight, for anything that pools countries: global, regional or income-group figures. `WGT` is the within-country weight. Within one country `PROJWT` is proportional to `WGT`, so a country's figures are the same under either ([`reports/README.md`](../reports/README.md) sets out the conventions the reproductions follow).

## Comparing with other waves

The first 37 variables have the same names, codes and labels in every wave, so the four wave files stack directly. [`docs/CODEBOOK.md`](../docs/CODEBOOK.md) documents them, and [`examples/`](../examples/) shows the stacking in Python, R, SQL and Julia.

- For trends across all four waves, use `worry_score` and `experience_score`, which use the five risk sources asked the same way in every wave. `worry_score_core7` and `experience_score_core7` add traffic accidents and work, and trend from 2021.
- `worry_index_published` and `experience_index_published` are the figures LRF published for 2023. Quote them for 2023 on its own, but don't chart them against other waves: the item sets change, and 2025 changed how the worry index is scored.
- For a global trend, keep to the countries present in every wave you compare (142 in 2019, 121 in 2021, 142 in 2023, 140 in 2025). Otherwise part of the change is a change in which countries were asked.

## Reports from this wave

| Report | Type | Published | Reproduced in Python and R |
| --- | --- | --- | --- |
| [Resilience in a Changing World](https://www.lrfoundation.org.uk/sites/default/files/2024-06/World%20Risk%20Poll%20Report%202024%20Resilience%20in%20a%20Changing%20World_1.pdf) | Core | June 2024 | [`core_resilience_in_a_changing_world`](../reports/WRP_2023/core_resilience_in_a_changing_world/) |
| [A World of Waste: Risks and opportunities in household waste management](https://www.lrfoundation.org.uk/sites/default/files/2024-10/WRP24%20-%20Waste%20Report%201_2.pdf) | Core | September 2024 | [`core_a_world_of_waste`](../reports/WRP_2023/core_a_world_of_waste/) |
| [Engineering Safer Workplaces: Global trends in occupational safety and health](https://www.lrfoundation.org.uk/sites/default/files/2024-10/World%20Risk%20Poll%2024%20-%20OSH%20Report%201_0.pdf) | Core | October 2024 | [`core_engineering_safer_workplaces`](../reports/WRP_2023/core_engineering_safer_workplaces/) |
| [What the World Worries About: Global perceptions and experiences of risk and harm](https://www.lrfoundation.org.uk/sites/default/files/2024-11/World%20Risk%20Poll%202024%20Report%20%20-%20What%20the%20world%20worries%20about%20.pdf) | Core | November 2024 | [`core_what_the_world_worries_about`](../reports/WRP_2023/core_what_the_world_worries_about/) |
| [Focus On: Risk perceptions and experiences of ocean workers](https://www.lrfoundation.org.uk/sites/default/files/2025-08/wrp-2024-focus-on-ocean-workers-updated.pdf) | Focus On | June 2025 | [`focus_on_ocean_workers`](../reports/WRP_2023/focus_on_ocean_workers/) |
| [Focus On: Migration in a warming world](https://storage.googleapis.com/gsec_library_files/items/s0lbzCgoswPJmkgZhmI6/file/1f0dc7c0-6662-4914-85d8-558cc47900e9-Migration%20in%20a%20warming%20world.pdf) | Focus On | May 2026 | [`focus_on_migration_in_a_warming_world`](../reports/WRP_2023/focus_on_migration_in_a_warming_world/) |

*Migration in a warming world* is published in the [Global Safety Evidence Centre library](https://repo.gsec.org.uk) (DOI [10.60743/5ppn-nc25](https://doi.org/10.60743/5ppn-nc25)) rather than on the Lloyd's Register Foundation publications pages.

Across the six reports, of the 4,061 numbers checked, 3,629 match the report or come within a point, 28 differ (each listed, with its reason where known, in the report's README), and 404 need Gallup World Poll items that are not in this release. [`reports/REPRODUCTION_SUMMARY.md`](../reports/REPRODUCTION_SUMMARY.md) has the detail.

## Citing

See [`CITATION.cff`](../CITATION.cff) for the dataset, and the [methodology report](../lrf_wrp_2023_methods.pdf) for how the poll was run.
