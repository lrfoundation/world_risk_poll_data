# World Risk Poll 2026: From alert to agency: What turns warnings into action?

- **Report:** *From alert to agency: What turns warnings into action?*, World Risk Poll 2026 report, Lloyd's
  Register Foundation (https://doi.org/10.60743/yx1k-t541). **Not yet published:** the report is due to launch,
  and no launch date has been given.
- **PDF:** https://doi.org/10.60743/yx1k-t541 (the DOI resolves once the report is launched)
- **Data:** `WRP_2025/WRP_2025.parquet` (World Risk Poll 2025, wave 4; 143,459 respondents, 140 countries),
  with `WRP_2023` for the comparisons with 2023

## What is reproduced

All 539 numbers in the report: every value printed in Charts 1.1 to 1.6, 2.1 to 2.3, 2.5 to 2.9 and 3.1 to
3.6 and in the chapter graphics, and every number in the text. This includes point gaps, ratios given in words
("twice", "almost half that rate"), counts of countries and regions, and shares given in words ("four in
five", "more than half"). Page numbers are the report's printed page numbers (PDF page minus 6 in the
chapters, roman numerals for the foreword and executive summary). Results are in [`RESULTS.md`](RESULTS.md).

Some charts print no values, or only some:

- **Chart 1.5** is a map that labels 13 countries; those 13 are compared. `C1_5` writes every country's value
  to `output/`. The colour scale's end labels (1% and 80%) are not entered.
- **Chart 2.4** plots coverage against impact for the 13 Early Warnings for All countries and prints no
  values. `C2_4` writes both values for each country to `output/`. The text beside it quotes seven of them,
  and those are compared.
- **Chart 3.3** plots coverage against the ability to act by disaster type and prints no values. `C3_3`
  writes both values for the 13 types it shows to `output/`. The text quotes several of them, and those are
  compared.
- **Chart 2.9** leaves out the three regions with fewer than 100 unwarned respondents (Northern America,
  Eastern Asia, Australia and New Zealand). `C2_9` also writes them to `output/`.

## Method notes

- **Questions** (2025): impacted by a disaster in the past five years (`WP24213`), type of the most impactful
  disaster (`WP24180`), warned through each of eight channels (`WP24181` to `WP24188`), able to take action
  because of the warning (`WP24215`), could protect yourself or your family in a future disaster (`WP22252`,
  the report's "agency"), and a household disaster plan known to everyone over 10 (`WP23345`). All use 1 = yes.
- **Weights and base:** `PROJWT`. Everyone asked a question is in its base, with don't know and refused.
  Impact is a share of all adults (1.3% answered don't know or refused). The disaster type is a share of the
  25,244 impacted adults; don't know and refused together are the chart's "Don't know/Refused".
- **Warnings:** the channel questions were asked of the 24,249 impacted adults who named a disaster type
  (the 995 who did not name one were not asked). This is the base for coverage, the channels and the number of
  warnings. "At least one warning" is yes to any channel. Don't know, refused and "does not apply" count as
  no. Counting the 995 as unwarned gives 75% globally instead of 80%, and 62% and 67% in low- and
  lower-middle-income countries instead of 64% and 77%. Leaving out the 100 respondents with no yes or no
  answer to any channel gives 80.3% globally, but moves six other values off the published ones (for example
  78% for lower-middle-income countries, published 77%, and 95% for tropical storms, published 94%).
- **Ability to act:** asked of the 16,996 warned respondents. "Not able" is the answer no (code 2), so the
  able and not-able shares leave 0.5% who answered don't know or refused.
- **Resilience (Charts 2.8, 3.4):** the released `resilience_*` scores x 100. Chart 2.8 uses the 24,249 asked
  about warnings, by number of channels (0 = no warning). Chart 3.4 compares the warned who could act with
  those who could not.
- **Plan and agency (Chart 3.6):** among the warned who answered yes or no to both questions. "It depends",
  don't know and refused are left out. Counting them as no gives 50.6% for "plan, no agency" (published 50).
- **Gaps are differences of rounded values** in this report: the gaps in Chart 3.4 and the gains in Chart
  3.5, and the same figures in the text. The societal gap is 67 − 64 = 3 (unrounded 3.8), and the gain from a
  second warning is 51 − 37 = 14 (unrounded 13.1). "Four to eight points" are the smallest and largest of the
  rounded gains after three channels (5, 4 and 8).
- **Countries with "sufficient data":** at least 100 respondents asked about warnings. This reproduces the
  page 11 rankings. Albania, Kosovo, Morocco and Georgia have lower coverage than Congo and Gabon, but only
  51, 39, 95 and 99 respondents. Israel (100% of 5) and South Korea (97% of 69) would otherwise top the list.
  A threshold of 100 *impacted* respondents would include Georgia (101 impacted, 22.8% warned), which would
  then be the lowest.
- **Early Warnings for All (EW4A):** 17 of the UN initiative's initial priority countries were surveyed in
  2025 (the list is the one in the 2023 report, `WRP_2023/core_resilience_in_a_changing_world`). Ethiopia (93
  respondents), Ecuador (79), Liberia (69) and Tajikistan (66) have too few, which leaves the 13 in Chart 2.4.
  "At least two-thirds" is 66.7% or more.
- **Chart 2.9:** a region is shown if it has at least 100 unwarned respondents, as the chart's note says.
- **The Philippines (page 7, Chart 1.6):** shares of the impacted adults naming each type, by `REGION2_PHL`.
  The text says "52% of all adults", but 52%, 19% and 16% are shares of the impacted; as shares of all adults
  they are 41%, 15% and 13%.
- **2023 comparisons:** experienced a disaster (`WP23344`) among all adults; the type (`WP22247`) among those
  who experienced one; and at least one warning from the four 2023 sources (`WP22248` to `WP22251`), defined
  as in the 2023 report (respondents with no yes or no answer to any source are left out).
- **Low-income countries, impacted vs not impacted (page 27):** individual resilience among those who
  answered yes (33) and no (32) to `WP24213`.
- **Mean number of warnings by phone and internet (page 23):** among the 24,249 asked, including the unwarned.
  The overall mean is 3.0. Among the warned only it is 3.7, and two group means of 3.1 and 2.2 cannot average
  to 3.7.
- **"More than 170 million":** the sum of `PROJWT` among unwarned respondents who own a mobile phone. The
  weights sum to 5.8 billion adults, and to 222 million unwarned adults.
- **Words compared as numbers:** "more than 143,000" (tolerance 1,000); "twice" as a ratio of 2 (0.3) and
  "almost half that rate" as 0.5 (0.1); "less than two thirds" as 67 (3); "a slim majority" as 50 (5); "more
  than nine in 10" as 90 (2); "around half" and "only half" as 50 (3); "around seven in 10" as 70 (2); "more
  than half" as 50 (10); "fewer than one in five" as 20 (6); "<1%" and "fewer than 1%" as 0 (the values
  round to 0). The Gallup-only findings use "more than two thirds" as 67 (12), "roughly two-thirds" as 67 (5),
  "roughly four in five" as 80 (3) and "more than 170 million" as 170 (10).
- **Rankings:** X102 and X104 compare the countries named as highest and lowest (in alphabetical order of
  ISO3 code, as a text value).

## Gallup World Poll data

37 findings need Gallup World Poll items that are not in the public release. The code is included; without
the data these findings are reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

| Item | Question | Findings |
| --- | --- | --- |
| `WP17626` | Has a mobile phone ("Do you have a mobile phone that you use to make and receive PERSONAL calls?"); 1 = yes | 35: Chart 2.9, X008, X009, X055 to X057, X132 to X138, X177, X187, X203 to X205 |
| `WP16056` | Access to the internet; 1 = yes | 2: X178 (mean warnings with and without internet access) |

The codes are the ones the World Risk Poll 2024 Resilience Index appendix gives for "Cellphone Access" and
"Internet Access", and that `WRP_2021/core_a_resilient_world` uses. Check them with Gallup. (The
`WRP_2023/core_resilience_in_a_changing_world` scripts use a placeholder, `GWP_MOBILE_PHONE`, for a different
three-category question on phones with internet access.) The Gallup code was tested in Python and R with a
synthetic file of random values (not committed); both gave the same results.

## External data

None. The report uses no external index: the word "inform" appears only in "information", "informing",
"informed" and "informal", and there is no INFORM Risk Index. The World Bank income groups are in the data
(`CountryIncomeLevel`). Figures the report quotes from other sources are context and are not reproduced:

- UNDRR: disasters caused an estimated 41,000 deaths a year over the past decade; direct economic losses were
  0.28% of global GDP; the least developed countries had nearly 13% of losses with less than 1.5% of GDP (a
  "more than eight-fold" disproportion).
- Hurricane Katrina (2005); the Early Warnings for All target of universal coverage by the end of 2027; the
  Protective Action Decision Model's three processes; the Trishuli river flood of August 2026.
- Lloyd's Register Foundation's £4.5 million for projects; indigenous people are close to half of Bolivia's
  population.

Not entered as findings: "three is the magic number" and the other statements that three channels are the
threshold (Charts 2.8 and 3.5 are compared); descriptions of the Poll ("every two years", "fourth edition",
"one of three reports"); "three key levers"; the question wording ("over the age of 10"); and the map
legend and axis labels.

## Findings that do not match

No finding differs from its published value by more than its tolerance.

17 findings are within tolerance but do not round to the published figure. All are numbers given in words
(see Method notes): X001 and X010 (143,459 for "more than 143,000"), X006 (64.3% for "less than two
thirds"), X007 (52.0% for "a slim majority"), X039, X152 and X159_sandstorm_warned (91.6% for "more than
nine in 10"), X040, X153 and X159_sandstorm_act (47.4% for "around half"), X054, X110, X113 and X207 (58.0%
for "more than half"), X111 (14.1% for "fewer than one in five"), X157 (71.0% for "around seven in 10") and
X158 (52.5% for "only half").

Within the report (the report is not yet published, so these may still be corrected):

- **Page iv and page 27:** low-income countries have "the lowest ability to act" and are "least likely to be
  able to act on a warning ..., at 48%". Lower-middle-income countries are lower (47%; 46.9 against 48.0), as
  the report's own figures on the same pages show.
- **Page 21:** earthquakes "roughly three in four (73%) were able to act, a similar proportion to those
  impacted by floods". For floods it is 59%, as the previous sentence says.
- **Page 16:** "roughly two-thirds" of the unwarned in Southern Asia and Eastern Africa own a phone. Chart 2.9
  prints 58% and 63%.
- **Page 7:** "52% of all adults" is a share of the impacted (see Method notes).
- **Chart 3.3** leaves out tornadoes (77% warned and 77% able to act, 144 respondents), which Chart 2.5 shows.
  Tsunamis (97% of 13 respondents) and "other, not nature related" events are in neither chart.
- **Chart 2.8's** title says "(% among those impacted by a disaster)", but it plots individual resilience
  scores.
- **Drafting:** "As shown in Chapter 1 of *******" (page 4) and "Acknowledgements******" (page ii) have
  placeholder asterisks; page 26 refers to findings "reported in Chapter 5" (the report has three chapters);
  "94%vs.t 76%" and "raises the change a message is received" (page iv).

## Run

```
Rscript reports/WRP_2025/core_early_warnings/reproduce.R
python reports/WRP_2025/core_early_warnings/reproduce.py
```
