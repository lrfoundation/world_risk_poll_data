# World Risk Poll 2026: A resilient life: How wellbeing shapes the capacity to cope

- **Report:** *A resilient life: How wellbeing shapes the capacity to cope*, World Risk Poll 2026 report,
  Lloyd's Register Foundation (https://doi.org/10.60743/sbwn-m411). **Not yet published:** the report is due
  to launch, and no launch date has been given.
- **PDF:** https://doi.org/10.60743/sbwn-m411 (the DOI resolves once the report is launched)
- **Data:** `WRP_2025/WRP_2025.parquet` (World Risk Poll 2025, wave 4; 143,459 respondents, 140 countries),
  with `WRP_2021` and `WRP_2023` for the Resilience Index trends and `WRP_2019` for two Gallup trends

## What is reproduced

All 470 numbers in the report: every value printed in Charts 1.1, 1.2, 1.7, 2.1, 2.4, 2.5 and 3.1 to 3.6
and in Tables 1.2, 1.3 and 3.1 (including the country names in Table 3.1), the numbers on the chapter
covers (the "408,798 stories", the "+26 points" rings and the 100-dot graphic), and every number in the
text, including point changes, counts ("18 increases ... 13 decreases", "97 countries", "five appear on
both lists"), ranks ("130th of 139") and ratios given in words ("twice as high"). Page numbers are the
report's printed page numbers (PDF page minus 6 in the chapters, roman numerals for the foreword and
executive summary). Results are in [`RESULTS.md`](RESULTS.md).

Some charts print no values. Their functions write the plotted values to `output/` only:

- **Charts 1.3 to 1.6** are line charts (individual resilience in five Eastern European countries,
  household resilience in five African countries, Ukraine's Index and dimensions, and societal resilience
  in six high-income countries): `C1_3` to `C1_6`. The text beside each chart quotes the changes, and
  those are compared.
- **Chart 2.2** (country % thriving against the Resilience Index) and **Chart 2.3** (the Index by present
  life rating and income group) need Gallup data: `C2_2` and `C2_3`. The r = 0.61, the two medians and the
  ranges the text reads off Chart 2.3 are compared.
- **Chart 3.1** labels only 2021 and 2025. The 2023 shares are written to `output/`.

## Method notes

- **Measures** (0-100): the Resilience Index and its four dimensions are the released `resilience_index`,
  `resilience_idv`, `resilience_hhl`, `resilience_com` and `resilience_soc` x 100 (the 2025 source file
  held them on a 0-100 scale; the release stores 0-1, and the report prints 0-100). The index is not
  recomputed. Weight: `PROJWT`. Base: everyone asked, with don't know and refused in the base, except
  where noted below.
- **Trends use the countries surveyed in 2025** in 2021 and 2023, as in *The quiet hazards*. This is
  what reproduces Table 1.2 and Chart 3.1. With every country in each wave, the Middle East is 55 in
  2021 and 50 in 2023 (published 52 and 53), because Iran (Middle East in 2021), Afghanistan and Yemen were
  not surveyed in 2025, and 2021 neighbours "somewhat" is 42.5% (published 42). Chart 1.1 is the same on
  either country set. Regions are `GlobalRegion`, which is the same in every wave for the 2025 countries.
- **Changes are differences of the rounded figures,** as printed: "individual resilience has fallen two
  points for a second consecutive edition" is 46 to 44 to 42 (unrounded -1.3 and -2.5), "two points above
  2021" is 55 to 57 (1.4), government cares "a lot" "nudged up by three points" is 19 to 22 (2.4), Southern
  Africa's "four points" is 47 to 51 (3.3), Bulgaria's agency "-40" is 75 to 35 (-39.4), and so on. Each
  such finding's note gives the unrounded change where it rounds differently. Using unrounded changes
  would move 17 of the matches to within tolerance, and X53 (two regions fell by two points) would
  differ: only Eastern Asia's unrounded fall (-2.5) reaches two points.
- **Counts of large changes and gaps** count a change or gap when it rounds to 10 points or more
  (|x| >= 9.5), the rule that also reproduces the 2023 resilience report's four-point counts
  (`WRP_2023/core_resilience_in_a_changing_world`). This gives the 18 increases and
  13 decreases in agency (strictly 10 or more: 14 and 12; differences of rounded shares: 18 and 12) and
  the 97 / 20 / 16 split of government care (strictly: 97 / 19 / 17). Agency is the country % who could
  protect themselves or their family from a future disaster (`WP22252` = yes), 2023 to 2025, in the 137
  countries surveyed in both.
- **Government cares about you** is `WP22231_ALL` in 2023 and 2025, the combined item that adds
  Myanmar's and Vietnam's own wording (`WP22525`, `WP22469`); the scripts build the same combination for
  2021. With `WP22231` alone the 2025 shares are 22 / 46 / 30 (published 22 / 47 / 29) and 131 countries
  (Chart 3.2 has 133). Neighbours care is `WP22232`.
- **Financial resilience and disaster plans in Africa (page 7)** exclude don't know and refused: the %
  who could cover basic needs for a month or more (`WP22228` = 2) and the % whose household has a plan
  known to all members (`WP22253` in 2021, `WP23345` in 2023-2025). With them in the base the changes are
  24, 16, 5, 6 and 6 (published 12, 14, 7, 4 and 3) and Algeria's plan change is 31 (published 30).
  The agency changes on page 6 keep them in the base, which reproduces all five.
- **Ukraine (page 8):** "neighbours cared about them at least somewhat" is `WP22232` = 1 or 2.
- **Six high-income countries (page 9):** "all saw declines ... in the perception that their governments
  care" is the % saying "a lot" or "somewhat" (Australia's % "a lot" rose by 0.1). Australia's
  discrimination items are `WP22259` (skin colour), `WP22262` (gender) and `WP22263` (disability).
- **Ranks (page 10)** are over the countries with a score, 1 = highest, ties sharing the best rank:
  140 countries on the individual, household and community dimensions and 139 on the societal dimension
  (Saudi Arabia has none). "No other country ranks so highly at the microlevel and so low at the
  macrosocietal level" is the U.S.'s position on societal rank minus its better individual or household
  rank (128; Taiwan is next with 107). The spread of the four ranks is not it: Morocco's is wider, in the
  other direction. "Bottom 20%" and "top 20%" are the rank as a % of countries, compared as upper bounds.
  Discrimination is `WP22259`-`WP22263` = yes, among everyone asked.
- **"408,798 stories"** (chapter 1 cover) is the number of respondents with all four dimension scores in
  2021, 2023 and 2025 (with an Index score: 409,270).
- **Page 1** quotes harm figures from *The quiet hazards*; they are computed as there ("yes, personally"
  plus "both", each rounded before adding).
- **Table 3.1** ranks countries on unrounded %; the neighbours list's last row, "Mexico, Republic of
  Congo", holds both countries at 54%. Names are printed as in the table.
- **Correlations** are Pearson, unweighted, across countries: r = 0.57 between the % feeling no
  government care and the % feeling no care from neighbours (133 countries).
- **Words compared as numbers:** "fewer than one in four" as an upper bound of 25 (tolerance 4); "roughly
  one in four" as 25 (tolerance 2); "nearly twice as high" and "twice as high" as a ratio of 2 (0.3 and
  0.25); "between 45 and 50" and "between 40 and 45" as 47.5 and 42.5 with a tolerance of 2.5; "most income
  groups" as the three the chart shows; "at least 10 points", "at least seven in 10" and "at least 55%" as
  lower bounds; "all", "four" and "two" of the named countries as counts.
- **Not entered:** edition counts ("fourth edition", "for the third time"), the thresholds that define
  the Life Evaluation Index (7+, 8+, 4) and the rating thresholds the text reads off Chart 2.3 ("above a
  rating of 2", "flatten above ... 7"), dates, and "these five regions" (the regions just named). Page 5
  says the other regions changed "by one point or remained unchanged"; Table 1.2 shows Northern America
  up two points (63 to 65), which is not a numbered claim.

## Gallup World Poll data

93 findings need Gallup World Poll items that are not in the public release. The code is included;
without the data these findings are reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item | What it is | Findings |
| --- | --- | --- |
| `WP16`, `WP18` | Cantril ladder, life today and in five years (0-10). The scripts build the Life Evaluation Index from them: thriving (7+ now and 8+ in five years), suffering (both 4 or below), struggling (everyone else with two valid ratings), as the report's note defines it. | 70: Charts 2.1 to 2.5 and 3.4, the chapter 2 cover, X28-X32, X83-X87, X89 |
| `WP16056` | "Do you have access to the internet in any way ...?" (1 = yes) | 13: Table 1.3, X27 |
| `WP139` | Confidence in the national government (1 = yes) | 3: X65, X75, X76 |
| `WP138` | Confidence in the judicial system and courts (1 = yes) | 3: X67, X75, X76 |
| `WP137` | Confidence in the military (1 = yes) | 4: X66, X82 (including the U.S. in 2019) |

These are Gallup's item codes (`WP16`, `WP18` as in *The quiet hazards*; `WP16056` as in *A resilient
world?* (2021); `WP137`-`WP139`, the National Institutions Index items). `WPID_RANDOM` does not repeat
across waves, so one Gallup file can hold the 2019, 2021 and 2025 respondents these findings need. Table
1.3's 2019 figures use the countries surveyed in 2025. The public 2019 item `L26` ("used the internet in
the past 30 days") is not the same measure: it gives 48, 26, 51, 21 and 53% for Table 1.3's 2019 column
(published 52, 31, 51, 28 and 56).

The Gallup code paths were tested with a synthetic file of random values (not committed): Python and R
give the same results for all 863 values.

## External data

None. Statistics the report quotes from other sources are context and are not reproduced: the IPCC
quotation, the research cited on pages 2, 8, 12, 17 and 23 (for example emotional wellbeing levelling off
at around $75,000 a year, and the 1995 Kobe earthquake), Gallup's finding that trust in national
governments has stayed below a majority in many democracies, Lloyd's Register Foundation's £4.5 million
for projects using the Poll, and the funded projects described on page 25.

## Findings that do not match

None: no finding differs from the published value by more than its tolerance.

Six findings are within tolerance but do not round to the published figure, all because the text gives
a bound or a round number:

- **X01:** 143,459 interviews ("more than 143,000").
- **X03_government and X03_neighbours:** 21.8% and 22.9% ("fewer than one in four").
- **X40:** 24.5% of adults in middle-income countries feel no government care ("roughly one in four").
- **X78:** the U.S. is 17th from the bottom of 133 countries on government cares "a lot" (12.8%, "bottom
  20%").
- **X80_disability:** the U.S. is 17th of 138 countries on discrimination due to a disability (12.3%,
  "top 20%").

## Run

```
Rscript reports/WRP_2025/core_a_resilient_life/reproduce.R
python reports/WRP_2025/core_a_resilient_life/reproduce.py
```
