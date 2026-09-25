"""Reproduce World Risk Poll 2024 Focus On: Migration in a warming world.

Run from the repository root:
    python reports/WRP_2023/focus_on_migration_in_a_warming_world/reproduce.py

Chapter 2 describes financial resilience, the greatest risk to safety and
climate change concern in the 2021 and 2023 polls (with 2019 for the climate
trend). Chapters 3 to 5 pool ("blend") the 2021 and 2023 respondents and add
two Gallup World Poll items that are not in the public release: the wish to
move permanently to another country (WP1325) and the preferred destination
country (WP3120). Chapter 5 compares the ND-GAIN climate adaptation score of
the preferred destination with that of the respondent's country. Each
function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, external_path, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

DK = [98, 99]  # don't know, refused: kept in the base
CLIMATE = "WP20719"  # 1 = very serious, 2 = somewhat serious, 3 = not a threat (2019: L5)
RISK = "WP22331"  # greatest source of risk to safety in daily life, coded (2019: L3_A)
MIGRATE = "WP1325"  # Gallup: 1 = would like to move permanently to another country, 2 = continue living here
DESTINATION = "WP3120"  # Gallup: country the respondent would like to move to (Gallup country code, as WP5)
GALLUP = [MIGRATE, DESTINATION]
# Greatest-risk codes: financial (not having enough money) and the general economy, and
# climate change or severe weather. 2019 has no separate climate code: 16 also covers
# earthquakes and other non-weather disasters.
RISK_CODES = {
    2019: {"climate": [16]},
    2021: {"financial": [9], "economy": [10], "climate": [19]},
    2023: {"financial": [9], "economy": [10], "climate": [19]},
}
REGIONS = {  # GlobalRegion codes -> keys
    1: "eastern_africa", 2: "cw_africa", 3: "northern_africa", 4: "southern_africa", 5: "latam",
    6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia", 10: "southern_asia",
    11: "middle_east", 12: "eastern_europe", 13: "nw_europe", 14: "southern_europe", 15: "anz",
}
# Chart 10 groups Africa, Latin America and Eastern Europe as "Other" (10 categories).
OTHER = ["eastern_africa", "cw_africa", "northern_africa", "southern_africa", "latam", "eastern_europe"]
LOW, LOWER_MIDDLE, UPPER_MIDDLE, HIGH = 1, 2, 3, 4  # CountryIncomeLevel

# ND-GAIN Country Index, 2024 release: overall score (0-100), readiness and
# vulnerability (0-1). Not redistributed here; see README for the download.
NDGAIN = "focus_on_migration_in_a_warming_world__ndgain_scores.csv"
NDGAIN_YEAR = 2022
ND_MEASURES = ["gain", "readiness", "vulnerability"]

COLS = ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "CountryIncomeLevel", "INCOME_5", "WP22228", "WP22229",
        RISK, CLIMATE]
d21 = load_wave(2021, COLS).assign(Year=2021)
d23 = load_wave(2023, COLS).assign(Year=2023)
d19 = load_wave(2019, ["COUNTRY_ISO3", "PROJWT", "L3_A", "L5"]).assign(Year=2019)
BY_YEAR = {2019: d19.rename(columns={"L3_A": RISK, "L5": CLIMATE}), 2021: d21, 2023: d23}

# --- Derived variables ---------------------------------------------------------

# Basic needs without income (Chart 1): WP22228 (less than a month / a month
# or more) with the follow-up WP22229 (weeks). 1 = less than a week, 2 = less
# than a month but a week or more (including don't know on the follow-up),
# 3 = don't know/refused, 4 = a month or more.
for df in (d21, d23):
    df["needs"] = np.select(
        [df.WP22229.eq(1), df.WP22228.eq(1), df.WP22228.isin(DK), df.WP22228.eq(2)], [1, 2, 3, 4], np.nan)

# The blended file (Chapters 3-5): 2021 and 2023 respondents pooled, weighted
# by PROJWT. WPID_RANDOM does not repeat across the two waves.
b = pd.concat([d21, d23], ignore_index=True)
# climate3: 1 very, 2 somewhat, 3 not a threat (DK/refused -> missing).
b["climate3"] = b[CLIMATE].where(b[CLIMATE].isin([1, 2, 3]))
# threat: 1 = a threat (very or somewhat serious), 2 = not a threat (Charts 8, 10).
b["threat"] = b.climate3.map({1: 1, 2: 1, 3: 2})
# very_not: 1 = very serious, 2 = not a threat; somewhat serious left out (Chapter 5).
b["very_not"] = b.climate3.map({1: 1, 3: 2})
# fin: 1 = less than a month, 2 = a month or more (DK/refused -> missing).
b["fin"] = b.WP22228.where(b.WP22228.isin([1, 2]))

# Destination lookup: Gallup country code (WP5) -> ISO3 and GlobalRegion, from
# every wave of the poll (148 countries; each country keeps its 2023 region).
# WP3120 is assumed to use the same country codes; destinations outside the
# poll's countries, and don't know/refused, are left out.
lookup = pd.concat([load_wave(y, ["WP5", "COUNTRY_ISO3", "GlobalRegion"]).drop_duplicates()
                    for y in (2023, 2025, 2021, 2019)]).drop_duplicates("WP5").set_index("WP5")
DEST_ISO3 = lookup["COUNTRY_ISO3"]
DEST_REGION = lookup["GlobalRegion"].map(REGIONS)

# --- Helpers -------------------------------------------------------------------


def risk(year, key):
    """% naming a greatest-risk category in `year` (all countries surveyed that year)."""
    return pct(BY_YEAR[year], RISK, RISK_CODES[year][key])


@lru_cache(maxsize=None)
def _migrants():
    g = merge_gallup(b, GALLUP)
    m = g[g[MIGRATE].eq(1)].copy()
    m["dest_region"] = m[DESTINATION].map(DEST_REGION)
    m["dest_iso3"] = m[DESTINATION].map(DEST_ISO3)
    m["dest10"] = m.dest_region.where(~m.dest_region.isin(OTHER), "other")
    return m[m.dest_region.notna()]


def migrants():
    """Blended respondents who would like to move, with their destination region and ISO3."""
    return _migrants().copy()


@lru_cache(maxsize=None)
def _ndgain_gaps():
    m = migrants()
    nd = pd.read_csv(external_path(NDGAIN))
    nd = nd[nd.year == NDGAIN_YEAR].set_index("ISO3")[ND_MEASURES]
    for x in ND_MEASURES:
        m[f"gap_{x}"] = m.dest_iso3.map(nd[x]) - m.COUNTRY_ISO3.map(nd[x])
    return m[m[[f"gap_{x}" for x in ND_MEASURES]].notna().all(axis=1)]


def ndgain_gaps():
    """Migrants with the ND-GAIN gaps (destination minus origin) for each measure."""
    return _ndgain_gaps().copy()


def shares(m, group, groups, cat="dest_region"):
    """% of each group's destinations in each category (rows sum to 100): {'<group>_<cat>': %}."""
    t = distribution(m[m[group].notna()], cat, by=group)
    return {f"{groups[int(k)]}_{c}": v for k, row in t.iterrows() for c, v in row.items()}


def crosstab_tests(m, group, groups, cat="dest_region"):
    """Chi-square, df, Cramer's V and adjusted standardised residuals of `group` by `cat`.

    Counts are weighted by PROJWT rescaled to the sample size, so the weighted
    table has the same total as the number of respondents.
    """
    m = m[m[group].notna() & m[cat].notna()]
    w = m.PROJWT * len(m) / m.PROJWT.sum()
    obs = w.groupby([m[group], m[cat]]).sum().unstack(fill_value=0)
    n = obs.values.sum()
    row, col = obs.sum(axis=1), obs.sum(axis=0)
    exp = np.outer(row, col) / n
    chi2 = ((obs.values - exp) ** 2 / exp).sum()
    k = min(obs.shape) - 1
    adj = (obs.values - exp) / np.sqrt(exp * np.outer(1 - row / n, 1 - col / n))
    out = {"chi2": chi2, "df": (obs.shape[0] - 1) * (obs.shape[1] - 1), "cramers_v": np.sqrt(chi2 / (n * k))}
    for i, gk in enumerate(obs.index):
        for j, c in enumerate(obs.columns):
            out[f"resid_{groups[int(gk)]}_{c}"] = adj[i, j]
    return out


def svy_lm(m, y, terms):
    """Survey-weighted linear regression of `y` on `terms` (a dict name -> 0/1 or numeric Series).

    PROJWT weights; linearisation (sandwich) standard errors for a design with
    weights only (HC0 x n/(n-1), as survey::svyglm), p-values from t(n - p).
    Returns a DataFrame with coef and p, indexed by term name.
    """
    X = sm.add_constant(pd.DataFrame(terms, index=m.index).astype(float), has_constant="add")
    fit = sm.WLS(m[y], X, weights=m.PROJWT).fit(cov_type="HC0")
    n, p = X.shape
    se = np.sqrt(np.diag(fit.cov_params()) * n / (n - 1))
    tval = fit.params / se
    return pd.DataFrame({"coef": fit.params, "p": 2 * stats.t.sf(np.abs(tval), n - p)})


def dummies(s, levels, prefix):
    """0/1 columns for each of `levels` of `s` (the reference level is left out)."""
    return {f"{prefix}{lv}": s.eq(lv).astype(float) for lv in levels}


def income_model(m, interaction):
    """Chart 14 model: income group, income quintile, climate concern, financial resilience.

    Sample: very serious or not a threat, a financial resilience answer, a
    classified income group and an income quintile. With `interaction`, very
    serious (reference: not a threat) is interacted with the income group,
    so the income-group coefficients are those for people who do not see
    climate change as a threat.
    """
    m = m[m.very_not.notna() & m.fin.notna() & m.CountryIncomeLevel.isin([1, 2, 3, 4]) & m.INCOME_5.notna()]
    terms = {**dummies(m.CountryIncomeLevel, [LOWER_MIDDLE, UPPER_MIDDLE, HIGH], "income"),
             **dummies(m.INCOME_5, [2, 3, 4, 5], "quintile"),
             "month_or_more": m.fin.eq(2).astype(float)}
    if interaction:
        very = m.very_not.eq(1).astype(float)
        terms["very_serious"] = very
        for lv in [LOWER_MIDDLE, UPPER_MIDDLE, HIGH]:
            terms[f"very_serious_x_income{lv}"] = very * m.CountryIncomeLevel.eq(lv)
    else:
        terms["not_a_threat"] = m.very_not.eq(2).astype(float)
    return svy_lm(m, "gap_gain", terms)


# --- Key findings and introduction (pages 2-3) -------------------------------------------


@report.finding("X01")
def economic_rank():
    # Rank among the substantive categories (codes 1-21, leaving out other,
    # nothing, DK and refused), with financial (9) and the general economy (10)
    # combined.
    share = distribution(d23, RISK)
    share = share[[c for c in share.index if 1 <= c <= 21]]
    combined = share[[9, 10]].sum()
    return 1 + int((share.drop([9, 10]) > combined).sum())


@report.finding("X02")
def less_than_month_2023():
    return pct(d23, "needs", [1, 2])


@report.finding("X03")
def climate_risk_2023():
    return risk(2023, "climate")


@report.finding("X04")
def climate_risk_peak_year():
    return max([2019, 2021, 2023], key=lambda y: risk(y, "climate"))


@report.finding("X05")
def migrate_ratio_very():
    g = merge_gallup(b[b.climate3.notna()], [MIGRATE])
    return pct(g[g.climate3.eq(1)], MIGRATE, [1]) / pct(g[g.climate3.isin([2, 3])], MIGRATE, [1])


@report.finding("X06")
def countries_2023():
    return d23.COUNTRY_ISO3.nunique()


# --- 2.1 Economic insecurity (page 4) -----------------------------------------------------


@report.finding("X07")
def week_2023():
    return pct(d23, "needs", [1])


@report.finding("X08")
def week_2021():
    return pct(d21, "needs", [1])


@report.finding("X09")
def month_2023():
    return pct(d23, "needs", [2])


@report.finding("X10")
def month_2021():
    return pct(d21, "needs", [2])


@report.finding("X11")
def more_2021():
    return pct(d21, "needs", [4])


@report.finding("X12")
def more_2023():
    return pct(d23, "needs", [4])


@report.finding("X13")
def financial_2021():
    return risk(2021, "financial")


@report.finding("X14")
def financial_2023():
    return risk(2023, "financial")


@report.finding("X15")
def economy_2021():
    return risk(2021, "economy")


@report.finding("X16")
def economy_2023():
    return risk(2023, "economy")


@report.finding("X17")
def financial_or_economy_2023():
    return pct(d23, RISK, RISK_CODES[2023]["financial"] + RISK_CODES[2023]["economy"])


@report.finding("C2_1")
def chart1():
    keys = {1: "week", 2: "month", 3: "dk", 4: "more"}
    out = {}
    for year, df in ((2021, d21), (2023, d23)):
        for code, v in distribution(df, "needs").items():
            out[f"{keys[int(code)]}_{year}"] = v
    return out


@report.finding("C2_2")
def chart2():
    return {f"{name}_{y}": risk(y, key) for name, key in (("personal_finances", "financial"), ("economy", "economy"))
            for y in (2021, 2023)}


# --- 2.2 Climate risk (page 5) --------------------------------------------------------------


@report.finding("X18")
def very_2019():
    return pct(BY_YEAR[2019], CLIMATE, [1])


@report.finding("X19")
def very_2021():
    return pct(d21, CLIMATE, [1])


@report.finding("X20")
def very_2023():
    return pct(d23, CLIMATE, [1])


@report.finding("X21")
def somewhat_2019():
    return pct(BY_YEAR[2019], CLIMATE, [2])


@report.finding("X22")
def somewhat_2023():
    return pct(d23, CLIMATE, [2])


@report.finding("X23")
def dk_2019():
    return pct(BY_YEAR[2019], CLIMATE, DK)


@report.finding("X24")
def dk_2023():
    return pct(d23, CLIMATE, DK)


@report.finding("X25")
def not_2019():
    return pct(BY_YEAR[2019], CLIMATE, [3])


@report.finding("X26")
def not_2023():
    return pct(d23, CLIMATE, [3])


@report.finding("X27")
def climate_risk_2019():
    return risk(2019, "climate")


@report.finding("X28")
def climate_risk_2021():
    return risk(2021, "climate")


@report.finding("C2_3")
def chart3():
    cats = {"very": [1], "somewhat": [2], "dk": DK, "not": [3]}
    return {f"{k}_{y}": pct(BY_YEAR[y], CLIMATE, codes) for k, codes in cats.items() for y in (2019, 2021, 2023)}


@report.finding("C2_4")
def chart4():
    return {str(y): risk(y, "climate") for y in (2021, 2023)}


# --- 3. Who wants to leave (pages 6-7): Gallup WP1325 ------------------------------------


def migrate_by(group, groups):
    g = merge_gallup(b[b[group].notna()], [MIGRATE])
    r = pct(g, MIGRATE, [1], by=group)
    return {groups[int(k)]: v for k, v in r.items()}


CLIMATE3 = {1: "very", 2: "somewhat", 3: "not"}
FIN = {1: "less", 2: "more"}


@report.finding("C3_5")
def chart5():
    return migrate_by("climate3", CLIMATE3)


@report.finding("X29")
def migrate_very():
    return migrate_by("climate3", CLIMATE3)["very"]


@report.finding("X30")
def migrate_somewhat_or_not():
    g = merge_gallup(b[b.climate3.isin([2, 3])], [MIGRATE])
    return pct(g, MIGRATE, [1])


@report.finding("X31")
def stay_lowest():
    g = merge_gallup(b[b.climate3.notna()], [MIGRATE])
    return pct(g, MIGRATE, [2], by="climate3").min()


@report.finding("X32")
def migrate_more():
    return migrate_by("fin", FIN)["more"]


@report.finding("X33")
def migrate_less():
    return migrate_by("fin", FIN)["less"]


@report.finding("C3_6")
def chart6():
    return migrate_by("fin", FIN)


def chart7_values():
    g = merge_gallup(b[b.climate3.notna() & b.fin.notna()], [MIGRATE])
    r = pct(g, MIGRATE, [1], by=["climate3", "fin"])
    return {f"{CLIMATE3[int(c)]}_{FIN[int(f)]}": v for (c, f), v in r.items()}


@report.finding("C3_7")
def chart7():
    return chart7_values()


@report.finding("X34")
def migrate_very_more():
    return chart7_values()["very_more"]


@report.finding("X35")
def migrate_very_less():
    return chart7_values()["very_less"]


@report.finding("X36")
def migrate_not_more():
    return chart7_values()["not_more"]


@report.finding("X37")
def migrate_not_less():
    return chart7_values()["not_less"]


@report.finding("X38")
def migrate_not_ratio():
    v = chart7_values()
    return v["not_less"] / v["not_more"]


# --- 4. Where people want to go (pages 9-11): Gallup WP1325 and WP3120 --------------------

THREAT = {1: "threat", 2: "not"}
# Chart 10 groups: financial resilience x climate concern.
GROUP4 = {1: "less_threat", 2: "less_not", 3: "more_threat", 4: "more_not"}


def four_groups(m):
    return (m.fin - 1) * 2 + m.threat


def chart8_values():
    m = migrants()
    return {**shares(m, "threat", THREAT), **crosstab_tests(m, "threat", THREAT)}


def chart9_values():
    m = migrants()
    return {**shares(m, "fin", FIN), **crosstab_tests(m, "fin", FIN)}


def chart10_values():
    m = migrants()
    m["group4"] = four_groups(m)
    return {**shares(m, "group4", GROUP4, "dest10"), **crosstab_tests(m, "group4", GROUP4, "dest10")}


@report.finding("C4_8")
def chart8():
    return chart8_values()


def c8(key):
    return chart8_values()[key]


@report.finding("X39")
def namerica_threat():
    return c8("threat_northern_america")


@report.finding("X40")
def namerica_not():
    return c8("not_northern_america")


@report.finding("X41")
def namerica_gap():
    v = chart8_values()
    return v["threat_northern_america"] - v["not_northern_america"]


@report.finding("X42")
def largest_gap_region():
    v = chart8_values()
    return max(REGIONS.values(), key=lambda r: abs(v.get(f"threat_{r}", 0) - v.get(f"not_{r}", 0)))


@report.finding("X43")
def largest_fall_region():
    v = chart8_values()
    return max(REGIONS.values(), key=lambda r: v.get(f"not_{r}", 0) - v.get(f"threat_{r}", 0))


@report.finding("X44")
def middle_east_not():
    return c8("not_middle_east")


@report.finding("X45")
def middle_east_threat():
    return c8("threat_middle_east")


@report.finding("X46")
def nw_europe_threat():
    return c8("threat_nw_europe")


@report.finding("X47")
def nw_europe_not():
    return c8("not_nw_europe")


@report.finding("X48")
def se_asia_not():
    return c8("not_southeastern_asia")


@report.finding("X49")
def se_asia_threat():
    return c8("threat_southeastern_asia")


@report.finding("X50")
def anz_threat():
    return c8("threat_anz")


@report.finding("X51")
def anz_not():
    return c8("not_anz")


@report.finding("C4_9")
def chart9():
    return chart9_values()


def text9(key):
    return lambda: chart9_values()[key]


for fid, key in [("X52", "more_nw_europe"), ("X53", "less_nw_europe"), ("X54", "more_anz"), ("X55", "less_anz"),
                 ("X56", "more_middle_east"), ("X57", "less_middle_east"), ("X58", "less_southern_asia"),
                 ("X59", "more_southern_asia"), ("X60", "more_northern_america"), ("X61", "less_northern_america")]:
    report.finding(fid)(text9(key))


@report.finding("C4_10")
def chart10():
    return chart10_values()


def text10(key):
    return lambda: chart10_values()[key]


for fid, key in [("X62", "less_not_middle_east"), ("X63", "less_not_southeastern_asia"),
                 ("X64", "less_threat_middle_east"), ("X65", "less_threat_southeastern_asia"),
                 ("X66", "less_not_northern_america"), ("X67", "less_threat_northern_america")]:
    report.finding(fid)(text10(key))


@report.finding("X68")
def namerica_less_gap():
    v = chart10_values()
    return v["less_threat_northern_america"] - v["less_not_northern_america"]


for fid, key in [("X69", "less_not_nw_europe"), ("X70", "less_threat_nw_europe"), ("X71", "more_not_nw_europe"),
                 ("X72", "more_threat_nw_europe"), ("X73", "more_threat_northern_america"),
                 ("X74", "more_not_northern_america"), ("X75", "more_not_anz"), ("X76", "more_threat_anz"),
                 ("X77", "more_not_middle_east"), ("X78", "more_threat_middle_east"),
                 ("X79", "more_not_southeastern_asia"), ("X80", "more_threat_southeastern_asia")]:
    report.finding(fid)(text10(key))


# --- 5. ND-GAIN gaps (pages 12-16): Gallup WP1325, WP3120 and ND-GAIN -----------------------

VERY_NOT = {1: "very", 2: "not"}


def nd_means(group, groups):
    """Mean ND-GAIN gaps by group: {'<measure>_<group>': mean}."""
    m = ndgain_gaps()
    m = m[m[group].notna()]
    return {f"{x}_{groups[int(k)]}": v for x in ND_MEASURES
            for k, v in wmean(m, f"gap_{x}", by=group).items()}


def chart11_values():
    return nd_means("very_not", VERY_NOT)


def chart12_values():
    return nd_means("fin", FIN)


def chart13_values():
    m = ndgain_gaps()
    m = m[m.very_not.notna() & m.fin.notna()]
    return {f"{x}_{VERY_NOT[int(c)]}_{FIN[int(f)]}": v for x in ND_MEASURES
            for (c, f), v in wmean(m, f"gap_{x}", by=["very_not", "fin"]).items()}


def model11():
    m = ndgain_gaps()
    m = m[m.very_not.notna()]
    return svy_lm(m, "gap_gain", {"not_a_threat": m.very_not.eq(2)})


def model12():
    m = ndgain_gaps()
    m = m[m.fin.notna()]
    return svy_lm(m, "gap_gain", {"month_or_more": m.fin.eq(2)})


def model13():
    m = ndgain_gaps()
    m = m[m.very_not.notna() & m.fin.notna()]
    not_, more = m.very_not.eq(2).astype(float), m.fin.eq(2).astype(float)
    return svy_lm(m, "gap_gain", {"not_a_threat": not_, "month_or_more": more, "interaction": not_ * more})


@report.finding("C5_11a")
def chart11a():
    v = chart11_values()
    return {"very": v["gain_very"], "not": v["gain_not"]}


@report.finding("C5_11b")
def chart11b():
    return {k: v for k, v in chart11_values().items() if not k.startswith("gain")}


@report.finding("X81")
def gap_very():
    return chart11_values()["gain_very"]


@report.finding("X82")
def gap_not():
    return chart11_values()["gain_not"]


@report.finding("X83")
def gap_very_minus_not():
    v = chart11_values()
    return v["gain_very"] - v["gain_not"]


@report.finding("X84")
def coef_not_threat():
    return model11().loc["not_a_threat", "coef"]


@report.finding("X85")
def p_not_threat():
    return model11().loc["not_a_threat", "p"]


for fid, key in [("X86", "readiness_very"), ("X87", "readiness_not"), ("X88", "vulnerability_very"),
                 ("X89", "vulnerability_not")]:
    report.finding(fid)((lambda k: lambda: chart11_values()[k])(key))


@report.finding("C5_12a")
def chart12a():
    v = chart12_values()
    return {"less": v["gain_less"], "more": v["gain_more"], "p": model12().loc["month_or_more", "p"]}


@report.finding("C5_12b")
def chart12b():
    return {k: v for k, v in chart12_values().items() if not k.startswith("gain")}


@report.finding("X90")
def gap_less():
    return chart12_values()["gain_less"]


@report.finding("X91")
def gap_more():
    return chart12_values()["gain_more"]


@report.finding("X92")
def gap_less_minus_more():
    v = chart12_values()
    return v["gain_less"] - v["gain_more"]


@report.finding("X93")
def coef_month_or_more():
    return model12().loc["month_or_more", "coef"]


@report.finding("X94")
def p_month_or_more():
    return model12().loc["month_or_more", "p"]


for fid, key in [("X95", "readiness_less"), ("X96", "readiness_more"), ("X97", "vulnerability_less"),
                 ("X98", "vulnerability_more")]:
    report.finding(fid)((lambda k: lambda: chart12_values()[k])(key))


@report.finding("C5_13a")
def chart13a():
    return {k[len("gain_"):]: v for k, v in chart13_values().items() if k.startswith("gain_")}


@report.finding("C5_13b")
def chart13b():
    return {k: v for k, v in chart13_values().items() if not k.startswith("gain")}


@report.finding("X99")
def gap_very_less():
    return chart13_values()["gain_very_less"]


@report.finding("X100")
def gap_not_more():
    return chart13_values()["gain_not_more"]


@report.finding("X101")
def coef_interaction():
    return model13().loc["interaction", "coef"]


@report.finding("X102")
def p_interaction():
    return model13().loc["interaction", "p"]


for fid, key in [("X103", "readiness_very_less"), ("X104", "readiness_not_less"), ("X105", "readiness_very_more"),
                 ("X106", "readiness_not_more"), ("X108", "vulnerability_very_less")]:
    report.finding(fid)((lambda k: lambda: chart13_values()[k])(key))


@report.finding("X107")
def largest_readiness_group():
    v = chart13_values()
    return max(["very_less", "very_more", "not_less", "not_more"], key=lambda g: v[f"readiness_{g}"])


def other_vulnerability():
    v = chart13_values()
    return [v[f"vulnerability_{g}"] for g in ("very_more", "not_less", "not_more")]


@report.finding("X109")
def other_vulnerability_highest():
    return max(other_vulnerability())


@report.finding("X110")
def other_vulnerability_lowest():
    return min(other_vulnerability())


@report.finding("C5_14")
def chart14():
    # No values are printed on the chart: coefficients of the main-effects model.
    return income_model(ndgain_gaps(), interaction=False)["coef"].drop("const")


def model14_text():
    return income_model(ndgain_gaps(), interaction=True)


@report.finding("X111")
def coef_lower_middle():
    return model14_text().loc[f"income{LOWER_MIDDLE}", "coef"]


@report.finding("X112")
def coef_upper_middle():
    return model14_text().loc[f"income{UPPER_MIDDLE}", "coef"]


@report.finding("X113")
def coef_high():
    return model14_text().loc[f"income{HIGH}", "coef"]


@report.finding("X114")
def coef_upper_middle_very():
    return model14_text().loc[f"very_serious_x_income{UPPER_MIDDLE}", "coef"]


@report.finding("X115")
def p_upper_middle_very():
    return model14_text().loc[f"very_serious_x_income{UPPER_MIDDLE}", "p"]


if __name__ == "__main__":
    sys.exit(report.run())
