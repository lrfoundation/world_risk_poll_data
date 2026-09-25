# World Risk Poll 2021: A Changed World? Perceptions and experiences of risk in the Covid age

- **Report:** *World Risk Poll 2021: A Changed World? Perceptions and experiences of risk in the Covid age*, Lloyd's Register Foundation, July 2022 (60 pages)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-06/LRF_2021_report_risk-in-the-covid-age_online_version_2.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries) and,
  for the comparisons with 2019, `WRP_2019/WRP_2019.parquet` (wave 1; 154,195 respondents, 142 countries)

## What is reproduced

All 1,017 numbers the report publishes from the poll: every value in Charts 1.1 to 5.3, Map 3.1 and
Tables 1.1 to 5.1, and every number in the text, including changes between 2019 and 2021, ratios
("four times as likely") and counts ("in three regions"). Results are in [`RESULTS.md`](RESULTS.md).

Three scatter plots print no values: Chart 2.2 (worry vs experience of work-related harm, by country),
Chart 2.4 (the same for food and water) and Chart 3.2 (satisfaction with healthcare vs feeling less
safe, by country). Chart 4.3 prints only the four income-group totals; its country points carry no
values. Functions `C2_2`, `C2_4`, `C3_2` and `C4_3` compute the country points anyway, in
`output/reproduced_*.csv`, but there are no published values to compare them with. The numbers the text
quotes from these charts (Italy 36%, Guinea 20%, Belgium 3% and so on) are recorded as text findings.

The report does not publish the worry or experience indices (`worry_index_published`,
`experience_index_published`); it uses the individual questions.

## Method notes

- **Weights:** `PROJWT`, so global and regional figures are population-weighted.
- **Base:** everyone asked the question, with don't know and refused included. Worry about harm from
  the work you do (`WP22214`) was asked only of the employed, so it is among workers.
- **Countries:** figures for 2021 alone use all 121 countries. Every comparison with 2019 uses the 119
  countries surveyed in both years (the report says so on page 10). The safety question (`WP20711`)
  and the greatest-risk question (`WP22331`) were not asked in China in 2021, so China is also left
  out of the 2019 figures for those two questions. That reproduces Chart 1.1 exactly (with China,
  2019 'less safe' is 25%, not 30%).
- **Table 1.2 and Chart 1.5** use the 119 countries in both years, although they show 2021 only. With
  all 121, Eastern Europe's road figure is 13% (published 12%), because 39% of the Czech Republic,
  surveyed only in 2021, named road accidents. Every other value in both is the same either way.
- **2019 variables:** safety `L2` (2021 `WP20711`), greatest risk `L3_A` (`WP22331`), climate change
  `L5` (`WP20719`), worry `L6A`–`L6D`, `L6G` (`WP20720`–`WP20723`, `WP20726`), experience
  `L8A`–`L8D`, `L8G` (`WP22442`–`WP22445`, `WP22447`), food-safety source `L14`.
- **Greatest risk, 2019 vs 2021 (Chart 1.3):** the 2019 codes are mapped onto the 2021 codes. 2019 has
  no codes for Covid-19, war or non-weather disasters (the chart shows no 2019 value for them), and no
  code for hunger (the chart shows 1%). 2019 code 16 combines climate change, natural disasters and
  weather, and is compared with 2021 'climate change or severe weather'.
- **Experience of harm:** the 2021 item has four answers: yes personally (1), yes someone I know (2),
  both (3), no (4). The report uses two definitions (page 22):
  - Comparisons with 2019 (Table 2.1, Charts 4.1, the text on pages 22–23, 37–40) count any 'yes'
    (1, 2 or 3), because the 2019 question (yes/no) did not separate the two.
  - Analyses of 2021 alone count 'personally experienced' as 1 or 3.
- **Work-related harm:** personal experience of harm from work (`WP22448`) is taken over everyone who
  answered it, not only workers. The report calls them workers, but only the full base reproduces
  Chart 2.1 (15 of 15 regions), Chart 2.3, Table 2.2 (60 of 60) and the country figures in the text
  (Italy 36%, Guinea 20%, Belgium 3%). Among workers only, Italy is 38%, Southern Asia 31% (published
  28%) and Middle East 15% (published 11%). Worry about work is among workers, as asked.
- **Differences and ratios are computed from the rounded percentages.** This is what the report does:
  the 'difference' columns of Chart 1.2 and Table 1.1 are differences of the printed figures (Northern
  America 37 − 26 = 11; unrounded, 10.4), the text's 'five-point increases' are 27 − 22 and 25 − 20
  (unrounded, 5.7 and 5.3), and the Table 2.1 ratios are ratios of the printed percentages (traffic
  37 / 32 = 1.2; unrounded, 1.1). Unrounded values would give five mismatches in Chart 1.2, one in
  Table 1.1 (Myanmar, 47 against 48) and four in Table 2.1. Counts against a threshold stated with rounded figures ('at least 30%', 'a 10-point gap')
  also use the rounded figures, and the note on each row says so.
- **Climate change, Table 5.1:** 'don't know' is code 98 only, and the total is 'not a threat' plus
  'don't know', so refused answers are in the base but in neither column. Latin America 2021 then gives
  8 + 6 = 15 as published; including refused gives 17. Charts 5.1 and 5.2 show 'don't know/refused'
  together.
- **Severe weather harm groups (Chart 5.3):** had experienced harm (personally or both), know someone
  who had, neither. Don't know and refused are left out, as in the chart.
- **Groups:** `GlobalRegion` (the report's 15 regions), `CountryIncomeLevel` (Chart 4.3), `INCOME_5`
  (within-country income quintiles), `IncomeFeelings` (feelings about household income, Chart 2.3 and
  Table 2.2), `Education`, `AgeGroups4`, `Gender`.
- **Population counts** (India's 233 million injured workers, China's 360 million who don't know about
  climate change, the United States' 89% of Northern America) are sums of `PROJWT`, which adds up to
  each country's adult population.
- **'<0.5'** values are recorded as 0 with a tolerance of 0.5, so they match when the reproduced value
  is under 0.5.
- **Approximate wording** ('about one-third', 'about half', 'about six in 10', 'about 233 million') is
  recorded with a wider tolerance, given in the row.

## Gallup World Poll data

Nine findings need Gallup World Poll items that are not in the public release. They must be licensed
from Gallup directly. The code is included; without the data these findings are reported as
`GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

| Findings | Gallup World Poll item | Code used |
| --- | --- | --- |
| X17 (page 13) and Chart 3.2 | "In the city or area where you live, are you satisfied or dissatisfied with the availability of quality healthcare?" | `GWP_HEALTHCARE_SATISFACTION` (placeholder; 1 = satisfied) |
| X29 (page 19) | "Ideally, if you had the opportunity, would you like to move permanently to another country, or would you prefer to continue living in this country?" | `WP1325` (1 = move to another country) |
| X32 (page 19) | Satisfaction with the roads and highways | `GWP_ROADS_SATISFACTION` (placeholder; 1 = satisfied) |

The healthcare and roads item codes are placeholders: confirm the Gallup item codes and codings when
requesting the data. X29 and X32 are quoted from "Gallup's 2021 World Poll", which covered more
countries than the World Risk Poll, so the 16% global figure may not be reproducible from the World
Risk Poll respondents alone.

`IncomeFeelings` (feelings about household income), which is also a Gallup World Poll item, is in the
public release, so Chart 2.3 and Table 2.2 use public data.

## External data

None is needed. The report also quotes figures from other organisations, which are context and not
reproduced: homicide rates in Latin America (22.3 per 100,000 in 2015, against 5.3 worldwide; World
Bank, page 18), 677 workplace deaths in Italy in January–July 2021 (Italian media, page 26), a $500
million World Bank programme for India's informal workers (page 27), 14.9 million excess deaths and
81% of excess deaths in middle-income countries (WHO, page 35), a 25% rise in anxiety and depression
(WHO, page 38), 'more than 200 medical journals' (page 45) and the 375 million daily reach of the WMO
network of weather presenters (page 50).

## Findings that do not match

3 findings differ from the published values by more than their tolerance:

- **T1_1_TUR_diff (Table 1.1, Turkey):** the table prints a 25-point increase in 'less safe', but its
  own figures are 34% (2019) and 50% (2021), a 16-point increase. The data gives 34.5% and 50.1%. The
  25 looks like a typo; Turkey is still fifth largest at 16 points.
- **C1_3_hunger_2019 (Chart 1.3):** the chart shows 1% naming hunger in 2019, but the 2019 file has no
  hunger code, so the reproduction gives 0. 2019 'other' is 6.6% in the data against 6% published,
  so the report probably recoded some 'other' answers as hunger. Not reproducible from the public data.
- **X53_CAN (page 27):** Canadian workers finding it very difficult on their income: 24% published,
  22.9% in the data. Only 32 respondents are in this group. Workers only gives 31.6%, excluding don't
  know changes nothing, and 'yes, personally' alone gives 15.7%. The United States (33%) and Northern
  America (32%) in the same sentence match. Not explained.

13 more findings are within tolerance but do not round to the published figure:

- Seven are approximate wording with a wider tolerance: X50 ('about one-third', 32.4%), X52 ('about
  233 million', 233.6 million), X73 ('about half', 52.2% and 51.1%), X78 ('about one-third', 30.8% and
  32.4%), X84 ('about 360 million', 360.2 million), X88 ('about six in 10', 58.3%).
- **X90_road:** 'about one in four' of those naming road accidents felt less safe; Chart 1.4 prints 26
  (25.6%).
- **X24_crime:** the text says road accidents, personal health and crime were each in the top three
  named risks in 11 of the 15 regions. Road accidents and personal health are; crime is in 10.
- **C1_3_other_2019:** 6.6% against 6%, probably because 2019 hunger answers are in 'other' (above).
- **T2_1_mental_2019_ratio:** 19 / 20 = 0.95, which the report rounds up to 1.0.
- **T3_1_southern_europe_middle:** 3.5%, printed as 4; a rounding boundary.

## Run

```
Rscript reports/WRP_2021/core_a_changed_world/reproduce.R
python reports/WRP_2021/core_a_changed_world/reproduce.py
```
