# World Risk Poll 2021 Focus On: The impact of income and migration on violence and harassment at work

- **Report:** *World Risk Poll 2021 Focus On: The impact of income and migration on violence and harassment at work*, Lloyd's Register Foundation, April 2023
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2024-05/WRP_FocusOn_VH%20%281%29_1%20%282%29.pdf
- **Data:** `WRP_2021/WRP_2021.parquet` (World Risk Poll 2021, wave 2; 125,911 respondents, 121 countries)

## What is reproduced

All 210 numbers in the report: every value printed in Charts 1 to 10, and every number in
the text, including percentage-point gaps. Results are in [`RESULTS.md`](RESULTS.md).

The report's charts are numbered 1 to 10 without chapters, so chart values use
`C<chart>_<key>` (for example `C5_northern_america_foreign_difficult`). Page numbers are PDF
page numbers (the printed page number plus one).

Most of the report compares foreign-born and native-born workers. Country of birth is a
Gallup World Poll item that is not in the public data, so 184 of the 210 findings are
`GALLUP_ONLY` (see below). The 26 findings that run on the public data are Chart 1
(experience of violence and harassment by region), the regional and global figures in the
text, the global comparison by feelings about income (X23–X25), and the Convention 190
statement on page 13 (X77).

## Method notes

- **Workers (base):** everyone who has ever worked, that is, everyone who did not answer
  "respondent has never worked" (code 7) at any of the three violence and harassment
  questions (`WP22400_ALL`, `WP22403_ALL`, `WP22406_ALL`). This is the Risk and Gender
  report's definition, with one difference: it **includes China**, where the physical
  violence question was not asked but the other two were. Including China reproduces East
  Asia in Chart 1 (22.7%, published 23%); without it East Asia is 18.2%.
- **Experienced violence and harassment:** yes to at least one of the three forms. Don't
  know and refused count as no.
- **Country of birth (footnote 4):** foreign/native-born splits use workers who gave their
  country of birth (`WP4657` = 1 born in this country, 2 born in another country).
- **Feelings about income (footnote 5):** `IncomeFeelings`. "Comfortable" is living
  comfortably or getting by (1, 2); "difficult" is finding it difficult or very difficult
  (3, 4). Don't know and refused are left out of these splits.
- **Told someone (Charts 3, 6, 7, 9):** `WP22409` among workers who experienced violence and
  harassment, with don't know and refused in the base (Chart 3 shows a small don't know
  segment).
- **Reasons for not telling anyone (Charts 4, 8, page 12):** `WP22416` did not know what to
  do, `WP22417` procedures were unclear, `WP22420` fear for reputation, `WP22415` waste of
  time, `WP22419` fear of punishment. These were asked of those who did not tell anyone.
- **Number of forms (Chart 10):** count of yes answers to the three forms; "no experience"
  is zero.
- **Chart 2** prints only the size of the gap between foreign-born and native-born workers,
  without a sign (the label colour shows which group is higher). The function returns the
  absolute gap; each row's note gives the direction. North Africa is printed as "-" and is
  not recorded; the function still computes it.
- **Page 12:** "their native-born counterparts at 47%" is read as native-born men in Latin
  America and the Caribbean.
- **X77 ("over a third"):** the share of the region's 2021 Poll countries that the report's
  own Convention 190 table (page 13) marks as ratified, in force or not yet in force. It is
  7 of 18 (Argentina, Ecuador, Uruguay, El Salvador, Mexico, Panama, Peru). The statement
  names only the last four.
- **Weights:** `PROJWT`. Chart 1 matches under `PROJWT`, but not under `WGT` (Latin America
  20%, East Asia 19%).
- **Gaps** in the text are computed from unrounded values.

## Gallup World Poll data

Every foreign-born versus native-born finding (184 findings, including all of Charts 2–10)
needs the Gallup World Poll item "Were you born in this country?" (`WP4657` in the code:
1 = born in this country, 2 = born in another country). That item is not in the public
release, and must be licensed from Gallup directly. The code is included; without the data
these findings are reported as `GALLUP_ONLY`. See
[`reports/README.md`](../../README.md#gallup-world-poll-data).

The code path was tested with a synthetic `WP4657` file (random codes). Python and R ran
every finding and agreed to 1e-12. The results are meaningless, so they are not included.

Two things to check if you run these findings with the Gallup data:

- **X12, X13 (global told someone):** the report gives 56% for native-born and 53% for
  foreign-born workers. In the public data, 51.8% of all workers who experienced violence
  and harassment told someone (`PROJWT`), which is below both. Two subgroups cannot both be
  above their combined figure, so the published global figures probably use a different
  base or weight. With `WGT` the combined figure is 56.4%.
- **Footnote 4:** the published figures exclude workers who did not give a country of
  birth. The findings that run on the public data (Chart 1, X23–X25, X37, X57) cannot apply
  that filter. The effect should be small unless many workers did not answer it.

## Figures quoted from other sources

These are not from the poll and are not reproduced: the ILO Violence and Harassment
Convention (C190) and Recommendation (R206), and C190 entering into force in Canada in
January 2024; World Bank Gini index rankings (United States 110th of 167, Canada 47th,
Australia 65th, United Kingdom 48th; Belgium, the Netherlands and Iceland in the top 10;
Finland, Denmark and Norway in the top 20); Pew Research Center (50% of US migrants in 2018
born in Mexico or elsewhere in Latin America); 10% of migrants in Canada and Australia, and
8% in New Zealand, born in China; Brazil's 2022 immigration figures (eight of the top 10
countries of origin in Latin America, the United States fourth, China seventh, Venezuela
nearly 20%). The Convention 190 ratification status used in X77 is typed from the report's
own table on page 13.

## Findings that do not match

1 finding differs from the published value by more than the ±1-point tolerance:

- **X01 (sidebar, page 2):** "22% of workers have experienced violence and harassment at
  work. This rises to 28% for those working outside their country of birth." All workers
  give 20.9%. The sidebar's two figures are the same as the native-born (22%) and
  foreign-born (28%) figures on page 4, so "workers" probably means native-born workers.
  Tried: `WGT` (21.5%), currently employed only (22.6%), don't know excluded (20.2%).

2 more findings are within tolerance but do not round to the published figure: X24 (workers
finding it difficult on their income, 23.5% against 23%), and X77 ("over a third": 38.9%).

## Run

```
Rscript reports/WRP_2021/focus_on_violence_and_harassment_income_migration/reproduce.R
python reports/WRP_2021/focus_on_violence_and_harassment_income_migration/reproduce.py
```

With the Gallup item:

```
GALLUP_WP_PATH=/path/to/gallup_items.parquet python reports/WRP_2021/focus_on_violence_and_harassment_income_migration/reproduce.py
```
