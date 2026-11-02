# World Risk Poll 2026: From alert to agency: What turns warnings into action?

- **Report:** *From alert to agency: What turns warnings into action?*, World Risk Poll 2026 report, Lloyd's Register Foundation, October 2026 (doi:10.60743/yx1k-t541)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2026-10/world-risk-poll-report-2026-early-warnings.pdf
- **Data:** `WRP_2025/WRP_2025.parquet` (World Risk Poll 2025, wave 4; 143,459 respondents, 140 countries), with
  `WRP_2023` for the 2023 comparisons

## What is reproduced

All 232 numbers in the report: every value in Charts 1.1 to 3.6 and every number in the text,
including counts of countries, the countries named as highest and lowest, and the point differences
printed on Charts 3.4 and 3.5. Page numbers are the report's printed page numbers (PDF page = printed
page + 6 in the chapters; roman numerals for the front matter). Results are in
[`RESULTS.md`](RESULTS.md).

Two charts have no printed values, so their values come from the text:

- **Chart 2.4** (scatter of warning coverage against % impacted in the Early Warnings for All
  priority countries): the text gives coverage for seven of the 13 countries (`C2_4_warned_*`). The
  function also writes coverage and % impacted for all 13 to `output/`.
- **Chart 3.3** (bubbles of % warned against % able to act, by disaster type): the text gives the
  share able to act for five types (`C3_3_*`). Its horizontal axis is Chart 2.5.

Chart 1.5 is a map; the 13 countries it labels are compared and every other country's value is
written to `output/`.

## Method notes

- **Impacted (Chapter 1):** `WP24213` = yes, among all respondents (don't know and refused in the
  base). Disaster type is `WP24180` among those impacted; Chart 1.2 combines don't know and refused
  (6%).
- **Warned (Chapter 2):** the eight channel questions (`WP24181` to `WP24188`) were asked of everyone
  impacted whose most impactful disaster has a type, that is, not don't know or refused. "Received at
  least one warning" is yes to any channel, among those asked; don't know counts as no. With everyone
  impacted in the base, coverage is 75.4% (published 80). The number of warnings is the count of
  channels answered yes.
- **Able to act (Chapter 3):** `WP24215` = yes, among those warned (everyone warned was asked), with
  don't know in the base. Chart 3.4 compares those who answered yes with those who answered no.
- **Index:** the released `resilience_index_100` and `resilience_idv`, `resilience_hhl`,
  `resilience_com` and `resilience_soc` (times 100). The index is not recomputed.
- **Plan and agency (Chart 3.6):** agency is `WP22252` yes against no, and the plan is `WP23345` yes
  against no; "it depends", don't know and refused are left out. If they are counted as no agency or
  no plan, "plan, no agency" is 50.6% (published 50) and the other three are unchanged.
- **2023 comparisons (X03 to X05)** use all countries surveyed in 2023, unlike the trends in *A
  resilient life*. With only the countries surveyed in 2025, tropical storms are 20% and earthquakes
  15% (published 19 and 16), and warning coverage is 71% (published 70). The 2023 coverage is yes to
  any of the four sources (`WP22248` to `WP22251`) among those asked.
- **Sufficient data:** country figures (X09) and the Early Warnings for All countries (X10, Chart 2.4)
  need at least 100 respondents asked about warnings. This leaves out Morocco (95), Georgia (99) and
  South Korea (69), and gives Vietnam, Hong Kong and China as the three highest and the Republic of
  the Congo and Gabon as the two lowest.
- **Early Warnings for All countries:** the scripts list the 30 initial priority countries announced
  in 2023. Sixteen were surveyed in 2025; the 13 with at least 100 respondents asked are the 13 in
  Chart 2.4 (Ecuador, Ethiopia and Liberia have fewer). "At least two-thirds" (X10) is on the unrounded
  percentages: Madagascar is 65.1%.
- **Unwarned and mobile phones (Chart 2.9, X15 to X17):** the unwarned are those asked about warnings
  who said yes to no channel. Chart 2.9 leaves out regions with fewer than 100 unwarned respondents:
  Northern America (65), Eastern Asia (89) and Australia and New Zealand (93). X16 counts the regions
  at 90% or more after rounding, across all 15 regions. X15 is the sum of `PROJWT`, the projection
  weight, in millions.
- **Changes are differences of the rounded figures.** The gaps on Chart 3.4 and the increments on
  Chart 3.5 are differences of the two printed values. Rounding is half up.
- **"<1%":** Chart 1.2 (sandstorms, tsunamis) and the text on Israel print "<1%" for a value that
  rounds to 0. The scripts write `<1` in that case (Israel is 0.499%).
- **Readings of the text:**
  - "Only half" (drought) and "around half" (sandstorms) of those warned were able to act (C3_3) are
    recorded as 50 with a tolerance of 3. The data give 52.5% and 47.4%.
  - "Scoring 33 compared with 32 among those not impacted" (X12) is individual resilience in
    low-income countries by whether the respondent was impacted by a disaster. The conclusion calls it
    a sense of personal agency.

## Gallup World Poll data

21 findings need Gallup World Poll items that are not in the public release. The code is included;
without the data these findings are reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item (name used in the code) | What it is | Findings |
| --- | --- | --- |
| `WP17626` | Has a mobile phone (1 = yes) | Chart 2.9, X13, X15, X16, X17 |
| `WP16056` | Access to the internet (1 = yes) | X14 |

`WP16056` and `WP17626` are the item codes used in the 2021 report's folder
([`core_a_resilient_world`](../../WRP_2021/core_a_resilient_world/README.md)); check them with Gallup.
The public data has no mobile phone item.

The Gallup code paths were tested with a synthetic file of random values (not committed): Python
and R give the same results.

## Findings that do not match

No finding differs from the published value by more than its tolerance. Three are within tolerance
but do not round to the published figure: X01, 143,459 interviews, "more than 143,000", and the two
"half" readings in C3_3 above.

Figures the report quotes from other sources are context and are not reproduced: 41,000 deaths a year
from disasters (page 2), the UNDRR figures on economic losses (0.28% of global GDP, 13% and 1.5%,
page 4), the Early Warnings for All target of 2027 (page 8), and Lloyd's Register Foundation's £4.5
million committed to projects (page 26). The number of channels asked about (eight in 2025, four in
2023, page 13) describes the questionnaire. Statements without a number, such as internet warnings
skewing towards storms and SMS outranking WhatsApp "across all hazard types" (page 13), are not
compared.

## Run

```
python reports/WRP_2025/core_from_alert_to_agency/reproduce.py
Rscript reports/WRP_2025/core_from_alert_to_agency/reproduce.R
```
