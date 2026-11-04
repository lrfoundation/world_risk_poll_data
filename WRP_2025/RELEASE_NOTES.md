# World Risk Poll 2025 (Wave 4): final release

This is the final release of the fourth wave of the Lloyd's Register Foundation World Risk Poll. With the
launch of *From alert to agency*, *A resilient life* and *After the storm* on 13 October 2026, all five
*World Risk Poll 2026* reports built on the 2025 data have been published. Every number in them is recomputed,
in Python and in R, from the public data in this repository, apart from the findings that need Gallup World
Poll data outside this release, which are coded and flagged.

The data files themselves have not changed since the first 2025 release on 1 September 2026. What this
release adds is the full set of reports, the code that reproduces them, and this summary of everything
needed to use the wave.

## At a glance

| | |
| --- | --- |
| Wave | 4 (the fourth edition of the Poll) |
| Fieldwork | 2025, as a module of the Gallup World Poll |
| Interviews | 143,459 adults aged 15 and older |
| Coverage | 140 countries and territories |
| Interview mode | Face-to-face in 93 countries and territories, telephone in 46, self-administered web survey in one (China) |
| Variables | 228: a 37-variable harmonised block shared with every wave, then 191 wave-specific variables |
| Reports | 5 core reports, published as *World Risk Poll 2026* (June and October 2026) |
| Methodology | [`lrf_wrp_2025_methods.pdf`](../lrf_wrp_2025_methods.pdf), *World Risk Poll Reports 2026: Methodology* (https://doi.org/10.60743/p021-zg62) |
| Licence | [CC BY-SA 4.0](../LICENSE) |

## The data

| File | Description |
| --- | --- |
| [`WRP_2025.sav`](WRP_2025.sav) | SPSS file with variable and value labels |
| [`WRP_2025.parquet`](WRP_2025.parquet) | Apache Parquet, same content |
| [`WRP_2025.csv`](WRP_2025.csv) | CSV of numeric codes, UTF-8 with BOM |
| [`WRP_2025_data_dictionary.csv`](WRP_2025_data_dictionary.csv) | One row per variable: label, codes, coverage, derivation |
| [`WRP_2025_README.txt`](WRP_2025_README.txt) | Notes on the wave and on cross-wave comparability |
| [`WRP_2025.zip`](WRP_2025.zip) | The five files above, bundled |

The files are byte-for-byte identical to the 2025 data on the
[World Risk Poll website](https://wrp.lrfoundation.org.uk/world-risk-poll-data), which includes the
correction to a subsample in China that the Foundation made on 2 September 2026. That correction does not
change any published finding.

A few things are worth knowing before analysing this wave:

- **Weights.** Use `PROJWT` (the projection weight) for anything that pools countries, such as global,
  regional or income-group figures; it scales each country to its adult population. Within a single country
  `PROJWT` is proportional to `WGT`, so country figures are the same under either.
- **Base.** Gallup's convention, which the reports follow, keeps "don't know" and "refused" in the
  denominator. Respondents who were not asked a question are left out.
- **China.** The China sample was collected by an opt-in web panel rather than the probability samples used
  everywhere else, and should be read with that in mind (see the methodology report).
- **Indices.** The published Worry Index for 2025 is a simple mean of ten items, so it is not comparable with
  the Rasch-weighted indices of earlier waves. No Experience of Harm Index was published for 2025;
  `experience_score` and `experience_score_core7` fill that gap and trend across waves. The Resilience Index
  is held on two scales: `resilience_index` (0 to 1) and `resilience_index_100` (0 to 100).
- **Trends.** The first 37 variables carry the same names, codes and labels in every wave, so the four wave
  files stack directly. Country coverage differs by wave (142, 121, 142 and 140), so restrict a global trend
  to the countries present in every wave being compared. [`docs/CODEBOOK.md`](../docs/CODEBOOK.md) documents
  the harmonised block, and [`examples/`](../examples/) shows the stacking in Python, R, SQL and Julia.
- **Gallup World Poll items.** Some report findings combine World Risk Poll questions with core Gallup World
  Poll items (wellbeing, mobile phone ownership and similar) that are not in this public release. They must
  be obtained from [Gallup](https://www.gallup.com/analytics/318875/global-research.aspx).

## The reports

Five core reports draw on the 2025 data. The first two, published in June, return to the Poll's long-running
questions on climate change and everyday harm. The last three, published together in October, form a
resilience series: one sets out how resilience is distributed and what strengthens it, one looks at the hours
before a disaster, and one at the years after it.

### Alone together: The hidden consensus on climate change

Published 23 June 2026 (updated 2 September 2026). DOI: https://doi.org/10.60743/d5zy-ec79 ·
[PDF](https://www.lrfoundation.org.uk/sites/default/files/2026-09/wrp-report-2026-the-hidden-consensus-on-climate-change.pdf) ·
[Reproduction](../reports/WRP_2025/core_alone_together/)

Concern about climate change is at its highest point in the Poll's history: three in four adults (75%) see
it as a very or somewhat serious threat to their country over the next 20 years. What is new in 2025 is a
"second-order" question, developed with the UNDP Human Development Report Office, asking how seriously people
think others in their country take the threat. Most people's answers line up, but where they do not, people
tend to underestimate those around them: 22% are more concerned than they think others are, twice the share
who think the reverse (11%). Whilst 40% of adults see climate change as a very serious threat, only 31% believe
most people in their country do, and the gap is widest in high-income countries (49% against 20%). The report
sets out what this hidden consensus means for risk communication and climate policy.

### The quiet hazards: How everyday risk shapes daily life

Published 23 June 2026 (updated 2 September 2026). DOI: https://doi.org/10.60743/9djc-t718 ·
[PDF](https://www.lrfoundation.org.uk/sites/default/files/2026-09/world-risk-poll-report-2026-how-everyday-risk-shapes-daily-life.pdf) ·
[Reproduction](../reports/WRP_2025/core_the_quiet_hazards/)

This report turns to the everyday risks that touch the most lives. Road-related accidents are the risk people
most often name as the greatest threat to their safety (14%), but the more telling movements are in harm:
personal harm from food (14%) and from drinking water (13%) are the highest the Poll has recorded, whilst harm
at work among the current workforce has fallen from 19% in 2021 to 16%. The 2025 Poll also asked about harm
from wildfires and from the air people breathe; 12% of adults had been harmed by the air they breathe and 8%
by wildfires.

### A resilient life: How wellbeing shapes the capacity to cope

Published 13 October 2026. DOI: https://doi.org/10.60743/sbwn-m411 ·
[PDF](https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-resilience.pdf) ·
[Reproduction](../reports/WRP_2025/core_a_resilient_life/)

The third edition of the Resilience Index combines individual, household, community and societal resilience
into one score. Globally it is stable at 57 out of 100, but the headline hides two opposing movements:
individual resilience has fallen for a second consecutive edition, from 46 in 2021 to 42, its lowest since the
Index began, whilst societal resilience has reached its highest level yet (66). Africa's four main regions
recorded the largest gains of any since 2023. The report pairs the Index with Gallup's wellbeing measures for
the same respondents, which are not in the public release, so the findings that rely on them are flagged
rather than reproduced.

### From alert to agency: What turns warnings into action?

Published 13 October 2026. DOI: https://doi.org/10.60743/yx1k-t541 ·
[PDF](https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-early-warnings.pdf) ·
[Reproduction](../reports/WRP_2025/core_from_alert_to_agency/)

One in five adults (20%) worldwide has been impacted by a disaster in the past five years, and four in five
of them (80%) received an advance warning. Coverage is uneven, however: fewer than two-thirds of those impacted
in low-income countries were warned (64%), against 84% in upper-middle- and high-income countries. The report's
central question is what happens next, because a warning received is not a warning acted upon. The ability to
act rises with every additional channel that delivers the warning, from 37% of those warned once to 64% of
those warned three times. The Poll's early warning data also feed the UN Early Warnings for All dashboard.

### After the storm: How disasters reshape resilience and trust

Published 13 October 2026. DOI: https://doi.org/10.60743/16n7-bn41 ·
[PDF](https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-after-the-storm.pdf) ·
[Reproduction](../reports/WRP_2025/core_after_the_storm/)

Unlike the other reports, this one does not give a global picture. It follows seven disasters that struck
between the 2021 and 2023 editions (earthquakes in Morocco, Türkiye and Ecuador, cyclones in Mozambique and New
Zealand, and floods in Pakistan and South Africa) and compares the regions each struck with the rest of the
country, using the 2021 and 2023 data at the sub-national level. Four of the cases are followed into 2025.
National averages hide much of what happened: Türkiye's Resilience Index score was 51 in both 2021 and 2023,
whilst the earthquake regions fell three points and the rest of the country rose one. Trust can move the other
way, too. In Mozambique, the share who felt the government cared about them "a lot" rose 20 percentage points
further in the cyclone-hit provinces than in the rest of the country. These are descriptive differences between
regions, not measured effects of the disasters, and the report is careful to say so.

## Reproducing the reports

Every report has a folder under [`reports/WRP_2025/`](../reports/WRP_2025/) with the report's published
figures, a Python and an R script that recompute each of them from this data, and a generated `RESULTS.md`
comparing the three. [`reports/README.md`](../reports/README.md) explains the conventions.

| Report | Numbers checked | Match or within a point | Differ | Need Gallup data |
| --- | --- | --- | --- | --- |
| Alone together | 258 | 244 | 2 | 12 |
| The quiet hazards | 930 | 724 | 7 | 199 |
| A resilient life | 471 | 377 | 1 | 93 |
| From alert to agency | 541 | 504 | 0 | 37 |
| After the storm | 1,507 | 966 | 2 | 539 |
| **All five reports** | **3,707** | **2,815** | **12** | **880** |

Each number that differs is explained in its report's README; many are errors in the report itself, such as
text that contradicts its own chart. The findings that need Gallup World Poll data are coded
and documented, and run if you have licensed the items (set `GALLUP_WP_PATH`; see the reports README). The
Python and R scripts agree on every value.

```
pip install -r reports/requirements.txt
Rscript -e 'install.packages(c("arrow", "dplyr"))'
Rscript reports/WRP_2025/core_after_the_storm/reproduce.R
python reports/WRP_2025/core_after_the_storm/reproduce.py
```

## What has changed since the first 2025 release

The first 2025 release (tag [`2025`](https://github.com/lrfoundation/world_risk_poll_data/releases/tag/2025),
1 September 2026) added the wave 4 data. Since then:

- The 2019, 2021 and 2023 data were rebuilt in the same harmonised format, so all four waves stack directly
  ([#2](https://github.com/lrfoundation/world_risk_poll_data/pull/2)).
- A licence, a citation file, the harmonised-block codebook and quickstart examples in Python, R, SQL and Julia
  were added ([#3](https://github.com/lrfoundation/world_risk_poll_data/pull/3)).
- Every World Risk Poll core and Focus On report from 2019 onwards is now reproduced in Python and R
  ([#4](https://github.com/lrfoundation/world_risk_poll_data/pull/4),
  [#5](https://github.com/lrfoundation/world_risk_poll_data/pull/5)), and this release brings the last three
  2025 reports in line with their published versions.
- The README links the [World Risk Poll Data Explorer](https://tools.gsec.org.uk/wrp-explorer.html)
  ([#6](https://github.com/lrfoundation/world_risk_poll_data/pull/6)).

The 2025 data files are unchanged.

## How to cite

The dataset: see [`CITATION.cff`](../CITATION.cff). For the methodology and the reports, the Foundation's
recommended citations are:

- Lloyd's Register Foundation. (2026). *World Risk Poll Reports 2026: Methodology*. Lloyd's Register
  Foundation. https://doi.org/10.60743/p021-zg62
- Lloyd's Register Foundation. (2026). *World Risk Poll 2026 Report. Alone together: The hidden consensus on
  climate change*. Lloyd's Register Foundation. https://doi.org/10.60743/d5zy-ec79
- Lloyd's Register Foundation. (2026). *World Risk Poll 2026 Report. The quiet hazards: How everyday risk
  shapes daily life*. Lloyd's Register Foundation. https://doi.org/10.60743/9djc-t718
- Lloyd's Register Foundation. (2026). *World Risk Poll 2026 Report. A resilient life: How wellbeing shapes the
  capacity to cope*. Lloyd's Register Foundation. https://doi.org/10.60743/sbwn-m411
- Lloyd's Register Foundation. (2026). *World Risk Poll 2026 Report. From alert to agency: What turns warnings
  into action?* Lloyd's Register Foundation. https://doi.org/10.60743/yx1k-t541
- Lloyd's Register Foundation. (2026). *World Risk Poll 2026 Report. After the storm: How disasters reshape
  resilience and trust*. Lloyd's Register Foundation. https://doi.org/10.60743/16n7-bn41

## More information

- World Risk Poll: https://wrp.lrfoundation.org.uk/
- World Risk Poll Data Explorer: https://tools.gsec.org.uk/wrp-explorer.html
- Lloyd's Register Foundation: https://www.lrfoundation.org.uk/
