"""Reproduce World Risk Poll 2026: A resilient life: How wellbeing shapes the capacity to cope.

Run from the repository root:
    python reports/WRP_2025/core_a_resilient_life/reproduce.py

The report uses the Resilience Index from the 2021, 2023 and 2025 polls
(Chapter 1), relates it to Gallup's Life Evaluation Index (Chapter 2), and
looks at how much people feel their government and neighbours care about
them (Chapter 3). Each function below computes one chart, table or text
statement listed in published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

# --- Variables -------------------------------------------------------------------

# Resilience Index (0-100) and its four dimensions (0-1 in the data, x 100 here).
DIMS = {"index": "resilience_index_100", "individual": "resilience_idv", "household": "resilience_hhl",
        "community": "resilience_com", "societal": "resilience_soc"}
AGENCY = "WP22252"     # could protect yourself or family in a future disaster: 1 = yes
FINANCE = "WP22228"    # could cover basic needs if income was lost: 2 = a month or more
NEIGHBOURS = "WP22232"  # neighbours care about you: 1 a lot, 2 somewhat, 3 not at all
GOVERNMENT = "WP22231_ALL"  # government cares about you (2023, 2025), including Myanmar and Vietnam
CARE = {"a_lot": 1, "somewhat": 2, "not_at_all": 3}
DK = [98, 99]  # don't know, refused
DISCRIMINATION = ["WP22259", "WP22260", "WP22261", "WP22262", "WP22263"]  # skin, religion, nationality, gender, disability
HARM = {"prolonged_weather": "WP24177", "severe_weather": "WP22445", "traffic": "WP22446", "food": "WP22442",
        "water": "WP22443", "mental_health": "WP22447", "crime": "WP22444"}  # 1 personally, 2 someone else, 3 both

REGION = {1: "east_africa", 2: "cw_africa", 3: "north_africa", 4: "southern_africa", 5: "latam",
          6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia", 10: "southern_asia",
          11: "middle_east", 12: "eastern_europe", 13: "nw_europe", 14: "southern_europe", 15: "anz"}
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # 9 = not classified: left out
AFRICA = {3: "north_africa", 2: "cw_africa", 4: "southern_africa", 1: "east_africa"}
LE = {1: "thriving", 2: "struggling", 3: "suffering"}

BASE = ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel", *DIMS.values()]
d25 = load_wave(2025, BASE + [AGENCY, FINANCE, NEIGHBOURS, GOVERNMENT, "WP22231", "WP23345", *DISCRIMINATION, *HARM.values()])
d23 = load_wave(2023, BASE + [AGENCY, FINANCE, NEIGHBOURS, GOVERNMENT, "WP23345"])
d21 = load_wave(2021, BASE + [AGENCY, FINANCE, NEIGHBOURS, "WP22231", "WP22469", "WP22525", "WP22253"])
d19 = load_wave(2019, ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion"])

# Trends use the countries surveyed in 2025 in every wave, classified by their 2025
# region (this is what reproduces Table 1.2 and the 2021 values in Chart 3.1; see README).
REGION_2025 = d25.groupby("COUNTRY_ISO3")["GlobalRegion"].first()
C25 = set(REGION_2025.index)
d21 = d21[d21.COUNTRY_ISO3.isin(C25)].copy()
d23 = d23[d23.COUNTRY_ISO3.isin(C25)].copy()
d19 = d19[d19.COUNTRY_ISO3.isin(C25)].copy()
WAVES = {2021: d21, 2023: d23, 2025: d25}

# --- Derived variables -----------------------------------------------------------

for d in (d19, d21, d23, d25):
    d["region"] = d.COUNTRY_ISO3.map(REGION_2025)

for d in WAVES.values():
    for key, var in DIMS.items():
        d[key] = d[var] if key == "index" else 100 * d[var]

# 2021 asked Vietnam and Myanmar about "the authorities" and "the government in power";
# the combined question matches the 2023 and 2025 WP22231_ALL.
d21[GOVERNMENT] = d21.WP22231.fillna(d21.WP22469).fillna(d21.WP22525)

# Disaster plan known to all household members: 2021 wording (WP22253), 2023-25 "over 10 years old".
d21["plan"] = d21.WP22253
d23["plan"] = d23.WP23345
d25["plan"] = d25.WP23345

# Country scores (unrounded) for every wave.
country = {y: pd.DataFrame({k: wmean(d, k, by="COUNTRY_ISO3") for k in DIMS}) for y, d in WAVES.items()}


# --- Helpers ---------------------------------------------------------------------


def r0(x):
    """Round half up to a whole number, as printed (same rule in the R script)."""
    if isinstance(x, (pd.Series, pd.DataFrame)):
        return np.floor(x.astype(float) + 0.5 + 1e-9)
    return np.floor(np.asarray(x, dtype=float) + 0.5 + 1e-9)


def keyed(series, keys):
    """Rename a by-group result's index with readable keys, dropping unknown groups."""
    return {keys[k]: v for k, v in series.items() if k in keys}


def score(iso, dim, year):
    return country[year].loc[iso, dim]


def rounded_change(iso, dim, start, end):
    """Change in a country's score between two waves, from the rounded scores."""
    return float(r0(score(iso, dim, end)) - r0(score(iso, dim, start)))


def country_pct(y, var, codes, iso, exclude=None):
    return pct(WAVES[y][WAVES[y].COUNTRY_ISO3 == iso], var, codes, exclude=exclude)


def pct_change(var_by_year, codes, iso, start, end, exclude=None):
    """Change in a country's % between two waves, from the rounded percentages."""
    vals = {y: country_pct(y, var_by_year[y], codes, iso, exclude) for y in (start, end)}
    return float(r0(vals[end]) - r0(vals[start]))


def harmed(var):
    """% personally harmed: 'yes, personally' + 'both', each rounded first (as The quiet hazards)."""
    t = distribution(d25, var)
    return float(r0(t.get(1, 0.0)) + r0(t.get(3, 0.0)))


def rank_of(series, iso):
    """Rank of a country, 1 = highest, on unrounded values."""
    return int(series.dropna().rank(ascending=False, method="min")[iso])


def life_evaluation(df):
    """Gallup Life Evaluation Index groups from the Cantril ladder (WP16 now, WP18 in five years).

    1 thriving (now 7+ and future 8+), 3 suffering (both 4 or below),
    2 struggling (everyone else with valid answers).
    """
    g = merge_gallup(df, ["WP16", "WP18"])
    now, fut = g.WP16.where(g.WP16 <= 10), g.WP18.where(g.WP18 <= 10)
    g["ladder"] = now
    g["life_eval"] = np.select([(now >= 7) & (fut >= 8), (now <= 4) & (fut <= 4), now.notna() & fut.notna()],
                               [1.0, 3.0, 2.0], default=np.nan)
    return g


def care_gaps(var):
    """Country 'not at all' minus 'a lot', from the rounded percentages (Chart 3.2)."""
    t = distribution(d25, var, by="COUNTRY_ISO3")
    return pd.Series(r0(t[3]) - r0(t[1]), index=t.index)


def top_not_at_all(var):
    """Table 3.1: countries with the highest % 'not at all', ties at the 10th rounded value included."""
    s = pct(d25, var, [3], by="COUNTRY_ISO3").sort_values(ascending=False)
    cutoff = r0(s.iloc[9])
    return s[r0(s) >= cutoff]


def internet(df):
    """Gallup WP16056: access to the internet (1 = yes)."""
    return merge_gallup(df, ["WP16056"])


def confidence(df, item):
    """Gallup confidence items (1 = yes): WP137 military, WP138 judicial system, WP139 national government."""
    return merge_gallup(df, [item])


# --- Front matter and executive summary ---------------------------------------------


@report.finding("X01")
def interviews():
    return len(d25)


@report.finding("X02")
def countries():
    return d25.COUNTRY_ISO3.nunique()


@report.finding("X03")
def index_2025():
    return wmean(d25, "index")


def global_rounded(dim, year):
    return float(r0(wmean(WAVES[year], dim)))


@report.finding("X04")
def index_change_2021_2025():
    return global_rounded("index", 2025) - global_rounded("index", 2021)


@report.finding("X05")
def individual_change_2023_2025():
    return global_rounded("individual", 2025) - global_rounded("individual", 2023)


@report.finding("X06")
def individual_change_2021_2023():
    return global_rounded("individual", 2023) - global_rounded("individual", 2021)


@report.finding("X07")
def household_change():
    return global_rounded("household", 2025) - global_rounded("household", 2023)


@report.finding("X08")
def community_change():
    return global_rounded("community", 2025) - global_rounded("community", 2023)


for _fid, _iso in [("X09", "GRC"), ("X10", "NZL"), ("X11", "AUS"), ("X12", "NLD"), ("X13", "EST"), ("X14", "FRA")]:
    report.finding(_fid)(lambda iso=_iso: rounded_change(iso, "societal", 2021, 2025))


def table_1_2():
    """Resilience Index by region (2025 classification) in each wave."""
    return pd.DataFrame({y: wmean(d, "index", by="region") for y, d in WAVES.items()})


@report.finding("X15")
def region_change_2023_2025():
    t = table_1_2()
    return keyed(r0(t[2025]) - r0(t[2023]), REGION)


@report.finding("X16")
def household_change_africa():
    return {iso: rounded_change(iso, "household", 2021, 2025) for iso in ["DZA", "NGA", "KEN", "EGY", "UGA"]}


def table_1_3():
    """% with internet access in 2019 and 2025, by African region and globally (countries surveyed in 2025)."""
    out = {}
    for year, d in ((2019, d19), (2025, d25)):
        g = internet(d[d.COUNTRY_ISO3.isin(C25)])
        by_region = pct(g, "WP16056", [1], by="region")
        for code, key in AFRICA.items():
            out[(key, year)] = by_region[code]
        out[("global", year)] = pct(g, "WP16056", [1])
    return out


@report.finding("X17")
def internet_change():
    t = table_1_3()
    return {key: float(r0(t[(key, 2025)]) - r0(t[(key, 2019)])) for key in ["north_africa", "cw_africa", "southern_africa"]}


def agency_change_2023_2025():
    a23 = pct(d23, AGENCY, [1], by="COUNTRY_ISO3")
    a25 = pct(d25, AGENCY, [1], by="COUNTRY_ISO3")
    return (a25 - a23).dropna()


@report.finding("X18")
def agency_increases():
    # A change counts when it rounds to 10 points or more.
    return int((r0(agency_change_2023_2025()) >= 10).sum())


@report.finding("X19")
def agency_decreases():
    return int((r0(-agency_change_2023_2025()) >= 10).sum())


def life_eval_index(dim="index", by=None):
    g = life_evaluation(d25)
    keys = ["CountryIncomeLevel", "life_eval"] if by == "income" else "life_eval"
    return wmean(g, dim, by=keys)


@report.finding("X20")
def thriving_suffering_gap():
    s = life_eval_index()
    return float(r0(s[1]) - r0(s[3]))


@report.finding("X21")
def smallest_income_gap():
    s = life_eval_index(by="income").unstack()
    gaps = r0(s.loc[list(INCOME), 1]) - r0(s.loc[list(INCOME), 3])
    return float(gaps.min())


def chart_2_3():
    """Resilience Index by present life rating (0-10) and income group (no printed values)."""
    g = life_evaluation(d25)
    return wmean(g, "index", by=["CountryIncomeLevel", "ladder"]).unstack()


@report.finding("X22")
def bottom_of_ladder():
    g = life_evaluation(d25)
    low = g[g.ladder <= 2]
    return keyed(wmean(low, "index", by="CountryIncomeLevel"), INCOME)


@report.finding("X23")
def ten_below_nine():
    t = chart_2_3()
    return int(sum(t.loc[code, 10] < t.loc[code, 9] for code in INCOME))


@report.finding("C2_3")
def chart_2_3_values():
    t = chart_2_3().loc[list(INCOME)]
    return {(INCOME[i], int(r)): v for (i, r), v in t.stack().items()}


@report.finding("X24")
def government_not_at_all_change():
    return float(r0(pct(d25, GOVERNMENT, [3])) - r0(pct(d21, GOVERNMENT, [3])))


@report.finding("X25")
def government_gap_not_at_all():
    return int((care_gaps(GOVERNMENT) >= 10).sum())


@report.finding("X26")
def government_gap_a_lot():
    return int((care_gaps(GOVERNMENT) <= -10).sum())


def chart_3_6():
    t = wmean(d25, "household", by=["CountryIncomeLevel", NEIGHBOURS]).unstack()
    return t.loc[list(INCOME), [1, 2, 3]]


@report.finding("X27")
def care_household_gap():
    t = chart_3_6()
    return {INCOME[i]: float(r0(t.loc[i, 1]) - r0(t.loc[i, 3])) for i in INCOME}


@report.finding("X28")
def care_correlation():
    gov = pct(d25, GOVERNMENT, [3], by="COUNTRY_ISO3")
    nbr = pct(d25, NEIGHBOURS, [3], by="COUNTRY_ISO3")
    both = pd.concat([gov, nbr], axis=1).dropna()
    return both.iloc[:, 0].corr(both.iloc[:, 1])


# --- Chapter 1 -------------------------------------------------------------------


@report.finding("X29")
def harm_2025():
    return {key: harmed(var) for key, var in HARM.items()}


@report.finding("C1_1")
def chart_1_1():
    return {(k, y): wmean(d, k) for k in DIMS for y, d in WAVES.items()}


@report.finding("C1_2")
def chart_1_2():
    return {(k, INCOME[i]): v for k in DIMS for i, v in wmean(d25, k, by="CountryIncomeLevel").items() if i in INCOME}


@report.finding("X30")
def individual_high_vs_upper_middle():
    s = wmean(d25, "individual", by="CountryIncomeLevel")
    return float(r0(s[4]) - r0(s[3]))


@report.finding("T1_2")
def table_1_2_values():
    t = table_1_2()
    return {(REGION[r], y): t.loc[r, y] for r in REGION for y in WAVES}


@report.finding("X31")
def individual_change_2021_2025():
    return {iso: rounded_change(iso, "individual", 2021, 2025) for iso in ["POL", "SVK", "HRV", "BGR", "BIH", "MAR"]}


@report.finding("X32")
def larger_fall_than_poland():
    change = (country[2025]["individual"] - country[2021]["individual"]).dropna()
    return int((change < change["POL"]).sum())


@report.finding("X33")
def morocco_individual_2021():
    return score("MAR", "individual", 2021)


@report.finding("X34")
def morocco_individual_2025():
    return score("MAR", "individual", 2025)


@report.finding("X35")
def agency_change_2021_2025():
    return {iso: pct_change({y: AGENCY for y in WAVES}, [1], iso, 2021, 2025) for iso in ["SVK", "BGR", "HRV", "POL", "BIH"]}


@report.finding("X36")
def household_range():
    return {iso: score(iso, "household", 2025) for iso in ["DZA", "EGY"]}


@report.finding("X37")
def finance_change():
    # Among those giving an answer: with don't know and refused in the base the changes are
    # 24, 16, 5, 6 and 6 points (see README).
    return {iso: pct_change({y: FINANCE for y in WAVES}, [2], iso, 2021, 2025, DK) for iso in ["DZA", "EGY", "UGA", "KEN", "NGA"]}


@report.finding("X38")
def plan_change():
    # Among those giving an answer, as for X37 (Algeria is 31 points with don't know in the base).
    return {iso: pct_change({y: "plan" for y in WAVES}, [1], iso, 2021, 2025, DK) for iso in ["DZA", "KEN"]}


@report.finding("T1_3")
def table_1_3_values():
    return table_1_3()


@report.finding("X39")
def ukraine():
    out = {f"community_{y}": score("UKR", "community", y) for y in WAVES}
    out["individual_2025"] = score("UKR", "individual", 2025)
    return out


@report.finding("X40")
def ukraine_neighbours():
    return {y: country_pct(y, NEIGHBOURS, [1, 2], "UKR") for y in WAVES}


@report.finding("X41")
def us_scores():
    return {"USA_individual": score("USA", "individual", 2025), "USA_household": score("USA", "household", 2025),
            "SWE_individual": score("SWE", "individual", 2025), "VNM_household": score("VNM", "household", 2025),
            "USA_community": score("USA", "community", 2025)}


@report.finding("C1_7")
def us_ranks():
    return {k: rank_of(country[2025][k], "USA") for k in ["individual", "household", "community", "societal"]}


@report.finding("X42")
def societal_ranked():
    return int(country[2025]["societal"].notna().sum())


def us_confidence(item, year):
    d = {2019: d19, 2025: d25}[year]
    return pct(confidence(d[d.COUNTRY_ISO3 == "USA"], item), item, [1])


@report.finding("X43")
def us_confidence_items():
    return {"national_government": us_confidence("WP139", 2025), "judicial": us_confidence("WP138", 2025),
            "military_2025": us_confidence("WP137", 2025), "military_2019": us_confidence("WP137", 2019)}


@report.finding("X44")
def us_government_a_lot():
    return country_pct(2025, "WP22231", [1], "USA")


@report.finding("X45")
def us_discrimination():
    return {v: country_pct(2025, v, [1], "USA") for v in DISCRIMINATION}


@report.finding("X46")
def us_discrimination_rank():
    return {v: rank_of(pct(d25, v, [1], by="COUNTRY_ISO3"), "USA") for v in ["WP22259", "WP22261", "WP22262"]}


@report.finding("C1_3")
def chart_1_3():
    """Individual resilience in five Eastern European countries (no printed values)."""
    return {(iso, y): score(iso, "individual", y) for iso in ["POL", "SVK", "HRV", "BGR", "BIH"] for y in WAVES}


@report.finding("C1_4")
def chart_1_4():
    """Household resilience in five African countries (no printed values)."""
    return {(iso, y): score(iso, "household", y) for iso in ["DZA", "NGA", "KEN", "EGY", "UGA"] for y in WAVES}


@report.finding("C1_5")
def chart_1_5():
    """Ukraine: Resilience Index and dimensions (no printed values)."""
    return {(k, y): score("UKR", k, y) for k in DIMS for y in WAVES}


@report.finding("C1_6")
def chart_1_6():
    """Societal resilience in six high-income countries (no printed values)."""
    return {(iso, y): score(iso, "societal", y) for iso in ["GRC", "NZL", "AUS", "NLD", "EST", "FRA"] for y in WAVES}


# --- Chapter 2 (Gallup Life Evaluation Index) -------------------------------------------


@report.finding("C2_1")
def chart_2_1():
    by_income = life_eval_index(by="income")
    out = {(INCOME[i], LE[le]): v for (i, le), v in by_income.items() if i in INCOME and le in LE}
    out.update({("global", LE[le]): v for le, v in life_eval_index().items() if le in LE})
    return out


def country_wellbeing():
    g = life_evaluation(d25)
    return pd.DataFrame({"thriving": pct(g[g.life_eval.notna()], "life_eval", [1], by="COUNTRY_ISO3"),
                         "ladder": wmean(g, "ladder", by="COUNTRY_ISO3"),
                         "index": country[2025]["index"]})


@report.finding("X47")
def ladder_index_correlation():
    t = country_wellbeing().dropna()
    return t.ladder.corr(t["index"])


@report.finding("X48")
def median_index():
    return country[2025]["index"].median()


@report.finding("X49")
def median_thriving():
    return country_wellbeing().thriving.median()


@report.finding("C2_2")
def chart_2_2():
    """Country % thriving against the Resilience Index (no printed values)."""
    t = country_wellbeing().dropna()
    return {(iso, k): t.loc[iso, k] for iso in t.index for k in ["thriving", "index"]}


@report.finding("C2_4")
def chart_2_4():
    return {(k, LE[le]): v for k in ["individual", "household", "community", "societal"]
            for le, v in life_eval_index(k).items() if le in LE}


@report.finding("C2_5")
def chart_2_5():
    g = life_evaluation(d25)
    suffering = g[g.life_eval == 3]
    return {(INCOME[i], k): v for k in ["individual", "household", "community", "societal"]
            for i, v in wmean(suffering, k, by="CountryIncomeLevel").items() if i in INCOME}


# --- Chapter 3 -------------------------------------------------------------------


@report.finding("C3_1")
def chart_3_1():
    out = {}
    for who, var in (("government", GOVERNMENT), ("neighbours", NEIGHBOURS)):
        for y in (2021, 2025):
            for key, code in CARE.items():
                out[(who, y, key)] = pct(WAVES[y], var, [code])
    return out


@report.finding("X50")
def government_a_lot_change():
    return float(r0(pct(d25, GOVERNMENT, [1])) - r0(pct(d21, GOVERNMENT, [1])))


@report.finding("X51")
def government_somewhat_change():
    return float(r0(pct(d25, GOVERNMENT, [2])) - r0(pct(d21, GOVERNMENT, [2])))


@report.finding("C3_2")
def chart_3_2():
    out = {}
    for who, var in (("gov", GOVERNMENT), ("nbr", NEIGHBOURS)):
        g = care_gaps(var)
        out[f"{who}_a_lot"] = int((g <= -10).sum())
        out[f"{who}_under_10"] = int(((g > -10) & (g < 10)).sum())
        out[f"{who}_not_at_all"] = int((g >= 10).sum())
    return out


@report.finding("C3_3")
def chart_3_3():
    return {(who, INCOME[i]): v for who, var in (("government", GOVERNMENT), ("neighbours", NEIGHBOURS))
            for i, v in pct(d25, var, [3], by="CountryIncomeLevel").items() if i in INCOME}


@report.finding("C3_4")
def chart_3_4():
    g = life_evaluation(d25)
    return keyed(pct(g[g.life_eval.notna()], "life_eval", [1], by="CountryIncomeLevel"), INCOME)


@report.finding("C3_5")
def chart_3_5():
    return {(who, REGION[r]): v for who, var in (("government", GOVERNMENT), ("neighbours", NEIGHBOURS))
            for r, v in pct(d25, var, [3], by="GlobalRegion").items() if r in REGION}


@report.finding("T3_1")
def table_3_1():
    out = {}
    for who, var in (("government", GOVERNMENT), ("neighbours", NEIGHBOURS)):
        top = top_not_at_all(var)
        out[f"{who}_top10"] = ", ".join(sorted(top.index))
        out.update({f"{who}_{iso}": v for iso, v in top.items()})
    return out


@report.finding("X52")
def on_both_lists():
    return len(set(top_not_at_all(GOVERNMENT).index) & set(top_not_at_all(NEIGHBOURS).index))


@report.finding("C3_6")
def chart_3_6_values():
    t = chart_3_6()
    keys = {1: "a_lot", 2: "somewhat", 3: "not_at_all"}
    return {(INCOME[i], keys[c]): t.loc[i, c] for i in INCOME for c in keys}


if __name__ == "__main__":
    sys.exit(report.run())
