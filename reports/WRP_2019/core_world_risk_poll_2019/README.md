# The Lloyd's Register Foundation World Risk Poll: Full report and analysis of the 2019 poll

- **Report:** *The Lloyd's Register Foundation World Risk Poll: Full report and analysis of the 2019 poll*,
  Lloyd's Register Foundation, 2020 (215 pages)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-11/LRF_WorldRiskReport_Book_03.03.22%20Small_0.pdf
- **Data:** `WRP_2019/WRP_2019.parquet` (World Risk Poll 2019, wave 1; 154,195 respondents,
  142 countries and territories)

## What is reproduced

The whole report except the questionnaire (Appendix 1) and the references (Appendix 2), which
have no findings: the Preface, Foreword, Executive Summary, Introduction, Chapters 1 to 10 and
Appendix 3 (printed pages i–178 and 208–209; PDF pages 1–183 and 213–214). The chapters are:

1. *How safe do we feel?*
2. *The sources of greatest risk in people's lives*
3. *The risk perception gap*
4. *Influencing understanding of risk*
5. *Risk at work*
6. *Climate change risk*
7. *Technology-related risk perceptions*
8. *Internet-related risk perceptions*
9. *Food and water risk*
10. *Forecasting risk*

That is 2,432 findings: every value in Charts 1.1 to 10.4 and Tables 1.1, 1.2 and 5.1, and
every number in the text, footnotes and key findings that comes from the poll, including the
percentage-point gaps and counts. For Chapter 10 these are the recorded 2019 values; the 2020
and 2021 forecasts cannot be computed from the poll (see
[Chapter 10 forecasts](#chapter-10-forecasts-not-reproducible)). Results are in
[`RESULTS.md`](RESULTS.md).

Of the 2,432 findings, 2,179 match the published figure (`MATCH`), 123 are within tolerance
(`WITHIN_TOLERANCE`), 41 are different (`DIFFERENT`), 88 need Gallup World Poll data that is
not public (`GALLUP_ONLY`) and 1 needs external data that is no longer published
(`EXTERNAL_ONLY`). These counts are with the Freedom House and WHO files downloaded (see
[External data](#external-data)). Python and R give the same value for every finding.

Module-level names in the Chapters 3–5 and 6–10 sections of the scripts carry `p2_` and `p3_`
prefixes.

## Method notes

- **Page numbers:** the `page` column in `published_figures.csv` is the printed page number.
  PDF page = printed page + 5; the Preface and Foreword are pages i and ii.
- **Finding IDs** carry the chapter number (for example `X6_01`, `C7_2_eastern_europe_help`,
  `A3_middle_east`).
- **Weights:** `PROJWT`, so global, regional, income-group and other group figures are
  population-weighted. Country figures are the same under `WGT`.
- **Base:** everyone asked the question, with don't know and refused kept in the
  denominator. This reproduces the headline figures (for example 41% / 28% / 13% / 18% on
  climate change). Questions asked only of some respondents use those respondents: the work
  items (`L19`–`L21`) are asked of workers, the internet worry items (`L27A`–`C`) of internet
  users, and the government items (`L16A`–`C`) were not asked in Saudi Arabia and
  Turkmenistan. Exceptions are given under each chapter below.
- **Global** figures cover all 142 countries.
- **Regions:** `GlobalRegion` (15 regions) reproduces every regional chart. It matches the
  country lists in Appendix 3 exactly. The file's other region variables (`REG_GLOBAL`,
  `REG2_GLOBAL`) are Gallup's own groupings; the only use of them is `REG_GLOBAL` = 1 for the
  European Union average in Chapter 4.
- **Income groups:** `CountryIncomeLevel` (World Bank FY2019-20) reproduces the income
  charts. Footnote 16 says the upper-middle-income group had 39 countries; the data have 43
  (see [Findings that do not match](#findings-that-do-not-match)).
- **Other groups:** education is `Education` (0–8, 9–15, 16+ years), age is `AgeGroups4`, and
  feelings about household income are `IncomeFeelings`. All are in the public data.
- **Countries** are keyed by `COUNTRY_ISO3`. Kosovo is `XKX`; Swaziland (Eswatini) is `SWZ`;
  Hong Kong is `HKG`.
- **Rounding:** the report appears to round twice, first to one decimal and then to a whole
  number. Values between x.45 and x.50 are printed rounded up (for example 39.47% printed as
  40, 6.48% as 7). In the Executive Summary to Chapter 2, 18 of the within-tolerance findings
  are of this kind.
- **Gaps** in the text are computed from unrounded values. The gaps printed in Charts 3.5, 3.6
  and 5.4 were taken from the rounded bars, so some differ by a point.
- **Rankings and lists** in the text are text findings. A ranking ("ranked first", "the four
  governments trusted least") has the country's ISO3 code as its value. A list (for example
  "the three regions most likely to say AI will mostly harm") is compared as text, in
  alphabetical order.
- **Population counts** ("equivalent to 1 billion people") are the sum of `PROJWT` over the
  respondents concerned. `PROJWT` sums to 5.36 billion adults. The report's own counts imply
  about 5.8 billion, so its counts are about 8% higher than the data give.
- **Worry Index and Experience of Harm Index:** `worry_index_published` and
  `experience_index_published` times 100.
- **Maps** (Charts 1.4, 2.5, 2.8, 5.2, 8.1, 8.4, 8.8, 9.6 and 9.8) colour every country but
  print only the top three and bottom three countries and the legend range. These are
  compared; the legend ends (`min`, `max`) are the lowest and highest country values. The
  functions return every country's value.
- **Correlations** are Pearson correlations across countries, usually between a country
  percentage (weighted within country) and an external indicator (see
  [External data](#external-data)). The correlations in Chapters 1 and 2 have a tolerance of
  0.05, because the external series have been revised since 2020.
- **Charts that print no values** (the scatter plots in Charts 2.7, 2.9, 3.7, 4.5, 5.14, 7.3,
  7.9, 8.6 and 9.7) have nothing to compare. Their functions return the plotted poll values,
  which appear in `output/` but not in `RESULTS.md`.

### Executive Summary, Preface and Foreword

- **"150,000 people"** is compared with the 154,195 respondents (tolerance 5,000).
- **No risk (E07, E08):** 19% gave "nothing/no risks" as their first response
  (`L3_A` = 19). The "additional 21%" gave it as their second (`L3_B` = 19), out of all
  respondents.
- **Food safety information (E09–E11):** `L14` = 5 (government agency) is the most
  trusted source; famous person (`L13G`) and religious leaders (`L13H`) in low-income
  economies. "About half" has a tolerance of 5.
- **Violence and harassment at work (E13–E19):** working women who said physical
  harassment or violence is a risk to their safety at work (`L20D`) or had experienced
  it (`L21D`, which in 2019 asks "have you or has anyone you work with"). "Over
  two-thirds" has a tolerance of 8.
- **Worry and Experience of Harm indices (E35–E39):** country means of the two indices.
  "Over-worriers" are the five countries with the largest gap (worry minus experience); the
  data give them in the same order as the report.
- **Government trust (E40–E42):** the Government Safety Performance Index (see Chapter 9).
  "25% of the countries" is the share of the 140 countries with a score below 50.

### Introduction

The only poll figure is the number of countries (142). The Introduction's other figures
describe the Gallup World Poll in general and are not recorded (see
[Context](#context-figures-from-other-sources-not-recorded)).

### Chapter 1: How safe do we feel?

- **Safety (`L2`):** 1 = more safe, 2 = less safe, 3 = about as safe. Charts show more
  safe, about as safe, less safe, in that order.
- **Risk as opportunity or danger (`L1`):** 1 = opportunity, 2 = danger, 3 = both,
  4 = neither; don't know and refused make up the last segment. Small segments without a
  label in Charts 1.7 and 1.8 are not recorded.
- **Footnote 34:** each country's mean on a scale of 1 = more safe, 2 = about as safe,
  3 = less safe (don't know excluded), correlated with 2018 GDP per capita and 2018 GDP
  growth.
- **"At least one in three" (X1_35)** counts countries whose rounded percentage is 33 or
  more. **"More than 10 percentage points" (X1_43)** compares the rounded percentages for
  men and women. Both counts match only when the rounded figures are used.
- **Largest gender gap (X1_26):** the report calls Chile's gap the largest. It is the
  largest among high-income economies. Argentina, upper-middle income in the data, has a
  larger one (62% of women against 41% of men feel less safe).

### Chapter 2: The sources of greatest risk in people's lives

- **Questions:** `L3_A` (greatest source of risk to your safety) and `L3_B` (another major
  source). `L3_B` was asked only of people who named a risk at `L3_A`. Its "not asked"
  rows count as not naming anything.
- **Two measures of "first or second response".** The report uses both:
  - *Global figures* (Chart 2.1 and the global statements in the text) add the % naming a
    risk first and the % naming it second. Someone who named the same category twice
    counts twice. For example, road accidents: 15.4% + 8.0% = 23%.
  - *Country, region and group figures* (Charts 2.2–2.14 and the text on them) are the
    % of respondents who named the risk, or any risk in a group, first or second.

  Each measure reproduces its own figures. Neither reproduces the other's: the second
  measure gives 22% for road and 16% for crime globally, against the published 23% and 19%.
- **Groups (Chart 2.2 onwards):** road/transport = codes 1, 2; health = 9, 10; crime = 3;
  financial/economic = 5, 6; environment = 13 (pollution), 16 (climate change, natural
  disasters, weather); food/water = 11, 12; political = 7; no risk = 19. In Chart 2.1 and
  the global text, each code is reported on its own.
- **Urban and rural (X2_25)** use `Urbanicity2`. They do not match (see
  [Findings that do not match](#findings-that-do-not-match)).
- **Chart 2.13** omits Pakistan (7.6% in the data, which would appear as 8%) but includes
  France (7.3%).
- **Freedom House (X2_59–X2_61, X2_63):** the countries where more than half said they
  face no risk (first or second response), classified by the 2020 edition of Freedom in
  the World (see [External data](#external-data)).

### Chapter 3: The risk perception gap

- **Numeracy** (`L12`): correct = "10% is the same as 1 out of 10". "Did not know" on page 53
  is don't know only (41%); for people with 16+ years of education it is don't know plus
  refused (15%; don't know alone is 14.5%). In the lightning comparison (page 58),
  "incorrect" includes don't know, as the report groups them on page 53 (2.15); wrong
  answers only give 2.28.
- **Likelihood ratings** (`L9A`–`L9E`, 0–10): averages exclude don't know and refused;
  the percentages in Chart 3.3 keep them in the base (the chart does not show them).
- **"Country differences explain about 10% of the variation"** (page 60): the report does
  not give its method. The code uses the between-country share of variance (eta squared) of
  each person's mean rating over the five risks, weighted with `WGT`: 11.4%. The five
  single items give 6–11%. Weighting with `PROJWT` gives 17%.
- **Worry Index and Experience of Harm Index:** Chart 3.6's legend says "% Very worried" and
  "% Have experienced", but its values are the two indices. The country-level average gap
  (about 23 points, page 65) is the unweighted mean of the 142 country gaps.
- **Chart 3.7** (Worry Index against Experience of Harm Index) prints no values. The countries
  the text names as examples of "over-worriers" (page 65) are not checked.

### Chapter 4: Influencing understanding of risk

- **Food safety sources** (`L13A`–`L13H`) are asked of everyone. **Most trusted source**
  (`L14`, Charts 4.3 and 4.4) is asked of those who would use at least one source, and
  that is the base.
- **Lost-bag questions** (`L17A`–`L17C`): "very likely" percentages. The **social trust
  score** (page 77) scores very likely 3, somewhat likely 2, not likely at all 1, and
  averages the three questions. Only respondents who answered all three count. The police
  question was not asked in Kuwait, Pakistan and Turkmenistan, which leaves the 139
  countries of footnote 17. Country scores are correlated (Pearson, unweighted) with the
  percentage who trust the food safety authority most (don't know in the base). This gives
  0.530, against the published 0.529. Allowing incomplete answers gives 0.509 (142 countries).
- **Chart 4.5** (social trust against trust in the food safety authority) prints no values.
- **Seat belt laws** (Charts 4.6 and 4.8, page 79): WHO Table A7 (see
  [External data](#external-data)). The six surveyed countries with no national law
  (Afghanistan, Bangladesh, Benin, Liberia, Mexico and Niger) match the text. Nine surveyed
  countries are not in the WHO table (Bahrain, Algeria, Hong Kong, Nicaragua, Sierra Leone,
  Taiwan, Kosovo, Yemen and Zambia). They count as having no law in Chart 4.6 and are left
  out of Chart 4.8. Chart 4.8 groups countries into no law, a law that does not cover all
  occupants ("partial"), and a law that covers all occupants ("full"). It averages the
  country percentages, following the text's "an average of 58% of people".
- **Religion** (footnotes 12–13): the "European Union" average uses `REG_GLOBAL` = 1 (the
  EU-28 in 2019).

### Chapter 5: Risk at work

- **Workers:** respondents employed full or part time (`EMP_2010` 1, 2, 3 or 5), who are the
  respondents asked `L19`–`L21`. The questions on reporting safety problems, responsibility
  and safety rules (`L22`–`L25`) were asked only of those who work for an employer, and use
  that base.
- **Occupation** is `EMP8B`. "About/nearly 600 million" injured workers is the sum of
  `PROJWT` over workers who have been seriously injured (565 million).
- **Harm at work** (`L21A`–`L21E`) is harm to the respondent or someone they work with.
  "Three or more causes" and "no injuries / all five types" count the yes answers.
  Mental health harm is `L8G`.
- **Southern Asia agriculture (X5_17):** the text describes the 32% of men and 32% of women
  as those "who work in the region's large agricultural sector". The data gives 32.2% and
  31.6% as the injury rates among the region's agricultural workers, which is the reading
  used. As shares of workers in agriculture, the data gives 39% and 41%.
- **Chart 5.2 legend:** the ends (3% and 68%) are the lowest and highest country values,
  3.9% (Poland) and 68.7% (Sierra Leone), truncated rather than rounded.
- **Chart 5.4 gaps** are absolute differences. **Chart 5.7** shows each region's top risk,
  excluding trips and falls. The `top_<region>` rows check which risk is top: the risks whose
  rounded value equals the rounded maximum, so the Eastern Asia tie (16% machinery and fire)
  is kept.
- **Chart 5.14** (free to report safety problems against the UL Safety Index) prints no
  values. The UL Safety Index is no longer published (see [External data](#external-data)).
- **GDP correlation (footnote 36):** log of GDP per capita, PPP (current international $,
  `NY.GDP.PCAP.PP.CD`), 2019, against the country % free to report safety problems. The
  code gives 0.622, against the published 0.614. Current US$ gives 0.672, and PPP in
  constant 2017 $ gives 0.620.
- **Chart 5.16** is recorded as printed, following its legend colours. The printed
  "engaged" values (63–73%) are lower than the "actively disengaged" values (72–90%). The
  text on the same page gives engaged 81% and actively disengaged 67%, so the legend may
  be swapped.

### Chapter 6: Climate change risk

- **Numeracy (Charts 6.4 and 7.6):** correct = "10% is the same as 1 out of 10" (`L12` = 3);
  any other answer, including don't know, is "not correct".
- **U.S. regions (Chart 6.7):** `REGION2_USA`; "North/Midwest" combines Northeast and Midwest.
  "Elsewhere in the U.S." in the text is everyone outside the South.
- **Experience of severe weather (Chart 6.8):** `L8D` yes or no; don't know and refused are
  left out.
- **Footnote 10 (X6_27):** the "average percentage of people in a country who have 0–8 years
  of education" (44%) is the population-weighted share of all respondents. The unweighted
  mean of the 142 country shares is 36%.
- **Chart 6.9 (model):** the report used a multilevel logistic regression, and does not
  publish the full specification. The code fits two weighted logistic regressions (`glm`,
  binomial; very serious vs other, and not a threat vs other) on everyone who gave an answer
  (don't know and refused left out, 18% of the weighted sample, X6_35). Predictors:
  education, gender, age group, feelings about household income (`IncomeFeelings`),
  numeracy, experience of severe weather (`L8D`), satisfaction with air and water quality and
  religion (Gallup items), and country fixed effects in place of the multilevel country
  effect. Region and income group are country-level, so the country effects absorb them. The
  chart values are average predicted probabilities with everyone's education set to each
  level. Weights are `PROJWT` scaled to mean 1.

### Chapter 7: Technology-related risk perceptions

- **"No opinion" (Charts 7.1, 7.10):** everyone who did not say mostly help or mostly harm:
  no opinion, neither, don't know and refused. The three bars add to 100.
- **"Higher-income countries" (key finding 2, X7_04):** high-income countries (22%). All
  non-low-income countries together give 20%.
- **Chart 7.3** plots country % "mostly help" against Gallup's Food and Shelter Index;
  **Chart 7.9** plots country % "mostly harm" against the Wellcome Global Monitor 2018 Trust
  in Scientists Index. Neither prints values. The functions return the poll axis for every
  country; the correlation in footnote 14 needs Gallup data (see
  [Gallup World Poll data](#gallup-world-poll-data)). The Wellcome index was not fetched, as
  there is nothing to compare it with.

### Chapter 8: Internet-related risk perceptions

- **Internet users:** `L27A`–`L27C` were asked only of those who used the internet in the
  past 30 days (`L26` = 1), so every Chapter 8 worry figure is among internet users.
- **Middle income (X8_17):** lower-middle and upper-middle combined.
- **Footnote 7 (X8_12):** countries with fewer than 100 respondents asked the internet-risk
  questions (unweighted): Madagascar and Rwanda, 97 each.
- **Footnote 9 (X8_13, X8_14):** Pearson correlation across countries between % of internet
  users worried about false information and the World Bank GINI index, using each country's
  latest estimate from 2018 or earlier (the report retrieved the data in May 2020). This
  gives r = 0.431, as published, over 132 countries (published 131). Using estimates up to
  2019 gives the same r.
- **Chart 8.1:** the bottom three countries for internet use are Chad (8%), Niger (9%) and
  Ethiopia (11%), as published. But Rwanda (9%) and Madagascar (10%) are lower than Ethiopia
  in the data and are not listed. Footnote 7 drops these two countries from internet-user
  results. Rwanda still appears in the top three of Chart 8.4.
- **Chart 8.6** (no printed values): % of internet users worried about online bullying and
  their mean age, by country. The labelled countries sit where the data puts them (for
  example Australia 8% and 50 years, Ethiopia 49% and 24 years).

### Chapter 9: Food and water risk

- **Two biggest risks (X9_03):** unsafe food (12) or water (11) given as the greatest
  (`L3_A`) or another major (`L3_B`) source of risk.
- **Chart 9.1:** WRP countries grouped into WHO sub-regions using the lists in Appendix 3.
  Hong Kong, Kosovo, Palestine and Taiwan are not WHO member states and are left out. X9_08
  ranks the six WHO regions (sub-regions combined): Eastern Mediterranean 31%, Africa 26%,
  Americas 20%, South-East Asia 18%.
- **Worry vs experience gaps (X9_13, X9_14):** the regions the text names as having gaps of
  "five percentage points or more" match the rounded chart values, not the unrounded ones
  (Eastern Asia 4.9, Middle East 4.8, Eastern Africa 4.6 points). So these two lists use the
  rounded chart values.
- **Trusted sources (Chart 9.5, `L14`):** everyone asked, with don't know included.
- **Government Safety Performance Index (Chart 9.9, X9_44–X9_48):** as the report defines
  it: yes = 1, any other answer (no, don't know, refused) = 0 on `L16A`–`L16C`, averaged and
  multiplied by 100; country scores are weighted means. Saudi Arabia and Turkmenistan were
  not asked.
- **Chart 9.7** (no printed values): % saying the government does a good job on food safety,
  for Eastern European countries and for regions. Its x-axis, confidence in the national
  government, is a Gallup item.

### Chapter 10: Forecasting risk

- The forecasts come from regression models on one year of poll data, with 14 external
  predictors (IMF, World Bank, UNWTO, Gallup indices) projected under three scenarios. The
  Methodology report that describes them is not public, so the 2020 and 2021 values cannot
  be reproduced. They are listed under
  [Chapter 10 forecasts](#chapter-10-forecasts-not-reproducible).
- The recorded 2019 values are reproduced. The report uses the 127 countries with a forecast
  and does not list the 15 it left out, so the code uses all 142 countries.
- **Less safe:** `L2` = 2. **Experience of Harm Index and Worry Index:** as above. **Risk
  gap:** the mean of each person's Worry minus Experience Index. **Workplace injuries:** yes
  to any of `L21A`–`L21E`, among those asked (people in work).

### Appendix 3 (regional maps)

The `A3_` findings count the countries the appendix lists in each World Risk Poll region,
and compare them with the number of countries in each `GlobalRegion`. All 15 match (142 in
total).

### Chapter 10 forecasts (not reproducible)

| Figure | 2019 (recorded) | 2020 | 2021 |
| --- | --- | --- | --- |
| Less safe, optimistic / central / pessimistic (Chart 10.2, text) | 24 | 28 / 32 / 40 | 24 / 24 / 29 |
| Experience of Harm Index | 16 | 17 / 17 / 19 | 16 / 17 / 18 |
| Worry Index | 40 | 40 / 41 / 42 | 40 / 41 / 42 |
| Risk gap | 24 | 23 / 24 / 23 | 24 / 24 / 24 |
| Workplace injuries | 40 | 41 / 42 / 44 | 39 / 41 / 42 |
| Less safe, central, low / lower-middle / upper-middle / high income (Chart 10.3) | 38 / 26 / 20 / 27 | 45 / 30 / 28 / 39 | 40 / 26 / 18 / 28 |

Chart 10.4 (less safe, central scenario, 2020 / 2021): Southern Africa 54 / 37, Latin
America & Caribbean 60 / 50, Eastern Africa 47 / 42, Central/Western Africa 46 / 40,
Northern Africa 43 / 31, Middle East 35 / 25, Southern Europe 45 / 29, Northern/Western
Europe 39 / 26, Southern Asia 32 / 27, Northern America 40 / 30, Australia & New Zealand
28 / 22, Eastern Europe 30 / 20, Central Asia 23 / 20, Southeastern Asia 17 / 13, Eastern
Asia 17 / 9. The text also gives 127 forecast countries, 15 left out, and about 5 billion
adults (X10_04, reproduced for all 142 countries).

## Gallup World Poll data

88 findings need Gallup World Poll items that are not in the public release. They must be
licensed from Gallup directly. The code is included; without the data these findings are
reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item | Meaning, codes and status | Findings |
| --- | --- | --- |
| `WP112` | Confidence in the local police (1 = yes, 2 = no). Code given in the report (page 165). | Chart 1.6, X1_19, X1_27, X1_28 |
| `WP113` | Feel safe walking alone at night (1 = yes, 2 = no). Code given in the report (page 165). | X1_17, X1_18, X2_32 |
| `WP31` | Standard of living getting better (1) or worse (2). **Item code not confirmed**; check with Gallup. | Chart 1.6, X1_21, X1_22 |
| `WP89` | Good (1) or bad (2) time to find a job in your area. **Item code not confirmed**; check with Gallup. | X1_09, X1_10 |
| `GWP_INTERVIEW_LANGUAGE` | **Placeholder name** for the language of the interview, holding "English", "Russian", "Chinese", "Arabic", "French" or "Spanish". | Chart 1.8, X1_38 |
| `WP119` | "Is religion an important part of your daily life?" (1 = yes). The usual Gallup code, but **not confirmed**. | X4_06, X4_07 (footnotes 12–13) |
| `GWP_EMPLOYEE_ENGAGEMENT` | **Placeholder name** for Gallup's employee engagement measure (1 = engaged, 2 = not engaged, 3 = actively disengaged), asked in the 2019 Gallup World Poll in 108 countries. The item code is not known; rename it to Gallup's variable. | X5_47–X5_50, Chart 5.16 (page 107) |
| `WP93` | Satisfied with the quality of the air where you live (1 = satisfied). **Item code not confirmed**; check with Gallup. | Chart 6.9, X6_36 |
| `WP94` | Satisfied with the quality of the water where you live (1 = satisfied). **Item code not confirmed**; check with Gallup. | Chart 6.9, X6_36 |
| `WP1233` | Religion (denomination, used as categories). **Item code not confirmed**; check with Gallup. | Chart 6.9, X6_36 |
| `WP40`, `WP43` | Not enough money for food / for shelter in the past 12 months (1 = yes, 2 = no); Gallup's Food and Shelter Index. | X7_09, X7_10 (footnote 14) |
| `WP139` | Confidence in the national government (1 = yes, 2 = no; the wording is given in footnote 31). | X9_28, X9_32–X9_34, X9_37, X9_49; x-axis of Chart 9.7 |

- **Placeholder and unconfirmed codes:** rename the two placeholder names to Gallup's
  variables, and check the codes marked "not confirmed" with Gallup.
- `WP119` (importance of religion, Chapter 4) and `WP1233` (religion itself, needed by the
  Chapter 6 model) are different items.
- The Food and Shelter Index is computed as Gallup describes it: each person scores 100 x
  the share of the two items answered "no" (had enough money), averaged by country.
- The code for the Chapter 1–2 findings was tested with a synthetic file of the same layout.
  The code for the Chapter 6–9 findings was tested with a file of random values for these
  items: Python and R give the same results.
- Gallup figures for other years are not recorded, because they are not in this wave: Hong
  Kong's 80% confidence in police in 2017, and China's 76% for standard of living in 2015.
- Chapter 3 (page 66) also mentions life satisfaction (Cantril ladder) and Gallup's Community
  Basics and National Institutions Indices, and Chapter 4 (page 79) mentions the National
  Institutions Index. The report publishes no figures from them in these chapters.

## External data

The three World Bank files are committed in `reports/external/` (licence CC BY 4.0). The
Freedom House and WHO data allow only non-commercial use, so they are not redistributed here;
download them with `fetch_external.py` (see [Run](#run)). Without them, the findings that use
them are reported as `EXTERNAL_ONLY`. See
[`reports/external/README.md`](../../external/README.md).

- **World Bank World Development Indicators, 7 indicators** (Chapters 1 and 2):
  [`reports/external/core_world_risk_poll_2019__worldbank.csv`](../../external/core_world_risk_poll_2019__worldbank.csv),
  from the API (`https://api.worldbank.org/v2/country/all/indicator/<code>?format=json`),
  downloaded 25 September 2026. Licence CC BY 4.0. Columns `iso3`, `country`, `indicator`,
  `year`, `value`.

  | Indicator | Used for | Year used |
  | --- | --- | --- |
  | `NY.GDP.PCAP.CD` GDP per capita, current US$ | X1_29 (footnote 34) | 2018 |
  | `NY.GDP.MKTP.KD.ZG` GDP growth, annual % | X1_30 (footnote 34) | 2018 |
  | `SI.POV.GINI` Gini index | X2_33, X2_34, Chart 2.7 (footnote 24) | most recent value up to 2018 |
  | `SP.DYN.CDRT.IN` Crude death rate | X2_37 (footnote 29) | 2018 |
  | `SH.DTH.INJR.ZS` Cause of death by injury, % | Chart 2.9 | 2016 |
  | `SH.H2O.BASW.ZS` At least basic drinking water, % | X2_55 (footnote 55) | 2017 |
  | `EN.CLC.MDAT.ZS` Droughts, floods, extreme temperatures, % of population | X2_56 (footnote 56) | average 1990-2009 |

  The Gini correlation uses 131 countries, as in the report. Using values up to 2017 gives
  0.565 instead of 0.578.
- **World Bank GDP per capita** (Chapter 5, footnote 36: X5_42, X5_43):
  [`reports/external/core_world_risk_poll_2019__worldbank_gdp.csv`](../../external/core_world_risk_poll_2019__worldbank_gdp.csv),
  from the World Development Indicators API (https://api.worldbank.org/v2/): GDP per capita
  `NY.GDP.PCAP.CD`, `NY.GDP.PCAP.PP.CD` and `NY.GDP.PCAP.PP.KD`, 2017–2019. Licence:
  CC BY 4.0. Downloaded 25 September 2026.
- **World Bank GINI index** (`SI.POV.GINI`; Chapter 8, footnote 9: X8_13, X8_14):
  [`reports/external/core_world_risk_poll_2019__worldbank_SI.POV.GINI.csv`](../../external/core_world_risk_poll_2019__worldbank_SI.POV.GINI.csv).
  Source: https://api.worldbank.org/v2/country/all/indicator/SI.POV.GINI?format=json&date=1990:2020,
  downloaded 25 September 2026 (World Bank data last updated 13 July 2026). Licence:
  CC BY 4.0. Later revisions mean this is not the May 2020 vintage the report used.
- **Freedom House, *Freedom in the World 2020*** (Chapter 2: X2_60, X2_61, X2_63). **Not
  redistributed here**, because Freedom House allows free use for non-commercial purposes
  only. Download it with `python reports/external/fetch_external.py freedomhouse`, which
  writes `reports/external/downloaded/core_world_risk_poll_2019__freedom_house.csv`. Without
  it, X2_60, X2_61 and X2_63 are reported as `EXTERNAL_ONLY`. The source is
  https://freedomhouse.org/sites/default/files/2020-02/2020_All_Data_FIW_2013-2020.xlsx
  (2020 edition rows; status, political rights, civil liberties and total score). The data
  are © Freedom House. Palestine is not matched, because Freedom House scores the West Bank
  and the Gaza Strip separately. The copy used for `RESULTS.md` was downloaded on
  25 September 2026.
- **WHO seat-belt laws** (Chapter 4: X4_14–X4_16, Chart 4.6, X4_19, Chart 4.8). **Not
  redistributed here**, because the WHO licence (CC BY-NC-SA 3.0 IGO) is non-commercial.
  Download it with `python reports/external/fetch_external.py who_seatbelt`, which writes
  `reports/external/downloaded/core_world_risk_poll_2019__who_seatbelt_laws.csv`. Without it,
  those findings are reported as `EXTERNAL_ONLY`. The source is WHO *Global status report on
  road safety 2018*, Statistical Annex Table A7 ("Seat-belt laws, enforcement and wearing
  rates by country/area"). The table is parsed from the report PDF on WHO IRIS
  (https://iris.who.int/server/api/core/bitstreams/9c866a4e-fda7-43bd-96df-27d7c3b509bc/content;
  item https://iris.who.int/handle/10665/276462). It gives a national seat belt law, and
  whether the law applies to drivers, front and rear seat passengers, for 175 countries.
  ISO3 codes come from the WHO GHO API. The national-law column was checked against GHO
  indicator `RS_209`: 161 countries with a law, as the report says. 105 have a law covering
  all occupants, the report's "best practice". The copy used for `RESULTS.md` was downloaded
  on 25 September 2026.
- **UL Safety Index** (Chapter 5: X5_41). Underwriters Laboratories discontinued the index in
  April 2020 and no longer publishes it, so it could not be fetched. X5_41 (the correlation
  of 0.530 between the index and the % free to report safety problems) is therefore reported
  as `EXTERNAL_ONLY`. Anyone who has a copy can put it in
  `reports/external/downloaded/core_world_risk_poll_2019__ul_safety_index.csv` (columns
  `iso3`, `ul_safety_index`).

The committed World Bank files are snapshots. The sources above are enough to rebuild them,
though a new download may differ slightly.

### Context: figures from other sources (not recorded)

Statistics the report quotes from other organisations are context and are not reproduced.
They include:

- **The poll and population:** the coverage of about 98% of the world's adult population
  (Methodology report); the UN population forecast (9.7 to 10 billion by 2050).
- **Roads:** WHO road traffic figures (20–50 million injuries and 1.3 million deaths a year,
  1.35 million in Chapters 3–5; 93% of road deaths in low- and middle-income countries; a
  cost of 3% of GDP; the traffic fatality rates in Chart 2.3); seat belts reducing deaths by
  45–50% (front) and 25% (rear).
- **Crime and inequality:** homicide rates (World Bank); The Economist's 8% of the world's
  population and 38% of criminal killings in Latin America; the 11 of the 20 highest Gini
  coefficients in Latin America.
- **Economy:** GDP per capita values in Chart 2.10 and Rwanda's about $800; IMF growth
  rankings; the Statista share of South Africans living in cities (67%); OECD and IMF 2020
  growth forecasts (2.4%, 3.3%, -3%, 5.8%).
- **Other hazards:** the estimated 320,000 drowning deaths a year; Nepal's 2015 earthquake
  deaths; ICAO aeroplane accidents (2.8 per million departures); lightning deaths (about
  24,000 a year).
- **Food and water:** WHO food and water figures (600 million ill and 420,000 deaths a year,
  485,000 deaths from diarrhoea, $95 billion productivity loss); the World Bank on foodborne
  illness (41% of population, 53% of illness, 75% of deaths, $110 billion); the WHO foodborne
  disease DALYs per 100,000 in Chart 9.1 (Havelaar et al. 2015: AFR D 1,276; AFR E 1,179;
  SEAR D 711; SEAR B 685; EMR D 571; EMR B 362; AMR D 315; WPR B 293; AMR B 140; EUR B 52;
  EUR C 49; EUR A 41; WPR A 36; AMR A 35).
- **Work:** ILO occupational deaths (nearly 3 million) and injuries (374 million), and their
  cost (2–6% of GDP); Sierra Leone's agriculture share of GDP (57%); more than a billion
  agricultural workers; WHO's $1 trillion cost of depression and anxiety; the UK's
  15.4 million lost workdays.
- **Climate, technology and the internet:** IPCC and others on climate change; Gallup U.S.
  partisan gap on climate concern (17 points in 2000, 48 in 2017); 2012 Gallup U.S. poll on
  nuclear safety (72% of men, 42% of women); Pew 2017 online harassment (four in 10, 62%);
  CSIS cost of cybercrime ($600 billion, 0.8% of global GDP).
- **Forecasting:** the Chapter 10 scenario assumptions and Chart 10.1 (GDP growth,
  unemployment, tourism, mortality).

## Findings that do not match

41 findings differ from the published values by more than their tolerance:

- **E23, E25 (people harmed by food and water):** 930 million and 763 million, against
  "1 billion" and "823 million". The report's counts imply about 5.8 billion adults;
  `PROJWT` sums to 5.36 billion. The percentages (E22, E24) match.
- **E28 (71% of internet users worry about at least one internet risk):** 68% with
  `PROJWT`. Other bases tried: excluding don't know 69%, `WGT` 70.5%, unweighted 71.3%,
  mean of country percentages 72%. The three single-risk figures (E29, E30 and the
  country figures) match with `PROJWT`.
- **X1_11, X1_12 (footnote 16):** the report's upper-middle-income group has 39
  countries and China makes up 56% of it. The data (World Bank FY2019-20) have 43
  countries, with China at 54.9%. Chart 1.2 and the "24% excluding China" (X1_13, 23.4%)
  still match within tolerance. Not explained.
- **X1_30 (correlation with GDP growth, footnote 34):** the data give -0.455. On the
  footnote's scale (1 = more safe, 3 = less safe), faster growth goes with safer scores,
  so the correlation must be negative. Its size is within 0.013 of the published 0.468.
  The report appears to print it without the sign.
- **X2_12 (8% named personal health issues as their second response):** code 9 gives
  6.7%, although code 9 reproduces the first-response figure (X2_08, 11%). Adding code 10
  (drugs, alcohol, smoking) gives 7.6%.
- **X2_25_urban, X2_25_rural (urban 25%, rural 21% naming road hazards):** the data give
  27.7% and 22.4%. The other group figures on the same page match with the road/transport
  definition. Road code 1 alone gives 24.6% and 20.1%. The six-category urbanicity variable
  does not give both figures either. Not explained.
- **X2_50 (300 million people naming food or water risks):** the data give 3.2%, which is
  170 million (183 million on a 5.8 billion base). Not explained.
- **X4_10_police:** 69.2% of people in high-income economies are "very likely" to think the
  police would return a lost bag, against the published 68%. The neighbours figure next to
  it (57%) matches. Not explained.
- **C4_6_law_low, C4_6_law_lower_middle, C4_6_law_high (Chart 4.6, "% of countries with a
  seat belt law"):** 71% (low income), 91% (lower-middle) and 93% (high), against the
  published 76%, 88% and 96%. The world (89% against 90%) and upper-middle (93%) values
  match. Each difference is one country in or out. The likely cause is how the nine
  countries missing from the WHO table were treated.
- **Seat belt use in low-income economies, 6 values (C4_6_wear_low and the five low-income
  values of Chart 4.7: C4_7_low_women, C4_7_low_men, C4_7_low_edu_0_8, C4_7_low_edu_9_15,
  C4_7_low_edu_16plus):** the data is 1.3–2.7 points below the published values. The other
  income groups match. Leaving Yemen out of the low-income group (11% of Yemenis say they
  wear a seat belt) gives 45.8% overall, 41.0% of women, 50.9% of men, and 42.1%, 56.3% and
  53.7% by education. That is closer, but two values are still more than a point off. Not
  explained.
- **C4_7_high_edu_0_8:** 94.1% against 93% (a small group). Not explained.
- **X4_19 and Chart 4.8, 6 values (X4_19_none, X4_19_partial, X4_19_full, C4_8_none,
  C4_8_partial, C4_8_full; seat belt use by strictness of law: 58%, 72%, 93%):** the data
  gives 50%, 64% and 86% (average of country percentages). These alternatives were tried:
  - Pooled respondents (`PROJWT`): 47%, 67%, 82%.
  - Don't know excluded.
  - WHO's own grouping in its Figure 12 (no law or driver only / front seats / all
    occupants): 53%, 66%, 86% as country averages, or 43%, 75%, 82% pooled.

  None reproduces the chart. The report does not say how it grouped or averaged the
  countries. The six "no law" countries are 22–81% (average 50%).
- **X5_07_northwest_europe:** the key findings (page 85) say at least one in four workers
  in Northern/Western Europe name physical violence and harassment as a risk. Page 96 and
  the data give 23%.
- **Chart 5.6, 5 values (C5_6_women_edu_9_15, C5_6_women_edu_16plus, C5_6_men_edu_0_8,
  C5_6_men_edu_9_15, C5_6_men_edu_16plus; injury at work by gender and education):** only
  women with 0–8 years of education match (19%). The data gives women 11.8% and 7.1%, and
  men 28.2%, 22.4% and 11.7%, against the published 10%, 3%, 32%, 31% and 6%. The text on
  the same page (24% for 0–8 years, 10% for 16+ years, both sexes) matches the data. These
  alternatives were tried: `WGT`, don't know excluded, each income group, each region, each
  country, and employees only. None reproduces the chart. Not explained.
- **X5_36_all_five:** 65.1% of workers with all five types of harm at work report mental
  health harm, against the published 64%. Excluding don't know gives 66.0%. Not explained.
- **X5_43 (142 countries in the GDP correlation):** the current World Bank data has no GDP
  per capita (PPP) for Taiwan, Venezuela and Yemen, so the correlation uses 139 countries.
- **X6_37 (key finding 2):** the U.S. (21%) does not have the highest % saying climate
  change is not a threat among high-income countries: Lithuania (23%), Bahrain (23%) and the
  United Arab Emirates (22%) are higher.
- **X6_14 (low income, climate change a very serious threat):** 37% against 38% published.
  The text gives 38% for low income and 37% for each middle-income group. The data gives
  36.9% low, 37.2% lower-middle and 37.5% upper-middle, so 38% may belong to upper-middle.
  No weighting or base tried gives 38% for low income. Not explained.
- **X9_05 ("nearly one-third" harmed by food or water):** 22% experienced harm from food or
  water. "Nearly one-third" is the sum of the food (17%) and water (14%) figures, 31.6%,
  which counts the 9% harmed by both twice.
- **X10_06 and C10_3_low_2019 (low income, less safe, 2019):** 40% against 38%.
  **C10_4_middle_east_2019:** 30% against 32%. Both use the report's unpublished
  127-country set. Leaving out Afghanistan gives 37% for low income, and leaving out Saudi
  Arabia gives 33% for the Middle East. So the difference is consistent with the country
  set, but the set cannot be checked.

123 findings are within tolerance but do not round to the published figure:

- **Executive Summary to Chapter 2 (38):** 18 are values between x.45 and x.50 that the
  report rounded up (see Rounding above). The other 20 are five correlations (external data
  revised since 2020); the Freedom House counts (10 Not Free and 8 Partly Free, against 11
  and 7: Thailand was Not Free in the 2019 edition); the verbal figures "150,000", "about
  half", "over two-thirds", "almost 70%" and "more than 1 billion"; and C1_9_world_low
  (24.9% printed as 24), X2_06 (15.4% printed as 16), E40 (24.3% of countries printed as
  25%) and X1_13.
- **Chapters 3–5 (42):** most are values close to a rounding boundary, or chart gaps taken
  from rounded bars. The "about" figures (X3_12, X5_03, X5_09) and the two correlations
  X4_11 and X5_42 are also in this group.
- **Chapters 6–10 (43):** most are values close to x.5 or Chapter 10 values on the
  127-country set. Also X9_46: 34 countries have a GSPI score below 50, against 35
  published. North Macedonia scores 50.02.

## Run

The Freedom House and WHO data are not redistributed. Download them first; without them,
the findings that use them are reported as `EXTERNAL_ONLY`.

```
python reports/external/fetch_external.py freedomhouse who_seatbelt
python reports/WRP_2019/core_world_risk_poll_2019/reproduce.py
Rscript reports/WRP_2019/core_world_risk_poll_2019/reproduce.R
```
