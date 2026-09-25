"""Reproduce World Risk Poll 2026: The quiet hazards: How everyday risk shapes daily life.

Run from the repository root:
    python reports/WRP_2025/core_the_quiet_hazards/reproduce.py

The report uses the 2025 data (wave 4) and trends it against 2019, 2021 and
2023. Each function below computes one chart, table or text statement listed
in published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, external_path, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

# --- Variables -------------------------------------------------------------------

# Worry ("could cause you serious harm": 1 very, 2 somewhat, 3 not) and harm
# ("experienced serious harm in the past two years": 1 personally, 2 know
# someone, 3 both, 4 no) items. Same names in 2021-2025; 2025 adds the last three.
WORRY = {"traffic": "WP22213", "severe_weather": "WP20723", "crime": "WP20722", "food": "WP20720",
         "mental_health": "WP20726", "work": "WP22214", "water": "WP20721",
         "prolonged_weather": "WP24174", "wildfires": "WP24173", "air": "WP24175"}
HARM = {"traffic": "WP22446", "severe_weather": "WP22445", "crime": "WP22444", "food": "WP22442",
        "mental_health": "WP22447", "work": "WP22448", "water": "WP22443",
        "prolonged_weather": "WP24177", "wildfires": "WP24176", "air": "WP24178"}
WORRY_2019 = {"severe_weather": "L6D", "crime": "L6C", "food": "L6A", "mental_health": "L6G", "water": "L6B"}
NEW_2025 = ["prolonged_weather", "wildfires", "air"]
WEATHER = ["prolonged_weather", "severe_weather", "wildfires", "air"]
RISK_LABEL = {"traffic": "Traffic/roadside accidents", "severe_weather": "Severe weather events",
              "crime": "Violent crime", "food": "Food you eat", "mental_health": "Mental health issues",
              "work": "Work you do", "water": "Water you drink",
              "prolonged_weather": "Severe prolonged weather events", "wildfires": "Wildfires",
              "air": "The air you breathe"}
WORRIED, HARMED, DK = [1, 2], [1, 3], [98, 99]
WORKFORCE = [1, 2, 3, 4, 5]  # EMP_2010: employed full/part time, self-employed or unemployed

REGION = {1: "east_africa", 2: "cw_africa", 3: "north_africa", 4: "southern_africa", 5: "latam",
          6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia",
          10: "southern_asia", 11: "middle_east", 12: "eastern_europe", 13: "nw_europe",
          14: "southern_europe", 15: "anz"}
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # 9 = not classified: left out
US_REGION = {1: "northeast", 2: "midwest", 3: "south", 4: "west"}  # REGION2_USA
HOURS = {1: "lt15", 2: "h15_29", 3: "h30_39", 4: "h40_49", 5: "h50plus"}  # Gallup EMP_WORK_HOURS

# Top-of-mind risk (WP22331) labels used in Table 1.1; 98 = don't know or refused.
TOP_LABEL = {1: "Road-related accidents", 2: "Other transport", 3: "Crime/violence", 4: "War/terrorism",
             5: "Personal health", 6: "Drugs, alcohol, smoking", 7: "COVID-19", 8: "Mental health",
             9: "Financial", 10: "Economy", 11: "Politics", 12: "Technology", 13: "Water",
             14: "Unsafe food", 15: "Hunger", 16: "Household accidents", 17: "Work", 18: "Pollution",
             19: "Climate change/severe weather", 20: "Non-weather disasters", 21: "Drowning",
             22: "Other", 23: "Nothing", 98: "Don't know"}

BASE = ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "WGT", "GlobalRegion", "CountryIncomeLevel", "EMP_2010"]
d25 = load_wave(2025, BASE + ["Age", "Gender", "Education", "Urbanicity", "INCOME_5", "WP22331", "WP22252",
                              "WP22228", "WP20719", "REGION2_USA", "worry_index_published",
                              *WORRY.values(), *HARM.values()])
# Trends use the countries surveyed in 2025 in every wave (the report's footnote v
# says so for 2019; it also reproduces the 2021 and 2023 figures).
C25 = set(d25.COUNTRY_ISO3)
d23 = load_wave(2023, BASE + ["WP22331", *[WORRY[k] for k in WORRY if k not in NEW_2025],
                              *[HARM[k] for k in HARM if k not in NEW_2025]])
d21 = load_wave(2021, BASE + ["WP22331", *[WORRY[k] for k in WORRY if k not in NEW_2025],
                              *[HARM[k] for k in HARM if k not in NEW_2025]])
d19 = load_wave(2019, BASE + ["L3_A", "L19", *WORRY_2019.values()])
d23, d21, d19 = (d[d.COUNTRY_ISO3.isin(C25)].copy() for d in (d23, d21, d19))
WAVES = {2019: d19, 2021: d21, 2023: d23, 2025: d25}

# --- Derived variables -----------------------------------------------------------

for d in WAVES.values():
    d["region"] = d.GlobalRegion.map(REGION)
    d["income"] = d.CountryIncomeLevel.map(INCOME)
d25["us_region"] = d25.REGION2_USA.map(US_REGION)

# Top-of-mind risk with don't know and refused together (the report's
# "Don't know"; India's 36% in 2025 only matches with both).
d25["top_risk"] = d25.WP22331.replace({99: 98})

# Experience of Harm Index (0-100): share of the 10 harm items answered
# "personally" or "both", for respondents with no don't know or refused
# answer on any of them. This reproduces the country scores in Chart 2.4.
H = d25[list(HARM.values())]
d25["ehi"] = np.where(H.isin(DK).any(axis=1), np.nan, 100 * H.isin(HARMED).sum(axis=1) / 10)
# Worry Index (0-100): LRF's published 2025 index.
d25["wi"] = 100 * d25.worry_index_published
# Number of the four weather-related hazards personally experienced (footnote ii, p. 26).
d25["n_weather"] = d25[[HARM[k] for k in WEATHER]].isin(HARMED).sum(axis=1)

# Current workforce (experience of harm at work) and current employees (the
# worry-about-work question is asked only of the employed).
wf = {y: d[d.EMP_2010.isin(WORKFORCE)] for y, d in WAVES.items()}

# --- Helpers ---------------------------------------------------------------------


def r0(x):
    """Round half up to a whole number, as printed (same rule in the R script)."""
    return np.floor(np.asarray(x, dtype=float) + 0.5 + 1e-9)


def rsum(df, var, codes, by=None):
    """Sum of the rounded % in each of `codes`.

    The report builds 'worried' (very + somewhat) and 'personally experienced'
    (personally + both) by adding the two rounded percentages; this reproduces
    Charts 2.2, 2.3, 3.4, 4.3 and 4.6 exactly (see README).
    """
    t = distribution(df, var, by=by)
    if by is None:
        return float(sum(r0(t.get(c, 0.0)) for c in codes))
    return sum(pd.Series(r0(t[c]), index=t.index) if c in t.columns else 0.0 for c in codes)


def worried(df, key, by=None):
    return rsum(df, WORRY[key], WORRIED, by)


def harmed(y, key, by=None):
    """% personally harmed (rounded sum); work among the current workforce."""
    return rsum(wf[y] if key == "work" else WAVES[y], HARM[key], HARMED, by)


def harmed_df(df, key, by=None):
    base = df[df.EMP_2010.isin(WORKFORCE)] if key == "work" else df
    return rsum(base, HARM[key], HARMED, by)


def top_risk(df, codes, by=None):
    return pct(df, "WP22331", codes, by=by)


def keyed(series, keys):
    """Rename a by-group result's index with readable keys, dropping unknown groups."""
    return {keys[k]: v for k, v in series.items() if k in keys}


def top_three(df):
    """Table 1.1: the three highest-ranked categories on rounded %, tied ones grouped."""
    shares = distribution(df, "top_risk")
    groups = {}
    for code, v in shares.items():
        groups.setdefault(float(r0(v)), []).append((v, TOP_LABEL[int(code)]))
    out = []
    for rounded in sorted(groups, reverse=True)[:3]:
        members = groups[rounded]
        out.append((max(v for v, _ in members), ", ".join(sorted(label for _, label in members))))
    return out


def life_evaluation(df):
    """Gallup Life Evaluation Index groups from the Cantril ladder (WP16 now, WP18 in five years).

    1 thriving (now 7+ and future 8+), 3 suffering (both 4 or below),
    2 struggling (everyone else with valid answers).
    """
    g = merge_gallup(df, ["WP16", "WP18"])
    now, fut = g.WP16.where(g.WP16 <= 10), g.WP18.where(g.WP18 <= 10)
    g["life_eval"] = np.select([(now >= 7) & (fut >= 8), (now <= 4) & (fut <= 4), now.notna() & fut.notna()],
                               [1.0, 3.0, 2.0], default=np.nan)
    return g


def hours(df):
    """Gallup EMP_WORK_HOURS: 1 <15, 2 15-29, 3 30-39, 4 40-49, 5 50+ hours a week (98 no answer)."""
    g = merge_gallup(df, ["EMP_WORK_HOURS"])
    g["hours"] = g.EMP_WORK_HOURS.where(g.EMP_WORK_HOURS <= 5)
    return g


def external(name):
    """A snapshot in reports/external/ (see README); missing files give EXTERNAL_ONLY."""
    return pd.read_csv(external_path(f"core_the_quiet_hazards__{name}.csv"))


LE = {1: "thriving", 2: "struggling", 3: "suffering"}

# --- Executive summary and front matter ------------------------------------------


@report.finding("X01")
def interviews():
    return len(d25)


@report.finding("X02")
def countries():
    return d25.COUNTRY_ISO3.nunique()


@report.finding("X03")
def work_harm_2025():
    return harmed(2025, "work")


@report.finding("X04")
def work_harm_2023():
    return harmed(2023, "work")


@report.finding("X05")
def work_harm_2021():
    return harmed(2021, "work")


@report.finding("X06")
def food_harm():
    return harmed(2025, "food")


@report.finding("X07")
def water_harm():
    return harmed(2025, "water")


@report.finding("X08")
def top_road():
    return top_risk(d25, [1])


@report.finding("X09")
def top_health():
    return top_risk(d25, [5])


@report.finding("X10")
def top_crime():
    return top_risk(d25, [3])


@report.finding("X11")
def n_regions():
    return d25.GlobalRegion.nunique()


def table_1_1():
    return {REGION[r]: top_three(g) for r, g in d25.groupby("GlobalRegion")}


@report.finding("X12")
def distinct_top_three():
    return len({tuple(label for _, label in t) for t in table_1_1().values()})


@report.finding("X13")
def prolonged_harm():
    return harmed(2025, "prolonged_weather")


@report.finding("X14")
def severe_weather_harm():
    return harmed(2025, "severe_weather")


@report.finding("X15")
def air_harm():
    return harmed(2025, "air")


@report.finding("X16")
def wildfire_harm():
    return harmed(2025, "wildfires")


@report.finding("X17")
def air_not_worried():
    return pct(d25, WORRY["air"], [3])


def top10_harm(key):
    """The 10 countries with the highest % personally harmed (ISO3 -> unrounded %)."""
    return pct(d25, HARM[key], HARMED, by="COUNTRY_ISO3").sort_values(ascending=False).head(10)


@report.finding("X18")
def weather_overlap():
    return len(set(top10_harm("severe_weather").index) & set(top10_harm("prolonged_weather").index))


# --- Chapter 1: Top risks to safety -----------------------------------------------


@report.finding("X19")
def road_change():
    return float(r0(top_risk(d25, [1])) - r0(top_risk(d23, [1])))


@report.finding("X20")
def dk_2025():
    return top_risk(d25, DK)


@report.finding("X21")
def dk_2023():
    return top_risk(d23, DK)


@report.finding("X22")
def dk_2021():
    return top_risk(d21, DK)


@report.finding("X23")
def dk_change():
    return float(r0(top_risk(d25, DK)) - r0(top_risk(d23, DK)))


@report.finding("X24")
def india_dk_2021():
    return top_risk(d21[d21.COUNTRY_ISO3 == "IND"], DK)


@report.finding("X25")
def india_dk_2023():
    return top_risk(d23[d23.COUNTRY_ISO3 == "IND"], DK)


@report.finding("X26")
def india_dk_2025():
    return top_risk(d25[d25.COUNTRY_ISO3 == "IND"], DK)


@report.finding("X27")
def road_2023():
    return top_risk(d23, [1])


@report.finding("X28")
def road_2021():
    return top_risk(d21, [1])


@report.finding("X29")
def road_2019():
    return pct(d19, "L3_A", [1])  # 2019 first answer; code 1 = road-related accidents


@report.finding("X30")
def top_economy():
    return top_risk(d25, [10])


@report.finding("X31")
def top_climate():
    return top_risk(d25, [19])


@report.finding("X32")
def top_financial():
    return top_risk(d25, [9])


@report.finding("X33")
def top_war():
    return top_risk(d25, [4])


@report.finding("X34")
def top_refused():
    return top_risk(d25, [99])


@report.finding("X35")
def top_dont_know():
    return top_risk(d25, [98])


@report.finding("X36")
def dk_unable_to_protect():
    return top_risk(d25[d25.WP22252 == 2], DK)


@report.finding("X37")
def dk_able_to_protect():
    return top_risk(d25[d25.WP22252 == 1], DK)


def road_by_region(y):
    return keyed(top_risk(WAVES[y], [1], by="GlobalRegion"), REGION)


@report.finding("X38")
def road_anz():
    return road_by_region(2025)["anz"]


@report.finding("X39")
def road_northern_america():
    return road_by_region(2025)["northern_america"]


def road_region_change(region):
    return float(r0(road_by_region(2025)[region]) - r0(road_by_region(2023)[region]))


@report.finding("X40")
def road_change_northern_america():
    return road_region_change("northern_america")


@report.finding("X41")
def road_change_eastern_asia():
    return road_region_change("eastern_asia")


@report.finding("X42")
def road_change_southern_asia():
    return road_region_change("southern_asia")


@report.finding("X43")
def road_in_top_three():
    return sum(any("Road-related" in label for _, label in t) for t in table_1_1().values())


@report.finding("X44")
def road_top():
    return sum(t[0][1] == "Road-related accidents" for t in table_1_1().values())


@report.finding("X45")
def health_second():
    return sum("Personal health" in t[1][1] for t in table_1_1().values())


def region_top_risk(region, codes):
    return keyed(top_risk(d25, codes, by="GlobalRegion"), REGION)[region]


@report.finding("X46")
def eastern_asia_environment():
    return region_top_risk("eastern_asia", [19])


@report.finding("X47")
def eastern_europe_war():
    return region_top_risk("eastern_europe", [4])


@report.finding("X48")
def anz_mental_health():
    return region_top_risk("anz", [8])


@report.finding("X49")
def northern_america_politics():
    return region_top_risk("northern_america", [11])


CHART_1_1 = {"dk": DK, "road": [1], "health": [5], "crime": [3], "economy": [10], "climate": [19],
             "nothing": [23], "financial": [9], "other": [22], "war": [4], "work": [17],
             "technology": [12], "environment": [18]}


@report.finding("C1_1")
def top_risks_2025():
    out = {}
    for key, codes in CHART_1_1.items():
        out[key] = top_risk(d25, codes)
        out[f"{key}_change"] = float(r0(out[key]) - r0(top_risk(d23, codes)))  # rounded, as printed
    return out


@report.finding("C1_2")
def road_by_region_trend():
    return {f"{reg}_{y}": v for y in (2021, 2023, 2025) for reg, v in road_by_region(y).items()}


@report.finding("T1_1")
def top_three_by_region():
    return {f"{reg}_{i}": v for reg, t in table_1_1().items() for i, (v, _) in enumerate(t, 1)}


@report.finding("T1_1")
def top_three_labels():
    return {f"{reg}_{i}_risk": label for reg, t in table_1_1().items() for i, (_, label) in enumerate(t, 1)}


@report.finding("X50")
def crime_change():
    return float(r0(top_risk(d25, [3])) - r0(top_risk(d23, [3])))


def crime_latam(y):
    return keyed(top_risk(WAVES[y], [3], by="GlobalRegion"), REGION)["latam"]


@report.finding("X51")
def crime_latam_2025():
    return crime_latam(2025)


@report.finding("X52")
def crime_latam_2023():
    return crime_latam(2023)


@report.finding("X53")
def crime_latam_change():
    return float(r0(crime_latam(2025)) - r0(crime_latam(2023)))


@report.finding("C1_3")
def crime_trend():
    out = {}
    for y in (2021, 2023, 2025):
        out[f"latam_{y}"] = crime_latam(y)
        out[f"global_{y}"] = top_risk(WAVES[y], [3])
    return out


def crime_declines():
    """Table 1.2: the 13 largest national falls in % naming crime and violence, 2023-2025."""
    a = top_risk(d23, [3], by="COUNTRY_ISO3")
    b = top_risk(d25, [3], by="COUNTRY_ISO3")
    t = pd.DataFrame({"y2023": a, "y2025": b}).dropna()
    t["gap"] = t.y2023 - t.y2025
    return t.sort_values("gap", ascending=False).head(13)


@report.finding("T1_2")
def crime_declines_table():
    out = {}
    for iso, row in crime_declines().iterrows():
        out[f"{iso}_2023"] = row.y2023
        out[f"{iso}_2025"] = row.y2025
        out[f"{iso}_gap"] = float(r0(row.y2023) - r0(row.y2025))  # rounded figures, as printed
    return out


@report.finding("T1_2")
def crime_declines_countries():
    return {"countries": " ".join(sorted(crime_declines().index))}


def region_of(d):
    return d.groupby("COUNTRY_ISO3").GlobalRegion.first()


@report.finding("X54")
def declines_in_latam():
    return int((region_of(d25)[crime_declines().index] == 5).sum())


def latam_in_top10_crime(d):
    top = top_risk(d, [3], by="COUNTRY_ISO3").sort_values(ascending=False).head(10)
    return int((region_of(d)[top.index] == 5).sum())


@report.finding("X55")
def crime_top10_latam_2025():
    return latam_in_top10_crime(d25)


@report.finding("X56")
def crime_top10_latam_2023():
    return latam_in_top10_crime(d23)


@report.finding("X57")
def crime_latam_countries():
    return top_risk(d25, [3], by="COUNTRY_ISO3")[["ECU", "CHL", "CRI", "MEX", "PER", "COL", "ARG"]]


CHART_1_4 = {"road": [1], "health": [5], "economy": [9, 10]}  # economy includes financial


@report.finding("C1_4")
def top_risk_by_wellbeing():
    g = life_evaluation(d25)
    out = {}
    for risk, codes in CHART_1_4.items():
        r = pct(g, "WP22331", codes, by=["CountryIncomeLevel", "life_eval"])
        for (inc, le), v in r.items():
            if inc in INCOME and le in LE:
                out[f"{INCOME[inc]}_{risk}_{LE[le]}"] = v
    return out


@report.finding("X58")
def economy_lower_middle_suffering():
    g = life_evaluation(d25)
    return pct(g[(g.CountryIncomeLevel == 2) & (g.life_eval == 3)], "WP22331", [9, 10])


# --- Chapter 2: Trends in everyday risk --------------------------------------------


@report.finding("X59")
def risks_half_worried():
    return sum(worried(d25, k) >= 50 for k in WORRY)


@report.finding("X60")
def work_worry():
    return worried(d25, "work")


@report.finding("C2_1")
def worry_vs_experience():
    """Chart 2.1 is a scatter with no printed values: worry and personal harm for the 10 risks."""
    return {**{f"worry_{k}": worried(d25, k) for k in WORRY}, **{f"harm_{k}": harmed(2025, k) for k in HARM}}


def ratios():
    """Table 2.1: % worried / % personally harmed, unrounded, by region."""
    t = pd.DataFrame({k: pct(d25, WORRY[k], WORRIED, by="GlobalRegion")
                      / pct(wf[2025] if k == "work" else d25, HARM[k], HARMED, by="GlobalRegion") for k in WORRY})
    return t.rename(index=REGION)


@report.finding("T2_1")
def ratio_table():
    out = {}
    for reg, row in ratios().iterrows():
        out[f"{reg}_max"] = row.max()
        out[f"{reg}_min"] = row.min()
    return out


@report.finding("T2_1")
def ratio_table_risks():
    out = {}
    for reg, row in ratios().iterrows():
        out[f"{reg}_max_risk"] = RISK_LABEL[row.idxmax()]
        out[f"{reg}_min_risk"] = RISK_LABEL[row.idxmin()]
    return out


@report.finding("X61")
def wildfire_biggest_ratio():
    return int((ratios().idxmax(axis=1) == "wildfires").sum())


@report.finding("X62")
def worry_stable():
    return max(abs(pct(d25, WORRY[k], WORRIED) - pct(d23, WORRY[k], WORRIED)) for k in ("traffic", "crime", "food", "work"))


def worry_trend(key, y):
    if y == 2019:
        return rsum(d19, WORRY_2019[key], WORRIED) if key in WORRY_2019 else None
    if y < 2025 and key in NEW_2025:
        return None
    return worried(WAVES[y], key)


@report.finding("X63")
def severe_weather_worry_change():
    return worry_trend("severe_weather", 2025) - worry_trend("severe_weather", 2023)


@report.finding("X64")
def water_worry_change():
    return worry_trend("water", 2025) - worry_trend("water", 2023)


@report.finding("X65")
def prolonged_worry():
    return worried(d25, "prolonged_weather")


@report.finding("X66")
def prolonged_worry_rank():
    w = {k: worried(d25, k) for k in WORRY}
    return 1 + sum(v > w["prolonged_weather"] for v in w.values())


@report.finding("X67")
def wildfire_worry():
    return worried(d25, "wildfires")


@report.finding("X68")
def air_worry():
    return worried(d25, "air")


@report.finding("X69")
def severe_weather_worry():
    return worried(d25, "severe_weather")


@report.finding("C2_2")
def worry_trends():
    out = {}
    for key in WORRY:
        for y in (2019, 2021, 2023, 2025):
            v = worry_trend(key, y)
            if v is not None:
                out[f"{key}_{y}"] = v
    return out


@report.finding("X70")
def severe_weather_harm_2023():
    return harmed(2023, "severe_weather")


@report.finding("X71")
def severe_weather_harm_2021():
    return harmed(2021, "severe_weather")


@report.finding("X72")
def traffic_harm():
    return harmed(2025, "traffic")


@report.finding("X73")
def crime_harm():
    return harmed(2025, "crime")


@report.finding("C2_3")
def harm_trends():
    return {f"{k}_{y}": harmed(y, k) for k in HARM for y in (2021, 2023, 2025) if y == 2025 or k not in NEW_2025}


def country_ehi():
    return wmean(d25, "ehi", by="COUNTRY_ISO3")


@report.finding("X74")
def ehi_20_plus():
    return int((country_ehi() >= 20).sum())


@report.finding("X75")
def ehi_20_plus_lowest():
    e = country_ehi()
    return e[e >= 20].min()


@report.finding("X76")
def ehi_global():
    return wmean(d25, "ehi", weight="WGT")  # within-country weight; PROJWT gives 13.9


@report.finding("C2_4")
def worry_vs_experience_index():
    """Chart 2.4 is a scatter with no printed values: country Worry and Experience of Harm Index."""
    wi, e = wmean(d25, "wi", by="COUNTRY_ISO3"), country_ehi()
    return {**{f"{c}_worry": v for c, v in wi.items()}, **{f"{c}_experience": v for c, v in e.items()}}


SIX = ["CHN", "IND", "PHL", "TCD", "COM", "SOM"]


def six_profiles():
    """Chart 2.5: % personally harmed (rounded sum) for each risk in the six countries."""
    d = d25[d25.COUNTRY_ISO3.isin(SIX)]
    return pd.DataFrame({k: harmed_df(d, k, by="COUNTRY_ISO3") for k in HARM})


@report.finding("C2_5")
def six_countries():
    p = six_profiles()
    glob = {k: harmed(2025, k) for k in ("severe_weather", "prolonged_weather")}
    return {"CHN_severe_weather": p.loc["CHN", "severe_weather"], "CHN_work": p.loc["CHN", "work"],
            "IND_min": p.loc["IND"].min(), "IND_max": p.loc["IND"].max(),
            "PHL_severe_weather": p.loc["PHL", "severe_weather"],
            "PHL_prolonged_weather": p.loc["PHL", "prolonged_weather"],
            "TCD_severe_weather": p.loc["TCD", "severe_weather"],
            "COM_mental_health": p.loc["COM", "mental_health"],
            "COM_prolonged_weather": p.loc["COM", "prolonged_weather"], "SOM_work": p.loc["SOM", "work"],
            "PHL_vs_global": min(p.loc["PHL", k] / glob[k] for k in glob)}


@report.finding("C2_5")
def six_countries_highest():
    p = six_profiles()
    return {"highest_work": p["work"].idxmax(), "highest_mental": p["mental_health"].idxmax()}


def know_someone(key):
    return pct(wf[2025] if key == "work" else d25, HARM[key], [2])


@report.finding("C2_6")
def personal_and_social_harm():
    out = {}
    for k in HARM:
        out[f"{k}_personal"] = harmed(2025, k)
        out[f"{k}_know"] = know_someone(k)
    return out


@report.finding("X77")
def know_prolonged():
    return know_someone("prolonged_weather")


@report.finding("X78")
def know_traffic():
    return know_someone("traffic")


@report.finding("X79")
def know_vs_personal_traffic():
    return float(r0(know_someone("traffic"))) / harmed(2025, "traffic")


@report.finding("X80")
def ehi_lower_middle():
    return wmean(d25[d25.CountryIncomeLevel == 2], "ehi")


@report.finding("C2_7")
def indices_by_wellbeing():
    g = life_evaluation(d25)
    e = wmean(g, "ehi", by=["CountryIncomeLevel", "life_eval"])
    w = wmean(g, "wi", by=["CountryIncomeLevel", "life_eval"])
    out = {}
    for (inc, le) in e.index:
        if inc in INCOME and le in LE:
            key = f"{INCOME[inc]}_{LE[le]}"
            out[f"{key}_experience"] = e[(inc, le)]
            out[f"{key}_worry"] = w[(inc, le)]
            out[f"{key}_gap"] = float(r0(w[(inc, le)]) - r0(e[(inc, le)]))
    return out


# --- Chapter 3: Workplace harm ----------------------------------------------------


@report.finding("X81")
def workers_harmed_millions():
    w = wf[2025]
    return (w.PROJWT * w.WP22448.isin(HARMED)).sum() / 1e6


@report.finding("C3_1")
def work_harm_trend():
    out = {"2019": pct(d19, "L19", [1])}  # 2019: ever seriously injured while working (asked of the employed)
    out.update({str(y): harmed(y, "work") for y in (2021, 2023, 2025)})
    return out


def work_harm_by(var, keys):
    return keyed(harmed(2025, "work", by=var), keys)


@report.finding("C3_2")
def work_harm_education_resilience():
    return {**work_harm_by("Education", {1: "primary", 2: "secondary", 3: "tertiary"}),
            **work_harm_by("WP22228", {1: "lt_month", 2: "month_plus"})}


@report.finding("X82")
def work_harm_lt_month():
    return work_harm_by("WP22228", {1: "x"})["x"]


@report.finding("X83")
def work_harm_month_plus():
    return work_harm_by("WP22228", {2: "x"})["x"]


@report.finding("X84")
def work_harm_primary():
    return work_harm_by("Education", {1: "x"})["x"]


@report.finding("X85")
def work_harm_secondary():
    return work_harm_by("Education", {2: "x"})["x"]


@report.finding("X86")
def work_harm_tertiary():
    return work_harm_by("Education", {3: "x"})["x"]


def work_by_income():
    e = keyed(harmed(2025, "work", by="CountryIncomeLevel"), INCOME)
    w = keyed(worried(d25, "work", by="CountryIncomeLevel"), INCOME)
    return e, w


@report.finding("C3_3")
def work_income():
    e, w = work_by_income()
    out = {}
    for inc in INCOME.values():
        out[f"{inc}_experience"], out[f"{inc}_worry"], out[f"{inc}_gap"] = e[inc], w[inc], w[inc] - e[inc]
    return out


def work_income_value(inc, what):
    e, w = work_by_income()
    return {"experience": e[inc], "worry": w[inc], "gap": w[inc] - e[inc]}[what]


for _fid, _inc, _what in [("X87", "low", "experience"), ("X88", "low", "worry"), ("X89", "low", "gap"),
                          ("X90", "lower_middle", "experience"), ("X91", "upper_middle", "experience"),
                          ("X92", "lower_middle", "worry"), ("X93", "upper_middle", "worry"),
                          ("X94", "high", "experience"), ("X95", "high", "worry"), ("X96", "high", "gap")]:
    report.finding(_fid)(lambda inc=_inc, what=_what: work_income_value(inc, what))


@report.finding("X97")
def out_of_workforce():
    return pct(d25, "EMP_2010", [6])


@report.finding("X98")
def in_workforce():
    return pct(d25, "EMP_2010", WORKFORCE)


def work_harm_region(y):
    return keyed(harmed(y, "work", by="GlobalRegion"), REGION)


report.finding("X99")(lambda: work_harm_region(2023)["eastern_asia"])
report.finding("X100")(lambda: work_harm_region(2025)["eastern_asia"])
report.finding("X101")(lambda: work_harm_region(2023)["nw_europe"])
report.finding("X102")(lambda: work_harm_region(2025)["nw_europe"])


@report.finding("X103")
def regions_more_harm_than_2021():
    a, b = work_harm_region(2021), work_harm_region(2025)
    return sum(b[r] > a[r] for r in b)


@report.finding("X104")
def work_harm_declines():
    a, b = work_harm_region(2023), work_harm_region(2025)
    return {r: b[r] - a[r] for r in ("southern_asia", "southeastern_asia", "southern_africa", "middle_east", "anz", "northern_america")}


@report.finding("C3_4")
def work_harm_by_region():
    return {f"{reg}_{y}": v for y in (2021, 2023, 2025) for reg, v in work_harm_region(y).items()}


def hours_by(df, what, by="hours"):
    """% harmed (workforce) or worried (employees) by hours band, as rounded sums."""
    if what == "experience":
        return rsum(df[df.EMP_2010.isin(WORKFORCE)], "WP22448", HARMED, by=by)
    return rsum(df, "WP22214", WORRIED, by=by)


@report.finding("C3_5")
def work_by_hours():
    g = hours(d25)
    out = {}
    for scope, df in (("global", g), ("high", g[g.CountryIncomeLevel == 4])):
        for what in ("experience", "worry"):
            for h, v in hours_by(df, what).items():
                out[f"{scope}_{what}_{HOURS[h]}"] = v
    return out


def high_income_hours(what):
    g = hours(d25)
    return hours_by(g[g.CountryIncomeLevel == 4], what)


report.finding("X105")(lambda: high_income_hours("worry")[[1, 2, 3, 4]].min())
report.finding("X106")(lambda: high_income_hours("worry")[[1, 2, 3, 4]].max())
report.finding("X107")(lambda: high_income_hours("worry")[5])
report.finding("X108")(lambda: high_income_hours("experience")[5])


@report.finding("X109")
def hours_distribution():
    g = hours(d25)
    w = g[g.EMP_2010.isin(WORKFORCE)]
    out = {HOURS[h]: pct(w, "hours", [h]) for h in (4, 5, 3, 2, 1)}
    out["h40plus"] = rsum(w, "hours", [4, 5])
    return out


@report.finding("X110")
def top_quintile_by_hours():
    g = hours(d25)
    w = g[(g.CountryIncomeLevel == 4) & g.EMP_2010.isin(WORKFORCE)]
    r = pct(w, "INCOME_5", [5], by="hours")
    return {HOURS[h]: r[h] for h in (5, 3, 1)}


def work_worry_models():
    """Logistic regressions of worry about harm at work, employees in high-income countries.

    Unweighted. Hours band reference 40-49; covariates as listed in the report.
    Model 2 adds worry about mental health issues (reference: not worried).
    """
    g = hours(d25)
    m = g[(g.CountryIncomeLevel == 4) & g.WP22214.isin([1, 2, 3])].copy()
    m["worried"] = m.WP22214.isin(WORRIED).astype(float)
    for v in ("Education", "Urbanicity"):
        m[v] = m[v].where(m[v] != 9)
    m["Gender"] = m.Gender.where(m.Gender.isin([1, 2]))
    m["mental"] = m.WP20726.where(m.WP20726.isin([1, 2, 3]))
    base = ("worried ~ C(hours, Treatment(4)) + Age + C(Gender) + C(Education) + C(INCOME_5)"
            " + C(EMP_2010) + C(Urbanicity)")
    fam = sm.families.Binomial()
    m1 = smf.glm(base, data=m.dropna(subset=["hours", "Age", "Gender", "Education", "INCOME_5", "Urbanicity"]),
                 family=fam).fit()
    m2 = smf.glm(base + " + C(mental, Treatment(3))",
                 data=m.dropna(subset=["hours", "Age", "Gender", "Education", "INCOME_5", "Urbanicity", "mental"]),
                 family=fam).fit()
    return m1.params, m2.params


def odds_pct(b):
    return 100 * (np.exp(b) - 1)


report.finding("X111")(lambda: odds_pct(work_worry_models()[0]["C(hours, Treatment(4))[T.5.0]"]))
report.finding("X112")(lambda: odds_pct(-work_worry_models()[0]["C(hours, Treatment(4))[T.1.0]"]))
report.finding("X113")(lambda: odds_pct(work_worry_models()[1]["C(mental, Treatment(3))[T.2.0]"]))
report.finding("X114")(lambda: odds_pct(work_worry_models()[1]["C(mental, Treatment(3))[T.1.0]"]))


def hi_worry_wellbeing_hours():
    g = life_evaluation(hours(d25))
    g = g[g.CountryIncomeLevel == 4].copy()
    g["thriving"] = np.where(g.life_eval == 1, 1.0, np.where(g.life_eval.isin([2, 3]), 2.0, np.nan))
    return rsum(g, "WP22214", WORRIED, by=["thriving", "hours"])


@report.finding("C3_6")
def worry_wellbeing_hours():
    r = hi_worry_wellbeing_hours()
    return {f"{'thriving' if t == 1 else 'not_thriving'}_{HOURS[h]}": v for (t, h), v in r.items()}


report.finding("X115")(lambda: hi_worry_wellbeing_hours()[(2.0, 5.0)])
report.finding("X116")(lambda: hi_worry_wellbeing_hours()[(1.0, 5.0)])

# --- Chapter 4: Weather-related risks ----------------------------------------------


@report.finding("C4_1")
def weather_worry_levels():
    return {f"{k}_{lvl}": pct(d25, WORRY[k], [code]) for k in WEATHER
            for lvl, code in (("very", 1), ("somewhat", 2), ("not", 3))}


@report.finding("X117")
def weather_hazard_count():
    out = {"any": pct(d25, "n_weather", [1, 2, 3, 4])}
    out.update({name: pct(d25, "n_weather", [n]) for n, name in ((1, "one"), (2, "two"), (3, "three"), (4, "four"))})
    return out


PROXIMITY = {4: "no", 2: "know", 1: "personal", 3: "both"}  # harm answer groups


def worry_by_proximity(key, level):
    """% very (1) or somewhat (2) worried by harm answer; worry DK stays in the base."""
    r = pct(d25, WORRY[key], [level], by=HARM[key])
    return {PROXIMITY[g]: v for g, v in r.items() if g in PROXIMITY}


@report.finding("C4_2")
def worry_and_proximity():
    return {f"{k}_{g}_{lvl}": v for k in WEATHER for lvl, code in (("very", 1), ("somewhat", 2))
            for g, v in worry_by_proximity(k, code).items()}


report.finding("X118")(lambda: worry_by_proximity("wildfires", 1)["personal"])
report.finding("X119")(lambda: worry_by_proximity("prolonged_weather", 1)["personal"])
report.finding("X120")(lambda: worry_by_proximity("wildfires", 2)["personal"])
report.finding("X121")(lambda: worry_by_proximity("prolonged_weather", 2)["personal"])
report.finding("X122")(lambda: worry_by_proximity("wildfires", 1)["both"])
report.finding("X123")(lambda: worry_by_proximity("prolonged_weather", 1)["both"])


@report.finding("C4_3")
def weather_harm_by_income():
    return {f"{k}_{inc}": v for k in WEATHER for inc, v in keyed(harmed(2025, k, by="CountryIncomeLevel"), INCOME).items()}


@report.finding("X124")
def weather_harm_high_income():
    return {k: keyed(harmed(2025, k, by="CountryIncomeLevel"), INCOME)["high"] for k in WEATHER}


def wildfire_countries():
    """Countries with at least 2% of land burned in 2025 (GWIS snapshot), with harm and worry."""
    burned = external("gwis_burned_area").set_index("iso3").burned_pct
    t = pd.DataFrame({"harm": pct(d25, HARM["wildfires"], HARMED, by="COUNTRY_ISO3"),
                      "worry": pct(d25, WORRY["wildfires"], WORRIED, by="COUNTRY_ISO3")})
    t["burned"] = burned.reindex(t.index)
    return t[t.burned >= 2]


@report.finding("X125")
def burned_countries():
    return len(wildfire_countries())


@report.finding("X126")
def wildfire_correlation():
    t = wildfire_countries()
    return t.harm.corr(t.worry)


@report.finding("C4_4")
def wildfire_scatter():
    """Chart 4.4 is a scatter with no printed values."""
    t = wildfire_countries()
    return {**{f"{c}_harm": v for c, v in t.harm.items()}, **{f"{c}_worry": v for c, v in t.worry.items()}}


def wildfire_worry_by_country():
    return worried(d25, "wildfires", by="COUNTRY_ISO3")


@report.finding("C4_5")
def most_worried_wildfires():
    rs = wildfire_worry_by_country()
    top = rs[rs >= rs.sort_values(ascending=False).iloc[12]].index  # top 13, ties kept
    t = distribution(d25[d25.COUNTRY_ISO3.isin(top)], WORRY["wildfires"], by="COUNTRY_ISO3")
    out = {}
    for c in top:
        out[f"{c}_very"], out[f"{c}_somewhat"] = t.loc[c, 1], t.loc[c, 2]
    return out


@report.finding("C4_5")
def most_worried_wildfires_countries():
    rs = wildfire_worry_by_country()
    return {"countries": " ".join(sorted(rs[rs >= rs.sort_values(ascending=False).iloc[12]].index))}


@report.finding("X127")
def wildfire_worry_top10():
    return wildfire_worry_by_country()[["GRC", "PRT", "MNG", "CYP", "TUR", "MWI", "KOR", "BRA", "PHL", "BOL"]]


@report.finding("X128")
def us_wildfire_worry():
    return wildfire_worry_by_country()["USA"]


@report.finding("X129")
def us_wildfire_rank():
    rs = wildfire_worry_by_country()
    return int((rs >= rs["USA"]).sum())  # last place among countries tied on the rounded figure


def us_worry(key):
    return keyed(worried(d25[d25.COUNTRY_ISO3 == "USA"], key, by="us_region"), {v: v for v in US_REGION.values()})


report.finding("X130")(lambda: us_worry("wildfires")["west"])
report.finding("X131")(lambda: us_worry("wildfires")["northeast"])
report.finding("X132")(lambda: us_worry("wildfires")["south"])
report.finding("X133")(lambda: us_worry("wildfires")["midwest"])


@report.finding("X134")
def us_west_ratio():
    w = us_worry("wildfires")
    return w["west"] / max(v for r, v in w.items() if r != "west")


@report.finding("C4_6")
def us_regional_worry():
    return {f"{k}_{r}": v for k in WEATHER for r, v in us_worry(k).items()}


@report.finding("C4_7")
def air_satisfaction_scatter():
    """Chart 4.7 is a scatter with no printed values. Needs the Gallup item
    'In the city or area where you live, are you satisfied or dissatisfied with
    the quality of air?' (placeholder name; 1 = satisfied)."""
    g = merge_gallup(d25, ["GWP_AIR_QUALITY_SATISFACTION"])
    s = pct(g, "GWP_AIR_QUALITY_SATISFACTION", [1], by="COUNTRY_ISO3")
    w = pct(g, WORRY["air"], WORRIED, by="COUNTRY_ISO3")
    return {**{f"{c}_satisfied": v for c, v in s.items()}, **{f"{c}_worry": v for c, v in w.items()}}


DEGURBA = {1: "cities", 2: "towns", 3: "rural"}  # placeholder Gallup degree-of-urbanisation item


def air_worry_by_degurba(by):
    g = merge_gallup(d25, ["GWP_DEGURBA"])
    return rsum(g, WORRY["air"], WORRIED, by=[by, "GWP_DEGURBA"])


@report.finding("C4_8")
def air_worry_urbanicity():
    r = air_worry_by_degurba("GlobalRegion")
    return {f"{REGION[reg]}_{DEGURBA[u]}": v for (reg, u), v in r.items() if reg in REGION and u in DEGURBA}


def urban_rural_gaps():
    t = air_worry_by_degurba("COUNTRY_ISO3").unstack()
    t["gap"] = t[1] - t[3]
    t["iso"] = t.index
    return t.sort_values(["gap", "iso"], ascending=[False, True]).head(10)  # ties: ISO3 order


BALKANS = ["ALB", "BIH", "BGR", "HRV", "GRC", "XKX", "MNE", "MKD", "SRB", "SVN"]
report.finding("X135")(lambda: int((region_of(d25)[urban_rural_gaps().index] == 7).sum()))
report.finding("X136")(lambda: int(urban_rural_gaps().index.isin(BALKANS).sum()))


@report.finding("T4_1")
def urban_rural_table():
    return {f"{c}_{DEGURBA[u]}": row[u] for c, row in urban_rural_gaps().iterrows() for u in DEGURBA}


def pm25_bands():
    """Chart 4.9: country-level harm and worry by how far PM2.5 exceeds the WHO guideline (5 ug/m3)."""
    pm = external("worldbank_pm25").set_index("iso3").value
    t = pd.DataFrame({"experience": pct(d25, HARM["air"], HARMED, by="COUNTRY_ISO3"),
                      "worry": pct(d25, WORRY["air"], WORRIED, by="COUNTRY_ISO3")})
    t["ratio"] = pm.reindex(t.index) / 5
    t = t.dropna()
    t["band"] = pd.cut(t.ratio, [0, 2, 3, 5, 7, np.inf], right=False, labels=["lt2x", "x2_3", "x3_5", "x5_7", "x7plus"])
    return t


@report.finding("C4_9")
def pm25_medians():
    t = pm25_bands()
    med = t.groupby("band", observed=True)[["experience", "worry"]].median()
    return {f"{m}_{b}": med.loc[b, m] for m in ("experience", "worry") for b in med.index}


@report.finding("X137")
def pm25_mid_harm():
    t = pm25_bands()
    return t[t.band.isin(["x2_3", "x3_5", "x5_7"])].experience.median()


@report.finding("T4_2")
def top10_weather_harm():
    out = {}
    for k in ("severe_weather", "prolonged_weather"):
        top = top10_harm(k).index
        rs = harmed_df(d25[d25.COUNTRY_ISO3.isin(top)], k, by="COUNTRY_ISO3")
        out.update({f"{k}_{c}": v for c, v in rs.items()})
    return out


@report.finding("T4_2")
def top10_weather_harm_countries():
    return {f"{k}_top10": " ".join(sorted(top10_harm(k).index)) for k in ("severe_weather", "prolonged_weather")}


report.finding("X138")(lambda: harmed_df(d25[d25.COUNTRY_ISO3 == "PHL"], "severe_weather"))
report.finding("X139")(lambda: pct(d25, WORRY["prolonged_weather"], [1]))
report.finding("X140")(lambda: pct(d25, WORRY["prolonged_weather"], [2]))


def no_threat_top5():
    return pct(d25, "WP20719", [3], by="COUNTRY_ISO3").sort_values(ascending=False).head(5)


report.finding("X141")(lambda: no_threat_top5().iloc[-1])
report.finding("X142")(lambda: int(no_threat_top5().index.isin(["BHR", "SAU", "ARE"]).sum()))


def least_worried_prolonged():
    rs = worried(d25, "prolonged_weather", by="COUNTRY_ISO3")
    t = pd.DataFrame({"rs": rs, "iso": rs.index})
    return pd.Index(t.sort_values(["rs", "iso"]).head(10).iso)  # ties: ISO3 order


@report.finding("C4_10")
def least_worried():
    t = distribution(d25, WORRY["prolonged_weather"], by="COUNTRY_ISO3")
    g = distribution(d25, WORRY["prolonged_weather"])
    out = {"global_very": g[1], "global_somewhat": g[2]}
    for c in least_worried_prolonged():
        out[f"{c}_very"], out[f"{c}_somewhat"] = t.loc[c, 1], t.loc[c, 2]
    return out


@report.finding("C4_10")
def least_worried_countries():
    return {"countries": " ".join(sorted(least_worried_prolonged()))}


if __name__ == "__main__":
    sys.exit(report.run())
