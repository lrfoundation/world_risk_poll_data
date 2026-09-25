# World Risk Poll 2024 Focus On: Migration in a Warming World

- **Report:** *World Risk Poll 2024 – Focus On: Migration in a warming world*, Lloyd's Register Foundation
  Global Safety Evidence Centre, 7 May 2026 (19 pages; https://doi.org/10.60743/5ppn-nc25; CC BY-SA 4.0).
  It is published in the Global Safety Evidence Centre library (https://repo.gsec.org.uk, item
  "world-risk-poll-2024-focus-on-migration-in-a-warming-world"), not on the Lloyd's Register Foundation
  publications pages.
- **PDF:** https://storage.googleapis.com/gsec_library_files/items/s0lbzCgoswPJmkgZhmI6/file/1f0dc7c0-6662-4914-85d8-558cc47900e9-Migration%20in%20a%20warming%20world.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (wave 2; 125,911 respondents, 121 countries) and
  `WRP_2023/WRP_2023.parquet` (wave 3; 146,910 respondents, 142 countries), pooled for Chapters 3–5.
  The climate trend in Chapter 2 also uses `WRP_2019/WRP_2019.parquet`.

## What is reproduced

All 229 numbers in the report: every value printed in Charts 1–13b, and every number in the text and
chart footnotes, including percentage-point gaps, chi-square statistics, Cramér's V, standardised
residuals, regression coefficients and their p-values. Results are in [`RESULTS.md`](RESULTS.md).

53 findings use only the public data (Chapter 2): 47 match, 5 are within tolerance and 1 is different.
The other 176 need Gallup World Poll data (see below). Chapter 5 also needs ND-GAIN data (see
External data).

Page numbers in `published_figures.csv` are PDF pages. The printed page number is one less.

Charts with no published values to compare:

- **Chart 14** (forest plot of the regression on page 16) prints no values. Its function (`C5_14`)
  writes the model's coefficients to `output/`, where Python and R are compared. The coefficients in
  the text on the same page are findings X111–X115 (see the model note).
- **Charts 8–10** (chord diagrams) print only some of their shares. Only the printed values are in
  `published_figures.csv`; the functions write the share of every destination region for every group,
  and the test statistics, to `output/`.

Not recorded: p-value thresholds ("p < 0.001"), and the illustrative values in the method boxes on
pages 8 and 12 (0.05, ±1.96, "a residual of 8"). The "coefficient of –2.83" example on page 12 is the
Chart 12a coefficient and is recorded with it (X93).

## Method notes

- **Questions (2021 and 2023 names):** household could cover basic needs without income for less than a
  month or a month or more (`WP22228`), with the follow-up in weeks (`WP22229`); greatest source of risk
  to safety in daily life, coded (`WP22331`; 2019 `L3_A`); climate change a threat to the country in the
  next 20 years (`WP20719`; 2019 `L5`).
- **Weights:** `PROJWT`. Country figures are the same under `WGT`.
- **Base:** everyone asked the question, with don't know and refused kept in the denominator.
- **Chart 1 (basic needs):** less than a week is `WP22229` = 1; less than a month is the rest of
  `WP22228` = 1 (a week or more, or don't know on the follow-up); a month or more is `WP22228` = 2. The
  2023 "don't know/refused" segment is printed as 4%: that is 100 minus the other three rounded figures
  (13 + 24 + 59). The data give 4.9%.
- **Greatest risk (Charts 2 and 4, X01):** financial (not having enough money) is code 9 and the general
  economy code 10 in 2021 and 2023; climate change or severe weather is code 19. In 2019 the nearest
  code is 16, which also covers earthquakes and other non-weather disasters (as in
  `WRP_2023/core_what_the_world_worries_about`). Chart 2's "Economic risk" bars are the general economy
  alone, as the text on the same page (5% and 7%) shows, although the chart note says the category
  combines both. X01 ranks the substantive categories (codes 1–21) with codes 9 and 10 combined:
  road-related accidents 16.0%, economic insecurity 13.2%, crime/violence 12.7%.
- **Trends (Charts 2–4):** each wave uses all the countries surveyed that year (142, 121 and 142).
  Restricting 2019 and 2021 to the countries surveyed in 2023 gives the same rounded figures.
- **Blending (Chapters 3–5):** the report says only that the 2021 and 2023 polls "are blended together
  to provide the maximal sample size". The scripts pool the respondents of both waves and weight them by
  `PROJWT`, so each wave counts in proportion to the adult population of its countries. `WPID_RANDOM`
  does not repeat across the two waves, so one Gallup file can hold both.
- **Groups:**
  - Climate concern (Charts 5 and 7): very serious, somewhat serious, not a threat (`WP20719` = 1, 2,
    3; don't know and refused are left out).
  - "A threat" in the chord diagrams (Charts 8 and 10) is very or somewhat serious, against not a
    threat. This keeps the three analyses at similar sample sizes, as their Cramér's V values imply
    (see below).
  - Chapter 5 compares very serious with not a threat and leaves out somewhat serious, as its charts
    and the forest plot ("Not a threat" is the only climate coefficient) show.
  - Financial resilience: less than a month (`WP22228` = 1) or a month or more (2); don't know and
    refused are left out.
  - Charts 6 and 12 split by financial resilience only, so they include every climate answer.
- **Migration desire (Charts 5–7):** % answering "move to another country" (`WP1325` = 1) among
  those asked, with don't know and refused in the base. X31 ("85% or more" would rather stay) is the
  lowest % answering "continue living in this country" (`WP1325` = 2) across the three climate
  groups.
- **Destinations (Charts 8–10):** among those who would like to move, the preferred destination
  country (`WP3120`) is mapped to a region with a lookup from Gallup country codes (`WP5`) to
  `COUNTRY_ISO3` and `GlobalRegion`. The lookup covers the 148 countries surveyed in any wave of the
  poll, each with its 2023 region, so Iran is Southern Asia. Destinations outside these countries (for
  example Qatar), and don't know or refused, are left out. Shares are within each group and add up to
  100%, as the chart notes say. Charts 8 and 9 use the 15 regions. Chart 10 groups Eastern, Central/
  Western, Northern and Southern Africa, Latin America and Eastern Europe as "Other", which gives the 10
  categories its 27 degrees of freedom imply (4 groups x 10 categories).
- **Chi-square tests (Charts 8–10):** Pearson chi-square on the group by destination table, with
  counts weighted by `PROJWT` rescaled to the sample size (so the weighted total is the number of
  respondents). Cramér's V is √(χ²/(n(k − 1))), with k the smaller dimension of the table. The
  "standardised residuals" are adjusted standardised residuals, (O − E)/√(E(1 − row share)(1 − column
  share)), which are standard normal under independence, as the report's ±1.96 threshold assumes. With
  two groups, both rows of a column have the same residual with opposite signs. The published χ² and
  V imply about 9,000 respondents in each analysis (9,100, 9,700 and 8,400).
- **ND-GAIN gap (Chapter 5):** the ND-GAIN score of the preferred destination minus that of the
  respondent's country, for the overall score (0–100) and its readiness and vulnerability components
  (0–1). The scripts use the 2024 release's latest year, 2022, the same release that reproduces the
  ND-GAIN figures of *Alone together* (`reports/WRP_2025/core_alone_together/`). The report does not
  say which release or year it used. The overall score is 50 × (readiness − vulnerability + 1), so a
  gap of 17.7 points goes with, for example, readiness +0.22 and vulnerability −0.13 (Chart 11). Hong
  Kong, Kosovo, Palestine and Taiwan have no ND-GAIN score; respondents from or preferring them are
  left out. Means are weighted by `PROJWT`.
- **Regressions (Chapter 5):** "survey-weighted regression". The scripts fit weighted least squares
  (statsmodels `WLS` in Python, `glm` with a gaussian family in R) with `PROJWT` weights and
  linearisation (sandwich) standard errors for a design with weights only: HC0 × n/(n − 1), as
  `survey::svyglm` computes them. p-values use a t distribution with n − p degrees of freedom. The
  outcome is the ND-GAIN score gap.
  - Chart 11a (X84, X85): not a threat (reference: very serious), among very serious and not a threat.
  - Chart 12a (X93, X94, C5_12a_p): a month or more (reference: less than a month).
  - Chart 13a (X101, X102): not a threat, a month or more, and their interaction.
  - Chart 14 (`C5_14`, no published values): income group of the respondent's country
    (`CountryIncomeLevel` in the wave the respondent was interviewed; reference low income; "not
    classified" left out), income quintile within the country (`INCOME_5`; reference poorest 20%), not
    a threat (reference very serious) and a month or more (reference less than a month). This is the
    specification the chart note lists.
  - Text on page 16 (X111–X115): the same model with very serious (reference: not a threat)
    interacted with the income group. The text's income-group coefficients (−7.5, −11.9, −20.2) do not
    match the forest plot, which puts them at about −8, −17 and −23. They fit a model with this
    interaction instead: the income-group coefficients are then those of people who do not see
    climate change as a threat, and −11.9 − 4.97 = −16.9 for very serious in upper-middle-income
    countries is close to the plotted −17. X114 (−4.97, "those who perceive climate change as a very
    serious threat actually aspire to smaller ND-GAIN improvements") is read as the upper-middle-income
    × very serious interaction term. This is our reading; the report does not give the model.

## Gallup World Poll data

176 findings (Charts 5–13b, X05 and X29–X115) need two Gallup World Poll items that are not in the
public release. They must be licensed from Gallup directly. The code is included; without the data
these findings are reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

| Findings | Gallup World Poll item | Code used |
| --- | --- | --- |
| Charts 5–13b, X05, X29–X115 | "Ideally, if you had the opportunity, would you like to move permanently to another country, or would you prefer to continue living in this country?" | `WP1325` (1 = move to another country, 2 = continue living in this country), as in `reports/WRP_2021/core_a_changed_world/` |
| Charts 8–13b, X39–X115 | "To which country would you like to move?" (asked of those who would like to move) | `WP3120` (**unconfirmed**; assumed to use Gallup's country codes, the same as `WP5`) |

`WP3120` is our understanding of Gallup's code for the preferred destination country. Confirm the item
code and its coding when requesting the data. If your file codes destinations in another way (for
example as ISO3 codes), change the lookup at the top of the scripts (`DEST_ISO3`, `DEST_REGION`).
`GALLUP_WP_PATH` must hold the respondents of both the 2021 and the 2023 waves.

Both scripts were tested with a synthetic `GALLUP_WP_PATH` file holding `WP1325` and `WP3120` for every
2021 and 2023 respondent. All the Gallup code paths run (percentages, chi-square tests, ND-GAIN gaps
and regressions), and Python and R agree on all 387 values.

## External data

- **ND-GAIN Country Index** (Chapter 5: Charts 11a–13b, X81–X115). **Not redistributed here**,
  because ND-GAIN gives no formal licence. Download it with
  `python reports/external/fetch_external.py ndgain_scores`, which writes
  `reports/external/downloaded/focus_on_migration_in_a_warming_world__ndgain_scores.csv`. Without it,
  these findings are reported as `EXTERNAL_ONLY` (if the Gallup data are available; otherwise they are
  `GALLUP_ONLY`). The file combines `resources/gain/gain.csv`, `resources/readiness/readiness.csv` and
  `resources/vulnerability/vulnerability.csv` from the ND-GAIN Country Index 2024 release
  (https://gain.nd.edu/assets/581929/nd_gain_countryindex_2024.zip), with one row per country (ISO3)
  and year (1995–2022). The scripts use 2022. Downloaded 2026-09-25. ND-GAIN describes the index as
  "free and open-access" but gives no formal licence. The suggested citation is: Notre Dame Global
  Adaptation Initiative Country Index (ND-GAIN), University of Notre Dame.
- **World Bank income groups** (Chart 14): the `CountryIncomeLevel` variable in the poll files.
- The report quotes no statistics from other organisations. Its references (IDMC, the World Bank's
  *Groundswell*, UNDP's *Peoples' Climate Vote*, Pew Research Center, IPCC, IOM, the UN Global Compact
  for Migration and UNDRR) are cited as context only.

## Findings that do not match

1 finding differs from the published value by more than its tolerance:

- **C2_3_dk_2021 (Chart 3, don't know/refused in 2021):** printed as 18%; the data give 19.0% (18.7%
  don't know and 0.3% refused). The four printed 2021 values (41, 26, 18, 14) add up to 99. The same
  figure is 19% in Chart 3.2 of *What the world worries about*
  (`reports/WRP_2023/core_what_the_world_worries_about/`). Tried: the countries surveyed in 2023 (19.0%),
  don't know only (18.7%) and `WGT` (14.2%). Not explained beyond a rounding or typing slip.

5 findings are within tolerance but do not round to the published figure:

- **C2_1_dk_2023:** 4.9% printed as 4% (see the Chart 1 note).
- **C2_2_economy_2021, C2_2_economy_2023:** 5.3% and 7.3% against the printed 5.4% and 7.4%. The
  financial bars match to one decimal (5.6% and 5.9%). Tried: excluding don't know and refused, the
  countries surveyed in both waves, and `WGT`. Not explained.
- **X02:** "more than a third" (36.2%).
- **X06:** "over 140 countries" (142 in 2023).

The report is also inconsistent in places that need the Gallup data to check:

- **Southeast Asia, Chart 8:** the chart prints 11% for those who do not see climate change as a threat;
  the text gives 12% (X48).
- **Northern America, Chart 10:** the chart prints 26% for the financially more resilient who see
  climate change as a threat; the text says "16% of both groups" (X73). The chart's ribbons are
  coloured by climate concern (pink for a threat) and ordered by group along each destination arc;
  read that way, every other printed value in Chart 10 matches the text.
- **Chart 14:** the plotted income-group coefficients differ from the text (see the model note), and
  the plot marks the fourth income quintile as significant, while the text says the income quintile
  "plays no significant role".

## Run

```
python reports/external/fetch_external.py ndgain_scores   # optional: ND-GAIN data for Chapter 5
Rscript reports/WRP_2023/focus_on_migration_in_a_warming_world/reproduce.R
python reports/WRP_2023/focus_on_migration_in_a_warming_world/reproduce.py
```
