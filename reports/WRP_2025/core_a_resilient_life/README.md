# World Risk Poll 2026: A resilient life: How wellbeing shapes the capacity to cope

- **Report:** *A resilient life: How wellbeing shapes the capacity to cope*, World Risk Poll 2026 report, Lloyd's Register Foundation, October 2026 (doi:10.60743/sbwn-m411)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-resilience.pdf
- **Data:** `WRP_2025/WRP_2025.parquet` (World Risk Poll 2025, wave 4; 143,459 respondents, 140 countries), with
  `WRP_2023` and `WRP_2021` for the Resilience Index trends and `WRP_2019` for the 2019 Gallup items

## What is reproduced

All 341 numbers in the report: every value in Charts 1.1 to 3.6 and Tables 1.2, 1.3 and 3.1, and
every number in the text, including point changes, counts of countries, ranks, correlations and the
names in Table 3.1. Page numbers are the report's printed page numbers (PDF page = printed page + 6
in the chapters; roman numerals for the front matter). Results are in [`RESULTS.md`](RESULTS.md).

Some charts show no printed values, so there is nothing to compare. They still have a function that
computes what they plot, and the values are written to `output/` only:

- **Charts 1.3 to 1.6** (line charts of five or six countries' scores in 2021, 2023 and 2025):
  `C1_3`, `C1_4`, `C1_5`, `C1_6`. The changes the text gives about them are compared.
- **Chart 2.2** (country % thriving against the Resilience Index): `C2_2`. Its dividing lines (X48,
  X49) are compared.
- **Chart 2.3** (Resilience Index by present life rating and income group): `C2_3`. The text's
  ranges for ratings 0 to 2 (X22) and the 9 against 10 comparison (X23) are compared.

Table 1.1 lists the questions in the index and contains no poll figures.

## Method notes

- **Index:** the released `resilience_index_100` and `resilience_idv`, `resilience_hhl`,
  `resilience_com` and `resilience_soc` (times 100), as in the 2024 report's folder. The index is not
  recomputed.
- **Weights and base:** `PROJWT`; everyone asked the question, with don't know and refused in the
  base, except X37 and X38 (below).
- **Trends use the countries surveyed in 2025, classified by their 2025 region.** This reproduces
  every 2021 and 2023 value in Table 1.2 and Chart 3.1. With each wave's own countries, Southern Asia
  in 2021 is 51.3 (published 52), and 42.5% of adults said their neighbours care "somewhat" in 2021
  (published 42; 42.4 with the 2025 countries). Afghanistan, Iran and Nicaragua (2021) and also
  Eswatini and Yemen (2023) were not surveyed in 2025.
- **Changes are differences of the rounded figures.** Every point change in the text is the
  difference of the two rounded scores or percentages, as printed: for example Poland's agency fell
  from 51% to 15%, "37 points" (unrounded 36.1), and New Zealand's societal resilience from 65 to 57,
  "8 points" (unrounded 7.4). Rounding is half up.
- **Agency counts (X18, X19):** % who could protect themselves or their family in a future disaster
  (`WP22252` = yes) in the 137 countries surveyed in 2023 and 2025. A change counts when it rounds
  to 10 points or more, which gives 18 increases and 13 decreases. A strict unrounded 10 gives 14 and
  12.
- **Financial resilience and household plans (X37, X38)** are among those giving an answer (don't
  know and refused excluded). This reproduces all seven changes. With don't know and refused in the
  base, the financial changes are 24, 16, 5, 6 and 6 points (published 12, 14, 7, 4 and 3). "More
  than a month" is `WP22228` = "a month or more". The 2021 plan question is `WP22253` ("known by all
  household members"); 2023 and 2025 ask `WP23345` ("over 10 years old").
- **Government care:** `WP22231_ALL`, which includes the versions of the question asked in Vietnam
  ("the authorities") and Myanmar ("the government in power"). For 2021, where the release has no
  combined variable, the scripts combine `WP22231`, `WP22469` and `WP22525` the same way. Without
  them, Southeastern Asia in Chart 3.5 is 25.5% (published 22), and Chart 3.2 counts 96 and 19
  countries (published 97 and 20). X44 (U.S.) uses `WP22231`, which is the same there.
- **Chart 3.2** classifies each country by the difference of its rounded "not at all" and "a lot"
  percentages: 10 points or more either way, or a gap under 10.
- **Table 3.1** lists the countries with the highest rounded "not at all" percentages; Mexico and the
  Republic of Congo tie at 54% for the tenth row of the neighbours list. The ISO3 sets are compared
  (`T3_1_*_top10`), then each country's percentage.
- **Ranks (Chart 1.7, X46)** are on unrounded country scores, 1 = highest. Societal resilience and the
  overall index have 139 countries (no societal score for Saudi Arabia).
- **Harm figures on page 1 (X29)** come from *The quiet hazards*: "yes, personally" plus "both", each
  rounded first, as that report does.
- **Correlation (X28):** Pearson, unweighted, across the 133 countries with both care percentages.
- **Readings of the text:**
  - "Between 45 and 50" and "between 40 and 45" (X22) are recorded as the midpoints with a tolerance of
    2.5.
  - "In most income groups, average resilience among people rating their lives a 10 is slightly lower
    than among those rating them a 9" (X23) is recorded as 3 of 4 groups, tolerance 1.
  - "The only country to have recorded a larger decline since 2021 is Morocco" (X32) is the number of
    countries whose individual resilience fell more than Poland's (unrounded).
  - "Ranging from 62 in Algeria to 39 in Egypt" (X36) compares the two countries' household scores.

## Gallup World Poll data

73 findings need Gallup World Poll items that are not in the public release. The code is included;
without the data these findings are reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item (name used in the code) | What it is | Findings |
| --- | --- | --- |
| `WP16`, `WP18` | Cantril ladder, life today and in five years. The scripts build the Life Evaluation Index groups from them: thriving (7+ now and 8+ in five years), suffering (both 4 or below), struggling (everyone else). `WP16` alone is the present life rating. | Charts 2.1, 2.4, 2.5, 3.4, X20-X23, X47, X49 (and Charts 2.2, 2.3) |
| `WP16056` | Access to the internet (1 = yes), 2019 and 2025 | Table 1.3, X17 |
| `WP137`, `WP138`, `WP139` | Confidence in the military, the judicial system and the national government (1 = yes), U.S. | X43 |

`WP16`, `WP18` and `WP16056` are Gallup's item codes. `WP137`, `WP138` and `WP139` are the codes these
confidence items usually have in the Gallup World Poll; check them with Gallup. Table 1.3 uses the
countries surveyed in 2025 in both years. The public data has a related item for 2021-2025,
`WP22222` ("used the internet in the past 30 days"), but it is not the item the report uses.

The Gallup code paths were tested with a synthetic file of random values (not committed): Python
and R give the same results.

## Findings that do not match

No finding differs from the published value by more than its tolerance. One is within tolerance
but does not round to the published figure: X01, 143,459 interviews, "more than 143,000".

Figures the report quotes from other sources are context and are not reproduced: the IPCC quotation
(page 1), the $75,000 income threshold from Kahneman and Deaton (page 14), the 1995 Kobe earthquake
(page 23) and Lloyd's Register Foundation's £4.5 million committed to projects (page 25). The claims
that the U.S. has "the widest such split of any country" and that "no other country ranks so highly
at the microlevel and so low at the macrosocietal level" (page 10) give no number and are not
compared.

## Run

```
python reports/WRP_2025/core_a_resilient_life/reproduce.py
Rscript reports/WRP_2025/core_a_resilient_life/reproduce.R
```
