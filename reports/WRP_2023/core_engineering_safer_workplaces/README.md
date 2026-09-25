# World Risk Poll 2024 Report: Engineering safer workplaces

- **Report:** *Engineering safer workplaces: Global trends in occupational safety and health*
  (World Risk Poll 2024 Report), Lloyd's Register Foundation, October 2024, 31 pages
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-10/World%20Risk%20Poll%2024%20-%20OSH%20Report%201_0.pdf
- **Data:** `WRP_2023/WRP_2023.parquet` (World Risk Poll 2023, wave 3; 146,910 respondents, 142
  countries). Trend figures also use `WRP_2021/WRP_2021.parquet` (wave 2) and, for 2019,
  `WRP_2019/WRP_2019.parquet` (wave 1).

## What is reproduced

All 516 numbers in the report: every value in Charts 2.1 to 4.7 and Tables 2.1 and 4.1
(355 values), and every number in the text (161 values), including percentage-point
changes, counts, ranks and the two odds ratios. Results are in [`RESULTS.md`](RESULTS.md).
Page numbers in `published_figures.csv` are PDF pages (the printed page number plus 5 from
page 6 on).

Four charts are scatter plots with no printed values: Chart 2.7 (worry against experience for
seven risks), Chart 2.11 (sector harm rates against the share of men, of primary education only
and of households that could last less than a week), Chart 3.1 (regional harm against
reporting) and Chart 3.3 (sector harm against reporting). The scripts compute them
(`C2_7`, `C2_11`, `C3_1`, `C3_3` in `output/`), but there are no published values to compare.
The values in the text next to Charts 3.1 and 3.3 are checked (X50, X58).

## Method notes

- **Current workforce:** `EMP_2010` codes 1–5 (employed full-time for an employer or for
  self, employed part-time, unemployed). Out of the workforce (6) is excluded. This is the
  base for almost every figure. Footnote i on page 7 (17%) adds people out of the workforce
  who last worked within the past two years (`WP23336` = 1).
- **Weights:** `PROJWT` throughout, so global, regional and group figures are
  population-weighted. X04 (667 million) is the `PROJWT` sum of the harmed current workforce.
- **Base:** everyone asked the question, with don't know and refused included.
- **Workplace harm:** `WP22448` "personally experienced" = yes, personally (1) or both (3).
  2019 (Chart 2.1, Italy in X26) uses `L19`, "ever been seriously injured while working",
  which was asked only of the employed.
- **Worry about work:** `WP22214`, very or somewhat worried. It was asked only of the employed
  (`EMP_2010` 1, 2, 3, 5), so the unemployed are not in these figures. The 2021 figure (52%)
  needs the current-workforce filter: some 2021 respondents with no `EMP_2010` code were asked
  the question, and including them gives 48%.
- **Trends (Charts 2.2, 2.3; X24–X32):** each wave uses all its countries (121 in 2021, 142 in
  2023). The 2021 figures use each country's **2023** region and income group. This moves Iran
  from the Middle East to Southern Asia and changes the income group of seven countries.
  With the 2021 groupings, the Middle East (2021) is 15.5% instead of 13%, and upper-middle
  income (2021) is 13.3% instead of 15%.
- **Survey mode (X20–X23):** countries interviewed by telephone in 2021 and face to face in
  2023 (27) against countries with the same mode in both years (92), among the 119 countries
  asked about harm at work in both years. The average change is the unweighted mean of the
  country changes (2023 minus 2021). Modes come from the methodology documents (see External
  data).
- **Employment type:** part-time combines `EMP_2010` codes 3 and 5.
- **Financial resilience (Chart 2.8):** less than a week (`WP22229` = 1), one to four weeks
  (`WP22229` = 2, 3) and a month or more (`WP22228` = 2).
- **Job sector:** `WP23340`. Market and non-market services are codes 7 and 8.
- **Reporting harm (Chapter 3):** `WP23335` = yes, among the current workforce who were
  personally harmed. "Does not apply", don't know and refused stay in the base.
- **OSH training (Chapter 4):** past two years = `WP23338` yes. "Not within the past two years
  or not sure when" = trained (`WP23337` yes) and anything else at `WP23338`, including trained
  respondents who were not asked the follow-up (8,845 in the full sample). Never = `WP23337` no. Don't know
  and refused at `WP23337` stay in the base (0.2%).
- **Table 4.1:** the bottom-10 column is headed "Proportion NOT trained in last two years", but
  its values are the % never trained (the text says so for Senegal). The scripts rank the
  countries from the data, so the table also tests the ranking.
- **Chart 2.4:** the colour-scale ends (41%, 4%) are the highest and lowest African countries.
  They are recorded as `C2_4_legend_max` and `C2_4_legend_min`.
- **Charts 4.3 and 4.6:** the Eastern Asia middle segment is under 5% and not labelled.
- **X27 ("five points or more"):** the function returns the smallest of the three regional
  decreases.
- **Odds ratios (Chart 4.7, X13):** logistic regression (statsmodels `glm` Binomial in Python,
  `glm(family = binomial)` in R), unweighted. The sample is the current workforce harmed in
  the past two years who answered yes or no to `WP23335` (10,499 respondents). The outcome is
  told someone (1) against did not (0). The predictors are training (three categories, never =
  reference), `Gender`, `Age` (years), `Education` (all codes), `WP23340` (all codes) and log
  GDP per capita. Taiwan and Yemen (no GDP value) and respondents with no age are dropped.
  The report names these controls ("such as gender, age, education, job sector and GDP per
  capita") but not their coding or the weighting.

## Gallup World Poll data

Every finding uses public World Risk Poll data. No Gallup World Poll items are needed.

## External data

- **World Bank GDP per capita** (`NY.GDP.PCAP.CD`, current US$), 2021–2023 for all
  economies, from the World Bank API:
  `https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD?date=2021:2023&format=json&per_page=2000`.
  Saved as
  [`reports/external/core_engineering_safer_workplaces__worldbank_NY.GDP.PCAP.CD.csv`](../../external/core_engineering_safer_workplaces__worldbank_NY.GDP.PCAP.CD.csv).
  Licence CC BY 4.0. Downloaded 25 September 2026 (API last updated 13 July 2026). The model
  uses the 2023 values. The report's authors used an earlier release, so their GDP values may
  differ slightly.
- **Interview mode by country, 2021 and 2023:** parsed from the country tables in the World
  Risk Poll methodology documents:
  - 2023: https://www.lrfoundation.org.uk/sites/default/files/2024-06/World%20Risk%20Poll%202024%20Report%20Methodology.pdf
    (Table 3)
  - 2021: https://www.lrfoundation.org.uk/sites/default/files/2024-06/lrf_wrp_2021_full_methods.pdf
    (Table 3)

  Saved as
  [`reports/external/core_engineering_safer_workplaces__wrp_interview_mode.csv`](../../external/core_engineering_safer_workplaces__wrp_interview_mode.csv)
  (`F2F` face to face, `TEL` telephone, `WEB` web, which is China in 2023). The PDF parser
  missed seven 2023 rows (Afghanistan, Brazil, Chile, Jordan, Nepal, Nicaragua, Paraguay).
  They were read from the PDF by eye, and all are face to face. © Lloyd's Register
  Foundation, licensed CC BY-SA 4.0. Downloaded 25 September 2026.

**Statistics from other organisations** quoted as context (not reproduced):

- ILO: around 3 million deaths a year from work-related accidents and diseases, and more than
  395 million workers injured at work in 2019 (page 7).
- ILO: among member states, 58% of high-income countries have a national OSH policy and 47% a
  national OSH programme, against 26% and 8% of low-income countries (page 9).
- WHO: nine in 10 injury-related deaths occur in low- and middle-income countries (page 9).
- FAO: 80 fishers die every day (page 15).
- Reserve Bank of Australia: construction is 7% of Australia's economic output (page 26).
- ILO Conventions 155 (1981), 187 (2006) and 188, and the ILO's foundation in 1919 (pages 6,
  15).

## Findings that do not match

5 findings differ from the published values by more than their tolerance:

- **X13_older and C4_7_older (odds ratio 1.8 for training that was not recent):** the model
  gives 2.19. The recent-training odds ratio (3.3) matches. The following alternatives all give
  2.0–2.3 for the older-training category and 3.1–3.5 for recent training: `WGT` weights, age
  groups instead of years, GDP in PPP terms or not logged, 2022 GDP, the employed only, sectors
  1–9 only, "not within two years" limited to an explicit no, don't know counted as not told,
  country fixed effects instead of GDP, adding region, income quintile, urbanicity or
  employment type, "personally" only (not "both"), and training as the only predictor.
  `PROJWT` weights give about 5.0 and 2.6. Not explained. The report does not give the full specification.
- **X33 ("seven countries" with changes of 10 points or more):** Table 2.1 and the text on the
  same page list eight countries, and the data gives eight. The word "seven" is an error in the
  report.
- **X50_northern_america (82%):** the text gives one figure for Australia & New Zealand and
  Northern America. Australia & New Zealand is 82.0%. Northern America is 80.5% (81.0% with
  "does not apply" excluded), and Chart 3.1 plots it at about 80%.
- **X62 (five of the top 10 countries in Eastern Europe):** the World Risk Poll regions put
  Latvia in Northern/Western Europe, so the data gives four (Czech Republic, Slovakia, Hungary,
  Romania). The report counts Latvia as Eastern Europe.

One more finding is within tolerance but does not round to the published figure: X01
(146,910 interviews, "nearly 147,000").

## Run

```
python reports/WRP_2023/core_engineering_safer_workplaces/reproduce.py
Rscript reports/WRP_2023/core_engineering_safer_workplaces/reproduce.R
```
