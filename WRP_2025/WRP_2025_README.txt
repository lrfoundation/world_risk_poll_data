World Risk Poll 2025 - harmonised single-wave file
============================================================

Built 2026-08-31 by build_wrp_waves.py from the supplied SPSS files.

Cases:     143,459
Variables: 228 (37 harmonised, 191 wave-specific)

Files
-----
WRP_2025.sav                    SPSS, with variable and value labels
WRP_2025.parquet                Apache Parquet, same content
WRP_2025.csv                    CSV of numeric codes, UTF-8 with BOM
WRP_2025_data_dictionary.csv    One row per variable: label, codes, coverage, derivation

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
- Source: LRF_WAVE4_WITH_INDICES_FOR_PUBLIC_RELEASE.sav (143,459 cases), unchanged apart from the harmonised block.
- LRF published no experience index for 2025. experience_score and experience_score_core7 fill that gap.
- The published worry_index for 2025 covers ten items and is a simple mean, so it is not comparable with the wave 1-3 published indices.
- Resilience in the source file is on a 0-100 scale; resilience_index here is 0-1, resilience_index_100 is 0-100.

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

