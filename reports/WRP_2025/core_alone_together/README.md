# World Risk Poll 2026: Alone together: The hidden consensus on climate change

- **Report:** *Alone together: The hidden consensus on climate change*, World Risk Poll 2026 report,
  Lloyd's Register Foundation, June 2026 (https://doi.org/10.60743/d5zy-ec79). The second-order
  question was developed with the UNDP Human Development Report Office.
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2026-09/wrp-report-2026-the-hidden-consensus-on-climate-change.pdf
- **Data:** `WRP_2025/WRP_2025.parquet` (World Risk Poll 2025, wave 4; 143,459 respondents, 140
  countries). The Chapter 1 trend also uses `WRP_2019`, `WRP_2021` and `WRP_2023`.

## What is reproduced

All 258 numbers in the report: every value printed in Charts 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 2.5,
2.6 and 2.8, and every number in the text. Results are in [`RESULTS.md`](RESULTS.md).

Charts 1.3 (eight high-income countries, 2019–2025) and 2.4 (personal against perceived societal
concern, by country) print no values, and Chart 1.4 prints values only for its annotations. So
there are no published values to compare for the rest of these charts. Their functions (`C1_3`,
`C2_4`, and the `change_<ISO3>` values of `C1_4`) write every plotted value to `output/`, where
Python and R are compared. Chart 2.7 prints only its two correlations (X57, X58). The "Country A"
and "Country B" illustration on page 6 (25 people each) is hypothetical and is not reproduced.

## Method notes

- **Questions:** personal view = `WP20719`, "climate change a threat to the country in the next
  20 years" (in 2019 it is `L5`, see `docs/CODEBOOK.md`). Perceived societal view = `WP24225`,
  "most other people in (country) view climate change as a threat", new in 2025. Both use 1 = very
  serious, 2 = somewhat serious, 3 = not a threat at all, 98 = don't know, 99 = refused.
- **Weights:** `PROJWT`, so the global, regional, income-group and EU figures are
  population-weighted.
- **Base:** everyone asked, with don't know and refused kept in the base. The report's "Don't
  know" includes refused (footnote i on page 2).
- **Alignment (page 5, page 7, Charts 2.2 and 2.8):** among respondents who gave a substantive
  answer to both questions (86.7% of adults). The report says this on page 7 and under Chart 2.2.
  "Aligned" means the same answer to both questions. "More personal concern" means the personal
  answer is more serious than the perceived societal one.
- **Trend (Charts 1.1, 1.2):** each wave uses all the countries surveyed that year (142, 121, 142,
  140), as the note to Chart 1.1 says.
- **Income groups:** `CountryIncomeLevel` from the 2025 file (World Bank FY2024-25). For the trend
  (Chart 1.2 and the 2019 figures in X08 and X10), **each wave's countries are grouped by their 2025
  income group**. Countries not surveyed in 2025 are left out (8 countries in 2019, 3 in 2021, 5 in
  2023). Each wave's own classification does not reproduce the chart: for example, 37% of adults in
  low-income countries saw a very serious threat in 2019, against the published 49%. Ethiopia and
  Venezuela are "not classified" in 2025 and are in no income group.
- **Country gaps and changes are differences of rounded percentages.** This applies to the gap
  column of Chart 2.5, the country counts (X04, X16, X39, X40), X44–X46, the eight high-income
  countries (X23, X24), and the Tunisia and Vietnam changes in Chart 1.4. The evidence:
  - The Chart 2.5 gaps for Uruguay (63 − 26 = 37), Spain (37), Argentina (36) and Chile (69 − 36 =
    33) match the rounded figures. The unrounded gaps are 36.4, 36.3, 35.3 and 33.5.
  - "110 out of 140" countries is 108 with unrounded gaps.
  - Only 5 high-income countries fell by 10 points or more unrounded. Denmark (−9.9), Canada (−9.6)
    and New Zealand (−9.5) make up the report's eight.
  - Vietnam's "+24pp" is 23.4 unrounded.

  Gaps for the world, income groups and single countries in the text use unrounded values, as in
  the other reports (for example, the high-income gap of 29 points is 28.7).
- **Significant change (Chart 1.4):** a change of more than 4 points in % very serious between 2023
  and 2025 (the chart's "+4pp margin of error"), on unrounded values. This reproduces all four
  counts: 23 of 50 high-income countries fell, 24 of 50 low- and lower-middle-income countries
  rose, 9 of those 50 (18%, "fewer than one in five") fell, and 5 of the 50 high-income countries
  (10%) rose. The report does not describe any other test. Rounded changes do not reproduce the
  counts.
- **EU (Chart 2.6, X55, X56):** the 27 member states, all surveyed in 2025, pooled with `PROJWT`.
- **Totals printed as sums of rounded figures.** The total labels in Chart 2.3, and "75%" (40% +
  35%), "71%" and "84%" in the text, add the rounded components. The script uses unrounded
  totals, so these findings are within tolerance rather than exact matches.
- **National vulnerability (X57, X58, Chart 2.7):** Pearson correlation across the 136 countries
  with an ND-GAIN score (Hong Kong, Kosovo, Palestine and Taiwan have none). It correlates each
  country's % very serious (don't know in the base, as in Charts 2.4 and 2.5) with the ND-GAIN
  vulnerability score. The score is the 2024 release's latest year, 2022; the report cites the
  2024 ND-GAIN technical report. This gives r = 0.058 and 0.514, against the published 0.06 and
  0.52. Other versions tried:

  | Version | r (personal) | r (perceived) |
  | --- | --- | --- |
  | 2024 release, 2022 (used here) | 0.058 | 0.514 |
  | 2023 release, 2021 | 0.046 | 0.512 |
  | 2026 release, 2024 | 0.004 | 0.488 |
  | 2024 release, don't know excluded | 0.153 | 0.547 |

  The report's footnote refers to a "2023 ND-GAIN release". The page 11 text says higher
  vulnerability scores mean lower vulnerability; in ND-GAIN, a higher score means more vulnerable.
- **Chart 2.8** is the mean of Gallup's National Institutions Index (0–100), weighted by `PROJWT`,
  by income group and alignment group (see below).

## Gallup World Poll data

Chart 2.8 (12 values, `C2_8_*`) needs Gallup's **National Institutions Index**. The index measures
confidence in the national government, the honesty of elections, the military, and the judicial
system and courts. It is not in the public release, and must be licensed from Gallup directly. The
code calls it `INDEX_NI`, which is our understanding of Gallup's name for the index. If your
licensed file uses another name, rename that column to `INDEX_NI`. Its component items are, to our
knowledge, `WP139`, `WP144`, `WP137` and `WP138`. The code is included; without the data these
findings are reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).
The code was tested with a dummy `INDEX_NI` file in both Python and R.

## External data

- **ND-GAIN vulnerability** (X57, X58). **Not redistributed here**, because ND-GAIN gives no
  formal licence. Download it with `python reports/external/fetch_external.py ndgain`, which
  writes `reports/external/downloaded/core_alone_together__ndgain_vulnerability.csv`. Without
  it, X57 and X58 are reported as `EXTERNAL_ONLY`. The file is `resources/vulnerability/vulnerability.csv` from the ND-GAIN Country Index 2024 release
  (https://gain.nd.edu/assets/581929/nd_gain_countryindex_2024.zip). It has one row per country
  (ISO3) and one column per year from 1995 to 2022; the script uses the 2022 column. Downloaded
  2026-09-25. The download page (https://gain.nd.edu/our-work/country-index/download-data/) now
  serves the 2026 release. ND-GAIN describes the index as "free and open-access" but gives no
  formal licence. The suggested citation is: Notre Dame Global Adaptation Initiative Country Index
  (ND-GAIN), University of Notre Dame.
- **Figures the report quotes from other sources** are not reproduced:
  - Copernicus: 2025 was the third-warmest year on record.
  - The Center for Global Development: welfare losses around five times higher in low-income
    countries.
  - Rhodium Group: the largest emitters.
  - UNDP Human Development Report 2023/24: the quotation on page 5.
  - Lloyd's Register Foundation's £4.5 million invested in interventions.
  - The top-of-mind risk ranking from the *Quiet hazards* report (Chart 1.1 there).

## Findings that do not match

2 findings differ from the published values by more than their tolerance:

- **X04 (foreword):** the foreword says that in 10 countries the gap between personal and
  perceived societal concern exceeds 30 points. The data gives 14 countries on rounded figures
  (15 unrounded). These are the ten in Chart 2.5, all 33 points or more, plus Brazil, Cyprus and
  Australia (32 each) and Japan (31). The foreword seems to describe the ten countries in Chart
  2.5, whose smallest gap is 33 points (X46 matches).
- **X54 (India):** "nearly one in five Indian adults say they 'don't know' across both questions".
  16.8% answer don't know or refused to the perceived societal question, which Chart 2.6 prints as
  17%. That is closer to one in six. The personal question (18.2%, X53) fits the wording. Not
  explained beyond loose wording.

16 more findings are within tolerance but do not round to the published figure:

- **Sums of rounded figures:** X03, C1_1_any_2025, X09, X35, X47 and three Chart 2.3 totals (see
  Method notes).
- **X25:** "67% in step with society" on page 5; page 7 and Chart 2.2 give 66%, and the data gives
  66.4%.
- **X29:** 33% misaligned, printed as 22% + 11%; unrounded 33.6%.
- **Upper bounds:** X37 ("within one point", 0.4), X38 ("within five points", 5.5, which is 5 on
  rounded figures) and C1_4_lower_fall_share ("fewer than one in five", 18%).
- **X53:** 18.2% for "nearly one in five".
- **X58:** r = 0.514 against 0.52 (see the ND-GAIN note).
- **X01:** 143,459 interviews for "more than 143,000".

## Run

```
Rscript reports/WRP_2025/core_alone_together/reproduce.R
python reports/WRP_2025/core_alone_together/reproduce.py
```
