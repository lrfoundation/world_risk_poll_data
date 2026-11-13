# How the wave files are built

`build_wrp_waves.py` is the script that made the four harmonised wave files in
this repository (`WRP_2019/` to `WRP_2025/`) from the SPSS files the Foundation
holds for each wave. It is the script that built the current release on
31 August 2026, unchanged: each wave's `_README.txt` says "Built 2026-08-31 by
build_wrp_waves.py", and the script writes those four READMEs word for word.

It is here so that anyone can see exactly how each variable in the harmonised
block is derived. [`docs/CODEBOOK.md`](../docs/CODEBOOK.md) describes the block;
this is the code behind it. You cannot run it from this repository alone,
because the source files it reads are not published here.

## What it reads

Six SPSS files, which must sit in the same folder as the script:

| File | What the script takes from it |
| --- | --- |
| `19_wrp.sav` | 2019 (Wave 1): the respondents and the published wave 1 indices |
| `21_wrp.sav` | 2021 (Wave 2): the respondents. It also holds the 2019 rows, which are dropped |
| `LRF_WAVE_3_WITH_INDICES_FOR_PUBLIC_RELEASE_10082024_v2.sav` | 2023 (Wave 3): the respondents |
| `LRF_WAVE4_WITH_INDICES_FOR_PUBLIC_RELEASE.sav` | 2025 (Wave 4): the respondents, and part of the country code lookup |
| `trend_wrp_21_OLD.sav` | The 2019 and 2021 trend file. For 2019: age, the Gallup country code (WP5) and the projection weight. For 2021: the published worry and experience indices, and the resilience index for the cases `trended_wrp.sav` lacks |
| `trended_wrp.sav` | The 2019 to 2023 trend file. The rest of the country code lookup, and for 2021 the six-category urban/rural variable and the resilience index and its four dimensions, recomputed to match wave 3 |

The file names are set near the top of the script (`F_W1` to `F_TREND3`). If a
corrected file arrives under a new name, change the name there, or give the new
file the old name.

## What it writes

An `output/` folder next to the script, holding one folder per wave with the
same files as this repository's wave folders, plus a zip of each:

```
output/WRP_<year>/WRP_<year>.sav
output/WRP_<year>/WRP_<year>.parquet
output/WRP_<year>/WRP_<year>.csv
output/WRP_<year>/WRP_<year>_data_dictionary.csv
output/WRP_<year>/WRP_<year>_README.txt
output/WRP_<year>.zip
```

`WRP_2025/RELEASE_NOTES.md` is written by hand, not by the script.

**Each run deletes the whole `output/` folder before it starts.** Move anything
you want to keep out of it first.

## Running it

It was last run with Python 3.12 on Windows. It needs numpy, pandas, pyreadstat,
and pyarrow (pandas uses pyarrow to write the Parquet files):

```
pip install numpy pandas pyreadstat pyarrow
python build_wrp_waves.py
```

It looks for the source files next to itself, not in the folder you run it
from, so put a copy of the script in the folder that holds the six files. It
prints one line per wave and then "Done". The four waves should come out as:

| Wave | Cases | Variables |
| --- | --- | --- |
| 2019 | 154,195 | 245 (37 harmonised, 208 wave-specific) |
| 2021 | 125,911 | 270 (37 harmonised, 233 wave-specific) |
| 2023 | 146,910 | 325 (37 harmonised, 288 wave-specific) |
| 2025 | 143,459 | 228 (37 harmonised, 191 wave-specific) |

## Checking a rebuild

With the same source files, each new `_data_dictionary.csv` should match the one
in this repository exactly: it holds every variable's label, codes, valid and
missing counts, minimum, maximum and mean, and no build date. The `_README.txt`
files should differ only in the "Built" date. The `.sav`, `.parquet` and `.csv`
files may differ byte for byte under newer library versions even when the data
is the same, so compare those through the data dictionary rather than by size.

If you change the script, rebuild all four waves and commit the new files and
the script together, so that the script here always matches the data here.
