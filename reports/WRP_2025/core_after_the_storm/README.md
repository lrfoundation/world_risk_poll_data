# World Risk Poll 2026: After the storm: How disasters reshape resilience and trust

- **Report:** *After the storm: How disasters reshape resilience and trust*, World Risk Poll 2026 report, Lloyd's Register
  Foundation, October 2026 (doi:10.60743/16n7-bn41)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-after-the-storm.pdf
- **Data:** `WRP_2021`, `WRP_2023` and `WRP_2025` (World Risk Poll 2021, 2023 and 2025), for ten countries: the seven
  case studies (Morocco, Ecuador, Mozambique, New Zealand, Türkiye, Pakistan, South Africa) and Thailand, the Philippines
  and Lebanon; Chapter 1 uses every country

## What is reproduced

All 1,132 numbers in the report: every value in the charts and tables, including the one-decimal estimates and
intervals in appendix Tables A.1 to A.4, and every number in the text, including counts of regions and respondents.
Page numbers are the report's printed page numbers (PDF page = printed page + 6; roman numerals for the front matter).
A number the report repeats is recorded once, with every page it appears on. Results are in [`RESULTS.md`](RESULTS.md).

Charts 2.8 and 4.1 to 4.3 have no printed values: they plot the estimates in Tables A.1 and A.3, which are compared.
The maps (Charts 2.1 to 2.7 and 4.4 to 4.7) are compared through the regional changes and sample sizes their text and
notes give.

## Method

- **Comparison.** In each country, respondents in the affected regions (A = 1) are compared with the rest of the
  country. The difference-in-differences is the coefficient on A × 2023 in a weighted least squares regression of the
  outcome on A, the 2023 wave and their interaction, weighted by `PROJWT`. Intervals are HC1 (heteroskedasticity-robust,
  with the n / (n − k) correction), estimate ± 1.96 SE. This reproduces every estimate and interval in Tables A.1 and
  A.2 that the public data can compute.
- **Affected regions** (Table 2.1): Marrakech-Safi (`REGION_MAR` provinces mapped to the 12 regions in 2021,
  `REGION3_MAR` = 7 after); Guayas and El Oro (`REGION_ECU` 8, 6); Sofala, Zambezia and Manica (`REGION_MOZ` 8, 10, 4);
  Northland and Auckland (`REGION_NZL` 1, 2); the Mediterranean and Central East Anatolia (`REGION3_TUR` 6, 11); Sindh
  (`REGION_PAK` 1); KwaZulu-Natal (`REGION_ZAF` 4).
- **Region don't know and refused.** In Ecuador the five respondents who gave no province are left out (the published
  estimates match only that way). In Morocco 2021 the seven who gave no province stay in the rest of the country (they
  match only that way).
- **Outcomes.** The Index and its dimensions times 100 (`resilience_index_100` is already 0 to 100). The questions are
  0 or 100, with don't know and refused (and "it depends") in the base: government cares 'a lot' (`WP22231` = 1),
  neighbours care 'a lot' (`WP22232` = 1), could protect their family (`WP22252` = 1), disaster exposure (`WP22245`,
  `WP23344`, `WP24213` = 1), national government well prepared (`WP22241`, `WP24198` = 1), local government
  (`WP24199` = 1), and confidence in national government (`WP139` = 1, Gallup). The Worry Index is
  `worry_index_published` times 100.
- **Three waves (Table A.3, Chart 4.9).** One regression per case and measure with A, wave dummies and their
  interactions gives the gap at each wave; the 2023 to 2025 change is the difference of the two interactions. The
  adjusted column removes Southeast Anatolia (Türkiye) and Hawke's Bay, East Cape, Waikato and Bay of Plenty (New
  Zealand) from both groups.
- **Pooled models (Tables 2.2 and A.4).** One regression on the stacked case studies with country-by-wave dummies,
  country-by-affected dummies and A × 2023 (and A × 2025 for Table A.4), with `PROJWT` rescaled to sum to one in each
  country and wave. Confidence pools the five case studies that asked it; government care in Table A.4 pools Türkiye and
  New Zealand. The appendix sensitivity checks (without Ecuador; region- and PSU-clustered CR1 intervals; the
  exploratory slopes on months and on the exposure check) and the four-case model are coded the same way. Months are the
  case attributes in Table 2.1, entered in the scripts.
- **Maps.** Regional changes are the change in the weighted regional mean. Sample sizes count respondents with an Index
  score. Pakistan's former FATA is shown with Khyber Pakhtunkhwa, as on the map.
- **Changes** (chart bars, map regions and the text) are the unrounded change, rounded half up.
- **Countries measured in both editions (X06).** 120 countries have Index data in 2021 and 2023; 118 have an overall
  Index score in both (China and Saudi Arabia have none in 2021). The Index fell in 74 and rose in 44 (published 75 and
  43); the individual dimension fell in 87.

## Gallup World Poll data and region codes

458 findings need data that is not in the public release. The code is included; without the data these findings are
reported as `GALLUP_ONLY`. See [`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item (name used in the code) | What it is | Findings |
| --- | --- | --- |
| `REGION_ZAF` (2021) | South Africa's province in 2021 (public from 2023) | Every South Africa estimate that uses 2021 (211 findings), so also the seven-case pooled models |
| `REGION_NZL` (2025) | New Zealand's region in 2025 (the public file has only North and South Island) | Every New Zealand estimate that uses 2025, so also Table A.4 (196 findings) |
| `WP139` | Confidence in national government (1 = yes) | Charts 3.2 and 3.6, Tables A.2 to A.4 and Table 2.2 confidence rows (83 findings) |
| `WP12259`, `WP12258` | Primary sampling unit and stratum | PSU-clustered intervals (X37) |
| `REGION_TUR` (2025) | Türkiye's NUTS-2 unit in 2025 | X25 |
| `REGION_MOZ`, `REGION_PAK`, `REGION_ECU` (2025) | Province in 2025 (the public file has only macro-regions) | X28 |

The scripts expect each item under the name in the table, with the same codes as the public variable of that name in
the other waves. South Africa's changes from 2023 to 2025 need no Gallup data and are compared through Chart 4.7 and
X31.

The Gallup code paths were tested with a synthetic file of random values (not committed): every finding runs, and
Python and R give the same results.

## Findings that do not match

One finding differs from the published value by more than its tolerance:

- **X19, perceived neighbourly care without KwaZulu-Natal.** The report says the seven-case rise of seven percentage
  points "halves to four" without KwaZulu-Natal. The six-case pooled model gives 3.0 (HC1 −1.4 to 7.4). The seven-case
  model needs South Africa's 2021 provinces, so the difference cannot be traced further with the public data.

Within tolerance but not rounding to the published figure:

- **Double rounding.** Some whole numbers are rounded from a one-decimal value: Table 2.1's lower bound for Türkiye
  (26.48, Table A.2 26.5, printed 27), "22 percentage points above" (KwaZulu-Natal neighbours gap in 2023, 21.47),
  New Zealand's neighbours gap "by five" in the text (−4.48; Chart 3.3 prints −4), Sindh's 17% (16.48) and
  upper-middle-income individual resilience among the impacted, 59 (58.497).
- **Istanbul** changed 0.6 points between 2023 and 2025 (49.6 to 50.2), printed as "level" (0).
- **Türkiye adjusted neighbours lower bound** in Table A.3 is −21.450 (published −21.4).
- **Approximate counts:** "more than 143,000" interviews (143,459), "about 14,000" respondents (14,022), "about 10,000"
  (10,008), and X06 above.
- **Shares of the affected respondents:** "two thirds" of Türkiye's are in the Mediterranean region (72.6% of
  respondents, 75.0% weighted), recorded as 67 with a tolerance of 6; "nine in ten" of New Zealand's are in Auckland
  (90.9%).

Not compared: figures the report quotes from other sources (deaths, people affected or displaced, damage estimates,
magnitudes and dates of the disasters, the number of officially affected provinces); months from each disaster to the
fieldwork (Tables 2.1 and 4.1, as the public files have no interview date); the approximate margins of error on page 49
(about nine percentage points at 132 respondents, and so on); and statements without a number, such as which regions
the disasters reached.

## Run

```
python reports/WRP_2025/core_after_the_storm/reproduce.py
Rscript reports/WRP_2025/core_after_the_storm/reproduce.R
```
