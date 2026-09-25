"""Reproduce World Risk Poll 2024: A World of Waste.

Run from the repository root:
    python reports/WRP_2023/core_a_world_of_waste/reproduce.py

The report uses three questions from the 2023 poll: the most common material in
household waste (WP23341), whether household waste is separated (WP23342) and
what happens to it once taken outside the home (WP23343). Each function below
computes one chart, table or text statement listed in published_figures.csv;
see README.md for the method notes.
"""

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, load_wave, merge_gallup, pct  # noqa: E402

report = Report(__file__)

d = load_wave(2023, [
    "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "Gender",
    "AgeGroups4", "Education", "INCOME_5", "WP20719", "WP23341", "WP23342", "WP23343",
    "REGION_IND", "REGION_BRA",
])

INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # CountryIncomeLevel (9 = Venezuela, not classified)
REGION = {
    1: "eastern_africa", 2: "central_western_africa", 3: "northern_africa", 4: "southern_africa",
    5: "latin_america", 6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia",
    10: "southern_asia", 11: "middle_east", 12: "eastern_europe", 13: "northern_western_europe",
    14: "southern_europe", 15: "australia_nz",
}
AGE = {1: "15_29", 2: "30_49", 3: "50_64", 4: "65plus"}  # AgeGroups4
SEX = {2: "women", 1: "men"}  # Gender
EDUCATION = {1: "primary", 2: "secondary", 3: "tertiary"}
CLIMATE = {1: "very", 2: "somewhat", 3: "not"}  # WP20719: climate change a threat to the country
URBAN = {1: "cities", 2: "towns", 3: "rural"}  # degree of urbanisation (Gallup item, see below)
QUINTILE = {1: "q1", 2: "q2", 3: "q3", 4: "q4", 5: "q5"}  # INCOME_5
EUROPE = [12, 13, 14]
ASIA = [7, 8, 9, 10]
AFRICA = [1, 2, 3, 4]
SUB_SAHARAN_AFRICA = [1, 2, 4]

# --- Derived variables ---------------------------------------------------------

# Material (WP23341): 1 plastic, 2 food, 3 cardboard/paper, 4 cans/metal,
# 5 household dust/leaves/mud, 6 ash, 7 glass, 8 other, 98/99 DK/refused.
d["food_green"] = d.WP23341.isin([2, 5]).astype(float)  # food and green waste
d["dry"] = d.WP23341.isin([1, 3, 4, 7]).astype(float)  # dry recyclables

# Disposal (WP23343): 1 household burns it, 2 government collects it,
# 3 community group, 4 private company, 5 household takes it to the tip,
# 6 household throws it outside, 96 other, 98/99 DK/refused.
# Collected ('controlled disposal') = government, community group or private company.
d["collected"] = d.WP23343.isin([2, 3, 4]).astype(float)
d["burns"] = d.WP23343.eq(1).astype(float)

# Separation (WP23342): 1 yes, 2 no, 3 sometimes, 98/99 DK/refused.
d["separated"] = d.WP23342.eq(1).astype(float)

# Waste behaviour quadrant (Chapter 6): 'separated' is yes only, 'collected' is
# any organised collection; everything else is 'not'.
d["quadrant"] = np.select(
    [d.collected.eq(1) & d.separated.eq(1), d.collected.eq(1), d.separated.eq(1)], [1, 2, 3], default=4
)
QUADRANT = {1: "both", 2: "collected_only", 3: "separated_only", 4: "neither"}

# Main disposal method for Chart 4.3: burning vs dumping vs the tip vs all
# collection combined (the chart note).
d["main_method"] = np.select(
    [d.WP23343.eq(1), d.WP23343.eq(6), d.WP23343.eq(5), d.collected.eq(1)], [1, 2, 3, 4], default=9
)

# Eastern Europe as the report's text uses it (pages 12 and 33): the
# GlobalRegion plus the Western Balkans and Georgia. In GlobalRegion, Albania,
# Bosnia, Montenegro, North Macedonia and Serbia are Southern Europe and
# Georgia is Central Asia.
EASTERN_EUROPE_WIDE = sorted(set(d.loc[d.GlobalRegion.eq(12), "COUNTRY_ISO3"])
                             | {"ALB", "BIH", "MKD", "MNE", "SRB", "GEO"})

COUNTRY_REGION = d.groupby("COUNTRY_ISO3").GlobalRegion.first()
COUNTRY_INCOME = d.groupby("COUNTRY_ISO3").CountryIncomeLevel.first()

ind = d[d.COUNTRY_ISO3 == "IND"]
bra = d[d.COUNTRY_ISO3 == "BRA"]

INDIA_STATES = {  # REGION_IND codes shown on the Chart 5.8 map
    1: "andhra_pradesh", 3: "assam", 4: "bihar", 6: "chhattisgarh", 7: "delhi", 9: "gujarat", 10: "haryana",
    11: "himachal_pradesh", 13: "jharkhand", 14: "karnataka", 15: "kerala", 16: "madhya_pradesh",
    17: "maharashtra", 22: "odisha", 24: "punjab", 25: "rajasthan", 27: "tamil_nadu", 29: "uttar_pradesh",
    30: "uttarakhand", 31: "west_bengal", 32: "telangana",
}
BRAZIL_STATES = {  # REGION_BRA codes shown on the Chart 5.11 map
    13: "amazonas", 15: "para", 17: "tocantins", 21: "maranhao", 23: "ceara", 24: "rio_grande_do_norte",
    25: "paraiba", 26: "pernambuco", 27: "alagoas", 28: "sergipe", 29: "bahia", 31: "minas_gerais",
    33: "rio_de_janeiro", 35: "sao_paulo", 41: "parana", 42: "santa_catarina", 43: "rio_grande_do_sul",
    50: "mato_grosso_do_sul", 52: "goias", 53: "federal_district", 54: "espirito_santo", 55: "amapa",
    56: "rondonia",
}

# --- Gallup World Poll item ------------------------------------------------------
# Every urban-rural figure uses the degree of urbanisation (cities / towns and
# semi-dense areas / rural areas), a Gallup World Poll item that is not in the
# public release. GWP_DEGURBA is a placeholder name, coded 1 = cities,
# 2 = towns and semi-dense areas, 3 = rural areas. The public Urbanicity
# variable (self-reported) does not reproduce these figures (see README).


@lru_cache(maxsize=None)
def urban():
    return merge_gallup(d, ["GWP_DEGURBA"])


# --- Helpers -------------------------------------------------------------------


def named(series, names, prefix=""):
    """Rename a pct(..., by=...) result: {prefix + names[code]: value}."""
    return {f"{prefix}{names[k]}": v for k, v in series.items() if k in names}


def by2(df, var, codes, g1, names1, g2, names2):
    """% by two groups, keys '<name1>_<name2>'."""
    r = pct(df, var, codes, by=[g1, g2])
    return {f"{names1[a]}_{names2[b]}": v for (a, b), v in r.items() if a in names1 and b in names2}


def country(var, codes, df=None):
    """% by country (ISO3). Within a country PROJWT is proportional to WGT."""
    return pct(d if df is None else df, var, codes, by="COUNTRY_ISO3")


def top(series, n):
    """ISO3 codes of the n highest values, sorted alphabetically, as text."""
    return "; ".join(sorted(series.sort_values(ascending=False).index[:n]))


def rank_of(series, key):
    return int((series > series[key]).sum() + 1)


# --- Executive summary ------------------------------------------------------------


@report.finding("X01")
def respondents():
    return len(d)


@report.finding("X02")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X03")
def plastic_or_food():
    return pct(d, "WP23341", [1, 2])


@report.finding("X04")
def plastic():
    return pct(d, "WP23341", [1])


@report.finding("X05")
def food():
    return pct(d, "WP23341", [2])


@report.finding("X06")
def separates():
    return pct(d, "WP23342", [1])


@report.finding("X07")
def separates_high_income():
    return pct(d, "WP23342", [1], by="CountryIncomeLevel")[4]


@report.finding("X08")
def separates_low_income():
    return pct(d, "WP23342", [1], by="CountryIncomeLevel")[1]


@report.finding("X09")
def government_collection():
    return pct(d, "WP23343", [2])


@report.finding("X10")
def collected_low_income_cities():
    u = urban()
    return pct(u[u.CountryIncomeLevel == 1], "collected", [1], by="GWP_DEGURBA")[1]


@report.finding("X11")
def collected_low_income_rural():
    u = urban()
    return pct(u[u.CountryIncomeLevel == 1], "collected", [1], by="GWP_DEGURBA")[3]


@report.finding("X12")
def uncontrolled_four_in_ten():
    return pct(d, "WP23343", [1, 5, 6])


@report.finding("X13")
def burns():
    return pct(d, "WP23343", [1])


@report.finding("X14")
def burns_central_western_africa():
    return pct(d, "WP23343", [1], by="GlobalRegion")[2]


@report.finding("X15")
def burns_eastern_africa():
    return pct(d, "WP23343", [1], by="GlobalRegion")[1]


@report.finding("X16")
def burns_indonesia():
    return country("burns", [1])["IDN"]


@report.finding("X17")
def burns_indonesia_half():
    return country("burns", [1])["IDN"]


@report.finding("X18")
def separated_and_collected():
    return pct(d, "quadrant", [1])


@report.finding("X19")
def separated_or_collected_not_both():
    return pct(d, "quadrant", [2, 3])


@report.finding("X20")
def separated_and_collected_high():
    return pct(d, "quadrant", [1], by="CountryIncomeLevel")[4]


@report.finding("X21")
def separated_and_collected_low():
    return pct(d, "quadrant", [1], by="CountryIncomeLevel")[1]


@report.finding("X22")
def neither_low():
    return pct(d, "quadrant", [4], by="CountryIncomeLevel")[1]


# --- Chapter 2: The material world --------------------------------------------------


@report.finding("X23")
def household_dust():
    return pct(d, "WP23341", [5])


@report.finding("X24")
def cardboard():
    return pct(d, "WP23341", [3])


@report.finding("X25")
def cans():
    return pct(d, "WP23341", [4])


@report.finding("X26")
def ash():
    return pct(d, "WP23341", [6])


@report.finding("X27")
def glass():
    return pct(d, "WP23341", [7])


@report.finding("X28")
def other_material():
    return pct(d, "WP23341", [8])


MATERIALS = {"plastic": [1], "food": [2], "dust": [5], "cardboard": [3], "cans": [4], "other": [8], "ash": [6], "glass": [7]}


@report.finding("C2_1")
def primary_material():
    return {name: pct(d, "WP23341", codes) for name, codes in MATERIALS.items()}


@report.finding("C2_2")
def material_by_income():
    groups = {"plastic": [1], "food": [2], "cardboard": [3], "dust": [5], "other": [4, 6, 7, 8, 98, 99]}
    out = {}
    for name, codes in groups.items():
        out.update({f"{k}_{name}": v for k, v in named(pct(d, "WP23341", codes, by="CountryIncomeLevel"), INCOME).items()})
    return out


@report.finding("X29")
def plastic_high():
    return pct(d, "WP23341", [1], by="CountryIncomeLevel")[4]


@report.finding("X30")
def plastic_food_middle():
    p = pct(d, "WP23341", [1], by="CountryIncomeLevel")
    f = pct(d, "WP23341", [2], by="CountryIncomeLevel")
    return {"upper_middle_plastic": p[3], "upper_middle_food": f[3], "lower_middle_plastic": p[2], "lower_middle_food": f[2]}


@report.finding("X31")
def plastic_low():
    return pct(d, "WP23341", [1], by="CountryIncomeLevel")[1]


@report.finding("X32")
def food_high():
    return pct(d, "WP23341", [2], by="CountryIncomeLevel")[4]


@report.finding("X33")
def food_other_income():
    return named(pct(d, "WP23341", [2], by="CountryIncomeLevel"), {1: "low", 2: "lower_middle", 3: "upper_middle"})


@report.finding("X34")
def dust_ratio_low_high():
    r = pct(d, "WP23341", [5], by="CountryIncomeLevel")
    return r[1] / r[4]


@report.finding("C2_3")
def categories_by_income():
    return {**named(pct(d, "food_green", [1], by="CountryIncomeLevel"), INCOME, "food_green_"),
            **named(pct(d, "dry", [1], by="CountryIncomeLevel"), INCOME, "dry_")}


@report.finding("X35")
def food_green():
    return pct(d, "food_green", [1])


@report.finding("C2_4")
def categories_by_region():
    return {**named(pct(d, "food_green", [1], by="GlobalRegion"), REGION, "food_green_"),
            **named(pct(d, "dry", [1], by="GlobalRegion"), REGION, "dry_")}


@report.finding("X36")
def regions_food_green_above_dry():
    return int((pct(d, "food_green", [1], by="GlobalRegion") > pct(d, "dry", [1], by="GlobalRegion")).sum())


@report.finding("X37")
def dry_four_regions():
    r = named(pct(d, "dry", [1], by="GlobalRegion"), REGION)
    return {k: r[k] for k in ("northern_western_europe", "southern_europe", "australia_nz", "northern_america")}


@report.finding("X38")
def plastic_top10_composition():
    top10 = country("WP23341", [1]).sort_values(ascending=False).index[:10]
    return {"europe": int(COUNTRY_REGION[top10].isin(EUROPE).sum()),
            "southeastern_asia": int(COUNTRY_REGION[top10].eq(9).sum()),
            "lower_middle": int(COUNTRY_INCOME[top10].eq(2).sum())}


TABLE_2_1 = {  # material: (codes, countries printed in Table 2.1)
    "plastic": ([1], ["SVN", "CZE", "SWZ", "SLV", "NLD", "BEL", "KHM", "ITA", "MMR", "IDN"]),
    "food": ([2], ["COD", "CIV", "GAB", "MAR", "LBN", "KWT", "PAK", "AZE", "MYS", "ISR"]),
    "dust": ([5], ["ETH", "AFG", "SLE", "MWI", "NER", "ZWE", "BFA", "TCD", "ZMB", "MLI"]),
    "cardboard": ([3], ["ISL", "SWE", "USA", "GBR", "IRL", "CAN", "TWN", "AUT", "AUS", "HRV"]),
}


@report.finding("T2_1")
def top10_by_material():
    out = {}
    for name, (codes, printed) in TABLE_2_1.items():
        r = country("WP23341", codes)
        out.update({f"{name}_{iso}": r[iso] for iso in printed})
        out[f"{name}_top10"] = top(r, 10)
    return out


@report.finding("X39")
def top_food_dust_countries():
    f, u = country("WP23341", [2]), country("WP23341", [5])
    return {"food_COD": f["COD"], "food_CIV": f["CIV"], "food_GAB": f["GAB"], "dust_AFG": u["AFG"]}


@report.finding("X40")
def dry_by_sex():
    return named(pct(d, "dry", [1], by="Gender"), SEX)


def sex_gap(var, group):
    """Men minus women, % with `var` = 1, by `group`."""
    r = pct(d, var, [1], by=[group, "Gender"]).unstack()
    return r[1] - r[2]


@report.finding("X41")
def sex_gap_over_5():
    # Either gap: men minus women for dry recyclables, or women minus men for
    # food and green waste (Eastern Europe: 4.9 and 5.4 points).
    dry, food_green = sex_gap("dry", "GlobalRegion"), -sex_gap("food_green", "GlobalRegion")
    return {REGION[k]: int(max(dry[k], food_green[k]) > 5) for k in (8, 7, 12)}


@report.finding("C2_5")
def categories_by_sex():
    out = {}
    for code, sex in SEX.items():
        out[f"{sex}_food_green"] = pct(d, "food_green", [1], by="Gender")[code]
        out[f"{sex}_dry"] = pct(d, "dry", [1], by="Gender")[code]
    return out


# "Differences of 10 percentage points or more" (page 12) are gaps that round
# to 10 or more: Ukraine (9.9) and Kyrgyzstan (9.6) are in the report's list.


@report.finding("X42")
def men_dry_10_points():
    g = sex_gap("dry", "COUNTRY_ISO3")
    hit = g[g >= 9.5]
    return {"count": len(hit), "countries": "; ".join(sorted(hit.index))}


@report.finding("X43")
def women_dry_10_points():
    g = -sex_gap("dry", "COUNTRY_ISO3")
    hit = g[g >= 9.5]
    return {"count": len(hit), "countries": "; ".join(sorted(hit.index))}


@report.finding("C2_6")
def dry_by_income_age():
    return by2(d, "dry", [1], "CountryIncomeLevel", INCOME, "AgeGroups4", AGE)


MIN_AGE_BASE = 100


def age_gap(var):
    """% with `var` = 1 aged 15-29 and 65+, by country.

    Countries with fewer than 100 respondents in either age group are left
    out, which reproduces the country list in Chart 3.4 (Saudi Arabia, for
    example, has three respondents aged 65+).
    """
    r = pct(d, var, [1], by=["COUNTRY_ISO3", "AgeGroups4"]).unstack()
    n = d.groupby(["COUNTRY_ISO3", "AgeGroups4"]).size().unstack()
    keep = (n[1] >= MIN_AGE_BASE) & (n[4] >= MIN_AGE_BASE)
    return r.loc[keep, 1], r.loc[keep, 4]


@report.finding("T2_2")
def dry_age_gap_countries():
    young, old = age_gap("dry")
    gap = young - old  # ranking uses the unrounded gap
    out = {}
    for iso in ["BGR", "TWN", "MUS", "SVK", "PRT"]:
        # The printed gap is the difference of the rounded figures.
        out.update({f"{iso}_15_29": young[iso], f"{iso}_65plus": old[iso],
                    f"{iso}_gap": round(young[iso]) - round(old[iso])})
    out["top5"] = top(gap, 5)
    return out


@report.finding("X44")
def dry_age_gap_over_25():
    young, old = age_gap("dry")
    return int(((young - old) > 25).sum())


@report.finding("C2_7")
def dry_by_income_education():
    return by2(d, "dry", [1], "CountryIncomeLevel", INCOME, "Education", EDUCATION)


@report.finding("X45")
def dry_cities_rural():
    return named(pct(urban(), "dry", [1], by="GWP_DEGURBA"), {1: "cities", 3: "rural"})


@report.finding("X46")
def dry_cities_rural_low_income():
    u = urban()
    return named(pct(u[u.CountryIncomeLevel == 1], "dry", [1], by="GWP_DEGURBA"), {1: "cities", 3: "rural"})


# --- Chapter 3: Dividing lines in waste separation ----------------------------------

SEPARATION = {"yes": [1], "sometimes": [3], "no": [2]}


@report.finding("X47")
def does_not_separate():
    return pct(d, "WP23342", [2])


@report.finding("X48")
def sometimes_separates():
    return pct(d, "WP23342", [3])


@report.finding("C3_1")
def separation_by_region():
    out = {f"global_{s}": pct(d, "WP23342", codes) for s, codes in SEPARATION.items()}
    for s, codes in SEPARATION.items():
        out.update({f"{k}_{s}": v for k, v in named(pct(d, "WP23342", codes, by="GlobalRegion"), REGION).items()})
    return out


@report.finding("X49")
def separation_nine_in_ten():
    r = named(pct(d, "WP23342", [1], by="GlobalRegion"), REGION)
    return {k: r[k] for k in ("australia_nz", "northern_western_europe")}


@report.finding("X50")
def separation_asia_africa():
    r = named(pct(d, "WP23342", [1], by="GlobalRegion"), REGION)
    return {k: r[k] for k in ("eastern_asia", "southeastern_asia", "central_asia", "southern_asia",
                              "southern_africa", "central_western_africa")}


@report.finding("X51")
def sometimes_china():
    return country("WP23342", [3])["CHN"]


@report.finding("X52")
def sometimes_not_china():
    return pct(d[d.COUNTRY_ISO3 != "CHN"], "WP23342", [3])


@report.finding("X53")
def separates_eastern_asia_without_china():
    return pct(d[(d.GlobalRegion == 8) & (d.COUNTRY_ISO3 != "CHN")], "WP23342", [1])


@report.finding("C3_2")
def separation_by_income():
    out = {}
    for s, codes in SEPARATION.items():
        out.update({f"{k}_{s}": v for k, v in named(pct(d, "WP23342", codes, by="CountryIncomeLevel"), INCOME).items()})
    return out


@report.finding("X54")
def separation_ratio_high_low():
    r = pct(d, "WP23342", [1], by="CountryIncomeLevel")
    return r[4] / r[1]


@report.finding("X55")
def separation_middle_income():
    r = pct(d, "WP23342", [1], by="CountryIncomeLevel")
    return {"upper_middle": r[3], "lower_middle": r[2]}


TABLE_3_1 = {"yes": ["KOR", "ISL", "BEL", "ITA", "SVN", "MLT", "TWN", "CZE", "LUX", "SWE"],
             "no": ["GAB", "CIV", "XKX", "TGO", "CMR", "BEN", "LBR", "COG", "MNE", "ALB"]}


@report.finding("T3_1")
def separation_top10():
    out = {}
    for s, printed in TABLE_3_1.items():
        r = country("WP23342", SEPARATION[s])
        out.update({f"{s}_{iso}": r[iso] for iso in printed})
        out[f"{s}_top10"] = top(r, 10)
    return out


@report.finding("X56")
def separation_top10_europe_eastern_asia():
    top10 = country("WP23342", [1]).sort_values(ascending=False).index[:10]
    return int(COUNTRY_REGION[top10].isin(EUROPE + [8]).sum())


@report.finding("X57")
def no_separation_top10_composition():
    top10 = country("WP23342", [2]).sort_values(ascending=False).index[:10]
    return {"sub_saharan_africa": int(COUNTRY_REGION[top10].isin(SUB_SAHARAN_AFRICA).sum()),
            "eastern_europe": int(top10.isin(EASTERN_EUROPE_WIDE).sum())}


@report.finding("X58")
def separation_young_old():
    yes = pct(d, "WP23342", [1], by="AgeGroups4")
    return {"15_29_yes": yes[1], "15_29_no": pct(d, "WP23342", [2], by="AgeGroups4")[1], "65plus_yes": yes[4]}


@report.finding("C3_3")
def separation_by_age():
    out = {}
    for s, codes in SEPARATION.items():
        out.update({f"{k}_{s}": v for k, v in named(pct(d, "WP23342", codes, by="AgeGroups4"), AGE).items()})
    return out


CHART_3_4 = ["BRA", "GRC", "ARG", "URY", "VEN", "PER", "PHL", "DOM", "SLV", "HRV", "COL", "CRI", "BGR", "PAN", "CHL"]


@report.finding("C3_4")
def separation_age_gap_countries():
    young, old = age_gap("separated")
    gap = old - young  # ranking uses the unrounded gap
    out = {}
    for iso in CHART_3_4:
        # The printed gap is the difference of the rounded figures.
        out.update({f"{iso}_15_29": young[iso], f"{iso}_65plus": old[iso],
                    f"{iso}_gap": round(old[iso]) - round(young[iso])})
    means = pct(d, "separated", [1], by="AgeGroups4")
    out.update({"mean_15_29": means[1], "mean_65plus": means[4], "top15": top(gap, 15)})
    return out


@report.finding("X59")
def separation_latin_america():
    return {"latin_america": pct(d, "WP23342", [1], by="GlobalRegion")[5], "global": pct(d, "WP23342", [1])}


@report.finding("X60")
def age_gap_top15_latin_america():
    young, old = age_gap("separated")
    top15 = (old - young).sort_values(ascending=False).index[:15]
    return int(COUNTRY_REGION[top15].eq(5).sum())


@report.finding("X61")
def separation_by_sex_income():
    r = named(pct(d, "WP23342", [1], by="Gender"), SEX)
    r.update({k: v for k, v in by2(d, "separated", [1], "CountryIncomeLevel", INCOME, "Gender", SEX).items()
              if k.startswith(("upper_middle", "lower_middle"))})
    return r


@report.finding("C3_5")
def separation_by_sex():
    out = {}
    for s, codes in SEPARATION.items():
        out.update({f"{k}_{s}": v for k, v in named(pct(d, "WP23342", codes, by="Gender"), SEX).items()})
    return out


@report.finding("X62")
def sex_differences_two_regions():
    sep = by2(d, "separated", [1], "GlobalRegion", REGION, "Gender", SEX)
    dry = by2(d, "dry", [1], "GlobalRegion", REGION, "Gender", SEX)
    out = {}
    for region in ("northern_america", "southern_asia"):
        for sex in ("women", "men"):
            out[f"{region}_sep_{sex}"] = sep[f"{region}_{sex}"]
            out[f"{region}_dry_{sex}"] = dry[f"{region}_{sex}"]
    return out


@report.finding("X63")
def separation_by_education():
    return named(pct(d, "WP23342", [1], by="Education"), EDUCATION)


@report.finding("X64")
def separation_by_climate():
    return named(pct(d, "WP23342", [1], by="WP20719"), CLIMATE)


@report.finding("X65")
def separation_by_climate_high_income():
    return named(pct(d[d.CountryIncomeLevel == 4], "WP23342", [1], by="WP20719"), CLIMATE)


@report.finding("C3_6")
def separation_by_income_climate():
    return by2(d, "separated", [1], "CountryIncomeLevel", INCOME, "WP20719", CLIMATE)


# --- Chapter 4: The open burning of household waste -----------------------------------

METHODS = {"government": [2], "landfill": [5], "burns": [1], "street": [6], "community": [3], "private": [4], "other": [96]}


@report.finding("C4_1")
def disposal_methods():
    return {name: pct(d, "WP23343", codes) for name, codes in METHODS.items()}


@report.finding("X66")
def government_vs_next():
    r = {code: pct(d, "WP23343", [code]) for code in [1, 3, 4, 5, 6, 96]}
    return pct(d, "WP23343", [2]) / max(r.values())


@report.finding("X67")
def uncontrolled():
    return pct(d, "WP23343", [1, 5, 6])


@report.finding("X68")
def dumps_outside():
    return pct(d, "WP23343", [6])


@report.finding("X69")
def collected():
    return pct(d, "collected", [1])


@report.finding("X70")
def burning_rank():
    shares = {code: pct(d, "WP23343", [code]) for code in range(1, 7)}
    return sum(v > shares[1] for v in shares.values()) + 1


@report.finding("X71")
def takes_to_dump():
    return pct(d, "WP23343", [5])


@report.finding("X72")
def burns_by_income():
    return named(pct(d, "burns", [1], by="CountryIncomeLevel"), INCOME)


@report.finding("X73")
def burns_europe_max():
    return pct(d, "burns", [1], by="GlobalRegion")[[12, 13, 14, 15]].max()


@report.finding("C4_2")
def burns_by_region():
    return {**named(pct(d, "burns", [1], by="GlobalRegion"), REGION), "global": pct(d, "burns", [1])}


def burning_most_common():
    """Countries where burning is the most common of the four methods (Chart 4.3).

    Compared on shares rounded to whole numbers: Benin burns 29.3% and takes
    28.7% to the tip (29% each) and is not in the chart.
    """
    shares = pct(d, "main_method", [1], by="COUNTRY_ISO3").to_frame("burn")
    for code, name in [(2, "dump"), (3, "tip"), (4, "collected")]:
        shares[name] = pct(d, "main_method", [code], by="COUNTRY_ISO3")
    shares = shares.round()
    return shares.index[shares.burn > shares[["dump", "tip", "collected"]].max(axis=1)]


@report.finding("X74")
def majority_burn():
    return int((country("burns", [1]) > 50).sum())


@report.finding("X75")
def burning_most_common_count():
    return len(burning_most_common())


@report.finding("X76")
def burning_most_common_outside_africa_asia():
    return int((~COUNTRY_REGION[burning_most_common()].isin(AFRICA + ASIA)).sum())


@report.finding("C4_3")
def burning_countries():
    r = country("burns", [1])
    most = burning_most_common()
    return {**{iso: r[iso] for iso in most}, "global": pct(d, "burns", [1]), "countries": "; ".join(sorted(most))}


def country_rates():
    rates = country("collected", [1]).to_frame("collected")
    rates["burns"] = country("burns", [1])
    rates["separated"] = country("separated", [1])
    rates["dry"] = country("dry", [1])
    return rates


@report.finding("X77")
def collection_burning_correlation():
    rates = country_rates()
    return rates.collected.corr(rates.burns)


@report.finding("C4_4")
def collection_vs_burning():
    # Scatter plot: no values are printed, so these have nothing to compare with.
    rates = country_rates()
    return {f"{iso}_{m}": rates.loc[iso, m] for iso in rates.index for m in ("collected", "burns")}


@report.finding("X78")
def eswatini():
    r = country("burns", [1])
    return {"SWZ": r["SWZ"], "rank": rank_of(r, "SWZ")}


@report.finding("X79")
def eswatini_three_in_four():
    return country("burns", [1])["SWZ"]


# --- Chapter 5: Controlled disposal: an urban-rural divide -----------------------------


@report.finding("C5_1")
def collected_by_region():
    return {**named(pct(d, "collected", [1], by="GlobalRegion"), REGION), "global": pct(d, "collected", [1])}


@report.finding("X80")
def collected_three_in_five():
    r = named(pct(d, "collected", [1], by="GlobalRegion"), REGION)
    return {k: r[k] for k in ("eastern_asia", "middle_east", "central_asia", "northern_africa", "southern_africa")}


@report.finding("X81")
def regions_minority_collected():
    return int((pct(d, "collected", [1], by="GlobalRegion") < 50).sum())


@report.finding("X82")
def collected_asia_africa():
    r = named(pct(d, "collected", [1], by="GlobalRegion"), REGION)
    return {k: r[k] for k in ("southeastern_asia", "southern_asia", "eastern_asia", "central_asia",
                              "central_western_africa", "eastern_africa")}


@report.finding("X83")
def collected_by_income():
    return named(pct(d, "collected", [1], by="CountryIncomeLevel"), INCOME)


def collected_income_urban():
    return by2(urban(), "collected", [1], "CountryIncomeLevel", INCOME, "GWP_DEGURBA", URBAN)


@report.finding("X84")
def collected_income_urban_text():
    r = collected_income_urban()
    return {k: v for k, v in r.items() if not k.startswith("low_") or k == "low_towns"}


@report.finding("X85")
def collected_austria_denmark():
    u = urban()
    return by2(u[u.COUNTRY_ISO3.isin(["AUT", "DNK"])], "collected", [1], "COUNTRY_ISO3",
               {"AUT": "AUT", "DNK": "DNK"}, "GWP_DEGURBA", URBAN)


@report.finding("C5_2")
def collected_by_income_urban():
    means = named(pct(urban(), "collected", [1], by="GWP_DEGURBA"), URBAN, "mean_")
    return {**collected_income_urban(), **means}


def region_urban_gap():
    r = pct(urban(), "collected", [1], by=["GlobalRegion", "GWP_DEGURBA"]).unstack()
    return r[1], r[3]  # cities, rural


@report.finding("X86")
def europe_80_to_90():
    cities, rural = region_urban_gap()
    values = list(cities[EUROPE]) + list(rural[EUROPE])
    return int(min(values) >= 79.5 and max(values) < 90.5)


@report.finding("X87")
def urban_gap_high_income_regions():
    cities, rural = region_urban_gap()
    return {"australia_nz": cities[15] - rural[15], "northern_america": cities[6] - rural[6]}


@report.finding("X88")
def urban_gap_over_50():
    cities, rural = region_urban_gap()
    return {"southern_africa": int(cities[4] - rural[4] > 50), "eastern_africa": int(cities[1] - rural[1] > 50)}


@report.finding("C5_3")
def collected_by_region_urban():
    cities, rural = region_urban_gap()
    out = {}
    for code, name in REGION.items():
        out.update({f"{name}_rural": rural[code], f"{name}_cities": cities[code],
                    f"{name}_gap": round(cities[code]) - round(rural[code])})  # from the rounded figures
    means = pct(urban(), "collected", [1], by="GWP_DEGURBA")
    out.update({"mean_rural": means[3], "mean_cities": means[1]})
    return out


def country_urban_gap():
    r = pct(urban(), "collected", [1], by=["COUNTRY_ISO3", "GWP_DEGURBA"]).unstack()
    return r[1], r[3]


@report.finding("X89")
def countries_urban_gap_60():
    # Gaps as printed in Chart 5.4: differences of the rounded figures.
    cities, rural = country_urban_gap()
    return int(((cities.round() - rural.round()) >= 60).sum())


CHART_5_4 = ["KHM", "SEN", "NPL", "NIC", "PRY", "TZA", "BOL", "MNG", "MLI", "GTM", "KGZ", "HND", "IRQ", "GHA", "NAM"]


@report.finding("C5_4")
def collected_country_urban_gap():
    cities, rural = country_urban_gap()
    gap = cities - rural
    out = {}
    for iso in CHART_5_4:
        out.update({f"{iso}_rural": rural[iso], f"{iso}_cities": cities[iso],
                    f"{iso}_gap": round(cities[iso]) - round(rural[iso])})  # from the rounded figures
    means = pct(urban(), "collected", [1], by="GWP_DEGURBA")
    out.update({"mean_rural": means[3], "mean_cities": means[1], "top15": top(gap, 15)})
    return out


def india_urban():
    u = urban()
    return u[u.COUNTRY_ISO3 == "IND"]


@report.finding("X90")
def india_urban_text():
    u = india_urban()
    c = named(pct(u, "collected", [1], by="GWP_DEGURBA"), URBAN)
    b = named(pct(u, "burns", [1], by="GWP_DEGURBA"), URBAN)
    return {"cities_collected": c["cities"], "cities_burns": b["cities"], "towns_collected": c["towns"],
            "rural_collected": c["rural"], "rural_burns": b["rural"], "towns_burns": b["towns"]}


@report.finding("C5_5")
def india_collected_burns():
    u = india_urban()
    return {**named(pct(u, "burns", [1], by="GWP_DEGURBA"), {k: f"{v}_burns" for k, v in URBAN.items()}),
            **named(pct(u, "collected", [1], by="GWP_DEGURBA"), {k: f"{v}_collected" for k, v in URBAN.items()})}


@report.finding("X91")
def india_burners_not_separating():
    return pct(ind[ind.burns == 1], "separated", [0])


@report.finding("C5_6")
def india_plastic_among_burners_collected():
    # % whose main waste is plastic, among households that burn / have their
    # waste collected (the reading that fits the text; see README).
    u = india_urban()
    return {**named(pct(u[u.burns == 1], "WP23341", [1], by="GWP_DEGURBA"), {k: f"{v}_burns" for k, v in URBAN.items()}),
            **named(pct(u[u.collected == 1], "WP23341", [1], by="GWP_DEGURBA"),
                    {k: f"{v}_collected" for k, v in URBAN.items()})}


@report.finding("C5_7")
def india_burns_quintile_urban():
    return by2(india_urban(), "burns", [1], "GWP_DEGURBA", URBAN, "INCOME_5", QUINTILE)


@report.finding("C5_8")
def india_burns_by_state():
    return named(pct(ind, "burns", [1], by="REGION_IND"), INDIA_STATES)


@report.finding("X92")
def india_delhi_assam():
    r = named(pct(ind, "burns", [1], by="REGION_IND"), INDIA_STATES)
    s = pct(ind, "burns", [1], by="REGION_IND")
    return {"delhi": r["delhi"], "assam": r["assam"], "assam_rank": rank_of(s, 3)}


@report.finding("X93")
def delhi_air_quality():
    # Needs the Gallup World Poll item on satisfaction with air quality where
    # the respondent lives (placeholder name; 2 = dissatisfied assumed).
    g = merge_gallup(ind, ["GWP_AIR_QUALITY_SATISFACTION"])
    g["delhi"] = np.where(g.REGION_IND == 7, 1, 2)
    r = pct(g, "GWP_AIR_QUALITY_SATISFACTION", [2], by="delhi")
    return {"delhi": r[1], "rest": r[2]}


def brazil_urban():
    u = urban()
    return u[u.COUNTRY_ISO3 == "BRA"]


@report.finding("X94")
def brazil_burns_urban():
    return named(pct(brazil_urban(), "burns", [1], by="GWP_DEGURBA"), URBAN)


@report.finding("X95")
def brazil_rural_poorest_richest():
    u = brazil_urban()
    r = pct(u[u.GWP_DEGURBA == 3], "burns", [1], by="INCOME_5")
    return {"rural_q1": r[1], "rural_q5": r[5]}


@report.finding("C5_9")
def brazil_collected_burns():
    u = brazil_urban()
    return {**named(pct(u, "burns", [1], by="GWP_DEGURBA"), {k: f"{v}_burns" for k, v in URBAN.items()}),
            **named(pct(u, "collected", [1], by="GWP_DEGURBA"), {k: f"{v}_collected" for k, v in URBAN.items()})}


@report.finding("C5_10")
def brazil_burns_quintile_urban():
    return by2(brazil_urban(), "burns", [1], "GWP_DEGURBA", URBAN, "INCOME_5", QUINTILE)


@report.finding("C5_11")
def brazil_burns_by_state():
    return named(pct(bra, "burns", [1], by="REGION_BRA"), BRAZIL_STATES)


@report.finding("X96")
def brazil_maranhao_para():
    r = named(pct(bra, "burns", [1], by="REGION_BRA"), BRAZIL_STATES)
    return {"maranhao": r["maranhao"], "para": r["para"]}


# --- Chapter 6: Global household waste: further analysis --------------------------------


@report.finding("X97")
def quadrants_global():
    return {name: pct(d, "quadrant", [code]) for code, name in QUADRANT.items() if code > 1}


@report.finding("X98")
def quadrants_middle_income():
    q = {code: pct(d, "quadrant", [code], by="CountryIncomeLevel") for code in QUADRANT}
    return {"upper_middle_both": q[1][3], "upper_middle_collected_only": q[2][3],
            "lower_middle_separated_only": q[3][2], "lower_middle_neither": q[4][2]}


@report.finding("C6_1")
def quadrants_by_income():
    out = {f"global_{name}": pct(d, "quadrant", [code]) for code, name in QUADRANT.items()}
    for code, name in QUADRANT.items():
        out.update({f"{k}_{name}": v for k, v in named(pct(d, "quadrant", [code], by="CountryIncomeLevel"), INCOME).items()})
    return out


@report.finding("X99")
def collected_only_top10_composition():
    r = country("quadrant", [2]).sort_values(ascending=False)
    top10, top5 = r.index[:10], r.index[:5]
    return {"eastern_europe": int(top10.isin(EASTERN_EUROPE_WIDE).sum()),
            "top5_eastern_europe": int(top5.isin(EASTERN_EUROPE_WIDE).sum()),
            "top5_over_two_thirds": int((r.iloc[:5] > 200 / 3).all())}


TABLE_6_1 = ["XKX", "MNE", "BGR", "BIH", "SRB", "KWT", "PSE", "MKD", "GEO", "CHL"]
TABLE_6_2 = ["LKA", "NPL", "BGD", "MWI", "UGA", "TJK", "SWE", "KHM", "KEN", "HND"]


@report.finding("T6_1")
def collected_not_separated_top10():
    r = country("quadrant", [2])
    return {**{iso: r[iso] for iso in TABLE_6_1}, "top10": top(r, 10)}


@report.finding("T6_2")
def separated_not_collected_top10():
    r = country("quadrant", [3])
    return {**{iso: r[iso] for iso in TABLE_6_2}, "top10": top(r, 10)}


@report.finding("X100")
def separated_not_collected_south_asia():
    r = country("quadrant", [3])
    return {iso: r[iso] for iso in ("LKA", "NPL", "BGD", "IND")}


@report.finding("X101")
def fate_of_separated_uncollected():
    s = d[d.quadrant == 3]
    burns = pct(s, "WP23343", [1], by="CountryIncomeLevel")
    return {"global_landfill": pct(s, "WP23343", [5]), "global_burns": pct(s, "WP23343", [1]),
            "low_burns": burns[1], "lower_middle_burns": burns[2]}


@report.finding("C6_2")
def collected_separated_dry():
    # Bubble chart: no values are printed, so these have nothing to compare
    # with. Also returns the country-level correlation between separation and
    # collection within each income group (the text says it is negative only
    # in low-income countries).
    rates = country_rates()
    out = {f"{iso}_{m}": rates.loc[iso, m] for iso in rates.index for m in ("collected", "separated", "dry")}
    for code, name in INCOME.items():
        r = rates[COUNTRY_INCOME[rates.index] == code]
        out[f"corr_{name}"] = r.collected.corr(r.separated)
    return out


if __name__ == "__main__":
    sys.exit(report.run())
