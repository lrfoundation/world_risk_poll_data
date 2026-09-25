"""Reproduce The Lloyd's Register Foundation World Risk Poll: Full report and analysis of the 2019 poll.

Run from the repository root:
    python reports/WRP_2019/core_world_risk_poll_2019/reproduce.py

Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes. The script has one
section per chapter of the report. It was written in three parts (Executive
Summary to Chapter 2; Chapters 3-5; Chapters 6-10), and module-level names
from the second and third carry p2_ and p3_ prefixes.
"""

import sys
import warnings
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

# The chapters add many derived columns one at a time; pandas warns that this
# fragments the data frame, which affects only speed.
warnings.simplefilter("ignore", pd.errors.PerformanceWarning)

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, external_path, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)


def add_columns(df, columns):
    """`df` plus any of `columns` it does not have yet, loaded from the 2019 file.

    Every load of the wave has the same rows in the same order, so the new
    columns line up with the old ones.
    """
    new = [c for c in dict.fromkeys(columns) if c not in df.columns]
    return pd.concat([df, load_wave(2019, new)], axis=1) if new else df



# ==============================================================================
# Part 1: Executive Summary, Introduction, Chapters 1-2
# ==============================================================================

# --- Data ------------------------------------------------------------------------
# Columns used by the report. Later chapters add theirs to this list.

COLUMNS = [
    "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel",
    "Gender", "AgeGroups4", "Education", "Urbanicity2", "IncomeFeelings",
    "worry_index_published", "experience_index_published",
    "L1", "L2", "L3_A", "L3_B", "L4A", "L5", "L8A", "L8B", "L13G", "L13H", "L14",
    "L16A", "L16B", "L16C", "L19", "L20D", "L21D", "L27A", "L27B", "L27C",
]
d = load_wave(2019, COLUMNS)

WORLD_BANK = pd.read_csv(external_path("core_world_risk_poll_2019__worldbank.csv"))


def freedom_house():
    """Freedom in the World 2020 scores. Not redistributed here: see reports/external/README.md."""
    return pd.read_csv(external_path("core_world_risk_poll_2019__freedom_house.csv")).dropna(subset=["iso3"])

# --- Codes -------------------------------------------------------------------------

DK = [98, 99]
REGION = {  # GlobalRegion
    1: "east_africa", 2: "central_west_africa", 3: "north_africa", 4: "southern_africa", 5: "latin_america",
    6: "north_america", 7: "central_asia", 8: "east_asia", 9: "southeast_asia", 10: "south_asia",
    11: "middle_east", 12: "east_europe", 13: "north_west_europe", 14: "south_europe", 15: "aus_nz",
}
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # CountryIncomeLevel
SEX = {2: "women", 1: "men"}  # Gender
SAFE = {"more": [1], "same": [3], "less": [2]}  # L2
RISK = {"opp": [1], "danger": [2], "both": [3], "neither": [4], "dk": DK}  # L1

# --- Derived variables ---------------------------------------------------------------

# Safety scale for footnote 34: 1 = more safe, 2 = about as safe, 3 = less safe (DK/refused missing).
d["safety_scale"] = d.L2.map({1: 1, 3: 2, 2: 3})

# Greatest sources of risk (L3_A first response, L3_B second response; L3_B is missing for
# people who named no risk or did not know at L3_A, and was not asked of them).
# Two measures are used in Chapter 2 (see README):
#  - global "first or second response" figures (Chart 2.1 and the global text) add the % naming a
#    category first and the % naming it second (mentions);
#  - country, region and group figures use the % of respondents naming the category (or any
#    category in a group) first or second: the t2_* flags below (1 = named, 2 = not).
TOP2_GROUPS = {
    "road": [1, 2],  # road-related and other transportation accidents
    "health": [9, 10],  # personal health condition/illness; drugs, alcohol, smoking
    "crime": [3],
    "financial": [5, 6],  # not having enough money; economy-related
    "environment": [13, 16],  # pollution; climate change, natural disasters, weather
    "food_water": [11, 12],
    "political": [7],
    "none": [19],  # nothing/no risks
}
for name, codes in TOP2_GROUPS.items():
    d[f"t2_{name}"] = np.where(d.L3_A.isin(codes) | d.L3_B.isin(codes), 1, 2)
d["second_response"] = d.L3_B.fillna(0)  # 0 = not asked the follow-up

# Government Safety Performance Index (Chapter 9, used in the Executive Summary):
# yes = 1, any other answer = 0 on L16A-C, averaged and x 100. Not asked in two countries.
gspi = d[d.L16A.notna()].copy()
gspi["gspi"] = 100 * gspi[["L16A", "L16B", "L16C"]].eq(1).mean(axis=1)

# --- Helpers ---------------------------------------------------------------------------


def shares(df, var, categories, exclude=None):
    """% in each named category of `var`: {"<name>": %}."""
    table = distribution(df, var, exclude=exclude)
    return {name: table[table.index.intersection(codes)].sum() for name, codes in categories.items()}


def grid(df, var, categories, by, groups):
    """% in each named category of `var` within each group of `by`: {"<group>_<name>": %}."""
    table = distribution(df, var, by=by)
    return {
        f"{group}_{name}": table.loc[code, table.columns.intersection(codes)].sum()
        for code, group in groups.items() for name, codes in categories.items()
    }


def keyed(values, groups):
    """Rename a Series indexed by group codes: {"<group>": value}."""
    return {name: values[code] for code, name in groups.items()}


def by_country(df, var, codes):
    """Weighted % with `var` in `codes`, by country (Series indexed by ISO3)."""
    return pct(df, var, codes, by="COUNTRY_ISO3")


def world_map(values):
    """All country values plus the lowest and highest (the map legend's end points)."""
    return {**values.to_dict(), "min": values.min(), "max": values.max()}


def ranked(values, n, lowest=False):
    """ISO3 codes of the n highest (or lowest) countries: {1: iso3, 2: ...}."""
    order = values.sort_values(ascending=lowest).index[:n]
    return {i: iso for i, iso in enumerate(order, 1)}


def mentions(df, codes):
    """Global 'first or second response' %: % naming `codes` first plus % naming them second."""
    w = df.PROJWT
    return 100 * ((w * df.L3_A.isin(codes)).sum() + (w * df.L3_B.isin(codes)).sum()) / w.sum()


def population(mask):
    """Adults represented: sum of PROJWT over the rows in `mask`, in whole people."""
    return round(d.PROJWT[mask].sum())


def world_bank(indicator, year=None, latest_upto=None):
    """World Bank indicator by ISO3, for one year or the most recent value up to a year."""
    x = WORLD_BANK[WORLD_BANK.indicator == indicator]
    if year is not None:
        return x[x.year == year].set_index("iso3").value
    x = x[x.year <= latest_upto].sort_values("year")
    return x.groupby("iso3").value.last()


def correlation(x, y):
    """Pearson correlation across the countries present in both series, and the count."""
    both = pd.concat([x, y], axis=1, join="inner").dropna()
    return both.iloc[:, 0].corr(both.iloc[:, 1]), len(both)


# --- Executive Summary, Preface and Foreword ------------------------------------------


@report.finding("E01")
def respondents_preface():
    return len(d)


@report.finding("E02")
def countries_preface():
    return d.COUNTRY_ISO3.nunique()


@report.finding("E03")
def respondents_foreword():
    return len(d)


@report.finding("E04")
def countries_foreword():
    return d.COUNTRY_ISO3.nunique()


@report.finding("E05")
def respondents():
    return len(d)


@report.finding("E06")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("E07")
def no_risk_first():
    return pct(d, "L3_A", [19])


@report.finding("E08")
def no_risk_second():
    return pct(d, "second_response", [19])


@report.finding("E09")
def trust_government_food_agency():
    return pct(d, "L14", [5])


@report.finding("E10")
def low_income_famous_person():
    return pct(d[d.CountryIncomeLevel == 1], "L13G", [1])


@report.finding("E11")
def low_income_religious_leaders():
    return pct(d[d.CountryIncomeLevel == 1], "L13H", [1])


@report.finding("E12")
def women_less_safe():
    return pct(d[d.Gender == 2], "L2", [2])


# Violence and harassment at work (L20D risk, L21D experience): asked of workers.
women = d[d.Gender == 2]
women_vh_risk = by_country(women, "L20D", [1])
women_vh_experience = by_country(women, "L21D", [1])


@report.finding("E13")
def women_vh_risk_two_thirds():
    return women_vh_risk[["MWI", "SWZ", "NPL"]]


@report.finding("E14")
def women_vh_risk_developed():
    return women_vh_risk[["FIN", "FRA", "SWE", "AUS"]]


@report.finding("E15")
def zambia_women_vh_experience():
    return women_vh_experience["ZMB"]


@report.finding("E16")
def top_women_vh_experience():
    return ranked(women_vh_experience, 1)[1]


@report.finding("E17")
def australia_rank_women_vh_experience():
    return list(women_vh_experience.sort_values(ascending=False).index).index("AUS") + 1


@report.finding("E18")
def australia_women_vh_experience():
    return women_vh_experience["AUS"]


@report.finding("E19")
def australia_men_vh_experience():
    return by_country(d[d.Gender == 1], "L21D", [1])["AUS"]


@report.finding("E20")
def workers_ever_injured():
    return pct(d, "L19", [1])


@report.finding("E21")
def countries_half_workers_injured():
    return int((by_country(d, "L19", [1]) > 50).sum())


@report.finding("E22")
def harm_food():
    return pct(d, "L8A", [1])


@report.finding("E23")
def harm_food_people():
    return population(d.L8A == 1)


@report.finding("E24")
def harm_water():
    return pct(d, "L8B", [1])


@report.finding("E25")
def harm_water_people():
    return population(d.L8B == 1)


@report.finding("E26")
def harm_food_top_countries():
    return by_country(d, "L8A", [1])[["LBR", "ZMB", "MOZ"]]


@report.finding("E27")
def gm_food_harm():
    return pct(d, "L4A", [2])


@report.finding("E28")
def internet_any_worry():
    users = d[d.L27A.notna()].copy()  # internet users in the past 30 days
    users["any_worry"] = np.where(users[["L27A", "L27B", "L27C"]].eq(1).any(axis=1), 1, 2)
    return pct(users, "any_worry", [1])


@report.finding("E29")
def internet_false_information():
    return pct(d, "L27B", [1])


@report.finding("E30")
def internet_fraud():
    return pct(d, "L27C", [1])


@report.finding("E31")
def internet_fraud_western_europe():
    return by_country(d, "L27C", [1])[["PRT", "FRA", "ESP", "GBR", "ITA"]]


@report.finding("E32")
def climate_threat():
    return pct(d, "L5", [1, 2])


@report.finding("E33")
def china_climate_very_serious():
    return by_country(d, "L5", [1])["CHN"]


@report.finding("E34")
def us_climate_not_a_threat():
    return by_country(d, "L5", [3])["USA"]


worry = wmean(d, "worry_index_published", by="COUNTRY_ISO3")
experience = wmean(d, "experience_index_published", by="COUNTRY_ISO3")


@report.finding("E35")
def countries_in_indices():
    return int((worry.notna() & experience.notna()).sum())


@report.finding("E36")
def over_worriers():
    return ranked(worry - experience, 5)


@report.finding("E37")
def smallest_worry_experience_gap():
    return ranked(worry - experience, 1, lowest=True)[1]


@report.finding("E38")
def highest_worry():
    return ranked(worry, 5)


@report.finding("E39")
def highest_experience():
    return ranked(experience, 4)


gspi_country = wmean(gspi, "gspi", by="COUNTRY_ISO3")


@report.finding("E40")
def gspi_below_50():
    return 100 * (gspi_country < 50).mean()


@report.finding("E41")
def gspi_lowest():
    return ranked(gspi_country, 4, lowest=True)


@report.finding("E42")
def gspi_highest():
    return ranked(gspi_country, 2)


# --- Introduction -------------------------------------------------------------------------


@report.finding("I01")
def countries_introduction():
    return d.COUNTRY_ISO3.nunique()


# --- Chapter 1: How safe do we feel? ---------------------------------------------------------


@report.finding("X1_01")
def more_safe_key_finding():
    return pct(d, "L2", [1])


@report.finding("X1_02")
def less_safe_key_finding():
    return pct(d, "L2", [2])


@report.finding("X1_03")
def as_safe_key_finding():
    return pct(d, "L2", [3])


@report.finding("X1_04")
def risk_danger_key_finding():
    return pct(d, "L1", [2])


@report.finding("X1_05")
def risk_opportunity_key_finding():
    return pct(d, "L1", [1])


@report.finding("X1_06")
def more_safe():
    return pct(d, "L2", [1])


@report.finding("X1_07")
def less_safe():
    return pct(d, "L2", [2])


@report.finding("C1_1")
def safety_global():
    return shares(d, "L2", {**SAFE, "dk": DK})


@report.finding("C1_2")
def safety_by_income():
    return grid(d, "L2", SAFE, "CountryIncomeLevel", INCOME)


@report.finding("X1_08")
def upper_middle_more_safe():
    return pct(d[d.CountryIncomeLevel == 3], "L2", [1])


@report.finding("X1_09")
def high_income_bad_time_job_less_safe():
    # Gallup World Poll WP89: good (1) or bad (2) time to find a job in your area.
    g = merge_gallup(d[d.CountryIncomeLevel == 4], ["WP89"])
    return pct(g, "L2", [2], by="WP89")[2]


@report.finding("X1_10")
def high_income_good_time_job_less_safe():
    g = merge_gallup(d[d.CountryIncomeLevel == 4], ["WP89"])
    return pct(g, "L2", [2], by="WP89")[1]


upper_middle = d[d.CountryIncomeLevel == 3]


@report.finding("X1_11")
def china_share_upper_middle():
    return 100 * upper_middle.PROJWT[upper_middle.COUNTRY_ISO3 == "CHN"].sum() / upper_middle.PROJWT.sum()


@report.finding("X1_12")
def upper_middle_countries():
    return upper_middle.COUNTRY_ISO3.nunique()


@report.finding("X1_13")
def upper_middle_excl_china_more_safe():
    return pct(upper_middle[upper_middle.COUNTRY_ISO3 != "CHN"], "L2", [1])


@report.finding("C1_3")
def safety_by_region():
    return grid(d, "L2", SAFE, "GlobalRegion", REGION)


@report.finding("X1_14")
def east_asia_more_safe():
    return pct(d[d.GlobalRegion == 8], "L2", [1])


@report.finding("X1_15")
def south_africa_share_of_region():
    region = d[d.GlobalRegion == 4]
    return 100 * region.PROJWT[region.COUNTRY_ISO3 == "ZAF"].sum() / region.PROJWT.sum()


less_safe_country = by_country(d, "L2", [2])


@report.finding("X1_16")
def southern_africa_less_safe():
    return less_safe_country[["ZAF", "NAM", "BWA", "LSO", "SWZ"]]


@report.finding("C1_4")
def less_safe_map():
    return world_map(less_safe_country)


def safety_table(countries):
    table = distribution(d, "L2", by="COUNTRY_ISO3")
    return {f"{iso}_{name}": table.loc[iso, codes].sum() for iso in countries for name, codes in SAFE.items()}


@report.finding("T1_1")
def most_less_safe():
    return safety_table(["LBN", "HKG", "AFG", "VEN"])


@report.finding("X1_17")
def afghanistan_safe_walking():
    # Gallup World Poll WP113: feel safe walking alone at night in your area (1 = yes).
    return by_country(merge_gallup(d, ["WP113"]), "WP113", [1])["AFG"]


@report.finding("X1_18")
def lowest_safe_walking():
    return ranked(by_country(merge_gallup(d, ["WP113"]), "WP113", [1]), 1, lowest=True)[1]


@report.finding("X1_19")
def hong_kong_police_confidence():
    # Gallup World Poll WP112: confidence in the local police (1 = yes).
    return by_country(merge_gallup(d, ["WP112"]), "WP112", [1])["HKG"]


@report.finding("T1_2")
def most_more_safe():
    return safety_table(["RWA", "CHN", "LAO", "ARE", "ETH"])


@report.finding("X1_20")
def ethiopia_more_safe():
    return by_country(d, "L2", [1])["ETH"]


@report.finding("X1_21")
def china_living_standards():
    # Gallup World Poll WP31: standard of living getting better (1) or worse (2).
    return by_country(merge_gallup(d, ["WP31"]), "WP31", [1])["CHN"]


@report.finding("X1_22")
def top_living_standards():
    return ranked(by_country(merge_gallup(d, ["WP31"]), "WP31", [1]), 1)[1]


@report.finding("X1_23")
def women_less_safe_ch1():
    return pct(d, "L2", [2], by="Gender")[2]


@report.finding("X1_24")
def men_less_safe():
    return pct(d, "L2", [2], by="Gender")[1]


@report.finding("C1_5")
def less_safe_by_income_and_gender():
    world = {f"world_{s}": v for s, v in keyed(pct(d, "L2", [2], by="Gender"), SEX).items()}
    groups = {(i, s): f"{inc}_{sex}" for i, inc in INCOME.items() for s, sex in SEX.items()}
    return {**world, **keyed(pct(d, "L2", [2], by=["CountryIncomeLevel", "Gender"]), groups)}


less_safe_by_sex = pct(d, "L2", [2], by=["COUNTRY_ISO3", "Gender"]).unstack()


@report.finding("X1_25")
def less_safe_by_gender_countries():
    return {f"{iso}_{sex}": less_safe_by_sex.loc[iso, code] for iso in ("CHL", "USA", "JPN") for code, sex in SEX.items()}


@report.finding("X1_26")
def largest_gender_gap_high_income():
    high = d[d.CountryIncomeLevel == 4].COUNTRY_ISO3.unique()
    gap = less_safe_by_sex[2] - less_safe_by_sex[1]
    return ranked(gap[gap.index.isin(high)], 1)[1]


def us_less_safe_no_police_confidence(sex):
    g = merge_gallup(d[(d.COUNTRY_ISO3 == "USA") & (d.Gender == sex)], ["WP112"])
    return pct(g[g.WP112 == 2], "L2", [2])


@report.finding("X1_27")
def us_women_no_police_confidence():
    return us_less_safe_no_police_confidence(2)


@report.finding("X1_28")
def us_men_no_police_confidence():
    return us_less_safe_no_police_confidence(1)


@report.finding("C1_6")
def safety_by_living_standards_and_police():
    g = merge_gallup(d, ["WP31", "WP112"])
    return {**grid(g, "L2", SAFE, "WP31", {1: "living_better", 2: "living_worse"}),
            **grid(g, "L2", SAFE, "WP112", {1: "police_yes", 2: "police_no"})}


safety_scale_country = wmean(d, "safety_scale", by="COUNTRY_ISO3")


@report.finding("X1_29")
def safety_gdp_per_capita_correlation():
    return correlation(safety_scale_country, world_bank("NY.GDP.PCAP.CD", year=2018))[0]


@report.finding("X1_30")
def safety_gdp_growth_correlation():
    return correlation(safety_scale_country, world_bank("NY.GDP.MKTP.KD.ZG", year=2018))[0]


@report.finding("X1_31")
def risk_danger():
    return pct(d, "L1", [2])


@report.finding("X1_32")
def risk_opportunity():
    return pct(d, "L1", [1])


@report.finding("X1_33")
def risk_both():
    return pct(d, "L1", [3])


@report.finding("X1_34")
def risk_neither_dk():
    return pct(d, "L1", [4, *DK])


@report.finding("C1_7")
def risk_by_region():
    return grid(d, "L1", RISK, "GlobalRegion", REGION)


opportunity_country = by_country(d, "L1", [1])


def at_least_one_in_three():
    """Countries where the rounded % seeing risk as opportunity is 33 or more."""
    return opportunity_country[np.round(opportunity_country) >= 33].index


@report.finding("X1_35")
def countries_one_in_three_opportunity():
    return len(at_least_one_in_three())


@report.finding("X1_36")
def one_in_three_higher_income():
    income = d.groupby("COUNTRY_ISO3").CountryIncomeLevel.first()
    return int(income[at_least_one_in_three()].isin([3, 4]).sum())


@report.finding("X1_37")
def opportunity_countries():
    return opportunity_country[["ARE", "BHR", "KWT", "SAU", "DEU", "SVN", "AUT", "USA"]]


# Language of interview (Chart 1.8) is a Gallup World Poll field that is not in the public
# data; GWP_INTERVIEW_LANGUAGE is a placeholder name holding the language (e.g. "Spanish").
LANGUAGES = {"English": "english", "Russian": "russian", "Chinese": "chinese", "Arabic": "arabic",
             "French": "french", "Spanish": "spanish"}


@report.finding("X1_38")
def spanish_opportunity():
    g = merge_gallup(d, ["GWP_INTERVIEW_LANGUAGE"])
    return pct(g[g.GWP_INTERVIEW_LANGUAGE == "Spanish"], "L1", [1])


@report.finding("X1_39")
def latin_america_opportunity():
    return pct(d[d.GlobalRegion == 5], "L1", [1])


@report.finding("X1_40")
def spain_opportunity():
    return opportunity_country["ESP"]


@report.finding("C1_8")
def risk_by_language():
    g = merge_gallup(d, ["GWP_INTERVIEW_LANGUAGE"])
    return grid(g, "L1", RISK, "GWP_INTERVIEW_LANGUAGE", LANGUAGES)


@report.finding("X1_41")
def men_opportunity():
    return pct(d, "L1", [1], by="Gender")[1]


@report.finding("X1_42")
def women_opportunity():
    return pct(d, "L1", [1], by="Gender")[2]


@report.finding("C1_9")
def opportunity_by_gender_and_income():
    world = {f"world_{inc}": v for inc, v in keyed(pct(d, "L1", [1], by="CountryIncomeLevel"), INCOME).items()}
    groups = {(i, s): f"{sex}_{inc}" for i, inc in INCOME.items() for s, sex in SEX.items()}
    return {**world, **keyed(pct(d, "L1", [1], by=["CountryIncomeLevel", "Gender"]), groups)}


opportunity_by_sex = pct(d, "L1", [1], by=["COUNTRY_ISO3", "Gender"]).unstack()


@report.finding("X1_43")
def countries_men_opportunity_gap():
    return int((np.round(opportunity_by_sex[1]) - np.round(opportunity_by_sex[2]) > 10).sum())


@report.finding("X1_44")
def opportunity_gender_gap_countries():
    return {f"{iso}_{sex}": opportunity_by_sex.loc[iso, code]
            for iso in ("BHR", "AUT", "JPN", "USA") for code, sex in SEX.items()}


@report.finding("X1_45")
def opportunity_tertiary():
    return pct(d, "L1", [1], by="Education")[3]


@report.finding("X1_46")
def opportunity_primary():
    return pct(d, "L1", [1], by="Education")[1]


@report.finding("X1_47")
def opportunity_living_comfortably():
    return pct(d, "L1", [1], by="IncomeFeelings")[1]


@report.finding("X1_48")
def opportunity_very_difficult():
    return pct(d, "L1", [1], by="IncomeFeelings")[4]


EDUCATION = {1: "educ_0_8", 2: "educ_9_15", 3: "educ_16plus"}
INCOME_FEELINGS = {1: "comfortable", 2: "getting_by", 3: "difficult", 4: "very_difficult"}


@report.finding("C1_10")
def risk_by_education_and_income_feelings():
    return {**grid(d, "L1", RISK, "Education", EDUCATION), **grid(d, "L1", RISK, "IncomeFeelings", INCOME_FEELINGS)}


# --- Chapter 2: The sources of greatest risk in people's lives -----------------------------

t2_country = {name: by_country(d, f"t2_{name}", [1]) for name in TOP2_GROUPS}


@report.finding("X2_01")
def countries_health_over_40():
    return int((t2_country["health"] > 40).sum())


@report.finding("X2_02")
def no_risk_first_key_finding():
    return pct(d, "L3_A", [19])


@report.finding("X2_03")
def no_risk_second_key_finding():
    return pct(d, "second_response", [19])


@report.finding("X2_04")
def first_no_risk():
    return pct(d, "L3_A", [19])


@report.finding("X2_05")
def first_dk():
    return pct(d, "L3_A", DK)


@report.finding("X2_06")
def first_road():
    return pct(d, "L3_A", [1])


@report.finding("X2_07")
def first_crime():
    return pct(d, "L3_A", [3])


@report.finding("X2_08")
def first_health():
    return pct(d, "L3_A", [9])


@report.finding("X2_09")
def second_none_dk_not_asked():
    return pct(d, "second_response", [0, 19, *DK])


@report.finding("X2_10")
def second_road():
    return pct(d, "second_response", [1])


@report.finding("X2_11")
def second_crime():
    return pct(d, "second_response", [3])


@report.finding("X2_12")
def second_health():
    return pct(d, "second_response", [9])


@report.finding("X2_13")
def top2_road_global():
    return mentions(d, [1])


@report.finding("X2_14")
def top2_crime_global():
    return mentions(d, [3])


@report.finding("X2_15")
def top2_health_global():
    return mentions(d, [9])


@report.finding("X2_16")
def top2_finances_global():
    return mentions(d, [5])


@report.finding("X2_17")
def top2_economy_global():
    return mentions(d, [6])


TOP2_CODES = {  # Chart 2.1 categories (L3_A / L3_B codes)
    "none": 19, "road": 1, "crime": 3, "health": 9, "other": 18, "economy": 6, "financial": 5, "climate": 16,
    "cooking": 4, "other_transport": 2, "work": 14, "politics": 7, "food": 12, "drugs": 10, "pollution": 13,
    "mental": 15, "water": 11, "internet": 8, "drowning": 17,
}


@report.finding("C2_1")
def top2_global():
    return {name: mentions(d, [code]) for name, code in TOP2_CODES.items()}


@report.finding("X2_18")
def low_income_financial():
    return pct(d[d.CountryIncomeLevel == 1], "t2_financial", [1])


CHART_2_2 = ["road", "health", "crime", "financial", "environment", "food_water", "political"]


@report.finding("C2_2")
def top2_by_region():
    out = {}
    for name in CHART_2_2:
        out.update({f"{region}_{name}": v
                    for region, v in keyed(pct(d, f"t2_{name}", [1], by="GlobalRegion"), REGION).items()})
    return out


@report.finding("X2_19")
def road_people():
    return population(d.t2_road == 1)


@report.finding("C2_3")
def road_by_country():
    return t2_country["road"]


@report.finding("X2_20")
def countries_road_over_50():
    return int((t2_country["road"] > 50).sum())


@report.finding("X2_21")
def road_rwanda_madagascar():
    return t2_country["road"][["RWA", "MDG"]]


@report.finding("X2_22")
def road_australia():
    return t2_country["road"]["AUS"]


@report.finding("C2_4")
def road_by_gender_and_age():
    groups = {(s, a): f"{sex}_{age}" for s, sex in SEX.items()
              for a, age in {1: "15_29", 2: "30_49", 3: "50_64", 4: "65plus"}.items()}
    return keyed(pct(d, "t2_road", [1], by=["Gender", "AgeGroups4"]), groups)


@report.finding("X2_23")
def road_by_income_feelings():
    return keyed(pct(d, "t2_road", [1], by="IncomeFeelings"), {1: "comfortable", 3: "difficult", 4: "very_difficult"})


@report.finding("X2_24")
def road_by_education():
    return keyed(pct(d, "t2_road", [1], by="Education"), {3: "educ_16plus", 1: "educ_0_8"})


@report.finding("X2_25")
def road_urban_rural():
    return keyed(pct(d, "t2_road", [1], by="Urbanicity2"), {2: "urban", 1: "rural"})


@report.finding("X2_26")
def crime_global():
    return mentions(d, [3])


@report.finding("X2_27")
def crime_afghanistan():
    return t2_country["crime"]["AFG"]


@report.finding("X2_28")
def crime_brazil():
    return t2_country["crime"]["BRA"]


@report.finding("C2_5")
def crime_map():
    return world_map(t2_country["crime"])


@report.finding("X2_29")
def crime_countries_over_50():
    over = t2_country["crime"][t2_country["crime"] >= 50].index
    region = d.groupby("COUNTRY_ISO3").GlobalRegion.first()
    return {"n50": len(over), "latam": int((region[over] == 5).sum()),
            "latam_pct": pct(d[d.GlobalRegion == 5], "t2_crime", [1])}


@report.finding("X2_30")
def crime_south_africa():
    return t2_country["crime"]["ZAF"]


@report.finding("C2_6")
def crime_by_region_and_gender():
    total = {f"{r}_total": v for r, v in keyed(pct(d, "t2_crime", [1], by="GlobalRegion"), REGION).items()}
    groups = {(g, s): f"{region}_{sex}" for g, region in REGION.items() for s, sex in SEX.items()}
    return {**total, **keyed(pct(d, "t2_crime", [1], by=["GlobalRegion", "Gender"]), groups)}


@report.finding("X2_31")
def crime_aus_nz_by_gender():
    return keyed(pct(d[d.GlobalRegion == 15], "t2_crime", [1], by="Gender"), SEX)


@report.finding("X2_32")
def safe_walking_australia_new_zealand():
    g = merge_gallup(d, ["WP113"])
    walk = pct(g, "WP113", [1], by=["COUNTRY_ISO3", "Gender"]).unstack()
    gap = walk[1] - walk[2]
    out = {f"{iso}_{sex}": walk.loc[iso, code] for iso in ("AUS", "NZL") for code, sex in ((1, "men"), (2, "women"))}
    return {**out, "AUS_gap": gap["AUS"], "NZL_gap": gap["NZL"], "largest": ranked(gap, 1)[1]}


GINI = world_bank("SI.POV.GINI", latest_upto=2018)


@report.finding("X2_33")
def crime_gini_correlation():
    return correlation(t2_country["crime"], GINI)[0]


@report.finding("X2_34")
def crime_gini_countries():
    return correlation(t2_country["crime"], GINI)[1]


@report.finding("C2_7")
def crime_gini_scatter():
    # No values are printed in the scatter plot; the labelled countries are returned for reference.
    labelled = ["ZAF", "BRA", "NGA", "CHN", "MEX", "IND", "USA", "IDN", "GBR", "SVN"]
    return {**{f"{iso}_pct": t2_country["crime"][iso] for iso in labelled},
            **{f"{iso}_gini": GINI.get(iso, np.nan) for iso in labelled}}


@report.finding("C2_8")
def health_map():
    return world_map(t2_country["health"])


@report.finding("X2_35")
def health_by_age():
    return keyed(pct(d, "t2_health", [1], by="AgeGroups4"), {4: "65plus", 1: "15_29"})


@report.finding("X2_36")
def health_by_gender():
    return keyed(pct(d, "t2_health", [1], by="Gender"), SEX)


@report.finding("X2_37")
def health_death_rate_correlation():
    return correlation(t2_country["health"], world_bank("SP.DYN.CDRT.IN", year=2018))[0]


@report.finding("C2_9")
def health_injury_scatter():
    # No values are printed in the scatter plot; the labelled countries are returned for reference.
    injury = world_bank("SH.DTH.INJR.ZS", year=2016)
    labelled = ["IRQ", "LBY", "AFG", "BRA", "IND", "MEX", "NGA", "CHN", "MMR", "ZAF", "POL", "IDN", "USA", "SRB",
                "GBR", "BGR"]
    return {**{f"{iso}_pct": t2_country["health"][iso] for iso in labelled},
            **{f"{iso}_injury": injury.get(iso, np.nan) for iso in labelled}}


@report.finding("X2_38")
def financial_global():
    return mentions(d, [5, 6])


@report.finding("X2_39")
def financial_rwanda():
    return t2_country["financial"]["RWA"]


@report.finding("X2_40")
def financial_lithuania():
    return t2_country["financial"]["LTU"]


@report.finding("C2_10")
def financial_by_country():
    return t2_country["financial"]


@report.finding("X2_41")
def environment_global():
    return mentions(d, [13, 16])


@report.finding("X2_42")
def environment_nepal():
    return t2_country["environment"]["NPL"]


@report.finding("C2_11")
def environment_by_country():
    return t2_country["environment"]


@report.finding("X2_43")
def climate_very_serious():
    return pct(d, "L5", [1])


@report.finding("X2_44")
def climate_top_threat():
    return mentions(d, [16])


@report.finding("X2_45")
def political_global():
    return mentions(d, [7])


@report.finding("X2_46")
def political_lebanon_hong_kong():
    return t2_country["political"][["LBN", "HKG"]]


@report.finding("X2_47")
def countries_political_over_20():
    return int((t2_country["political"] > 20).sum())


@report.finding("C2_12")
def political_by_country():
    return t2_country["political"]


@report.finding("X2_48")
def political_spotlight():
    return t2_country["political"][["KOR", "BEL", "USA", "ESP", "CYP"]]


@report.finding("X2_49")
def food_water_global():
    return mentions(d, [11, 12])


@report.finding("X2_50")
def food_water_people():
    return population(d.t2_food_water == 1)


@report.finding("X2_51")
def water_global():
    return mentions(d, [11])


@report.finding("X2_52")
def food_global():
    return mentions(d, [12])


@report.finding("C2_13")
def food_water_by_country():
    return t2_country["food_water"]


@report.finding("X2_53")
def food_water_luxembourg_france():
    return t2_country["food_water"][["LUX", "FRA"]]


@report.finding("X2_54")
def france_government_food():
    return by_country(d, "L16A", [1])["FRA"]


@report.finding("X2_55")
def food_water_drinking_water_correlation():
    return correlation(t2_country["food_water"], world_bank("SH.H2O.BASW.ZS", year=2017))[0]


@report.finding("X2_56")
def food_water_disasters_correlation():
    return correlation(t2_country["food_water"], world_bank("EN.CLC.MDAT.ZS", latest_upto=2019))[0]


@report.finding("X2_57")
def no_risk_first_ch2():
    return pct(d, "L3_A", [19])


@report.finding("X2_58")
def no_risk_second_ch2():
    return pct(d, "second_response", [19])


no_risk_majority = t2_country["none"][t2_country["none"] > 50].index


@report.finding("X2_59")
def countries_no_risk_majority():
    return len(no_risk_majority)


@report.finding("X2_60")
def no_risk_majority_not_free():
    return int((freedom_house().set_index("iso3").status.reindex(no_risk_majority) == "NF").sum())


@report.finding("X2_61")
def no_risk_majority_partly_free():
    return int((freedom_house().set_index("iso3").status.reindex(no_risk_majority) == "PF").sum())


@report.finding("C2_14")
def no_risk_by_country():
    return t2_country["none"]


@report.finding("X2_62")
def no_risk_by_education():
    return keyed(pct(d, "t2_none", [1], by="Education"), {1: "educ_0_8", 3: "educ_16plus"})


@report.finding("X2_63")
def no_risk_freedom_correlation():
    return correlation(t2_country["none"], freedom_house().set_index("iso3").total)[0]


# ==============================================================================
# Part 2: Chapters 3-5
# ==============================================================================

p2_SEX = {2: "women", 1: "men"}  # Gender: 1 = Male, 2 = Female
p2_DK = [98, 99]
p2_REGIONS = {  # GlobalRegion codes
    1: "east_africa", 2: "central_west_africa", 3: "north_africa", 4: "southern_africa", 5: "latin_america",
    6: "north_america", 7: "central_asia", 8: "east_asia", 9: "southeast_asia", 10: "south_asia",
    11: "middle_east", 12: "east_europe", 13: "northwest_europe", 14: "south_europe", 15: "aus_nz",
}
p2_INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # CountryIncomeLevel
p2_EDU = {1: "edu_0_8", 2: "edu_9_15", 3: "edu_16plus"}  # Education (9 = DK/refused, not charted)
p2_LIKELY = {"traffic": "L9A", "attacked": "L9B", "lightning": "L9E", "drowning": "L9D", "aeroplane": "L9C"}
p2_WORRY = {"food": "L6A", "water": "L6B", "crime": "L6C", "weather": "L6D", "power": "L6E",
            "appliances": "L6F", "mental": "L6G"}
p2_HARM = {"food": "L8A", "water": "L8B", "crime": "L8C", "weather": "L8D", "power": "L8E",
           "appliances": "L8F", "mental": "L8G"}
p2_SOURCES = {"family": "L13A", "labels": "L13F", "medical": "L13B", "news": "L13C", "authority": "L13E",
              "internet": "L13D", "famous": "L13G", "religious": "L13H"}
p2_TRUST_CODES = {"family": 1, "medical": 2, "news": 3, "internet": 4, "authority": 5, "labels": 6,
                  "famous": 7, "religious": 8}  # L14 codes
p2_BAG = {"neighbour": "L17A", "stranger": "L17B", "police": "L17C"}
p2_OCC = {"business_owner": 1, "vendor": 2, "professional": 3, "manager": 4, "clerical": 5, "service": 6,
          "construction": 7, "farmer": 8, "other": 97, "dk": 98, "refused": 99}  # EMP8B codes
p2_RISK_AT_WORK = {"machinery": "L20A", "fire": "L20B", "chemicals": "L20C", "violence": "L20D", "trips": "L20E"}
p2_HARM_AT_WORK = {"machinery": "L21A", "fire": "L21B", "chemicals": "L21C", "violence": "L21D", "trips": "L21E"}

d = add_columns(d, [
    "WPID_RANDOM", "PROJWT", "WGT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "REG_GLOBAL", "Gender",
    "Education", "AgeGroups4", "IncomeFeelings", "worry_index_published", "experience_index_published",
    "L10", "L12", "L14", "L15", "L19", "L22", "L23", "L25", "EMP8B",
    *p2_LIKELY.values(), *p2_WORRY.values(), *p2_HARM.values(), *p2_SOURCES.values(), *p2_BAG.values(),
    *p2_RISK_AT_WORK.values(), *p2_HARM_AT_WORK.values(),
])

# --- Derived variables ---------------------------------------------------------

# Chapter 3. The Worry Index and Experience of Harm Index are published on a
# 0-100 scale; the data holds them on 0-1.
d["p2_worry_100"] = 100 * d.worry_index_published
d["p2_experience_100"] = 100 * d.experience_index_published
# Numeracy (L12): 3 = correct; "incorrect" in the lightning comparison (page 58)
# groups wrong answers with don't know, as the report does on page 53.
d["p2_numeracy"] = np.where(d.L12.eq(3), 1, np.where(d.L12.notna(), 2, np.nan))
# Likelihood ratings (L9A-E, 0-10): don't know / refused (98, 99) set to missing
# for averages; the Chart 3.3 percentages keep them in the base.
for p2_v in p2_LIKELY.values():
    d["p2_" + p2_v + "_score"] = d[p2_v].where(d[p2_v] <= 10)
d["p2_likely_mean"] = d[["p2_" + v + "_score" for v in p2_LIKELY.values()]].mean(axis=1)

# Chapter 4. Social trust score (page 77): very likely = 3, somewhat likely = 2,
# not likely at all = 1, averaged over the three lost-bag questions; respondents
# must answer all three (the police question was not asked in three countries,
# which leaves the 139 countries of footnote 17).
p2_bag = d[list(p2_BAG.values())].where(d[list(p2_BAG.values())] <= 3)
d["p2_social_trust"] = (4 - p2_bag).mean(axis=1, skipna=False)

# Seat belt laws: WHO Global status report on road safety 2018, Table A7 (see
# README). Countries not in the WHO table count as having no law in Chart 4.6.
# The WHO table is not redistributed here (see reports/external/README.md), so
# the law columns are added the first time a finding needs them.


@lru_cache(maxsize=None)
def p2_add_seatbelt_laws():
    p2_who = pd.read_csv(external_path("core_world_risk_poll_2019__who_seatbelt_laws.csv"), index_col="iso3")
    d["p2_national_law"] = d.COUNTRY_ISO3.map(p2_who.national_law)
    d["p2_all_occupants"] = d.COUNTRY_ISO3.map(p2_who.all_occupants)
    d["p2_seatbelt_law"] = np.select(  # Chart 4.8: 1 none, 2 partial (not all occupants), 3 full (all occupants)
        [d.p2_national_law.eq("No"), d.p2_all_occupants.eq("No"), d.p2_all_occupants.eq("Yes")], [1, 2, 3],
        default=np.nan)
    return True

# Chapter 5. Workers: employed full or part time, the respondents asked the
# work questions (L19-L21; L22-L25 only of those who work for an employer).
p2_w = d[d.L19.notna()].copy()
p2_w["n_harm_types"] = p2_w[list(p2_HARM_AT_WORK.values())].eq(1).sum(axis=1)  # 0-5 types of harm at work
p2_w["three_plus"] = np.where(p2_w.n_harm_types >= 3, 1, 2)
p2_w["any_risk"] = np.where(p2_w[list(p2_RISK_AT_WORK.values())].eq(1).any(axis=1), 1, 2)
p2_w["low_income"] = np.where(p2_w.CountryIncomeLevel.eq(1), 1, 2)

# --- Helpers -------------------------------------------------------------------


def p2_keyed(values, mapping):
    """Rename a Series indexed by codes to readable keys, dropping unmapped codes."""
    return {mapping[k]: v for k, v in values.items() if k in mapping}


def p2_pct_by(df, var, codes, by, mapping, exclude=None):
    """% with `var` in `codes` for each group of `by`, keyed by `mapping`."""
    return p2_keyed(pct(df, var, codes, by=by, exclude=exclude), mapping)


def p2_region_pct(df, var, codes, exclude=None):
    return p2_pct_by(df, var, codes, "GlobalRegion", p2_REGIONS, exclude)


def p2_with_world(df, var, codes):
    """Chart 4.1 / 4.6 layout: {"world": %, "low": %, ...}."""
    return {"world": pct(df, var, codes), **p2_pct_by(df, var, codes, "CountryIncomeLevel", p2_INCOME)}


def p2_sorted_keys(keys):
    return ", ".join(sorted(keys))


# =============================================================================
# Chapter 3: The risk perception gap
# =============================================================================


@report.finding("X3_01")
def p2_numeracy_correct():
    return pct(d, "L12", [3])


@report.finding("X3_02")
def p2_numeracy_incorrect():
    return pct(d, "L12", [1, 2])


@report.finding("X3_03")
def p2_numeracy_dont_know():
    return pct(d, "L12", [98])


@report.finding("X3_04")
def p2_numeracy_incorrect_tertiary():
    return pct(d[d.Education == 3], "L12", [1, 2])


@report.finding("X3_05")
def p2_numeracy_dont_know_tertiary():
    return pct(d[d.Education == 3], "L12", p2_DK)


@report.finding("X3_06")
def p2_numeracy_by_sex():
    return p2_pct_by(d, "L12", [3], "Gender", p2_SEX)


@report.finding("C3_1")
def p2_numeracy_by_sex_education():
    r = pct(d, "L12", [3], by=["Gender", "Education"])
    return {f"{sex}_{edu}": r[(s, e)] for s, sex in p2_SEX.items() for e, edu in p2_EDU.items()}


@report.finding("X3_07")
def p2_numeracy_regions_text():
    r = p2_region_pct(d, "L12", [3])
    return {k: r[k] for k in ("aus_nz", "north_america", "northwest_europe", "latin_america", "south_asia")}


@report.finding("X3_08")
def p2_numeracy_sub_saharan():
    r = p2_region_pct(d, "L12", [3])
    return {k: r[k] for k in ("east_africa", "central_west_africa", "southern_africa")}


@report.finding("X3_09")
def p2_bigger_not_above_smaller():
    bigger, smaller = p2_region_pct(d, "L12", [1]), p2_region_pct(d, "L12", [2])
    return p2_sorted_keys(k for k in bigger if bigger[k] <= smaller[k])


@report.finding("C3_2")
def p2_numeracy_by_region():
    table = distribution(d, "L12", by="GlobalRegion")
    cats = {"same": [3], "bigger": [1], "smaller": [2], "dk": p2_DK}
    return {f"{region}_{cat}": table.loc[code, table.columns.intersection(codes)].sum()
            for code, region in p2_REGIONS.items() for cat, codes in cats.items()}


@report.finding("X3_10")
def p2_likelihood_means():
    return {risk: wmean(d, "p2_" + var + "_score") for risk, var in p2_LIKELY.items()}


@report.finding("C3_3")
def p2_likelihood_distribution():
    cats = {"r0": [0], "r1_4": [1, 2, 3, 4], "r5": [5], "r6_9": [6, 7, 8, 9], "r10": [10]}
    out = {}
    for risk, var in p2_LIKELY.items():
        for cat, codes in cats.items():
            out[f"{risk}_{cat}"] = pct(d, var, codes)
        out[f"{risk}_mean"] = wmean(d, "p2_" + var + "_score")
    return out


@report.finding("X3_11")
def p2_lightning_by_numeracy():
    r = wmean(d, "p2_L9E_score", by="p2_numeracy")
    return {"correct": r[1], "incorrect": r[2]}


@report.finding("C3_4")
def p2_likelihood_by_region():
    out = {}
    for risk, var in p2_LIKELY.items():
        out[f"world_{risk}"] = wmean(d, "p2_" + var + "_score")
        for region, value in p2_keyed(wmean(d, "p2_" + var + "_score", by="GlobalRegion"), p2_REGIONS).items():
            out[f"{region}_{risk}"] = value
    return out


@report.finding("X3_12")
def p2_country_share_of_variance():
    # Between-country share of the variance (eta squared, %) of each person's
    # mean likelihood rating, weighted with the within-country weight WGT
    # (PROJWT is proportional to WGT within a country, so the country means
    # are the same; using PROJWT for the totals gives 17%).
    g = d[d.p2_likely_mean.notna()]
    grand = wmean(g, "p2_likely_mean", weight="WGT")
    fitted = g.COUNTRY_ISO3.map(wmean(g, "p2_likely_mean", weight="WGT", by="COUNTRY_ISO3"))
    return 100 * (g.WGT * (fitted - grand) ** 2).sum() / (g.WGT * (g.p2_likely_mean - grand) ** 2).sum()


@report.finding("X3_13")
def p2_very_worried():
    return {risk: pct(d, var, [1]) for risk, var in p2_WORRY.items()}


@report.finding("C3_5")
def p2_worried_vs_experienced():
    out = {}
    for risk in p2_WORRY:
        worried, experienced = pct(d, p2_WORRY[risk], [1]), pct(d, p2_HARM[risk], [1])
        out.update({f"{risk}_worried": worried, f"{risk}_experienced": experienced,
                    f"{risk}_gap": worried - experienced})
    return out


@report.finding("X3_14")
def p2_worry_index():
    return wmean(d, "p2_worry_100")


@report.finding("X3_15")
def p2_experience_index():
    return wmean(d, "p2_experience_100")


@report.finding("X3_16")
def p2_indices_regions_text():
    worry = p2_keyed(wmean(d, "p2_worry_100", by="GlobalRegion"), p2_REGIONS)
    experience = p2_keyed(wmean(d, "p2_experience_100", by="GlobalRegion"), p2_REGIONS)
    return {"southern_africa_worry": worry["southern_africa"], "latin_america_worry": worry["latin_america"],
            "southern_africa_experience": experience["southern_africa"]}


@report.finding("C3_6")
def p2_indices_by_region():
    worry = p2_keyed(wmean(d, "p2_worry_100", by="GlobalRegion"), p2_REGIONS)
    experience = p2_keyed(wmean(d, "p2_experience_100", by="GlobalRegion"), p2_REGIONS)
    out = {}
    for region in p2_REGIONS.values():
        out.update({f"{region}_worry": worry[region], f"{region}_experience": experience[region],
                    f"{region}_gap": worry[region] - experience[region]})
    return out


def p2_country_indices():
    return pd.DataFrame({"worry": wmean(d, "p2_worry_100", by="COUNTRY_ISO3"),
                         "experience": wmean(d, "p2_experience_100", by="COUNTRY_ISO3")})


@report.finding("C3_7")
def p2_indices_by_country():
    # Scatter chart with country labels only: no published values to compare.
    c = p2_country_indices()
    return {**{f"{k}_worry": v for k, v in c.worry.items()}, **{f"{k}_experience": v for k, v in c.experience.items()}}


@report.finding("X3_17")
def p2_mean_country_gap():
    c = p2_country_indices()
    return (c.worry - c.experience).mean()


@report.finding("X3_18")
def p2_lowest_worry_country():
    return p2_country_indices().worry.idxmin()


@report.finding("X3_19")
def p2_sweden():
    c = p2_country_indices().loc["SWE"]
    return {"worry": c.worry, "experience": c.experience, "gap": c.worry - c.experience}


@report.finding("X3_20")
def p2_indices_by_sex():
    worry = p2_keyed(wmean(d, "p2_worry_100", by="Gender"), p2_SEX)
    experience = p2_keyed(wmean(d, "p2_experience_100", by="Gender"), p2_SEX)
    return {"worry_women": worry["women"], "worry_men": worry["men"],
            "experience_men": experience["men"], "experience_women": experience["women"]}


@report.finding("X3_21")
def p2_worry_by_region_and_sex():
    r = wmean(d, "p2_worry_100", by=["GlobalRegion", "Gender"])
    regions = {6: "north_america", 15: "aus_nz", 14: "south_europe", 4: "southern_africa", 5: "latin_america"}
    return {f"{region}_{sex}": r[(code, s)] for code, region in regions.items() for s, sex in p2_SEX.items()}


@report.finding("X3_22")
def p2_worry_by_income_feelings():
    r = wmean(d, "p2_worry_100", by="IncomeFeelings")
    return {"comfortable": r[1], "very_difficult": r[4]}


# =============================================================================
# Chapter 4: Influencing understanding of risk
# =============================================================================


@report.finding("X4_01")
def p2_wear_seatbelt():
    return pct(d, "L10", [1])


@report.finding("X4_02")
def p2_government_require_rules():
    return pct(d, "L15", [1])


@report.finding("X4_03")
def p2_food_sources():
    return {src: pct(d, var, [1]) for src, var in p2_SOURCES.items()}


@report.finding("C4_1")
def p2_food_sources_by_income():
    return {f"{src}_{g}": v for src, var in p2_SOURCES.items() for g, v in p2_with_world(d, var, [1]).items()}


@report.finding("X4_04")
def p2_low_income_famous_religious():
    low = d[d.CountryIncomeLevel == 1]
    return {"famous": pct(low, "L13G", [1]), "religious": pct(low, "L13H", [1])}


@report.finding("X4_05")
def p2_famous_by_region_text():
    r = p2_region_pct(d, "L13G", [1])
    return {k: r[k] for k in ("east_africa", "central_west_africa", "southern_africa", "south_asia", "southeast_asia")}


def p2_religion_important():
    # Gallup World Poll item WP119 "Is religion an important part of your daily
    # life?" (1 = yes, 2 = no); not in the public release.
    return merge_gallup(d, ["WP119"])


@report.finding("X4_06")
def p2_religion_east_africa():
    g = p2_religion_important()
    return pct(g[g.GlobalRegion == 1], "WP119", [1])


@report.finding("X4_07")
def p2_religion_eu():
    g = p2_religion_important()
    return pct(g[g.REG_GLOBAL == 1], "WP119", [1])  # REG_GLOBAL 1 = European Union


@report.finding("C4_2")
def p2_food_sources_by_region():
    return {f"{region}_{src}": v for src, var in p2_SOURCES.items() for region, v in p2_region_pct(d, var, [1]).items()}


@report.finding("X4_08")
def p2_trust_most_text():
    return {src: pct(d, "L14", [p2_TRUST_CODES[src]]) for src in ("family", "medical", "authority", "famous", "religious")}


@report.finding("C4_3")
def p2_use_and_trust_most():
    out = {}
    for src, var in p2_SOURCES.items():
        out[f"{src}_use"] = pct(d, var, [1])
        out[f"{src}_trust"] = pct(d, "L14", [p2_TRUST_CODES[src]])
    return out


@report.finding("C4_4")
def p2_trust_most_by_sex_education():
    groups = {"world": d, **{sex: d[d.Gender == s] for s, sex in p2_SEX.items()},
              **{edu: d[d.Education == e] for e, edu in p2_EDU.items()}}
    return {f"{grp}_{src}": pct(df, "L14", [p2_TRUST_CODES[src]])
            for grp, df in groups.items() for src in ("family", "medical", "authority")}


@report.finding("X4_09")
def p2_lost_bag_very_likely():
    return {who: pct(d, var, [1]) for who, var in p2_BAG.items()}


@report.finding("X4_10")
def p2_lost_bag_high_income():
    high = d[d.CountryIncomeLevel == 4]
    return {"police": pct(high, "L17C", [1]), "neighbour": pct(high, "L17A", [1])}


def p2_social_trust_by_country():
    c = pd.DataFrame({"social_trust": wmean(d, "p2_social_trust", by="COUNTRY_ISO3"),
                      "trust_authority": pct(d, "L14", [5], by="COUNTRY_ISO3")})
    return c.dropna()


@report.finding("C4_5")
def p2_social_trust_chart():
    # Scatter chart with country labels only: no published values to compare.
    c = p2_social_trust_by_country()
    return {**{f"{k}_social_trust": v for k, v in c.social_trust.items()},
            **{f"{k}_trust_authority": v for k, v in c.trust_authority.items()}}


@report.finding("X4_11")
def p2_social_trust_correlation():
    c = p2_social_trust_by_country()
    return c.social_trust.corr(c.trust_authority)


@report.finding("X4_12")
def p2_social_trust_countries():
    return len(p2_social_trust_by_country())


@report.finding("X4_13")
def p2_countries():
    return d.COUNTRY_ISO3.nunique()


def p2_no_law_countries():
    p2_add_seatbelt_laws()
    return pct(d[d.p2_national_law == "No"], "L10", [1], by="COUNTRY_ISO3")


@report.finding("X4_14")
def p2_no_law_count():
    return len(p2_no_law_countries())


@report.finding("X4_15")
def p2_no_law_most_wear():
    r = p2_no_law_countries()
    return p2_sorted_keys(r[r > 50].index)


@report.finding("X4_16")
def p2_no_law_under_half_wear():
    r = p2_no_law_countries()
    return p2_sorted_keys(r[r < 50].index)


@report.finding("X4_17")
def p2_do_not_wear_seatbelt():
    return pct(d, "L10", [2])


@report.finding("C4_6")
def p2_seatbelt_by_income():
    p2_add_seatbelt_laws()
    countries = d.drop_duplicates("COUNTRY_ISO3")[["COUNTRY_ISO3", "CountryIncomeLevel", "p2_national_law"]]
    has_law = 100 * countries.p2_national_law.eq("Yes")
    law = {"world": has_law.mean(), **p2_keyed(has_law.groupby(countries.CountryIncomeLevel).mean(), p2_INCOME)}
    return {**{f"wear_{g}": v for g, v in p2_with_world(d, "L10", [1]).items()},
            **{f"law_{g}": v for g, v in law.items()}}


@report.finding("X4_18")
def p2_seatbelt_by_education_text():
    r = p2_pct_by(d, "L10", [1], "Education", p2_EDU)
    return {"edu_0_8": r["edu_0_8"], "edu_16plus": r["edu_16plus"]}


@report.finding("C4_7")
def p2_seatbelt_by_income_sex_education():
    out = {}
    for code, g in p2_INCOME.items():
        sub = d[d.CountryIncomeLevel == code]
        out.update({f"{g}_{k}": v for k, v in p2_pct_by(sub, "L10", [1], "Gender", p2_SEX).items()})
        out.update({f"{g}_{k}": v for k, v in p2_pct_by(sub, "L10", [1], "Education", p2_EDU).items()})
    return out


def p2_seatbelt_by_law():
    # Average of the country percentages in each law group (the text: "an
    # average of 58% of people"); countries not in the WHO table are left out.
    country = pct(d, "L10", [1], by="COUNTRY_ISO3")
    p2_add_seatbelt_laws()
    group = d.drop_duplicates("COUNTRY_ISO3").set_index("COUNTRY_ISO3").p2_seatbelt_law
    return p2_keyed(country.groupby(group).mean(), {1: "none", 2: "partial", 3: "full"})


@report.finding("X4_19")
def p2_seatbelt_by_law_text():
    return p2_seatbelt_by_law()


@report.finding("C4_8")
def p2_seatbelt_by_law_chart():
    return p2_seatbelt_by_law()


@report.finding("X4_20")
def p2_government_rules_regions():
    r = p2_region_pct(d, "L15", [1])
    return {"south_europe": r["south_europe"], "south_asia": r["south_asia"],
            "IND": pct(d[d.COUNTRY_ISO3 == "IND"], "L15", [1])}


@report.finding("X4_21")
def p2_government_rules_lowest_region():
    r = p2_region_pct(d, "L15", [1])
    return min(r, key=r.get)


# =============================================================================
# Chapter 5: Risk at work
# =============================================================================


@report.finding("X5_01")
def p2_occupation_text():
    r = distribution(p2_w, "EMP8B")
    return {k: r[p2_OCC[k]] for k in ("farmer", "vendor", "manager")}


@report.finding("C5_1")
def p2_occupation():
    r = distribution(p2_w, "EMP8B")
    return {k: r[code] for k, code in p2_OCC.items()}


@report.finding("X5_02")
def p2_ever_injured():
    return pct(p2_w, "L19", [1])


@report.finding("X5_03")
def p2_ever_injured_people():
    return p2_w.PROJWT[p2_w.L19 == 1].sum()


def p2_injured_by_occupation(df=p2_w):
    return p2_pct_by(df, "L19", [1], "EMP8B", {v: k for k, v in p2_OCC.items()})


@report.finding("X5_04")
def p2_injured_farmers():
    return p2_injured_by_occupation()["farmer"]


@report.finding("X5_05")
def p2_injured_construction():
    return p2_injured_by_occupation()["construction"]


def p2_violence_risk_by_country():
    return pct(p2_w, "L20D", [1], by="COUNTRY_ISO3")


@report.finding("X5_06")
def p2_france_violence_risk():
    return p2_violence_risk_by_country()["FRA"]


@report.finding("X5_07")
def p2_violence_risk_regions_key_finding():
    r = p2_region_pct(p2_w, "L20D", [1])
    return {"northwest_europe": r["northwest_europe"], "aus_nz": r["aus_nz"]}


@report.finding("X5_08")
def p2_mental_health_by_injury():
    r = pct(p2_w, "L8G", [1], by="L19")
    return {"injured": r[1], "not_injured": r[2]}


@report.finding("X5_09")
def p2_free_to_report():
    return pct(d, "L22", [1])


@report.finding("X5_10")
def p2_injured_by_view_of_rules():
    r = pct(p2_w, "L19", [1], by="L25")
    return {"difficult": r[2], "good": r[1]}


@report.finding("X5_11")
def p2_rules_good_by_education_text():
    r = p2_pct_by(p2_w, "L25", [1], "Education", p2_EDU)
    return {"edu_16plus": r["edu_16plus"], "edu_0_8": r["edu_0_8"]}


@report.finding("X5_12")
def p2_injured_by_income():
    r = p2_pct_by(p2_w, "L19", [1], "CountryIncomeLevel", p2_INCOME)
    return {"low": r["low"], "high": r["high"]}


def p2_injured_by_country():
    return pct(p2_w, "L19", [1], by="COUNTRY_ISO3")


@report.finding("C5_2")
def p2_injured_map():
    # Every country's value (the map), plus the legend ends: the lowest and
    # highest country values.
    r = p2_injured_by_country()
    return {**r.to_dict(), "legend_min": r.min(), "legend_max": r.max()}


@report.finding("T5_1")
def p2_injured_over_half():
    r = p2_injured_by_country()
    return r[r > 50].sort_values(ascending=False).to_dict()


@report.finding("X5_13")
def p2_injured_over_half_count():
    return int((p2_injured_by_country() > 50).sum())


@report.finding("X5_14")
def p2_injured_sierra_leone():
    return p2_injured_by_country()["SLE"]


@report.finding("C5_3")
def p2_injured_by_profession():
    r = p2_injured_by_occupation()
    return {k: r[k] for k in ("farmer", "construction", "business_owner", "vendor", "service", "professional",
                              "manager", "clerical")}


@report.finding("C5_4")
def p2_injured_construction_vs_farming():
    r = pct(p2_w, "L19", [1], by=["GlobalRegion", "EMP8B"])
    out = {}
    for code, region in p2_REGIONS.items():
        c, f = r[(code, 7)], r[(code, 8)]
        out.update({f"{region}_construction": c, f"{region}_farmer": f, f"{region}_gap": abs(c - f)})
    return out


@report.finding("X5_15")
def p2_injured_by_sex():
    return p2_pct_by(p2_w, "L19", [1], "Gender", p2_SEX)


@report.finding("C5_5")
def p2_injured_by_sex_profession():
    out = {}
    for s, sex in p2_SEX.items():
        r = p2_injured_by_occupation(p2_w[p2_w.Gender == s])
        out.update({f"{sex}_{k}": r[k] for k in ("business_owner", "vendor", "professional", "manager", "clerical",
                                                  "service", "construction", "farmer")})
    return out


@report.finding("X5_16")
def p2_injured_south_asia_by_sex():
    return p2_pct_by(p2_w[p2_w.GlobalRegion == 10], "L19", [1], "Gender", p2_SEX)


@report.finding("X5_17")
def p2_injured_farmers_south_asia_by_sex():
    # The text describes these as the shares of men and women "who work in the
    # region's large agricultural sector"; they are the injury rates among
    # Southern Asia's agricultural workers (see README).
    farmers = p2_w[(p2_w.GlobalRegion == 10) & (p2_w.EMP8B == 8)]
    return p2_pct_by(farmers, "L19", [1], "Gender", p2_SEX)


@report.finding("X5_18")
def p2_injured_sri_lanka_by_sex():
    return p2_pct_by(p2_w[p2_w.COUNTRY_ISO3 == "LKA"], "L19", [1], "Gender", p2_SEX)


@report.finding("X5_19")
def p2_injured_by_education_text():
    r = p2_pct_by(p2_w, "L19", [1], "Education", p2_EDU)
    return {"edu_16plus": r["edu_16plus"], "edu_0_8": r["edu_0_8"]}


@report.finding("C5_6")
def p2_injured_by_sex_education():
    r = pct(p2_w, "L19", [1], by=["Gender", "Education"])
    return {f"{sex}_{edu}": r[(s, e)] for s, sex in p2_SEX.items() for e, edu in p2_EDU.items()}


@report.finding("X5_20")
def p2_risks_at_work():
    return {risk: pct(p2_w, var, [1]) for risk, var in p2_RISK_AT_WORK.items()}


@report.finding("X5_21")
def p2_any_risk_low_income():
    r = pct(p2_w, "any_risk", [1], by="low_income")
    return {"low": r[1], "not_low": r[2]}


@report.finding("X5_22")
def p2_fire_bangladesh():
    return pct(p2_w[p2_w.COUNTRY_ISO3 == "BGD"], "L20B", [1])


def p2_risks_by_region():
    risks = {k: v for k, v in p2_RISK_AT_WORK.items() if k != "trips"}
    return pd.DataFrame({risk: pd.Series(p2_region_pct(p2_w, var, [1])) for risk, var in risks.items()})


@report.finding("C5_7")
def p2_top_risk_by_region():
    # Value of every risk (excluding trips and falls) in each region, and the
    # top one(s): the risks whose rounded value equals the rounded maximum.
    t = p2_risks_by_region()
    out = {f"{region}_{risk}": t.loc[region, risk] for region in t.index for risk in t.columns}
    for region, row in t.round().iterrows():
        out[f"top_{region}"] = " / ".join(sorted(row.index[row == row.max()]))
    return out


@report.finding("X5_23")
def p2_violence_risk_regions():
    r = p2_region_pct(p2_w, "L20D", [1])
    return {"northwest_europe": r["northwest_europe"], "aus_nz": r["aus_nz"]}


@report.finding("X5_24")
def p2_violence_risk_france_by_sex():
    return p2_pct_by(p2_w[p2_w.COUNTRY_ISO3 == "FRA"], "L20D", [1], "Gender", p2_SEX)


@report.finding("C5_8")
def p2_violence_risk_by_country_sex():
    countries = ["FRA", "AUS", "FIN", "BEL", "NZL", "SWE", "GBR", "NLD", "IRL", "LUX", "DNK", "NOR", "DEU", "CHE",
                 "AUT", "LTU", "LVA", "EST"]
    r = pct(p2_w, "L20D", [1], by=["COUNTRY_ISO3", "Gender"])
    allr = p2_violence_risk_by_country()
    out = {}
    for c in countries:
        out.update({f"{c}_all": allr[c], f"{c}_women": r[(c, 2)], f"{c}_men": r[(c, 1)]})
    return out


@report.finding("X5_25")
def p2_violence_risk_by_sex():
    return p2_pct_by(p2_w, "L20D", [1], "Gender", p2_SEX)


@report.finding("X5_26")
def p2_violence_risk_income_sex():
    r = pct(p2_w, "L20D", [1], by=["CountryIncomeLevel", "Gender"])
    return {"low_men": r[(1, 1)], "low_women": r[(1, 2)], "high_women": r[(4, 2)], "high_men": r[(4, 1)]}


@report.finding("C5_9")
def p2_risks_by_sex_income():
    out = {}
    for risk, var in p2_RISK_AT_WORK.items():
        r = pct(p2_w, var, [1], by=["Gender", "CountryIncomeLevel"])
        out.update({f"{sex}_{g}_{risk}": r[(s, i)] for s, sex in p2_SEX.items() for i, g in p2_INCOME.items()})
    return out


@report.finding("C5_10")
def p2_harm_at_work():
    return {k: pct(p2_w, v, [1]) for k, v in p2_HARM_AT_WORK.items()}


@report.finding("X5_27")
def p2_harm_trips():
    return pct(p2_w, "L21E", [1])


@report.finding("X5_28")
def p2_three_or_more_harms():
    r = p2_pct_by(p2_w, "three_plus", [1], "CountryIncomeLevel", p2_INCOME)
    return {"low": r["low"], "high": r["high"]}


@report.finding("X5_29")
def p2_harm_by_sex():
    out = {}
    for k in ("machinery", "fire", "violence"):
        r = p2_pct_by(p2_w, p2_HARM_AT_WORK[k], [1], "Gender", p2_SEX)
        out.update({f"{k}_men": r["men"], f"{k}_women": r["women"]})
    return out


@report.finding("X5_30")
def p2_harm_violence():
    return pct(p2_w, "L21D", [1])


@report.finding("X5_31")
def p2_harm_violence_regions_text():
    r = p2_region_pct(p2_w, "L21D", [1])
    return {k: r[k] for k in ("aus_nz", "southern_africa", "central_west_africa", "east_africa", "north_america")}


@report.finding("X5_32")
def p2_harm_violence_under_5():
    r = p2_region_pct(p2_w, "L21D", [1])
    return p2_sorted_keys(k for k, v in r.items() if v < 5)


@report.finding("C5_11")
def p2_harm_violence_by_region():
    return p2_region_pct(p2_w, "L21D", [1])


def p2_harm_violence_women_by_country():
    return pct(p2_w[p2_w.Gender == 2], "L21D", [1], by="COUNTRY_ISO3").sort_values(ascending=False)


@report.finding("X5_33")
def p2_harm_violence_countries():
    r = pct(p2_w, "L21D", [1], by=["COUNTRY_ISO3", "Gender"])
    return {"ZMB_women": r[("ZMB", 2)], "AUS_women": r[("AUS", 2)], "AUS_men": r[("AUS", 1)]}


@report.finding("X5_34")
def p2_harm_violence_women_top():
    return p2_harm_violence_women_by_country().index[0]


@report.finding("X5_35")
def p2_harm_violence_women_australia_rank():
    return list(p2_harm_violence_women_by_country().index).index("AUS") + 1


@report.finding("C5_12")
def p2_harm_by_age():
    out = {}
    for k, v in p2_HARM_AT_WORK.items():
        r = pct(p2_w, v, [1], by="AgeGroups4")
        out.update({f"{k}_age_15_29": r[1], f"{k}_age_50_64": r[3]})
    return out


@report.finding("X5_36")
def p2_mental_health_by_harm_count():
    r = pct(p2_w, "L8G", [1], by="n_harm_types")
    return {"none": r[0], "all_five": r[5]}


@report.finding("C5_13")
def p2_mental_health_by_hazard():
    out = {}
    for k in ("violence", "chemicals", "fire", "machinery"):
        r = pct(p2_w, "L8G", [1], by=p2_HARM_AT_WORK[k])
        out.update({f"{k}_yes": r[1], f"{k}_no": r[2]})
    return out


@report.finding("X5_37")
def p2_mental_health_violence():
    return pct(p2_w[p2_w.L21D == 1], "L8G", [1])


def p2_free_to_report_by_country():
    return pct(d, "L22", [1], by="COUNTRY_ISO3")


@report.finding("X5_38")
def p2_free_to_report_lowest():
    r = p2_free_to_report_by_country()
    return {"SEN": r["SEN"], "PAK": r["PAK"]}


@report.finding("X5_39")
def p2_free_to_report_under_60_count():
    return int((p2_free_to_report_by_country() < 60).sum())


@report.finding("X5_40")
def p2_free_to_report_under_60_regions():
    r = p2_region_pct(d, "L22", [1])
    return p2_sorted_keys(k for k, v in r.items() if v < 60) or "none"


@report.finding("C5_14")
def p2_free_to_report_chart():
    # Scatter against the UL Safety Index, with country labels only: no
    # published values to compare. Returns the poll side of the chart.
    return p2_free_to_report_by_country()


@report.finding("X5_41")
def p2_free_to_report_ul_correlation():
    # Needs the UL Safety Index (safety frameworks), discontinued in April 2020
    # and no longer published. Put it in reports/external/downloaded/ as
    # core_world_risk_poll_2019__ul_safety_index.csv (iso3, ul_safety_index);
    # without it the finding is reported as EXTERNAL_ONLY.
    ul = pd.read_csv(external_path("core_world_risk_poll_2019__ul_safety_index.csv")).set_index("iso3").ul_safety_index
    c = pd.concat([p2_free_to_report_by_country().rename("report"), ul], axis=1, join="inner").dropna()
    return c.report.corr(c.ul_safety_index)


def p2_free_to_report_and_gdp():
    wb = pd.read_csv(external_path("core_world_risk_poll_2019__worldbank_gdp.csv"))
    gdp = wb[(wb.indicator == "NY.GDP.PCAP.PP.CD") & (wb.year == 2019)].set_index("iso3").value
    return pd.concat([p2_free_to_report_by_country().rename("report"), np.log(gdp).rename("log_gdp")],
                     axis=1, join="inner").dropna()


@report.finding("X5_42")
def p2_free_to_report_gdp_correlation():
    c = p2_free_to_report_and_gdp()
    return c.report.corr(c.log_gdp)


@report.finding("X5_43")
def p2_free_to_report_gdp_countries():
    return len(p2_free_to_report_and_gdp())


@report.finding("X5_44")
def p2_free_to_report_by_income_feelings():
    r = pct(d, "L22", [1], by="IncomeFeelings")
    difficult = pct(d[d.IncomeFeelings.isin([3, 4])], "L22", [1])
    return {"comfortable": r[1], "difficult": difficult}


@report.finding("X5_45")
def p2_most_responsible():
    r = distribution(d, "L23")
    return {"employer": r[1], "government": r[3], "union": r[2], "nobody": r[4]}


@report.finding("X5_46")
def p2_rules_good():
    return pct(d, "L25", [1])


@report.finding("C5_15")
def p2_rules_good_by_sex_education():
    r = pct(d, "L25", [1], by=["Education", "Gender"])
    alle = pct(d, "L25", [1], by="Education")
    out = {}
    for e, edu in p2_EDU.items():
        out.update({f"{edu}_all": alle[e], f"{edu}_women": r[(e, 2)], f"{edu}_men": r[(e, 1)]})
    return out


# Employee engagement (Chart 5.16 and the text around it) is Gallup's measure,
# asked in the 2019 Gallup World Poll in 108 countries; it is not in the public
# release. GWP_EMPLOYEE_ENGAGEMENT is a placeholder name: 1 = engaged,
# 2 = not engaged, 3 = actively disengaged (see README).
p2_ENGAGEMENT = "GWP_EMPLOYEE_ENGAGEMENT"


def p2_engagement():
    return merge_gallup(d, [p2_ENGAGEMENT])


@report.finding("X5_47")
def p2_engaged_share():
    g = p2_engagement()
    return pct(g[g.L22.notna()], p2_ENGAGEMENT, [1])


@report.finding("X5_48")
def p2_free_to_report_by_engagement():
    r = pct(p2_engagement(), "L22", [1], by=p2_ENGAGEMENT)
    return {"engaged": r[1], "disengaged": r[3]}


@report.finding("X5_49")
def p2_rules_by_engagement():
    g = p2_engagement()
    good, difficult = pct(g, "L25", [1], by=p2_ENGAGEMENT), pct(g, "L25", [2], by=p2_ENGAGEMENT)
    return {"engaged_good": good[1], "engaged_difficult": difficult[1],
            "disengaged_good": good[3], "disengaged_difficult": difficult[3]}


@report.finding("X5_50")
def p2_engagement_countries():
    g = p2_engagement()
    return g.loc[g[p2_ENGAGEMENT].notna(), "COUNTRY_ISO3"].nunique()


@report.finding("C5_16")
def p2_free_to_report_by_engagement_income():
    r = pct(p2_engagement(), "L22", [1], by=["CountryIncomeLevel", p2_ENGAGEMENT])
    return {f"{g}_{k}": r[(i, code)] for i, g in p2_INCOME.items() for k, code in (("engaged", 1), ("disengaged", 3))}


# ==============================================================================
# Part 3: Chapters 6-10 and Appendix 3
# ==============================================================================

p3_DK = [98, 99]

# GlobalRegion codes -> keys used in finding ids, and the labels the charts use.
p3_REGIONS = {
    1: "east_africa", 2: "central_western_africa", 3: "northern_africa", 4: "southern_africa",
    5: "latin_america", 6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia",
    10: "southern_asia", 11: "middle_east", 12: "eastern_europe", 13: "northern_western_europe",
    14: "southern_europe", 15: "australia_nz",
}
p3_REGION_LABELS = {
    "east_africa": "Eastern Africa", "central_western_africa": "Central/Western Africa",
    "northern_africa": "Northern Africa", "southern_africa": "Southern Africa",
    "latin_america": "Latin America & Caribbean", "northern_america": "Northern America",
    "central_asia": "Central Asia", "eastern_asia": "Eastern Asia", "southeastern_asia": "Southeastern Asia",
    "southern_asia": "Southern Asia", "middle_east": "Middle East", "eastern_europe": "Eastern Europe",
    "northern_western_europe": "Northern/Western Europe", "southern_europe": "Southern Europe",
    "australia_nz": "Australia & New Zealand",
}
p3_INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # CountryIncomeLevel (9 = not classified)
p3_EDU = {1: "edu_0_8", 2: "edu_9_15", 3: "edu_16plus"}  # Education (9 = DK/refused)
p3_AGE = {1: "age_15_29", 2: "age_30_49", 3: "age_50_64", 4: "age_65plus"}  # AgeGroups4
p3_SEX = {2: "women", 1: "men"}  # Gender

# WHO sub-regions (Appendix 3), for the countries in the 2019 poll. Hong Kong,
# Kosovo, Palestine and Taiwan are not WHO member states and are not listed.
p3_WHO_SUBREGIONS = {
    "afr_d": "DZA BEN BFA CMR TCD GAB GMB GHA GIN LBR MDG MLI MRT MUS NER NGA SEN SLE TGO",
    "afr_e": "BWA COG CIV ETH KEN LSO MWI MOZ NAM RWA ZAF SWZ UGA TZA ZMB ZWE",
    "amr_a": "CAN USA",
    "amr_b": "ARG BRA CHL COL CRI DOM SLV HND JAM MEX PAN PRY URY VEN",
    "amr_d": "BOL ECU GTM NIC PER",
    "emr_b": "BHR CYP IRN JOR KWT LBN LBY SAU TUN ARE",
    "emr_d": "AFG EGY IRQ MAR PAK YEM",
    "eur_a": "AUT BEL HRV DNK FIN FRA DEU GRC IRL ISR ITA LUX MLT NLD NOR PRT SVN ESP SWE CHE GBR",
    "eur_b": "ALB ARM AZE BIH BGR GEO KGZ MNE POL ROU SRB SVK TJK MKD TUR TKM UZB",
    "eur_c": "BLR EST HUN KAZ LVA LTU MDA RUS UKR",
    "sear_b": "IDN LKA THA",
    "sear_d": "BGD IND MMR NPL",
    "wpr_a": "AUS JPN NZL SGP",
    "wpr_b": "KHM CHN LAO MYS MNG PHL KOR VNM",
}
p3_WHO_OF = {iso: sub for sub, isos in p3_WHO_SUBREGIONS.items() for iso in isos.split()}

p3_WORK_INJURY = ["L21A", "L21B", "L21C", "L21D", "L21E"]  # injury or harm while working, past two years

d = add_columns(d, [
    "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel",
    "Gender", "Age", "AgeGroups4", "Education", "IncomeFeelings", "REGION2_USA",
    "L2", "L3_A", "L3_B", "L4A", "L4B", "L4C", "L5", "L6A", "L6B", "L7A", "L7B", "L8A", "L8B", "L8D",
    "L12", "L14", "L16A", "L16B", "L16C", "L26", "L27A", "L27B", "L27C", *p3_WORK_INJURY,
    "worry_index_published", "experience_index_published",
])

# --- Derived variables -----------------------------------------------------------

# Group keys as strings, so that one helper serves every breakdown.
d["p3_region"] = d.GlobalRegion.map(p3_REGIONS)
d["p3_income"] = d.CountryIncomeLevel.map(p3_INCOME)
d["p3_edu"] = d.Education.map(p3_EDU)
d["p3_age"] = d.AgeGroups4.map(p3_AGE)
d["p3_sex"] = d.Gender.map(p3_SEX)
d["p3_sex_age"] = d.p3_sex + "_" + d.p3_age
d["p3_sex_edu"] = d.p3_sex + "_" + d.p3_edu
# Middle income (Chapter 8): lower-middle and upper-middle combined.
d["p3_income3"] = d.CountryIncomeLevel.map({1: "low", 2: "middle", 3: "middle", 4: "high"})
# WHO sub-region (Chart 9.1) and WHO region (sub-regions combined).
d["p3_who_sub"] = d.COUNTRY_ISO3.map(p3_WHO_OF)
d["p3_who"] = d.p3_who_sub.str.split("_").str[0]

# Numeracy (L12): correct = "10% is the same as 1 out of 10" (code 3); anything
# else, including don't know, is "not correct". Missing where not asked.
d["p3_numeracy"] = np.where(d.L12.isna(), np.nan, np.where(d.L12.eq(3), 1, 2))
d["p3_numeracy_key"] = d.p3_numeracy.map({1: "correct", 2: "not_correct"})
d["p3_income_numeracy"] = d.p3_income + "_" + d.p3_numeracy_key
d["p3_region_numeracy"] = d.p3_region + "_" + d.p3_numeracy_key
d["p3_region_sex"] = d.p3_region + "_" + d.p3_sex

# U.S. regions (Chart 6.7): REGION2_USA 1 Northeast, 2 Midwest, 3 South, 4 West.
d["p3_us_region"] = d.REGION2_USA.map({1: "north_midwest", 2: "north_midwest", 3: "south", 4: "west"})

# Experience of harm from severe weather (Chart 6.8): yes / no; DK and refused are left out.
d["p3_severe_weather"] = d.L8D.map({1: "yes", 2: "no"})

# Food or water among the two biggest risks named (L3_A, L3_B): 11 = water, 12 = food.
d["p3_foodwater_top2"] = np.where(d.L3_A.isin([11, 12]) | d.L3_B.isin([11, 12]), 1, 2)

# Harm from food or water, and from both, in the past two years.
d["p3_harm_either"] = np.where(d.L8A.eq(1) | d.L8B.eq(1), 1, 2)
d["p3_harm_both"] = np.where(d.L8A.eq(1) & d.L8B.eq(1), 1, 2)

# Government Safety Performance Index (Chapter 9): yes = 1, any other answer
# (no, DK, refused) = 0, averaged over food, water and power lines, x 100.
# Not asked in Saudi Arabia and Turkmenistan.
d["p3_gspi"] = np.where(d.L16A.isna(), np.nan, 100 * d[["L16A", "L16B", "L16C"]].eq(1).sum(axis=1) / 3)

# Work injury (Chapter 10): yes to any of L21A-L21E, among those asked (workers).
d["p3_work_injury"] = np.where(d.L21A.isna(), np.nan, np.where(d[p3_WORK_INJURY].eq(1).any(axis=1), 1, 2))

# Risk gap (Chapter 10): Worry Index minus Experience Index for each person.
d["p3_risk_gap"] = d.worry_index_published - d.experience_index_published

# --- Helpers -------------------------------------------------------------------


def p3_share(df, var, cats, by=None):
    """% in each named category of `var` ({name: codes}), overall or for each `by` group.

    Returns {name: %} or {"<group>_<name>": %}.
    """
    table = distribution(df, var, by=by)
    if by is None:
        return {name: table[table.index.intersection(codes)].sum() for name, codes in cats.items()}
    return {f"{g}_{name}": table.loc[g, table.columns.intersection(codes)].sum()
            for g in table.index for name, codes in cats.items()}


def p3_pct_by(df, var, codes, by):
    """% with `var` in `codes` for each `by` group: {group: %}."""
    return pct(df, var, codes, by=by).to_dict()


def p3_country_map(var, codes, df=None):
    """% by country (ISO3 keys) plus the minimum and maximum across countries (map legends)."""
    r = pct(d if df is None else df, var, codes, by="COUNTRY_ISO3").dropna()
    return {**r.to_dict(), "min": r.min(), "max": r.max()}


def p3_round(x):
    """Round half up to whole numbers (as the charts print), the same in Python and R."""
    return np.floor(x + 0.5)


def p3_labels(keys):
    """Region keys -> labels, in alphabetical order, joined with '; '."""
    return "; ".join(sorted(p3_REGION_LABELS[k] for k in keys))


def p3_country_names(isos):
    names = d.drop_duplicates("COUNTRY_ISO3").set_index("COUNTRY_ISO3").Country
    return "; ".join(sorted(names[i] for i in isos))


def p3_adults(mask):
    """Adult population represented (sum of PROJWT) by the rows in `mask`."""
    return d.loc[mask, "PROJWT"].sum()


p3_L5 = {"very": [1], "somewhat": [2], "not": [3], "dk": p3_DK}
p3_HELP_HARM = {"help": [1], "harm": [2]}
p3_HELP_HARM_NONE = {"help": [1], "harm": [2], "none": [3, 4, *p3_DK]}

# =================================================================================
# Chapter 6: Climate change risk
# =================================================================================


@report.finding("X6_01")
def p3_climate_very():
    return pct(d, "L5", [1])


@report.finding("X6_02")
def p3_climate_somewhat():
    return pct(d, "L5", [2])


@report.finding("X6_03")
def p3_climate_not():
    return pct(d, "L5", [3])


@report.finding("X6_04")
def p3_china_very():
    return pct(d[d.COUNTRY_ISO3 == "CHN"], "L5", [1])


@report.finding("X6_05")
def p3_us_not():
    return pct(d[d.COUNTRY_ISO3 == "USA"], "L5", [3])


@report.finding("X6_06")
def p3_climate_dk():
    return pct(d, "L5", p3_DK)


@report.finding("X6_07")
def p3_climate_dk_people():
    return p3_adults(d.L5.isin(p3_DK))


@report.finding("C6_1")
def p3_climate_global():
    return p3_share(d, "L5", p3_L5)


@report.finding("C6_2")
def p3_climate_by_region():
    return p3_share(d, "L5", {"very": [1], "somewhat": [2]}, by="p3_region")


@report.finding("X6_08")
def p3_climate_serious_min_region():
    return min(p3_pct_by(d, "L5", [1, 2], by="p3_region").values())


@report.finding("X6_09")
def p3_climate_very_southern_europe():
    return p3_pct_by(d, "L5", [1], by="p3_region")["southern_europe"]


@report.finding("X6_10")
def p3_climate_very_latin_america():
    return p3_pct_by(d, "L5", [1], by="p3_region")["latin_america"]


@report.finding("X6_11")
def p3_climate_very_edu_16plus():
    return p3_pct_by(d, "L5", [1], by="p3_edu")["edu_16plus"]


@report.finding("X6_12")
def p3_climate_very_edu_0_8():
    return p3_pct_by(d, "L5", [1], by="p3_edu")["edu_0_8"]


@report.finding("C6_3")
def p3_climate_by_edu_age():
    cats = {"very": [1], "somewhat": [2], "not": [3]}
    return {**{f"global_{k}": v for k, v in p3_share(d, "L5", cats).items()},
            **p3_share(d, "L5", cats, by="p3_edu"), **p3_share(d, "L5", cats, by="p3_age")}


@report.finding("C6_4")
def p3_climate_by_numeracy():
    return p3_pct_by(d, "L5", [1], by="p3_region_numeracy")


@report.finding("X6_13")
def p3_climate_very_high_income():
    return p3_pct_by(d, "L5", [1], by="p3_income")["high"]


@report.finding("X6_14")
def p3_climate_very_low_income():
    return p3_pct_by(d, "L5", [1], by="p3_income")["low"]


@report.finding("X6_15")
def p3_climate_very_middle_income():
    r = p3_pct_by(d, "L5", [1], by="p3_income")
    return {k: r[k] for k in ("lower_middle", "upper_middle")}


@report.finding("C6_5")
def p3_climate_by_region_gender():
    return p3_pct_by(d, "L5", [1], by="p3_region_sex")


@report.finding("X6_16")
def p3_climate_gap_middle_east():
    me = d[d.p3_region == "middle_east"]
    r = p3_pct_by(me, "L5", [1], by="p3_sex")
    return r["women"] - r["men"]


@report.finding("X6_17")
def p3_climate_not_regions_text():
    r = p3_pct_by(d, "L5", [3], by="p3_region")
    return {k: r[k] for k in ("east_africa", "northern_america", "central_asia", "northern_africa", "southern_asia")}


@report.finding("C6_6")
def p3_climate_not_by_region():
    return p3_pct_by(d, "L5", [3], by="p3_region")


@report.finding("X6_18")
def p3_ethiopia_not():
    return pct(d[d.COUNTRY_ISO3 == "ETH"], "L5", [3])


@report.finding("X6_19")
def p3_ethiopia_edu_0_8():
    return pct(d[d.COUNTRY_ISO3 == "ETH"], "Education", [1])


@report.finding("X6_20")
def p3_finland_not():
    return pct(d[d.COUNTRY_ISO3 == "FIN"], "L5", [3])


@report.finding("X6_21")
def p3_climate_dk_countries():
    r = pct(d, "L5", p3_DK, by="COUNTRY_ISO3")
    return {k: r[k] for k in ("LAO", "NPL", "KHM")}


@report.finding("X6_22")
def p3_china_somewhat():
    return pct(d[d.COUNTRY_ISO3 == "CHN"], "L5", [2])


@report.finding("X6_23")
def p3_china_not():
    return pct(d[d.COUNTRY_ISO3 == "CHN"], "L5", [3])


@report.finding("X6_24")
def p3_china_dk():
    return pct(d[d.COUNTRY_ISO3 == "CHN"], "L5", p3_DK)


@report.finding("X6_25")
def p3_india_not():
    return pct(d[d.COUNTRY_ISO3 == "IND"], "L5", [3])


@report.finding("X6_26")
def p3_india_very():
    return pct(d[d.COUNTRY_ISO3 == "IND"], "L5", [1])


@report.finding("X6_27")
def p3_edu_0_8_global():
    # Population-weighted share (see README): the unweighted mean of country shares is 36%.
    return pct(d, "Education", [1])


@report.finding("X6_28")
def p3_countries():
    return d.COUNTRY_ISO3.nunique()


def p3_us_very(region_keys):
    us = d[d.COUNTRY_ISO3 == "USA"]
    return pct(us[us.p3_us_region.isin(region_keys)], "L5", [1])


def p3_us_severe(region_keys):
    us = d[d.COUNTRY_ISO3 == "USA"]
    return pct(us[us.p3_us_region.isin(region_keys)], "L8D", [1])


@report.finding("X6_29")
def p3_us_south_very():
    return p3_us_very(["south"])


@report.finding("X6_30")
def p3_us_elsewhere_very():
    return p3_us_very(["north_midwest", "west"])


@report.finding("X6_31")
def p3_us_south_severe():
    return p3_us_severe(["south"])


@report.finding("X6_32")
def p3_us_elsewhere_severe():
    return p3_us_severe(["north_midwest", "west"])


@report.finding("C6_7")
def p3_us_regions():
    us = d[d.COUNTRY_ISO3 == "USA"]
    out = p3_share(us, "L5", {"very": [1], "somewhat": [2], "not": [3]}, by="p3_us_region")
    out.update({f"{k}_experienced": v for k, v in p3_pct_by(us, "L8D", [1], by="p3_us_region").items()})
    return out


@report.finding("X6_33")
def p3_climate_very_severe_yes():
    return p3_pct_by(d, "L5", [1], by="p3_severe_weather")["yes"]


@report.finding("X6_34")
def p3_climate_very_severe_no():
    return p3_pct_by(d, "L5", [1], by="p3_severe_weather")["no"]


@report.finding("C6_8")
def p3_climate_by_severe_weather():
    return p3_share(d, "L5", p3_L5, by="p3_severe_weather")


@report.finding("X6_35")
def p3_climate_model_excluded():
    return pct(d, "L5", p3_DK)


@lru_cache(maxsize=None)
def p3_climate_model():
    """Chart 6.9: average predicted probabilities by education from two logistic models.

    The report used a multilevel logistic regression with Gallup World Poll
    items (satisfaction with air and water quality, religion). This version
    uses country fixed effects (see README). Needs the Gallup items.
    """
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    g = merge_gallup(d, ["WP93", "WP94", "WP1233"])
    g = g[g.L5.isin([1, 2, 3]) & g.Education.isin([1, 2, 3]) & g.IncomeFeelings.isin([1, 2, 3, 4])
          & g.AgeGroups4.notna() & g.p3_numeracy.notna() & g.WP93.isin([1, 2]) & g.WP94.isin([1, 2])
          & g.WP1233.notna()].copy()
    g["p3_w"] = g.PROJWT / g.PROJWT.mean()
    g["p3_correct"] = (g.p3_numeracy == 1).astype(float)
    g["p3_severe"] = (g.L8D == 1).astype(float)
    g["p3_air_ok"] = (g.WP93 == 1).astype(float)
    g["p3_water_ok"] = (g.WP94 == 1).astype(float)
    rhs = ("C(Education) + C(Gender) + C(AgeGroups4) + C(IncomeFeelings) + p3_correct + p3_severe"
           " + p3_air_ok + p3_water_ok + C(WP1233) + C(COUNTRY_ISO3)")
    out = {}
    for outcome, code in (("very", 1), ("not", 3)):
        g["p3_y"] = (g.L5 == code).astype(float)
        fit = smf.glm("p3_y ~ " + rhs, data=g, family=sm.families.Binomial(), var_weights=g.p3_w).fit()
        for level, key in p3_EDU.items():
            p = fit.predict(g.assign(Education=float(level)))
            out[f"{key}_{outcome}"] = 100 * np.average(p, weights=g.p3_w)
    return out


@report.finding("X6_36")
def p3_climate_model_16plus():
    return p3_climate_model()["edu_16plus_very"]


@report.finding("C6_9")
def p3_climate_model_by_edu():
    return p3_climate_model()


@report.finding("C6_10")
def p3_climate_by_sex_age():
    return p3_share(d, "L5", {"very": [1], "somewhat": [2], "not": [3]}, by="p3_sex_age")


@report.finding("X6_37")
def p3_high_income_most_sceptical():
    r = pct(d[d.CountryIncomeLevel == 4], "L5", [3], by="Country")
    return r.idxmax()


# =================================================================================
# Chapter 7: Technology-related risk perceptions
# =================================================================================


@report.finding("X7_01")
def p3_gm_harm():
    return pct(d, "L4A", [2])


@report.finding("X7_02")
def p3_gm_help():
    return pct(d, "L4A", [1])


@report.finding("X7_03")
def p3_gm_help_low_income():
    return p3_pct_by(d, "L4A", [1], by="p3_income")["low"]


@report.finding("X7_04")
def p3_gm_help_high_income():
    return p3_pct_by(d, "L4A", [1], by="p3_income")["high"]


@report.finding("X7_05")
def p3_nuclear_help():
    return pct(d, "L4B", [1])


@report.finding("X7_06")
def p3_nuclear_harm():
    return pct(d, "L4B", [2])


@report.finding("X7_07")
def p3_help_four_in_ten():
    return {"nuclear": pct(d, "L4B", [1]), "ai": pct(d, "L4C", [1])}


@report.finding("X7_08")
def p3_harm_three_in_ten():
    return {"nuclear": pct(d, "L4B", [2]), "ai": pct(d, "L4C", [2])}


@report.finding("C7_1")
def p3_technologies_global():
    out = {}
    for tech, var in (("gm", "L4A"), ("nuclear", "L4B"), ("ai", "L4C")):
        out.update({f"{tech}_{k}": v for k, v in p3_share(d, var, p3_HELP_HARM_NONE).items()})
    return out


@report.finding("C7_2")
def p3_gm_by_region():
    return p3_share(d, "L4A", p3_HELP_HARM, by="p3_region")


@report.finding("C7_3")
def p3_gm_help_by_country():
    # y-axis of the scatter; the x-axis (Food and Shelter Index) needs Gallup data (X7_09).
    return pct(d, "L4A", [1], by="COUNTRY_ISO3").dropna().to_dict()


def p3_food_shelter_correlation():
    """Country Food and Shelter Index vs % saying GM food will mostly help.

    Gallup's Food and Shelter Index from WP40 (not enough money for food) and
    WP43 (not enough money for shelter), 1 = yes, 2 = no: each person scores
    100 x the share of the two items answered "no"; countries are the weighted
    mean. Countries without the items are left out.
    """
    g = merge_gallup(d, ["WP40", "WP43"])
    g = g[g.WP40.isin([1, 2, *p3_DK]) & g.WP43.isin([1, 2, *p3_DK])].copy()
    g["p3_fsi"] = 100 * (g.WP40.eq(2).astype(float) + g.WP43.eq(2)) / 2
    both = pd.concat([wmean(g, "p3_fsi", by="COUNTRY_ISO3").rename("fsi"),
                      pct(d, "L4A", [1], by="COUNTRY_ISO3").rename("help")], axis=1, join="inner").dropna()
    return both.fsi.corr(both.help), len(both)


@report.finding("X7_09")
def p3_food_shelter_r():
    return p3_food_shelter_correlation()[0]


@report.finding("X7_10")
def p3_food_shelter_n():
    return p3_food_shelter_correlation()[1]


@report.finding("X7_11")
def p3_gm_help_low_income_p129():
    return p3_pct_by(d, "L4A", [1], by="p3_income")["low"]


@report.finding("X7_12")
def p3_gm_harm_high_income():
    return p3_pct_by(d, "L4A", [2], by="p3_income")["high"]


@report.finding("X7_13")
def p3_gm_harm_high_income_very_worried():
    return pct(d[d.CountryIncomeLevel == 4], "L4A", [2], by="L6A")[1]


@report.finding("X7_14")
def p3_gm_harm_high_income_not_worried():
    return pct(d[d.CountryIncomeLevel == 4], "L4A", [2], by="L6A")[3]


@report.finding("X7_15")
def p3_nuclear_harm_southern_europe():
    return p3_pct_by(d, "L4B", [2], by="p3_region")["southern_europe"]


@report.finding("X7_16")
def p3_nuclear_harm_spain():
    return pct(d[d.COUNTRY_ISO3 == "ESP"], "L4B", [2])


@report.finding("X7_17")
def p3_nuclear_help_low_income():
    return p3_pct_by(d, "L4B", [1], by="p3_income")["low"]


@report.finding("X7_18")
def p3_nuclear_harm_low_income():
    return p3_pct_by(d, "L4B", [2], by="p3_income")["low"]


@report.finding("X7_19")
def p3_nuclear_help_high_income():
    return p3_pct_by(d, "L4B", [1], by="p3_income")["high"]


@report.finding("X7_20")
def p3_nuclear_harm_high_income():
    return p3_pct_by(d, "L4B", [2], by="p3_income")["high"]


@report.finding("C7_4")
def p3_nuclear_by_region():
    return p3_share(d, "L4B", p3_HELP_HARM, by="p3_region")


@report.finding("X7_21")
def p3_nuclear_help_high_income_by_edu():
    return p3_pct_by(d[d.CountryIncomeLevel == 4], "L4B", [1], by="p3_edu")


@report.finding("C7_5")
def p3_nuclear_high_income_by_edu():
    return p3_share(d[d.CountryIncomeLevel == 4], "L4B", p3_HELP_HARM, by="p3_edu")


@report.finding("C7_6")
def p3_nuclear_help_by_numeracy_income():
    return p3_pct_by(d, "L4B", [1], by="p3_income_numeracy")


def p3_nuclear_high_income_sex(sex, codes):
    return p3_pct_by(d[d.CountryIncomeLevel == 4], "L4B", codes, by="p3_sex")[sex]


@report.finding("X7_22")
def p3_nuclear_harm_high_income_women():
    return p3_nuclear_high_income_sex("women", [2])


@report.finding("X7_23")
def p3_nuclear_help_high_income_women():
    return p3_nuclear_high_income_sex("women", [1])


@report.finding("X7_24")
def p3_nuclear_help_high_income_men():
    return p3_nuclear_high_income_sex("men", [1])


@report.finding("X7_25")
def p3_nuclear_harm_high_income_men():
    return p3_nuclear_high_income_sex("men", [2])


@report.finding("C7_7")
def p3_nuclear_high_income_by_sex_edu():
    return p3_share(d[d.CountryIncomeLevel == 4], "L4B", p3_HELP_HARM, by="p3_sex_edu")


@report.finding("X7_26")
def p3_ai_help_eastern_asia():
    return p3_pct_by(d, "L4C", [1], by="p3_region")["eastern_asia"]


@report.finding("X7_27")
def p3_ai_harm_eastern_asia():
    return p3_pct_by(d, "L4C", [2], by="p3_region")["eastern_asia"]


@report.finding("X7_28")
def p3_ai_harm_china():
    return pct(d[d.COUNTRY_ISO3 == "CHN"], "L4C", [2])


@report.finding("X7_29")
def p3_ai_harm_lowest_country():
    return pct(d, "L4C", [2], by="Country").idxmin()


@report.finding("X7_30")
def p3_ai_harm_southern_europe():
    return p3_pct_by(d, "L4C", [2], by="p3_region")["southern_europe"]


@report.finding("X7_31")
def p3_ai_harm_latin_america():
    return p3_pct_by(d, "L4C", [2], by="p3_region")["latin_america"]


@report.finding("X7_32")
def p3_ai_harm_northern_america():
    return p3_pct_by(d, "L4C", [2], by="p3_region")["northern_america"]


@report.finding("C7_8")
def p3_ai_by_region():
    return p3_share(d, "L4C", p3_HELP_HARM, by="p3_region")


@report.finding("C7_9")
def p3_ai_harm_by_country():
    # y-axis of the scatter; the x-axis is the Wellcome Global Monitor 2018 Trust in
    # Scientists Index (external, not used: the chart prints no values).
    return pct(d, "L4C", [2], by="COUNTRY_ISO3").dropna().to_dict()


@report.finding("X7_33")
def p3_ai_help_high_income():
    return p3_pct_by(d, "L4C", [1], by="p3_income")["high"]


@report.finding("X7_34")
def p3_ai_help_low_income():
    return p3_pct_by(d, "L4C", [1], by="p3_income")["low"]


@report.finding("X7_35")
def p3_ai_harm_top3_regions():
    r = pd.Series(p3_pct_by(d, "L4C", [2], by="p3_region"))
    return p3_labels(r.sort_values(ascending=False).index[:3])


@report.finding("X7_36")
def p3_ai_help_top_region():
    r = pd.Series(p3_pct_by(d, "L4C", [1], by="p3_region"))
    return p3_REGION_LABELS[r.idxmax()]


@report.finding("C7_10")
def p3_ai_by_sex_age():
    return p3_share(d, "L4C", p3_HELP_HARM_NONE, by="p3_sex_age")


# =================================================================================
# Chapter 8: Internet-related risk perceptions
# L27A-C were asked only of internet users (L26 = 1); pct() drops the others.
# =================================================================================


@report.finding("X8_01")
def p3_worry_false_info():
    return pct(d, "L27B", [1])


@report.finding("X8_02")
def p3_worry_fraud():
    return pct(d, "L27C", [1])


@report.finding("X8_03")
def p3_worry_bullying():
    return pct(d, "L27A", [1])


@report.finding("X8_04")
def p3_bullying_women():
    return p3_pct_by(d, "L27A", [1], by="p3_sex")["women"]


@report.finding("X8_05")
def p3_bullying_men():
    return p3_pct_by(d, "L27A", [1], by="p3_sex")["men"]


@report.finding("X8_06")
def p3_bullying_15_29():
    return p3_pct_by(d, "L27A", [1], by="p3_age")["age_15_29"]


@report.finding("X8_07")
def p3_bullying_65plus():
    return p3_pct_by(d, "L27A", [1], by="p3_age")["age_65plus"]


@report.finding("X8_08")
def p3_internet():
    return pct(d, "L26", [1])


@report.finding("X8_09")
def p3_internet_northern_america():
    return p3_pct_by(d, "L26", [1], by="p3_region")["northern_america"]


@report.finding("X8_10")
def p3_internet_east_africa():
    return p3_pct_by(d, "L26", [1], by="p3_region")["east_africa"]


@report.finding("X8_11")
def p3_internet_southern_asia():
    return p3_pct_by(d, "L26", [1], by="p3_region")["southern_asia"]


@report.finding("C8_1")
def p3_internet_map():
    return p3_country_map("L26", [1])


@report.finding("C8_2")
def p3_internet_by_sex_age_edu():
    out = {}
    for col, groups in (("p3_age", p3_AGE), ("p3_edu", p3_EDU)):
        r = p3_pct_by(d, "L26", [1], by=["p3_sex", col])
        out.update({f"{s}_{g}": r[(s, g)] for s in ("women", "men") for g in groups.values()})
    return out


@report.finding("X8_12")
def p3_internet_small_samples():
    n = d[d.L27A.notna()].groupby("COUNTRY_ISO3").size()
    return int((n < 100).sum())


@report.finding("C8_3")
def p3_internet_risks_global():
    cats = {"yes": [1], "no": [2], "dk": p3_DK}
    out = {}
    for risk, var in (("bullying", "L27A"), ("false_info", "L27B"), ("fraud", "L27C")):
        out.update({f"{risk}_{k}": v for k, v in p3_share(d, var, cats).items()})
    return out


@report.finding("C8_4")
def p3_false_info_map():
    return p3_country_map("L27B", [1])


def p3_gini_correlation():
    """Country % of internet users worried about false information vs the World Bank
    GINI index (SI.POV.GINI): each country's latest estimate from 2018 or earlier,
    the latest available when the report retrieved it (May 2020)."""
    gini = pd.read_csv(external_path("core_world_risk_poll_2019__worldbank_SI.POV.GINI.csv"))
    gini = gini[gini.year <= 2018].sort_values("year").groupby("iso3").value.last()
    both = pd.concat([pct(d, "L27B", [1], by="COUNTRY_ISO3").rename("worry"), gini.rename("gini")],
                     axis=1, join="inner").dropna()
    return both.worry.corr(both.gini), len(both)


@report.finding("X8_13")
def p3_gini_r():
    return p3_gini_correlation()[0]


@report.finding("X8_14")
def p3_gini_n():
    return p3_gini_correlation()[1]


@report.finding("C8_5")
def p3_internet_risks_by_age():
    out = {}
    for risk, var in (("false_info", "L27B"), ("fraud", "L27C"), ("bullying", "L27A")):
        out.update({f"{risk}_{k}": v for k, v in p3_pct_by(d, var, [1], by="p3_age").items()})
    return out


@report.finding("X8_15")
def p3_false_info_lowest_age_group():
    return min(p3_pct_by(d, "L27B", [1], by="p3_age").values())


@report.finding("X8_16")
def p3_bullying_low_income():
    return p3_pct_by(d, "L27A", [1], by="p3_income3")["low"]


@report.finding("X8_17")
def p3_bullying_middle_income():
    return p3_pct_by(d, "L27A", [1], by="p3_income3")["middle"]


@report.finding("X8_18")
def p3_bullying_high_income():
    return p3_pct_by(d, "L27A", [1], by="p3_income3")["high"]


@report.finding("C8_6")
def p3_bullying_and_age_by_country():
    # Scatter with no printed values: % worried about online bullying and mean age
    # of internet users, by country.
    users = d[d.L27A.notna()]
    worry = pct(users, "L27A", [1], by="COUNTRY_ISO3").dropna()
    age = wmean(users, "Age", by="COUNTRY_ISO3").dropna()
    return {**{f"{k}_bullying": v for k, v in worry.items()}, **{f"{k}_age": v for k, v in age.items()}}


@report.finding("C8_7")
def p3_fraud_by_sex_edu_age():
    out = {}
    for col, groups in (("p3_edu", p3_EDU), ("p3_age", p3_AGE)):
        r = p3_pct_by(d, "L27C", [1], by=["p3_sex", col])
        out.update({f"{s}_{g}": r[(s, g)] for s in ("women", "men") for g in groups.values()})
    return out


@report.finding("X8_19")
def p3_fraud_western_europe():
    r = pct(d, "L27C", [1], by="COUNTRY_ISO3")
    return {k: r[k] for k in ("PRT", "FRA", "ESP", "GBR", "ITA")}


@report.finding("C8_8")
def p3_fraud_map():
    return p3_country_map("L27C", [1])


# =================================================================================
# Chapter 9: Food and water risk
# =================================================================================


@report.finding("X9_01")
def p3_harm_food():
    return pct(d, "L8A", [1])


@report.finding("X9_02")
def p3_harm_water():
    return pct(d, "L8B", [1])


@report.finding("X9_03")
def p3_foodwater_top2():
    return pct(d, "p3_foodwater_top2", [1])


@report.finding("X9_04")
def p3_food_not_good_eastern_europe():
    return p3_pct_by(d, "L16A", [2], by="p3_region")["eastern_europe"]


@report.finding("X9_05")
def p3_harm_food_or_water():
    return pct(d[d.L8A.notna()], "p3_harm_either", [1])


@report.finding("X9_06")
def p3_harm_food_people():
    return p3_adults(d.L8A.eq(1))


@report.finding("X9_07")
def p3_harm_food_and_water():
    return pct(d[d.L8A.notna()], "p3_harm_both", [1])


@report.finding("X9_08")
def p3_sear_rank():
    r = pd.Series(p3_pct_by(d, "L8A", [1], by="p3_who")).sort_values(ascending=False)
    return list(r.index).index("sear") + 1


@report.finding("C9_1")
def p3_harm_food_by_who_subregion():
    return p3_pct_by(d, "L8A", [1], by="p3_who_sub")


@report.finding("X9_09")
def p3_worried_food():
    return pct(d, "L6A", [1, 2])


@report.finding("X9_10")
def p3_worried_water():
    return pct(d, "L6B", [1, 2])


@report.finding("X9_11")
def p3_likely_food():
    return pct(d, "L7A", [1, 2])


@report.finding("X9_12")
def p3_likely_water():
    return pct(d, "L7B", [1, 2])


@report.finding("C9_2")
def p3_very_worried_by_income():
    food = p3_pct_by(d, "L6A", [1], by="p3_income")
    water = p3_pct_by(d, "L6B", [1], by="p3_income")
    return {**{f"{k}_food": v for k, v in food.items()}, **{f"{k}_water": v for k, v in water.items()}}


@report.finding("C9_3")
def p3_likely_and_experienced_by_income():
    out = {}
    for t, likely, harm in (("food", "L7A", "L8A"), ("water", "L7B", "L8B")):
        out.update({f"{t}_{k}_likely": v for k, v in p3_pct_by(d, likely, [1], by="p3_income").items()})
        out.update({f"{t}_{k}_experienced": v for k, v in p3_pct_by(d, harm, [1], by="p3_income").items()})
    return out


def p3_food_worry_vs_harm():
    return (pd.Series(p3_pct_by(d, "L6A", [1], by="p3_region")),
            pd.Series(p3_pct_by(d, "L8A", [1], by="p3_region")))


@report.finding("X9_13")
def p3_worry_exceeds_harm_regions():
    # From the rounded chart values: the unrounded gap is 4.9 points in Eastern Asia.
    worry, harm = p3_food_worry_vs_harm()
    gap = p3_round(worry) - p3_round(harm)
    return p3_labels(gap.index[gap >= 5])


@report.finding("X9_14")
def p3_harm_exceeds_worry_regions():
    # From the rounded chart values: unrounded, Middle East is 4.8 and Eastern Africa 4.6.
    worry, harm = p3_food_worry_vs_harm()
    gap = p3_round(harm) - p3_round(worry)
    return p3_labels(gap.index[gap >= 5])


@report.finding("X9_15")
def p3_food_worry_top_region():
    worry, _ = p3_food_worry_vs_harm()
    return p3_REGION_LABELS[worry.sort_values(ascending=False).index[0]]


@report.finding("X9_16")
def p3_food_worry_second_region():
    worry, _ = p3_food_worry_vs_harm()
    return p3_REGION_LABELS[worry.sort_values(ascending=False).index[1]]


@report.finding("X9_17")
def p3_food_gap_east_africa():
    worry, harm = p3_food_worry_vs_harm()
    return harm["east_africa"] - worry["east_africa"]


@report.finding("X9_18")
def p3_food_harm_east_africa():
    return p3_food_worry_vs_harm()[1]["east_africa"]


@report.finding("X9_19")
def p3_food_worry_east_africa():
    return p3_food_worry_vs_harm()[0]["east_africa"]


@report.finding("C9_4")
def p3_food_worry_harm_by_region():
    worry, harm = p3_food_worry_vs_harm()
    return {**{f"{k}_worried": v for k, v in worry.items()}, **{f"{k}_experienced": v for k, v in harm.items()}}


@report.finding("X9_20")
def p3_trust_family():
    return pct(d, "L14", [1])


@report.finding("X9_21")
def p3_trust_medical():
    return pct(d, "L14", [2])


@report.finding("X9_22")
def p3_trust_agency():
    return pct(d, "L14", [5])


@report.finding("C9_5")
def p3_trust_by_edu_sex_age():
    cats = {"family": [1], "medical": [2], "agency": [5]}
    return {**p3_share(d, "L14", cats, by="p3_edu"), **p3_share(d, "L14", cats, by="p3_sex_age")}


@report.finding("X9_23")
def p3_water_good():
    return pct(d, "L16B", [1])


@report.finding("X9_24")
def p3_food_good():
    return pct(d, "L16A", [1])


@report.finding("X9_25")
def p3_food_not_good_northern_america():
    return p3_pct_by(d, "L16A", [2], by="p3_region")["northern_america"]


@report.finding("X9_26")
def p3_food_not_good_northern_western_europe():
    return p3_pct_by(d, "L16A", [2], by="p3_region")["northern_western_europe"]


@report.finding("X9_27")
def p3_food_not_good_france():
    return pct(d[d.COUNTRY_ISO3 == "FRA"], "L16A", [2])


@report.finding("C9_6")
def p3_food_not_good_map():
    return p3_country_map("L16A", [2])


def p3_confidence_government():
    """Rows with the Gallup World Poll item WP139, confidence in the national
    government (1 = yes, 2 = no; DK and refused stay in the base)."""
    return merge_gallup(d, ["WP139"])


@report.finding("X9_28")
def p3_confidence_france():
    g = p3_confidence_government()
    return pct(g[g.COUNTRY_ISO3 == "FRA"], "WP139", [1])


@report.finding("X9_29")
def p3_food_not_good_nearly_half():
    r = p3_pct_by(d, "L16A", [2], by="p3_region")
    return {k: r[k] for k in ("latin_america", "southern_europe", "middle_east")}


@report.finding("X9_30")
def p3_food_good_eastern_europe():
    return p3_pct_by(d, "L16A", [1], by="p3_region")["eastern_europe"]


@report.finding("X9_31")
def p3_harm_either_eastern_europe():
    return p3_pct_by(d[d.L8A.notna()], "p3_harm_either", [1], by="p3_region")["eastern_europe"]


@report.finding("X9_32")
def p3_confidence_eastern_europe_median():
    g = p3_confidence_government()
    return pct(g[g.p3_region == "eastern_europe"], "WP139", [1], by="COUNTRY_ISO3").median()


@report.finding("X9_33")
def p3_food_good_confident():
    g = p3_confidence_government()
    return pct(g[g.p3_region == "eastern_europe"], "L16A", [1], by="WP139")[1]


@report.finding("X9_34")
def p3_food_good_not_confident():
    g = p3_confidence_government()
    return pct(g[g.p3_region == "eastern_europe"], "L16A", [1], by="WP139")[2]


@report.finding("C9_7")
def p3_food_good_eastern_europe_countries():
    # Scatter with no printed values: y-axis (% government does a good job on food
    # safety) for Eastern European countries and for regions. The x-axis is
    # confidence in the national government (Gallup WP139).
    ee = d[d.p3_region == "eastern_europe"]
    return {**pct(ee, "L16A", [1], by="COUNTRY_ISO3").dropna().to_dict(), **p3_pct_by(d, "L16A", [1], by="p3_region")}


@report.finding("X9_35")
def p3_food_good_ukraine_romania():
    r = pct(d, "L16A", [1], by="COUNTRY_ISO3")
    return {k: r[k] for k in ("UKR", "ROU")}


@report.finding("X9_36")
def p3_food_good_lowest_two():
    r = pct(d, "L16A", [1], by="COUNTRY_ISO3").dropna().sort_values()
    return p3_country_names(r.index[:2])


@report.finding("X9_37")
def p3_confidence_ukraine_romania():
    r = pct(p3_confidence_government(), "WP139", [1], by="COUNTRY_ISO3")
    return {k: r[k] for k in ("UKR", "ROU")}


@report.finding("X9_38")
def p3_water_good_northern_africa():
    return p3_pct_by(d, "L16B", [1], by="p3_region")["northern_africa"]


@report.finding("X9_39")
def p3_water_good_eastern_europe():
    return p3_pct_by(d, "L16B", [1], by="p3_region")["eastern_europe"]


@report.finding("X9_40")
def p3_water_good_below_half_regions():
    r = pd.Series(p3_pct_by(d, "L16B", [1], by="p3_region"))
    return p3_labels(r.index[r < 50])


@report.finding("X9_41")
def p3_water_good_tunisia_morocco():
    r = pct(d, "L16B", [1], by="COUNTRY_ISO3")
    return {k: r[k] for k in ("TUN", "MAR")}


@report.finding("C9_8")
def p3_water_not_good_map():
    return p3_country_map("L16B", [2])


@report.finding("X9_42")
def p3_water_good_ukraine():
    return pct(d[d.COUNTRY_ISO3 == "UKR"], "L16B", [1])


@report.finding("X9_43")
def p3_water_good_russia():
    return pct(d[d.COUNTRY_ISO3 == "RUS"], "L16B", [1])


def p3_gspi_by_country():
    return wmean(d, "p3_gspi", by="COUNTRY_ISO3").dropna()


@report.finding("X9_44")
def p3_gspi_countries():
    return len(p3_gspi_by_country())


@report.finding("X9_45")
def p3_gspi_median():
    return p3_gspi_by_country().median()


@report.finding("X9_46")
def p3_gspi_below_50():
    return int((p3_gspi_by_country() < 50).sum())


@report.finding("X9_47")
def p3_gspi_75_or_more():
    return int((p3_gspi_by_country() >= 75).sum())


@report.finding("X9_48")
def p3_gspi_highest():
    r = p3_gspi_by_country()
    return {k: r[k] for k in ("SGP", "ARE")}


@report.finding("X9_49")
def p3_confidence_croatia():
    g = p3_confidence_government()
    return pct(g[g.COUNTRY_ISO3 == "HRV"], "WP139", [1])


@report.finding("X9_50")
def p3_gspi_not_asked():
    asked = d.groupby("COUNTRY_ISO3").L16A.count()
    return p3_country_names(asked.index[asked == 0])


@report.finding("C9_9")
def p3_gspi_scores():
    return p3_gspi_by_country().to_dict()


# =================================================================================
# Chapter 10: Forecasting risk
# Only the recorded 2019 values can be computed; the 2020-2021 forecasts come from
# models with external predictors (see README). The report's 127 forecast
# countries are not listed, so all 142 countries are used.
# =================================================================================


@report.finding("X10_01")
def p3_less_safe():
    return pct(d, "L2", [2])


@report.finding("X10_02")
def p3_experience_index():
    return 100 * wmean(d, "experience_index_published")


@report.finding("X10_03")
def p3_work_injury():
    return pct(d, "p3_work_injury", [1])


@report.finding("X10_04")
def p3_adults_all():
    return d.PROJWT.sum()


@report.finding("X10_05")
def p3_less_safe_high_income():
    return p3_pct_by(d, "L2", [2], by="p3_income")["high"]


@report.finding("X10_06")
def p3_less_safe_low_income():
    return p3_pct_by(d, "L2", [2], by="p3_income")["low"]


@report.finding("X10_07")
def p3_less_safe_northern_america():
    return p3_pct_by(d, "L2", [2], by="p3_region")["northern_america"]


@report.finding("X10_08")
def p3_less_safe_southern_europe():
    return p3_pct_by(d, "L2", [2], by="p3_region")["southern_europe"]


@report.finding("X10_09")
def p3_less_safe_latin_america():
    return p3_pct_by(d, "L2", [2], by="p3_region")["latin_america"]


@report.finding("C10_2")
def p3_outcomes_2019():
    return {
        "harm_2019": 100 * wmean(d, "experience_index_published"),
        "worry_2019": 100 * wmean(d, "worry_index_published"),
        "gap_2019": 100 * wmean(d, "p3_risk_gap"),
        "less_safe_2019": pct(d, "L2", [2]),
        "injuries_2019": pct(d, "p3_work_injury", [1]),
    }


@report.finding("C10_3")
def p3_less_safe_by_income_2019():
    return {f"{k}_2019": v for k, v in p3_pct_by(d, "L2", [2], by="p3_income").items()}


@report.finding("C10_4")
def p3_less_safe_by_region_2019():
    return {f"{k}_2019": v for k, v in p3_pct_by(d, "L2", [2], by="p3_region").items()}


# =================================================================================
# Appendix 3: Regions
# =================================================================================


@report.finding("A3")
def p3_countries_by_region():
    n = d.drop_duplicates("COUNTRY_ISO3").p3_region.value_counts()
    return {**n.to_dict(), "total": int(n.sum())}


if __name__ == "__main__":
    sys.exit(report.run())
