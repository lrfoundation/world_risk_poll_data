"""Reproduce World Risk Poll 2021: A Resilient World? Understanding vulnerability in a changing climate.

Run from the repository root:
    python reports/WRP_2021/core_a_resilient_world/reproduce.py

Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

DK = [98, 99]
DISCRIMINATION = ["WP22259", "WP22260", "WP22261", "WP22262", "WP22263"]  # skin, religion, nationality, sex, disability
SERVICES = {"electricity": "WP22254", "water": "WP22255", "food": "WP22256",
            "medical": "WP22257", "telephone": "WP22258"}

d = load_wave(2021, [
    "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel",
    "Gender", "Education", "Urbanicity", "INCOME_5", "resilience_index",
    "WP20711", "WP20719", "WP22228", "WP22229", "WP22230", "WP22231", "WP22469", "WP22525",
    "WP22232", "WP22240", "WP22241", "WP22242", "WP22243", "WP22244", "WP22245", "WP22247",
    "WP22252", "WP22253", *SERVICES.values(), *DISCRIMINATION,
])

# --- Derived variables ---------------------------------------------------------

# Groupings used as keys. CountryIncomeLevel 9 (Venezuela, not classified)
# has no income key, so it drops out of every income breakdown.
d["region"] = d.GlobalRegion.map({
    1: "eastern_africa", 2: "central_western_africa", 3: "northern_africa", 4: "southern_africa",
    5: "latin_america", 6: "northern_america", 7: "central_asia", 8: "eastern_asia",
    9: "southeastern_asia", 10: "southern_asia", 11: "middle_east", 12: "eastern_europe",
    13: "northern_western_europe", 14: "southern_europe", 15: "australia_nz",
})
d["income"] = d.CountryIncomeLevel.map({1: "low_income", 2: "lower_middle", 3: "upper_middle", 4: "high_income"})
d["income3"] = d.CountryIncomeLevel.map({1: "low_income", 2: "middle_income", 3: "middle_income", 4: "high_income"})
d["income2"] = d.CountryIncomeLevel.map({1: "low_lower_middle", 2: "low_lower_middle",
                                         3: "upper_middle_high", 4: "upper_middle_high"})
# Urbanicity: large cities and their suburbs are one group ("large cities/suburbs").
d["urban"] = d.Urbanicity.map({1: "rural", 2: "small_town", 3: "large_city", 6: "large_city"})

# Basic needs (Chart 1.3), as in the Focus On: Risk and Gender pilot: the first
# question splits less / more than a month, follow-ups give weeks or months.
# 4 = less than a month, weeks not known; 9 = a month or more, months not known.
d["basic_needs"] = np.select(
    [d.WP22228.eq(1) & d.WP22229.isin([1, 2, 3]), d.WP22228.eq(1),
     d.WP22228.eq(2) & d.WP22230.isin([1, 2, 3, 4]), d.WP22228.eq(2)],
    [d.WP22229, 4, d.WP22230 + 4, 9], default=98,
)

# Government cares (Charts 2.6, Table 2.3): Vietnam was asked about "the
# authorities" (WP22469) and Myanmar about "the government of Myanmar"
# (WP22525) instead of WP22231. Merging them reproduces Chart 2.6.
d["gov_cares"] = d.WP22231.fillna(d.WP22469).fillna(d.WP22525)

# Any discrimination (Chart 2.5, X20): yes to any of the five types.
# Respondents in the three countries not asked count as "no" (as in the pilot).
d["any_discrimination"] = np.where(d[DISCRIMINATION].eq(1).any(axis=1), 1, 2)

# Type of the last disaster (Charts 4.1, 4.2): 0 = no disaster in the past
# five years (including don't know/refused to WP22245). WP22247 is asked of
# everyone who said yes; 50 = drought.
d["disaster_type"] = np.where(d.WP22245.eq(1), d.WP22247, 0)

# --- Helpers -------------------------------------------------------------------


def pick(values, *keys):
    """Some of the values of a Series: {key: value}."""
    return {k: values[k] for k in keys}


def by_category(df, var, categories, by):
    """% in each named category of `var` for each `by` group: {"<group>_<category>": %}."""
    out = {}
    for name, codes in categories.items():
        for group, value in pct(df, var, codes, by=by).items():
            out[f"{group}_{name}"] = value
    return out


def country_values(df, var, codes, isos):
    """% with `var` in `codes` for the listed countries, keyed by ISO3."""
    r = pct(df, var, codes, by="COUNTRY_ISO3")
    return {iso: r[iso] for iso in isos}


def names_by_gap(gaps, threshold, exclude=()):
    """Country names with gap > threshold, largest first, as "A; B; C"."""
    g = gaps.drop(list(exclude), errors="ignore").dropna()
    g = g[g > threshold].sort_values(ascending=False)
    return "; ".join(g.index)


def resilience_gap(df, by, high, low):
    """Country-level gap in mean Resilience Index between two groups of `by`."""
    m = wmean(df, "resilience_index", by=["Country", by]).unstack()
    return m[high] - m[low]


YES = [1]

# --- Executive summary ---------------------------------------------------------


@report.finding("X01")
def respondents():
    return len(d)


@report.finding("X02")
def countries():
    return d.COUNTRY_ISO3.nunique()


# --- Chapter 1: individual- and household-level indicators ---------------------

AGENCY = {"yes": [1], "no": [2], "depends": [3], "dk": DK}


@report.finding("X03")
def could_protect_text():
    return {k: pct(d, "WP22252", codes) for k, codes in AGENCY.items()}


@report.finding("C1_1")
def could_protect():
    return {k: pct(d, "WP22252", codes) for k, codes in AGENCY.items()}


@report.finding("X04")
def could_protect_by_income():
    return pct(d, "WP22252", YES, by="income3")


@report.finding("X05")
def could_protect_southern_africa():
    return pct(d, "WP22252", YES, by="region")["southern_africa"]


@report.finding("X06")
def could_protect_southeastern_asia():
    return pct(d, "WP22252", YES, by="region")["southeastern_asia"]


@report.finding("C1_2")
def could_protect_by_region():
    return pct(d, "WP22252", YES, by="region")


@report.finding("X07")
def basic_needs_less_than_month():
    return pct(d, "basic_needs", [1, 2, 3, 4])


@report.finding("X08")
def basic_needs_less_than_week():
    return pct(d, "basic_needs", [1])


@report.finding("X09")
def basic_needs_less_than_month_regions():
    return pick(pct(d, "basic_needs", [1, 2, 3, 4], by="region"), "southern_asia", "northern_africa")


@report.finding("C1_3")
def basic_needs_by_region():
    return by_category(d, "basic_needs", {
        "lt_week": [1], "week_to_month": [2, 3, 4], "month_to_3": [5, 6, 7], "4_plus": [8], "dk": [9, 98],
    }, by="region")


# Internet access (WP16056) and mobile phone (WP17626) are Gallup World Poll
# items that are not in the public release.
@report.finding("X10")
def internet_access_text():
    g = merge_gallup(d, ["WP16056"])
    return pct(g, "WP16056", YES, by="income")


@report.finding("C1_4")
def internet_and_mobile():
    g = merge_gallup(d, ["WP16056", "WP17626"])
    return {**{f"{k}_internet": v for k, v in pct(g, "WP16056", YES, by="income").items()},
            **{f"{k}_mobile": v for k, v in pct(g, "WP17626", YES, by="income").items()}}


@report.finding("C1_5")
def could_protect_by_internet():
    g = merge_gallup(d, ["WP16056"])
    r = pct(g, "WP22252", YES, by=["income", "WP16056"])
    return {f"{inc}_{'internet' if net == 1 else 'no_internet'}": v
            for (inc, net), v in r.items() if net in (1, 2)}


PLAN = pct(d, "WP22253", YES, by="COUNTRY_ISO3")
PLAN_MAJORITY = PLAN[PLAN > 50].index


@report.finding("X11")
def plan_majority_countries():
    return len(PLAN_MAJORITY)


@report.finding("X12")
def plan_majority_southeastern_asia():
    return d[d.COUNTRY_ISO3.isin(PLAN_MAJORITY) & d.region.eq("southeastern_asia")].COUNTRY_ISO3.nunique()


@report.finding("X13")
def plan_70_percent():
    return int((PLAN >= 70).sum())


@report.finding("C1_6")
def plan_by_country():
    return PLAN[PLAN > 50]


# --- Chapter 2: community- and society-level indicators ------------------------

CARES = {"a_lot": [1], "somewhat": [2], "not_at_all": [3]}


@report.finding("X14")
def neighbours_care():
    return {k: pct(d, "WP22232", codes) for k, codes in CARES.items()}


@report.finding("X15")
def neighbours_care_by_income_text():
    return pick(pct(d, "WP22232", YES, by="income"), "low_income", "high_income")


@report.finding("C2_1")
def neighbours_care_a_lot():
    return {**pct(d, "WP22232", YES, by="income"), **pct(d, "WP22232", YES, by="urban")}


@report.finding("X16")
def disaster_by_income():
    return pick(pct(d, "WP22245", YES, by="income"), "low_income", "upper_middle", "high_income")


# Helped a stranger (WP110) is a Gallup World Poll item (not asked in China).
def helped_stranger():
    return merge_gallup(d, ["WP110"])


@report.finding("X17")
def helped_stranger_text():
    return pick(pct(helped_stranger(), "WP110", YES, by="region"),
                "latin_america", "northern_america", "northern_western_europe", "eastern_asia")


@report.finding("C2_2")
def helped_stranger_by_region():
    return pct(helped_stranger(), "WP110", YES, by="region")


@report.finding("C2_3_median_helped")
def median_helped_stranger():
    return pct(helped_stranger(), "WP110", YES, by="COUNTRY_ISO3").median()


@report.finding("C2_3_median_neighbours")
def median_neighbours_care():
    return pct(d, "WP22232", YES, by="COUNTRY_ISO3").median()


@report.finding("X18")
def japan_helped_stranger():
    return pct(helped_stranger(), "WP110", YES, by="COUNTRY_ISO3")["JPN"]


@report.finding("X19")
def japan_neighbours_care():
    return pct(d, "WP22232", YES, by="COUNTRY_ISO3")["JPN"]


# Satisfaction with healthcare (WP97), schools (WP93) and roads (WP92) are
# Gallup World Poll items; 2 = dissatisfied.
INFRASTRUCTURE = {
    "healthcare": ("WP97", ["VEN", "LBN", "GAB", "AFG", "ZMB", "TGO", "MAR", "MNG", "RUS", "MLI"]),
    "education": ("WP93", ["VEN", "MLI", "LBN", "AFG", "GAB", "ZWE", "UGA", "IRQ", "MNG", "GIN"]),
    "roads": ("WP92", ["VEN", "MNG", "SLE", "GAB", "TGO", "GIN", "ZMB", "LBN", "MLI", "ZWE"]),
}


@report.finding("T2_1")
def dissatisfied_with_infrastructure():
    g = merge_gallup(d, [item for item, _ in INFRASTRUCTURE.values()])
    return {f"{key}_{iso}": v for key, (item, isos) in INFRASTRUCTURE.items()
            for iso, v in country_values(g, item, [2], isos).items()}


@report.finding("X20")
def any_discrimination():
    return pct(d, "any_discrimination", YES)


FOUR_TYPES = {"skin": "WP22259", "religion": "WP22260", "nationality": "WP22261", "sex": "WP22262"}


@report.finding("X21")
def discrimination_range():
    values = [pct(d, var, YES) for var in FOUR_TYPES.values()]
    return {"low": min(values), "high": max(values)}


@report.finding("X22")
def discrimination_disability():
    return pct(d, "WP22263", YES)


@report.finding("X23")
def discrimination_text():
    return {k: pct(d, FOUR_TYPES[k], YES) for k in ("nationality", "religion", "sex")}


TYPES = {**FOUR_TYPES, "disability": "WP22263"}


@report.finding("C2_4")
def discrimination_by_type():
    return {k: pct(d, var, YES) for k, var in TYPES.items()}


TOP5 = {
    "nationality": ["AFG", "ZMB", "CMR", "BOL", "KEN"], "religion": ["ZMB", "BRA", "UGA", "CMR", "BOL"],
    "sex": ["ZMB", "BOL", "AFG", "USA", "AUS"], "skin": ["ZMB", "USA", "BOL", "BRA", "MOZ"],
    "disability": ["BGD", "MOZ", "CMR", "COG", "GIN"],
}


@report.finding("T2_2")
def discrimination_top_countries():
    return {f"{k}_{iso}": v for k, isos in TOP5.items() for iso, v in country_values(d, TYPES[k], YES, isos).items()}


@report.finding("X24")
def discrimination_united_states():
    return {k: pct(d, TYPES[k], YES, by="COUNTRY_ISO3")["USA"] for k in ("skin", "nationality", "sex")}


ANY_BY_COUNTRY = pct(d, "any_discrimination", YES, by="COUNTRY_ISO3")


@report.finding("X25")
def high_income_in_top_ten():
    top10 = ANY_BY_COUNTRY.sort_values(ascending=False).index[:10]
    return d[d.COUNTRY_ISO3.isin(top10) & d.CountryIncomeLevel.eq(4)].COUNTRY_ISO3.nunique()


@report.finding("X26")
def any_discrimination_text():
    return {iso: ANY_BY_COUNTRY[iso] for iso in ["ZMB", "BOL", "CMR", "UGA", "BRA", "USA"]}


@report.finding("C2_5")
def any_discrimination_map():
    isos = ["USA", "AFG", "BRA", "CMR", "UGA", "ZMB", "BOL", "COG", "MOZ", "ZWE"]
    return {**{iso: ANY_BY_COUNTRY[iso] for iso in isos}, "max": ANY_BY_COUNTRY.max()}


@report.finding("X27")
def government_cares():
    return {k: pct(d, "gov_cares", codes) for k, codes in CARES.items()}


@report.finding("X28")
def government_not_at_all_text():
    return pick(pct(d, "gov_cares", [3], by="region"), "central_western_africa", "latin_america")


@report.finding("C2_6")
def government_cares_by_region():
    return by_category(d, "gov_cares", {**CARES, "dk": DK}, by="region")


GOV_NOT_AT_ALL = pct(d, "gov_cares", [3], by="COUNTRY_ISO3")
COUNTRY_REGION = d.drop_duplicates("COUNTRY_ISO3").set_index("COUNTRY_ISO3").region


@report.finding("T2_3")
def government_not_at_all_top_countries():
    return pick(GOV_NOT_AT_ALL, "ROU", "IRQ", "HND", "PRY", "BIH", "LBN", "VEN", "SEN", "ALB", "PAN", "NGA", "COL")


@report.finding("X29")
def top_twelve_in_latin_america():
    top12 = GOV_NOT_AT_ALL.sort_values(ascending=False).index[:12]
    return int((COUNTRY_REGION[top12] == "latin_america").sum())


@report.finding("X30")
def majority_not_at_all_by_region():
    over = COUNTRY_REGION[GOV_NOT_AT_ALL[GOV_NOT_AT_ALL > 50].index]
    return {r: int((over == r).sum()) for r in ("eastern_europe", "southern_europe", "northern_western_europe")}


@report.finding("X31")
def countries_in_region():
    return {r: int((COUNTRY_REGION == r).sum()) for r in ("eastern_europe", "southern_europe")}


# National Institutions Index: Gallup World Poll index (0-100) built from
# confidence in the military, the judiciary, the national government and
# the honesty of elections. INDEX_NI is a placeholder name; see README.
@report.finding("C2_7")
def national_institutions_index():
    return wmean(merge_gallup(d, ["INDEX_NI"]), "INDEX_NI", by="region")


@report.finding("C2_8")
def government_cares_vs_institutions():
    # Scatter with no printed values: country-level correlation between the
    # % saying the government cares 'a lot' or 'somewhat' and the mean index.
    g = merge_gallup(d, ["INDEX_NI"])
    x = pct(g, "gov_cares", [1, 2], by="COUNTRY_ISO3")
    y = wmean(g, "INDEX_NI", by="COUNTRY_ISO3")
    both = pd.concat([x, y], axis=1).dropna()
    return {"corr": both.corr().iloc[0, 1]}


# --- Chapter 3: Towards a global Resilience Index -------------------------------


@report.finding("C3_1")
def resilience_by_region():
    return wmean(d, "resilience_index", by="region")


@report.finding("X32")
def resilience_bottom_top_quintile():
    r = wmean(d, "resilience_index", by="INCOME_5")
    return {"bottom": r[1], "top": r[5]}


@report.finding("C3_2")
def resilience_by_group():
    sex = wmean(d, "resilience_index", by="Gender")
    quintile = wmean(d, "resilience_index", by="INCOME_5")
    return {"men": sex[1], "women": sex[2], **wmean(d, "resilience_index", by="urban"),
            **{f"q{q}": quintile[q] for q in range(1, 6)}}


@report.finding("X33")
def resilience_afghanistan_by_sex():
    r = wmean(d[d.COUNTRY_ISO3 == "AFG"], "resilience_index", by="Gender")
    return {"women": r[2], "men": r[1]}


@report.finding("X34")
def men_higher_than_women():
    return names_by_gap(resilience_gap(d, "Gender", 1, 2), 0.07, exclude=["Afghanistan"])


@report.finding("X35")
def resilience_urban_rural():
    r = wmean(d[d.COUNTRY_ISO3.isin(["ZAF", "NGA"])], "resilience_index", by=["COUNTRY_ISO3", "urban"])
    return {f"{iso}_{u}": r[(iso, u)] for iso in ("ZAF", "NGA") for u in ("large_city", "rural")}


@report.finding("X36")
def urban_rural_gaps():
    return names_by_gap(resilience_gap(d, "urban", "large_city", "rural"), 0.08 - 1e-9,
                        exclude=["South Africa", "Nigeria"])


@report.finding("X37")
def primary_education_urban_rural():
    r = pct(d[d.COUNTRY_ISO3.isin(["ZAF", "NGA"])], "Education", [1], by=["COUNTRY_ISO3", "urban"])
    return {f"{iso}_{u}": r[(iso, u)] for iso in ("NGA", "ZAF") for u in ("rural", "large_city")}


INCOME_GAP_COUNTRIES = ["AFG", "EGY", "USA", "BOL", "MEX", "ZMB", "LBN", "EST", "IND", "ECU"]


@report.finding("T3_3")
def resilience_income_gaps():
    m = wmean(d, "resilience_index", by=["COUNTRY_ISO3", "INCOME_5"])
    out = {}
    for iso in INCOME_GAP_COUNTRIES:
        out[f"{iso}_bottom"], out[f"{iso}_top"] = m[(iso, 1)], m[(iso, 5)]
        out[f"{iso}_difference"] = m[(iso, 5)] - m[(iso, 1)]
    return out


@report.finding("X38")
def less_safe():
    return pct(d, "WP20711", [2])


@report.finding("X39")
def resilience_by_safety():
    r = wmean(d, "resilience_index", by="WP20711")
    return {"less_safe": r[2], "about_as_safe": r[3], "more_safe": r[1]}


@report.finding("X40")
def less_safe_by_government_cares():
    r = pct(d, "WP20711", [2], by="gov_cares")
    return {"not_at_all": r[3], "a_lot": r[1]}


@report.finding("X41")
def less_safe_by_discrimination():
    r = pct(d, "WP20711", [2], by="WP22261")
    return {"yes": r[1], "no": r[2]}


def low_resilience_group(rows):
    # Population = sum of PROJWT among group members with an index score.
    g = d[rows & d.resilience_index.notna()]
    return {"population": g.PROJWT.sum(), "score": wmean(g, "resilience_index")}


@report.finding("X42")
def afghan_women_lower_quintiles():
    # "Lower income quintiles" = the bottom three quintiles, which reproduces
    # the published population size.
    return low_resilience_group(d.COUNTRY_ISO3.eq("AFG") & d.Gender.eq(2) & d.INCOME_5.isin([1, 2, 3]))


@report.finding("X43")
def afghanistan_primary_education():
    r = pct(d[d.COUNTRY_ISO3 == "AFG"], "Education", [1], by="Gender")
    return {"women": r[2], "men": r[1]}


@report.finding("X44")
def rural_women_central_western_africa():
    # Rural = "a rural area or on a farm" (Urbanicity 1); bottom three quintiles.
    return low_resilience_group(d.region.eq("central_western_africa") & d.Urbanicity.eq(1)
                                & d.Gender.eq(2) & d.INCOME_5.isin([1, 2, 3]))


@report.finding("X45")
def rural_primary_education_central_western_africa():
    r = pct(d[d.region.eq("central_western_africa") & d.Urbanicity.eq(1)], "Education", [1], by="Gender")
    return {"women": r[2], "men": r[1]}


# --- Chapter 4: Resilience and natural hazards ---------------------------------

DISASTER_TYPES = {"flood": [1], "hurricane": [2], "earthquake": [7], "drought": [50], "wildfire": [8],
                  "thunder": [4], "tornado": [3], "blizzard": [10], "mudslide": [6], "volcano": [9], "tsunami": [5]}


@report.finding("X46")
def experienced_disaster():
    return pct(d, "WP22245", YES)


@report.finding("X47")
def disaster_types_text():
    return {k: pct(d, "disaster_type", DISASTER_TYPES[k]) for k in ("flood", "hurricane", "earthquake")}


@report.finding("X48")
def disaster_types_minor():
    return {k: pct(d, "disaster_type", DISASTER_TYPES[k]) for k in ("drought", "wildfire", "thunder")}


@report.finding("C4_1")
def disaster_types():
    return {k: pct(d, "disaster_type", codes) for k, codes in DISASTER_TYPES.items()}


@report.finding("X49")
def experienced_disaster_regions():
    return pick(pct(d, "WP22245", YES, by="region"), "middle_east", "southeastern_asia")


@report.finding("X50")
def earthquakes_middle_east():
    return {**pick(pct(d, "disaster_type", [7], by="region"), "middle_east"),
            **pick(pct(d, "disaster_type", [7], by="COUNTRY_ISO3"), "IRN", "TUR")}


@report.finding("X51")
def disasters_southeastern_asia():
    sea = d[d.region.eq("southeastern_asia")]
    return {k: pct(sea, "disaster_type", DISASTER_TYPES[k]) for k in ("flood", "hurricane", "earthquake")}


@report.finding("C4_2")
def disaster_types_by_region():
    return by_category(d, "disaster_type", {
        "flood": [1], "hurricane": [2], "earthquake": [7], "drought": [50], "wildfire": [8],
        "other": [3, 4, 5, 6, 9, 10, 11], "none": [0],
    }, by="region")


@report.finding("X52")
def floods():
    return {**pick(pct(d, "disaster_type", [1], by="region"), "central_western_africa"),
            **pick(pct(d, "disaster_type", [1], by="COUNTRY_ISO3"), "BFA", "BEN", "SLE", "TGO")}


def services_by_disaster(df):
    """% who went without each service, by experience of disaster (WP22245 1 = yes, 2 = no)."""
    out = {}
    for service, var in SERVICES.items():
        r = pct(df, var, YES, by="WP22245")
        out[f"{service}_disaster"], out[f"{service}_no_disaster"] = r[1], r[2]
    return out


@report.finding("X53")
def smallest_service_gap():
    r = services_by_disaster(d)
    return min(r[f"{s}_disaster"] - r[f"{s}_no_disaster"] for s in SERVICES)


@report.finding("C4_3")
def services_global():
    return services_by_disaster(d)


@report.finding("C4_4")
def services_by_income():
    return {f"{grp}_{k}": v for grp in ("low_lower_middle", "upper_middle_high")
            for k, v in services_by_disaster(d[d.income2 == grp]).items()}


@report.finding("X54")
def well_prepared():
    return pct(d, "WP22243", YES)


@report.finding("X55")
def well_prepared_regions_text():
    return pick(pct(d, "WP22243", YES, by="region"), "southern_asia", "northern_america", "australia_nz",
                "southeastern_asia", "central_western_africa", "latin_america", "northern_africa", "southern_africa")


@report.finding("X56")
def resilience_southern_asia():
    return wmean(d, "resilience_index", by="region")["southern_asia"]


@report.finding("C4_5")
def well_prepared_by_region():
    return pct(d, "WP22243", YES, by="region")


@report.finding("C4_6")
def institutions_prepared_by_region():
    # National government: WP22241 only; Myanmar's alternative wording
    # (WP22526, "the government in power") is not merged.
    out = {}
    for who, var in {"hospitals": "WP22242", "local": "WP22244", "national": "WP22241"}.items():
        for region, value in pct(d, var, YES, by="region").items():
            out[f"{region}_{who}"] = value
    return out


TRUST_MOST = {"local_news": [3], "weather_service": [1], "internet": [7], "emergency": [6],
              "disaster_agency": [2], "religious": [4], "famous": [5]}


@report.finding("X57")
def trust_most_text():
    return {k: pct(d, "WP22240", TRUST_MOST[k]) for k in ("local_news", "weather_service", "internet")}


@report.finding("X58")
def religious_leaders_low_income():
    return pct(d, "WP22240", [4], by="income")["low_income"]


@report.finding("T4_1")
def trust_most_by_income():
    out = {}
    for source, codes in TRUST_MOST.items():
        out[f"{source}_all"] = pct(d, "WP22240", codes)
        for inc, value in pct(d, "WP22240", codes, by="income").items():
            out[f"{source}_{inc}"] = value
    return out


DISASTER_BY_COUNTRY = pct(d, "WP22245", YES, by="Country")


@report.finding("X59")
def most_disasters():
    return "; ".join(DISASTER_BY_COUNTRY.sort_values(ascending=False).index[:2])


@report.finding("C4_7")
def resilience_vs_disasters():
    # Scatter with no printed values: country-level correlation between the
    # mean Resilience Index and the % who experienced a disaster.
    both = pd.concat([wmean(d, "resilience_index", by="Country"), DISASTER_BY_COUNTRY], axis=1).dropna()
    return {"corr": both.corr().iloc[0, 1]}


@report.finding("X60")
def climate_threat_by_disaster():
    r = pct(d, "WP20719", [1, 2], by="WP22245")
    return {"disaster": r[1], "no_disaster": r[2]}


@report.finding("X61")
def climate_very_serious_by_disaster():
    r = pct(d, "WP20719", [1], by="WP22245")
    return {"disaster": r[1], "no_disaster": r[2]}


def very_serious_by_type(codes):
    """% climate change a very serious threat: experienced this type vs everyone else."""
    r = pct(d.assign(this_type=np.where(d.disaster_type.isin(codes), 1, 2)), "WP20719", [1], by="this_type")
    return r[1], r[2]


@report.finding("X62")
def climate_very_serious_hurricane():
    yes, no = very_serious_by_type([2])
    return {"hurricane": yes, "no_hurricane": no}


@report.finding("T4_2")
def climate_very_serious_by_type():
    r = pct(d, "WP20719", [1], by="WP22245")
    out = {"any_experienced": r[1], "any_not": r[2], "any_difference": r[1] - r[2]}
    for k in ("drought", "wildfire", "flood", "hurricane", "earthquake"):
        yes, no = very_serious_by_type(DISASTER_TYPES[k])
        out.update({f"{k}_experienced": yes, f"{k}_not": no, f"{k}_difference": yes - no})
    return out


# --- Appendix 3: Resilience Index methodology ------------------------------------


@report.finding("X63")
def countries_without_index():
    has = d.groupby("COUNTRY_ISO3").resilience_index.count()
    return int((has == 0).sum())


@report.finding("X64")
def countries_missing_society_items():
    # A country with an index score counts when every respondent is missing
    # the National Institutions Index, government cares or all discrimination items.
    g = merge_gallup(d, ["INDEX_NI"])
    g["any_disc_item"] = g[DISCRIMINATION].notna().any(axis=1)
    c = g.groupby("COUNTRY_ISO3").agg(index=("resilience_index", "count"), ni=("INDEX_NI", "count"),
                                      gov=("gov_cares", "count"), disc=("any_disc_item", "sum"))
    c = c[c["index"] > 0]
    return int(((c.ni == 0) | (c.gov == 0) | (c.disc == 0)).sum())


@report.finding("A3_1")
def resilience_distribution():
    # Histogram on page 61 has no printed values: weighted mean and SD.
    g = d[d.resilience_index.notna()]
    mean = wmean(g, "resilience_index")
    sd = np.sqrt((g.PROJWT * (g.resilience_index - mean) ** 2).sum() / g.PROJWT.sum())
    return {"mean": mean, "sd": sd}


if __name__ == "__main__":
    sys.exit(report.run())
