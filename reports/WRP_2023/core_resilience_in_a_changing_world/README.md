# World Risk Poll 2024 Report: Resilience in a Changing World

- **Report:** *World Risk Poll 2024 Report: Resilience in a Changing World*, Lloyd's Register Foundation, June 2024 (45 pages)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-06/World%20Risk%20Poll%20Report%202024%20Resilience%20in%20a%20Changing%20World_1.pdf
- **Data:** `WRP_2023/WRP_2023.parquet` (World Risk Poll 2023, wave 3; 146,910 respondents, 142 countries),
  compared with `WRP_2021/WRP_2021.parquet` (wave 2; 125,911 respondents, 121 countries)

## What is reproduced

All 1,713 numbers in the report: every value in Charts 2.1 to 5.7, Tables 2.2, 4.1 and 4.2, the
country table in Appendix ii (margin of error, Resilience Index and four sub-indexes for all 142
countries), and every number in the text, including point changes, counts of countries,
correlations and model estimates. Table 2.2 is a ranking, so its 80 cells are country names.
Page numbers here and in `published_figures.csv` are PDF pages (the printed page number plus 5). Results are in [`RESULTS.md`](RESULTS.md).

Some charts show no printed values, so there is nothing to compare. They still have a function
that computes what they plot:

- **Chart 2.5** (every country's 2023 Resilience Index as an unlabelled dot): `C2_5`.
- **Chart 5.2** (country change in disaster experience against change in planning): `C5_2`.
- **Charts 5.3 and 5.4** (planning against agency, by region and by country): `C5_3`, `C5_4`.
- The global-median lines in Charts 2.3, 2.4 and 2.7 to 2.10 have no values printed.

Table 2.1 and Appendix Tables 1 to 3 list questions and frameworks and contain no poll figures.

## Method notes

- **Index:** the released `resilience_index_100` and `resilience_idv`, `resilience_hhl`,
  `resilience_com` and `resilience_soc` (times 100). These reproduce all 850 Appendix ii values,
  so the index is not recomputed. China has no overall score in 2021. Saudi Arabia has no
  societal score, and so no overall score, in either year.
- **Weights:** `PROJWT`. Country figures are the same under `WGT`.
- **Base:** everyone asked the question, with don't know and refused kept in the base.
- **Region and income group:** the report classifies countries by their **2023** region and
  income group in both years. In the 2021 file Iran is in the Middle East, and seven countries
  (GIN, IDN, JOR, LBN, PAN, ROU, SLV) are in a different income group. Using each wave's own
  codes gives a 2021 Middle East score of 55 (published 52), and 2021 lower-middle and
  upper-middle community scores of 62 and 66 (published 60 and 67). Using the 2023 codes
  reproduces every 2021 regional and income-group figure (Charts 2.1, 2.11 and 5.1, and the
  community footnote on PDF page 13).
- **Country sets:** global figures use every country in each wave, as the report does (55 in
  2021 vs 57 in 2023). Country changes use the 120 countries measured in both years (Jamaica was
  not measured in 2023). The overall index and the societal dimension have 118 comparable
  countries (no China in 2021, no Saudi Arabia); the individual, household and community
  dimensions have 120.
- **Significant change:** the report counts a country as changed when the change is "four
  points or more". The counts in Chart 2.2, Chart 2.6 and the text are reproduced when the
  unrounded change rounds to four or more (|change| ≥ 3.5). A strict unrounded ≥ 4 gives 5
  increases and 15 decreases in the overall index (published 8 and 20). Differencing rounded
  scores gives 8 and 17. Only the rounding rule reproduces all ten counts in Chart 2.6.
- **Point changes** in the charts and text are computed from unrounded scores. The report says
  it took some text changes from rounded figures (PDF page 7, footnote ii), so a few differ by a
  point (see below).
- **Early warning (Chapter 3):** as the chart notes define it. "At least one warning" means yes
  to any of the four sources (`WP22248`–`WP22251`). "No warning" means no to at least one source
  and yes to none. Respondents with no yes or no answer to any source are excluded. Chart 3.2 and
  the source figures in the text use everyone who experienced a disaster.
- **Financial resilience (Charts 3.6, 4.2):** from `WP22228` and `WP22229`. The groups are
  less than a week, a week to a month (including don't know on the weeks follow-up), and a month
  or more. "More than a month" (PDF page 30) is the answer "a month or more".
- **Employment (Chart 4.1):** full time for an employer (`EMP_2010` = 1); in the workforce but
  not full time for an employer (2–5); out of the workforce (6).
- **Any discrimination (Chart 2.11):** yes to any of the five types (`WP22259`–`WP22263`), among
  respondents asked at least one of them. The items were not asked in the UAE, China or Saudi
  Arabia in 2021, or in the UAE, Saudi Arabia or Yemen in 2023.
- **Disaster types:** `WP22247` (the type of the disaster experienced). Flooding among all
  adults (PDF page 27) is flooding as a share of everyone asked the disaster question.
- **Case studies:** Pakistan's provinces come from `REGION_PAK` and New Zealand's regions from
  `REGION_NZL`. Both variables exist in 2021 and 2023. Morocco is the whole country.
- **Correlations:** Pearson correlations across countries, unweighted, using countries with
  both values. Changes are 2023 minus 2021 over the 120 common countries.
  - PDF page 15, R = 0.65 and R = 0.40: change in individual vs household resilience (0.653), and
    change in community vs societal resilience (0.403). Footnote ii sits after "community or
    societal resilience", but individual–community is 0.14 and individual–societal −0.01, so
    0.40 is the community–societal correlation that the next sentence describes.
  - PDF page 26, R = 0.25: change in community resilience vs the change in real GDP growth
    (World Bank `NY.GDP.MKTP.KD.ZG`, 2023 minus 2021). This is 0.249, and the other dimensions
    are not related to it (individual 0.04, household −0.09, societal 0.19). Growth in 2022,
    growth in 2023, and the mean or cumulative growth over 2022–23 give 0.19 or less.
  - PDF page 26, R = 0.55: change in the % who could cover basic needs for a month or more vs
    change in individual resilience (0.551). The appendix's 0–1 weeks score gives 0.35 instead.
  - PDF page 28, R = 0.22 and PDF page 29, R = 0.12: change in % who experienced a disaster vs change in
    % with a household plan, and vs change in % with agency (yes).
  - PDF page 29, R = 0.90: across the 15 regions, % with a household plan vs % with agency in 2023.
- **Model (PDF pages 23–24):** the report does not give its specification. The one used here is
  weighted least squares (`PROJWT`) of the Resilience Index (0–100) on employment status
  (`EMP_2010`), age group (`AgeGroups3`), sex, income quintile, urbanicity (`Urbanicity`),
  region (`GlobalRegion`), and the country's log GDP per capita, real GDP growth and CPI
  inflation in 2023 (World Bank; see below). Education is left out, as the report does, because
  it is part of the index. The reference groups are out of the workforce, aged 50+, male, the
  poorest 20%, rural and Eastern Africa. Rows missing any variable are dropped (9 countries have
  no World Bank inflation for 2023). The estimates are: full time for an employer +4.1 (published
  4), aged 15–29 +3.8 (published 4) and aged 30–49 +2.4 (published 2). The other employment
  groups are +2.0 to +2.9, "roughly half the same effect". Without the three World Bank variables
  the estimates are 4.3, 3.5 and 2.3. Python uses statsmodels `wls` and R uses `glm` with
  gaussian family and the same weights.
- **Margin of error (Appendix ii):** 95% margin for a 50% proportion with the Kish design
  effect of `WGT`: 196 × √(0.25 × deff / n), where deff = n Σw² / (Σw)². This reproduces all 142
  published margins to one decimal. The "average country-level margin of error ... +/- 4"
  (PDF page 8) is their mean, 3.9.
- **Table 2.2:** countries are ranked on unrounded 2023 scores across all 142 countries.
  `bottom_1` is the lowest-scoring country, which is the last row of the table. Names are
  printed as in the report (for example "Taiwan, PoC").
- **Readings of the text:**
  - "Burkina Faso, Russia, Kyrgyzstan and Ukraine saw increases of at least four points" (X34):
    the smallest of the four changes.
  - "all of which saw increases of eight percentage points or more" (X72): the smallest
    increase among the eight countries named. Latvia's is 7.8.
  - "women far more likely than men (73% vs 27%)" in Afghanistan (X98): the % of each sex out of
    the workforce. The share of women among those out of the workforce is also 73%.
  - "no other countries rank in the top or bottom 10 ... on more than two resilience
    dimensions" (X79): top and bottom are counted separately. Niger is in the bottom 10 for
    individual and household resilience and in the top 10 for societal resilience, so counting
    them together gives one country, as Table 2.2 itself shows.
  - "two-thirds" (X85_flood): recorded as 67 with a 2-point tolerance. "Twice the rate" (X129):
    the ratio 66/34, with a 0.25 tolerance.
  - The "17 countries" of the Early Warnings for All initiative measured by the poll (X84) are
    the countries in Chart 3.1. The list of 30 priority countries is the UN's.

## Gallup World Poll data

The World Risk Poll is fielded as part of the Gallup World Poll (GWP). The Resilience Index uses
several GWP items, including education, internet and mobile phone access at home, feeling safe
walking alone, helping a stranger, satisfaction with local infrastructure and confidence in
national institutions. The released index and dimension scores already include them, so none of
the index findings need Gallup data.

Twenty-four findings use GWP items that are **not** in the public release, and are reported as
`GALLUP_ONLY` without them. The code is included (`merge_gallup`), and the items must be
licensed from Gallup directly (see [`reports/README.md`](../../README.md#gallup-world-poll-data)).
Except for `WP108`, the GWP item codes are not known, so the code uses the placeholder names
below. Rename the columns in your Gallup file to match.

| Placeholder / item | Findings | Coding the code expects |
| --- | --- | --- |
| `GWP_MOBILE_PHONE` | X14, X93, X94, X95, Chart 3.8 | 1 = owns a mobile phone that can access the internet; 2 = owns one that cannot (or doesn't know); 3 = no mobile phone |
| `GWP_DEGURBA` | Chart 3.7 | Gallup's degree of urbanisation: 1 = rural areas; 2 = towns and semi-dense areas; 3 = cities |
| `GWP_INTERNET_ACCESS` | X88 ("71% ... had access to the internet in some way") | 1 = yes |
| `GWP_LOCAL_ECONOMY` | X68, X69 (Brazil, local economy getting better) | 1 = getting better |
| `WP108` | X135 (Morocco, donated money to charity in the past month, 2023) | 1 = yes |
| `GWP_NATIONAL_INSTITUTIONS` | X144 (17 countries missing societal items) | the national institutions index, missing where not asked |

Chart 3.7's "degree of urbanisation" is not the self-reported `Urbanicity` in the release. Using
`Urbanicity` as a stand-in (rural or farm / small town or village / large city or suburb) gives
69%, 66% and 74% warned, against the published 65%, 67% and 74%, so the chart needs Gallup's
variable.

Both scripts were also run with a made-up GWP file holding these columns. Every Gallup finding
ran, and Python and R agreed.

## External data

`reports/external/core_resilience_in_a_changing_world__worldbank.csv` is a snapshot of World
Bank World Development Indicators for 2020–2023, one row per country, indicator and year. It
holds:

- GDP per capita, current US$ (`NY.GDP.PCAP.CD`)
- GDP growth, annual % (`NY.GDP.MKTP.KD.ZG`)
- Inflation, consumer prices, annual % (`FP.CPI.TOTL.ZG`)

It was downloaded on 25 September 2026 from
`https://api.worldbank.org/v2/country/all/indicator/<code>?date=2020:2023&format=json`
(database last updated 13 July 2026), and is licensed CC BY 4.0. It is used by the model
(X96, X102, X103) and by the GDP-growth correlation (X108). The report used World Bank data
retrieved in April 2024, so revisions since then may shift these slightly. Taiwan has no World
Bank data. Yemen has no 2021–2023 GDP data.

These statistics are quoted from other sources and not reproduced:

- The WMO on 2023 as the warmest year, and Copernicus on 1.5 °C.
- Global inflation above 8% (2022), 14% in Eastern Europe (IMF), and 8.7% in 2022 against 4.7%
  in 2021 (IMF).
- The −3.1% fall in global GDP (World Bank).
- Morocco's 6.8-magnitude earthquake: 380,000 people severely affected (about 1% of the
  population), about 3,000 deaths and 6.6 million affected.
- Pakistan's 2022 floods: 15% of the population, 1,700 deaths and 8 million displaced.
- Five hazard events in Ukraine with 32 deaths.
- About 12% of Türkiye's population not sampled.
- The 30 Early Warnings for All priority countries.
- Two Gallup World Poll figures from years with no World Risk Poll data in this release:
  internet access in 2017 (half) and Morocco's 2% charity donations in 2022.

## Findings that do not match

One finding differs from the published value by more than its tolerance:

- **X105:** the report says women score equal to or lower than men on the Resilience Index in
  every country. In the data, women score higher in 5 countries on rounded scores (7 unrounded:
  ARE, COG, GIN, HKG, LUX, MLI, PHL). The largest lead is 2.3 points (UAE), and none reaches the
  report's 4-point significance threshold. So the statement holds for significant differences
  only. Not otherwise explained.

Seven more findings are within tolerance but do not round to the published figure:

- **X01:** 146,910 interviews ("nearly 147,000").
- **X22 and X115_central_asia:** the text took these changes from rounded figures (65 − 62 = 3
  and 19 − 9 = 10). The unrounded changes are 3.6 and 9.2.
- **T4_1_southern_europe_gap and X101_southern_europe:** the gap is 6.4. The rounded scores in
  the same row (58 − 51) give the published 7.
- **X85_flood:** 66.2% ("two-thirds").
- **C5_1_latin_america_2021:** 24.5% against the published 24, on a rounding boundary.

## Run

```
Rscript reports/WRP_2023/core_resilience_in_a_changing_world/reproduce.R
python reports/WRP_2023/core_resilience_in_a_changing_world/reproduce.py
```
