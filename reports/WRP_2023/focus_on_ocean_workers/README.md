# World Risk Poll 2024 Focus On: Risk perceptions and experiences of ocean workers

- **Report:** *World Risk Poll 2024 Focus On: Risk perceptions and experiences of ocean workers*, Lloyd's Register Foundation, June 2025 (doi:10.60743/xjn7-9x64)
- **PDF:** https://www.lrfoundation.org.uk/sites/default/files/2025-08/wrp-2024-focus-on-ocean-workers-updated.pdf
- **Data:** `WRP_2023/WRP_2023.parquet` (World Risk Poll 2023, wave 3; 146,910 respondents, 142 countries)

## What is reproduced

All 81 numbers the report publishes from the poll: every value in its nine poll charts, and
every number in the text, including the gap and the ratios between ocean workers and other
workers. Results are in [`RESULTS.md`](RESULTS.md).

The report's charts are not numbered. Here, `C1_<n>` are the four charts in "Climate change
and ocean workers" and `C2_<n>` are the five charts in "The cost of work at sea", in the order
they appear. The tropical cyclone chart on page 3 uses US EPA data, not the poll, so it is not
included. Pages are PDF pages. The page number printed on each page is one less.

## Method notes

- **Ocean workers:** the report does not say which survey answers define the group. The
  public release identifies them only through Job Sector (Coded), `WP23340` = 2 "Fishing"
  (478 respondents, whatever their current employment status). This group is used here.
  The report's group seems to be different, and probably broader. See "Findings that do not match".
- **Other workers:** the current workforce (`EMP_2010` 1 to 5: employed full or part time,
  self-employed or unemployed, but not out of the workforce) who are not ocean workers. This is
  the "current workforce" of the 2024 'Engineering safer workplaces' report. With this base,
  every "other workers" figure in the text and charts rounds to the published value. Other
  bases were tried. Currently working (`WP23336` = 4) gives 17.0% harmed at work against
  18%. Everyone who is not an ocean worker gives 72% and 18% against 74% and 20% for the
  climate threat and severe weather harm.
- **Chart 1.2 (climate change a threat):** the "all other workers" bar matches every
  respondent who is not an ocean worker (39%, 33%, 12%, 16%). Its segments add up to the
  global 72% quoted in the chart subtitle, not to the 74% for other workers in the text. The
  current workforce gives 40%, 34%, 10% and 16%.
- **Weights:** `PROJWT`, except in Chart 2.2 (see below).
- **Base:** everyone asked the question, with don't know and refused included. Work worry
  (`WP22214`) was asked only of those currently working (`WP23336` = 4). OSH training
  (`WP23337`) was asked of everyone who has worked. Telling someone (`WP23335`) was asked of
  those who experienced harm at work. Its "does not apply" answers stay in the base.
  Excluding them moves other workers from 50.9% to 51.8%.
- **Personally experienced harm** (`WP22445`, `WP22448`) is "yes, personally" or "both" (codes
  1 and 3), as in the 2024 'Engineering safer workplaces' report.
- **Greatest source of risk** (`WP22331`): climate change is code 19 ("Climate change or
  severe weather-related events"). Work-related accidents are code 17.
- **OSH training timing (Chart 2.4):** "last 2 years" means yes to `WP23337` and yes to
  `WP23338`. "More than 2 years ago" means yes to `WP23337` and no to `WP23338`.
- **Chart 2.2 (worry about work harm, by sector):** the values for the seven sectors other
  than ocean workers match **unweighted** shares among each sector's current workforce, all
  14 exactly. With `PROJWT`, electricity, gas or water supply would be 13% and 50%, not 13%
  and 34%. The ocean workers bar repeats the weighted figures in the text (26% very worried),
  so it uses `PROJWT`. X23 ranks the sectors on these chart values.
- **Chart 2.3 (harm from work, by sector):** `PROJWT`, among each sector's current workforce.
  The ocean workers bar uses all ocean workers, as elsewhere. The "global mean" is the whole
  current workforce. Chart 2.3 repeats Chart 2.10 of the 2024 'Engineering safer workplaces'
  report, with "Fishing 26%" replaced by "Ocean workers 25%".
- **Ratios (X06, X18):** 'almost triple' and 'three times higher' have a tolerance of 0.5.
  Ranks (X23, X27) have a tolerance of 0.

## Gallup World Poll data

None. Every variable used is in the public release.

## External data

None used. Statistics that the report quotes from other sources, not reproduced here:

- US EPA tropical cyclone indicators (page 3): an average of 6–7 North Atlantic hurricanes a
  year since 1878. 8 of the 10 most active years since 1950 came after the mid-1990s. Cyclone
  intensity has risen over the past 30 years (ACE index). The IPCC reports more intense
  cyclones over the past 40 years.
- The 72% and 6% global figures (page 3) are quoted from the 2024 'What the world worries
  about' report. They are poll figures, so they are reproduced (X01, X02).

## Findings that do not match

15 findings differ from the published values by more than the tolerance. All of them are
ocean worker figures.

The public "Fishing" group gives these values:

- Naming climate change as the greatest risk: 19% against 17% (X03, C1_1_ocean). The
  11-point gap with other workers is 14 points here (X04).
- Don't know and not a threat on climate change: 15% and 19% against 17% and 16% (C1_2).
- Worried about severe weather: 83% against 80% (X09). Somewhat worried: 33% against 31%
  (C1_3).
- Harmed by severe weather: 36% against 33% (X14, C1_4).
- Very worried about work: 25% against 26% (X21, C2_2).
- Ever trained in OSH: 28% against 32% (X28).
- Trained in the past two years: 19% against 25% (X30, C2_4).
- Rank for worry about work: third, behind mining and agriculture (56.1%, unweighted), not
  second (X23). This follows from the chart's ocean bar: 26% + 31% there, 25% + 31% here.

The other ocean worker figures match: 66% climate threat, 44% very serious, 49% very worried
about severe weather, 9% work accidents as the greatest risk, 56% worried about work, 25%
harmed at work, 7% trained more than two years ago and 41% told someone. So the report's
group is not the public "Fishing" group:

- The 2024 'Engineering safer workplaces' report publishes figures for Fishing (current
  workforce): 26% harmed at work, and 20% / 7% / 73% for OSH training. The public data
  reproduces them: 26.4% harmed, and 19.8% / 7.5% / 72.8% for training.
- The ocean workers report has 25% harmed and 25% / 7% for training instead.

The report calls ocean workers "those who work on or near the water". That probably
includes seafarers and other maritime workers. The public release cannot identify them,
because shipping and transport fall under Market services. Other versions of the Fishing
group do not match either:

- Only those in the current workforce (406 respondents) gives, for example, 20% for climate
  change as the greatest risk and 26% harmed at work.
- Only those currently working (`WP23336` = 4, 392 respondents) gives 22% and 27%.
- Weighting by `WGT`, or not weighting at all, is further off.

3 more findings are within tolerance but do not round to the published figure. All three are
ocean worker values: somewhat serious threat (22.1% against 23%), and very worried about
severe weather (49.9% against 49%, in the text and the chart).

## Run

```
python reports/WRP_2023/focus_on_ocean_workers/reproduce.py
Rscript reports/WRP_2023/focus_on_ocean_workers/reproduce.R
```
