# World Risk Poll 2026: The quiet hazards: How everyday risk shapes daily life

- **Report:** *The quiet hazards: How everyday risk shapes daily life*, World Risk Poll 2026 report, Lloyd's Register Foundation, June 2026 (doi:10.60743/9djc-t718)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2026-09/world-risk-poll-report-2026-how-everyday-risk-shapes-daily-life.pdf
- **Data:** `WRP_2025/WRP_2025.parquet` (World Risk Poll 2025, wave 4; 143,459 respondents, 140 countries), with
  `WRP_2023`, `WRP_2021` and `WRP_2019` for the trends

## What is reproduced

All 930 numbers in the report: every value in Charts 1.1 to 4.10 and Tables 1.1 to 4.2, and every
number in the text, including percentage-point changes, counts ("six countries", "seven of the 10"),
ranks and the names in the ranking tables. Page numbers are the report's printed page numbers
(PDF page = printed page + 6 in the chapters). Results are in [`RESULTS.md`](RESULTS.md).

Four charts are scatter plots with no printed values: Chart 2.1 (worry vs harm by risk), Chart 2.4
(country Worry Index vs Experience of Harm Index), Chart 4.4 (wildfire harm vs worry in the most
burned countries) and Chart 4.7 (satisfaction with air quality vs worry). Their functions (`C2_1`,
`C2_4`, `C4_4`, `C4_7`) compute the plotted points, which are written to `output/` only; there are
no published values to compare. The numbers the text gives about them (for example "six countries",
"global average of nine", "r = 0.37") are compared.

## Method notes

- **Weights and base:** `PROJWT`; everyone asked the question, with don't know and refused in the
  base. Worry about work (`WP22214`) is asked only of current employees. Harm at work (`WP22448`) is
  reported for the current workforce: `EMP_2010` 1-5 (employed or unemployed).
- **"Worried" and "personally experienced" are sums of rounded percentages.** The report adds the
  rounded "very" and "somewhat" worried figures, and the rounded "yes, personally" and "both" harm
  figures (the note to Chart 2.2 says "the sum of Very worried + Somewhat worried"). The scripts do the
  same (`rsum`). This reproduces every value in Charts 2.2, 2.3, 3.4, 4.3 and 4.6 and the country
  totals in the text on page 29 (94 = 79 + 15). Adding unrounded percentages instead turns 56 of the
  715 matches into within-tolerance findings. Rounding is half up.
- **Changes and gaps** (Chart 1.1 "+6pp", Table 1.2 gap column, Chart 3.3 "+28", and the text's
  "down 2 points", "a gap of 44 points") are differences of the rounded figures, as printed. For
  example, Table 1.2 gives France 27% to 15%, a gap of 12 (unrounded: 12.6). The one exception is X62,
  "within one percentage point", which is compared unrounded.
- **Trends** (2019, 2021, 2023) use the countries surveyed in 2025, as footnote v says for 2019. This
  also reproduces the 2021 and 2023 values in Charts 1.2, 1.3, 2.2, 2.3 and 3.4; all countries in each
  wave do not (for example Southern Asia 2023 in Chart 1.2: 21.2% against the published 22%).
- **2019 items:** top-of-mind risk is `L3_A` (the first of two answers), worry is `L6A`-`L6G`, and
  harm at work is `L19` ("ever been seriously injured while working", asked of the employed).
- **2021:** China was not asked the top-of-mind question (`WP22331`) or the employment questions, so
  it drops out of those 2021 figures, as the report's note to Chart 3.1 says.
- **Top-of-mind risk (`WP22331`):** "Don't know" is don't know plus refused (India's 36% in 2025 only
  matches with both). Economy is code 10 alone in Chart 1.1 and Table 1.1, and economy plus financial
  (codes 9, 10) in Chart 1.4, as its note says. Chart 1.1's "Environment" (2%, no change) is pollution
  (code 18); climate change and severe weather is code 19.
- **Table 1.1** ranks the categories on percentages rounded to whole numbers and groups ties, as the
  table does ("Road-related accidents, Personal health 9%"). The value compared is the unrounded
  share of the first tied category. Labels are written in ASCII, and tied labels alphabetically (for
  example the table prints "Environment — climate change/severe weather" and "Road-related accidents,
  Personal health").
- **Table 2.1** ratios are unrounded % worried divided by unrounded % personally harmed.
- **Worry Index** is `worry_index_published` x 100. **Experience of Harm Index** is not in the data
  (`experience_index_published` is empty for 2025): the scripts compute it per respondent as the share
  of the 10 harm items answered "personally" or "both" (0-100), for respondents with no don't know or
  refused answer on the 10 items. This reproduces the country scores in Chart 2.4 (Chad 36, Philippines
  29, Comoros 28, Somalia 27.5, China 24, India 20.3) and exactly six countries at 20 or above.
- **"Global average of nine" (X76)** is 8.8 with the within-country weight `WGT` (each country
  weighted by its sample size). With `PROJWT` it is 13.9, and the mean of the 140 country scores is
  8.4. The income-group averages (for example "averaging 15" in lower-middle-income countries) use
  `PROJWT`.
- **Chart 4.2** groups respondents by their harm answer. The chart note says don't know and refused
  are excluded; that holds for the harm answer, but worry don't know stays in the base. Excluding it
  as well moves eight of the 32 bars up by a point, and then none of the eight matches.
- **Chart 4.5** shows the 13 countries whose worried total (rounded sum) is 84% or more; the text lists
  the first ten. **The U.S. rank of 109th (X129)** counts the countries at or above the U.S. rounded
  figure (46%): the U.S. is last of the countries tied at 46% (107th-109th). On unrounded figures it
  is 111th.
- **U.S. regions (Chart 4.6)** use `REGION2_USA` (Northeast, Midwest, South, West).
- **Chart 2.5** annotations use the same rounded sums; harm at work is among the workforce. "More
  than triple the global rate" is compared as the smaller of 62/17 and 62/19.
- **Text claims given as words** are compared as numbers: "nearly twice" and "more than twice" as a
  ratio of 2 (tolerance 0.5), "roughly two-thirds" as 67% (tolerance 2), "no two regions share the same
  top three" as 15 distinct rankings.
- **Balkans (X136):** Albania, Bosnia and Herzegovina, Bulgaria, Croatia, Greece, Kosovo, Montenegro,
  North Macedonia, Serbia and Slovenia.

## Gallup World Poll data

199 findings need Gallup World Poll items that are not in the public release. The code is included;
without the data these findings are reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item (name used in the code) | What it is | Findings |
| --- | --- | --- |
| `WP16`, `WP18` | Cantril ladder, life today and in five years. The scripts build the Life Evaluation Index groups from them: thriving (7+ now and 8+ in five years), suffering (both 4 or below), struggling (everyone else). | Chart 1.4, Chart 2.7, Chart 3.6, X58, X115, X116 |
| `EMP_WORK_HOURS` | Hours worked in a typical week, in five bands (1 = under 15 ... 5 = 50 or more). The name is the one Gallup's variable has in the 2019 release (`WRP_2019`), where it was included; it is not in the 2025 release. | Chart 3.5, Chart 3.6, X105-X116 |
| `GWP_DEGURBA` (placeholder) | Degree of urbanisation: 1 cities, 2 towns and semi-dense areas, 3 rural areas. | Chart 4.8, Table 4.1, X135, X136 |
| `GWP_AIR_QUALITY_SATISFACTION` (placeholder) | "In the city or area where you live, are you satisfied or dissatisfied with the quality of air?" (1 = satisfied). | Chart 4.7 (no printed values) |

`WP16` and `WP18` are Gallup's item codes. The last two names are placeholders; rename them to
Gallup's codes when you have the file. The self-reported `Urbanicity` in the public data (large city
or suburb / small town / rural) is not the same measure: it matches 6 of the 45 values in Chart 4.8.

The regressions on page 23 (X111-X114) are logistic regressions, unweighted, among current employees
in high-income countries who gave a worry answer: worried (very or somewhat) about harm at work on
hours band (reference 40-49 hours), age, gender, education, income quintile (`INCOME_5`),
employment status (`EMP_2010`) and `Urbanicity`. The second model adds worry about mental health
issues (`WP20726`, reference not worried). The value is (odds ratio - 1) x 100; 40-49 vs under 15
hours is the inverse of the under-15 coefficient. The report does not give its exact specification
or weights, so the tolerance is 10 points.

The Gallup code paths were tested with a synthetic file of random values (not committed): Python
and R give the same results.

## External data

| File | Source | Used for |
| --- | --- | --- |
| [`core_the_quiet_hazards__worldbank_pm25.csv`](../../external/core_the_quiet_hazards__worldbank_pm25.csv) | World Bank indicator `EN.ATM.PM25.MC.M3`, PM2.5 mean annual exposure (ug/m3), most recent year (2023). https://api.worldbank.org/v2/country/all/indicator/EN.ATM.PM25.MC.M3?format=json&per_page=20000&mrnev=1. Licence CC BY 4.0. Downloaded 2026-09-25. No value for Hong Kong, Taiwan or Kosovo. | Chart 4.9, X137 |
| [`core_the_quiet_hazards__gwis_burned_area.csv`](../../external/core_the_quiet_hazards__gwis_burned_area.csv) | Global Wildfire Information System (GWIS, European Commission JRC / Copernicus), 2025 burned-area estimates by country: https://api2.effis.emergency.copernicus.eu/statistics/v2/gwis/estimatesoverview?countries=<ISO3 list>&year=2025. `burned_pct` = burned area / country area x 100. Copernicus Emergency Management Service data: free, full and open access, redistribution allowed with attribution (Commission Delegated Regulation (EU) No 1159/2013); cite GWIS. It is not CC BY 4.0, so the maintainers may prefer to fetch it rather than commit it; the scripts read it through `external_path`. Downloaded 2026-09-25. No value for Kosovo. | X125, X126, Chart 4.4 |

Chart 4.9 bands countries by PM2.5 divided by the WHO guideline of 5 ug/m3 (7x or more, 5-7x, 3-5x,
2-3x, under 2x) and takes the median of the country percentages. The report used 2024 "Air Quality
Index (AQI)" PM2.5 data; the World Bank series is the closest public source.

Statistics the report quotes from other organisations are context and are not reproduced: the WHO's
99% of people breathing air above its limits; the ILO's estimate of about 3 million workplace deaths
a year; nearly 8 million deaths from air pollution in 2023 (Health Effects Institute); the World
Bank's $6 trillion health cost and 5% of GDP; the GWIS list of the 10 countries with most land
burned (eight in sub-Saharan Africa); the average annual temperatures in Chart 4.10; the weather
events described on page 35; and Lloyd's Register Foundation's £4.5 million investment.

## Findings that do not match

7 findings differ from the published values by more than the tolerance, all from external data:

- **X125 and X126 (GWIS):** the report counts 46 surveyed countries with at least 2% of land burned
  in 2025 and a correlation of 0.37 between wildfire harm and worry across them. The current GWIS
  estimates give 35 countries and r = 0.44. The estimates have been revised since publication: India
  (1.5%) and Brazil (1.9%), both labelled in Chart 4.4, are now below 2%, and the ten countries with
  most land burned are no longer the ones the report lists. At a 1% threshold there are 47 countries
  (r = 0.335).
- **Chart 4.9, 5 values:** the PM2.5 source differs (World Bank 2023, not the report's 2024 AQI
  data), so countries fall into different bands. The reproduced medians are 7.5, 6.2, 5.2, 3.6 and
  3.8% for harm and 42.6, 46.3, 47.0, 52.2 and 40.9% for worry (published 8, 5, 5, 5, 3 and 44, 46,
  47, 51, 42). The two harm values for the most and least polluted bands are within tolerance.

9 more findings are within tolerance but do not round to the published figure:

- **X01:** 143,459 interviews ("more than 143,000").
- **X64:** worry about drinking water "rose by four points"; Chart 2.2 shows 49% to 52% (3 points).
  Unrounded, the change is 3.5 points (3.6 with all 2023 countries).
- **X81:** 616 million workers harmed (published 610 million), from `PROJWT` totals.
- **C3_2_month_plus and X83:** 14% of workers who could cover basic needs for a month or more were
  harmed at work. Adding the rounded "personally" and "both" figures gives 15; the unrounded sum is
  14.1. This is the one chart where the rounded sums do not reproduce the published value.
- **X98:** 65% of adults are in the workforce ("roughly two-thirds").
- **X121:** the text gives 34% somewhat worried among those personally harmed by prolonged weather;
  Chart 4.2 prints 33% for the same bar. The data gives 33.5%.
- **C4_9_experience_x7plus and C4_9_experience_lt2x:** see Chart 4.9 above.

## Run

```
python reports/WRP_2025/core_the_quiet_hazards/reproduce.py
Rscript reports/WRP_2025/core_the_quiet_hazards/reproduce.R
```
