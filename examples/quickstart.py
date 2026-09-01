"""
Quickstart: load one World Risk Poll wave, then stack all four waves into
a trend file using the harmonised block described in docs/CODEBOOK.md.

Requires: pandas, pyarrow
    pip install pandas pyarrow

Run from the repository root:
    python examples/quickstart.py
"""

import pandas as pd

WAVES = ["WRP_2019", "WRP_2021", "WRP_2023", "WRP_2025"]


def weighted_mean(df, value, weight):
    """Weighted mean of `value`, over the rows where `value` is present."""
    d = df.dropna(subset=[value])
    return (d[value] * d[weight]).sum() / d[weight].sum()


# --- Load a single wave -----------------------------------------------

wave = pd.read_parquet("WRP_2025/WRP_2025.parquet")
print(f"{len(wave):,} respondents, {wave.shape[1]} variables")

# Within-country weighted average worry score for this wave.
print(f"2025 worry_score (WGT-weighted): {weighted_mean(wave, 'worry_score', 'WGT'):.3f}")

# --- Stack all four waves for a trend -----------------------------------
# Only the first 37 columns (the harmonised block) carry matching names,
# codes and labels across waves -- that's what makes concatenation valid.
# See docs/CODEBOOK.md for what each one means and which waves it covers.

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

trend = pd.concat(
    [pd.read_parquet(f"{w}/{w}.parquet", columns=HARMONISED_COLS) for w in WAVES],
    ignore_index=True,
)
print(f"\nPooled trend file: {len(trend):,} respondents across {len(WAVES)} waves")

# Global worry_score by year, weighted by PROJWT (a population weight,
# appropriate here because the trend is pooled across countries -- use
# WGT instead for a within-country-only comparison).
by_year = trend.groupby("Year").apply(
    lambda g: weighted_mean(g, "worry_score", "PROJWT"), include_groups=False
)
print("\nGlobal worry_score by year (PROJWT-weighted):")
print(by_year.round(3))

# --- A wave-specific question, trended by hand -------------------------
# "Climate change is a threat to [country] in the next 20 years" is asked
# in every wave, but it sits OUTSIDE the harmonised block and its variable
# name changes: L5 in 2019, WP20719 from 2021 on. Codes: 1 = very serious
# threat, 2 = somewhat serious, 3 = not a threat; 98/99 are DK/refused.
# This is the general recipe for any comparable question that isn't
# pre-harmonised: map the per-wave name, keep the substantive codes, then
# concatenate.

CLIMATE_VAR = {
    "WRP_2019": "L5",
    "WRP_2021": "WP20719",
    "WRP_2023": "WP20719",
    "WRP_2025": "WP20719",
}

climate = pd.concat(
    [
        pd.read_parquet(f"{w}/{w}.parquet", columns=["Year", "PROJWT", var])
        .rename(columns={var: "climate_threat"})
        .query("climate_threat in [1, 2, 3]")
        for w, var in CLIMATE_VAR.items()
    ],
    ignore_index=True,
)
# "serious" = very serious (1) or somewhat serious (2).
climate["serious"] = climate["climate_threat"].isin([1, 2]).astype(float)

pct_serious = 100 * climate.groupby("Year").apply(
    lambda g: weighted_mean(g, "serious", "PROJWT"), include_groups=False
)
print("\nClimate change seen as a serious threat, % by year (PROJWT-weighted):")
print(pct_serious.round(1))
