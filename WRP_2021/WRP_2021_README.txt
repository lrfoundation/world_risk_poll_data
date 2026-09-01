World Risk Poll 2021 - harmonised single-wave file
============================================================

Built 2026-08-31 by build_wrp_waves.py from the supplied SPSS files.

Cases:     125,911
Variables: 270 (37 harmonised, 233 wave-specific)

Files
-----
WRP_2021.sav                    SPSS, with variable and value labels
WRP_2021.parquet                Apache Parquet, same content
WRP_2021.csv                    CSV of numeric codes, UTF-8 with BOM
WRP_2021_data_dictionary.csv    One row per variable: label, codes, coverage, derivation

The three data files hold identical content. The CSV stores numeric codes,
not labels; the data dictionary gives the code-to-label mapping for every
categorical variable in its value_labels column.

Structure
---------
The first 37 variables are the harmonised block. They carry the same names,
codes and labels in all four wave files, so the waves stack directly.
Everything after that is this wave's own questionnaire content, unchanged
from the source file.

Notes for this wave
-------------------
- Source: the 2021 rows of 21_wrp.sav (125,911 cases), with the published wave 2 worry and experience indices merged from trend_wrp_21_OLD.sav and resilience from trended_wrp.sav.
- 21_wrp.sav also holds the 2019 rows; they are excluded here and are in the 2019 file instead.
- Urbanicity (6-category) and the four resilience dimensions are missing for the 505 Jamaica cases, which are absent from trended_wrp.sav. Urbanicity2 and resilience_index cover them.
- HouseholdSize is the total number of people in the household.

Cross-wave comparability
------------------------
- worry_score and experience_score use the five risk sources asked in
  identical form in every wave, so they trend across all four waves.
- worry_score_core7 and experience_score_core7 add traffic accidents and
  work, and so cover 2021 to 2025 only.
- worry_index_published and experience_index_published are the figures LRF
  published for each wave. They are not comparable between waves: the item
  sets change and wave 4 switched from a Rasch-weighted, min-max scaled
  index to a simple mean. Quote them for single-wave figures, use the
  computed scores for trends.
- experience_score counts harm to the respondent or to someone they know.
  2019 asked about the respondent only, so its wording is not identical,
  but this is the definition LRF itself uses to trend the series and the
  one that produces a coherent trend. experience_score_self holds the
  strictly personal definition, which is comparable 2021 to 2025.
- Resilience was first measured in 2021, so the 2019 file has none.
- Country coverage differs by wave: 142 countries and areas in 2019, 121
  in 2021, 142 in 2023 and 140 in 2025. For a global trend, restrict to
  the countries present in every wave you are comparing, otherwise part
  of the change you see is a change in the sample of countries.

