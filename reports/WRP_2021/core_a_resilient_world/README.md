# World Risk Poll 2021: A Resilient World? Understanding vulnerability in a changing climate

- **Report:** *World Risk Poll 2021: A Resilient World? Understanding vulnerability in a changing
  climate*, Lloyd's Register Foundation, September 2022 (72 pages)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-06/LRF_2021_report2-resilience_online_version.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries)

## What is reproduced

All 722 numbers the report publishes from the poll: every value in Charts 1.1 to 4.6 and
Tables 2.1 to 4.2, and every number in the text, including the executive summary and the
counts of countries. Results are in [`RESULTS.md`](RESULTS.md): 623 match, 9 are within
tolerance, 3 differ and 87 need Gallup World Poll data.

Some charts have no printed values. For these, the scripts compute a summary that is not
compared with a published value:

- **Chart 2.3** (helped a stranger vs neighbours care, by country): only the two medians are
  printed, and both are recorded. The helped-a-stranger axis needs Gallup data.
- **Chart 2.8** (government cares vs National Institutions Index, by country): `C2_8_corr`,
  the country-level correlation. Needs Gallup data.
- **Chart 4.7** (Resilience Index vs % who experienced a disaster, by country): `C4_7_corr`,
  the country-level correlation (-0.21). The text calls it "a modest negative correlation".
- **Appendix 3 histogram** (page 61, distribution of Resilience Index scores): `A3_1_mean` and
  `A3_1_sd`. The y-axis is not labelled, and its scale (a maximum of about 27) does not match
  a count or a percentage of the global sample.

## Method notes

- **Weights:** `PROJWT`, so global, regional and group figures are population-weighted.
- **Base:** everyone asked the question, with don't know and refused included.
- **Countries:** all 121 countries. Regions use `GlobalRegion`. Income groups use
  `CountryIncomeLevel`. Venezuela is not classified (code 9), so it is left out of every
  income-group figure. "Middle-income" (page 12) combines lower-middle and upper-middle income.
- **Urbanisation:** `Urbanicity` 1 = rural areas, 2 = small towns, and 3 and 6 = large
  cities/suburbs.
- **Resilience Index:** the published index `resilience_index` (0–1), averaged with weights.
  The index includes Gallup World Poll items (education, internet and phone access, safe walking,
  helped a stranger, local infrastructure and the National Institutions Index). The release
  has the computed index, so the index findings do not need Gallup data.
- **Lowest-resilience groups (page 36):** "lower income quintiles" means the bottom three
  (`INCOME_5` 1–3). "Rural" means `Urbanicity` 1. Population size is the sum of `PROJWT`
  among group members who have an index score. These definitions reproduce both published
  population sizes to within 500 people. The classification tree is not re-fitted: the
  scripts compute the two groups it identified.
- **Basic needs (Chart 1.3):** uses the pilot's combination of `WP22228` with the follow-ups
  `WP22229` (weeks) and `WP22230` (months). "One month to three months" is around a month,
  two months and three months. Two groups have no follow-up answer: "less than a month" with
  no weeks answer counts as one week to less than a month, and "a month or more" with no
  months answer counts as don't know. This reproduces every segment. "Less than a month"
  (X07, X09) is `WP22228` = 1.
- **Government cares (`gov_cares`):** `WP22231`, with the alternative wordings asked in
  Vietnam (`WP22469`, "the authorities") and Myanmar (`WP22525`). Without these, Southeastern Asia
  in Chart 2.6 is 31% 'a lot' against the published 26%, and the global 'a lot' is 20% against 19%.
- **Governments well prepared (Chart 4.6):** national government is `WP22241` only. Adding
  Myanmar's "government in power" wording (`WP22526`) gives 65% for Southeastern Asia
  against the published 68%.
- **Discrimination:** each type uses the respondents who were asked. "Any discrimination"
  (X20, Chart 2.5) is yes to any of the five types. The three countries that were not asked
  (China, Saudi Arabia, United Arab Emirates) count as "no", as in the pilot. This gives the
  published 21%. Among the countries that were asked, it is 27%.
- **Disaster types (Charts 4.1, 4.2):** `WP22247`, as a percentage of all respondents.
  "Other" in Chart 4.2 is every other type named (tornado, thunder or lightning storm,
  tsunami, mudslide, volcano, blizzard, other). "Did not experience disaster" includes don't know
  and refused to `WP22245`.
- **Essential services by disaster (Charts 4.3, 4.4):** respondents who said yes (1) or no
  (2) to `WP22245`. Don't know answers to each service question stay in the base.
- **Most trusted source (Table 4.1):** `WP22240` was asked only of people who would look to
  two or more sources (`WP22233`–`WP22239`). The base is the people who were asked.
- **Climate change and disaster type (Table 4.2):** each type compares people whose last
  disaster was that type with everyone else. "Any type" compares yes and no to `WP22245`.
- **Education:** harmonised `Education` (1 = primary or less), the same item as `WP3117` in
  the report's appendix.
- **Tables of top countries** (Tables 2.1–2.3, 3.3, Charts 1.6, 2.5): the scripts compute the
  countries the report prints. The public data gives the same top countries, in the printed
  order, for Tables 2.2, 2.3 and 3.3 and Chart 1.6. The ten countries labelled on the Chart 2.5
  map are the ten highest in the data.
- **Text lists** (X34, X36, X59) are compared as text: country names in order of the gap or
  percentage, separated by "; ".
- **Gaps** in the text are computed from unrounded values. The "Difference" columns of
  Tables 3.3 and 4.2 were computed from rounded values, so three of them are within
  tolerance rather than exact.
- **Not recorded:** values the charts do not display (under 5% in Charts 1.3 and 2.6, under 1%
  in Chart 4.2). The scripts still compute them (see `output/`). Phrases such as "less than half",
  "at least two-thirds" or "in two regions" are also not recorded when they only describe
  values already recorded from the same page or a chart.
- **Chart numbers:** the PDF text layer contains older captions (for example "Chart 2.9" for
  Chart 3.1, "Chart 3.1" for Chart 4.1). The IDs use the chart numbers printed on the page.
- **Tolerance:** ±1 point for percentages; 0.01 for Resilience Index scores; 0.1 for the
  one-decimal shares in Chart 4.1 and X48, and 0.01 for the tsunami share (0.03%); 0 for counts of
  countries and respondents; 1,000 for the two population sizes printed to the thousand.

## Gallup World Poll data

87 findings need Gallup World Poll items that are not in the public release. These items
must be licensed from Gallup directly. The code is included. Without the data, these findings
are reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item | Question | Findings |
| --- | --- | --- |
| `WP16056` | Access to the internet | X10, Chart 1.4 (internet), Chart 1.5 |
| `WP17626` | Has a mobile phone | Chart 1.4 (mobile phone) |
| `WP110` | Helped a stranger in the past month | X17, X18, Chart 2.2, Chart 2.3 median |
| `WP97`, `WP93`, `WP92` | Satisfied with quality healthcare / schools / roads (2 = dissatisfied) | Table 2.1 |
| `INDEX_NI` | Gallup's National Institutions Index, 0–100 | Chart 2.7, Chart 2.8, X64 |

`WP16056`, `WP17626`, `WP110`, `WP92`, `WP93` and `WP97` are the item codes given in the
report's Appendix 3. `INDEX_NI` is a placeholder name for Gallup's National Institutions
Index. The index averages confidence in the military, the judicial system, the national
government and the honesty of elections (GWP items usually coded `WP137`, `WP138`, `WP139`
and `WP144`). Check the name with Gallup. X64 (the eight countries with indicative scores)
also needs this index, to tell which countries lack it.

The public data has a related item, `WP22222` ("used the internet in the past 30 days"). It is
not the item the report uses: it gives 22%, 41%, 76% and 89% by income group, against the
published internet access figures of 27%, 43%, 81% and 91%. The scripts do not use it as a
substitute.

## External data

None. The World Bank income groups are in the data (`CountryIncomeLevel`, FY2021-22). The
report also quotes statistics from other organisations. These are context and are not
recorded:

- ILO: 80 million full-time jobs could be lost to heat stress by 2030 (page 13).
- UN ESCAP: $86.5 billion in annual losses from natural hazards in Southeastern Asia (page 17).
- Over six million people have left Venezuela since 2015 (page 23).
- Serfilippi and Ramnath (2018): 76 resilience indicators (pages 10, 55).
- 2017 Iran earthquake, more than 500 deaths; 2020 Izmir earthquake, 116 deaths (page 38).
- UN OCHA: flooding affected 1.4 million people in Central and Western Africa in 2021, and
  displaced about 378,000 in 12 countries (page 39).
- Iceland in 2021: 14 earthquakes of magnitude 5.0 or above, and the longest eruption in 50
  years, 25 miles from Reykjavik (page 44).
- World Bank: the United States has the highest income inequality of any high-income
  country (page 33). Guinea, Mali and Sierra Leone have among the lowest GDP per capita
  (page 22).

## Findings that do not match

3 findings differ from the published values:

- **X29:** the text says "half" of the 12 countries in Table 2.3 are in Latin America. The
  table itself lists five: Honduras, Paraguay, Venezuela, Panama and Colombia. The data agrees
  with the table.
- **X30 (Southern Europe):** the text says more than 50% say the government does not care at
  all in five of the 12 Southern European countries. The data gives six, because Portugal is at
  50.4%. The report may have counted Portugal as 50%.
- **X36:** the text says urban/rural gaps of 0.08 or more were "also seen in Algeria, Ghana and
  Sierra Leone". The data agrees for those three, but the United Arab Emirates (0.10) also
  passes the threshold, and the report does not name it. Not explained. The paragraph is about
  Africa, so the list may include only African countries.

9 more findings are within tolerance but do not round to the published figure:

- **C3_1 (Southeastern Asia):** 0.640 against the published 0.65. Excluding Cambodia, Laos
  and Vietnam (indicative scores) gives 0.630, and `WGT` gives 0.636. Not explained.
  Every other region matches.
- **C2_1 (large cities/suburbs):** 19.0% against 18%. Large cities alone give 17.6%, but
  the same grouping gives the published 0.58 in Chart 3.2.
- **X09 (Northern Africa):** 49.6% against 49%. This is the sum of the two rounded chart segments (24 + 25).
- **X40 (government does not care at all):** 44.7% against 44%. `WP22231` alone gives 44.4%.
- **T3_3 (Afghanistan and Ecuador differences), T4_2 (earthquake difference):** the report
  subtracted the rounded values.
- **X42, X44 (population sizes):** within 500 of the figures printed to the nearest thousand.

## Run

```
python reports/WRP_2021/core_a_resilient_world/reproduce.py
Rscript reports/WRP_2021/core_a_resilient_world/reproduce.R
```
