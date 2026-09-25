# World Risk Poll 2024: A World of Waste

- **Report:** *A World of Waste: Risks and opportunities in household waste management*, World Risk Poll 2024 report, Lloyd's Register Foundation, September 2024 (42 pages)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-10/WRP24%20-%20Waste%20Report%201_2.pdf
- **Data:** `WRP_2023/WRP_2023.parquet` (World Risk Poll 2023, wave 3; 146,910 respondents, 142 countries and territories)

## What is reproduced

All 817 numbers in the report: every value printed in Charts 2.1 to 6.1 and Tables 2.1, 2.2,
3.1, 6.1 and 6.2 (including the two maps, Charts 5.8 and 5.11), and every number in the text,
including counts such as "22 countries" and approximate wordings such as "four in five".
Each ranked table or chart also has a text finding (`..._top10`, `..._top15`, `..._countries`)
that checks that the data give the same list of countries. Results are in [`RESULTS.md`](RESULTS.md).

618 findings use only the public data: 598 match and 20 are within tolerance. The other 199
need Gallup World Poll data (see below).

Page numbers in `published_figures.csv` are PDF pages. The printed page number is 4 less from
PDF page 5 on; the executive summary is PDF page 3.

Charts 4.4 (collection against burning, by country) and 6.2 (collection, separation and dry
recyclables, by country) are scatter and bubble plots with no printed values. Their functions
(`C4_4`, `C6_2`) compute the country values, but there are no published values to compare.
The only printed number, the correlation of -0.79 in the Chart 4.4 footnote, is finding X77.

## Method notes

- **Questions:** most common material in household waste (`WP23341`), whether household waste
  is separated (`WP23342`) and what happens to it once taken outside the home (`WP23343`).
  Climate change concern is `WP20719`.
- **Weights:** `PROJWT`. Country, Indian state and Brazilian state figures are the same under `WGT`.
- **Base:** all respondents, with don't know and refused kept in the denominator. This
  reproduces the headline figures (for example 42% plastic, 53% separate, 44% government
  collection) and every income-group figure.
- **Groups:** income groups use `CountryIncomeLevel`. Venezuela (not classified) is in the
  global figures but in no income group. Regions use `GlobalRegion`, age `AgeGroups4`,
  education `Education` and income quintiles `INCOME_5`.
- **Material categories:** food and green waste = food or household dust (`WP23341` 2, 5).
  Dry recyclables = plastic, cardboard/paper, cans/metal or glass (1, 3, 4, 7). The "other"
  segment of Chart 2.2 is cans, ash, glass, other, don't know and refused.
- **Collected** ("controlled disposal") = government, community group or private company
  (`WP23343` 2, 3, 4). **Uncontrolled** = burns, takes it to the tip, throws it outside (1, 5, 6).
- **Quadrants (Chapter 6):** separated means "yes" only, and "sometimes" counts as not
  separated, as the report's footnote says. Anything other than organised collection counts
  as not collected.
- **Chart 4.3 (burning is the most common method):** burning is compared with dumping,
  taking to the tip and all collection combined, on shares rounded to whole numbers. Benin
  burns 29.3% and takes 28.7% to the tip. Both round to 29%, and Benin is not in the chart.
  With unrounded shares there would be 23 countries, not 22.
- **Page 12 ("differences of 10 percentage points or more"):** these are gaps that round to
  10 or more. Ukraine (9.9) and Kyrgyzstan (9.6) are in the report's list of ten.
- **Page 11 ("the gap between men and women increases to more than five percentage points"):**
  the gap in either dry recyclables or food and green waste. In Eastern Europe the dry
  recyclables gap is 4.9 points and the food and green waste gap is 5.4.
- **Age-gap rankings (Table 2.2, Chart 3.4):** countries with fewer than 100 respondents aged
  15–29 or 65+ are left out. Without this rule, the Chart 3.4 top 15 includes Saudi Arabia
  (three respondents aged 65+), Tanzania, Nigeria, Singapore and Somalia. With it, the data give
  the chart's 15 countries exactly. Table 2.2 gives the same top 5 either way.
- **Printed gap columns** (Table 2.2, Charts 3.4, 5.3 and 5.4) are differences of the rounded
  figures, as the notes to Charts 5.3 and 5.4 say. For example, Bulgaria is 82% vs 42% in
  Table 2.2, a printed gap of 40; the unrounded gap is 39.4. Gaps in the text use unrounded
  values. Rankings use unrounded gaps.
- **Eastern Europe in the text** (pages 12 and 33) includes the Western Balkans (Albania,
  Bosnia and Herzegovina, Montenegro, North Macedonia, Serbia) and Georgia. In `GlobalRegion`,
  these countries are Southern Europe and Central Asia. Findings X57 and X99 count
  countries with this wider definition, which gives the report's "three" and "seven".
  Sub-Saharan Africa is Eastern, Central/Western and Southern Africa.
- **X91 (India, "41% of households that burn their waste but do not separate it"):** read as the
  share of Indian households that burn their waste and do not separate it (41.3%). As a share of
  all Indian households it would be 9.4%.
- **Chart 5.6 (India, plastic):** the chart gives 51% and 58% for "burns it", and 33% and 39% for
  "waste is collected". With the text ("households that burn their waste are also much more
  likely to cite plastic"), this is read as the share whose main waste is plastic among
  households that burn, and among households whose waste is collected. Nationally, the public
  data give 53% and 35%, which fits this reading.
- **Maps (Charts 5.8, 5.11)** use `REGION_IND` and `REGION_BRA`. State samples are small
  (India 20 to 520 respondents; Brazil 10 to 230). All 44 map labels match.
- **Approximate wordings** ("four in five", "around three in five", "nearly 30 times", "more than
  twice") have a tolerance that covers the wording. Each one is in the row's note.
- **Counts, flags and ranks** must match exactly (tolerance 0). A flag is 1 when a stated
  condition holds, for example "more than 50 points".

## Gallup World Poll data

199 findings need Gallup World Poll items that are not in the public release. Those items must
be licensed from Gallup directly. The code is included. Without the data, these findings are
reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

- **Degree of urbanisation** (197 findings): every "cities / towns and semi-dense areas / rural
  areas" figure. These are X10, X11, X45, X46, X84–X90, X94, X95, and Charts 5.2–5.7, 5.9 and
  5.10, which include all of the urban-rural analysis of India and Brazil. The report uses the
  Degree of Urbanisation classification (cities, towns and semi-dense areas, rural areas). This
  is not the self-reported `Urbanicity` variable in the release. The code calls it
  `GWP_DEGURBA`. **This is a placeholder name**, because the Gallup item code is not known here.
  The codes are assumed to be 1 = cities, 2 = towns and semi-dense areas and 3 = rural areas.
  Rename the column in your Gallup file, or change the name in both scripts.
  Using `Urbanicity` instead (large city or suburb = cities, small town or village = towns,
  rural area or farm = rural) does not reproduce the report. Only 57 of the 197 findings come
  within a point. For example, collection in cities in low-income countries is 48% against the
  published 39%, and burning in rural Brazil is 47% against 36%.
- **Satisfaction with air quality** (X93, 2 findings): "27% of residents [of Delhi] express
  dissatisfaction, compared to an average of 15% across the rest of India". This is the Gallup
  World Poll question on satisfaction with the quality of the air where the respondent lives.
  The code calls it `GWP_AIR_QUALITY_SATISFACTION`. **This is a placeholder name**, and 2 is
  assumed to mean dissatisfied.

Both scripts were tested with a synthetic `GALLUP_WP_PATH` file holding these two columns. All
the Gallup code paths run, and Python and R agree.

## External data

None. The report quotes these statistics from other sources. They are context only and are
not reproduced:

- UNEP: more than two billion tonnes of municipal solid waste a year, rising to 3.4–3.8 billion
  tonnes by 2050 (UNEP and World Bank). 38% of municipal solid waste in 2020 was uncontrolled
  (Global Waste Management Outlook 2024).
- UNEP Global Resources Outlook: plastics production contributes 4.5% of global climate impacts.
  Enough plastic to fill 2,000 garbage trucks is dumped into water supplies each day.
- UN: less than 10% of single-use plastics have ever been recycled.
- World Bank *What a Waste 2.0*: food and green waste are 44% of global waste.
- Up to 1 million deaths a year in lower-income countries from diseases related to
  mismanaged waste.
- Eswatini has a population of just over a million. Indonesia is the fourth most populous
  country and the second-biggest producer of plastic waste.
- The poll's coverage: "more than 95% of the world's adult population" (page 6).

## Findings that do not match

None. No finding is `DIFFERENT`.

20 findings are within tolerance but do not round to the published figure:

- **17 approximate wordings:** "nearly 147,000" (146,910); "four in 10" uncontrolled (40.5%);
  Indonesia "nearly half" and "half" (47.6%; the report also gives 48%); Eswatini "three in
  four" (77.2%; the report also gives 77%); "around two in five" (41.3%, 42.6%); "nearly 30
  times" (28.3); "more than two and a half times" (2.57); "around four in five" (four regions,
  78.6%–83.6%); "around three in five" (five regions, 58.5%–64.0%).
- **3 other values:** Uttar Pradesh 35.5% (published 36%) and Bahia 11.5% (published 12%) on the
  maps are at a rounding boundary. Malawi is 55.3% in the data and 56% in Chart 4.3; this is not
  explained.

One inconsistency in the report cannot be checked without the Gallup data. For the poorest rural
households in Brazil, the text gives 42% (X95_rural_q1) and Chart 5.10 prints 41% for the same
figure. Both are recorded.

## Run

```
Rscript reports/WRP_2023/core_a_world_of_waste/reproduce.R
python reports/WRP_2023/core_a_world_of_waste/reproduce.py
```
