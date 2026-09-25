"""Reproduce World Risk Poll 2021: A Changed World? Perceptions and experiences of risk in the Covid age.

Run from the repository root:
    python reports/WRP_2021/core_a_changed_world/reproduce.py

The report compares 2021 with 2019 on several questions. Each function below
computes one chart, table or text statement listed in published_figures.csv;
see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, countries_in_all, distribution, load_wave, merge_gallup, pct  # noqa: E402

report = Report(__file__)

REGIONS = {  # GlobalRegion code -> key
    1: "eastern_africa", 2: "central_western_africa", 3: "northern_africa", 4: "southern_africa",
    5: "latin_america", 6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia",
    10: "southern_asia", 11: "middle_east", 12: "eastern_europe", 13: "northern_western_europe",
    14: "southern_europe", 15: "australia_nz",
}
QUINTILES = {1: "bottom", 2: "second", 3: "middle", 4: "fourth", 5: "top"}  # INCOME_5
FEELINGS = {1: "comfortable", 2: "getting_by", 3: "difficult", 4: "very_difficult"}  # IncomeFeelings
EDUCATION = {1: "primary", 2: "secondary", 3: "post_secondary"}
PERSONAL = [1, 3]  # experience items: 1 = yes, personally; 2 = know someone; 3 = both; 4 = no
DK = [98, 99]

WORRY_21 = {"food": "WP20720", "water": "WP20721", "crime": "WP20722", "weather": "WP20723",
            "traffic": "WP22213", "mental": "WP20726", "work": "WP22214"}
HARM_21 = {"food": "WP22442", "water": "WP22443", "crime": "WP22444", "weather": "WP22445",
           "traffic": "WP22446", "mental": "WP22447", "work": "WP22448"}
WORRY_19 = {"food": "L6A", "water": "L6B", "crime": "L6C", "weather": "L6D", "mental": "L6G"}
HARM_19 = {"food": "L8A", "water": "L8B", "crime": "L8C", "weather": "L8D", "mental": "L8G"}

d = load_wave(2021, [
    "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "AgeGroups4", "Gender",
    "Education", "INCOME_5", "IncomeFeelings", "WP20711", "WP22331", "WP20719",
    *WORRY_21.values(), *HARM_21.values(),
])
d19 = load_wave(2019, [
    "WPID_RANDOM", "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "L2", "L3_A", "L5", "L14",
    *WORRY_19.values(), *HARM_19.values(),
])

# --- Derived variables ---------------------------------------------------------

# Trend frames. Comparisons use only the 119 countries surveyed in both years
# (report p. 10), with the questions under common names:
#   safe     feel more (1), less (2) or about as safe (3) as five years ago
#   risk     greatest source of risk, on the 2021 codes (WP22331)
#   climate  climate change a threat: very (1), somewhat (2), not (3)
#   worry_*  very (1), somewhat (2), not worried (3)
#   harm_*   experienced serious harm in the past two years: yes (1), no (2).
#            2019 has only yes/no; in 2021 "yes" is the respondent, someone
#            they know, or both, which is how the report trends it (p. 22).
COMMON = countries_in_all([2019, 2021])
RISK_2019_TO_2021 = {  # L3_A code -> WP22331 code. 2019 has no hunger, Covid-19, war or disaster codes.
    1: 1, 2: 2, 3: 3, 4: 16, 5: 9, 6: 10, 7: 11, 8: 12, 9: 5, 10: 6, 11: 13, 12: 14, 13: 18,
    14: 17, 15: 8, 16: 19, 17: 21, 18: 22, 19: 23, 98: 98, 99: 99,
}
ANY_HARM = {1: 1, 2: 1, 3: 1, 4: 2, 98: 98, 99: 99}

t19 = d19[d19.COUNTRY_ISO3.isin(COMMON)].copy()
t19["safe"], t19["risk"], t19["climate"] = t19.L2, t19.L3_A.map(RISK_2019_TO_2021), t19.L5
t21 = d[d.COUNTRY_ISO3.isin(COMMON)].copy()
t21["safe"], t21["risk"], t21["climate"] = t21.WP20711, t21.WP22331, t21.WP20719
for item, var in WORRY_19.items():
    t19[f"worry_{item}"], t19[f"harm_{item}"] = t19[var], t19[HARM_19[item]]
for item, var in WORRY_21.items():
    t21[f"worry_{item}"], t21[f"harm_{item}"] = t21[var], t21[HARM_21[item]].map(ANY_HARM)
TREND = {2019: t19, 2021: t21}


def trend(var):
    """The two waves for a trend on `var`, both restricted to the countries asked it in 2021.

    The safety and greatest-risk questions were not asked in China in 2021, so
    China is left out of the 2019 figures for those questions too.
    """
    asked = set(t21.loc[t21[var].notna(), "COUNTRY_ISO3"])
    return {year: df[df.COUNTRY_ISO3.isin(asked)] for year, df in TREND.items()}


# Severe weather harm group (Charts 5.3): experienced (personally or both),
# know someone who has, neither. Don't know / refused are not shown.
d["weather_harm"] = d.WP22445.map({1: 1, 3: 1, 2: 2, 4: 3})

# --- Helpers -------------------------------------------------------------------


def shares(df, var, cats, by=None):
    """% in each named category of `var` (a category may pool several codes).

    Returns a Series (name -> %) or, with `by`, a groups x names table.
    """
    t = distribution(df, var, by=by)
    if by is None:
        return pd.Series({name: t[t.index.intersection(codes)].sum() for name, codes in cats.items()})
    return pd.DataFrame({name: t[t.columns.intersection(codes)].sum(axis=1) for name, codes in cats.items()})


def flat(table, keys):
    """{"<keys[group]>_<column>": value} for a groups x names table, in the order of `keys`."""
    return {f"{keys[g]}_{c}": table.loc[g, c] for g in keys if g in table.index for c in table.columns}


def by_country(df, var, codes, countries):
    r = pct(df[df.COUNTRY_ISO3.isin(countries)], var, codes, by="COUNTRY_ISO3")
    return {iso: r[iso] for iso in countries}


def rdiff(a, b):
    """Difference of rounded percentages, as the report computes its changes and gaps."""
    return float(np.round(a) - np.round(b))


def rratio(a, b):
    """Ratio of rounded percentages, as in Table 2.1 and the text's 'x times as likely'."""
    return float(np.round(a) / np.round(b))


def top_named(df, n=3):
    """{region code: codes of its `n` most-named risks}; 'other', DK and refused excluded."""
    t = distribution(df, "WP22331", by="GlobalRegion").drop(columns=[22, 98, 99], errors="ignore")
    return {g: list(row.sort_values(ascending=False).index[:n]) for g, row in t.iterrows()}


SAFE = {"more": [1], "same": [3], "less": [2], "dk": DK}
RISKS = {  # Chart 1.3 / 1.4 category -> WP22331 code
    "road": 1, "crime": 3, "health": 5, "covid": 7, "none": 23, "financial": 9, "economic": 10, "other": 22,
    "climate": 19, "work": 17, "war": 4, "politics": 11, "non_road": 2, "cooking": 16, "mental": 8,
    "disasters": 20, "drugs": 6, "hunger": 15, "pollution": 18, "water": 13, "internet": 12, "food": 14,
    "drowning": 21,
}
CLIMATE = {"very": [1], "somewhat": [2], "not": [3], "dk": DK}
workers = d[d.WP22214.notna()]  # worry about work was asked only of the employed

# --- Preface, Executive Summary, Introduction -----------------------------------------


@report.finding("X01")
def respondents():
    return len(d)


@report.finding("X02")
def countries_2021():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X03")
def countries_2019():
    return d19.COUNTRY_ISO3.nunique()


@report.finding("X04")
def countries_added():
    return len(set(d.COUNTRY_ISO3) - set(d19.COUNTRY_ISO3))


@report.finding("X05")
def countries_both():
    return len(COMMON)


@report.finding("X06")
def global_safety_text():
    w = trend("safe")
    more19, more21 = pct(w[2019], "safe", [1]), pct(w[2021], "safe", [1])
    return {"less_2019": pct(w[2019], "safe", [2]), "less_2021": pct(w[2021], "safe", [2]),
            "more_2021": more21, "more_change": rdiff(more21, more19)}


@report.finding("X07")
def greatest_risk_2021_text():
    return {k: pct(d, "WP22331", [RISKS[k]]) for k in ("covid", "road", "crime", "health")}


@report.finding("X08")
def covid_rank():
    t = distribution(d, "WP22331").drop([22, 23, 98, 99])
    return int((t > t[7]).sum() + 1)


@report.finding("X09")
def greatest_risk_trend_text():
    w = trend("risk")
    return {"health_2019": pct(w[2019], "risk", [5]), "none_2019": pct(w[2019], "risk", [23]),
            "none_2021": pct(w[2021], "risk", [23])}


@report.finding("X10")
def aged_65_plus():
    old = d[d.AgeGroups4 == 4]
    return {"covid": pct(old, "WP22331", [7]), "health": pct(old, "WP22331", [5])}


@report.finding("X11")
def climate_threat_text():
    return {"threat_2021": pct(t21, "climate", [1, 2]), "threat_2019": pct(t19, "climate", [1, 2]),
            "very_2021": pct(t21, "climate", [1]), "very_2019": pct(t19, "climate", [1])}


@report.finding("X12")
def climate_by_education_text():
    very, dk = pct(d, "WP20719", [1], by="Education"), pct(d, "WP20719", DK, by="Education")
    return {**{f"very_{k}": very[c] for c, k in EDUCATION.items()}, **{f"dk_{k}": dk[c] for c, k in EDUCATION.items()}}


@report.finding("X13")
def food_safety_authority_2019():
    return pct(d19, "L14", [5])  # 5 = the government food safety agency


# --- Chapter 1: Global perceptions of safety and greatest risks in 2021 ---------------


def less_safe_by(by):
    w = trend("safe")
    return pct(w[2019], "safe", [2], by=by), pct(w[2021], "safe", [2], by=by)


@report.finding("X14")
def regions_less_safe_up_10():
    a, b = less_safe_by("GlobalRegion")
    return sum(rdiff(b[g], a[g]) > 10 for g in REGIONS)


@report.finding("X15")
def crime_top_regions_text():
    r = pct(d, "WP22331", [3], by="GlobalRegion")
    return {"latin_america": r[5], "southern_africa": r[4]}


@report.finding("X16")
def less_safe_regions_text():
    a, b = less_safe_by("GlobalRegion")
    out = {}
    for code in (9, 2, 6, 13, 12, 5):
        k = REGIONS[code]
        out.update({f"{k}_2019": a[code], f"{k}_2021": b[code], f"{k}_change": rdiff(b[code], a[code])})
    return out


@report.finding("X17")
def healthcare_satisfaction():
    # Gallup World Poll: satisfied with the availability of quality healthcare
    # in the city or area where you live (1 = satisfied). Placeholder item name.
    g = merge_gallup(d, ["GWP_HEALTHCARE_SATISFACTION"])
    r = pct(g, "GWP_HEALTHCARE_SATISFACTION", [1], by="GlobalRegion")
    return {REGIONS[c]: r[c] for c in (13, 14, 12)}


@report.finding("X18")
def nigeria_less_safe():
    a, b = less_safe_by("COUNTRY_ISO3")
    return {"2019": a["NGA"], "2021": b["NGA"]}


@report.finding("X19")
def us_share_of_northern_america():
    na = d[d.GlobalRegion == 6]
    return 100 * na.loc[na.COUNTRY_ISO3 == "USA", "PROJWT"].sum() / na.PROJWT.sum()


@report.finding("X20")
def us_covid():
    return by_country(d, "WP22331", [7], ["USA"])["USA"]


@report.finding("X21")
def greatest_risk_by_education():
    t = shares(d, "WP22331", {"road": [1], "crime": [3], "financial": [9]}, by="Education")
    return {"post_secondary_road": t.loc[3, "road"], "post_secondary_crime": t.loc[3, "crime"],
            "primary_financial": t.loc[1, "financial"], "primary_road": t.loc[1, "road"],
            "primary_crime": t.loc[1, "crime"], "post_secondary_financial": t.loc[3, "financial"]}


@report.finding("X22")
def less_safe_among_covid():
    return pct(d[d.WP22331 == 7], "WP20711", [2])


@report.finding("X89")
def at_least_half_less_safe():
    r = pct(d, "WP20711", [2], by="WP22331")
    return int((r[[4, 11, 3]].round() >= 50).sum())


@report.finding("X90")
def about_one_in_four_less_safe():
    r = pct(d, "WP20711", [2], by="WP22331")
    return {"road": r[1], "cooking": r[16]}


@report.finding("X23")
def regions_covid_top_three():
    return sum(7 in top for top in top_named(d).values())


@report.finding("X24")
def regions_top_three():
    tops = top_named(d).values()
    return {k: sum(RISKS[k] in top for top in tops) for k in ("road", "health", "crime")}


@report.finding("X25")
def regions_covid_first():
    return sum(top[0] == 7 for top in top_named(d, 1).values())


@report.finding("X26")
def covid_algeria_egypt():
    return by_country(d, "WP22331", [7], ["DZA", "EGY"])


@report.finding("X27")
def crime_twice_any_other_region():
    r = pct(d, "WP22331", [3], by="GlobalRegion").round()
    return float(min(r[5], r[4]) / r.drop([5, 4]).max())


@report.finding("X28")
def crime_latin_american_countries():
    return by_country(d, "WP22331", [3], ["VEN", "ECU", "ARG", "COL", "MEX"])


@report.finding("X29")
def would_move():
    # Gallup World Poll WP1325: would like to move permanently to another
    # country (1) or continue living in this country (2).
    g = merge_gallup(d, ["WP1325"])
    return {"latin_america": pct(g[g.GlobalRegion == 5], "WP1325", [1]), "global": pct(g, "WP1325", [1])}


@report.finding("X30")
def latin_america_crime_groups():
    la = d[d.GlobalRegion == 5]
    age, sex = pct(la, "WP22331", [3], by="AgeGroups4"), pct(la, "WP22331", [3], by="Gender")
    inc, edu = pct(la, "WP22331", [3], by="INCOME_5"), pct(la, "WP22331", [3], by="Education")
    return {"age_15_29": age[1], "age_65plus": age[4], "men": sex[1], "women": sex[2],
            "income_bottom": inc[1], "income_top": inc[5], "post_secondary": edu[3], "primary": edu[1]}


@report.finding("X31")
def road_by_country():
    return by_country(d, "WP22331", [1], ["FIN", "ISL", "NZL", "NOR", "NLD", "AUS"])


@report.finding("X32")
def roads_satisfaction():
    # Gallup World Poll: satisfied with the roads and highways (1 = satisfied). Placeholder item name.
    g = merge_gallup(d, ["GWP_ROADS_SATISFACTION"])
    r = pct(g, "GWP_ROADS_SATISFACTION", [1], by="GlobalRegion")
    return {REGIONS[c]: r[c] for c in (2, 1, 5, 13)}


def road_trend():
    w = trend("risk")
    return pct(w[2019], "risk", [1], by="COUNTRY_ISO3"), pct(w[2021], "risk", [1], by="COUNTRY_ISO3")


@report.finding("X33")
def eastern_asia_road_up_10():
    a, b = road_trend()
    east = t21.loc[t21.GlobalRegion == 8, "COUNTRY_ISO3"].unique()
    return sum(rdiff(b[c], a[c]) > 10 for c in east if c in a.index and c in b.index)


@report.finding("X34")
def road_korea_hong_kong():
    a, b = road_trend()
    return {"KOR_2019": a["KOR"], "KOR_2021": b["KOR"], "HKG_2019": a["HKG"], "HKG_2021": b["HKG"]}


@report.finding("C1_1")
def safety_global():
    w = trend("safe")
    return {f"{y}_{k}": v for y in (2019, 2021) for k, v in shares(w[y], "safe", SAFE).items()}


@report.finding("C1_2")
def safety_by_region():
    w = trend("safe")
    t = {y: shares(w[y], "safe", {k: SAFE[k] for k in ("more", "same", "less")}, by="GlobalRegion")
         for y in (2019, 2021)}
    out = {}
    for code, k in REGIONS.items():
        for y in (2019, 2021):
            out.update({f"{k}_{y}_{c}": t[y].loc[code, c] for c in ("more", "same", "less")})
        out[f"{k}_diff"] = rdiff(t[2021].loc[code, "less"], t[2019].loc[code, "less"])
    return out


@report.finding("T1_1")
def safety_largest_increases():
    w = trend("safe")
    cats = {k: SAFE[k] for k in ("less", "same", "more")}
    t = {y: shares(w[y], "safe", cats, by="COUNTRY_ISO3") for y in (2019, 2021)}
    out = {}
    for iso in ("MMR", "ARM", "VNM", "NGA", "TUR"):
        for y in (2019, 2021):
            out.update({f"{iso}_{y}_{c}": t[y].loc[iso, c] for c in cats})
        out[f"{iso}_diff"] = rdiff(t[2021].loc[iso, "less"], t[2019].loc[iso, "less"])
    return out


@report.finding("C1_3")
def greatest_risk_global():
    w = trend("risk")
    out = {}
    for k, code in RISKS.items():
        if code in (7, 4, 20):  # Covid-19, war and non-weather disasters: not coded in 2019
            out[f"{k}_2021"] = pct(w[2021], "risk", [code])
            continue
        # 2019 has no hunger code, so hunger comes out as 0% (see README).
        out[f"{k}_2019"] = pct(w[2019], "risk", [code])
        out[f"{k}_2021"] = pct(w[2021], "risk", [code])
    return out


@report.finding("C1_4")
def less_safe_by_greatest_risk():
    r = pct(d, "WP20711", [2], by="WP22331")
    return {k: r[code] for k, code in RISKS.items() if k not in ("none", "other")}


T12_CATS = {"covid": [7], "health": [5], "road": [1], "crime": [3], "financial": [9], "economic": [10],
            "cooking": [16], "none": [23]}


# Table 1.2 and Chart 1.5 use the 119 countries surveyed in both years (t21):
# with all 121, Eastern Europe's road figure is 13% (published 12%), because
# of the Czech Republic, surveyed only in 2021. Every other value is the
# same either way (see README).


@report.finding("T1_2")
def top_risks_by_region():
    return flat(shares(t21, "WP22331", T12_CATS, by="GlobalRegion"), REGIONS)


@report.finding("C1_5")
def crime_by_region():
    r = pct(t21, "WP22331", [3], by="GlobalRegion")
    return {k: r[c] for c, k in REGIONS.items()}


# --- Chapter 2: Risk perceptions and experiences of harm ---------------------------
# Worry about work was asked only of the employed. Personal experience of harm
# from work is taken over everyone asked the experience item: that is what
# reproduces Charts 2.1 and 2.3 and Table 2.2 (see README).


@report.finding("X35")
def work_text():
    w, e = pct(t21, "worry_work", [1]), pct(t21, "harm_work", [1])
    return {"experienced": e, "very_worried": w, "ratio": rratio(w, e)}


@report.finding("X36")
def italy_work():
    it = d[d.COUNTRY_ISO3 == "ITA"]
    return {"experienced": pct(it, "WP22448", PERSONAL), "very_worried": pct(it, "WP22214", [1])}


@report.finding("X37")
def food_or_water_over_20():
    listed = ["SLE", "GHA", "ZMB", "IND", "PHL", "AFG"]
    food, water = by_country(d, "WP22442", PERSONAL, listed), by_country(d, "WP22443", PERSONAL, listed)
    return sum(max(food[c], water[c]) > 20 for c in listed)


@report.finding("X38")
def violent_crime_text():
    w, e = pct(t21, "worry_crime", [1]), pct(t21, "harm_crime", [1])
    return {"very_worried": w, "experienced": e, "ratio": rratio(w, e)}


@report.finding("X39")
def severe_weather_text():
    return {"experienced_2019": pct(t19, "harm_weather", [1]), "experienced_2021": pct(t21, "harm_weather", [1]),
            "very_worried_2019": pct(t19, "worry_weather", [1]), "very_worried_2021": pct(t21, "worry_weather", [1])}


@report.finding("X40")
def work_worry_regions_text():
    r = pct(workers, "WP22214", [1], by="GlobalRegion")
    return {REGIONS[c]: r[c] for c in (2, 4, 10, 1, 6, 13, 15)}


@report.finding("X41")
def regions_work_worry_30():
    r = pct(workers, "WP22214", [1], by="GlobalRegion")
    return int((r.round() >= 30).sum())


@report.finding("X42")
def work_harm_regions_text():
    r = pct(d, "WP22448", PERSONAL, by="GlobalRegion")
    return {REGIONS[c]: r[c] for c in (10, 14, 9)}


@report.finding("X43")
def belgium_guinea():
    e = by_country(d, "WP22448", PERSONAL, ["BEL", "GIN"])
    w = by_country(workers, "WP22214", [1], ["BEL", "GIN"])
    return {"BEL_experienced": e["BEL"], "BEL_very_worried": w["BEL"],
            "GIN_experienced": e["GIN"], "GIN_very_worried": w["GIN"]}


@report.finding("X44")
def belgium_ratio():
    e, w = by_country(d, "WP22448", PERSONAL, ["BEL"]), by_country(workers, "WP22214", [1], ["BEL"])
    return rratio(w["BEL"], e["BEL"])


@report.finding("X45")
def work_harm_18_or_more():
    e = by_country(d, "WP22448", PERSONAL, ["ITA", "CHE", "AFG", "VNM"])
    return sum(v >= 18 for v in e.values())


@report.finding("X46")
def afghanistan_crime_worry():
    return by_country(d, "WP20722", [1], ["AFG"])["AFG"]


@report.finding("X47")
def countries_work_harm_over_30():
    return int((pct(d, "WP22448", PERSONAL, by="COUNTRY_ISO3") > 30).sum())


@report.finding("X48")
def work_by_finances_text():
    e = pct(d, "WP22448", PERSONAL, by="IncomeFeelings")
    w = pct(workers, "WP22214", [1], by="IncomeFeelings")
    return {"experienced_very_difficult": e[4], "experienced_comfortable": e[1], "experienced_getting_by": e[2],
            "very_worried_very_difficult": w[4], "very_worried_comfortable": w[1]}


@report.finding("X49")
def four_times_as_likely():
    w = pct(workers, "WP22214", [1], by="IncomeFeelings")
    return rratio(w[4], w[1])


struggling = d[d.IncomeFeelings.isin([3, 4])]  # finding it difficult or very difficult


@report.finding("X50")
def southern_asia_struggling():
    return pct(struggling[struggling.GlobalRegion == 10], "WP22448", PERSONAL)


@report.finding("X51")
def india_struggling():
    return pct(struggling[struggling.COUNTRY_ISO3 == "IND"], "WP22448", PERSONAL)


@report.finding("X52")
def india_injured_people():
    # PROJWT sums to the adult population, so this is the number of people.
    ind = struggling[struggling.COUNTRY_ISO3 == "IND"]
    return ind.loc[ind.WP22448.isin(PERSONAL), "PROJWT"].sum()


@report.finding("X53")
def very_difficult_northern_america():
    vd = d[d.IncomeFeelings == 4]
    return {"northern_america": pct(vd[vd.GlobalRegion == 6], "WP22448", PERSONAL),
            **by_country(vd, "WP22448", PERSONAL, ["USA", "CAN"])}


@report.finding("T2_1")
def worry_experience_trend():
    out = {}
    for item in ("work", "mental", "food", "traffic", "water", "weather", "crime"):
        for y, df in TREND.items():
            if f"worry_{item}" not in df:
                continue
            w, e = pct(df, f"worry_{item}", [1]), pct(df, f"harm_{item}", [1])
            out.update({f"{item}_{y}_very_worried": w, f"{item}_{y}_experienced": e, f"{item}_{y}_ratio": rratio(w, e)})
    return out


@report.finding("C2_1")
def work_by_region():
    w = pct(workers, "WP22214", [1], by="GlobalRegion")
    e = pct(d, "WP22448", PERSONAL, by="GlobalRegion")
    out = {}
    for c, k in REGIONS.items():
        out.update({f"{k}_very_worried": w[c], f"{k}_experienced": e[c]})
    return out


@report.finding("C2_2")
def work_by_country():
    # Scatter plot with no printed values: computed for reference only.
    w = pct(workers, "WP22214", [1], by="COUNTRY_ISO3")
    e = pct(d, "WP22448", PERSONAL, by="COUNTRY_ISO3")
    return {f"{c}_{k}": v[c] for c in sorted(w.index) for k, v in (("very_worried", w), ("experienced", e))}


@report.finding("C2_3")
def work_by_finances():
    e = pct(d, "WP22448", PERSONAL, by="IncomeFeelings")
    w = pct(workers, "WP22214", [1], by="IncomeFeelings")
    return {**{f"experienced_{k}": e[c] for c, k in FEELINGS.items()},
            **{f"very_worried_{k}": w[c] for c, k in FEELINGS.items()}}


@report.finding("T2_2")
def work_harm_by_region_and_finances():
    r = pct(d[d.IncomeFeelings.isin(list(FEELINGS))], "WP22448", PERSONAL, by=["GlobalRegion", "IncomeFeelings"])
    return {f"{k}_{f}": r[(c, fc)] for c, k in REGIONS.items() for fc, f in FEELINGS.items()}


@report.finding("X54")
def food_harm_by_country():
    return by_country(d, "WP22442", PERSONAL, ["SLE", "GHA", "ZMB", "IND", "MOZ", "PHL", "AFG", "DZA"])


@report.finding("X55")
def countries_food_harm_20():
    return int((pct(d, "WP22442", PERSONAL, by="COUNTRY_ISO3") >= 20).sum())


@report.finding("X56")
def food_worry_by_country():
    return by_country(d, "WP20720", [1], ["MOZ", "SLE", "GHA", "PHL", "ZMB", "DZA"])


@report.finding("X57")
def water_harm_over_25():
    return sum(v > 25 for v in by_country(d, "WP22443", PERSONAL, ["CMR", "COG"]).values())


@report.finding("X58")
def water_by_country():
    listed = ["SLE", "COG", "GHA", "PHL"]
    w, e = by_country(d, "WP20721", [1], listed), by_country(d, "WP22443", PERSONAL, listed)
    return {f"{c}_{k}": v[c] for c in listed for k, v in (("very_worried", w), ("experienced", e))}


@report.finding("X91")
def water_worry_twice_experience():
    listed = ["SLE", "COG", "GHA"]
    w, e = by_country(d, "WP20721", [1], listed), by_country(d, "WP22443", PERSONAL, listed)
    return {c: rratio(w[c], e[c]) for c in listed}


@report.finding("C2_4")
def food_water_by_country():
    # Scatter plots with no printed values: computed for reference only.
    out = {}
    for item, (worry, harm) in {"food": ("WP20720", "WP22442"), "water": ("WP20721", "WP22443")}.items():
        w, e = pct(d, worry, [1], by="COUNTRY_ISO3"), pct(d, harm, PERSONAL, by="COUNTRY_ISO3")
        out.update({f"{item}_{c}_{k}": v[c] for c in sorted(w.index) for k, v in (("very_worried", w), ("experienced", e))})
    return out


# --- Chapter 3: Covid-19 and risk perceptions -----------------------------------------


def covid_by_country(df=d):
    return pct(df, "WP22331", [7], by="COUNTRY_ISO3")


SEA = sorted(d.loc[d.GlobalRegion == 9, "COUNTRY_ISO3"].unique())


@report.finding("X59")
def sea_countries_covid_10():
    return int((covid_by_country()[SEA] > 10).sum())


@report.finding("X60")
def covid_malaysia_philippines():
    r = covid_by_country()
    return {"MYS": r["MYS"], "PHL": r["PHL"]}


@report.finding("X61")
def sea_countries():
    return len(SEA)


@report.finding("C3_1")
def greatest_risk_by_age():
    t = shares(d, "WP22331", {"health": [5], "covid": [7]}, by="AgeGroups4")
    return flat(t, {1: "15_29", 2: "30_49", 3: "50_64", 4: "65plus"})


@report.finding("X62")
def covid_by_quintile_text():
    r = pct(d, "WP22331", [7], by="INCOME_5")
    return {"bottom": r[1], "top": r[5]}


@report.finding("X63")
def northern_africa_covid_quintiles():
    r = pct(d[d.GlobalRegion == 3], "WP22331", [7], by="INCOME_5")
    return {"bottom": r[1], "top_three_min": r[[3, 4, 5]].min(), "top_three_max": r[[3, 4, 5]].max()}


@report.finding("T3_1")
def covid_by_region_and_quintile():
    overall = pct(d, "WP22331", [7], by="GlobalRegion")
    q = pct(d, "WP22331", [7], by=["GlobalRegion", "INCOME_5"])
    out = {}
    for c, k in REGIONS.items():
        out[f"{k}_overall"] = overall[c]
        out.update({f"{k}_{qk}": q[(c, qc)] for qc, qk in QUINTILES.items()})
    return out


@report.finding("C3_2")
def healthcare_and_less_safe_by_country():
    # Scatter plot with no printed values; needs the Gallup healthcare item.
    g = merge_gallup(d, ["GWP_HEALTHCARE_SATISFACTION"])
    h = pct(g, "GWP_HEALTHCARE_SATISFACTION", [1], by="COUNTRY_ISO3")
    s = pct(g, "WP20711", [2], by="COUNTRY_ISO3")
    return {f"{c}_{k}": v[c] for c in sorted(s.index) for k, v in (("satisfied", h), ("less_safe", s))}


@report.finding("X64")
def countries_less_safe_two_thirds():
    return int((pct(d, "WP20711", [2], by="COUNTRY_ISO3") > 200 / 3).sum())


@report.finding("X65")
def covid_regions_text():
    r = pct(d, "WP22331", [7], by="GlobalRegion")
    return {"southeastern_asia": r[9], "northern_africa": r[3]}


@report.finding("M3_1")
def covid_southeastern_asia():
    r = covid_by_country()
    return {c: r[c] for c in ("MMR", "LAO", "VNM", "THA", "PHL", "MYS", "KHM", "SGP", "IDN")}


@report.finding("X66")
def covid_third_outside_sea():
    r = covid_by_country()
    return int((r.drop(SEA) >= 100 / 3).sum())


# --- Chapter 4: Do policymakers focus on people's greatest sources of risk? ---------

FIVE = ("weather", "mental", "crime", "food", "water")


@report.finding("X67")
def mental_harm_trend_text():
    return {"2019": pct(t19, "harm_mental", [1]), "2021": pct(t21, "harm_mental", [1])}


@report.finding("X68")
def harm_increases():
    return {k: rdiff(pct(t21, f"harm_{k}", [1]), pct(t19, f"harm_{k}", [1])) for k in ("weather", "mental")}


@report.finding("C4_1")
def harm_trend():
    return {f"{k}_{y}": pct(TREND[y], f"harm_{k}", [1]) for k in FIVE for y in (2019, 2021)}


@report.finding("X69")
def stable_worry_items():
    return sum(abs(rdiff(pct(t21, f"worry_{k}", [1]), pct(t19, f"worry_{k}", [1]))) <= 1 for k in FIVE)


@report.finding("X70")
def worry_trend_text():
    return {f"{k}_{y}": pct(TREND[y], f"worry_{k}", [1]) for k in ("crime", "food", "water") for y in (2019, 2021)}


@report.finding("X71")
def mental_worry_trend_text():
    return {str(y): pct(TREND[y], "worry_mental", [1]) for y in (2019, 2021)}


@report.finding("C4_2")
def worry_trend():
    return {f"{k}_{y}": pct(TREND[y], f"worry_{k}", [1]) for k in ("weather", "crime", "mental", "food", "water")
            for y in (2019, 2021)}


@report.finding("X72")
def mental_harm_2021():
    return {"personally": pct(t21, "WP22447", PERSONAL), "someone_known": pct(t21, "WP22447", [2])}


@report.finding("C4_3")
def mental_harm_by_income_group():
    # Totals for each World Bank income group; the country points carry no values.
    r = pct(d, "WP22447", PERSONAL, by="CountryIncomeLevel")
    c = pct(d, "WP22447", PERSONAL, by="COUNTRY_ISO3")
    groups = {"low": r[1], "lower_middle": r[2], "upper_middle": r[3], "high": r[4]}
    return {**groups, **{iso: c[iso] for iso in sorted(c.index)}}


@report.finding("X73")
def climate_very_serious_about_half():
    r = pct(d, "WP20719", [1], by="GlobalRegion")
    return {"northern_america": r[6], "australia_nz": r[15]}


@report.finding("C4_4")
def climate_by_weather_worry():
    r = pct(d[d.GlobalRegion.isin([6, 15, 10, 9])], "WP20719", [1], by=["GlobalRegion", "WP20723"])
    return {f"{REGIONS[g]}_{wk}": r[(g, wc)] for g in (6, 15, 10, 9) for wc, wk in ((1, "very"), (2, "somewhat"), (3, "not"))}


QWORRY = {"road": ("WP22213", d), "weather": ("WP20723", d), "mental": ("WP20726", d), "work": ("WP22214", workers),
          "food": ("WP20720", d), "water": ("WP20721", d), "crime": ("WP20722", d)}


def worry_by_quintile(item):
    var, df = QWORRY[item]
    return pct(df, var, [1], by="INCOME_5")


@report.finding("X74")
def worry_top_bottom_quintile():
    out = {}
    for item in ("road", "weather", "mental", "work"):
        r = worry_by_quintile(item)
        out.update({f"{item}_top": r[5], f"{item}_bottom": r[1]})
    return out


@report.finding("X75")
def risks_with_quintile_gap_10():
    return sum(rdiff(r[1], r[5]) >= 10 for r in map(worry_by_quintile, QWORRY))


C45 = {"weather": "WP22445", "work": "WP22448", "mental": "WP22447", "road": "WP22446", "food": "WP22442",
       "water": "WP22443", "crime": "WP22444"}


@report.finding("C4_5")
def harm_by_quintile():
    out = {}
    for item, var in C45.items():
        r = pct(d, var, PERSONAL, by="INCOME_5")
        out.update({f"{item}_{qk}": r[qc] for qc, qk in QUINTILES.items()})
    return out


def regional_harm_by_quintile():
    sa = pct(d[d.GlobalRegion == 4], "WP22444", PERSONAL, by="INCOME_5")
    ea = pct(d[d.GlobalRegion == 8], "WP22445", PERSONAL, by="INCOME_5")
    return sa, ea


@report.finding("X76")
def regional_harm_quintiles_text():
    sa, ea = regional_harm_by_quintile()
    return {"southern_africa_crime_bottom": sa[1], "southern_africa_crime_top": sa[5],
            "eastern_asia_weather_bottom": ea[1], "eastern_asia_weather_top": ea[5]}


@report.finding("X77")
def three_times_as_likely():
    sa, _ = regional_harm_by_quintile()
    return rratio(sa[1], sa[5])


# --- Chapter 5: Risk perceptions related to climate change ---------------------------


@report.finding("X78")
def climate_not_or_dk_trend():
    return {str(y): pct(TREND[y], "climate", [3, 98]) for y in (2019, 2021)}


@report.finding("C5_1")
def climate_global():
    return {f"{y}_{k}": v for y in (2019, 2021) for k, v in shares(TREND[y], "climate", CLIMATE).items()}


@report.finding("C5_2")
def climate_by_education():
    return flat(shares(d, "WP20719", CLIMATE, by="Education"), EDUCATION)


NOT_RECOGNISED = {"not": [3], "dk": [98], "total": [3, 98]}  # Table 5.1: refused not in 'don't know' or total


@report.finding("X79")
def climate_not_recognised_text():
    r = pct(t21, "climate", NOT_RECOGNISED["total"], by="GlobalRegion")
    return {REGIONS[c]: r[c] for c in (5, 12, 6, 15)}


@report.finding("X80")
def regions_not_recognised_40():
    return int((pct(t21, "climate", NOT_RECOGNISED["total"], by="GlobalRegion") > 40).sum())


@report.finding("X81")
def northern_africa_climate_by_education():
    r = pct(d[d.GlobalRegion == 3], "WP20719", [3, 98], by="Education")
    return {k: r[c] for c, k in EDUCATION.items()}


@report.finding("X82")
def countries_climate_dk_30():
    return int((pct(d, "WP20719", [98], by="COUNTRY_ISO3") > 30).sum())


china = d[d.COUNTRY_ISO3 == "CHN"]


@report.finding("X83")
def china_climate_dk():
    return pct(china, "WP20719", [98])


@report.finding("X84")
def china_climate_dk_people():
    return china.loc[china.WP20719 == 98, "PROJWT"].sum()


@report.finding("X85")
def china_climate_by_education():
    r = pct(china, "WP20719", [3, 98], by="Education")
    return {"primary": r[1], "post_secondary": r[3]}


@report.finding("T5_1")
def climate_not_recognised_by_region():
    out = {}
    t = {y: shares(TREND[y], "climate", NOT_RECOGNISED, by="GlobalRegion") for y in (2019, 2021)}
    for c, k in REGIONS.items():
        for y in (2019, 2021):
            out.update({f"{k}_{y}_{col}": t[y].loc[c, col] for col in NOT_RECOGNISED})
    return out


WEATHER_HARM = {1: "experienced", 2: "know_someone", 3: "neither"}


@report.finding("X86")
def climate_by_weather_harm_text():
    r = pct(d, "WP20719", [1], by="weather_harm")
    return {k: r[c] for c, k in WEATHER_HARM.items()}


@report.finding("X87")
def climate_primary_experienced():
    return pct(d[(d.Education == 1) & (d.weather_harm == 1)], "WP20719", [1])


@report.finding("X88")
def climate_secondary_plus_experienced():
    return pct(d[d.Education.isin([2, 3]) & (d.weather_harm == 1)], "WP20719", [1])


@report.finding("C5_3")
def climate_by_education_and_weather_harm():
    total = pct(d, "WP20719", [1], by="weather_harm")
    r = pct(d, "WP20719", [1], by=["Education", "weather_harm"])
    out = {f"total_{k}": total[c] for c, k in WEATHER_HARM.items()}
    out.update({f"{ek}_{k}": r[(e, c)] for e, ek in EDUCATION.items() for c, k in WEATHER_HARM.items()})
    return out


if __name__ == "__main__":
    sys.exit(report.run())
