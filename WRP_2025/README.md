# World Risk Poll 2025 (Wave 4)

The fourth World Risk Poll, with fieldwork in 2025. Its reports were published in 2026 as the *World Risk Poll 2026* reports, so look here for the data behind them. This folder holds the whole wave as one harmonised file, in three formats, with a data dictionary and notes.

For the full picture of this wave, with a summary of each report, its DOI and how to cite it, read [`RELEASE_NOTES.md`](RELEASE_NOTES.md).

| | |
| --- | --- |
| Wave | 4 |
| Fieldwork | 2025, as a module of the Gallup World Poll |
| Respondents | 143,459 adults aged 15 and older |
| Countries and territories | 140 |
| Interview mode | Face-to-face in 93 countries and territories, telephone in 46, and a self-administered web survey in one (China) |
| Variables | 228: the 37-variable harmonised block shared with every wave, then 191 from this wave's questionnaire |
| Reports | Five core reports, published as *World Risk Poll 2026* in June and October 2026 ([below](#reports-from-this-wave)) |
| Methodology | [`lrf_wrp_2025_methods.pdf`](../lrf_wrp_2025_methods.pdf), *World Risk Poll Reports 2026: Methodology* ([doi.org/10.60743/p021-zg62](https://doi.org/10.60743/p021-zg62)) |
| Licence | [CC BY-SA 4.0](../LICENSE) |

## Files

| File | What it is | Size |
| --- | --- | --- |
| [`WRP_2025.parquet`](WRP_2025.parquet) | Apache Parquet. The smallest download, and quick to load in Python, R or DuckDB | 7.1 MB |
| [`WRP_2025.sav`](WRP_2025.sav) | SPSS, with variable and value labels | 8.8 MB |
| [`WRP_2025.csv`](WRP_2025.csv) | CSV of numeric codes (UTF-8 with BOM). The labels are in the data dictionary | 65.7 MB |
| [`WRP_2025_data_dictionary.csv`](WRP_2025_data_dictionary.csv) | One row per variable: label, codes and their labels, coverage, how it was derived | 61 KB |
| [`WRP_2025_README.txt`](WRP_2025_README.txt) | The full notes on this wave and on comparing waves | |
| [`RELEASE_NOTES.md`](RELEASE_NOTES.md) | The final release of this wave: the reports, how closely they are reproduced, and how to cite them | |
| [`WRP_2025.zip`](WRP_2025.zip) | The data files, the data dictionary and `WRP_2025_README.txt`, in one download | 24.0 MB |

The three data files hold the same content, and are identical to the 2025 data on the [World Risk Poll website](https://wrp.lrfoundation.org.uk/world-risk-poll-data), including the correction to a subsample in China made on 2 September 2026.

## Before you analyse this wave

- **China.** The China sample came from an opt-in web panel, not the probability samples used everywhere else. Read its figures with that in mind (see the methodology report).
- **Worry index.** The published worry index for 2025 is a simple mean of ten items. Earlier waves published a Rasch-weighted index, so the two can't be compared. Use `worry_score` for trends.
- **Experience of harm.** LRF published no experience index for 2025, so `experience_index_published` is empty. `experience_score` and `experience_score_core7` fill the gap and trend across waves.
- **Resilience** is 0 to 100 in the source file. Here `resilience_index` is 0 to 1 and `resilience_index_100` is 0 to 100.
- **Gallup World Poll items.** Some report findings combine these questions with core Gallup World Poll items, such as wellbeing and mobile phone ownership, that are not in this release. They have to come from [Gallup](https://www.gallup.com/analytics/318875/global-research.aspx).
- **Built from** `LRF_WAVE4_WITH_INDICES_FOR_PUBLIC_RELEASE.sav`, unchanged apart from the harmonised block at the front.

## Weights and base

Use `PROJWT`, the population projection weight, for anything that pools countries: global, regional or income-group figures. It scales each country to its adult population. `WGT` is the within-country weight, and within one country `PROJWT` is proportional to it, so a country's figures are the same under either.

The reports follow Gallup's convention: "don't know" and "refused" stay in the denominator, and respondents who were not asked a question are left out ([`reports/README.md`](../reports/README.md)).

## Comparing with other waves

The first 37 variables have the same names, codes and labels in every wave, so the four wave files stack directly. [`docs/CODEBOOK.md`](../docs/CODEBOOK.md) documents them, and [`examples/`](../examples/) shows the stacking in Python, R, SQL and Julia.

- For trends across all four waves, use `worry_score` and `experience_score`. The `_core7` versions add traffic accidents and work, and trend from 2021.
- `worry_index_published` is the figure LRF published for 2025. Quote it for 2025 on its own, but don't chart it against earlier waves.
- For a global trend, keep to the countries present in every wave you compare (142 in 2019, 121 in 2021, 142 in 2023, 140 in 2025). Otherwise part of the change is a change in which countries were asked.

## Reports from this wave

| Report | Published | DOI | Reproduced in Python and R |
| --- | --- | --- | --- |
| [Alone together: The hidden consensus on climate change](https://www.lrfoundation.org.uk/sites/default/files/2026-09/wrp-report-2026-the-hidden-consensus-on-climate-change.pdf) | 23 June 2026 | [10.60743/d5zy-ec79](https://doi.org/10.60743/d5zy-ec79) | [`core_alone_together`](../reports/WRP_2025/core_alone_together/) |
| [The quiet hazards: How everyday risk shapes daily life](https://www.lrfoundation.org.uk/sites/default/files/2026-09/world-risk-poll-report-2026-how-everyday-risk-shapes-daily-life.pdf) | 23 June 2026 | [10.60743/9djc-t718](https://doi.org/10.60743/9djc-t718) | [`core_the_quiet_hazards`](../reports/WRP_2025/core_the_quiet_hazards/) |
| [A resilient life: How wellbeing shapes the capacity to cope](https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-resilience.pdf) | 13 October 2026 | [10.60743/sbwn-m411](https://doi.org/10.60743/sbwn-m411) | [`core_a_resilient_life`](../reports/WRP_2025/core_a_resilient_life/) |
| [From alert to agency: What turns warnings into action?](https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-early-warnings.pdf) | 13 October 2026 | [10.60743/yx1k-t541](https://doi.org/10.60743/yx1k-t541) | [`core_from_alert_to_agency`](../reports/WRP_2025/core_from_alert_to_agency/) |
| [After the storm: How disasters reshape resilience and trust](https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-after-the-storm.pdf) | 13 October 2026 | [10.60743/16n7-bn41](https://doi.org/10.60743/16n7-bn41) | [`core_after_the_storm`](../reports/WRP_2025/core_after_the_storm/) |

Across the five reports, of the 3,707 numbers checked, 2,815 match the report or come within a point, 12 differ (each listed, with its reason where known, in the report's README), and 880 need Gallup World Poll items that are not in this release. [`RELEASE_NOTES.md`](RELEASE_NOTES.md#reproducing-the-reports) breaks that down by report.

## Citing

See [`CITATION.cff`](../CITATION.cff) for the dataset. [`RELEASE_NOTES.md`](RELEASE_NOTES.md#how-to-cite) gives the Foundation's recommended citations for the methodology and each report.
