"""Reproduce World Risk Poll 2024 report: What the World Worries About.

Run from the repository root:
    python reports/WRP_2023/core_what_the_world_worries_about/reproduce.py

The report uses the 2023 poll, with trends back to 2021 and 2019. Each function
below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import GallupDataRequired, Report, distribution, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

REGIONS = {  # GlobalRegion code -> key used in finding ids
    1: "east_africa", 2: "cw_africa", 3: "north_africa", 4: "south_africa", 5: "latam",
    6: "north_america", 7: "central_asia", 8: "east_asia", 9: "se_asia", 10: "south_asia",
    11: "middle_east", 12: "east_europe", 13: "nw_europe", 14: "south_europe", 15: "anz",
}
# Risk -> (2019 worry item, 2021/2023 worry item, 2021/2023 experience item).
# Traffic and work were not asked in 2019; 2019 experience items are not used.
RISKS = {
    "food": ("L6A", "WP20720", "WP22442"), "water": ("L6B", "WP20721", "WP22443"),
    "crime": ("L6C", "WP20722", "WP22444"), "weather": ("L6D", "WP20723", "WP22445"),
    "traffic": (None, "WP22213", "WP22446"), "mental": ("L6G", "WP20726", "WP22447"),
    "work": (None, "WP22214", "WP22448"),
}
# Greatest source of risk (open question, coded): the codes differ in 2019.
ROAD = 1
CLIMATE = {2019: 16, 2021: 19, 2023: 19}  # 2019: "climate change, natural disasters or weather-related events"
CRIME, HEALTH = 3, 5
WORRIED = [1, 2]            # very or somewhat worried
PERSONAL = [1, 3]           # experience: "yes, personally" or "both"
EXPERIENCE = {"none": 4, "know": 2, "personal": 1, "both": 3}  # experience codes in chart order
DK = [98, 99]


def rnd(x):
    """Round half up to a whole number (the same rule in reproduce.R)."""
    return np.floor(x + 0.5)


# --- Data ------------------------------------------------------------------------------

def harmonise(df, year):
    """Common names across waves: safe, top_risk, climate, worry_<risk>, exp_<risk>."""
    names = {"L2": "safe", "L3_A": "top_risk", "L5": "climate"} if year == 2019 else \
        {"WP20711": "safe", "WP22331": "top_risk", "WP20719": "climate"}
    for risk, (w19, w, e) in RISKS.items():
        if year == 2019:
            if w19:
                names[w19] = f"worry_{risk}"
        else:
            names[w], names[e] = f"worry_{risk}", f"exp_{risk}"
    return df.rename(columns=names)


ITEMS_2123 = [v for _, w, e in RISKS.values() for v in (w, e)]
d23 = harmonise(load_wave(2023, [
    "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "WGT", "PROJWT", "Age", "Gender", "Education",
    "Urbanicity", "WP20711", "WP22331", "WP20719", *ITEMS_2123, "WP22232", "WP22228", "WP23344",
    "WP22247", "WP23342", "Q4_mean", "Q5_mean", "Q4_mean_projwt_byusertime", "Q5_mean_projwt_byusertime",
    "WPID_RANDOM",
]), 2023)
d21 = harmonise(load_wave(2021, ["COUNTRY_ISO3", "PROJWT", "WP20711", "WP22331", "WP20719", *ITEMS_2123,
                                 "WP22245", "WP22247"]), 2021)
d19 = harmonise(load_wave(2019, ["COUNTRY_ISO3", "PROJWT", "L2", "L3_A", "L5",
                                 *[w for w, _, _ in RISKS.values() if w]]), 2019)
N_COUNTRIES = {2019: d19.COUNTRY_ISO3.nunique(), 2021: d21.COUNTRY_ISO3.nunique(), 2023: d23.COUNTRY_ISO3.nunique()}

# --- Derived variables -----------------------------------------------------------------

# Trends (report footnote ii, page 7): earlier waves use only the countries surveyed
# in 2023 (137 in 2019, 120 in 2021), and every country keeps its 2023 region.
# Iran is Middle East in the 2019 and 2021 files and Southern Asia in 2023; the
# 2023 region reproduces Table 3.1 and the Chart 2.2 changes.
REGION_2023 = d23.groupby("COUNTRY_ISO3")["GlobalRegion"].first()
d23["region"] = d23["GlobalRegion"]
d21 = d21[d21.COUNTRY_ISO3.isin(REGION_2023.index)].copy()
d19 = d19[d19.COUNTRY_ISO3.isin(REGION_2023.index)].copy()
for df in (d21, d19):
    df["region"] = df.COUNTRY_ISO3.map(REGION_2023)
WAVE = {2019: d19, 2021: d21, 2023: d23}

# Climate change threat with refused merged into don't know (charts label this
# "Don't know/Refused"): 1 very, 2 somewhat, 3 not a threat, 98 DK/refused.
for df in WAVE.values():
    df["climate_dkr"] = df["climate"].replace({99: 98})


def valid_case_weight(df, ok):
    """PROJWT rescaled within each country so that the valid cases carry the
    country's whole population. This is how the 2023 file's
    Q4_mean_projwt_byusertime / Q5_mean_projwt_byusertime are built (checked
    to machine precision); it is applied to 2021 in the same way."""
    total = df.groupby("COUNTRY_ISO3")["PROJWT"].transform("sum")
    valid = df["PROJWT"].where(ok).groupby(df["COUNTRY_ISO3"]).transform("sum")
    return (df["PROJWT"] * total / valid).where(ok)


# Worry and Experience of Harm indices (Charts 4.6-4.8), 0-100. The report's
# definition is the simple mean of the seven items, not the Rasch-weighted
# worry_index_published / experience_index_published.
# 2023: the file's "Worried Mean" (Q4_mean) and "Experienced Mean" (Q5_mean)
# with their own projection weights.
d23["worry_idx"] = 100 * d23["Q4_mean"]
d23["exp_idx"] = 100 * d23["Q5_mean"]
d23["w_worry_idx"] = d23["Q4_mean_projwt_byusertime"]
d23["w_exp_idx"] = d23["Q5_mean_projwt_byusertime"]
# 2021: rebuilt with the rules that reproduce Q4_mean and Q5_mean exactly in 2023.
# Worry: very 2, somewhat 1, not 0, summed over the items asked and divided by 7
# (work, asked only of workers, counts 0 when not asked); missing if any asked
# item is DK/refused. Experience: share of the seven items personally experienced
# ("yes, personally" or "both"); missing if any item is DK/refused.
WORRY_COLS = [f"worry_{r}" for r in RISKS]
EXP_COLS = [f"exp_{r}" for r in RISKS]
score = d21[WORRY_COLS].replace({1: 2.0, 2: 1.0, 3: 0.0, 98: np.nan, 99: np.nan})
d21["worry_idx"] = (100 * score.fillna(0).sum(axis=1) / 14).where(~d21[WORRY_COLS].isin(DK).any(axis=1))
exp_ok = d21[EXP_COLS].notna().all(axis=1) & ~d21[EXP_COLS].isin(DK).any(axis=1)
d21["exp_idx"] = (100 * d21[EXP_COLS].isin(PERSONAL).mean(axis=1)).where(exp_ok)
d21["w_worry_idx"] = valid_case_weight(d21, d21["worry_idx"].notna())
d21["w_exp_idx"] = valid_case_weight(d21, d21["exp_idx"].notna())

# --- Helpers ---------------------------------------------------------------------------


def by_region(df, var, codes, **kw):
    """% by 2023 region, keyed by region name."""
    r = pct(df, var, codes, by="region", **kw)
    return {REGIONS[int(k)]: v for k, v in r.items()}


def country(df, var, codes, **kw):
    return pct(df, var, codes, by="COUNTRY_ISO3", **kw)


def top(series, n):
    """ISO3 codes of the n largest values, sorted alphabetically, as one string."""
    return "; ".join(sorted(series.sort_values(ascending=False).index[:n]))


def threat_shares(df, by=None):
    """% very, somewhat, not a threat, DK/refused and combined (very + somewhat)."""
    t = distribution(df, "climate_dkr", by=by)
    if by is None:
        t = t.to_frame().T
    out = pd.DataFrame({"very": t[1.0], "somewhat": t[2.0], "not": t[3.0], "dk": t[98.0]})
    out["combined"] = out["very"] + out["somewhat"]
    out["combined_rounded"] = rnd(out["very"]) + rnd(out["somewhat"])  # "based on rounded numbers"
    return out


# --- Executive summary --------------------------------------------------------------------


@report.finding("X01")
def interviews():
    return len(d23)


@report.finding("X02")
def countries_2023():
    return N_COUNTRIES[2023]


@report.finding("X03")
def threat_2023():
    return pct(d23, "climate", [1, 2])


@report.finding("X05")
def road_top_risk_2023():
    return pct(d23, "top_risk", [ROAD])


@report.finding("X06")
def road_top_risk_2021():
    return pct(d21, "top_risk", [ROAD])


@report.finding("X07")
def road_top_risk_2019():
    return pct(d19, "top_risk", [ROAD])


@report.finding("X08")
def more_safe_2023():
    return pct(d23, "safe", [1])


@report.finding("X09")
def about_as_safe_2023():
    return pct(d23, "safe", [3])


@report.finding("X10")
def less_safe_2023():
    return pct(d23, "safe", [2])


@report.finding("X11")
def worry_mental_2019():
    return pct(d19, "worry_mental", WORRIED)


@report.finding("X12")
def worry_mental_2021():
    return pct(d21, "worry_mental", WORRIED)


@report.finding("X13")
def worry_mental_2023():
    return pct(d23, "worry_mental", WORRIED)


# --- Chapter 2: road-related accidents -------------------------------------------------------


@report.finding("X14")
def crime_top_risk():
    return pct(d23, "top_risk", [CRIME])


@report.finding("X15")
def health_top_risk():
    return pct(d23, "top_risk", [HEALTH])


@report.finding("X16")
def climate_top_risk_2023():
    return pct(d23, "top_risk", [CLIMATE[2023]])


@report.finding("X17")
def climate_top_risk_2021():
    return pct(d21, "top_risk", [CLIMATE[2021]])


@report.finding("X18")
def climate_top_risk_2019():
    return pct(d19, "top_risk", [CLIMATE[2019]])


TOP_RISKS = {  # Chart 2.1: WP22331 codes (same in 2021 and 2023)
    "road": [1], "crime": [3], "health": [5], "dk": [98], "nothing": [23], "economy": [10],
    "climate": [19], "financial": [9], "other": [22], "war": [4],
}


@report.finding("C2_1")
def top_risks():
    out = {}
    for key, codes in TOP_RISKS.items():
        now = pct(d23, "top_risk", codes)
        out[key] = now
        out[f"{key}_chg"] = now - pct(d21, "top_risk", codes)  # unrounded change vs 2021
    return out


@report.finding("X19")
def road_high_income():
    return pct(d23, "top_risk", [ROAD], by="CountryIncomeLevel")[4]


@report.finding("X20")
def road_low_income():
    return pct(d23, "top_risk", [ROAD], by="CountryIncomeLevel")[1]


for _fid, _key in (("X21", "anz"), ("X22", "north_america"), ("X23", "se_asia"), ("X24", "central_asia"), ("X25", "south_africa")):
    report.finding(_fid)(lambda key=_key: by_region(d23, "top_risk", [ROAD])[key])


@report.finding("X26")
def road_minus_health():
    return pct(d23, "top_risk", [ROAD]) - pct(d23, "top_risk", [HEALTH])


@report.finding("C2_2")
def road_top_risk_by_region():
    now, before = by_region(d23, "top_risk", [ROAD]), by_region(d21, "top_risk", [ROAD])
    out = {}
    for key in now:
        out[key] = now[key]
        out[f"{key}_chg"] = now[key] - before[key]
    return out


@report.finding("C2_3")
def worry_by_risk():
    out = {}
    for risk in RISKS:
        t = distribution(d23, f"worry_{risk}")
        out[f"{risk}_very"], out[f"{risk}_somewhat"] = t[1.0], t[2.0]
        out[f"{risk}_total"] = t[1.0] + t[2.0]
    return out


@report.finding("C2_4")
def traffic_worry_and_experience_by_region():
    """Scatter plot with no printed values; X42-X45 are the values quoted in the text."""
    worry, exp = by_region(d23, "worry_traffic", WORRIED), by_region(d23, "exp_traffic", PERSONAL)
    return {**{f"{k}_worry": v for k, v in worry.items()}, **{f"{k}_experience": v for k, v in exp.items()}}


@report.finding("X27")
def worry_traffic_2023():
    return pct(d23, "worry_traffic", WORRIED)


@report.finding("X28")
def very_worried_traffic():
    return pct(d23, "worry_traffic", [1])


@report.finding("X29")
def somewhat_worried_traffic():
    return pct(d23, "worry_traffic", [2])


@report.finding("X30")
def worry_traffic_increase():
    return pct(d23, "worry_traffic", WORRIED) - pct(d21, "worry_traffic", WORRIED)


@report.finding("X31")
def worry_traffic_2021():
    return pct(d21, "worry_traffic", WORRIED)


for _fid, _risk in (("X32", "weather"), ("X33", "crime"), ("X34", "food"), ("X35", "water"), ("X36", "work")):
    report.finding(_fid)(lambda risk=_risk: pct(d23, f"worry_{risk}", WORRIED))


@report.finding("X37")
def traffic_personal_2023():
    return pct(d23, "exp_traffic", PERSONAL)


@report.finding("X38")
def traffic_know_2023():
    return pct(d23, "exp_traffic", [2])


@report.finding("X39")
def traffic_any_2023():
    return pct(d23, "exp_traffic", [1, 2, 3])


@report.finding("X40")
def traffic_personal_2021():
    return pct(d21, "exp_traffic", PERSONAL)


@report.finding("X41")
def traffic_know_2021():
    return pct(d21, "exp_traffic", [2])


@report.finding("X42")
def latam_worry_traffic():
    return by_region(d23, "worry_traffic", WORRIED)["latam"]


@report.finding("X43")
def latam_experience_traffic():
    return by_region(d23, "exp_traffic", PERSONAL)["latam"]


@report.finding("X44")
def nw_europe_experience_traffic():
    return by_region(d23, "exp_traffic", PERSONAL)["nw_europe"]


@report.finding("X45")
def nw_europe_worry_traffic():
    return by_region(d23, "worry_traffic", WORRIED)["nw_europe"]


@lru_cache(maxsize=None)
def traffic_country_changes():
    """Country % worried about / personally harmed by traffic accidents, 2021 and 2023."""
    t = pd.DataFrame({
        "worry_2021": country(d21, "worry_traffic", WORRIED), "worry_2023": country(d23, "worry_traffic", WORRIED),
        "experience_2021": country(d21, "exp_traffic", PERSONAL), "experience_2023": country(d23, "exp_traffic", PERSONAL),
    }).dropna()  # the 120 countries surveyed in both waves
    for block in ("worry", "experience"):
        t[f"{block}_chg"] = t[f"{block}_2023"] - t[f"{block}_2021"]
        t[f"{block}_chg_rounded"] = rnd(t[f"{block}_2023"]) - rnd(t[f"{block}_2021"])
    return t


@report.finding("C2_5")
def countries_changing_4_points():
    # Changes of 4 points or more between country figures rounded to whole numbers
    # (unrounded changes give 12/15 and 26/29).
    t = traffic_country_changes()
    return {f"{block}_{direction}": int((sign * t[f"{block}_chg_rounded"] >= 4).sum())
            for block in ("experience", "worry") for direction, sign in (("decrease", -1), ("increase", 1))}


@report.finding("X46")
def countries_experience_increase():
    return countries_changing_4_points()["experience_increase"]


@report.finding("X47")
def countries_experience_decrease():
    return countries_changing_4_points()["experience_decrease"]


@report.finding("X48")
def average_margin_of_error():
    # 95% margin of error for a 50% estimate with the Kish design effect of WGT.
    g = d23.groupby("COUNTRY_ISO3")["WGT"]
    n = g.size()
    deff = n * g.apply(lambda w: (w ** 2).sum()) / g.sum() ** 2
    return float((100 * 1.96 * np.sqrt(deff * 0.25 / n)).mean())


C2_6_COUNTRIES = {"worry": ["ITA", "ARE", "FRA", "CHN", "VNM", "SLE", "THA", "HRV", "MDA", "POL"],
                  "experience": ["CHN", "SLE", "PAN", "TUR", "USA", "CMR", "BRA", "THA", "MLI", "ZMB"]}


@report.finding("C2_6")
def biggest_changes():
    t = traffic_country_changes()
    out = {}
    for block, isos in C2_6_COUNTRIES.items():
        for iso in isos:
            out[f"{block}_{iso}_2021"] = t.loc[iso, f"{block}_2021"]
            out[f"{block}_{iso}_2023"] = t.loc[iso, f"{block}_2023"]
            out[f"{block}_{iso}_chg"] = t.loc[iso, f"{block}_chg"]
    return out


for _block in ("worry", "experience"):
    report.finding(f"C2_6_{_block}_up_top5")(lambda b=_block: top(traffic_country_changes()[f"{b}_chg"], 5))
    report.finding(f"C2_6_{_block}_down_top5")(lambda b=_block: top(-traffic_country_changes()[f"{b}_chg"], 5))


@report.finding("X49")
def china_experience_change():
    return traffic_country_changes().loc["CHN", "experience_chg"]


@report.finding("X50")
def sierra_leone_experience_change():
    return traffic_country_changes().loc["SLE", "experience_chg"]


@report.finding("X51")
def sierra_leone_worry_change():
    return traffic_country_changes().loc["SLE", "worry_chg"]


@report.finding("C2_7")
@lru_cache(maxsize=None)
def traffic_worry_by_experience():
    t = distribution(d23, "worry_traffic", by="exp_traffic")
    out = {}
    for key, code in EXPERIENCE.items():
        out[f"{key}_very"], out[f"{key}_somewhat"] = t.loc[code, 1.0], t.loc[code, 2.0]
        out[f"{key}_total"] = t.loc[code, 1.0] + t.loc[code, 2.0]
    return out


for _fid, _key in (("X52", "none_total"), ("X53", "none_very"), ("X54", "none_somewhat"), ("X55", "know_total"),
                   ("X56", "personal_total"), ("X57", "both_total"), ("X58", "personal_very"), ("X59", "know_very"),
                   ("X60", "both_very")):
    report.finding(_fid)(lambda key=_key: traffic_worry_by_experience()[key])


def top_risk_by_experience(code, exp_var):
    r = pct(d23, "top_risk", [code], by=exp_var)
    return {key: r[c] for key, c in EXPERIENCE.items()}


@report.finding("C2_8")
@lru_cache(maxsize=None)
def road_top_risk_by_experience():
    return top_risk_by_experience(ROAD, "exp_traffic")


@report.finding("C2_9")
@lru_cache(maxsize=None)
def weather_top_risk_by_experience():
    return top_risk_by_experience(CLIMATE[2023], "exp_weather")


@report.finding("C2_10")
def crime_top_risk_by_experience():
    return top_risk_by_experience(CRIME, "exp_crime")


for _fid, _key in (("X61", "none"), ("X62", "know"), ("X63", "personal"), ("X64", "both")):
    report.finding(_fid)(lambda key=_key: road_top_risk_by_experience()[key])
for _fid, _key in (("X65", "none"), ("X66", "know"), ("X67", "personal"), ("X68", "both")):
    report.finding(_fid)(lambda key=_key: weather_top_risk_by_experience()[key])


def roads_correlation(outcome, codes):
    # Needs the Gallup World Poll item "In the city or area where you live, are you
    # satisfied or dissatisfied with the roads and highways?" (placeholder name
    # GWP_ROADS_SATISFACTION: 1 = satisfied, 2 = dissatisfied). Pearson
    # correlation of the country figures (Chart 2.11).
    g = merge_gallup(d23[["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", outcome]], ["GWP_ROADS_SATISFACTION"])
    t = pd.DataFrame({"sat": country(g, "GWP_ROADS_SATISFACTION", [1]), "y": country(g, outcome, codes)}).dropna()
    return float(np.corrcoef(t["sat"], t["y"])[0, 1])


@report.finding("X69")
def roads_vs_worry():
    return roads_correlation("worry_traffic", WORRIED)


@report.finding("X70")
def roads_vs_experience():
    return roads_correlation("exp_traffic", PERSONAL)


# --- Chapter 3: climate change ---------------------------------------------------------------


@report.finding("X71")
def disaster_2021():
    return pct(d21, "WP22245", [1])


@report.finding("X72")
def disaster_2023():
    return pct(d23, "WP23344", [1])


def flood_share(df, asked):
    # Flood/heavy rain (WP22247 code 1) as a share of all adults: those not asked the
    # type question (no disaster) count as not experiencing a flood.
    return 100 * df.loc[df["WP22247"].eq(1), "PROJWT"].sum() / df.loc[df[asked].notna(), "PROJWT"].sum()


@report.finding("X73")
def flood_2021():
    return flood_share(d21, "WP22245")


@report.finding("X74")
def flood_2023():
    return flood_share(d23, "WP23344")


@report.finding("C3_2")
@lru_cache(maxsize=None)
def threat_trend():
    out = {}
    for year, df in WAVE.items():
        s = threat_shares(df).iloc[0]
        for key in ("very", "somewhat", "not", "dk"):
            out[f"{key}_{year}"] = s[key]
    return out


for _fid, _key in (("X75", "very_2019"), ("X76", "somewhat_2019"), ("X77", "not_2019"), ("X78", "dk_2019"),
                   ("X80", "very_2021"), ("X81", "very_2023"), ("X83", "somewhat_2021"), ("X84", "somewhat_2023"),
                   ("X89", "not_2023"), ("X90", "dk_2023"), ("X92", "dk_2021")):
    report.finding(_fid)(lambda key=_key: threat_trend()[key])


@report.finding("X79")
def very_decrease():
    t = threat_trend()
    return t["very_2021"] - t["very_2023"]


@report.finding("X82")
def somewhat_increase():
    t = threat_trend()
    return t["somewhat_2023"] - t["somewhat_2021"]


@report.finding("X85")
def combined_increase():
    return pct(d23, "climate", [1, 2]) - pct(d21, "climate", [1, 2])


@report.finding("X86")
def combined_2021():
    return pct(d21, "climate", [1, 2])


@report.finding("X87")
def combined_2019():
    return pct(d19, "climate", [1, 2])


@report.finding("X88")
def not_threat_increase():
    t = threat_trend()
    return t["not_2023"] - t["not_2021"]


@report.finding("X91")
def dk_decrease():
    t = threat_trend()
    return t["dk_2021"] - t["dk_2023"]


@lru_cache(maxsize=None)
def threat_by_region(year):
    t = threat_shares(WAVE[year], by="region")
    t.index = [REGIONS[int(k)] for k in t.index]
    return t


@report.finding("C3_3")
def threat_regions():
    t = threat_by_region(2023)
    out = {}
    for key, row in t.iterrows():
        for part in ("very", "somewhat", "dk", "not"):
            out[f"{key}_{part}"] = row[part]
        out[f"{key}_combined"] = row["combined_rounded"]
    return out


for _fid, _key, _part in (("X93", "south_europe", "combined_rounded"), ("X94", "nw_europe", "combined_rounded"),
                          ("X95", "latam", "very"), ("X98", "north_america", "very"), ("X99", "north_america", "not"),
                          ("X100", "south_asia", "not"), ("X101", "middle_east", "not"), ("X102", "se_asia", "dk"),
                          ("X103", "cw_africa", "dk"), ("X104", "south_africa", "dk")):
    report.finding(_fid)(lambda key=_key, part=_part: threat_by_region(2023).loc[key, part])


@report.finding("X96")
def east_asia_rank():
    t = threat_by_region(2023).sort_values(["combined_rounded", "combined"], ascending=False)
    return list(t.index).index("east_asia") + 1


@report.finding("X97")
def china_somewhat():
    return country(d23, "climate", [2])["CHN"]


@lru_cache(maxsize=None)
def region_change_2019_2023():
    """Table 3.1: differences of the rounded 2019 and 2023 regional figures."""
    a, b = threat_by_region(2019), threat_by_region(2023)
    out = pd.DataFrame({part: rnd(b[part]) - rnd(a[part]) for part in ("very", "somewhat", "not", "dk")})
    out["combined"] = b["combined_rounded"] - a["combined_rounded"]
    return out


@report.finding("T3_1")
def threat_change_by_region():
    t = region_change_2019_2023()
    return {f"{key}_{part}": row[part] for key, row in t.iterrows() for part in ("very", "somewhat", "not", "dk")}


for _fid, _key, _part in (("X105", "north_africa", "very"), ("X110", "south_europe", "very"), ("X111", "south_europe", "somewhat"),
                          ("X112", "anz", "combined"), ("X113", "anz", "not"), ("X114", "anz", "dk"), ("X115", "east_europe", "very")):
    report.finding(_fid)(lambda key=_key, part=_part: region_change_2019_2023().loc[key, part])


@report.finding("X106")
def north_africa_very_2019():
    return threat_by_region(2019).loc["north_africa", "very"]


@report.finding("X107")
def north_africa_very_2023():
    return threat_by_region(2023).loc["north_africa", "very"]


@report.finding("X108")
def south_europe_combined_2019():
    return threat_by_region(2019).loc["south_europe", "combined_rounded"]


@report.finding("X109")
def south_europe_combined_2023():
    return threat_by_region(2023).loc["south_europe", "combined_rounded"]


def china_and_rest(year):
    df = WAVE[year].assign(china=lambda x: np.where(x.COUNTRY_ISO3.eq("CHN"), "china", "rest"))
    return threat_shares(df, by="china")


@report.finding("C3_4")
def china_vs_rest():
    return {f"{who}_{year}": china_and_rest(year).loc[who, "combined_rounded"]
            for who in ("china", "rest") for year in WAVE}


for _fid, _who, _year in (("X116", "china", 2023), ("X117", "china", 2021), ("X118", "china", 2019),
                          ("X119", "rest", 2023), ("X120", "rest", 2019), ("X121", "rest", 2021)):
    report.finding(_fid)(lambda who=_who, year=_year: china_and_rest(year).loc[who, "combined_rounded"])
for _fid, _year in (("X122", 2021), ("X123", 2019), ("X124", 2023)):
    report.finding(_fid)(lambda year=_year: country(WAVE[year], "climate", [98])["CHN"])  # don't know only


@lru_cache(maxsize=None)
def threat_by_country():
    t = threat_shares(d23, by="COUNTRY_ISO3")
    t["dk_only"] = country(d23, "climate", [98])
    t["no_opinion"] = t["dk"]  # don't know or refused
    return t


C3_5_COUNTRIES = ["ESP", "DEU", "AUT", "GEO", "KOR", "ITA", "JPN", "LUX", "GBR", "IRL"]


@report.finding("C3_5")
def most_threatened():
    t = threat_by_country()
    out = {}
    for iso in C3_5_COUNTRIES:
        out[f"{iso}_very"], out[f"{iso}_somewhat"] = t.loc[iso, "very"], t.loc[iso, "somewhat"]
        out[f"{iso}_total"] = t.loc[iso, "combined_rounded"]
    return out


@report.finding("C3_5_top10")
def most_threatened_top10():
    # Ranked on the sum of the rounded figures, ties broken on the unrounded sum.
    t = threat_by_country().sort_values(["combined_rounded", "combined"], ascending=False)
    return "; ".join(sorted(t.index[:10]))


@report.finding("X125")
def spain_overall():
    return threat_by_country().loc["ESP", "combined_rounded"]


C3_6_COUNTRIES = ["SAU", "ETH", "ARE", "ISR", "IRQ", "MLI", "BHR", "JOR", "EST", "IND"]


@report.finding("C3_6")
def not_a_threat_countries():
    t = threat_by_country()
    return {iso: t.loc[iso, "not"] for iso in C3_6_COUNTRIES}


@report.finding("C3_6_top10")
def not_a_threat_top10():
    return top(threat_by_country()["not"], 10)


for _fid, _iso, _part in (("X126", "SAU", "not"), ("X127", "SAU", "very"), ("X129", "ETH", "not"), ("X130", "ETH", "very"),
                          ("X131", "ISR", "not"), ("X134", "MMR", "no_opinion"), ("X135", "LBY", "no_opinion"),
                          ("X136", "SAU", "dk_only")):
    report.finding(_fid)(lambda iso=_iso, part=_part: threat_by_country().loc[iso, part])


@report.finding("X128")
def saudi_ratio():
    t = threat_by_country()
    return t.loc["SAU", "not"] / t.loc["SAU", "very"]


@report.finding("X132")
def israel_not_2019():
    return country(d19, "climate", [3])["ISR"]


@report.finding("X133")
def israel_not_2021():
    return country(d21, "climate", [3])["ISR"]


C3_7_COUNTRIES = ["MMR", "LBY", "MAR", "LAO", "IDN", "NAM", "NGA", "COD", "YEM", "SAU"]


@report.finding("C3_7")
def dont_know_countries():
    t = threat_by_country()
    return {iso: t.loc[iso, "dk_only"] for iso in C3_7_COUNTRIES}


@report.finding("C3_7_top10")
def dont_know_top10():
    return top(threat_by_country()["dk_only"], 10)


# Model (Charts 3.8, 3.9 and pages 19-20). The report fits a multi-level model of
# saying climate change is a very serious threat. Here: a logistic regression
# (statsmodels GLM, binomial, logit link) with country fixed effects in place of
# the country random intercepts, so region and country income level are absorbed.
# Outcome: 1 = very serious threat, 0 = any other answer (DK/refused included).
# Covariates: worry about severe weather (ref. not worried), education (ref.
# primary), male, urbanicity (ref. rural area or farm; the report's "city" is a
# large city), age (years), neighbours care about you (WP22232) and could cover
# basic needs for a month (WP22228). Weights: WGT, rescaled to mean 1.
# Cases with DK/refused on a covariate are dropped. If GALLUP_WP_PATH is set,
# the two Gallup World Poll controls the report names are added: feelings about
# household income (WP2319) and not enough money for food (WP40).
MODEL_FORMULA = ("very ~ C(worry, Treatment('not')) + C(edu, Treatment('primary')) + male"
                 " + C(urban, Treatment('rural')) + Age + C(WP22232) + C(WP22228) + C(COUNTRY_ISO3)")


def model_data():
    m = d23[d23.worry_weather.isin([1, 2, 3]) & d23.Education.isin([1, 2, 3]) & d23.Urbanicity.isin([1, 2, 3, 6])
            & d23.Age.notna() & d23.WP22232.isin([1, 2, 3]) & d23.WP22228.isin([1, 2])].copy()
    m["very"] = m["climate"].eq(1).astype(float)
    m["worry"] = m["worry_weather"].map({1: "very", 2: "somewhat", 3: "not"})
    m["edu"] = m["Education"].map({1: "primary", 2: "secondary", 3: "tertiary"})
    m["male"] = m["Gender"].eq(1).astype(float)
    m["urban"] = m["Urbanicity"].map({1: "rural", 2: "town", 3: "city", 6: "suburb"})
    m["w"] = m["WGT"] / m["WGT"].mean()
    return m


@lru_cache(maxsize=None)
def climate_model():
    m, formula = model_data(), MODEL_FORMULA
    try:
        m = merge_gallup(m, ["WP2319", "WP40"])
        m = m[m.WP2319.isin([1, 2, 3, 4]) & m.WP40.isin([1, 2])].copy()
        m["w"] = m["WGT"] / m["WGT"].mean()
        formula += " + C(WP2319) + C(WP40)"
    except GallupDataRequired:
        pass  # public-data specification
    fit = smf.glm(formula, m, family=sm.families.Binomial(), var_weights=m["w"]).fit(tol=1e-10, tol_criterion="params", maxiter=100)
    odds = np.exp(fit.params)
    return {
        "very": odds["C(worry, Treatment('not'))[T.very]"],
        "somewhat": odds["C(worry, Treatment('not'))[T.somewhat]"],
        "tertiary": odds["C(edu, Treatment('primary'))[T.tertiary]"],
        "secondary": odds["C(edu, Treatment('primary'))[T.secondary]"],
        "male": odds["male"],
        "city": odds["C(urban, Treatment('rural'))[T.city]"],
    }


@report.finding("C3_8")
def odds_worry_weather():
    o = climate_model()
    return {"very": o["very"], "somewhat": o["somewhat"]}


@report.finding("C3_9")
def odds_education():
    o = climate_model()
    return {"tertiary": o["tertiary"], "secondary": o["secondary"]}


for _fid, _key in (("X04", "very"), ("X137", "somewhat"), ("X138", "tertiary"), ("X139", "secondary"),
                   ("X140", "male"), ("X141", "city")):
    report.finding(_fid)(lambda key=_key: climate_model()[key])


def environment_satisfaction(code):
    # Needs the Gallup World Poll item "In this country, are you satisfied or
    # dissatisfied with the efforts to preserve the environment?" (placeholder name
    # GWP_ENVIRONMENT_SATISFACTION: 1 = satisfied, 2 = dissatisfied).
    g = merge_gallup(d23[["WPID_RANDOM", "PROJWT", "climate"]], ["GWP_ENVIRONMENT_SATISFACTION"])
    return pct(g, "GWP_ENVIRONMENT_SATISFACTION", [1], by="climate")[code]


@report.finding("X142")
def env_satisfied_very():
    return environment_satisfaction(1)


@report.finding("X143")
def env_satisfied_not():
    return environment_satisfaction(3)


@report.finding("X144")
def env_satisfied_unsure():
    return environment_satisfaction(98)


@report.finding("X145")
def waste_separated_very():
    return pct(d23, "WP23342", [1], by="climate")[1]


@report.finding("X146")
def waste_separated_not():
    return pct(d23, "WP23342", [1], by="climate")[3]


# --- Chapter 4: global trends ----------------------------------------------------------------

SAFE = {"less": [2], "about": [3], "more": [1]}


@report.finding("C4_1")
def safety_trend():
    return {f"{key}_{year}": pct(df, "safe", codes) for year, df in WAVE.items() for key, codes in SAFE.items()}


@report.finding("X147")
def less_safe_2021():
    return pct(d21, "safe", [2])


@report.finding("X148")
def more_safe_2021():
    return pct(d21, "safe", [1])


@report.finding("X149")
def countries_2021():
    return N_COUNTRIES[2021]


@report.finding("X150")
def countries_2019_in_2023():
    return d19.COUNTRY_ISO3.nunique()  # 2019 countries also surveyed in 2023


@report.finding("C4_2")
def safety_by_region():
    return {f"{key}_{part}": v for part, codes in SAFE.items()
            for key, v in by_region(d23, "safe", codes).items()}


@report.finding("C4_3")
@lru_cache(maxsize=None)
def safety_change_by_region():
    """Scatter plot with no printed values: change 2019-2023 in feeling less and more safe."""
    out = {}
    for part in ("less", "more"):
        now, before = by_region(d23, "safe", SAFE[part]), by_region(d19, "safe", SAFE[part])
        out.update({f"{key}_{part}_chg": now[key] - before[key] for key in now})
    return out


@report.finding("X151")
def east_asia_more_safe():
    return by_region(d23, "safe", [1])["east_asia"]


@report.finding("X152")
def north_america_less_safe_change():
    return safety_change_by_region()["north_america_less_chg"]


@report.finding("X153")
def east_europe_less_safe_change():
    return safety_change_by_region()["east_europe_less_chg"]


@report.finding("X154")
def usa_less_safe_2019():
    return country(d19, "safe", [2])["USA"]


@report.finding("X155")
def usa_less_safe_2023():
    return country(d23, "safe", [2])["USA"]


@report.finding("C4_4")
def worry_trend():
    out = {}
    for risk, (w19, _, _) in RISKS.items():
        for year, df in WAVE.items():
            if year == 2019 and w19 is None:
                continue  # not asked in 2019
            out[f"{risk}_{year}"] = pct(df, f"worry_{risk}", WORRIED)
    return out


@report.finding("C4_5")
def experience_trend():
    return {f"{risk}_{year}": pct(WAVE[year], f"exp_{risk}", PERSONAL) for risk in RISKS for year in (2021, 2023)}


@report.finding("X156")
def traffic_experience_increase():
    return pct(d23, "exp_traffic", PERSONAL) - pct(d21, "exp_traffic", PERSONAL)


@report.finding("X157")
def weather_experience_increase():
    return pct(d23, "exp_weather", PERSONAL) - pct(d21, "exp_weather", PERSONAL)


def index_by_region(df, var):
    r = wmean(df, var, weight=f"w_{var}", by="region")
    return {REGIONS[int(k)]: v for k, v in r.items()}


@report.finding("C4_6")
def worry_index_by_region():
    return {f"{key}_{year}": v for year in (2021, 2023) for key, v in index_by_region(WAVE[year], "worry_idx").items()}


@report.finding("C4_7")
def experience_index_by_region():
    return {f"{key}_{year}": v for year in (2021, 2023) for key, v in index_by_region(WAVE[year], "exp_idx").items()}


@report.finding("C4_8")
def indices_2023():
    worry, exp = index_by_region(d23, "worry_idx"), index_by_region(d23, "exp_idx")
    return {**{f"{k}_experience": v for k, v in exp.items()}, **{f"{k}_worry": v for k, v in worry.items()}}


if __name__ == "__main__":
    sys.exit(report.run())
