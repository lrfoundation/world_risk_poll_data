# World Risk Poll 2021: Safe at Work? Global experiences of violence and harassment

- **Report:** *World Risk Poll 2021: Safe at Work? Global experiences of violence and harassment*, Lloyd's
  Register Foundation, January 2023 (52 pages). It was published alongside the ILO report *Experiences of
  violence and harassment at work: A global first survey*, which uses the same data.
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-06/LRF_2021_report_safe-at-work.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries).
  One text finding (X19, Australia in 2019) uses `WRP_2019/WRP_2019.parquet`.

## What is reproduced

All 504 numbers in the report. This covers every labelled value in Charts 1.1 to 1.10, 2.1 to 2.3 and 3.1 to
3.8, and in Tables 1.1, 1.2, 3.1, 3.2 and Appendix 3 Table 1. It also covers every number in the text,
including percentage-point gaps and the respondent counts in Appendix 3. The income-group column of Table 1.1
and the order of the regions in Table 1.2 are recorded as text findings. Chart segments that have no label
(for example don't know/refused) are not recorded. Results are in [`RESULTS.md`](RESULTS.md).

## Method notes

- **Weights:** `PROJWT`, so the global, regional and income-group figures are population-weighted.
- **Base ("ever worked"):** everyone who did not say "respondent has never worked" (code 7) at any of the three
  violence and harassment (V&H) questions (`WP22400_ALL`, `WP22403_ALL`, `WP22406_ALL`). This is 113,873
  respondents, as stated on pages 12 and 45. **China is in the base.** China was not asked the physical question,
  but it was asked the psychological question and a modified form of the sexual question. The Focus On: Risk and
  Gender report's code also requires `WP22400_ALL` to be present, which drops China (see below).
- **Any V&H:** yes to any of the three `_ALL` questions. The `_ALL` versions add the countries that are missing
  from the standard variables: the United Arab Emirates and Uzbekistan for physical, China for psychological
  ("psychologically hurting"), and China, Algeria, Jordan, Morocco and Pakistan for sexual ("unwanted intimate
  physical contact"). A question that was not asked counts as not experienced:
  physical in China, and sexual in Saudi Arabia, the United Arab Emirates and Iraq. Don't know and refused stay in
  the base. Each form's own chart (Charts 1.8 and 1.9) uses the respondents in the base who were asked that
  question.
- **When last experienced (Chart 1.1, X13, X14):** the most recent timing given for any of the forms experienced
  (`WP22402`, `WP22405_ALL`, `WP22408_ALL`).
- **How often (Chart 1.10, Table 1.2, X29):** among respondents in the base who experienced that form, the only ones
  asked. "Multiple" and "more than three times" in the text mean three or more times (codes 2 and 3).
- **"More than once" (X04, 58.5%):** the report does not say how this was computed. The code counts each form a
  person experienced separately and takes the share of those experiences that happened three or more times
  (58.2%). Counting people who experienced any form three or more times gives 60.3%. Adding "or more than one
  form" gives 65.8%.
- **Number of forms (Charts 2.1, 2.3 and 3.1; X07, X30, X31, X33, X34):** among respondents in the base who
  experienced any form.
- **Combinations of forms (Chart 2.2; X08, X32):** these use only respondents who answered yes or no to all three
  questions. That excludes China, Saudi Arabia, the United Arab Emirates and Iraq, and anyone who answered don't
  know or refused. This base reproduces every labelled value, for example men 49.2% psychological only and 19.7%
  psychological and physical. The Chart 2.1 base gives 53.7% and 13.8% instead. Chart 2.1 itself needs the full
  base: on the complete-answer base, men are 69.6%, 25.3% and 5.1% against the published 74%, 23% and 4%.
- **Discrimination (Charts 1.6, 1.7 and 2.3; X24, X25, X33):** "any discrimination" is yes to any of the five types
  (`WP22259` to `WP22263`). As in the Focus On: Risk and Gender report, respondents in countries that were not
  asked (China, Saudi Arabia, the United Arab Emirates) count as no. If they are excluded, "no discrimination" gives
  13.2% instead of the published 16%. In Chart 1.7 both bars show the percentage who experienced V&H. The short
  bar is those who answered no to that type of discrimination and the long bar is those who answered yes. The
  legend labels them "no experience" and "experience" of V&H.
- **Never worked (Chart 1.5, X23):** a percentage of all respondents.
- **Education (Chapter 3):** `Education` (1 primary, 2 secondary, 3 tertiary). "Told someone" (`WP22409`) is among
  those who experienced any V&H. Whom they told (Table 3.1, `WP22410`–`WP22414`, `WP22421`) is among those who told
  someone. Reasons (Table 3.2, `WP22415`–`WP22420`) are among those who did not tell anyone.
- **Income quintiles (Charts 3.4 and 3.6 to 3.8):** `INCOME_5`, which is within-country per-capita income
  quintiles. **Income groups:** `CountryIncomeLevel`.
- **Appendix 3 counts (X41 to X44, Table A3.1):** the questions were asked in the order physical, psychological,
  sexual. In China they were asked in the order psychological, sexual. The "99 respondents" who first said yes and
  then said they had never worked are 99 yes answers from 91 respondents. The 63% women (X43) is an unweighted
  share of respondents.
- **World Risk Poll 2019 (X19):** the 39% of Australian women and 24% of men are `L21D` in the 2019 data
  ("experienced harm while working in the past two years: physical harassment or violence", asked of those who
  work).
- **Gaps** in the text are computed from unrounded values.
- **Rounding in the charts:** chart labels seem to have been rounded from values already rounded to one decimal.
  For example, 45.47% becomes 45.5% and then 46%. This explains the chart values that are 1 point off at an x.5
  boundary (C1_3_middle_east_women, C1_7, C2_1_men_three, C3_1_secondary_none, C3_2_primary_no).

## Gallup World Poll data

The Chapter 3 comparison of foreign-born and native-born workers (Charts 3.3 to 3.8 and text findings X11, X12,
X38, X39, X40; 76 values) needs the Gallup World Poll item "Were you born in this country?". The code calls it
`WP4657` (1 = born in this country, 2 = born in another country), as the Focus On: Risk and Gender report does.
The item is not in the public release and must be licensed from Gallup. See
[`reports/README.md`](../../README.md#gallup-world-poll-data). The code is included, and without the item these
findings are reported as `GALLUP_ONLY`. The Gallup code was run with a synthetic `WP4657` file, and Python and R
agree.

Page 6 gives native-born women as 21.5% (X11_native). Page 33 and Chart 3.3 give 21.0% and 21% (X38_women_native,
C3_3_women_native). Both are recorded. Charts 3.6 and 3.7 are titled as V&H among women who experienced each type
of discrimination. The text describes the values the other way round: the percentage who experienced the
discrimination among women who experienced V&H. The code follows the text.

## External data

None is used. The report quotes these statistics from other sources. They are not reproduced:

- Australian Unions (ACTU) 2018: 54.8% of employed Australians had experienced sexual harassment at work (page 15).
- Eurofound 2015: 22.6% of workers in Finland reported "adverse social behaviour", the highest level of 29
  European countries (page 15).
- World Happiness Report 2022 and 2022 Social Progress Index rankings (page 14).

The World Bank's historical country classification (`OGHIST.xlsx`,
https://databankfiles.worldbank.org/public/ddpext_download/site-content/OGHIST.xlsx, checked 25 September 2026)
was used only to explain the Lebanon income-group finding. The code does not use it.

## Findings that do not match

3 findings differ from the published values:

- **T1_1_LBN_income:** Table 1.1 lists Lebanon as lower-middle income. `CountryIncomeLevel` (World Bank FY2021-22,
  at the time of fieldwork) is upper-middle. The World Bank reclassified Lebanon as lower-middle income for FY2023
  (July 2022), which is the classification the report uses. All other income groups in the table match, and the
  income-group charts match the data's classification.
- **X16 (74,364 respondents employed at the time of polling):** this is the base of the ILO report. Employed
  respondents in `EMP_2010` (codes 1, 2, 3 and 5) number 74,500. China has no `EMP_2010` in the public data. The
  ILO report's exact filter is not given. Not explained.
- **X42 ("1,295 respondents"):** the sentence on page 45 is garbled, and it is not clear what it counts. None of the
  counts tried matches: respondents asked a modified wording, those who said they had never worked at the sexual
  question, and those not asked. The code reports the respondents outside China who reached the modified sexual
  question (3,004). Not explained.

30 more findings are within tolerance but do not round to the published figure:

- **Charts at an x.5 boundary (6 values):** see the rounding note above. Rounding twice matches every labelled
  chart and table value that rounding once matches, plus these six.
- **Frequency by region (X29, Table 1.2; 9 values):** five of the regional and country values (eight findings,
  since Table 1.2 repeats the text) are 0.1 above the data. Adding the rounded "three to five times" and "more than
  five times" shares reproduces them, except Australia and New Zealand sexual (65.4 published, 65.3 either way).
  X29_physical is 55.6 in the data against 55.5 published.
- **Number of forms (X07, X30_two, X33_multiple_none, X34; 5 values):** 0.1 away from the data (for example,
  multiple forms 27.8% against 27.7%). Not explained.
- **Men's small segments in Chart 2.2 (2 values):** both are labelled 4.5%. The data gives 4.69% (sexual only) and
  4.75% (sexual and psychological).
- **X04** (58.5%, see the method notes); **X08_women** (32.9 published, 33.0 in the data); **X14** (the footnote's
  0.2% who did not know when; 0.28% in the data, over all forms); **X20** (page 15 gives Finland 47.0%, while
  Table 1.1 and the data give 47.9%); **X25_religion_men** (41.4 against 41.3); **X36_DEU** (15.1 against 14.6;
  only 11 German women in the base have primary education); **X36_ITA** (6.55 rounds to 6.6); and
  **X29_sexual_northern_america_gap** ("not seen": 0.7 points in the data).

## Relation to the Focus On: Risk and Gender report

Chapter 4 of *Focus On: Risk and Gender* ([`../focus_on_risk_and_gender/`](../focus_on_risk_and_gender/))
summarises this report. Its README lists men's figures it could not reproduce: 22% of men experienced any V&H and
5% sexual V&H (Charts 4.3 and 4.7, text gaps X44 and X50). This report gives the same figures as 21.9% and 4.6%.
Both reproduce here once China is kept in the base (21.93% and 4.63%). The women's figures are unchanged or also
match: 19.8%, and 6.5% sexual. The Focus On code drops China by also requiring `WP22400_ALL`. Its Chart 4.4 is this
report's Chart 2.2, and it matches exactly on the complete-answer base described above, including X45 (33% and
15%). The pilot folder has not been changed.

## Run

```
python reports/WRP_2021/core_safe_at_work/reproduce.py
Rscript reports/WRP_2021/core_safe_at_work/reproduce.R
```
