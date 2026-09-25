"""Reproduce World Risk Poll 2024 Report: Resilience in a Changing World.

Run from the repository root:
    python reports/WRP_2023/core_resilience_in_a_changing_world/reproduce.py

The report uses the 2023 poll (wave 3) and compares it with 2021 (wave 2).
Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, countries_in_all, external_path, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

REGIONS = {  # GlobalRegion code -> key
    1: "east_africa", 2: "central_western_africa", 3: "north_africa", 4: "southern_africa",
    5: "latin_america", 6: "north_america", 7: "central_asia", 8: "east_asia", 9: "southeast_asia",
    10: "south_asia", 11: "middle_east", 12: "eastern_europe", 13: "northern_western_europe",
    14: "southern_europe", 15: "anz",
}
INCOME = {4: "high", 3: "upper_middle", 2: "lower_middle", 1: "low"}  # CountryIncomeLevel
DIMS = {"index": "ri", "individual": "idv", "household": "hhl", "community": "com", "societal": "soc"}
WARNING_SOURCES = {"internet": "WP22248", "government": "WP22249", "radio": "WP22250", "community": "WP22251"}
DISCRIMINATION = ["WP22259", "WP22260", "WP22261", "WP22262", "WP22263"]
RESILIENCE = ["resilience_index_100", "resilience_idv", "resilience_hhl", "resilience_com", "resilience_soc"]
COMMON = [
    "WPID_RANDOM", "COUNTRY_ISO3", "Country", "GlobalRegion", "CountryIncomeLevel", "PROJWT", "WGT",
    "Gender", "AgeGroups3", "AgeGroups4", "Education", "Urbanicity", "EMP_2010", "INCOME_5", *RESILIENCE,
    "WP22247", *WARNING_SOURCES.values(), "WP22252", "WP22228", "WP22229", *DISCRIMINATION,
    "REGION_PAK", "REGION_NZL",
]

d23 = load_wave(2023, COMMON + ["WP23344", "WP23345", "WP20719"])
d21 = load_wave(2021, COMMON + ["WP22245", "WP22253"])

# --- Derived variables ---------------------------------------------------------

# The same questions under their 2021 and 2023 names: experienced a disaster in
# the past five years, and a household disaster plan known by all members.
d23 = d23.rename(columns={"WP23344": "disaster", "WP23345": "plan"})
d21 = d21.rename(columns={"WP22245": "disaster", "WP22253": "plan"})

# Region and income group: the report classifies countries by their 2023
# region and income group in both years (Iran moves from the Middle East to
# Southern Asia; seven countries change income group). This reproduces the
# 2021 regional and income-group figures; each wave's own codes do not.
REGION_2023 = d23.groupby("COUNTRY_ISO3").GlobalRegion.first()
INCOME_2023 = d23.groupby("COUNTRY_ISO3").CountryIncomeLevel.first()

for d in (d23, d21):
    # Resilience Index and its four dimensions on the published 0-100 scale.
    d["ri"] = d.resilience_index_100
    for short, var in zip(["idv", "hhl", "com", "soc"], RESILIENCE[1:]):
        d[short] = 100 * d[var]
    d["region"] = d.COUNTRY_ISO3.map(REGION_2023).fillna(d.GlobalRegion)
    d["income"] = d.COUNTRY_ISO3.map(INCOME_2023).fillna(d.CountryIncomeLevel)

    # Early warning (Chapter 3), among those who experienced a disaster:
    # 1 = yes to at least one source; 2 = no to at least one and yes to none;
    # missing if no substantive answer (yes/no) to any source.
    src = d[list(WARNING_SOURCES.values())]
    d["warned"] = np.select([src.eq(1).any(axis=1), src.eq(2).any(axis=1)], [1, 2], default=np.nan)

    # Financial resilience (how long the household could cover basic needs):
    # 1 = less than a week; 2 = a week to a month (includes DK on the weeks
    # follow-up); 3 = a month or more; missing = DK/refused on WP22228.
    d["fin"] = np.select([d.WP22228.eq(1) & d.WP22229.eq(1), d.WP22228.eq(1), d.WP22228.eq(2)], [1, 2, 3],
                         default=np.nan)

    # Employment (Chart 4.1): 1 = full time for an employer; 2 = in the
    # workforce but not (self-employed, part time, unemployed); 3 = out of it.
    d["emp"] = d.EMP_2010.map({1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 6: 3})

    # Any discrimination (Chart 2.11): yes to any of the five types, among
    # respondents asked at least one of them (DK/refused kept in the base).
    asked = d[DISCRIMINATION].notna().any(axis=1)
    d["any_discrimination"] = np.where(asked, np.where(d[DISCRIMINATION].eq(1).any(axis=1), 1, 2), np.nan)

    # Disaster type (WP22247) among everyone asked whether they experienced a
    # disaster: flooding (code 1) vs anything else, including no disaster.
    d["flood"] = np.where(d.disaster.notna(), np.where(d.WP22247.eq(1), 1, 2), np.nan)
    d["earthquake"] = np.where(d.disaster.notna(), np.where(d.WP22247.eq(7), 1, 2), np.nan)

ew23 = d23[d23.warned.notna()]  # experienced a disaster, substantive answer on warnings
ew21 = d21[d21.warned.notna()]
exp23 = d23[d23.disaster.eq(1)]  # experienced a disaster in the past five years
exp21 = d21[d21.disaster.eq(1)]

BOTH = countries_in_all([2021, 2023])  # the 120 countries measured in both years

# --- Helpers -------------------------------------------------------------------


def scores(df, by):
    """Resilience Index and dimension scores (0-100) by group: DataFrame, columns = DIMS keys."""
    return pd.DataFrame({dim: wmean(df, var, by=by) for dim, var in DIMS.items()})


S23 = scores(d23, "COUNTRY_ISO3")
S21 = scores(d21, "COUNTRY_ISO3")
CHANGE = (S23 - S21).loc[BOTH]  # country change 2021-2023, 120 countries (NaN where a score is missing)


def significant(dim):
    """Counts of countries whose score rose, fell or held: a change that rounds
    to four points or more is significant (|change| >= 3.5 points)."""
    ch = CHANGE[dim].dropna()
    return {"increase": int((ch >= 3.5).sum()), "decrease": int((ch <= -3.5).sum()),
            "no_change": int((ch.abs() < 3.5).sum())}


def change_chart(dim, isos):
    """2021 and 2023 score and point change for the countries in a chart."""
    out = {}
    for iso in isos:
        out[f"{iso}_2021"] = S21.loc[iso, dim]
        out[f"{iso}_2023"] = S23.loc[iso, dim]
        out[f"{iso}_change"] = S23.loc[iso, dim] - S21.loc[iso, dim]
    return out


def by_region(values):
    return {REGIONS[int(k)]: v for k, v in values.items() if int(k) in REGIONS}


def country_pct(df, var, codes):
    return pct(df, var, codes, by="COUNTRY_ISO3")


def corr(x, y):
    """Pearson correlation over countries with both values."""
    xy = pd.concat([x.rename("x"), y.rename("y")], axis=1).dropna()
    return float(np.corrcoef(xy.x, xy.y)[0, 1])


def country_change(var, codes):
    """Country change 2021-2023 in the % giving `codes` (common countries)."""
    return (country_pct(d23, var, codes) - country_pct(d21, var, codes)).loc[BOTH]


def gap_by_country(df, var, high, low):
    """Resilience Index of group `high` minus group `low` of `var`, by country."""
    return (wmean(df[df[var] == high], "ri", by="COUNTRY_ISO3")
            - wmean(df[df[var] == low], "ri", by="COUNTRY_ISO3"))


# --- Executive summary -----------------------------------------------------------


@report.finding("X01")
def interviews():
    return len(d23)


@report.finding("X02")
def countries_2023():
    return d23.COUNTRY_ISO3.nunique()


@report.finding("X03")
def countries_both():
    return len(BOTH)


@report.finding("X04")
def global_index_2023():
    return wmean(d23, "ri")


@report.finding("X05")
def global_index_2021():
    return wmean(d21, "ri")


@report.finding("X06")
def no_significant_change():
    return significant("index")["no_change"]


@report.finding("X07")
def significant_declines():
    return significant("index")["decrease"]


@report.finding("X08")
def significant_increases():
    return significant("index")["increase"]


@report.finding("X09")
def individual_declines():
    return significant("individual")["decrease"]


@report.finding("X10")
def no_agency_2021():
    return pct(d21, "WP22252", [2])


@report.finding("X11")
def no_agency_2023():
    return pct(d23, "WP22252", [2])


@report.finding("X12")
def no_warning_2023():
    return pct(ew23, "warned", [2])


@report.finding("X13")
def no_warning_2021():
    return pct(ew21, "warned", [2])


def mobile_phone(df):
    # Gallup World Poll mobile phone ownership (placeholder name; see README):
    # 1 = has a mobile phone that can access the internet, 2 = has one that
    # cannot (or does not know), 3 = no mobile phone.
    return merge_gallup(df, ["GWP_MOBILE_PHONE"])


@report.finding("X14")
def not_warned_own_phone():
    return pct(mobile_phone(ew23[ew23.warned == 2]), "GWP_MOBILE_PHONE", [1, 2])


@report.finding("X15")
def disaster_2023():
    return pct(d23, "disaster", [1])


@report.finding("X16")
def disaster_2021():
    return pct(d21, "disaster", [1])


@report.finding("X17")
def countries_planning_trend():
    return int((country_change("disaster", [1]).notna() & country_change("plan", [1]).notna()).sum())


# --- Chapter 2: The state of global resilience -------------------------------------


@report.finding("X18")
def global_index_2021_box():
    return wmean(d21, "ri")


@report.finding("X19")
def global_index_2023_box():
    return wmean(d23, "ri")


@report.finding("X20")
def decreases_box():
    return significant("index")["decrease"]


@report.finding("X21")
def increases_box():
    return significant("index")["increase"]


@report.finding("X22")
def east_asia_increase():
    return wmean(d23[d23.region == 8], "ri") - wmean(d21[d21.region == 8], "ri")


@report.finding("C2_1")
def index_by_region():
    out = {}
    for year, d in (("2021", d21), ("2023", d23)):
        for key, v in by_region(wmean(d, "ri", by="region")).items():
            out[f"{key}_{year}"] = v
    return out


@report.finding("X23")
def countries_2021():
    return d21.COUNTRY_ISO3.nunique()


@report.finding("X24")
def countries_2023_ch2():
    return d23.COUNTRY_ISO3.nunique()


@report.finding("X25")
def countries_both_ch2():
    return len(BOTH)


@report.finding("X26")
def unchanged_ch2():
    return significant("index")["no_change"]


def margin_of_error(df):
    """95% margin of error (points) for a 50% proportion, with the Kish design effect of WGT."""
    def moe(g):
        n, w = len(g), g.WGT
        deff = n * (w ** 2).sum() / w.sum() ** 2
        return 196 * np.sqrt(0.25 * deff / n)
    return df.groupby("COUNTRY_ISO3").apply(moe, include_groups=False)


@report.finding("X27")
def average_margin_of_error():
    return margin_of_error(d23).mean()


@report.finding("C2_2")
def changes_overall():
    return significant("index")


@report.finding("X28")
def comparable_countries():
    return int(CHANGE["index"].notna().sum())


@report.finding("C2_3")
def biggest_decreases():
    return change_chart("index", ["BGR", "ECU", "HRV", "MAR", "MKD", "LAO", "POL", "EGY", "SRB", "SVK"])


@report.finding("C2_4")
def biggest_increases():
    return change_chart("index", ["DZA", "GAB", "BFA", "RUS", "SLV", "KGZ", "THA", "UKR", "MLI", "LBN"])


def index_change(iso, dim="index"):
    return CHANGE.loc[iso, dim]


@report.finding("X29")
def bulgaria_change():
    return index_change("BGR")


@report.finding("X30")
def ecuador_change():
    return index_change("ECU")


@report.finding("X31")
def morocco_change():
    return index_change("MAR")


@report.finding("X32")
def algeria_change():
    return index_change("DZA")


@report.finding("X33")
def gabon_change():
    return index_change("GAB")


@report.finding("X34")
def conflict_increases():
    return CHANGE.loc[["BFA", "RUS", "KGZ", "UKR"], "index"].min()


@report.finding("X35")
def mali_change():
    return index_change("MLI")


@report.finding("X36")
def lebanon_change():
    return index_change("LBN")


@report.finding("X37")
def kuwait_index():
    return S23.loc["KWT", "index"]


@report.finding("X38")
def vietnam_index():
    return S23.loc["VNM", "index"]


@report.finding("X39")
def uzbekistan_change():
    return index_change("UZB")


@report.finding("X40")
def afghanistan_index():
    return S23.loc["AFG", "index"]


@report.finding("X41")
def afghanistan_change():
    return index_change("AFG")


@report.finding("X42")
def ecuador_change_bottom10():
    return index_change("ECU")


@report.finding("X43")
def china_index():
    return S23.loc["CHN", "index"]


def rank_2023(iso, dim="index"):
    return int(S23[dim].rank(ascending=False)[iso])


@report.finding("X44")
def kuwait_rank():
    return rank_2023("KWT")


@report.finding("X45")
def vietnam_rank():
    return rank_2023("VNM")


@report.finding("C2_5")
def country_index_2023():
    # Chart 2.5 shows every country's 2023 score as an unlabelled dot: no
    # published values to compare.
    return S23["index"].dropna()


@report.finding("C2_6")
def significant_changes_by_dimension():
    out = {}
    for dim in DIMS:
        s = significant(dim)
        out[f"{dim}_increase"], out[f"{dim}_decrease"] = s["increase"], s["decrease"]
    return out


@report.finding("X46")
def individual_declines_ch2():
    return significant("individual")["decrease"]


@report.finding("X47")
def overall_declines_comparison():
    return significant("index")["decrease"]


@report.finding("X48")
def individual_stable():
    return significant("individual")["no_change"]


@report.finding("X49")
def individual_increases():
    return significant("individual")["increase"]


@report.finding("X50")
def overall_increases_ch26():
    return significant("index")["increase"]


@report.finding("X51")
def overall_decreases_ch26():
    return significant("index")["decrease"]


@report.finding("X52")
def bulgaria_individual():
    return index_change("BGR", "individual")


@report.finding("X53")
def poland_individual():
    return index_change("POL", "individual")


@report.finding("X54")
def morocco_individual():
    return index_change("MAR", "individual")


@report.finding("X55")
def croatia_individual():
    return index_change("HRV", "individual")


@report.finding("C2_7")
def individual_changes():
    return change_chart("individual", ["DZA", "CHN", "LBN", "KGZ", "PRY", "SRB", "HRV", "MAR", "POL", "BGR"])


@report.finding("X56")
def no_agency_2023_ch2():
    return pct(d23, "WP22252", [2])


@report.finding("X57")
def no_agency_2021_ch2():
    return pct(d21, "WP22252", [2])


@report.finding("X58")
def household_stable():
    return significant("household")["no_change"]


@report.finding("X59")
def household_decreases():
    return significant("household")["decrease"]


@report.finding("X60")
def household_increases():
    return significant("household")["increase"]


@report.finding("C2_8")
def household_changes():
    return change_chart("household", ["DZA", "UZB", "TGO", "KGZ", "NIC", "MYS", "BGR", "MKD", "MAR", "BGD"])


@report.finding("X61")
def community_decreases():
    return significant("community")["decrease"]


@report.finding("X62")
def community_increases():
    return significant("community")["increase"]


@report.finding("C2_9")
def community_changes():
    return change_chart("community", ["THA", "SLV", "MMR", "LBN", "ZMB", "CYP", "ECU", "NZL", "LTU", "HRV"])


@report.finding("X63")
def community_by_income():
    out = {}
    for year, d in (("2021", d21), ("2023", d23)):
        for code, v in wmean(d, "com", by="income").items():
            if code in INCOME:
                out[f"{INCOME[code]}_{year}"] = v
    return out


@report.finding("X64")
def societal_stable():
    return significant("societal")["no_change"]


@report.finding("X65")
def societal_declines():
    return significant("societal")["decrease"]


@report.finding("X66")
def societal_increases():
    return significant("societal")["increase"]


@report.finding("C2_10")
def societal_changes():
    return change_chart("societal", ["GAB", "THA", "MLI", "UKR", "BFA", "SLE", "ECU", "LAO", "EGY", "JOR"])


@report.finding("X67")
def brazil_societal():
    return index_change("BRA", "societal")


def local_economy():
    # Gallup World Poll: local economic conditions getting better (1) or
    # worse (2); placeholder name, see README.
    return merge_gallup(d23, ["GWP_LOCAL_ECONOMY"])


@report.finding("X68")
def brazil_local_economy():
    return pct(local_economy(), "GWP_LOCAL_ECONOMY", [1], by="COUNTRY_ISO3")["BRA"]


@report.finding("X69")
def top_local_economy_g7_brics():
    g7_brics = ["CAN", "FRA", "DEU", "ITA", "JPN", "GBR", "USA", "BRA", "RUS", "IND", "CHN", "ZAF"]
    s = pct(local_economy(), "GWP_LOCAL_ECONOMY", [1], by="COUNTRY_ISO3")
    return d23.loc[d23.COUNTRY_ISO3 == s[g7_brics].idxmax(), "Country"].iloc[0]


def discrimination_by_income():
    out = {}
    for year, d in (("2021", d21), ("2023", d23)):
        out[f"total_{year}"] = pct(d, "any_discrimination", [1])
        for code, v in pct(d, "any_discrimination", [1], by="income").items():
            if code in INCOME:
                out[f"{INCOME[code]}_{year}"] = v
    return out


@report.finding("C2_11")
def discrimination_chart():
    return discrimination_by_income()


@report.finding("X70")
def discrimination_global():
    r = discrimination_by_income()
    return {"2021": r["total_2021"], "2023": r["total_2023"]}


@report.finding("X71")
def discrimination_income_text():
    return {k: v for k, v in discrimination_by_income().items() if not k.startswith("total")}


DISC23 = country_pct(d23, "any_discrimination", [1])


@report.finding("X72")
def discrimination_increases():
    change = (DISC23 - country_pct(d21, "any_discrimination", [1])).dropna()
    return change[["USA", "SGP", "BEL", "KOR", "SVN", "EST", "CAN", "LVA"]].min()


@report.finding("X73")
def discrimination_highest():
    return DISC23[["USA", "TCD", "AFG", "LBR"]].to_dict()


@report.finding("X74")
def usa_discrimination_rank():
    return int(DISC23.rank(ascending=False)["USA"])


@report.finding("X75")
def usa_discrimination_types():
    usa = d23[d23.COUNTRY_ISO3 == "USA"]
    return {k: pct(usa, v, [1]) for k, v in
            {"nationality": "WP22261", "gender": "WP22262", "skin": "WP22259", "disability": "WP22263"}.items()}


@report.finding("X76")
def corr_individual_household():
    return corr(CHANGE["individual"], CHANGE["household"])


@report.finding("X77")
def corr_community_societal():
    return corr(CHANGE["community"], CHANGE["societal"])


# Table 2.2: country names as printed where they differ from the data's names.
REPORT_NAMES = {"TWN": "Taiwan, PoC", "COD": "Democratic Republic of the Congo", "CIV": "Côte d'Ivoire"}
NAMES = d23.groupby("COUNTRY_ISO3").Country.first()


def ranking(dim):
    """Countries ordered from highest to lowest 2023 score on `dim`."""
    return list(S23[dim].dropna().sort_values(ascending=False).index)


@report.finding("T2_2")
def top_and_bottom():
    out = {}
    for dim in ["individual", "household", "community", "societal"]:
        order = ranking(dim)
        for k in range(10):
            out[f"{dim}_top_{k + 1}"] = REPORT_NAMES.get(order[k], NAMES[order[k]])
            iso = order[-(k + 1)]
            out[f"{dim}_bottom_{k + 1}"] = REPORT_NAMES.get(iso, NAMES[iso])
    return out


def extremes_count():
    """Per country: number of dimensions in the top 10, and in the bottom 10."""
    top, bottom = pd.Series(0, index=S23.index), pd.Series(0, index=S23.index)
    for dim in ["individual", "household", "community", "societal"]:
        order = ranking(dim)
        top[order[:10]] += 1
        bottom[order[-10:]] += 1
    return top, bottom


@report.finding("X78")
def extreme_countries():
    top, bottom = extremes_count()
    return {"KWT": top["KWT"], "AFG": bottom["AFG"], "YEM": bottom["YEM"]}


@report.finding("X79")
def other_extreme_countries():
    # Top and bottom counted separately (Niger is in the bottom 10 twice and
    # the top 10 once, see README).
    top, bottom = extremes_count()
    others = ~top.index.isin(["KWT", "AFG", "YEM"])
    return int(((top > 2) | (bottom > 2))[others].sum())


# --- Chapter 3: Early warnings ----------------------------------------------------


@report.finding("X80")
def warned_2023():
    return pct(ew23, "warned", [1])


@report.finding("X81")
def not_warned_2023():
    return pct(ew23, "warned", [2])


@report.finding("X82")
def warned_2021():
    return pct(ew21, "warned", [1])


@report.finding("X83")
def not_warned_2021():
    return pct(ew21, "warned", [2])


EW4ALL_IN_POLL = ["MOZ", "MUS", "KHM", "BGD", "LAO", "MDG", "SOM", "UGA", "COM", "LBR", "GTM", "ECU", "NPL",
                  "NER", "TCD", "TJK", "ETH"]  # Early Warnings for All priority countries shown in Chart 3.1


@report.finding("X84")
def ew4all_countries():
    return int(pd.Series(EW4ALL_IN_POLL).isin(d23.COUNTRY_ISO3).sum())


@report.finding("C3_1")
def ew4all_warned():
    return country_pct(ew23, "warned", [1])[EW4ALL_IN_POLL].to_dict()


@report.finding("X85")
def warning_by_hazard():
    hazards = {"earthquake": (7, 2), "mudslide": (6, 2), "heatwave": (51, 1), "hurricane": (2, 1),
               "blizzard": (10, 1), "tornado": (3, 1), "flood": (1, 1)}  # WP22247 code, warned answer
    return {k: pct(ew23[ew23.WP22247 == code], "warned", [answer]) for k, (code, answer) in hazards.items()}


@report.finding("X86")
def warning_sources_text():
    out = {}
    for key in ["radio", "government", "internet"]:
        out[f"{key}_2023"] = pct(exp23, WARNING_SOURCES[key], [1])
        out[f"{key}_2021"] = pct(exp21, WARNING_SOURCES[key], [1])
    return out


@report.finding("C3_2")
def warning_sources():
    return {f"{key}_{year}": pct(d, var, [1])
            for key, var in WARNING_SOURCES.items() for year, d in (("2021", exp21), ("2023", exp23))}


AGE4 = {1: "15_29", 2: "30_49", 3: "50_64", 4: "65plus"}


@report.finding("C3_3")
def internet_warning_by_age():
    out = {}
    for year, d in (("2021", exp21), ("2023", exp23)):
        for code, v in pct(d, "WP22248", [1], by="AgeGroups4").items():
            out[f"{AGE4[int(code)]}_{year}"] = v
    return out


@report.finding("X87")
def internet_warning_age_text():
    r = pct(exp23, "WP22248", [1], by="AgeGroups4")
    return {"15_29": r[1], "65plus": r[4]}


@report.finding("X88")
def internet_access():
    return pct(merge_gallup(d23, ["GWP_INTERNET_ACCESS"]), "GWP_INTERNET_ACCESS", [1])


@report.finding("X89")
def warned_2018_2023():
    return pct(ew23, "warned", [1])


def warned_by(var, labels):
    """% at least one warning and % no warning, by group."""
    warned, none = pct(ew23, "warned", [1], by=var), pct(ew23, "warned", [2], by=var)
    out = {}
    for code, label in labels.items():
        out[f"{label}_warned"], out[f"{label}_none"] = warned[code], none[code]
    return out


@report.finding("C3_4")
def warned_by_region():
    return warned_by("region", REGIONS)


EDUCATION = {1: "primary", 2: "secondary", 3: "tertiary"}
FIN = {1: "less_week", 2: "week_month", 3: "month_plus"}


@report.finding("C3_5")
def warned_by_education():
    return warned_by("Education", EDUCATION)


@report.finding("X90")
def warned_education_text():
    r = pct(ew23, "warned", [1], by="Education")
    return {label: r[code] for code, label in EDUCATION.items()}


@report.finding("C3_6")
def warned_by_financial_resilience():
    return warned_by("fin", FIN)


@report.finding("X91")
def warned_financial_text():
    r = pct(ew23, "warned", [1], by="fin")
    return {"month_plus": r[3], "less_week": r[1]}


@report.finding("C3_7")
def warned_by_urbanisation():
    # Gallup's degree of urbanisation (placeholder name; see README):
    # 1 = rural areas, 2 = towns and semi-dense areas, 3 = cities.
    g = merge_gallup(ew23, ["GWP_DEGURBA"])
    warned, none = pct(g, "warned", [1], by="GWP_DEGURBA"), pct(g, "warned", [2], by="GWP_DEGURBA")
    out = {}
    for code, label in {1: "rural", 2: "towns", 3: "cities"}.items():
        out[f"{label}_warned"], out[f"{label}_none"] = warned[code], none[code]
    return out


@report.finding("X92")
def warned_by_sex():
    r = pct(ew23, "warned", [1], by="Gender")
    return {"men": r[1], "women": r[2]}


@report.finding("X93")
def not_warned_have_phone():
    return pct(mobile_phone(ew23[ew23.warned == 2]), "GWP_MOBILE_PHONE", [1, 2])


@report.finding("X94")
def phone_ownership():
    g = mobile_phone(d23)
    return {"internet": pct(g, "GWP_MOBILE_PHONE", [1]), "no_internet": pct(g, "GWP_MOBILE_PHONE", [2]),
            "none": pct(g, "GWP_MOBILE_PHONE", [3])}


@report.finding("X95")
def smartphone_by_warning():
    r = pct(mobile_phone(ew23), "GWP_MOBILE_PHONE", [1], by="warned")
    return {"warned": r[1], "none": r[2]}


@report.finding("C3_8")
def phone_by_warning():
    g = mobile_phone(ew23)
    out = {}
    for code, label in {1: "warned", 2: "none"}.items():
        sub = g[g.warned == code]
        for phone, key in {1: "internet", 2: "no_internet", 3: "none"}.items():
            out[f"{label}_{key}"] = pct(sub, "GWP_MOBILE_PHONE", [phone])
    return out


@report.finding("C3_9")
def resilience_by_warning():
    s = scores(ew23, "warned")
    return {f"{dim}_{label}": s.loc[code, dim] for dim in DIMS for code, label in {1: "warned", 2: "none"}.items()}


# --- Chapter 4: What makes people more resilient? ----------------------------------------

@lru_cache(maxsize=None)
def world_bank():
    """World Bank indicators, 2020-2023 (snapshot in reports/external; see README)."""
    return pd.read_csv(external_path("core_resilience_in_a_changing_world__worldbank.csv"))


def wb(indicator, year):
    """World Bank indicator by ISO3 for one year."""
    w = world_bank()
    return w[(w.indicator == indicator) & (w.year == year)].set_index("iso3")["value"]


@lru_cache(maxsize=None)
def resilience_model():
    """WLS (PROJWT) of the Resilience Index on personal characteristics, region
    and country economic indicators (World Bank, 2023). Reference groups: out of
    the workforce, aged 50+, male, poorest 20%, rural, Eastern Africa."""
    m = d23[["ri", "EMP_2010", "AgeGroups3", "Gender", "INCOME_5", "Urbanicity", "GlobalRegion", "COUNTRY_ISO3",
             "PROJWT"]].copy()
    m["log_gdp_pc"] = np.log(m.COUNTRY_ISO3.map(wb("NY.GDP.PCAP.CD", 2023)))
    m["gdp_growth"] = m.COUNTRY_ISO3.map(wb("NY.GDP.MKTP.KD.ZG", 2023))
    m["inflation"] = m.COUNTRY_ISO3.map(wb("FP.CPI.TOTL.ZG", 2023))
    m = m.dropna()
    formula = ("ri ~ C(EMP_2010, Treatment(6)) + C(AgeGroups3, Treatment(3)) + C(Gender) + C(INCOME_5)"
               " + C(Urbanicity) + C(GlobalRegion) + log_gdp_pc + gdp_growth + inflation")
    return smf.wls(formula, data=m, weights=m.PROJWT).fit().params


@report.finding("X96")
def model_full_time():
    return resilience_model()["C(EMP_2010, Treatment(6))[T.1.0]"]


@report.finding("X97")
def afghanistan_employment_gap():
    return gap_by_country(d23, "emp", 1, 3)["AFG"]


@report.finding("X98")
def afghanistan_out_of_workforce():
    r = pct(d23[d23.COUNTRY_ISO3 == "AFG"], "emp", [3], by="Gender")
    return {"women": r[2], "men": r[1]}


@report.finding("X99")
def employment_gaps():
    return gap_by_country(d23, "emp", 1, 3)[["COM", "CHN"]].to_dict()


EMP = {1: "ft_employer", 2: "other_workforce", 3: "out_workforce"}


@report.finding("C4_1")
def dimensions_by_employment():
    s = scores(d23, "emp")
    return {f"{label}_{dim}": s.loc[code, dim] for code, label in EMP.items()
            for dim in ["individual", "household", "community", "societal"]}


@report.finding("X100")
def no_agency_by_employment():
    out = {}
    for year, d in (("2023", d23), ("2021", d21)):
        r = pct(d, "WP22252", [2], by="emp")
        out.update({f"out_{year}": r[3], f"other_{year}": r[2], f"ft_{year}": r[1]})
    return out


def quintile_gaps():
    poorest = wmean(d23[d23.INCOME_5 == 1], "ri", by="region")
    richest = wmean(d23[d23.INCOME_5 == 5], "ri", by="region")
    return poorest, richest


@report.finding("T4_1")
def income_quintiles_by_region():
    poorest, richest = quintile_gaps()
    out = {}
    for code, key in REGIONS.items():
        out[f"{key}_poorest"], out[f"{key}_richest"] = poorest[code], richest[code]
        out[f"{key}_gap"] = richest[code] - poorest[code]
    return out


@report.finding("X101")
def income_gaps_text():
    poorest, richest = quintile_gaps()
    return {key: richest[code] - poorest[code] for code, key in ((8, "east_asia"), (3, "north_africa"), (14, "southern_europe"))}


@report.finding("X102")
def model_age_15_29():
    return resilience_model()["C(AgeGroups3, Treatment(3))[T.1.0]"]


@report.finding("X103")
def model_age_30_49():
    return resilience_model()["C(AgeGroups3, Treatment(3))[T.2.0]"]


@report.finding("X104")
def age_gaps():
    return gap_by_country(d23, "AgeGroups4", 1, 4)[["MYS", "LKA", "PHL"]].to_dict()


GENDER_GAP = gap_by_country(d23, "Gender", 1, 2)  # men minus women


@report.finding("X105")
def women_above_men():
    men = wmean(d23[d23.Gender == 1], "ri", by="COUNTRY_ISO3").round()
    women = wmean(d23[d23.Gender == 2], "ri", by="COUNTRY_ISO3").round()
    return int((women > men).sum())


@report.finding("X106")
def gender_gaps():
    return GENDER_GAP[["AFG", "PAK", "CZE", "KOR"]].to_dict()


@report.finding("T4_2")
def conflict_countries():
    out = {}
    for iso in ["UKR", "RUS", "BFA", "MLI", "MMR", "AFG", "ECU"]:
        for dim in DIMS:
            out[f"{iso}_{dim}_2023"], out[f"{iso}_{dim}_2021"] = S23.loc[iso, dim], S21.loc[iso, dim]
    return out


@report.finding("X107")
def afghanistan_societal():
    return index_change("AFG", "societal")


@report.finding("X108")
def corr_growth_community():
    growth_change = wb("NY.GDP.MKTP.KD.ZG", 2023) - wb("NY.GDP.MKTP.KD.ZG", 2021)
    return corr(CHANGE["community"], growth_change.reindex(CHANGE.index))


@report.finding("X109")
def corr_financial_individual():
    return corr(country_change("WP22228", [2]), CHANGE["individual"])


@report.finding("C4_2")
def dimensions_by_financial_resilience():
    s = scores(d23, "fin")
    return {f"{label}_{dim}": s.loc[code, dim] for code, label in FIN.items() for dim in DIMS}


# --- Chapter 5: Natural hazards and resilience ----------------------------------------------


@report.finding("X110")
def disaster_both_years():
    return {"2023": pct(d23, "disaster", [1]), "2021": pct(d21, "disaster", [1])}


@report.finding("X111")
def disaster_types():
    return {k: pct(exp23, "WP22247", [code]) for k, code in (("flood", 1), ("hurricane", 2), ("earthquake", 7))}


@report.finding("X112")
def flooding_all_adults():
    return {"2023": pct(d23, "flood", [1]), "2021": pct(d21, "flood", [1])}


DISASTER_REGION = {year: by_region(pct(d, "disaster", [1], by="region")) for year, d in (("2021", d21), ("2023", d23))}


@report.finding("X113")
def anz_disaster():
    return DISASTER_REGION["2023"]["anz"]


def country_disaster(iso, d):
    return pct(d[d.COUNTRY_ISO3 == iso], "disaster", [1])


@report.finding("X114")
def nzl_aus_disaster():
    return {f"{iso}_{year}": country_disaster(iso, d) for iso in ("NZL", "AUS") for year, d in (("2023", d23), ("2021", d21))}


@report.finding("X115")
def disaster_region_increases():
    return {k: DISASTER_REGION["2023"][k] - DISASTER_REGION["2021"][k] for k in ("southern_africa", "central_asia")}


@report.finding("X116")
def ukraine_disaster():
    return {"2023": country_disaster("UKR", d23), "2021": country_disaster("UKR", d21)}


@report.finding("C5_1")
def disaster_by_region():
    return {f"{k}_{year}": v for year, r in DISASTER_REGION.items() for k, v in r.items()}


@report.finding("X117")
def agency_by_experience():
    r = pct(d23, "WP22252", [1], by="disaster")
    return {"exp": r[1], "noexp": r[2]}


@report.finding("X118")
def plan_by_experience():
    r = pct(d23, "plan", [1], by="disaster")
    return {"exp": r[1], "noexp": r[2]}


@report.finding("X119")
def countries_chart_5_2():
    return int((country_change("disaster", [1]).notna() & country_change("plan", [1]).notna()).sum())


@report.finding("X120")
def corr_experience_planning():
    return corr(country_change("disaster", [1]), country_change("plan", [1]))


@report.finding("X121")
def morocco_planning_change():
    return country_change("plan", [1])["MAR"]


@report.finding("C5_2")
def experience_and_planning_changes():
    # Scatter without data labels: no published values to compare.
    ch = pd.DataFrame({"experience": country_change("disaster", [1]), "planning": country_change("plan", [1])}).dropna()
    return {f"{iso}_{k}": v for iso, row in ch.iterrows() for k, v in row.items()}


@report.finding("X122")
def corr_experience_agency():
    return corr(country_change("disaster", [1]), country_change("WP22252", [1]))


@report.finding("X123")
def corr_region_plan_agency():
    return corr(pct(d23, "plan", [1], by="region"), pct(d23, "WP22252", [1], by="region"))


@report.finding("C5_3")
def plan_and_agency_by_region():
    # Scatter without data labels: no published values to compare.
    plan, agency = by_region(pct(d23, "plan", [1], by="region")), by_region(pct(d23, "WP22252", [1], by="region"))
    return {**{f"{k}_plan": v for k, v in plan.items()}, **{f"{k}_agency": v for k, v in agency.items()}}


@report.finding("C5_4")
def plan_and_agency_by_country():
    # Scatter without data labels: no published values to compare.
    plan, agency = country_pct(d23, "plan", [1]), country_pct(d23, "WP22252", [1])
    return {**{f"{k}_plan": v for k, v in plan.items()}, **{f"{k}_agency": v for k, v in agency.items()}}


def by_sex(var, codes):
    r = pct(d23, var, codes, by="Gender")
    return {"men": r[1], "women": r[2]}


@report.finding("X124")
def agency_by_sex():
    return by_sex("WP22252", [1])


@report.finding("X125")
def plan_by_sex():
    return by_sex("plan", [1])


@report.finding("X126")
def basic_needs_by_sex():
    return by_sex("WP22228", [2])


@report.finding("X127")
def climate_by_experience():
    r = pct(d23, "WP20719", [1], by="disaster")
    return {"exp": r[1], "noexp": r[2]}


CLIMATE_BY_TYPE = pct(exp23, "WP20719", [1], by="WP22247")


@report.finding("X128")
def climate_by_disaster_type():
    return {k: CLIMATE_BY_TYPE[code] for k, code in
            (("earthquake", 7), ("hurricane", 2), ("flood", 1), ("heatwave", 51), ("mudslide", 6))}


@report.finding("X129")
def mudslide_heatwave_ratio():
    return CLIMATE_BY_TYPE[6] / CLIMATE_BY_TYPE[51]


MAR23, MAR21 = d23[d23.COUNTRY_ISO3 == "MAR"], d21[d21.COUNTRY_ISO3 == "MAR"]


@report.finding("X130")
def morocco_resilience_text():
    return {"change": index_change("MAR"), "2023": S23.loc["MAR", "index"],
            "individual": index_change("MAR", "individual"), "household": index_change("MAR", "household")}


@report.finding("X131")
def morocco_disasters():
    m21 = MAR21[MAR21.disaster == 1]
    return {"2021": pct(MAR21, "disaster", [1]), "flood": pct(m21, "WP22247", [1]), "drought": pct(m21, "WP22247", [50]),
            "wildfire": pct(m21, "WP22247", [8]), "2023": pct(MAR23, "disaster", [1]),
            "earthquake": pct(MAR23[MAR23.disaster == 1], "WP22247", [7]), "earthquake_all": pct(MAR23, "earthquake", [1])}


@report.finding("X132")
def morocco_index_by_experience():
    r = wmean(MAR23, "ri", by="disaster")
    return {"exp": r[1], "noexp": r[2]}


@report.finding("C5_5")
def morocco_scores():
    return {f"{dim}_{year}": s.loc["MAR", dim] for dim in DIMS for year, s in (("2021", S21), ("2023", S23))}


@report.finding("X133")
def morocco_agency():
    r = pct(MAR23, "WP22252", [1], by="disaster")
    return {"2023": pct(MAR23, "WP22252", [1]), "2021": pct(MAR21, "WP22252", [1]), "exp": r[1], "noexp": r[2]}


@report.finding("X134")
def morocco_plan():
    return {"2023": pct(MAR23, "plan", [1]), "2021": pct(MAR21, "plan", [1])}


@report.finding("X135")
def morocco_donated():
    # Gallup World Poll WP108: donated money to a charity in the past month (1 = yes).
    return pct(merge_gallup(MAR23, ["WP108"]), "WP108", [1])


PAK23, PAK21 = d23[d23.COUNTRY_ISO3 == "PAK"], d21[d21.COUNTRY_ISO3 == "PAK"]
NZL23, NZL21 = d23[d23.COUNTRY_ISO3 == "NZL"], d21[d21.COUNTRY_ISO3 == "NZL"]


@report.finding("X136")
def pakistan_disaster():
    return {"2023": pct(PAK23, "disaster", [1]), "2021": pct(PAK21, "disaster", [1])}


@report.finding("X137")
def pakistan_flooding():
    return {"2023": pct(PAK23, "flood", [1]), "2021": pct(PAK21, "flood", [1])}


@report.finding("X138")
def new_zealand_disaster():
    return {"2023": pct(NZL23, "disaster", [1]), "2021": pct(NZL21, "disaster", [1])}


@report.finding("X139")
def new_zealand_flooding():
    return pct(NZL23, "flood", [1])


PAK_REGIONS = {1: "sindh", 2: "punjab", 3: "kp"}  # REGION_PAK
NZL_REGIONS = {2: "auckland", 9: "wellington", 14: "canterbury"}  # REGION_NZL


@report.finding("X140")
def pakistan_flooding_by_province():
    r = pct(PAK23, "flood", [1], by="REGION_PAK")
    return {key: r[code] for code, key in PAK_REGIONS.items()}


@report.finding("X141")
def auckland_flooding():
    return pct(NZL23, "flood", [1], by="REGION_NZL")[2]


def regional_changes(new, old, var, regions):
    ch = scores(new, var) - scores(old, var)
    return {f"{key}_{dim}": ch.loc[code, dim] for code, key in regions.items() for dim in DIMS}


@report.finding("X142")
def kp_changes():
    r = regional_changes(PAK23, PAK21, "REGION_PAK", PAK_REGIONS)
    return {"community": r["kp_community"], "societal": r["kp_societal"]}


@report.finding("C5_6")
def pakistan_regions():
    return regional_changes(PAK23, PAK21, "REGION_PAK", PAK_REGIONS)


@report.finding("X143")
def auckland_changes():
    r = regional_changes(NZL23, NZL21, "REGION_NZL", NZL_REGIONS)
    return {"community": r["auckland_community"], "societal": r["auckland_societal"]}


@report.finding("C5_7")
def new_zealand_regions():
    return regional_changes(NZL23, NZL21, "REGION_NZL", NZL_REGIONS)


# --- Appendices -----------------------------------------------------------------------------


@report.finding("X144")
def societal_items_missing():
    # Needs the Gallup national institutions items (placeholder name; see
    # README): countries where any societal item was not asked at all.
    g = merge_gallup(d23, ["GWP_NATIONAL_INSTITUTIONS"])
    items = [*DISCRIMINATION, "GWP_NATIONAL_INSTITUTIONS"]
    return int(g.groupby("COUNTRY_ISO3")[items].apply(lambda x: x.notna().any().eq(False).any()).sum())


@report.finding("X145")
def societal_all_missing():
    return int(S23["societal"].isna().sum())


@report.finding("TA_2")
def appendix_scores():
    moe = margin_of_error(d23)
    out = {}
    for iso in S23.index:
        out[f"{iso}_moe"] = moe[iso]
        for dim in DIMS:
            if pd.notna(S23.loc[iso, dim]):
                out[f"{iso}_{dim}"] = S23.loc[iso, dim]
    return out


if __name__ == "__main__":
    sys.exit(report.run())
