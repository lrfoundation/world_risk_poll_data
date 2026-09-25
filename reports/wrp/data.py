"""Loading the public World Risk Poll wave files and their data dictionaries."""

from functools import lru_cache
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

# Fieldwork year -> wave number. Report folders are named after the
# fieldwork year (WRP_2023), even where the reports were branded with the
# publication year (the "World Risk Poll 2024" reports use 2023 data).
WAVES = {2019: 1, 2021: 2, 2023: 3, 2025: 4}

# The 37-variable harmonised block (docs/CODEBOOK.md): same names, codes
# and labels in every wave, so these stack directly across waves.
HARMONISED_COLS = [
    "WPID_RANDOM", "Wave", "Year", "WP5", "Country", "COUNTRY_ISO2",
    "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "WGT", "PROJWT",
    "Age", "AgeGroups3", "AgeGroups4", "AgeGroups5", "Gender", "Education",
    "Urbanicity", "Urbanicity2", "EMP_2010", "INCOME_5", "HouseholdSize",
    "ChildrenInHousehold", "worry_score", "worry_score_core7",
    "worry_index_published", "experience_score", "experience_score_self",
    "experience_score_core7", "experience_index_published", "worry_exp_gap",
    "resilience_index", "resilience_index_100", "resilience_idv",
    "resilience_hhl", "resilience_com", "resilience_soc",
]


def data_path(year, fmt="parquet"):
    """Path to a wave file, e.g. data_path(2021) -> WRP_2021/WRP_2021.parquet."""
    if year not in WAVES:
        raise ValueError(f"No World Risk Poll wave for {year}; choose from {list(WAVES)}")
    return REPO_ROOT / f"WRP_{year}" / f"WRP_{year}.{fmt}"


def load_wave(year, columns=None):
    """Load one wave from its Parquet file, optionally only some columns.

    Coded columns come back as float64 with NaN where the question was not
    asked (rather than pandas' nullable Int64), so comparisons such as
    df.Q.eq(1) give plain True/False, as they do in R.
    """
    df = pd.read_parquet(data_path(year), columns=columns)
    nullable = [c for c, t in df.dtypes.items() if isinstance(t, pd.Int64Dtype)]
    return df.astype({c: "float64" for c in nullable})


def stack_waves(years, columns=None):
    """Stack several waves on the harmonised block (or a subset of it)."""
    columns = columns or HARMONISED_COLS
    return pd.concat([load_wave(y, columns) for y in years], ignore_index=True)


@lru_cache(maxsize=None)
def dictionary(year):
    """The wave's data dictionary: one row per variable."""
    path = REPO_ROOT / f"WRP_{year}" / f"WRP_{year}_data_dictionary.csv"
    return pd.read_csv(path, encoding="utf-8-sig")


def value_labels(year, variable):
    """Code -> label mapping for a categorical variable, from the dictionary.

    The dictionary stores labels as "1 = Very worried | 2 = Somewhat worried".
    """
    dd = dictionary(year)
    row = dd.loc[dd["variable"] == variable]
    if row.empty:
        raise KeyError(f"{variable} is not in the {year} data dictionary")
    raw = row["value_labels"].iloc[0]
    labels = {}
    if isinstance(raw, str):
        for part in raw.split(" | "):
            code, _, label = part.partition(" = ")
            labels[int(float(code))] = label
    return labels


def variable_label(year, variable):
    """The question wording / label of a variable, from the dictionary."""
    dd = dictionary(year)
    return dd.loc[dd["variable"] == variable, "label"].iloc[0]


def countries_in_all(years):
    """ISO3 codes of countries surveyed in every one of `years`.

    Use this for like-for-like trends: otherwise part of any change is a
    change in which countries were surveyed.
    """
    sets = [set(load_wave(y, ["COUNTRY_ISO3"])["COUNTRY_ISO3"]) for y in years]
    return sorted(set.intersection(*sets))
