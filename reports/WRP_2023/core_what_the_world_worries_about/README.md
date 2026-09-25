# World Risk Poll 2024: What the World Worries About

- **Report:** *What the world worries about: Global perceptions and experiences of risk and harm*, World Risk Poll 2024 report, Lloyd's Register Foundation, November 2024 (36 pages)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-11/World%20Risk%20Poll%202024%20Report%20%20-%20What%20the%20world%20worries%20about%20.pdf
- **Data:** `WRP_2023/WRP_2023.parquet` (World Risk Poll 2023, wave 3; 146,910 respondents, 142 countries and territories), with trends from `WRP_2021/WRP_2021.parquet` and `WRP_2019/WRP_2019.parquet`

## What is reproduced

All 705 findings in the report: every value printed in Charts 2.1 to 4.8 and Table 3.1, and every
number in the text, including percentage-point changes, country counts, the correlations in the
Chart 2.11 footnotes and the odds ratios from the report's model. Seven ranked charts (Chart 2.6
top five increases and decreases, Charts 3.5 to 3.7 top 10) also have a text finding (`..._top5`,
`..._top10`) that checks that the data give the same list of countries. Results are in
[`RESULTS.md`](RESULTS.md).

700 findings use only the public data: 689 match, 5 are within tolerance and 6 are different. The
other 5 need Gallup World Poll data (see below).

Page numbers in `published_figures.csv` are PDF pages. The printed page number is 5 less from PDF
page 6 on. The executive summary is PDF pages 3 and 4.

Charts with no printed values:

- **Chart 2.4** (traffic worry against personal experience, by region) and **Chart 4.3** (change in
  feeling less and more safe, 2019–2023, by region) are scatter plots. Their functions (`C2_4`,
  `C4_3`) compute the plotted values, but there are no published values to compare. The values
  quoted in the text are findings X42–X45 and X152–X153.
- **Chart 2.11** (satisfaction with roads against worry, by country) needs a Gallup World Poll item.
  Its only printed numbers are the two correlations in its footnotes (X69, X70).
- **Chart 3.1** (monthly global surface temperature anomalies) is Copernicus (ERA5) data, not poll
  data. It is not reproduced.

## Method notes

- **Questions (2023 and 2021 names):** feel more, less or about as safe as five years ago
  (`WP20711`; 2019 `L2`); greatest source of risk to safety in daily life, coded (`WP22331`; 2019
  `L3_A`); climate change a threat to the country in the next 20 years (`WP20719`; 2019 `L5`); worry
  about seven sources of harm (`WP20720`–`WP20723`, `WP22213`, `WP20726`, `WP22214`; 2019
  `L6A`–`L6D`, `L6G`, no traffic or work item); serious harm experienced in the past two years
  (`WP22442`–`WP22448`, asked in 2021 and 2023); experienced a disaster in the past five years
  (`WP23344`; 2021 `WP22245`) and its type (`WP22247`).
- **Weights:** `PROJWT`. Country figures are the same under `WGT`.
- **Base:** everyone asked the question, with don't know and refused kept in the denominator. Worry
  about work (`WP22214`) was asked only of people who work, so its base is those respondents.
- **Personal experience** of harm means "yes, personally experienced" or "both" (codes 1 and 3),
  as the note to Chart 4.5 says. "Know someone" is code 2 only.
- **Trends use the 2023 countries and regions.** Footnote ii (PDF page 7) says trends use only
  countries surveyed in 2023. So the 2019 figures use the 137 countries of the 2019 file that were
  surveyed again in 2023 (Belarus, Jamaica, Lesotho, Rwanda and Turkmenistan are left out), and
  the 2021 figures use 120 countries (Jamaica is left out). This is also where the report's "137
  countries in 2019" (X150) comes from. Every country keeps its 2023 region in all waves. This
  matters for Iran, which is Middle East in the 2019 and 2021 `GlobalRegion` and Southern Asia in
  2023. With the 2023 region, Table 3.1 matches in every cell and the Middle East is "No change"
  in Chart 2.2. With each wave's own region, the Middle East row of Table 3.1 is -1, 0, 7, -5
  (published 1, -1, 5, -4), Southern Asia's change in 'very serious threat' is 3 (published 2),
  and the Middle East rises by 3 points in Chart 2.2.
- **Greatest risk codes:** road-related accidents are code 1 in every wave. Climate change or
  severe weather is code 19 in 2021 and 2023. In 2019 the nearest code is 16, "climate change,
  natural disasters or weather-related events", which also covers earthquakes and volcanoes
  (code 20 from 2021). "Personal health conditions" on PDF page 8 (X26) is code 5.
- **Climate change: don't know.** Charts 3.2 and 3.3 are labelled "Don't know/Refused", so they
  combine codes 98 and 99. Chart 3.7 ("'don't know' if climate change is a threat") and the text
  on China's don't know answers (X122–X124) use don't know only (98). With don't know and refused,
  Laos (40.6%) would round to 41 rather than the printed 40, and the Dominican Republic (27.4%)
  would enter the top 10. The text's "no opinion" figures for Myanmar and Libya (52% and 48%, X134
  and X135) are don't know or refused. Chart 3.7 prints 51% for Myanmar, don't know only.
- **Rounded figures.** Where a chart or table note says so, figures are built from rounded
  numbers. Combined threat (very + somewhat) in Charts 3.3, 3.4 and 3.5 is the sum of the two
  rounded figures: for example, the rest of the world in 2023 is 44.4% + 26.5% = 70.9% unrounded,
  printed as 44 + 26 = 70. Table 3.1 is the difference of the rounded 2019 and 2023 figures, and
  so are the text findings on PDF page 19 that repeat it (X105–X115). The Chart 3.5 top 10 is
  ranked on these rounded sums. Italy (93 from rounded figures, 92.3% unrounded) is in the chart
  but would be 11th on unrounded totals. Ireland ties at 92 with Switzerland and North Macedonia
  and is picked on its unrounded total (92.5%).
- **Chart 2.5 (countries with changes of four points or more)** compares country figures rounded
  to whole numbers, which gives 16, 17, 29 and 36 exactly. Unrounded changes give 12, 15, 26 and
  29. It covers the 120 countries surveyed in both 2021 and 2023.
- **Other changes and gaps** (Charts 2.1, 2.2 and 2.6, and the text) use unrounded figures. Chart
  2.6 ranks countries on unrounded changes. For example, Sierra Leone (-8.94) is the fifth largest
  fall in worry, just ahead of Ukraine (-8.91).
- **Worry and Experience of Harm indices (Charts 4.6–4.8).** The chart notes define them as the
  mean of the seven worry items (very worried 2, somewhat 1, not worried 0) and the mean of
  personal experience of the seven harms, each on 0–100. This is not the Rasch-weighted
  `worry_index_published` / `experience_index_published` (those give, for example, 33.4 for
  Northern/Western Europe against the published 28). For 2023 the scripts use the file's own
  "Worried Mean" (`Q4_mean`) and "Experienced Mean" (`Q5_mean`) times 100, weighted by
  `Q4_mean_projwt_byusertime` and `Q5_mean_projwt_byusertime`. Those weights are `PROJWT` rescaled
  within each country so that the valid cases carry the country's whole population. The 2021 file
  has no such variables, so the scripts rebuild them with the rules that reproduce `Q4_mean` and
  `Q5_mean` exactly in 2023 (checked to machine precision): the worry scores are summed over the
  items asked and divided by 7, so work counts 0 for people not asked it, and a respondent with
  don't know or refused on any item has no score. Experience is the share of the seven items
  personally experienced, for respondents who answered all seven. The weights are rebuilt the same
  way. All 90 index values match.
- **Floods (X73, X74)** are the share of all adults whose disaster in the past five years was a
  flood or heavy rain (`WP22247` code 1). People who had no disaster count as no flood.
- **Margin of error (X48, "plus or minus 3.9 points"):** the methodology document's figure is
  approximated as the mean over countries of 1.96 × √(deff × 0.25 / n), with the Kish design effect
  of `WGT` (3.86).
- **Waste separation (X145, X146)** repeats a finding of the report *A World of Waste*: "yes" to
  `WP23342`, by answer to the climate change question.
- **Model (Charts 3.8 and 3.9, X04 and X137–X141).** The report fits a multi-level regression of
  saying climate change is a very serious threat, with demographic, attitudinal and structural
  (region, country income) factors. It names worry about severe weather, education, sex,
  urbanicity, age, struggling to afford food, neighbours caring, feelings about household income
  and ability to afford basic needs. It does not give the full specification. The scripts fit:
  - a logistic regression (`statsmodels` GLM in Python, `glm` in R; binomial, logit link), with
    country fixed effects in place of the country random intercepts. Region and country income
    level are country-level, so the country effects absorb them;
  - outcome: 1 = very serious threat (`WP20719` = 1), 0 = any other answer, including don't know
    and refused;
  - covariates: worry about severe weather (`WP20723`; reference not worried), education
    (`Education`; reference primary), male (`Gender`), urbanicity (`Urbanicity`: rural area or
    farm as reference, small town, large city, suburb; the report's "city" is a large city), age
    in years, neighbours care about you (`WP22232`) and could cover basic needs for a month
    (`WP22228`);
  - weights: `WGT`, rescaled to mean 1 in the model sample: the 131,614 respondents with a valid
    answer on every covariate;
  - if `GALLUP_WP_PATH` is set, the two Gallup World Poll controls are added (see below).

  Odds ratios are compared with a tolerance of 0.1. Other specifications tried (very, somewhat,
  tertiary, secondary, male, city; published 3.6, 1.6, 1.7, 1.3, 1.15, 1.1):
  - country fixed effects, unweighted: 3.78, 1.61, 2.04, 1.42, 1.09, 1.07;
  - country fixed effects, `WGT`, don't know and refused left out of the model (118,108
    respondents): 3.83, 1.55, 1.66, 1.19, 1.05, 1.04;
  - region and income-group dummies instead of country effects, unweighted: 3.90, 1.64, 2.01, 1.42,
    1.09, 1.01;
  - the same, `PROJWT`-weighted: 4.11, 1.69, 1.82, 1.41, 1.18, 1.11.

  No specification reproduces all six. The one used here gives four of the six within 0.1, and
  keeps don't know in the base, as the report does elsewhere.

## Gallup World Poll data

5 findings need Gallup World Poll items that are not in the public release. Those items must be
licensed from Gallup directly. The code is included. Without the data, these findings are reported
as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

- **Satisfaction with roads and highways** (X69, X70; Chart 2.11): "In the city or area where you
  live, are you satisfied or dissatisfied with the roads and highways?" The findings are the
  Pearson correlations, across the 142 countries, between the % satisfied and the % worried about
  traffic accidents (R = -0.47) and the % personally harmed in one (R = -0.14). The code calls the
  item `GWP_ROADS_SATISFACTION`. **This is a placeholder name**, because the Gallup item code is
  not known here. 1 is assumed to mean satisfied.
- **Satisfaction with efforts to preserve the environment** (X142–X144, PDF page 26): % satisfied
  among people who see climate change as a very serious threat (57%), not a threat (62%) or who
  don't know (66%). The code calls it `GWP_ENVIRONMENT_SATISFACTION`. **This is a placeholder
  name**, and 1 is assumed to mean satisfied.
- **Model controls (optional):** feelings about household income (`WP2319`) and not having enough
  money to buy food in the past 12 months (`WP40`). The item codes are believed to be right but
  should be checked against your Gallup file. The model runs without them, and its findings are
  not marked `GALLUP_ONLY`. If `GALLUP_WP_PATH` holds both items, the scripts add them as
  categorical controls (codes 1–4 and 1–2; other codes are left out of the model).

Both scripts were tested with a synthetic `GALLUP_WP_PATH` file holding these four columns. All the
Gallup code paths run, and Python and R agree.

## External data

None. The report quotes these statistics from other sources. They are context only and are not
reproduced:

- WHO: road traffic crashes kill around 1.2 million people a year; 92% of road deaths are in low- and
  middle-income countries, which have about 60% of the world's vehicles; road injuries were the 14th
  cause of death in 2021 (1.7% of deaths); non-communicable diseases (63%) and communicable
  conditions (27%) caused nine in 10 deaths in 2021; road traffic deaths are rising fastest in
  Africa.
- UN target to halve road traffic deaths by 2030.
- WHO: climate change will cause around 250,000 additional deaths a year between 2030 and 2050.
- Copernicus Climate Change Service (ERA5): monthly surface temperature anomalies, 1940–2024
  (Chart 3.1).
- Investopedia: Saudi Arabia is the largest oil exporter and the United Arab Emirates the eighth.

## Findings that do not match

6 findings differ from the published values by more than their tolerance:

- **Model odds ratios, 4 findings (X04 and C3_8_very, X138 and C3_9_tertiary):** 3.74 against
  3.6 for very worried about severe weather, and 1.95 against 1.7 for tertiary education. The
  report's model is multi-level, includes two Gallup World Poll controls and does not give its full
  specification. See the model note above for the specifications tried. The other four odds ratios
  (somewhat worried 1.62, secondary 1.32, male 1.11, large city 1.07) are within 0.1.
- **X18 (climate change or severe weather as the greatest risk, 2019):** 4.1% against the published
  3%. The 2019 code also covers non-weather disasters (see above), and the 2019 file has no
  narrower code. Not explained further.
- **C4_4_mental_2019 (worry about mental health, 2019):** Chart 4.4 prints 45%. The text gives 48%
  twice (PDF pages 4 and 29), and the data give 48.3%. The chart label looks wrong.

5 findings are within tolerance but do not round to the published figure:

- **X01:** "nearly 147,000" interviews (146,910).
- **X07:** road-related accidents as the greatest risk in 2019 are 15.5% against the published 16%
  (15.4% with all 142 countries of 2019). Not explained.
- **C2_1_climate_chg:** Chart 2.1 gives +3 points against 2021 for climate change or severe
  weather. The unrounded change is +3.6 (6.3% against 2.7%). The printed figure is the difference
  of the rounded figures, 6 - 3. The other Chart 2.1 changes match the unrounded changes (don't know
  is -8.3 unrounded and -9 from rounded figures, and the chart gives -8).
- **X30:** the text gives a five-point rise in worry about traffic accidents, from 71% to 76%. The
  unrounded rise is 4.3 points (71.3% to 75.6%).
- **X140:** odds ratio for men 1.11 against the published 1.15 (see the model note).

Two other inconsistencies in the report match the data on one side:

- Chart 3.5 draws Ireland's 'very serious threat' bar at about 47%, but labels it 65%. The data
  give 65.4%.
- Myanmar's uncertainty is 52% in the text and 51% in Chart 3.7. These are don't know or refused
  (51.9%) and don't know only (51.2%).

## Run

```
Rscript reports/WRP_2023/core_what_the_world_worries_about/reproduce.R
python reports/WRP_2023/core_what_the_world_worries_about/reproduce.py
```
