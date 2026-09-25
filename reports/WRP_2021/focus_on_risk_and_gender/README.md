# World Risk Poll 2021 Focus On: Risk and Gender

- **Report:** *World Risk Poll 2021 Focus On: Risk and Gender*, Lloyd's Register Foundation, March 2023
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-04/WRP2021_FocusOn_Gender_0.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries)

## What is reproduced

All 497 numbers in the report: every value in Charts 1.1 to 4.10 and Tables 1.1 and 2.1,
and every number in the text, including the percentage-point gaps between women and men.
Results are in [`RESULTS.md`](RESULTS.md).

## Method notes

- **Groups:** `Gender` (1 = male, 2 = female); the report calls this sex.
- **Weights:** `PROJWT`, so the global figures are population-weighted.
- **Base:** everyone asked the question, with don't know and refused included. Questions
  asked only in some countries, or only of some respondents (for example internet users),
  use the respondents who were asked.
- **Gaps** in the text are computed from unrounded values. So a gap can differ by a point
  from the difference between the two rounded figures printed in the chart.
- **Basic needs (Chart 2.2)** combines `WP22228` (less or more than a month) with the
  follow-ups `WP22229` (weeks) and `WP22230` (months). "A month or less" is less than a
  month plus around a month.
- **Any discrimination (Chart 2.8)** is yes to any of the five types (`WP22259`–`WP22263`).
  Respondents in countries that were not asked these questions count as "no". Excluding
  them gives 27.9% of women and 25.5% of men instead of the published 22% and 20%.
- **Never worked (Chart 4.1)** means "respondent has never worked" (code 7) at any of the
  three violence and harassment questions (`WP22400_ALL`, `WP22403_ALL`, `WP22406_ALL`).
- **Chapter 4 base:** everyone else, including China, where the physical violence and
  harassment question was not asked. Chart 4.4 (combinations of forms) is split among those
  who answered yes or no to all three questions, which leaves China out. These definitions
  also reproduce the figures in the full *Safe at Work?* report
  (`reports/WRP_2021/core_safe_at_work/`).
- **Forms of violence and harassment (Charts 4.3, 4.4):** physical, psychological and sexual
  use the `_ALL` versions of the questions, which merge the alternative wordings used in
  some countries. How often each form happened uses `WP22401`, `WP22404_ALL` and
  `WP22407_ALL`, among those who experienced it.
- **Chart 1.3 (experience):** each bar's segments are labelled by position. In the PDF text
  they appear as "no", "yes, know someone", "yes, personally".

## Gallup World Poll data

Findings X04–X07 compare foreign-born and native-born women. They need the Gallup World
Poll item "Were you born in this country?" (`WP4657` in the code: 1 = born in this
country, 2 = born in another country). That item is not in the public release, and must
be licensed from Gallup directly. The code is included; without the data these findings
are reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

The report does not say what the second figure in "51% vs 46%" and "60% vs 41%" is
compared with. The code reads it as native-born women.

## Findings that do not match

14 findings differ from the published values by more than the ±1-point tolerance. Each traces
back to the report itself:

- **Chart 2.4, 6 values:** the "Local government" and "You and your family" panels are
  swapped. Each panel's values match the other panel's question, and the text on the same
  page matches the data (family 5 points, local government 2 points).
- **Chart 4.6, 4 values:** the "ever experienced" values repeat Chart 4.5 (physical).
  Psychological violence and harassment is about 16–17% for both women and men.
- **X22:** page 8 gives the gap in feeling more safe as 2 points; page 4 says 3, and the
  data gives 4.
- **X34:** the text says women are 2 points *less* likely to report discrimination. The
  chart and the data show women 2 points *more* likely.
- **X54 (find out):** the text gives a 12-point gap. The chart on the same page shows 46%
  vs 36%, and the data gives 10 points.
- **C2_9 (men, religion, no):** 87% in the data against 86% published. The published yes
  and no values for this row add up to 98.

51 more findings are within tolerance but do not round to the published figure. Most are
values close to a rounding boundary (x.5), or text gaps that the report took from rounded
figures.

## Run

```
python reports/WRP_2021/focus_on_risk_and_gender/reproduce.py
Rscript reports/WRP_2021/focus_on_risk_and_gender/reproduce.R
```
