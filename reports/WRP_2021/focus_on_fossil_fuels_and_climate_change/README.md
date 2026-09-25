# World Risk Poll 2021 Focus On: Fossil fuel dependency and perceptions of climate change

- **Report:** *World Risk Poll 2021 Focus On: Fossil fuel dependency and perceptions of climate change*, Lloyd's Register Foundation, June 2023
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-05/WRP_FocusOn_Climate%20%281%29.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries).
  The report uses only the 2021 poll: every figure matches the 2021 data, and no 2019 data is used.

## What is reproduced

All 37 numbers the report publishes from the poll: 19 in the text and 18 in the charts
(the annotations on Chart 1, and the regional values on the Norway and Canada maps,
Charts 7 and 8). Results are in [`RESULTS.md`](RESULTS.md).

Charts 1 to 6 print no data values. Each one still has a function that computes it:

- **Chart 1** (`C1`): every country's % who see climate change as a 'very serious threat'
  (top circles) and % who name climate change as their greatest source of risk (bottom
  circles). Only the chart's three annotations are compared.
- **Charts 2 to 5** (`C2`–`C5`): % 'very serious threat' for the countries labelled on each
  chart. The other axis of these charts is Our World in Data (see External data).
- **Chart 6** (`C6`): % 'very serious threat' in each country where fuel is more than 50% of
  merchandise exports (World Bank). The chart's claim is compared as finding X13.

There are no published values to compare for these functions, so they appear only in
`output/`, not in `RESULTS.md`.

Pages are PDF pages. The page number printed on each page is one less.

## Method notes

- **Climate change question:** `WP20719`, "Do you think climate change will be a threat to
  the people in your country in the next 20 years?" 'Very serious threat' is code 1, and
  'very or somewhat serious' is codes 1 and 2.
- **Greatest source of risk:** `WP22331` (coded), code 19, "ENVIRONMENT: Climate change or
  severe weather-related events". It was not asked in China.
- **Weights:** `PROJWT`, so the global figures are population-weighted.
- **Base:** everyone asked the question, with don't know and refused included. This gives
  the headline figures: 41% and 67% globally, 87% and 94% in Chile, 8% and 31% in Saudi Arabia.
- **Chart 1 regions:** Europe is `GlobalRegion` 12 to 14 and Latin America is 5. The 12
  countries with the highest % 'very serious threat' are all in these regions. Sierra Leone
  is 13th.
- **'Less than 1%' (X10):** recorded as 0.5 with a tolerance of 0.5, so any value from 0 to 1
  is within tolerance. Chile's value is 0.7%.
- **Count findings** (X11, X13, C1_top12_latam_europe, X14) test a statement in the text and have a
  tolerance of 0.
- **Energy exports (X13, Chart 6):** fuel exports as a % of merchandise exports, World Bank
  WDI `TX.VAL.FUEL.ZS.UN`, 2021 values. In the current WDI release, 8 of the countries
  surveyed have fuel exports above 50% in 2021: Nigeria, Saudi Arabia, the United Arab
  Emirates, Norway, Kazakhstan, Congo Brazzaville, Gabon and Cameroon. In all 8, fewer
  than 50% say 'very serious threat' (Norway is the highest, at 45%), so the claim holds.
  The chart itself seems to mix years: Norway (78%) and Australia (42%) match the 2022
  values, and Saudi Arabia (77%) and Russia (43%) match 2021. With 2022 values the claim
  fails for one country: Colombia (fuel exports 54.5% in 2022, 64% 'very serious
  threat'). WDI values are revised over time. For example, the chart shows Kazakhstan at
  about 57%, and the current release has 66% for 2021 and 68% for 2022. So a current
  download will not match the report's snapshot exactly.
- **Norway regions (Chart 7):** built from the 2020 counties in `REGION4_NOR`. This grouping
  reproduces all five published values:

  | Report region | Counties (`REGION4_NOR` code) | n |
  | --- | --- | --- |
  | Northern Norway | Nordland (4), Troms og Finnmark (12) | 69 |
  | Trøndelag | Møre og Romsdal (3), Trøndelag (11) | 122 |
  | Western Norway | Rogaland (2), Vestland (10) | 198 |
  | Eastern Norway | Oslo (1), Viken (5), Innlandet (6) | 484 |
  | Southern Norway | Vestfold og Telemark (7), Agder (8) | 126 |

  So the map's "Trøndelag" includes Møre og Romsdal. If Møre og Romsdal is counted in
  Western Norway, Trøndelag becomes 48% and Western Norway 38%. One respondent with an
  unknown county is left out.
- **Canadian provinces (Chart 8):** the public release codes Canada in eight regions
  (`REGION_CAN`). Quebec (Montreal CMA plus the rest of Quebec), Ontario (Toronto CMA plus
  the rest of Ontario) and British Columbia (Vancouver CMA plus the rest of BC) can be built,
  and all three match. The other seven provinces need a province variable (see below).

## Gallup World Poll data

Findings X19 and seven values of Chart 8 (Alberta, Saskatchewan, Manitoba, Newfoundland
and Labrador, Nova Scotia, New Brunswick, Prince Edward Island) need respondents' Canadian
province. The public release does not have it. `REGION_CAN` combines Alberta,
Saskatchewan and Manitoba as "Prairies" (48.3% 'very serious threat') and the four
Atlantic provinces as "Atlantic" (57.9%). The code uses a placeholder item name,
**`GWP_CANADA_PROVINCE`**, holding the province name as text (for example "Alberta"). The
real Gallup item name and coding are not known. Adjust the name and values to match the
file you license. Without the data, these 8 findings are reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

These provinces have few respondents in a sample of 1,010. So the published values for
the smaller provinces rest on very small bases.

## External data

- **World Bank, World Development Indicators: Fuel exports (% of merchandise exports),
  `TX.VAL.FUEL.ZS.UN`.** The report cites this for Chart 6 (endnote 5).
  Snapshot: [`reports/external/focus_on_fossil_fuels_and_climate_change__worldbank_TX.VAL.FUEL.ZS.UN.csv`](../../external/focus_on_fossil_fuels_and_climate_change__worldbank_TX.VAL.FUEL.ZS.UN.csv)
  (`country_iso3`, `country`, `indicator`, `year`, `value`). It has the years 2021 and 2022,
  and countries only (regional and income aggregates are removed, using the API's country
  list). Source:
  `https://api.worldbank.org/v2/country/all/indicator/TX.VAL.FUEL.ZS.UN?format=json&date=2021:2022&per_page=1000`.
  Downloaded 2026-09-25. The WDI release was last updated 2026-07-13. Licence: CC BY 4.0.
  The scripts use the 2021 values. Taiwan is not in the World Bank data. Afghanistan,
  Algeria, Bangladesh, Guinea, Iraq, Israel, Kosovo, Serbia, Sierra Leone and Venezuela have no
  2021 value.
- **Our World in Data** (CO₂ emissions per capita, Charts 2 and 3; fossil fuel energy
  production, total and per capita, Charts 4 and 5; fossil fuels as a share of primary
  energy, Chart 6 bottom). These charts print no values from this data, so it is not
  downloaded.

Statistics from other sources that the report quotes, not reproduced here:

- Fossil fuels and energy make up "around 75%" of all exports for Saudi Arabia, the United
  Arab Emirates and Norway (World Bank; the 2021 snapshot gives 76.6%, 70.3% and 68.9%).
- Fossil fuels are 27% of primary energy in Norway, 97% in the United Arab Emirates and 100%
  in Saudi Arabia. Norway has the second-lowest share of any country (Our World in Data).
- China, the United States and Russia are the three biggest producers of fossil fuel energy
  (Our World in Data).
- Norway: over 5% of the workforce is employed in oil and gas. Oil and gas exports were worth
  $175 billion in 2022. Norway supplied 25% of the gas needs of the EU and UK in 2022. There
  are over 70 North Sea fields in production, and the moratorium on Barents Sea exploration
  was lifted in 2005.
- Canada: over 98% of the known economically recoverable oil is in Alberta's oil sands.
  Canada targets a 45% cut in carbon emissions by 2030.

## Findings that do not match

1 finding differs from the published value:

- **X14 (smallest country sample):** the text says the Poll "includes at least a thousand
  or more residents in each country". In 2021, Iceland (500 respondents) and Jamaica (505)
  had fewer. The other 119 countries had 1,000 or more.

3 more findings are within tolerance but do not round to the published figure:

- **X02:** 125,911 respondents ('over 125,000').
- **X10:** Chile 0.7% ('less than 1%'). See the method notes.
- **X18 (Canada):** 60.2% against the published 61%. Excluding don't know and refused gives
  66.3%, and the unweighted share is 62.2%. Not explained. The regional values that can be
  built from the public data all match.

## Run

```
python reports/WRP_2021/focus_on_fossil_fuels_and_climate_change/reproduce.py
Rscript reports/WRP_2021/focus_on_fossil_fuels_and_climate_change/reproduce.R
```
