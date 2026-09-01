# Codebook: the harmonised block

Every wave file (`WRP_2019`, `WRP_2021`, `WRP_2023`, `WRP_2025`) starts with
the same 37 variables, in the same order, with the same names, codes and
value labels. This is what lets the four wave files stack into a single
trend file — concatenate rows on these columns and you have a pooled
2019–2025 dataset. Everything after variable 37 in each file is that wave's
own questionnaire content and does not line up column-for-column across
waves; consult the wave's own `_data_dictionary.csv` for that part.

This page documents the harmonised block once instead of repeating it in
each wave's `_README.txt`. For wave-specific quirks (what wasn't asked that
year, definition changes, source files), see:

- [`WRP_2019/WRP_2019_README.txt`](../WRP_2019/WRP_2019_README.txt)
- [`WRP_2021/WRP_2021_README.txt`](../WRP_2021/WRP_2021_README.txt)
- [`WRP_2023/WRP_2023_README.txt`](../WRP_2023/WRP_2023_README.txt)
- [`WRP_2025/WRP_2025_README.txt`](../WRP_2025/WRP_2025_README.txt)

## Identifiers and sample

| # | Variable | Label | Notes |
| - | --- | --- | --- |
| 1 | `WPID_RANDOM` | Random unique case ID | Unique within a wave, not across waves |
| 2 | `Wave` | World Risk Poll wave | 1 = 2019, 2 = 2021, 3 = 2023, 4 = 2025 |
| 3 | `Year` | Year of fieldwork | |
| 4 | `WP5` | Gallup country code | |
| 5 | `Country` | Country/area name | String |
| 6 | `COUNTRY_ISO2` | Country ISO alpha-2 code | String |
| 7 | `COUNTRY_ISO3` | Country ISO alpha-3 code | String |
| 8 | `GlobalRegion` | Global region (World Risk Poll report definition) | See value labels below |
| 9 | `CountryIncomeLevel` | Country income group at time of fieldwork | World Bank classification, contemporaneous with each wave's fieldwork, not restated retrospectively |
| 10 | `WGT` | Within-country survey weight | As supplied |
| 11 | `PROJWT` | Population projection weight | For single-year or time-series population-weighted analysis. In `WRP_2019`, merged in from `PROJWT_2019` on `WPID_RANDOM`; not present in the original 2019 source file |

## Demographics

| # | Variable | Label | Notes |
| - | --- | --- | --- |
| 12 | `Age` | Age in years | |
| 13 | `AgeGroups3` | Age, 3 bands | 15-29 / 30-49 / 50+ |
| 14 | `AgeGroups4` | Age, 4 bands | 15-29 / 30-49 / 50-64 / 65+ |
| 15 | `AgeGroups5` | Age, 5 bands | 15-24 / 25-34 / 35-49 / 50-64 / 65+ |
| 16 | `Gender` | Gender | Male / Female |
| 17 | `Education` | Education level | Primary or less / Secondary / Tertiary / DK-Refused |
| 18 | `Urbanicity` | Urban/rural, 6 categories | |
| 19 | `Urbanicity2` | Urban/rural, 2 categories | Rural area or small town / Large city or suburb |
| 20 | `EMP_2010` | Employment status | |
| 21 | `INCOME_5` | Per capita income quintile | Poorest 20% ... Richest 20% |
| 22 | `HouseholdSize` | Household size | **Not comparable across all waves** — 2023 counts residents aged 15+, 2019/2021/2025 count the whole household. Don't trend it. |
| 23 | `ChildrenInHousehold` | Children under 15 in household | 0 / 1 / 2 / 3 / 4 / 5 or more / DK-Refused |

## Worry and experience scores

These are computed, not asked directly — derived the same way in every wave
from the risk-source items each wave has in common, so they're the columns
to use for a trend line. `worry_index_published` /
`experience_index_published` are what LRF actually put in each wave's
report; keep those for quoting a single wave's headline figure, but don't
chart them against each other — the item sets and, from wave 4, the scoring
method itself change between waves.

| # | Variable | Label | Comparable across |
| - | --- | --- | --- |
| 24 | `worry_score` | Mean of the 5 worry items asked identically in every wave (food, drinking water, violent crime, severe weather, mental health); very worried=1, somewhat=0.5, not=0 | All 4 waves |
| 25 | `worry_score_core7` | `worry_score` plus worry about traffic accidents and about own work | 2021–2025 only |
| 26 | `worry_index_published` | The worry index LRF published for this wave | Single-wave figures only — not comparable between waves |
| 27 | `experience_score` | Share of the 5 common items where the respondent reports harm in the past two years, self or someone they know | All 4 waves (LRF's own trended definition) |
| 28 | `experience_score_self` | As above, personal harm only (excludes "knows someone who has") | 2021–2025 only — drops sharply against 2019, which didn't offer the "someone you know" option |
| 29 | `experience_score_core7` | `experience_score` plus harm from traffic accidents and from work | 2021–2025 only |
| 30 | `experience_index_published` | The experience index LRF published for this wave | Single-wave figures only; empty for 2025 — LRF published no experience index that wave |
| 31 | `worry_exp_gap` | `worry_score` minus `experience_score` | All 4 waves |

## Resilience

First measured in 2021 — all resilience fields are empty for 2019.

| # | Variable | Label |
| - | --- | --- |
| 32 | `resilience_index` | Resilience Index, 0–1 |
| 33 | `resilience_index_100` | Resilience Index, 0–100 |
| 34 | `resilience_idv` | Resilience: individual dimension, 0–1 |
| 35 | `resilience_hhl` | Resilience: household dimension, 0–1 |
| 36 | `resilience_com` | Resilience: community dimension, 0–1 |
| 37 | `resilience_soc` | Resilience: society dimension, 0–1 |

## Value labels

**GlobalRegion** — 1 Eastern Africa · 2 Central/Western Africa · 3 Northern
Africa · 4 Southern Africa · 5 Latin America & the Caribbean · 6 Northern
America · 7 Central Asia · 8 Eastern Asia · 9 Southeastern Asia · 10
Southern Asia · 11 Middle East · 12 Eastern Europe · 13 Northern/Western
Europe · 14 Southern Europe · 15 Australia & New Zealand

**CountryIncomeLevel** — 1 Low income · 2 Lower-middle income · 3
Upper-middle income · 4 High income · 9 Not classified

**Education** — 1 Primary or less (up to 8 years) · 2 Secondary (9-15
years) · 3 Tertiary (16 years or more) · 9 DK/Refused

**Urbanicity** — 1 A rural area or on a farm · 2 A small town or village ·
3 A large city · 6 A suburb of a large city · 9 DK/Refused

**EMP_2010** — 1 Employed full time for an employer · 2 Employed full time
for self · 3 Employed part time, does not want full time · 4 Unemployed ·
5 Employed part time, wants full time · 6 Out of workforce

**INCOME_5** — 1 Poorest 20% · 2 Second 20% · 3 Middle 20% · 4 Fourth 20% ·
5 Richest 20%

**HouseholdSize** — 1 1-2 people · 2 3-4 people · 3 5-9 people · 4 10 or
more · 9 DK/Refused

## Country coverage by wave

Country coverage differs by wave: 142 countries and areas in 2019, 121 in
2021, 142 in 2023, 140 in 2025. For a global trend, restrict to the
countries present in every wave being compared — otherwise part of the
movement you see is a change in which countries were surveyed, not a
change in the underlying figure.

## Questions outside the harmonised block

Only these 37 variables are guaranteed to line up across waves. Many other
questions are comparable in wording but were not renamed, so their
variable name changes between waves — you have to map it yourself. For
example, "Is climate change a threat to [country] in the next 20 years?"
(1 = very serious threat, 2 = somewhat serious, 3 = not a threat, 98/99 =
DK/refused) is:

| Wave | Variable |
| --- | --- |
| 2019 | `L5` (asked as "...threat to people in [country]...") |
| 2021 | `WP20719` |
| 2023 | `WP20719` |
| 2025 | `WP20719` |

`examples/quickstart.*` works this exact case end to end. Always check
each wave's `_data_dictionary.csv` for the variable name and its codes
before assuming two columns mean the same thing.

## Wave-specific gaps

- **2019**: no `resilience_*` fields (not measured). Worry about traffic
  accidents and about work were not asked; worry about electrical power
  lines and household appliances was asked in 2019 only. The experience
  question asked only about personal harm — see `experience_score_self`
  above.
- **2023**: `HouseholdSize` counts residents aged 15+, not the whole
  household — don't trend it against the other waves.
- **2025**: `experience_index_published` is empty (LRF published none that
  wave). `worry_index_published` covers ten items, not the seven used in
  earlier waves, so it is not comparable even in shape to prior published
  indices.
