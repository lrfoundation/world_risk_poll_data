# World Risk Poll 2021 Focus On: Critical infrastructure resilience and perceptions of disaster preparedness

- **Report:** *World Risk Poll 2021 Focus On: Critical infrastructure resilience and perceptions of disaster preparedness*, Lloyd's Register Foundation, October 2023
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-05/Focus-On-Resilience.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries)

## What is reproduced

All 191 numbers in the report: every value in Charts 1 to 7 and Table 1, and every number in
the text, including percentage-point gaps and the counts of regions and countries. Results
are in [`RESULTS.md`](RESULTS.md).

The report's charts are numbered 1 to 7 without chapters, so chart values use
`C<chart>_<key>` and Table 1 uses `T1_<ISO3>_<column>`. Page numbers are PDF page numbers
(the printed page number plus one).

## Method notes

- **Weights and base:** `PROJWT`. Each percentage uses everyone asked the question, with
  don't know and refused in the base.
- **Lost access to critical infrastructure:** went without electricity (`WP22254`), clean
  drinking water (`WP22255`), food (`WP22256`), medicine or medical care (`WP22257`) or a
  telephone (`WP22258`) for more than a day in the past 12 months. "Any" is yes to at least
  one of the five; does not apply, don't know and refused count as no.
- **Experienced a disaster:** `WP22245` = yes (past five years). Chart 1 compares yes with no.
- **Government well prepared:** local government is `WP22244` and national government is
  `WP22241` (1 = yes, well prepared). Myanmar was asked about "the government in power"
  (`WP22526`) instead of the national government, and that item is used for Myanmar. This
  reproduces South-eastern Asia in Charts 3 and 4 (national 65%, gap 0). Without Myanmar,
  national is 68% and the gap is 2. It also makes South-eastern Asia one of the four regions
  where local government is ahead (X16).
- **Mean perceived governmental preparedness** is the mean of the national and local
  percentages for the region or country.
- **Gaps** are national minus local, so positive values favour national government. They
  are computed from unrounded percentages.
- **Chart 2** plots each region's mean perceived preparedness against the % who could
  protect themselves or their family in a future disaster (`WP22252` = yes). Only the R²
  (0.2) is printed. The function also returns the 15 points. It uses the squared Pearson
  correlation across the 15 regions, unweighted.
- **Charts 5 and 6, X26:** respondents who experienced a disaster and lost access to the
  service (Chart 5) or to any service (Chart 6).
- **Chart 7 (Eastern Africa countries)** uses a different summary: for each of the five
  services, the gap (and mean) among those who experienced a disaster and lost that service,
  then the mean of the five. All 14 country values round to the printed figures; the
  "any service" base used for Chart 6 does not (for example Zambia 21.6, Kenya 8.9). X36–X38
  quote Chart 7 values and use the same method.
- **Table 1:** countries are ranked by % who experienced a disaster (1 = highest), among the
  118 countries with both preparedness questions (or Myanmar's replacement). China, Algeria
  and Saudi Arabia were not asked. The table's heading says "of 119 countries" (X17), but
  all ten printed ranks match the 118-country ranking; Singapore is 118th, the last place.
- **"Only in four regions" (X16) and "only three regions" (X25):** South-eastern Asia's gap
  is −0.5. X16 counts regions where local is ahead (4); X25 counts gaps that round to below
  zero, as printed in Chart 4 (3). Both statements match on these readings.
- **Words as numbers:** "over half" (X08), "nearly a quarter" (X09) and "more than 4 in 5"
  (X21) have tolerances that cover the wording (see each row's note).

## Gallup World Poll data

None needed. The report's "confidence in national/local government" refers to the World
Risk Poll preparedness questions (`WP22241`, `WP22244`), which are in the public release. It
does not use the Gallup World Poll "confidence in institutions" items.

## Figures quoted from other sources

These are not from the poll and are not reproduced: the Sendai Framework (2015); the
Foundation's Foresight Review of Resilience Engineering (2015); the 2020 Tanzania floods and
Tanzania's National Disaster Management Strategy (2022–2027); the MV Wakashio grounding in
July 2020 (a 200,000-tonne bulk carrier; about 1,000 tons of heavy fuel oil); the 2020
Beirut port explosion and the 17 October Revolution in Lebanon; and the 2021 US troop
withdrawal from Afghanistan.

## Findings that do not match

10 findings differ from the published values by more than the tolerance:

- **X02, X07 (lost access among those who experienced a disaster, "75%", "3 in 4"):** the data
  gives 69.1%. Chart 1 uses the same groups and matches. Tried: `WGT` (70.0%), only those
  giving a yes/no answer to all five services (68.7%), and the unweighted mean of the country
  figures (66.4%). Not explained.
- **C1_medicine_no_disaster:** published 28%, data 17.8%. The other nine Chart 1 values
  match, including 29% for medicine among those who experienced a disaster. The bar is drawn
  at 28%, so this is probably an error in the chart. Not explained.
- **Chart 6, 5 regions (South Asia, Central Asia, East Asia, Northern/Western Europe,
  Southern Africa), and X33, X34:** among those who experienced a disaster and lost any
  service, these regions give 4.6, 5.4, 0.3, −10.2 and 3.2 against 7, 9, 2, −12 and 7. The
  other 10 regions and the global average (+5) match. Chart 7's method (the mean of the five
  services) reproduces these five (6.5, 9.0, 2.2, −11.5, 7.2). But it moves six other regions
  more than a point away (for example North Africa 8.3, which the text gives as 11), and the
  global average to 5.9. The chart seems to mix the two summaries. X33 and X34 (the
  Northern/Western Europe shift from −4 to −12, "8 points") follow from C6. Also tried:
  don't know counted as experiencing a disaster or losing access, don't know or "it depends"
  excluded, and `WGT`. None fits better.

19 more findings are within tolerance but do not round to the published figure. They
include all five Chart 5 values, which are printed to one decimal and are within 0.25 points
of the data. Tried for Chart 5: `WP22241` without Myanmar (water 6.8 matches; electricity
5.3, food 7.1, medicine 5.6, telephone 5.8), and respondents asked both questions
(electricity 5.1 and water 6.8 match; food 7.0, medicine 5.5, telephone 5.7).

Not recorded, because they are not numbers: page 7 says Tanzania "leads the way" in Eastern
Africa, followed by Zimbabwe and Uganda. In Chart 7 Zambia equals Tanzania at 18 (18.0 and
17.7 in the data). The same page calls Eastern Africa's 12-point gap the largest. That is
true of Chart 6 (Latin America and the Caribbean is also printed as 12), but not of Chart 4,
where North Africa is 17.

## Run

```
Rscript reports/WRP_2021/focus_on_critical_infrastructure/reproduce.R
python reports/WRP_2021/focus_on_critical_infrastructure/reproduce.py
```
