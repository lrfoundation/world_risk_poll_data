# World Risk Poll 2021: A Digital World

- **Report:** *World Risk Poll 2021: A Digital World. Perceptions of risk from AI and misuse of personal data*, Lloyd's Register Foundation, November 2022
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-04/LRF_2021_report_a-digital-world-ai-and-personal-data_online_version_1.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries).
  The 2019 comparisons also use `WRP_2019/WRP_2019.parquet` (wave 1).

## What is reproduced

All 501 numbers in the report: every value in Charts 1.1 to 3.8, Map 1.1 and Tables 1.1 and
1.2, and every number in the text, including the percentage-point gaps and the counts of
countries and regions. Results are in [`RESULTS.md`](RESULTS.md).

Chart 3.3 (the percentage very worried about theft of personal information against the World
Justice Project Rule of Law Index) prints no values, so there is nothing to compare. The
script still computes it: across the 110 countries with both figures, the correlation is
−0.42, which agrees with the report's statement that worry is higher where the rule of law
is weaker. The result is in `output/reproduced_*.csv` (`C3_3_correlation`,
`C3_3_n_countries`), not in `RESULTS.md`.

Figures that the report quotes from other organisations are not recorded. They are context
only: the ITU's 782 million people who came online between 2019 and 2021 and "more than a third"
still offline; UNCTAD's 71% of countries with data protection laws, 9% with draft laws and 48%
among least developed countries; the 11 paths of harm in Kröger et al. (2021); the "20 times"
credit limit in the Apple Card case; and the Stanford AI Index and private-investment
rankings. Verbal quantities ("about half", "two in five", "in six regions") are not recorded
unless the report also gives a number.

## Method notes

- **Weights:** `PROJWT`, so the global and regional figures are population-weighted.
- **Base:** everyone asked the question, with don't know and refused included. The one
  exception is Chart 3.7 (see below).
- **AI question (`WP22227`):** 1 = mostly help, 2 = mostly harm, 3 = don't have an opinion,
  4 = neither (volunteered), 98/99 = don't know/refused. "Don't know" in the charts and text
  is 98 and 99 together. "No opinion/don't know" in Table 1.1 and the text is 3, 98 and 99.
- **Help/harm ratios (Chart 1.2, Map 1.1, X13)** are the rounded "mostly help" percentage
  divided by the rounded "mostly harm" percentage, as the report calculated them. Unrounded
  ratios give 1.6 for Australia & New Zealand (published 1.7) and 0.7 for Southern Africa
  (published 0.6). The tolerance for ratios is 0.1.
- **Gaps** in the text and the net scores in Table 1.1 are computed from unrounded values. The
  report subtracts rounded figures, so four net scores and three text gaps are a point away
  (`WITHIN_TOLERANCE`).
- **Discrimination (Chapter 1):** experienced discrimination because of skin colour
  (`WP22259`), ethnic group/nationality (`WP22261`) or gender (`WP22262`). "Not experienced"
  is everyone else who was asked, including don't know. China, Saudi Arabia and the United
  Arab Emirates were not asked and are excluded, as the report's footnote 29 says. (Counting
  only those who said "no" to all three gives 8% don't know instead of the published 9%.)
- **Discrimination (Chapter 3, Chart 3.8):** the number of forms experienced out of five: skin
  colour, religion, ethnic group/nationality, gender and disability (`WP22259`–`WP22263`),
  among internet users in countries where the questions were asked. "Experienced
  discrimination" in X73 is one form or more.
- **Internet users** are those who used the internet in the past 30 days (`WP22222` = 1), as
  the report's footnote 48 defines them. Only they were asked about personal information.
  China's internet users were not asked. Saudi Arabia and Algeria were not asked the
  government item.
- **Government use of personal information** combines `WP22224` with the wordings used in
  Tajikistan and Vietnam ("the authorities", `WP22468`) and Myanmar ("the government in
  power", `WP22524`). Without them, Southeastern Asia is 57% very worried instead of the
  published 52% (Chart 3.5).
- **Chart 3.7, companies series:** don't know and refused are left out of the base. This
  reproduces all four bars (34, 41, 46, 52) and the 52% in the text. With them kept in, the
  values are 33.5, 40.2, 45.1 and 50.7. The government series in the same chart matches with
  don't know kept in, as in every other chart.
- **Trends (Charts 2.1, 2.4, X10, X11, X37–X40, X47, X59)** use the 119 countries surveyed in
  both 2019 and 2021 (the 121 countries of 2021 minus Czech Republic and Iceland). The 2019
  variables are `L26` (internet use) and `L4C` (AI will help or harm). Income groups use each
  country's 2021 World Bank group (`CountryIncomeLevel` in the 2021 file) in both years. The
  2019 file's own groups give 30% for lower-middle-income countries in 2019, not the
  published 31%.
- **Education:** `Education` 1 = primary or less, 2 = secondary, 3 = post-secondary. **Age:**
  `AgeGroups4`; "under 50" is 15–29 and 30–49 together. **Income quintiles:** `INCOME_5`.
  **Feelings about household income:** `IncomeFeelings` (Gallup's `WP2319`, which is in the
  public release).
- **Regions:** `GlobalRegion`, which matches the report's Appendix 2.
- **Text answers:** X32 (the country most likely to feel safe in a driverless car) and X44
  (the region with the widest gender gap in internet use) are compared as text.

## Gallup World Poll data

61 findings need Gallup World Poll items that are not in the public release. These items
must be licensed from Gallup directly. The code is included. Without the data, these findings
are reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item | Question | Findings |
| --- | --- | --- |
| `WP16056` | "Do you have access to the internet in any way, whether on a mobile phone, a computer, or some other device?" (1 = yes, 2 = no) | X18, X20, X25, X35, X60, Chart 1.3, Chart 1.8 (internet access groups) |
| `WP119` | "Is religion an important part of your daily life?" (1 = yes, 2 = no) | X22–X25, Chart 1.4 |
| `WP139` | Confidence in the national government (1 = yes, 2 = no) | X71, Chart 3.6 |

The report does not give the item codes. `WP16056` is the code that the 2021 report *A
Resilient World?* gives for internet access in its Appendix 3; its question wording is printed
in that report. `WP119` and `WP139` are the usual Gallup World Poll codes for these questions.
Check all three with Gallup.

"Access to the internet" (Charts 1.3 and 1.8) is not the public `WP22222` ("used the internet
in the past 30 days"). Using `WP22222` instead gives 44/27/22/5 and 31/31/23/14 in Chart 1.3
(published 44/26/22/5 and 28/32/23/15). In Chart 1.8 it gives 30/29/35 with access and 22/22/27
without (published 31/30/35 and 21/20/26). The scripts do not use it as a substitute.

## External data

- **World Justice Project Rule of Law Index 2021** (Chart 3.3). **Not redistributed here**,
  because the WJP data carries no open licence. Download it with
  `python reports/external/fetch_external.py wjp`, which writes
  `reports/external/downloaded/core_a_digital_world__wjp_rule_of_law_index_2021.csv`. Without
  it, Chart 3.3 is reported as `EXTERNAL_ONLY`. Overall score (0–1) for 139 countries, from the sheet "WJP ROL Index 2021 Scores" of the
  WJP historical data file,
  https://worldjusticeproject.org/rule-of-law-index/downloads/2025_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx,
  downloaded 25 September 2026. Licence: not stated in the file. The WJP publishes the Index
  data for free download and asks users to cite the WJP Rule of Law Index. 111 of the 121 poll countries have a score; China has no
  personal information data, which leaves 110.

## Findings that do not match

2 findings differ from the published values by more than their tolerance:

- **X29 (16 countries):** the report counts 16 countries where "mostly harm" is at least 10
  points higher among people who experienced discrimination based on race/nationality, skin
  colour or sex. The data gives 15. Of the 16 countries named in footnote 30 and on page 18,
  13 meet the rule. Afghanistan, Switzerland and Sweden have gaps of 9.7 to 9.9 points.
  Armenia (13.4) and Uzbekistan (14.9) meet the rule but are not named. Rounding the gaps to
  whole points gives 18 countries. The executive summary defines the groups by "skin colour,
  race/nationality or religion": that definition gives 27 countries. Excluding don't know
  from the AI question, or counting as "not experienced" only those who said no to all three
  questions, does not give 16 either. Not explained.
- **X56_women:** the report says 43% of women in Southern Asia with secondary education used
  the internet. The data gives 40.8% for the region (PROJWT; 42.1% with `WGT`). India alone
  gives 43.0%, so the report may have quoted the Indian figure. The men's figure (61%)
  matches the region.

12 more findings are within tolerance but do not round to the published figure. X05 (30%)
adds the rounded 22% and 8%; the unrounded sum is 30.6%. X63 (75%) is 74.2%; the executive
summary gives 74% for the same figure (X62). X46 ("just 10%" of women in Southern Asia with
primary education or less) is 9.4%. The rest are the four Table 1.1 net scores and the three
text gaps described above (X53, X59_65plus, X59_15_29), and two values close to a rounding
boundary (Germany "mostly harm" 19.5%, internet use at 65+ 46.5%).

## Run

```
Rscript reports/WRP_2021/core_a_digital_world/reproduce.R
python reports/WRP_2021/core_a_digital_world/reproduce.py
```
