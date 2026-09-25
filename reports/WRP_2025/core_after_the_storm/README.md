# World Risk Poll 2026: After the storm: How disasters reshape resilience and trust

- **Report:** *After the storm: How disasters reshape resilience and trust*, World Risk Poll 2026 report,
  Lloyd's Register Foundation (https://doi.org/10.60743/16n7-bn41). **Not yet published:** the report is due
  to launch, and no launch date has been given.
- **PDF:** https://doi.org/10.60743/16n7-bn41 (the DOI resolves once the report is launched)
- **Data:** `WRP_2025/WRP_2025.parquet` (World Risk Poll 2025, wave 4; 143,459 respondents, 140 countries),
  with `WRP_2021` and `WRP_2023` for the case studies

## What is reproduced

All 1,537 numbers in the report: every value printed in Charts 1.1, 1.2, 3.1 to 3.6, 4.8 and 4.9 and in
Tables 2.1, 2.2, 4.1 and A.1 to A.4, and every number in the text, including counts ("six of the seven",
"eight of the 11 provinces"), respondent counts in the chart notes, and ratios given in words ("nearly
tripled", "doubled"). Page numbers are the report's printed page numbers (PDF page minus 6 in the chapters,
roman numerals for the foreword and executive summary). Results are in [`RESULTS.md`](RESULTS.md).

Some charts print no values:

- **Charts 2.1 to 2.7 and 4.4 to 4.7** are maps of the change in the Resilience Index by region. Their
  functions (`C2_1` to `C2_7`, `C4_4` to `C4_7`) write every region's change to `output/` only. The text
  beside each map quotes many of these changes, and those are compared.
- **Chart 2.8** plots the Table A.1 estimates and two pooled estimates. The case values are compared through
  Table A.1; "Pooled, six cases" (without Ecuador) is written to `output/` (`C2_8_pooled6`).
- **Charts 4.1 to 4.3** plot the gaps in Table A.3, which are compared there.

## Method notes

- **Case studies and regions.** Each case study splits the country into the regions the disaster struck
  (affected) and every other region (rest of the country), using the poll's region variables:

  | Case | Affected regions | 2021 | 2023 | 2025 |
  | --- | --- | --- | --- | --- |
  | Morocco | Marrakech-Safi | `REGION_MAR` (provinces, mapped to regions) | `REGION3_MAR` | `REGION3_MAR` |
  | Mozambique | Zambezia, Sofala, Manica | `REGION_MOZ` | `REGION_MOZ` | |
  | New Zealand | Northland, Auckland | `REGION_NZL` | `REGION_NZL` | Gallup (see below) |
  | Türkiye | Mediterranean, Central East Anatolia (NUTS-1) | `REGION3_TUR` | `REGION3_TUR` | `REGION3_TUR` |
  | Pakistan | Sindh | `REGION_PAK` | `REGION_PAK` | |
  | South Africa | KwaZulu-Natal | Gallup (see below) | `REGION_ZAF` | `REGION_ZAF` |
  | Ecuador | Guayas, El Oro | `REGION_ECU` | `REGION_ECU` | |

  Region "don't know" and "refused" are left out (5 respondents in Ecuador 2021). The one exception is
  Morocco 2021, where the public file codes provinces: `reproduce.py` maps the 75 provinces to the 12 regions
  of the 2015 reform, and the 7 respondents whose province is "don't know" stay in the rest of Morocco. These
  two choices reproduce Tables A.1 and A.2 to the decimal (the report must have had those 7 respondents'
  region). Pakistan's former FATA (2023 only) is folded into Khyber Pakhtunkhwa, as in the maps.
- **Measures** (0-100): the Resilience Index and its four dimensions are `resilience_*` x 100.
  Government cares "a lot" (`WP22231` = 1), neighbours care "a lot" (`WP22232` = 1), could protect yourself
  or your family (`WP22252` = 1; "it depends" is in the base), reported disaster (`WP22245`, `WP23344`,
  `WP24213` = 1), national government well prepared (`WP22241` in 2021, with its "it depends" in the base;
  `WP24198` in 2025), local government well prepared (`WP24199`), Worry Index (`worry_index_published` x
  100), and the hazard named (`WP22247` in 2023, `WP24180` in 2025). Base: everyone asked, with don't know
  and refused in the base. Weight: `PROJWT`.
- **Case estimates** (Tables A.1 to A.3) come from a weighted least-squares regression within the country:
  the measure on an affected indicator, wave dummies and their interactions, weighted by `PROJWT`, with HC1
  standard errors (n / (n - k)) and normal 95% intervals. The difference-in-differences is the
  affected-by-2023 coefficient; the 2023-2025 change is the affected-by-2025 minus the affected-by-2023
  coefficient in the three-wave model. This reproduces every estimate and interval in Tables A.1 and A.2 for
  the six case studies in the public data, and Table A.3 for Morocco and Türkiye. South Africa's 2023-2025
  change uses 2023 and 2025 only (its 2021 regions are Gallup data); the estimate is the same and the HC1
  factor differs by about 0.1%. "Adjusted" removes Southeast Anatolia, and Waikato, Bay of Plenty, East Cape
  (Tairawhiti) and Hawke's Bay, from both groups.
- **Pooled models** (Tables 2.2 and A.4): one regression on the stacked case studies with country-by-wave
  and country-by-affected dummies and the affected-by-wave term(s), with `PROJWT` rescaled to sum to 1 in
  each country and wave, and HC1 errors. Case studies where a question was not asked in a wave are left out
  (confidence: Morocco and Pakistan; government cares in Table A.4: Morocco). Region-clustered errors (the
  appendix's second error) cluster by region within country, CR1: G / (G - 1) x (n - 1) / (n - k). The
  "months" and "exposure check" slopes interact the affected-by-2023 term with the months in Table 2.1 and
  with each case's exposure-check estimate.
- **Map notes and region counts** count respondents with an Index score (Northern Cape 2025: 39, as
  printed, of 40 respondents). A region is shaded if it has respondents in both waves and hatched if it has
  fewer than 50 in either. Table 2.1 and Table 4.1 count all respondents in the affected regions.
- **Türkiye's NUTS-2 units** come from `REGION_TUR` (2021 and 2023). The "eight of the 11 officially
  affected provinces" with no 2023 respondents are the provinces in the three units (TR63, TRC1, TRC2) with
  no 2023 respondents; the 118 respondents are those units' respondents in 2021. The "51% ... 50%" shares
  are unweighted shares of the affected-region respondents in TR62, TR63 and TRB1.
- **Chapter 1 and 2 national figures.** "Fell in 75 of the 120 countries and rose in 43" uses each country's
  Index as the mean of its four dimension scores (the Index as defined in Table 1.1); the mean of the
  respondent Index gives 74 and 44 (of 118 countries with an Index in both waves). The global changes on
  page 2 ("two points above 2021", "one point above 2021") are differences of the rounded scores (unrounded
  1.4 and 1.7).
- **Margins of error** (page 49): a percentage's margin is 1.96 x sqrt(0.25 / n); an Index margin is the
  half-width of the HC1 interval of the Index gap in one wave (Morocco 2023, 132 respondents: 2.7; New
  Zealand 2023, 418: 2.2).
- **Rounding.** The charts round each estimate once. Some whole numbers in the text are rounded from the
  one-decimal appendix values instead: for example New Zealand's neighbours estimate, -4.48, is -4 in Chart
  3.3 and "five" in the text (-4.5 rounded again). Nine text findings and one bound in Table 2.1 (26.48, printed
  27; Table A.2 prints 26.5) are within tolerance for this reason.
- **Words compared as numbers:** "nearly tripled" as a ratio of 3 (tolerance 0.5), "doubled" as 2 (0.3),
  "half" as 50% (15), "roughly two in five" as 40% (3), "fewer than one in ten", "within two points", "within
  three points" and "a point or less" as upper bounds, "about 14,000" and "about 10,000" with a tolerance of
  500. "About 14,000" counts respondents with an Index score in the seven countries in 2021 and 2023; "about
  10,000" counts all respondents in the five countries that asked about confidence.

## Gallup World Poll data

542 findings need data that is not in the public release. The code is included; without the data these
findings are reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item (name used in the code) | What it is | Findings |
| --- | --- | --- |
| `REGION_ZAF` (2021 respondents) | South Africa's province in 2021. The public 2021 file has no South African region variable. | 222: South Africa's 2021-2023 estimates and 2021 gaps, and everything pooled over the seven case studies (Table 2.2, the pooled bars in Charts 3.1 to 3.5, "six of the seven", the sensitivities and slopes on page 46) |
| `REGION_NZL` (2025 respondents) | New Zealand's 16 regions in 2025. The public 2025 file has only `REGION2_NZL` (North and South Island). | 212: New Zealand's 2025 gaps and changes in Table A.3, Chart 4.6, and the pooled three-wave model (Table A.4) |
| `WP139` | Confidence in the national government (1 = yes). | 137: Charts 3.2 and 3.6, the confidence rows of Tables 2.2 and A.2 to A.4, and the text on confidence |
| `FIELD_DATE` | Interview date (the name it has in the 2019 release). The months from each event to fieldwork are calendar months from the event month to the country's modal interview month. | 12: the months columns of Tables 2.1 and 4.1 |
| `REGION_TUR` (2025 respondents) | Türkiye's 26 NUTS-2 units in 2025 (the 2025 file has NUTS-1 only). | 5: Hatay, Kahramanmaraş and Osmaniye's 10 respondents in 2025 and the 63% share |
| `REGION_MOZ`, `REGION_PAK`, `REGION_ECU` (2025 respondents) | Provinces in 2025 (the public 2025 file has only three broad regions for each). | 6: the 2025 exposure checks on pages 45-46 |
| `WP12259` | Gallup's primary sampling unit, for the third (PSU-clustered) standard error. | 7 |

The region items are assumed to use the same codes as the 2023 public release (for example
`REGION_ZAF` 4 = KwaZulu-Natal). The confidence item `WP139` is the one the report's appendix names. All
the Gallup code paths were tested with a synthetic file of random values (not committed): Python and R
give the same results.

## External data

None. Figures the report quotes from other sources are context and are not reproduced: the earthquake
magnitudes, depths and distances (USGS), death tolls, injuries, displacement, damage and appeal figures
for each disaster (for example 2,960 dead in Morocco, 53,537 in Türkiye, 1,730 in Pakistan, 443 in
KwaZulu-Natal, 14 in Ecuador, 165 after Cyclone Freddy; US$34.2 billion and US$103.6 billion in Türkiye;
over US$30 billion in Pakistan, close to 70% of it in Sindh; the UN appeal of US$160 million revised to
US$816 million), the Baker Institute's "more than 10 construction amnesties since 2001", Gallup's note that
provinces holding about 12% of Türkiye's population could not be interviewed in 2023, the 11 officially
affected Turkish provinces, Lebanon's currency losing more than 85% of its value, and the dates of the
events and of the Malaysian floods.

Not entered as findings: the months after each event given in the text and chart labels ("surveyed a month
after", "22 months", "31 months", "25 to 41 months"), which are the Table 2.1 and 4.1 values; the text
columns of Tables 2.1 and 4.1; "six case studies meet (a) to (c)" and "four of the 11 officially affected
provinces" (checks on the geography, not survey estimates); and Thailand "just above the middle of the
country ranking" (Thailand's 28% is 60th of 142 countries in 2023; the median is 26%).

## Findings that do not match

2 findings differ from the published values by more than their tolerance:

- **X086 (page 6):** "Two thirds of Türkiye's affected respondents are in its Mediterranean region." The
  Mediterranean has 127 of 174 affected respondents in 2021 and 130 of 180 in 2023 (72.6%; 75% weighted). The
  share is 69% over all three waves and 62.5% in 2025 alone. Not explained.
- **X299 (page 22):** "without KwaZulu-Natal it halves to four". The pooled model on the six other case
  studies gives 3.0 (HC1 -1.4 to 7.4, within the margin of error as the text says). The report's "four" may be
  half of the seven-case estimate (7) rather than a separate estimate. Not explained further.

Within the report, Chart 3.1 shows the pooled individual-dimension estimate as -2 and Table 2.2 as -3
(both need the Gallup data), and the legends of Charts 4.4 to 4.7 say "2021 to 2023" for maps of the 2023
to 2025 change.

22 more findings are within tolerance but do not round to the published figure:

- **Rounded twice (see Method notes):** T2_1_TUR_expo_lo (26.48), X019 and X528 (21.47), X026, X040, X560
  and X600 (32.49), X295 and X302 (-4.48), X305 (16.48).
- **Words:** X004 (37.7% for "roughly two in five"), X005 (7.7% for "fewer than one in ten"), X087 (90.9%
  for "nine in ten"), X432 and X440 (1.5 for "within two points"), X468 (Istanbul +0.6 for "level").
- **Counts given as round numbers:** X001 and X006 (143,459), X430 (52 for "about 50"), X523 (39 for "about
  40"), X633 (14,027), X634 (10,024).

## Run

```
Rscript reports/WRP_2025/core_after_the_storm/reproduce.R
python reports/WRP_2025/core_after_the_storm/reproduce.py
```
