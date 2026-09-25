"""Reproduce World Risk Poll 2026: A resilient life: How wellbeing shapes the capacity to cope.

Run from the repository root:
    python reports/WRP_2025/core_a_resilient_life/reproduce.py

The report uses the 2025 data (wave 4), with Resilience Index trends across
2021, 2023 and 2025. Chapter 2 combines the Resilience Index with Gallup's
Life Evaluation Index (Cantril ladder), which is not in the public release.
Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

# --- Variables -------------------------------------------------------------------

# The Resilience Index and its four dimensions: the released 0-1 scores, used x 100.
DIMS = {"index": "resilience_index", "individual": "resilience_idv", "household": "resilience_hhl",
        "community": "resilience_com", "societal": "resilience_soc"}
FOUR = ["individual", "household", "community", "societal"]
REGION = {1: "east_africa", 2: "cw_africa", 3: "north_africa", 4: "southern_africa", 5: "latam",
          6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia",
          10: "southern_asia", 11: "middle_east", 12: "eastern_europe", 13: "nw_europe",
          14: "southern_europe", 15: "anz"}
AFRICA = ["north_africa", "southern_africa", "cw_africa", "east_africa"]
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # 9 = not classified: left out
LE = {1: "thriving", 2: "struggling", 3: "suffering"}
CARE = {1: "a_lot", 2: "somewhat", 3: "not_at_all"}
WHO = {"government": "gov", "neighbours": "WP22232"}
DISC = {"skin": "WP22259", "religion": "WP22260", "nationality": "WP22261", "gender": "WP22262",
        "disability": "WP22263"}
PLAN = {2021: "WP22253", 2023: "WP23345", 2025: "WP23345"}  # household disaster plan known to all
# Harm in the past two years (1 personally, 2 someone you know, 3 both, 4 no), page 1.
HARM = {"prolonged_weather": "WP24177", "severe_weather": "WP22445", "traffic": "WP22446", "food": "WP22442",
        "water": "WP22443", "mental_health": "WP22447", "crime": "WP22444"}
DK = [98, 99]
SIX = ["GRC", "NZL", "AUS", "NLD", "EST", "FRA"]  # Chart 1.6
# Country names as printed in Table 3.1 (others use the release's Country name).
NAME = {"COM": "Comoros", "BOL": "Bolivia", "PER": "Peru", "PAN": "Panama", "ROU": "Romania", "PRY": "Paraguay",
        "COL": "Colombia", "HND": "Honduras", "MDG": "Madagascar", "GRC": "Greece",
        "HKG": "Hong Kong (S.A.R. of China)", "GAB": "Gabon", "RUS": "Russia", "ECU": "Ecuador", "MEX": "Mexico",
        "COG": "Republic of Congo"}

BASE = ["WPID_RANDOM", "COUNTRY_ISO3", "Country", "PROJWT", "GlobalRegion", "CountryIncomeLevel", *DIMS.values(),
        "WP22231", "WP22232", "WP22252", "WP22228", *DISC.values()]
d25 = load_wave(2025, BASE + ["WP22231_ALL", "WP23345", *HARM.values()])
d23 = load_wave(2023, BASE + ["WP22231_ALL", "WP23345"])
d21 = load_wave(2021, BASE + ["WP22525", "WP22469", "WP22253"])
d19 = load_wave(2019, ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion"])  # Gallup items only

# --- Derived variables -----------------------------------------------------------

for y, d in [(2021, d21), (2023, d23), (2025, d25)]:
    for k, v in DIMS.items():
        d[k] = 100 * d[v]  # 0-100, as printed
    d["region"] = d.GlobalRegion.map(REGION)
    d["income"] = d.CountryIncomeLevel.map(INCOME)
    d["plan"] = d[PLAN[y]]
# Government cares about you: the combined version that adds Myanmar's and
# Vietnam's own wording (WP22231_ALL in 2023 and 2025; built the same way for 2021).
d25["gov"] = d25.WP22231_ALL
d23["gov"] = d23.WP22231_ALL
d21["gov"] = d21.WP22231.fillna(d21.WP22525).fillna(d21.WP22469)
d19["region"] = d19.GlobalRegion.map(REGION)

# Every country in each wave (country-level changes) and, for global and
# regional trends, the countries surveyed in 2025, as the report does (this
# reproduces Table 1.2 and Chart 3.1; see README).
C25 = set(d25.COUNTRY_ISO3)
ALL = {2021: d21, 2023: d23, 2025: d25}
TREND = {y: d[d.COUNTRY_ISO3.isin(C25)] for y, d in ALL.items()}

# --- Helpers ---------------------------------------------------------------------


def r0(x):
    """Round half up to a whole number, as printed (same rule in the R script)."""
    return float(np.floor(np.asarray(x, dtype=float) + 0.5 + 1e-9))


def rdiff(a, b):
    """Difference of two figures rounded as printed: how the report states its changes."""
    return r0(a) - r0(b)


def keyed(series, keys):
    """Rename a by-group result's index with readable keys, dropping unknown groups."""
    return {keys[k]: v for k, v in series.items() if k in keys}


def country(df, iso):
    return df[df.COUNTRY_ISO3 == iso]


def country_means(df, k):
    return wmean(df, k, by="COUNTRY_ISO3")


def country_pct(df, var, codes, exclude=None):
    return pct(df, var, codes, by="COUNTRY_ISO3", exclude=exclude)


def ranks(series, ascending=False):
    """Rank countries, 1 = highest (ties share the best rank)."""
    return series.dropna().rank(ascending=ascending, method="min")


def rsum(df, var, codes):
    """Sum of the rounded % in each of `codes` ('personally' + 'both', as in The quiet hazards)."""
    t = distribution(df, var)
    return sum(r0(t.get(c, 0.0)) for c in codes)


@lru_cache(maxsize=None)
def wellbeing():
    """2025 respondents with Gallup's Life Evaluation Index (WP16 now, WP18 in five years).

    life_eval: 1 thriving (now 7+ and future 8+), 3 suffering (both 4 or below),
    2 struggling (everyone else with valid answers). ladder: WP16, 0-10.
    """
    g = merge_gallup(d25, ["WP16", "WP18"])
    now, fut = g.WP16.where(g.WP16 <= 10), g.WP18.where(g.WP18 <= 10)
    g["ladder"] = now
    g["life_eval"] = np.select([(now >= 7) & (fut >= 8), (now <= 4) & (fut <= 4), now.notna() & fut.notna()],
                               [1.0, 3.0, 2.0], default=np.nan)
    g["thriving"] = np.where(g.life_eval.notna(), 100.0 * (g.life_eval == 1), np.nan)
    return g


@lru_cache(maxsize=None)
def gallup_wave(year, item):
    """One wave with a Gallup yes/no item (1 = yes) as a 0/100 variable `yes`."""
    d = {2019: d19, **ALL}[year]
    g = merge_gallup(d, [item])
    g["yes"] = np.where(g[item].notna(), 100.0 * (g[item] == 1), np.nan)
    return g


def internet(year):
    """Gallup WP16056: access to the internet in any way (1 = yes); countries surveyed in 2025."""
    g = gallup_wave(year, "WP16056")
    return g[g.COUNTRY_ISO3.isin(C25)]


def agency_change():
    """Change in country % who could protect themselves (WP22252 = yes), 2023 to 2025."""
    a23, a25 = country_pct(d23, "WP22252", [1]), country_pct(d25, "WP22252", [1])
    common = a23.index.intersection(a25.index)
    return a25[common] - a23[common]


def big(change):
    """A change counts as 10 points or more when it rounds to 10 or more."""
    return change.map(r0) >= 10


def region_change():
    """Regional Index change 2023 to 2025 (difference of the rounded Table 1.2 scores)."""
    a, b = wmean(TREND[2023], "index", by="region"), wmean(TREND[2025], "index", by="region")
    return pd.Series({k: rdiff(b[k], a[k]) for k in b.index})


def country_change(k, y0=2021, y1=2025, isos=None):
    """Country change in a dimension (difference of rounded scores), for `isos` or every
    country with a score in both waves."""
    a, b = country_means(ALL[y0], k).dropna(), country_means(ALL[y1], k).dropna()
    isos = isos or sorted(set(a.index) & set(b.index))
    return {i: rdiff(b[i], a[i]) for i in isos}


def care_gaps(who):
    """Country % 'not at all' minus % 'a lot', rounded: counts of gaps of 10+ points either way."""
    t = distribution(d25, WHO[who], by="COUNTRY_ISO3")
    gap = (t[3.0] - t[1.0]).map(r0)
    return {"a_lot_higher": int((gap <= -10).sum()), "under_10": int(((gap > -10) & (gap < 10)).sum()),
            "not_at_all_higher": int((gap >= 10).sum())}


def top10(who):
    """Table 3.1: rows of (countries, unrounded %) for the 10 highest % 'not at all'.

    Countries are ranked on unrounded %; the last row holds every remaining
    country with the same printed (rounded) value, as the table prints
    "Mexico, Republic of Congo".
    """
    s = country_pct(d25, WHO[who], [3]).sort_values(ascending=False)
    rows = [([i], s[i]) for i in s.index[:9]]
    last = [i for i in s.index[9:] if r0(s[i]) == r0(s.iloc[9])]
    rows.append((last, s.iloc[9]))
    return rows


def name(iso):
    return NAME.get(iso, d25.loc[d25.COUNTRY_ISO3 == iso, "Country"].iloc[0])


def gm(y, k, by=None):
    """Global (or by-group) mean of a 0-100 measure over the trend countries."""
    return wmean(TREND[y], k, by=by)


# --- Front matter and executive summary -------------------------------------------


@report.finding("X01")
def interviews():
    return len(d25)


@report.finding("X02")
def countries():
    return d25.COUNTRY_ISO3.nunique()


@report.finding("X03")
def care_a_lot():
    return {"government": pct(d25, "gov", [1]), "neighbours": pct(d25, "WP22232", [1])}


report.finding("X04")(lambda: gm(2025, "index"))
report.finding("X05")(lambda: rdiff(gm(2025, "index"), gm(2023, "index")))
report.finding("X06")(lambda: rdiff(gm(2025, "index"), gm(2021, "index")))
report.finding("X07")(lambda: gm(2021, "index"))
report.finding("X08")(lambda: gm(2025, "individual"))
report.finding("X09")(lambda: rdiff(gm(2025, "individual"), gm(2023, "individual")))
report.finding("X10")(lambda: rdiff(gm(2023, "individual"), gm(2021, "individual")))
report.finding("X11")(lambda: gm(2021, "individual"))
report.finding("X12")(lambda: gm(2023, "individual"))
report.finding("X13")(lambda: gm(2025, "household"))
report.finding("X14")(lambda: rdiff(gm(2025, "household"), gm(2023, "household")))
report.finding("X15")(lambda: gm(2025, "community"))
report.finding("X16")(lambda: rdiff(gm(2025, "community"), gm(2023, "community")))
report.finding("X17")(lambda: int(big(agency_change()).sum()))
report.finding("X18")(lambda: int(big(-agency_change()).sum()))
report.finding("X19")(lambda: int(big(-agency_change())[["IND", "PAK", "IDN"]].sum()))
report.finding("X20")(lambda: gm(2025, "societal"))
report.finding("X21")(lambda: gm(2023, "societal"))
report.finding("X22")(lambda: gm(2021, "societal"))
report.finding("X23")(lambda: country_change("societal", isos=SIX))


@report.finding("X24")
def african_region_changes():
    c = region_change()
    return {k: c[k] for k in [*AFRICA, "latam"]}


@report.finding("X25")
def africa_largest_gains():
    rank = region_change().rank(ascending=False, method="min")
    return int((rank[AFRICA] <= 4).sum())


report.finding("X26")(lambda: country_change("household", isos=["DZA", "NGA", "KEN", "EGY", "UGA"]))


def table_1_3():
    out = {}
    for y in (2019, 2025):
        g = internet(y)
        out.update({f"{k}_{y}": v for k, v in keyed(wmean(g, "yes", by="GlobalRegion"), REGION).items() if k in AFRICA})
        out[f"global_{y}"] = wmean(g, "yes")
    return out


@report.finding("X27")
def internet_change():
    t = table_1_3()
    return {k: rdiff(t[f"{k}_2025"], t[f"{k}_2019"]) for k in ["north_africa", "cw_africa", "southern_africa"]}


def by_life_eval(k, df=None):
    g = wellbeing() if df is None else df
    return keyed(wmean(g, k, by="life_eval"), LE)


report.finding("X28")(lambda: by_life_eval("index"))
report.finding("X29")(lambda: by_life_eval("individual"))


@report.finding("X30")
def individual_ratio():
    t = by_life_eval("individual")
    return t["thriving"] / t["suffering"]


@report.finding("X31")
def low_ladder_resilience():
    g = wellbeing()
    return keyed(wmean(g[g.ladder <= 2], "index", by="CountryIncomeLevel"), INCOME)


def chart_2_3():
    g = wellbeing()
    t = wmean(g, "index", by=["CountryIncomeLevel", "ladder"])
    return {(INCOME[i], int(r)): v for (i, r), v in t.items() if i in INCOME}


@report.finding("X32")
def ten_below_nine():
    t = chart_2_3()
    return sum(t[(inc, 10)] < t[(inc, 9)] for inc in INCOME.values())


def care(df, who):
    return keyed(distribution(df, WHO[who]), CARE)


report.finding("X33")(lambda: care(d25, "government"))
report.finding("X34")(lambda: rdiff(care(TREND[2025], "government")["not_at_all"],
                                    care(TREND[2021], "government")["not_at_all"]))


@report.finding("X35")
def neighbours_care():
    a, b = care(TREND[2021], "neighbours"), care(TREND[2025], "neighbours")
    return {"a_lot_2025": b["a_lot"], "not_at_all_2025": b["not_at_all"], "not_at_all_2021": a["not_at_all"],
            "a_lot_2021": a["a_lot"], "somewhat_2021": a["somewhat"], "somewhat_2025": b["somewhat"]}


@report.finding("X36")
def waves_not_at_all_exceeds():
    return sum(care(TREND[y], "government")["not_at_all"] > care(TREND[y], "government")["a_lot"] for y in TREND)


report.finding("X37")(lambda: care_gaps("government")["not_at_all_higher"])
report.finding("X38")(lambda: care_gaps("government")["a_lot_higher"])
report.finding("X39")(lambda: keyed(pct(d25, "gov", [3], by="CountryIncomeLevel"), INCOME))
report.finding("X40")(lambda: pct(d25[d25.CountryIncomeLevel.isin([2, 3])], "gov", [3]))


def household_by_neighbour_care():
    t = wmean(d25, "household", by=["CountryIncomeLevel", "WP22232"])
    return {(INCOME[i], CARE[c]): v for (i, c), v in t.items() if i in INCOME and c in CARE}


def household_care_gaps():
    t = household_by_neighbour_care()
    return {inc: rdiff(t[(inc, "a_lot")], t[(inc, "not_at_all")]) for inc in INCOME.values()}


report.finding("X41")(household_care_gaps)


@report.finding("X42")
def care_correlation():
    g, n = country_pct(d25, "gov", [3]), country_pct(d25, "WP22232", [3])
    j = pd.concat([g, n], axis=1).dropna()
    return float(np.corrcoef(j.iloc[:, 0], j.iloc[:, 1])[0, 1])


# --- Chapter 1 ---------------------------------------------------------------------


@report.finding("X43")
def stories():
    return int(sum(d[FOUR].notna().all(axis=1).sum() for d in ALL.values()))


report.finding("X44")(lambda: {k: rsum(d25, v, [1, 3]) for k, v in HARM.items()})


@report.finding("C1_1")
def chart_1_1():
    return {f"{k}_{y}": gm(y, k) for k in DIMS for y in TREND}


def by_income(k):
    return keyed(wmean(d25, k, by="CountryIncomeLevel"), INCOME)


@report.finding("C1_2")
def chart_1_2():
    return {f"{k}_{inc}": v for k in DIMS for inc, v in by_income(k).items()}


report.finding("X45")(lambda: by_income("index"))
report.finding("X46")(lambda: by_income("individual"))
report.finding("X47")(lambda: rdiff(by_income("individual")["high"], by_income("individual")["upper_middle"]))
report.finding("X48")(lambda: {inc: by_income("individual")["high"] / by_income("individual")[inc]
                               for inc in ["lower_middle", "low"]})
report.finding("X49")(lambda: by_income("household"))
report.finding("X50")(lambda: by_income("community"))
report.finding("X51")(lambda: by_income("societal"))


@report.finding("T1_2")
def table_1_2():
    return {f"{r}_{y}": v for y in TREND for r, v in keyed(gm(y, "index", by="GlobalRegion"), REGION).items()}


report.finding("X52")(lambda: {k: region_change()[k] for k in ["southern_asia", "eastern_asia"]})
report.finding("X53")(lambda: int((region_change() <= -2).sum()))
report.finding("X54")(lambda: country_change("individual", isos=["POL", "SVK", "HRV", "BGR", "BIH"]))


@report.finding("X55")
def morocco():
    a, b = wmean(country(d21, "MAR"), "individual"), wmean(country(d25, "MAR"), "individual")
    return {"change": rdiff(b, a), "2021": a, "2025": b}


@report.finding("X56")
def larger_fall_than_poland():
    c = pd.Series(country_change("individual"))
    return int((c < c["POL"]).sum())


@report.finding("X57")
def agency_eastern_europe():
    a, b = country_pct(d21, "WP22252", [1]), country_pct(d25, "WP22252", [1])
    return {i: rdiff(b[i], a[i]) for i in ["SVK", "BGR", "HRV", "POL", "BIH"]}


@report.finding("C1_3")
def chart_1_3():  # line chart with no printed values: written to output/ only
    return {f"{i}_{y}": wmean(country(d, i), "individual") for i in ["POL", "SVK", "HRV", "BGR", "BIH"]
            for y, d in ALL.items()}


report.finding("X58")(lambda: {i: wmean(country(d25, i), "household") for i in ["DZA", "EGY"]})


@report.finding("C1_4")
def chart_1_4():  # line chart with no printed values: written to output/ only
    return {f"{i}_{y}": wmean(country(d, i), "household") for i in ["DZA", "NGA", "KEN", "EGY", "UGA"]
            for y, d in ALL.items()}


@report.finding("X59")
def financial_change():
    # % who could cover basic needs for a month or more; don't know and refused excluded.
    a, b = (country_pct(d, "WP22228", [2], exclude=DK) for d in (d21, d25))
    return {i: rdiff(b[i], a[i]) for i in ["DZA", "EGY", "UGA", "KEN", "NGA"]}


@report.finding("X60")
def plan_change():
    a, b = (country_pct(d, "plan", [1], exclude=DK) for d in (d21, d25))
    return {i: rdiff(b[i], a[i]) for i in ["DZA", "KEN"]}


report.finding("T1_3")(table_1_3)
report.finding("X61")(lambda: {str(y): wmean(country(d, "UKR"), "community") for y, d in ALL.items()})
report.finding("X62")(lambda: wmean(country(d25, "UKR"), "individual"))
report.finding("X63")(lambda: {str(y): pct(country(d, "UKR"), "WP22232", [1, 2]) for y, d in ALL.items()})


@report.finding("C1_5")
def chart_1_5():  # line chart with no printed values: written to output/ only
    return {f"{k}_{y}": wmean(country(d, "UKR"), k) for k in DIMS for y, d in ALL.items()}


@report.finding("C1_6")
def chart_1_6():  # line chart with no printed values: written to output/ only
    return {f"{i}_{y}": wmean(country(d, i), "societal") for i in SIX for y, d in ALL.items()}


@report.finding("X64")
def six_government_care_fell():
    a, b = (country_pct(d[d.COUNTRY_ISO3.isin(SIX)], "gov", [1, 2]) for d in (d21, d25))
    return int((b[SIX] < a[SIX]).sum())


def confidence_fell(item, isos):
    a, b = (wmean(gallup_wave(y, item), "yes", by="COUNTRY_ISO3") for y in (2021, 2025))
    return int((b[isos] < a[isos]).sum())


report.finding("X65")(lambda: confidence_fell("WP139", SIX))
report.finding("X66")(lambda: confidence_fell("WP137", ["AUS", "GRC", "NZL", "NLD"]))
report.finding("X67")(lambda: confidence_fell("WP138", ["AUS", "GRC"]))


@report.finding("X68")
def australia_discrimination():
    return sum(pct(country(d25, "AUS"), DISC[k], [1]) > pct(country(d21, "AUS"), DISC[k], [1])
               for k in ["skin", "gender", "disability"])


def dim_ranks(k):
    return ranks(country_means(d25, k))


report.finding("X69")(lambda: {k: wmean(country(d25, "USA"), k) for k in ["individual", "household", "community"]})
report.finding("X70")(lambda: {"SWE": wmean(country(d25, "SWE"), "individual"),
                               "VNM": wmean(country(d25, "VNM"), "household")})
report.finding("X71")(lambda: {k: dim_ranks(k)["USA"] for k in FOUR})
report.finding("C1_7")(lambda: {k: dim_ranks(k)["USA"] for k in FOUR})
report.finding("X72")(lambda: len(dim_ranks("societal")))
report.finding("X73")(lambda: 100 * dim_ranks("community")["USA"] / len(dim_ranks("community")))


@report.finding("X74")
def micro_macro_split():
    r = pd.DataFrame({k: dim_ranks(k) for k in FOUR}).dropna()
    split = r.societal - r[["individual", "household"]].min(axis=1)
    return split.rank(ascending=False, method="min")["USA"]


def us_confidence(item, year=2025):
    return wmean(country(gallup_wave(year, item), "USA"), "yes")


def bottom_share(series, iso="USA"):
    """Position from the bottom as % of countries (rank 1 = lowest)."""
    r = ranks(series, ascending=True)
    return 100 * r[iso] / len(r)


def top_share(series, iso="USA"):
    r = ranks(series)
    return 100 * r[iso] / len(r)


report.finding("X75")(lambda: {"national_government": us_confidence("WP139"), "judiciary": us_confidence("WP138")})
report.finding("X76")(lambda: {k: bottom_share(wmean(gallup_wave(2025, it), "yes", by="COUNTRY_ISO3"))
                               for k, it in [("national_government", "WP139"), ("judiciary", "WP138")]})
report.finding("X77")(lambda: pct(country(d25, "USA"), "gov", [1]))
report.finding("X78")(lambda: bottom_share(country_pct(d25, "gov", [1])))
report.finding("X79")(lambda: {k: pct(country(d25, "USA"), DISC[k], [1])
                               for k in ["religion", "disability", "skin", "nationality", "gender"]})
report.finding("X80")(lambda: {k: top_share(country_pct(d25, DISC[k], [1])) for k in ["religion", "disability"]})
report.finding("X81")(lambda: {k: ranks(country_pct(d25, DISC[k], [1]))["USA"]
                               for k in ["skin", "nationality", "gender"]})


@report.finding("X82")
def us_military():
    a, b = us_confidence("WP137", 2019), us_confidence("WP137", 2025)
    return {"2025": b, "2019": a, "change": rdiff(b, a)}


# --- Chapter 2 (Gallup Life Evaluation Index) ----------------------------------------


@report.finding("X83")
def cover_gaps():
    return {k: rdiff(by_life_eval(k)["thriving"], by_life_eval(k)["suffering"]) for k in FOUR}


report.finding("X84")(lambda: rdiff(by_life_eval("index")["thriving"], by_life_eval("index")["suffering"]))


def chart_2_1_values():
    g = wellbeing()
    t = wmean(g, "index", by=["CountryIncomeLevel", "life_eval"])
    out = {f"{INCOME[i]}_{LE[e]}": v for (i, e), v in t.items() if i in INCOME}
    out.update({f"global_{k}": v for k, v in by_life_eval("index").items()})
    return out


@report.finding("C2_1")
def chart_2_1():
    return chart_2_1_values()


@report.finding("X85")
def smallest_income_gap():
    t = chart_2_1_values()
    return min(rdiff(t[f"{inc}_thriving"], t[f"{inc}_suffering"]) for inc in INCOME.values())


def country_wellbeing():
    g = wellbeing()
    return pd.DataFrame({"thriving": wmean(g, "thriving", by="COUNTRY_ISO3"),
                         "index": wmean(g, "index", by="COUNTRY_ISO3")})


@report.finding("C2_2")
def chart_2_2():  # scatter with no printed values: written to output/ only
    t = country_wellbeing()
    return {f"{c}_{iso}": v for iso, row in t.iterrows() for c, v in row.items()}


@report.finding("X86")
def thriving_correlation():
    t = country_wellbeing().dropna()
    return float(np.corrcoef(t.thriving, t["index"])[0, 1])


report.finding("X87")(lambda: float(country_wellbeing().thriving.dropna().median()))
report.finding("X88")(lambda: float(country_means(d25, "index").dropna().median()))


@report.finding("C2_3")
def chart_2_3_values():  # line chart with no printed values: written to output/ only
    return {f"{inc}_{r}": v for (inc, r), v in chart_2_3().items()}


@report.finding("C2_4")
def chart_2_4():
    return {f"{k}_{e}": v for k in FOUR for e, v in by_life_eval(k).items()}


report.finding("X89")(lambda: by_life_eval("household"))


@report.finding("C2_5")
def chart_2_5():
    g = wellbeing()
    g = g[g.life_eval == 3]
    return {f"{inc}_{k}": v for k in FOUR for inc, v in keyed(wmean(g, k, by="CountryIncomeLevel"), INCOME).items()}


# --- Chapter 3 ---------------------------------------------------------------------


@report.finding("X90")
def cover_dots():
    t = distribution(d25, "gov")  # WP22231_ALL: 99 = don't know or refused
    return {"not_at_all": t[3.0], "dk": t[99.0], "somewhat": t[2.0], "a_lot": t[1.0]}


@report.finding("X91")
def government_care_2021():
    a, b = care(TREND[2021], "government"), care(TREND[2025], "government")
    return {"a_lot_2021": a["a_lot"], "a_lot_change": rdiff(b["a_lot"], a["a_lot"]),
            "somewhat_2021": a["somewhat"], "somewhat_change": rdiff(b["somewhat"], a["somewhat"])}


@report.finding("C3_1")
def chart_3_1():  # 2023 is plotted but not labelled: written to output/ only
    return {f"{who}_{y}_{k}": v for who in WHO for y in TREND for k, v in care(TREND[y], who).items()}


report.finding("X92")(lambda: {"government_under_10": care_gaps("government")["under_10"],
                               "neighbours_not_at_all_higher": care_gaps("neighbours")["not_at_all_higher"],
                               "neighbours_a_lot_higher": care_gaps("neighbours")["a_lot_higher"]})
report.finding("C3_2")(lambda: {f"{who}_{k}": v for who in WHO for k, v in care_gaps(who).items()})
report.finding("X93")(lambda: keyed(pct(d25, "WP22232", [3], by="CountryIncomeLevel"), INCOME))
report.finding("C3_3")(lambda: {f"{who}_{inc}": v for who, var in WHO.items()
                                for inc, v in keyed(pct(d25, var, [3], by="CountryIncomeLevel"), INCOME).items()})


@report.finding("C3_4")
def chart_3_4():
    return keyed(wmean(wellbeing(), "thriving", by="CountryIncomeLevel"), INCOME)


def by_region(who):
    return keyed(pct(d25, WHO[who], [3], by="GlobalRegion"), REGION)


report.finding("X94")(lambda: {f"{who}_{r}": by_region(who)[r] for who, r in [
    ("government", "northern_america"), ("government", "cw_africa"), ("neighbours", "eastern_europe"),
    ("neighbours", "latam"), ("government", "eastern_asia"), ("government", "central_asia"),
    ("neighbours", "southeastern_asia")]})
report.finding("C3_5")(lambda: {f"{who}_{r}": v for who in WHO for r, v in by_region(who).items()})


@report.finding("T3_1")
def table_3_1():
    out = {}
    for who in WHO:
        for i, (isos, v) in enumerate(top10(who), 1):
            out[f"{who}_{i}_country"] = ", ".join(sorted(name(c) for c in isos))
            out[f"{who}_{i}_value"] = v
    return out


def both_lists():
    listed = {who: {c for isos, _ in top10(who) for c in isos} for who in WHO}
    return sorted(listed["government"] & listed["neighbours"])


report.finding("X95")(lambda: len(both_lists()))
report.finding("X96")(lambda: int(d25[d25.COUNTRY_ISO3.isin(both_lists())].drop_duplicates("COUNTRY_ISO3")
                                  .GlobalRegion.eq(5).sum()))
report.finding("X97")(lambda: float(country_pct(d25, "gov", [3])[both_lists()].min()))
report.finding("X98")(lambda: float(country_pct(d25, "WP22232", [3])[both_lists()].min()))
report.finding("X99")(lambda: {f"{who}_{i}": country_pct(d25, WHO[who], [3])[i]
                               for who, i in [("government", "PAN"), ("government", "PRY"),
                                              ("neighbours", "ECU"), ("neighbours", "MEX")]})


@report.finding("C3_6")
def chart_3_6():
    return {f"{inc}_{c}": v for (inc, c), v in household_by_neighbour_care().items()}


report.finding("X100")(lambda: max(household_care_gaps().values()))


if __name__ == "__main__":
    sys.exit(report.run())
