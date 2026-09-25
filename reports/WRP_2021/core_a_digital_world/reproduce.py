"""Reproduce World Risk Poll 2021: A Digital World.

Run from the repository root:
    python reports/WRP_2021/core_a_digital_world/reproduce.py

Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import (  # noqa: E402
    Report, countries_in_all, distribution, external_path, load_wave, merge_gallup, pct,
)

report = Report(__file__)

DK = [98, 99]
REGIONS = {  # GlobalRegion code -> key
    1: "east_africa", 2: "central_west_africa", 3: "north_africa", 4: "southern_africa", 5: "latin_america",
    6: "north_america", 7: "central_asia", 8: "east_asia", 9: "southeast_asia", 10: "south_asia",
    11: "middle_east", 12: "east_europe", 13: "north_west_europe", 14: "south_europe", 15: "aus_nz",
}
REGION_NAMES = {  # as printed in the report
    1: "Eastern Africa", 2: "Central/Western Africa", 3: "Northern Africa", 4: "Southern Africa",
    5: "Latin America & Caribbean", 6: "Northern America", 7: "Central Asia", 8: "Eastern Asia",
    9: "Southeastern Asia", 10: "Southern Asia", 11: "Middle East", 12: "Eastern Europe",
    13: "Northern/Western Europe", 14: "Southern Europe", 15: "Australia & New Zealand",
}
EDUCATION = {1: "primary", 2: "secondary", 3: "post_secondary"}  # 9 = DK/refused
AGE = {1: "15_29", 2: "30_49", 3: "50_64", 4: "65plus"}  # AgeGroups4
INCOME_FEELINGS = {1: "comfortable", 2: "getting_by", 3: "difficult", 4: "very_difficult"}  # 5, 6 = DK, refused
AI = {"help": [1], "harm": [2], "no_opinion": [3], "neither": [4], "dk": DK}  # WP22227
WORRY = {"very": [1], "somewhat": [2], "not": [3], "dk": DK}

# Gallup World Poll items that are not in the public release (see README).
INTERNET_ACCESS = "WP16056"  # 'Do you have access to the internet in any way...?' 1 = yes, 2 = no
RELIGION = "WP119"  # 'Is religion an important part of your daily life?' 1 = yes, 2 = no
CONFIDENCE = "WP139"  # confidence in the national government: 1 = yes, 2 = no

d = load_wave(2021, [
    "WPID_RANDOM", "PROJWT", "Gender", "Country", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel",
    "Education", "AgeGroups4", "IncomeFeelings", "INCOME_5",
    "WP22222", "WP22223", "WP22224", "WP22225", "WP22468", "WP22524", "WP22226", "WP22227",
    "WP22259", "WP22260", "WP22261", "WP22262", "WP22263", "WP22252",
])
d19 = load_wave(2019, ["PROJWT", "COUNTRY_ISO3", "AgeGroups4", "L26", "L4C"])

# --- Derived variables ---------------------------------------------------------

# Worry that the government will use personal information: Tajikistan and
# Vietnam were asked about "the authorities" (WP22468) and Myanmar about "the
# government in power" (WP22524) instead of WP22224. Chart 3.5 (Southeastern
# Asia 52%) includes them.
d["gov_worry"] = d.WP22224.fillna(d.WP22468).fillna(d.WP22524)

# Discrimination in Chapter 1: skin colour, ethnic group/nationality or gender
# (WP22259, WP22261, WP22262). 1 = yes to any, 2 = everyone else who was asked;
# missing where none was asked (China, Saudi Arabia, United Arab Emirates).
DISC3 = ["WP22259", "WP22261", "WP22262"]
d["disc3"] = np.where(d[DISC3].eq(1).any(axis=1), 1, 2)
d.loc[d[DISC3].isna().all(axis=1), "disc3"] = np.nan

# Forms of discrimination in Chapter 3: skin colour, religion, ethnic
# group/nationality, gender, disability. 0, 1 or 2 (= two or more) forms;
# missing where none was asked.
DISC5 = ["WP22259", "WP22260", "WP22261", "WP22262", "WP22263"]
d["n_disc"] = d[DISC5].eq(1).sum(axis=1).clip(upper=2).astype(float)
d.loc[d[DISC5].isna().all(axis=1), "n_disc"] = np.nan

# Age under 50 vs 50 and over (text, Chapter 3).
d["under_50"] = d.AgeGroups4.map({1: 1, 2: 1, 3: 2, 4: 2})

# Internet users: used the internet in the past 30 days. Only they were asked
# the personal information questions (China's internet users were not asked).
iu = d[d.WP22222 == 1]

# Trends: the 119 countries surveyed in both 2019 and 2021, stacked with common
# names. Income groups use each country's 2021 World Bank group in both years
# (the 2019 group gives 30% for lower-middle-income countries in 2019, not 31%).
BOTH = countries_in_all([2019, 2021])
income_2021 = d.groupby("COUNTRY_ISO3").CountryIncomeLevel.first()
trend = pd.concat([
    d19.rename(columns={"L26": "internet", "L4C": "ai"}).assign(year=2019),
    d[["PROJWT", "COUNTRY_ISO3", "AgeGroups4", "WP22222", "WP22227"]]
    .rename(columns={"WP22222": "internet", "WP22227": "ai"}).assign(year=2021),
], ignore_index=True)
trend = trend[trend.COUNTRY_ISO3.isin(BOTH)].copy()
trend["income"] = trend.COUNTRY_ISO3.map(income_2021)

# External data for Chart 3.3: World Justice Project Rule of Law Index 2021. Not
# redistributed here: python reports/external/fetch_external.py wjp downloads it.
WJP = "core_a_digital_world__wjp_rule_of_law_index_2021.csv"

# --- Helpers -------------------------------------------------------------------


def answers(df, var, categories, by=None, keys=None, exclude=None):
    """% in each named category of `var`.

    Without `by`: {name: %}. With `by`: {"<group key>_<name>": %}, where `keys`
    maps group codes to keys (groups not in `keys` are dropped).
    """
    table = distribution(df, var, by=by, exclude=exclude)
    if by is None:
        return {name: table[table.index.intersection(codes)].sum() for name, codes in categories.items()}
    out = {}
    for code, key in keys.items():
        if code in table.index:
            row = table.loc[code]
            for name, codes in categories.items():
                out[f"{key}_{name}"] = row[row.index.intersection(codes)].sum()
    return out


def keyed(series, keys):
    """Rename a Series indexed by codes with readable keys (codes not in `keys` dropped)."""
    return {key: series[code] for code, key in keys.items() if code in series.index}


def round_half_up(x):
    return math.floor(x + 0.5)


def ratio_rounded(help_pct, harm_pct):
    """Mostly help / mostly harm from the rounded percentages, as the report does."""
    return round_half_up(help_pct) / round_half_up(harm_pct)


# --- Executive summary and Chapter 1: Artificial intelligence ---------------------


@report.finding("X01")
def respondents():
    return len(d)


@report.finding("X02")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X03")
def ai_help():
    return pct(d, "WP22227", [1])


@report.finding("X04")
def ai_harm():
    return pct(d, "WP22227", [2])


@report.finding("X05")
def ai_no_opinion_or_dk():
    return pct(d, "WP22227", [3, *DK])


@report.finding("X06")
def ai_no_opinion():
    return pct(d, "WP22227", [3])


@report.finding("X07")
def ai_dk():
    return pct(d, "WP22227", DK)


@report.finding("X08")
def ai_help_by_sex():
    return keyed(pct(d, "WP22227", [1], by="Gender"), {2: "women", 1: "men"})


@report.finding("X09")
def ai_harm_by_sex():
    return keyed(pct(d, "WP22227", [2], by="Gender"), {2: "women", 1: "men"})


@report.finding("X10")
def ai_help_trend():
    return keyed(pct(trend, "ai", [1], by="year"), {2019: "2019", 2021: "2021"})


@report.finding("X11")
def ai_harm_trend():
    return keyed(pct(trend, "ai", [2], by="year"), {2019: "2019", 2021: "2021"})


@report.finding("C1_1")
def ai_world_and_sex():
    out = {f"world_{k}": v for k, v in answers(d, "WP22227", AI).items()}
    return out | answers(d, "WP22227", AI, by="Gender", keys={2: "women", 1: "men"})


@report.finding("X12")
def ai_east_asia():
    e = d[d.GlobalRegion == 8]
    return {"help": pct(e, "WP22227", [1]), "harm": pct(e, "WP22227", [2])}


@report.finding("X13")
def ai_ratio_east_asia():
    e = d[d.GlobalRegion == 8]
    return ratio_rounded(pct(e, "WP22227", [1]), pct(e, "WP22227", [2]))


@report.finding("X14")
def ai_east_africa():
    e = d[d.GlobalRegion == 1]
    return {"harm": pct(e, "WP22227", [2]), "help": pct(e, "WP22227", [1])}


@report.finding("X15")
def ai_harm_east_african_countries():
    r = pct(d[d.COUNTRY_ISO3.isin(["TZA", "KEN", "UGA"])], "WP22227", [2], by="COUNTRY_ISO3")
    return {iso: r[iso] for iso in ("TZA", "KEN", "UGA")}


@report.finding("X16")
def ai_help_max_east_african_countries():
    return pct(d[d.COUNTRY_ISO3.isin(["TZA", "KEN", "UGA"])], "WP22227", [1], by="COUNTRY_ISO3").max()


def ai_by_region():
    out = answers(d, "WP22227", AI, by="GlobalRegion", keys=REGIONS)
    for key in REGIONS.values():
        out[f"{key}_ratio"] = ratio_rounded(out[f"{key}_help"], out[f"{key}_harm"])
    return out


@report.finding("C1_2")
def chart_ai_by_region():
    return ai_by_region()


@report.finding("M1_1")
def map_ai_ratio_by_region():
    out = ai_by_region()
    return {key: out[f"{key}_ratio"] for key in REGIONS.values()}


@report.finding("X17")
def ai_china():
    c = d[d.COUNTRY_ISO3 == "CHN"]
    return {"help": pct(c, "WP22227", [1]), "harm": pct(c, "WP22227", [2])}


@report.finding("T1_1")
def ai_top_countries():
    table = distribution(d, "WP22227", by="COUNTRY_ISO3")
    out = {}
    for iso in ("KOR", "JPN", "FIN", "SWE", "CHN", "DEU", "NOR", "EST", "DNK", "ISL"):
        row = table.loc[iso]
        out[f"{iso}_help"] = row[1]
        out[f"{iso}_harm"] = row[2]
        out[f"{iso}_net"] = row[1] - row[2]
        out[f"{iso}_no_opinion_dk"] = row[row.index.intersection([3, *DK])].sum()
    return out


ACCESS = {1: "access", 2: "no_access"}


@report.finding("X18")
def ai_help_by_internet_access():
    g = merge_gallup(d, [INTERNET_ACCESS])
    return keyed(pct(g, "WP22227", [1], by=INTERNET_ACCESS), ACCESS)


@report.finding("X19")
def ai_help_primary():
    return pct(d[d.Education == 1], "WP22227", [1])


@report.finding("X20")
def ai_help_primary_with_access():
    g = merge_gallup(d[d.Education == 1], [INTERNET_ACCESS])
    return pct(g[g[INTERNET_ACCESS] == 1], "WP22227", [1])


@report.finding("C1_3")
def chart_ai_by_internet_access():
    g = merge_gallup(d, [INTERNET_ACCESS])
    return answers(g, "WP22227", AI, by=INTERNET_ACCESS, keys=ACCESS)


@report.finding("X21")
def ai_usa():
    u = d[d.COUNTRY_ISO3 == "USA"]
    return {"help": pct(u, "WP22227", [1]), "harm": pct(u, "WP22227", [2])}


RELIGIOUS = {1: "important", 2: "not_important"}


@report.finding("X22")
def religion_important():
    g = merge_gallup(d, [RELIGION])
    return {"USA": pct(g[g.COUNTRY_ISO3 == "USA"], RELIGION, [1]),
            "north_west_europe": pct(g[g.GlobalRegion == 13], RELIGION, [1]),
            "east_asia": pct(g[g.GlobalRegion == 8], RELIGION, [1])}


@report.finding("X23")
def ai_help_usa_by_religion():
    g = merge_gallup(d[d.COUNTRY_ISO3 == "USA"], [RELIGION])
    return keyed(pct(g, "WP22227", [1], by=RELIGION), RELIGIOUS)


@report.finding("X24")
def ai_by_religion_text():
    g = merge_gallup(d, [RELIGION])
    return answers(g, "WP22227", {"help": [1], "harm": [2]}, by=RELIGION, keys=RELIGIOUS)


@report.finding("C1_4")
def chart_ai_by_religion():
    g = merge_gallup(d, [RELIGION])
    return answers(g, "WP22227", AI, by=RELIGION, keys=RELIGIOUS)


@report.finding("X25")
def ai_help_by_religion_access_post_secondary():
    g = merge_gallup(d[d.Education == 3], [RELIGION, INTERNET_ACCESS])
    return keyed(pct(g[g[INTERNET_ACCESS] == 1], "WP22227", [1], by=RELIGION), RELIGIOUS)


DISCRIMINATED = {1: "experienced", 2: "not_experienced"}


@report.finding("X26")
def ai_discriminated():
    e = d[d.disc3 == 1]
    return {"help": pct(e, "WP22227", [1]), "harm": pct(e, "WP22227", [2])}


@report.finding("X27")
def ai_not_discriminated():
    n = d[d.disc3 == 2]
    return {"help": pct(n, "WP22227", [1]), "harm": pct(n, "WP22227", [2])}


@report.finding("X28")
def ai_no_opinion_dk_by_discrimination():
    return keyed(pct(d, "WP22227", [3, *DK], by="disc3"), DISCRIMINATED)


@report.finding("C1_5")
def chart_ai_by_discrimination():
    return answers(d, "WP22227", AI, by="disc3", keys=DISCRIMINATED)


@report.finding("X29")
def countries_discrimination_harm_gap():
    r = pct(d, "WP22227", [2], by=["COUNTRY_ISO3", "disc3"]).unstack()
    return int((r[1] - r[2] >= 10).sum())


@report.finding("C1_6")
def chart_ai_harm_discrimination_nordics():
    r = pct(d[d.COUNTRY_ISO3.isin(["DNK", "NOR", "SWE"])], "WP22227", [2], by=["COUNTRY_ISO3", "disc3"])
    return {f"{iso}_{DISCRIMINATED[code]}": v for (iso, code), v in r.items()}


CAR = {"yes": [1], "no": [2], "dk": DK}  # WP22226


@report.finding("X30")
def car_safe():
    return {"yes": pct(d, "WP22226", [1]), "no": pct(d, "WP22226", [2])}


@report.finding("C1_7")
def chart_car_safe():
    return answers(d, "WP22226", CAR)


@report.finding("X31")
def car_safe_country_max():
    return pct(d, "WP22226", [1], by="COUNTRY_ISO3").max()


@report.finding("X32")
def car_safe_top_country():
    iso = pct(d, "WP22226", [1], by="COUNTRY_ISO3").idxmax()
    return d.loc[d.COUNTRY_ISO3 == iso, "Country"].iloc[0]


@report.finding("X33")
def car_safe_afghanistan_by_sex():
    return keyed(pct(d[d.COUNTRY_ISO3 == "AFG"], "WP22226", [1], by="Gender"), {1: "men", 2: "women"})


@report.finding("T1_2")
def car_safe_top_countries():
    r = pct(d, "WP22226", [1], by="COUNTRY_ISO3")
    return {iso: r[iso] for iso in ("DNK", "ARE", "AFG", "ITA", "ESP", "KGZ", "SWE", "SAU", "IRN", "NPL")}


@report.finding("X34")
def car_safe_by_education():
    return keyed(pct(d, "WP22226", [1], by="Education"), EDUCATION)


def car_safe_by_access_education():
    g = merge_gallup(d, [INTERNET_ACCESS])
    return pct(g, "WP22226", [1], by=[INTERNET_ACCESS, "Education"])


@report.finding("X35")
def car_safe_access_gap_min():
    r = car_safe_by_access_education()
    return min(r[(1, e)] - r[(2, e)] for e in EDUCATION)


@report.finding("C1_8_world")
def chart_car_safe_world_by_education():
    return keyed(pct(d, "WP22226", [1], by="Education"), EDUCATION)


@report.finding("C1_8_internet")
def chart_car_safe_with_access_by_education():
    r = car_safe_by_access_education()
    return {key: r[(1, e)] for e, key in EDUCATION.items()}


@report.finding("C1_8_no_internet")
def chart_car_safe_without_access_by_education():
    r = car_safe_by_access_education()
    return {key: r[(2, e)] for e, key in EDUCATION.items()}


# --- Chapter 2: Global internet use -------------------------------------------------

INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}


def internet_trend(df):
    return keyed(pct(df, "internet", [1], by="year"), {2019: "2019", 2021: "2021"})


@report.finding("X36")
def countries_both_waves():
    return len(BOTH)


@report.finding("X37")
def internet_trend_world():
    return internet_trend(trend)


@report.finding("X38")
def internet_trend_lower_middle():
    return internet_trend(trend[trend.income == 2])


@report.finding("X39")
def internet_trend_upper_middle():
    return internet_trend(trend[trend.income == 3])


@report.finding("X40")
def internet_trend_low():
    return internet_trend(trend[trend.income == 1])


@report.finding("X41")
def internet_lowest_regions():
    r = pct(d, "WP22222", [1], by="GlobalRegion")
    return {REGIONS[code]: r[code] for code in (10, 1, 2)}


@report.finding("X42")
def internet_by_education():
    return keyed(pct(d, "WP22222", [1], by="Education"), EDUCATION)


@report.finding("X43")
def internet_by_sex():
    return keyed(pct(d, "WP22222", [1], by="Gender"), {1: "men", 2: "women"})


def internet_gender_gap_by_region():
    r = pct(d, "WP22222", [1], by=["GlobalRegion", "Gender"]).unstack()
    return r[1] - r[2]


@report.finding("X44")
def internet_widest_gender_gap_region():
    return REGION_NAMES[internet_gender_gap_by_region().idxmax()]


@report.finding("X45")
def internet_gender_gap_south_asia():
    return internet_gender_gap_by_region()[10]


@report.finding("X46")
def internet_south_asia_women_primary():
    return pct(d[(d.GlobalRegion == 10) & (d.Gender == 2) & (d.Education == 1)], "WP22222", [1])


@report.finding("X47")
def internet_trend_65plus():
    return internet_trend(trend[trend.AgeGroups4 == 4])


@report.finding("C2_1")
def chart_internet_trend_by_income():
    out = {f"world_{k}": v for k, v in internet_trend(trend).items()}
    r = pct(trend, "internet", [1], by=["income", "year"])
    return out | {f"{key}_{year}": r[(code, year)] for code, key in INCOME.items() for year in (2019, 2021)}


@report.finding("C2_2")
def chart_internet_by_region():
    return keyed(pct(d, "WP22222", [1], by="GlobalRegion"), REGIONS)


@report.finding("X48")
def primary_share_by_region():
    r = pct(d, "Education", [1], by="GlobalRegion")
    return {REGIONS[code]: r[code] for code in (10, 2, 1, 8, 3)}


@report.finding("X49")
def regions_primary_majority():
    return int((pct(d, "Education", [1], by="GlobalRegion") > 50).sum())


@report.finding("X50")
def internet_primary_by_region():
    r = pct(d[d.Education == 1], "WP22222", [1], by="GlobalRegion")
    return {REGIONS[code]: r[code] for code in (10, 1, 2)}


@report.finding("C2_3")
def chart_internet_by_education_region():
    out = {f"world_{k}": v for k, v in keyed(pct(d, "WP22222", [1], by="Education"), EDUCATION).items()}
    r = pct(d, "WP22222", [1], by=["GlobalRegion", "Education"])
    return out | {f"{REGIONS[g]}_{key}": r[(g, e)] for g in (10, 2, 1) for e, key in EDUCATION.items()}


@report.finding("X51")
def internet_by_income_quintile():
    return keyed(pct(d, "WP22222", [1], by="INCOME_5"), {1: "lowest", 5: "highest"})


@report.finding("X52")
def internet_south_asia_by_sex():
    return keyed(pct(d[d.GlobalRegion == 10], "WP22222", [1], by="Gender"), {1: "men", 2: "women"})


@report.finding("X53")
def internet_gender_gap_excluding_south_asia():
    r = pct(d[d.GlobalRegion != 10], "WP22222", [1], by="Gender")
    return r[1] - r[2]


@report.finding("X54")
def internet_excluding_south_asia_by_sex():
    return keyed(pct(d[d.GlobalRegion != 10], "WP22222", [1], by="Gender"), {1: "men", 2: "women"})


@report.finding("X55")
def primary_share_south_asia_by_sex():
    return keyed(pct(d[d.GlobalRegion == 10], "Education", [1], by="Gender"), {2: "women", 1: "men"})


@report.finding("X56")
def internet_south_asia_secondary_by_sex():
    s = d[(d.GlobalRegion == 10) & (d.Education == 2)]
    return keyed(pct(s, "WP22222", [1], by="Gender"), {1: "men", 2: "women"})


@report.finding("X57")
def internet_south_asia_men_primary():
    return pct(d[(d.GlobalRegion == 10) & (d.Gender == 1) & (d.Education == 1)], "WP22222", [1])


@report.finding("X58")
def internet_by_age():
    return keyed(pct(d, "WP22222", [1], by="AgeGroups4"), {1: "15_29", 4: "65plus"})


@report.finding("X59")
def internet_increase_by_age():
    r = pct(trend, "internet", [1], by=["AgeGroups4", "year"])
    return {key: r[(code, 2021)] - r[(code, 2019)] for code, key in {4: "65plus", 1: "15_29", 2: "30_49"}.items()}


@report.finding("C2_4")
def chart_internet_trend_by_age():
    r = pct(trend, "internet", [1], by=["AgeGroups4", "year"])
    return {f"{key}_{year}": r[(code, year)] for code, key in AGE.items() for year in (2019, 2021)}


@report.finding("X60")
def protect_low_income_by_internet_access():
    g = merge_gallup(d[d.CountryIncomeLevel == 1], [INTERNET_ACCESS])
    return keyed(pct(g, "WP22252", [1], by=INTERNET_ACCESS), ACCESS)


# --- Chapter 3: Online data ----------------------------------------------------------


@report.finding("X61")
def stolen_very_or_somewhat():
    return pct(iu, "WP22223", [1, 2])


@report.finding("X62")
def companies_very_or_somewhat_summary():
    return pct(iu, "WP22225", [1, 2])


@report.finding("X63")
def companies_very_or_somewhat():
    return pct(iu, "WP22225", [1, 2])


@report.finding("X64")
def government_very_or_somewhat():
    return pct(iu, "gov_worry", [1, 2])


@report.finding("X65")
def regions_majority_very_worried_stolen():
    return int((pct(iu, "WP22223", [1], by="GlobalRegion") > 50).sum())


@report.finding("X66")
def stolen_very_top_regions():
    r = pct(iu, "WP22223", [1], by="GlobalRegion")
    return {REGIONS[code]: r[code] for code in (2, 9, 4, 5, 1)}


@report.finding("C3_1")
def chart_worry_personal_information():
    out = {}
    for key, var in (("stolen", "WP22223"), ("companies", "WP22225"), ("government", "gov_worry")):
        out |= {f"{key}_{k}": v for k, v in answers(iu, var, WORRY).items()}
    return out


@report.finding("C3_2")
def chart_stolen_by_region():
    return answers(iu, "WP22223", WORRY, by="GlobalRegion", keys=REGIONS)


@report.finding("C3_3")
def chart_stolen_rule_of_law():
    # No values are printed on the chart: the correlation across countries is
    # reported for reference only (see README).
    wjp = pd.read_csv(external_path(WJP))
    very = pct(iu, "WP22223", [1], by="COUNTRY_ISO3")
    m = pd.DataFrame({"iso3": very.index, "very": very.values}).dropna().merge(wjp, on="iso3")
    return {"correlation": m["very"].corr(m["wjp_rule_of_law_index_2021"]), "n_countries": len(m)}


@report.finding("X67")
def stolen_very_by_sex():
    return keyed(pct(iu, "WP22223", [1], by="Gender"), {2: "women", 1: "men"})


@report.finding("X68")
def stolen_very_by_education():
    return keyed(pct(iu, "WP22223", [1], by="Education"), EDUCATION)


@report.finding("X69")
def stolen_very_by_age():
    return {"under_50": pct(iu, "WP22223", [1], by="under_50")[1],
            "65plus": pct(iu, "WP22223", [1], by="AgeGroups4")[4]}


@report.finding("X70")
def stolen_very_by_income_feelings_text():
    return keyed(pct(iu, "WP22223", [1], by="IncomeFeelings"), {1: "comfortable", 4: "very_difficult"})


@report.finding("C3_4")
def chart_stolen_very_by_age_income():
    return (keyed(pct(iu, "WP22223", [1], by="AgeGroups4"), AGE)
            | keyed(pct(iu, "WP22223", [1], by="IncomeFeelings"), INCOME_FEELINGS))


@report.finding("C3_5")
def chart_companies_government_by_region():
    c = pct(iu, "WP22225", [1], by="GlobalRegion")
    g = pct(iu, "gov_worry", [1], by="GlobalRegion")
    return {f"{key}_{item}": r[code] for code, key in REGIONS.items() for item, r in (("companies", c), ("government", g))}


CONFIDENT = {1: "confidence", 2: "no_confidence"}


@report.finding("X71")
def government_very_by_confidence():
    g = merge_gallup(iu, [CONFIDENCE])
    return keyed(pct(g, "gov_worry", [1], by=CONFIDENCE), CONFIDENT)


@report.finding("C3_6")
def chart_government_very_by_confidence_countries():
    g = merge_gallup(iu, [CONFIDENCE])
    isos = ["MUS", "TUR", "POL", "HND", "SLV", "GRC", "USA", "JPN", "HKG", "IRN"]
    r = pct(g[g.COUNTRY_ISO3.isin(isos)], "gov_worry", [1], by=["COUNTRY_ISO3", CONFIDENCE])
    return {f"{iso}_{key}": r[(iso, code)] for iso in isos for code, key in CONFIDENT.items()}


# Chart 3.7 and the text on page 34: the companies series leaves don't know and
# refused out of the base (this reproduces all four bars); the government series
# keeps them in, like every other chart.


@report.finding("X72")
def very_worried_very_difficult():
    v = iu[iu.IncomeFeelings == 4]
    return {"government": pct(v, "gov_worry", [1]), "companies": pct(v, "WP22225", [1], exclude=DK)}


@report.finding("C3_7")
def chart_companies_government_by_income_feelings():
    c = pct(iu, "WP22225", [1], by="IncomeFeelings", exclude=DK)
    g = pct(iu, "gov_worry", [1], by="IncomeFeelings")
    return {f"{key}_{item}": r[code] for code, key in INCOME_FEELINGS.items()
            for item, r in (("companies", c), ("government", g))}


@report.finding("C3_8")
def chart_very_worried_by_discrimination():
    forms = {0: "none", 1: "one", 2: "two_plus"}
    out = {}
    for key, var in (("stolen", "WP22223"), ("companies", "WP22225"), ("government", "gov_worry")):
        out |= {f"{key}_{k}": v for k, v in keyed(pct(iu, var, [1], by="n_disc"), forms).items()}
    return out


@report.finding("X73")
def very_worried_discriminated_very_difficult():
    v = iu[(iu.n_disc >= 1) & (iu.IncomeFeelings == 4)]
    return {"stolen": pct(v, "WP22223", [1]), "government": pct(v, "gov_worry", [1])}


if __name__ == "__main__":
    sys.exit(report.run())
