"""Reproduce World Risk Poll 2026: After the storm: How disasters reshape resilience and trust.

Run from the repository root:
    python reports/WRP_2025/core_after_the_storm/reproduce.py

The report follows seven disasters that struck between the 2021 and 2023 waves.
In each country, respondents in the regions the disaster struck ("affected
regions", A = 1) are compared with the rest of the country, and the change in
the rest of the country is subtracted from the change in the affected regions
(a difference-in-differences, Chapters 2 and 3). Four of the seven are followed
into 2025 (Chapter 4). Estimates are weighted least squares with PROJWT and
HC1 standard errors (95% intervals are the estimate +/- 1.96 SE); the pooled
models rescale the weight so that every country and wave counts equally.

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

# --- Variables -------------------------------------------------------------------

DIMS = {"index": "resilience_index_100", "societal": "resilience_soc", "community": "resilience_com",
        "household": "resilience_hhl", "individual": "resilience_idv"}
CARES = "WP22231"        # government cares about you and your wellbeing: 1 a lot, 2 somewhat, 3 not at all
NEIGHBOURS = "WP22232"   # neighbours care about you and your wellbeing: 1 a lot, 2 somewhat, 3 not at all
PROTECT = "WP22252"      # could protect yourself and your family in a future disaster: 1 yes, 2 no, 3 it depends
EXPOSURE = {2021: "WP22245", 2023: "WP23344", 2025: "WP24213"}  # experienced (2021, 2023) / impacted by (2025) a disaster
TYPE = {2023: "WP22247", 2025: "WP24180"}                         # type of disaster: 1 flood, 2 tropical storm, 7 earthquake
PREPARED = {2021: "WP22241", 2025: "WP24198"}  # national government well prepared for a disaster: 1 yes
LOCAL_PREPARED = "WP24199"                     # local government well prepared, 2025: 1 yes
WORRY = "worry_index_published"                # Worry Index, 2025 (0 to 1)
CONFIDENCE = "WP139"     # Gallup World Poll: confidence in national government (1 = yes)
PSU, STRATA = "WP12259", "WP12258"  # Gallup World Poll: primary sampling unit and stratum
MEASURES = ["index", "societal", "community", "household", "individual", "confidence", "cares", "neighbours", "protect"]
Z = 1.96

# Case studies in the order of the charts (months from the disaster to the 2023 fieldwork).
CASES = ["MAR", "ECU", "MOZ", "NZL", "TUR", "PAK", "ZAF"]
MONTHS = {"MAR": 1, "ECU": 5, "MOZ": 6, "NZL": 7, "TUR": 10, "PAK": 14, "ZAF": 22}
CONF_CASES = ["ECU", "MOZ", "NZL", "TUR", "ZAF"]  # confidence was not asked in Morocco or Pakistan
RECOVERY = ["MAR", "TUR", "NZL"]                   # followed into 2025 as recovery; South Africa is the repeat hit
OTHERS = ["THA", "PHL", "LBN"]                     # no single disaster footprint (Chart 3.6)

# Region variable for each case and wave. None: not in the public release, so the
# region comes from the Gallup World Poll item in GALLUP_REGION.
REGION_VAR = {
    "MAR": {2021: "REGION_MAR", 2023: "REGION3_MAR", 2025: "REGION3_MAR"},
    "ECU": {2021: "REGION_ECU", 2023: "REGION_ECU"},
    "MOZ": {2021: "REGION_MOZ", 2023: "REGION_MOZ"},
    "NZL": {2021: "REGION_NZL", 2023: "REGION_NZL", 2025: None},
    "TUR": {2021: "REGION3_TUR", 2023: "REGION3_TUR", 2025: "REGION3_TUR"},
    "PAK": {2021: "REGION_PAK", 2023: "REGION_PAK"},
    "ZAF": {2021: None, 2023: "REGION_ZAF", 2025: "REGION_ZAF"},
}
GALLUP_REGION = {"NZL": "REGION_NZL", "ZAF": "REGION_ZAF"}
AFFECTED = {"MAR": [7], "ECU": [6, 8], "MOZ": [4, 8, 10], "NZL": [1, 2], "TUR": [6, 11], "PAK": [1], "ZAF": [4]}
# Regions the disaster also reached outside the affected regions: removed from both groups
# in the adjusted estimates of Tables A.3 and A.4.
ALSO_REACHED = {"TUR": [12], "NZL": [3, 4, 5, 6]}

# Morocco 2021 codes provinces (REGION_MAR); 2023 and 2025 code the 12 regions (REGION3_MAR).
MAR_PROVINCES = {1: [54, 57, 58, 59, 60, 61, 68, 72], 2: [27, 28, 29, 30, 31, 32, 66, 75],
                 3: [45, 46, 48, 50, 51, 52, 53, 55, 56], 4: [17, 18, 37, 38, 39, 40, 70], 5: [20, 43, 44, 49, 67],
                 6: [19, 21, 33, 34, 35, 36, 41, 63, 64], 7: [22, 23, 24, 25, 26, 42, 65, 71], 8: [13, 16, 47, 62, 73],
                 9: [9, 10, 11, 12, 14, 15], 10: [5, 7, 8, 69], 11: [3, 4, 6, 74], 12: [1, 2]}
MAR_PROVINCE_REGION = {p: r for r, ps in MAR_PROVINCES.items() for p in ps}
MAR_REGIONS = {1: "tanger", 2: "oriental", 3: "fes_meknes", 4: "rabat", 5: "beni_mellal", 6: "casablanca_settat",
               7: "marrakech_safi", 8: "draa", 9: "souss_massa", 10: "guelmim", 11: "laayoune", 12: "dakhla"}
TUR_REGIONS = {1: "istanbul", 2: "west_marmara", 3: "aegean", 4: "east_marmara", 5: "west_anatolia", 6: "mediterranean",
               7: "central_anatolia", 8: "west_black_sea", 9: "east_black_sea", 10: "ne_anatolia", 11: "cea",
               12: "southeast_anatolia"}
NZL_REGIONS = {1: "northland", 2: "auckland", 3: "waikato", 4: "bay_of_plenty", 5: "east_cape", 6: "hawkes_bay", 7: "taranaki",
               8: "manawatu", 9: "wellington", 10: "tasman", 11: "nelson", 12: "marlborough", 13: "west_coast", 14: "canterbury",
               15: "otago", 16: "southland"}
ZAF_REGIONS = {1: "Eastern Cape", 2: "Free State", 3: "Gauteng", 4: "KwaZulu-Natal", 5: "Limpopo", 6: "Mpumalanga",
               7: "North West", 8: "Northern Cape", 9: "Western Cape"}
# Türkiye NUTS-2 units (REGION_TUR): the officially affected units inside the two affected
# regions, and the eight provinces with no 2023 respondents (TR63, TRC1, TRC2).
TUR_AFFECTED_UNITS = [12, 13, 22]   # TR62 Adana, TR63 Hatay, TRB1 Malatya
TUR_NO_2023 = [13, 24, 25]          # TR63 Hatay, TRC1 Gaziantep, TRC2 Sanliurfa
TR62, TR63, TRC3 = 12, 13, 26
NZ_HAWKES_BAY, SE_ANATOLIA = 6, 12
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}

# --- Data ------------------------------------------------------------------------

BASE = ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", *DIMS.values(), CARES, NEIGHBOURS, PROTECT]
WAVE_COLS = {
    2021: [EXPOSURE[2021], PREPARED[2021], "REGION_MAR", "REGION_ECU", "REGION_MOZ", "REGION_NZL", "REGION3_TUR", "REGION_TUR",
           "REGION_PAK"],
    2023: [EXPOSURE[2023], TYPE[2023], "REGION3_MAR", "REGION_ECU", "REGION_MOZ", "REGION_NZL", "REGION3_TUR", "REGION_TUR",
           "REGION_PAK", "REGION_ZAF"],
    2025: [EXPOSURE[2025], TYPE[2025], PREPARED[2025], LOCAL_PREPARED, WORRY, "REGION3_MAR", "REGION3_TUR", "REGION_ZAF"],
}


def yes100(s, code=1):
    """0/100 indicator of `code`, missing where the question was not asked (DK and refused stay in the base)."""
    return np.where(s.isna(), np.nan, 100.0 * (s == code))


def prepare(d):
    for key, var in DIMS.items():
        d[key] = d[var] if key == "index" else 100 * d[var]
    for key, var in (("cares", CARES), ("neighbours", NEIGHBOURS), ("protect", PROTECT)):
        if var in d:
            d[key] = yes100(d[var])
    return d


WAVE = {}
for _year, _cols in WAVE_COLS.items():
    _d = load_wave(_year, BASE + _cols)
    _d = prepare(_d[_d.COUNTRY_ISO3.isin(CASES + OTHERS)].copy())
    _d["wave"] = _year
    _d["exposure"] = yes100(_d[EXPOSURE[_year]])
    if _year in PREPARED:
        _d["prepared"] = yes100(_d[PREPARED[_year]])
    if _year == 2025:
        _d["local_prepared"] = yes100(_d[LOCAL_PREPARED])
        _d["worry"] = 100 * _d[WORRY]
    WAVE[_year] = _d


def r0(x):
    """Round half up, as the report does."""
    return float(np.floor(x + 0.5 + 1e-9))


def case_data(iso, years, gallup=()):
    """Respondents of one case study, with `region`, `A` (1 = affected region) and `wave`.

    Region don't know / refused are left out, except Morocco 2021, where the seven
    respondents who gave no province stay in the rest of the country.
    """
    frames = []
    for year in years:
        d = WAVE[year][WAVE[year].COUNTRY_ISO3 == iso].copy()
        var = REGION_VAR[iso].get(year)
        if var is None:
            var = GALLUP_REGION[iso]
            d = merge_gallup(d, [var])
        if iso == "MAR" and year == 2021:
            d["region"] = d[var].map(MAR_PROVINCE_REGION)
        else:
            d["region"] = d[var]
            d = d[d.region.notna() & ~d.region.isin([98, 99])]
        d["A"] = d.region.isin(AFFECTED[iso]).astype(int)
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    if gallup:
        d = merge_gallup(d, list(gallup))
    if CONFIDENCE in d:
        d["confidence"] = yes100(d[CONFIDENCE])
    return d


def with_confidence(d):
    d = merge_gallup(d, [CONFIDENCE])
    d["confidence"] = yes100(d[CONFIDENCE])
    return d


# --- Estimation ------------------------------------------------------------------

def wls(y, X, w, cluster=None):
    """Weighted least squares; HC1 variance, or CR1 when `cluster` is given."""
    XtW = X.T * w
    bread = np.linalg.inv(XtW @ X)
    b = bread @ (XtW @ y)
    u = X * (w * (y - X @ b))[:, None]
    n, k = X.shape
    if cluster is None:
        V = bread @ (u.T @ u) @ bread * n / (n - k)
    else:
        S = pd.DataFrame(u).groupby(pd.Series(cluster).astype(str).values).sum().values  # a missing region is its own cluster
        G = len(S)
        V = bread @ (S.T @ S) @ bread * G / (G - 1) * (n - 1) / (n - k)
    return b, V


def ci(est, var):
    se = np.sqrt(var)
    return est, est - Z * se, est + Z * se


def did(d, y, waves=(2021, 2023), cluster=None):
    """Affected-region change minus rest-of-country change: (estimate, lower, upper)."""
    d = d[d[y].notna() & d.wave.isin(waves)]
    T = (d.wave == waves[1]).astype(float).values
    A = d.A.values.astype(float)
    X = np.column_stack([np.ones(len(d)), A, T, A * T])
    b, V = wls(d[y].values, X, d.PROJWT.values, None if cluster is None else d[cluster].values)
    return ci(b[3], V[3, 3])


def changes(d, y, waves=(2021, 2023)):
    """(change in the affected regions, change in the rest of the country, gap)."""
    m = wmean(d, y, by=["A", "wave"])
    aff, rest = m[(1, waves[1])] - m[(1, waves[0])], m[(0, waves[1])] - m[(0, waves[0])]
    return aff, rest, aff - rest


def gap_model(d, y, cluster=None):
    """Gap (affected minus rest) at each wave and the change from 2023 to 2025, HC1."""
    d = d[d[y].notna()]
    waves = sorted(d.wave.unique())
    A = d.A.values.astype(float)
    T = [(d.wave == w).astype(float).values for w in waves[1:]]
    X = np.column_stack([np.ones(len(d)), A, *T, *[A * t for t in T]])
    b, V = wls(d[y].values, X, d.PROJWT.values, None if cluster is None else d[cluster].values)
    k = len(T)
    out = {f"gap_{waves[0]}": b[1]}
    for i, w in enumerate(waves[1:]):
        out[f"gap_{w}"] = b[1] + b[2 + k + i]
    if waves == [2021, 2023, 2025]:
        c = np.zeros(len(b))
        c[2 + k + 1], c[2 + k] = 1, -1
        out["change"], out["lo"], out["hi"] = ci(c @ b, c @ V @ c)
    return out


def pooled(frames, y, terms, cluster=None):
    """Pooled model: country-by-wave and country-by-affected effects plus `terms`.

    frames: case data stacked (with `iso`). terms: {name: column builder}. The weight
    is rescaled to sum to one within each country and wave. Returns (b, V) for terms.
    """
    d = pd.concat(frames, ignore_index=True)
    d = d[d[y].notna()].copy()
    d["w"] = d.PROJWT / d.groupby(["iso", "wave"]).PROJWT.transform("sum")
    cw = pd.get_dummies(d.iso + "_" + d.wave.astype(str), dtype=float)
    ca = pd.get_dummies(d.iso, dtype=float).mul(d.A, axis=0)
    extra = np.column_stack([f(d) for f in terms.values()])
    X = np.column_stack([cw.values, ca.values, extra])
    cl = None if cluster is None else cluster(d)
    b, V = wls(d[y].values, X, d.w.values, cl)
    k = extra.shape[1]
    return b[-k:], V[-k:, -k:]


def stacked(cases, years, gallup=(), drop_also_reached=False):
    frames = []
    for iso in cases:
        d = case_data(iso, years)
        if drop_also_reached:
            d = d[~d.region.isin(ALSO_REACHED.get(iso, []))]
        frames.append(d.assign(iso=iso))
    if gallup:
        frames = [merge_gallup(f, list(gallup)) for f in frames]
    if CONFIDENCE in gallup:
        frames = [f.assign(confidence=yes100(f[CONFIDENCE])) for f in frames]
    return frames


def a_t(year):
    return lambda d: (d.A * (d.wave == year)).astype(float).values


def pooled_did(cases, y, cluster=None, gallup=()):
    frames = stacked(cases, [2021, 2023], gallup)
    b, V = pooled(frames, y, {"a2023": a_t(2023)}, cluster)
    return ci(b[0], V[0, 0])


def pooled_three(cases, y, drop_also_reached=False, gallup=()):
    frames = stacked(cases, [2021, 2023, 2025], gallup, drop_also_reached)
    b, V = pooled(frames, y, {"a2023": a_t(2023), "a2025": a_t(2025)})
    est, lo, hi = ci(b[1] - b[0], V[0, 0] + V[1, 1] - 2 * V[0, 1])
    return {"c2123": b[0], "c2125": b[1], "change": est, "lo": lo, "hi": hi}


def region_cluster(d):
    return d.iso + "_" + d.region.fillna(-1).astype(int).astype(str)


def psu_cluster(d):
    return d.iso + "_" + d.wave.astype(str) + "_" + d[PSU].astype(str)


def confidence_cases(cases):
    return [c for c in cases if c in CONF_CASES]


def region_means(d, y="index"):
    m = wmean(d, y, by=["region", "wave"]).unstack()
    n = d[d[y].notna()].groupby(["region", "wave"]).size().unstack(fill_value=0)
    return m, n


def region_change(d, y1, y2, y="index"):
    m, _ = region_means(d, y)
    return (m[y2] - m[y1]).dropna()


def n_region(d, region, year, y="index"):
    return int(((d.region == region) & (d.wave == year) & d[y].notna()).sum())


def n_affected(d, year):
    return int(((d.A == 1) & (d.wave == year)).sum())


# --- Global and national figures --------------------------------------------------

GLOBAL = {y: prepare(load_wave(y, ["COUNTRY_ISO3", "PROJWT", *DIMS.values()] +
                               (["CountryIncomeLevel", EXPOSURE[2025]] if y == 2025 else []))) for y in (2021, 2023, 2025)}


@report.finding("X01")
def interviews():
    return len(GLOBAL[2025])


@report.finding("X02")
def countries():
    return GLOBAL[2025].COUNTRY_ISO3.nunique()


@report.finding("X03")
def turkiye_national():
    return {f"national_{y}": wmean(WAVE[y][WAVE[y].COUNTRY_ISO3 == "TUR"], "index") for y in (2021, 2023)}


@report.finding("X04")
def united_states_ranks():
    d = GLOBAL[2025]
    m = pd.DataFrame({k: wmean(d, k, by="COUNTRY_ISO3") for k in ("index", "household", "societal")}).dropna(subset=["index"])
    return {"household": int(m.household.rank(ascending=False)["USA"]), "societal": int(m.societal.rank(ascending=False)["USA"]),
            "countries": len(m)}


@report.finding("X05")
def impacted_2025():
    return pct(GLOBAL[2025], EXPOSURE[2025], [1])


@report.finding("X06")
def country_changes():
    # Countries with Index data in both editions: 120 have dimension scores, 118 an overall
    # Index score (China and Saudi Arabia have none in 2021). Changes are unrounded.
    c = {y: pd.DataFrame({k: wmean(GLOBAL[y], k, by="COUNTRY_ISO3") for k in DIMS}) for y in (2021, 2023)}
    both = c[2021].dropna(how="all").index.intersection(c[2023].dropna(how="all").index)
    ch = c[2023].loc[both] - c[2021].loc[both]
    return {"countries": len(both), "fell": int((ch["index"] < 0).sum()), "rose": int((ch["index"] > 0).sum()),
            "individual_fell": int((ch.individual < 0).sum())}


@report.finding("C1_1")
def chart_1_1():
    return {f"{k}_{y}": wmean(GLOBAL[y], k) for k in DIMS for y in GLOBAL}


@report.finding("C1_2")
def chart_1_2():
    d = GLOBAL[2025]
    d = d[d[EXPOSURE[2025]].isin([1, 2])]
    m = wmean(d, "individual", by=["CountryIncomeLevel", EXPOSURE[2025]])
    status = {1: "impacted", 2: "not_impacted"}
    return {f"{INCOME[i]}_{status[e]}": v for (i, e), v in m.items() if i in INCOME}


# --- Chapter 2: the seven case studies, 2021 to 2023 --------------------------------

def map_trio(d):
    aff, rest, gap = changes(d, "index")
    return {"affected": aff, "rest": rest, "gap": gap}


@report.finding("C2_1")
def chart_2_1():
    d = case_data("MAR", [2021, 2023])
    ch = region_change(d, 2021, 2023)
    out = map_trio(d)
    out.update(rabat=ch[4], souss_massa=ch[9], not_fallen=int((ch.map(r0) >= 0).sum()),
               n_draa_2021=n_region(d, 8, 2021), n_draa_2023=n_region(d, 8, 2023), n_guelmim_2021=n_region(d, 10, 2021),
               n_guelmim_2023=n_region(d, 10, 2023), n_laayoune_2023=n_region(d, 11, 2023), n_dakhla_2023=n_region(d, 12, 2023))
    return out


@report.finding("C2_2")
def chart_2_2():
    d = case_data("MOZ", [2021, 2023])
    ch = region_change(d, 2021, 2023)
    out = map_trio(d)
    out.update(sofala=ch[8], zambezia=ch[10], manica=ch[4], n_cabo_delgado=int((d.region == 1).sum()))
    return out


@report.finding("C2_3")
def chart_2_3():
    d = case_data("NZL", [2021, 2023])
    ch = region_change(d, 2021, 2023)
    _, n = region_means(d)
    out = map_trio(d)
    del out["affected"]
    out.update(northland=ch[1], auckland=ch[2], hatched=int((n.reindex(NZL_REGIONS, fill_value=0).min(axis=1) < 50).sum()),
               n_hawkes_bay_2021=n_region(d, 6, 2021), n_hawkes_bay_2023=n_region(d, 6, 2023),
               n_east_cape_2021=n_region(d, 5, 2021), n_east_cape_2023=n_region(d, 5, 2023))
    return out


@report.finding("C2_4")
def chart_2_4():
    d = case_data("TUR", [2021, 2023])
    ch = region_change(d, 2021, 2023)
    _, n = region_means(d)
    out = map_trio(d)
    out.update(cea=ch[11], mediterranean=ch[6], hatched=int((n.min(axis=1) < 50).sum()), n_min=int(n.values.min()),
               n_max=int(n.values.max()))
    return out


@report.finding("C2_5")
def chart_2_5():
    d = case_data("PAK", [2021, 2023])
    out = map_trio(d)
    d["region"] = d.region.replace({6: 3})  # the former FATA is shown with Khyber Pakhtunkhwa
    ch = region_change(d, 2021, 2023)
    out.update(punjab=ch[2], balochistan=ch[4], kp=ch[3], islamabad=ch[8], n_islamabad_2021=n_region(d, 8, 2021),
               n_islamabad_2023=n_region(d, 8, 2023))
    return out


@report.finding("C2_6")
def chart_2_6():
    d = case_data("ZAF", [2021, 2023])
    ch = region_change(d, 2021, 2023)
    out = map_trio(d)
    out.update(western_cape=ch[9])
    return out


@report.finding("C2_7")
def chart_2_7():
    d = case_data("ECU", [2021, 2023])
    ch = region_change(d, 2021, 2023)
    _, n = region_means(d)
    out = map_trio(d)
    shaded = n[(n.min(axis=1) > 0) & (n.index != 24)]  # 24 = Galapagos, omitted from the map
    out.update(guayas=ch[8], el_oro=ch[6], pichincha=ch[16], manabi=ch[12], shaded=len(shaded),
               hatched=int((shaded.min(axis=1) < 50).sum()))
    return out


def table_2_1(iso):
    d = case_data(iso, [2021, 2023])
    e, lo, hi = did(d, "exposure")
    return {"n_2021": n_affected(d, 2021), "n_2023": n_affected(d, 2023), "exposure": e, "exposure_lo": lo, "exposure_hi": hi}


def table_a1(iso):
    d = case_data(iso, [2021, 2023])
    out = {}
    for k in DIMS:
        out[f"{k}_est"], out[f"{k}_lo"], out[f"{k}_hi"] = did(d, k)
    return out


def table_a2(iso):
    d = case_data(iso, [2021, 2023])
    out = {}
    for k in ("cares", "neighbours", "protect", "exposure"):
        out[f"{k}_est"], out[f"{k}_lo"], out[f"{k}_hi"] = did(d, k)
    return out


def table_a2_confidence(iso):
    d = with_confidence(case_data(iso, [2021, 2023]))
    est, lo, hi = did(d, "confidence")
    return {"est": est, "lo": lo, "hi": hi}


def chart_3_1(iso):
    d = case_data(iso, [2021, 2023])
    out = {}
    for k in ("societal", "community", "household", "individual"):
        out[f"{k}_affected"], out[f"{k}_rest"], out[f"{k}_gap"] = changes(d, k)
    return out


def question_trio(iso, y):
    d = case_data(iso, [2021, 2023])
    if y == "confidence":
        d = with_confidence(d)
    return dict(zip(("affected", "rest", "gap"), changes(d, y)))


def chart_3_4(iso):
    d = case_data(iso, [2021, 2023])
    return {"community": changes(d, "community")[2], "neighbours": changes(d, "neighbours")[2]}


for _iso in CASES:
    report.finding(f"T2_1_{_iso}")(lambda iso=_iso: table_2_1(iso))
    report.finding(f"TA1_{_iso}")(lambda iso=_iso: table_a1(iso))
    report.finding(f"TA2_{_iso}")(lambda iso=_iso: table_a2(iso))
    report.finding(f"C3_1_{_iso}")(lambda iso=_iso: chart_3_1(iso))
    report.finding(f"C3_3_{_iso}")(lambda iso=_iso: question_trio(iso, "neighbours"))
    report.finding(f"C3_4_{_iso}")(lambda iso=_iso: chart_3_4(iso))
    report.finding(f"C3_5_{_iso}")(lambda iso=_iso: question_trio(iso, "protect"))
for _iso in CONF_CASES:
    report.finding(f"TA2conf_{_iso}")(lambda iso=_iso: table_a2_confidence(iso))


@report.finding("C3_2")
def chart_3_2():
    out = {}
    for iso in CONF_CASES:
        for k, v in question_trio(iso, "confidence").items():
            out[f"{iso}_{k}"] = v
    out["pooled"] = pooled_did(CONF_CASES, "confidence", gallup=[CONFIDENCE])[0]
    return out


@report.finding("T2_2")
def table_2_2():
    out = {}
    for m in MEASURES:
        cases = CONF_CASES if m == "confidence" else CASES
        out[f"{m}_est"], out[f"{m}_lo"], out[f"{m}_hi"] = pooled_did(cases, m, gallup=[CONFIDENCE] if m == "confidence" else ())
    return out


@report.finding("C3_1_pooled")
def chart_3_1_pooled():
    return {k: pooled_did(CASES, k)[0] for k in ("societal", "community", "household", "individual")}


@report.finding("C3_3_pooled")
def chart_3_3_pooled():
    return pooled_did(CASES, "neighbours")[0]


@report.finding("C3_4_pooled")
def chart_3_4_pooled():
    return {"community": pooled_did(CASES, "community")[0], "neighbours": pooled_did(CASES, "neighbours")[0]}


@report.finding("C3_5_pooled")
def chart_3_5_pooled():
    return pooled_did(CASES, "protect")[0]


def national(iso, y, years=(2021, 2023)):
    return [wmean(WAVE[t][WAVE[t].COUNTRY_ISO3 == iso], y) for t in years]


@report.finding("C3_6")
def chart_3_6():
    out = {}
    for iso in OTHERS:
        a, b = [wmean(with_confidence(WAVE[t][WAVE[t].COUNTRY_ISO3 == iso]), "confidence") for t in (2021, 2023)]
        out[iso] = b - a
    for iso in CONF_CASES:
        out[iso] = question_trio(iso, "confidence")["gap"]
    return out


# --- Chapter 2 and 3 text ------------------------------------------------------------

@report.finding("X07")
def turkiye_societal_levels():
    d = case_data("TUR", [2021, 2023])
    m = wmean(d[d.A == 1], "societal", by="wave")
    return {"affected_2021": m[2021], "affected_2023": m[2023]}


@report.finding("X08")
def turkiye_confidence_levels():
    d = with_confidence(case_data("TUR", [2021, 2023]))
    m = wmean(d[d.A == 1], "confidence", by="wave")
    return {"affected_2021": m[2021], "affected_2023": m[2023]}


@report.finding("X09")
def kwazulu_natal_2021_2023():
    d = case_data("ZAF", [2021, 2023])
    aff, rest, _ = changes(d, "exposure")
    m = wmean(d[d.A == 1], "neighbours", by="wave")
    return {"exposure_affected": aff, "exposure_rest": rest, "neighbours_2021": m[2021], "neighbours_2023": m[2023]}


@report.finding("X10")
def morocco_exposure():
    aff, rest, _ = changes(case_data("MAR", [2021, 2023]), "exposure")
    return {"affected": aff, "rest": rest}


@report.finding("X11")
def turkiye_exposure():
    d = case_data("TUR", [2021, 2023])
    med = wmean(d[d.region == 6], "exposure", by="wave")
    unit = wmean(d[d.REGION_TUR == TR62], "exposure", by="wave")
    nine = d[~d.region.isin([6, 11, 12])]
    rest = wmean(nine, "exposure", by="wave")
    nat = national("TUR", "exposure")
    sea23 = d[(d.region == SE_ANATOLIA) & (d.wave == 2023)]
    return {"national_2021": nat[0], "national_2023": nat[1], "mediterranean_2021": med[2021], "mediterranean_2023": med[2023],
            "mediterranean_change": med[2023] - med[2021], "adana_mersin_2021": unit[2021], "adana_mersin_2023": unit[2023],
            "nine_regions_2021": rest[2021], "nine_regions_2023": rest[2023],
            "adana_mersin_n_2021": int(((d.REGION_TUR == TR62) & (d.wave == 2021)).sum()),
            "adana_mersin_n_2023": int(((d.REGION_TUR == TR62) & (d.wave == 2023)).sum()),
            "nine_regions": nine.region.nunique(),
            "eight_provinces_n_2021": int((d.REGION_TUR.isin(TUR_NO_2023) & (d.wave == 2021)).sum()),
            "eight_provinces_n_2023": int((d.REGION_TUR.isin(TUR_NO_2023) & (d.wave == 2023)).sum()),
            "southeast_anatolia_n_2023": len(sea23), "southeast_anatolia_mardin_2023": int((sea23.REGION_TUR == TRC3).sum())}


@report.finding("X12")
def hawkes_bay_exposure():
    d = case_data("NZL", [2021, 2023])
    m = wmean(d[d.region == NZ_HAWKES_BAY], "exposure", by="wave")
    return {"2021": m[2021], "2023": m[2023]}


@report.finding("X13")
def pakistan_neighbours():
    d = case_data("PAK", [2021, 2023])
    m = wmean(d, "neighbours", by=["region", "wave"])
    return {"sindh_2021": m[(1, 2021)], "sindh_2023": m[(1, 2023)], "punjab_2021": m[(2, 2021)], "punjab_2023": m[(2, 2023)]}


@report.finding("X14")
def morocco_protect():
    a, b = national("MAR", "protect")
    return {"national_2021": a, "national_2023": b, "national_change": b - a}


@report.finding("X15")
def thailand_philippines():
    tha = WAVE[2023][WAVE[2023].COUNTRY_ISO3 == "THA"]
    a, b = national("THA", "index")
    p, q = national("PHL", "index")
    return {"thailand_exposure_2023": wmean(tha, "exposure"), "thailand_index_change": b - a, "philippines_index_change": q - p}


@report.finding("X16")
def lebanon():
    out = {}
    for k in ("index", "cares", "protect", "exposure"):
        out[f"{k}_2021"], out[f"{k}_2023"] = national("LBN", k)
    for k in ("community", "household", "individual", "societal"):
        a, b = national("LBN", k)
        out[f"{k}_change"] = b - a
    d = WAVE[2023][(WAVE[2023].COUNTRY_ISO3 == "LBN") & (WAVE[2023][EXPOSURE[2023]] == 1)]
    out["earthquake_2023"] = pct(d, TYPE[2023], [7])
    return out


@report.finding("X17")
def confidence_no_disaster():
    out = {}
    for iso, name in (("THA", "thailand"), ("LBN", "lebanon")):
        for t in (2021, 2023):
            out[f"{name}_{t}"] = wmean(with_confidence(WAVE[t][WAVE[t].COUNTRY_ISO3 == iso]), "confidence")
    return out


@report.finding("X18")
def neighbours_text():
    return {iso: did(case_data(iso, [2021, 2023]), "neighbours")[0] for iso in ("NZL", "PAK", "ECU")}


@report.finding("X19")
def neighbours_without_kzn():
    return pooled_did([c for c in CASES if c != "ZAF"], "neighbours")[0]


@report.finding("X20")
def case_counts():
    idx = [did(case_data(iso, [2021, 2023]), "index")[0] for iso in CASES]
    nbr = [did(case_data(iso, [2021, 2023]), "neighbours")[0] for iso in CASES]
    return {"index_fell": sum(e < 0 for e in idx), "neighbours_rose": sum(e > 0 for e in nbr)}


@report.finding("X21")
def affected_composition():
    tur = case_data("TUR", [2021, 2023])
    nzl = case_data("NZL", [2021, 2023])
    return {"turkiye_mediterranean": 100 * (tur.region == 6).sum() / (tur.A == 1).sum(),
            "nz_auckland": 100 * (nzl.region == 2).sum() / (nzl.A == 1).sum()}


@report.finding("X22")
def clusters():
    # Regions with respondents in 2021 or 2023 (South Africa: 2023, as its 2021 regions are not public).
    n = {iso: case_data(iso, [2023] if iso == "ZAF" else [2021, 2023]).region.nunique() for iso in CASES}
    return {"total": sum(n.values()), "min": min(n.values()), "max": max(n.values())}


@report.finding("X23")
def respondents():
    n = {iso: sum(int(WAVE[y][WAVE[y].COUNTRY_ISO3 == iso]["index"].notna().sum()) for y in (2021, 2023)) for iso in CASES}
    n["ECU"] = int(case_data("ECU", [2021, 2023])["index"].notna().sum())  # region don't know / refused left out
    return {"seven": sum(n.values()), "five": sum(n[c] for c in CONF_CASES)}


@report.finding("X24")
def turkiye_composition():
    d = case_data("TUR", [2021, 2023])
    aff = d[d.A == 1]
    share = 100 * aff.REGION_TUR.isin(TUR_AFFECTED_UNITS).groupby(aff.wave).mean()
    d25 = case_data("TUR", [2025])
    return {"share_2021": share[2021], "share_2023": share[2023],
            "tr63_n_2021": int(((d.REGION_TUR == TR63) & (d.wave == 2021)).sum()),
            "tr63_n_2023": int(((d.REGION_TUR == TR63) & (d.wave == 2023)).sum()),
            "southeast_anatolia_n_2021": n_region(d, SE_ANATOLIA, 2021, "wave"),
            "southeast_anatolia_n_2025": n_region(d25, SE_ANATOLIA, 2025, "wave")}


@report.finding("X25")
def turkiye_composition_2025():
    d = merge_gallup(case_data("TUR", [2025]), ["REGION_TUR"])
    aff = d[d.A == 1]
    return {"share_2025": 100 * aff.REGION_TUR.isin(TUR_AFFECTED_UNITS).mean(), "tr63_n_2025": int((d.REGION_TUR == TR63).sum())}


# --- Pooled models and standard errors (appendix) ---------------------------------------

@report.finding("X36")
def six_cases_without_ecuador():
    out = {}
    for k in ("index", "community", "neighbours"):
        out[k], out[f"{k}_lo"], out[f"{k}_hi"] = pooled_did([c for c in CASES if c != "ECU"], k)
    return out


@report.finding("X37")
def clustered_intervals():
    out = {}
    for k in ("index", "community", "neighbours"):
        _, out[f"{k}_hc1_lo"], out[f"{k}_hc1_hi"] = pooled_did(CASES, k)
        _, out[f"{k}_region_lo"], out[f"{k}_region_hi"] = pooled_did(CASES, k, region_cluster)
        _, out[f"{k}_psu_lo"], out[f"{k}_psu_hi"] = pooled_did(CASES, k, psu_cluster, gallup=[PSU, STRATA])
    return out


@report.finding("X38")
def three_wave_index_intervals():
    frames = stacked(RECOVERY, [2021, 2023, 2025])
    b, V = pooled(frames, "index", {"a2023": a_t(2023), "a2025": a_t(2025)})
    _, wlo, whi = ci(b[0], V[0, 0])
    _, nlo, nhi = ci(b[1] - b[0], V[0, 0] + V[1, 1] - 2 * V[0, 1])
    return {"widening_lo": wlo, "widening_hi": whi, "narrowing_lo": nlo, "narrowing_hi": nhi}


@report.finding("X39")
def exploratory_slopes():
    frames = stacked(CASES, [2021, 2023])
    check = {iso: did(f, "exposure")[0] for iso, f in zip(CASES, frames)}
    out = {}
    for key, attr in (("months", MONTHS), ("exposure", check)):
        def slope(d, a=attr):
            return (d.A * (d.wave == 2023) * d.iso.map(a)).values

        b, V = pooled(frames, "index", {"a2023": a_t(2023), "slope": slope})
        out[key], out[f"{key}_lo"], out[f"{key}_hi"] = ci(b[1], V[1, 1])
    return out


@report.finding("X40")
def region_cluster_only():
    count = 0
    for iso in CASES:
        d = case_data(iso, [2021, 2023])
        ms = [m for m in MEASURES if m != "confidence"]
        if iso in CONF_CASES:
            d, ms = with_confidence(d), MEASURES
        for m in ms:
            _, lo, hi = did(d, m)
            _, clo, chi = did(d, m, cluster="region")
            count += (lo <= 0 <= hi) and not (clo <= 0 <= chi)
    return count


@report.finding("X41")
def four_case_model():
    idx = pooled_three(RECOVERY + ["ZAF"], "index")
    nbr = pooled_three(RECOVERY + ["ZAF"], "neighbours")
    return {"index_change": idx["change"], "neighbours_2023": nbr["c2123"], "neighbours_2025": nbr["c2125"]}


# --- Chapter 4: three waves --------------------------------------------------------------

def three_wave(iso):
    return case_data(iso, [2021, 2023, 2025])


def table_4_1(iso):
    d = three_wave(iso)
    return {f"n_{y}": n_affected(d, y) for y in (2021, 2023, 2025)}


for _iso in RECOVERY + ["ZAF"]:
    report.finding(f"T4_1_{_iso}")(lambda iso=_iso: table_4_1(iso))


def table_a3(iso, m):
    d = three_wave(iso)
    if m == "confidence":
        d = with_confidence(d)
    out = gap_model(d, m)
    if iso in ALSO_REACHED and "change" in out:
        adj = gap_model(d[~d.region.isin(ALSO_REACHED[iso])], m)
        out.update(adj=adj["change"], adj_lo=adj["lo"], adj_hi=adj["hi"])
    return out


for _iso in RECOVERY + ["ZAF"]:
    for _m in MEASURES:
        if _iso == "MAR" and _m == "confidence":
            continue
        report.finding(f"TA3_{_iso}_{_m}")(lambda iso=_iso, m=_m: table_a3(iso, m))


@report.finding("TA4")
def table_a4():
    out = {}
    for m in MEASURES:
        # Morocco did not ask confidence, nor government care in 2025: those rows pool Türkiye and New Zealand.
        cases = ["TUR", "NZL"] if m in ("confidence", "cares") else RECOVERY
        g = [CONFIDENCE] if m == "confidence" else ()
        main = pooled_three(cases, m, gallup=g)
        adj = pooled_three(cases, m, drop_also_reached=True, gallup=g)
        out.update({f"{m}_{k}": v for k, v in main.items()})
        out.update({f"{m}_adj": adj["change"], f"{m}_adj_lo": adj["lo"], f"{m}_adj_hi": adj["hi"]})
    return out


@report.finding("X26")
def impacted_2025_by_region():
    out = {}
    for iso, key in (("MAR", "mar"), ("ZAF", "zaf"), ("TUR", "tur")):
        d = case_data(iso, [2025])
        out[f"{key}_affected"], out[f"{key}_rest"] = wmean(d[d.A == 1], "exposure"), wmean(d[d.A == 0], "exposure")
    mar = case_data("MAR", [2025])
    hit = mar[(mar.A == 1) & (mar[EXPOSURE[2025]] == 1)]
    out.update(mar_n_impacted=len(hit), mar_earthquake=pct(hit, TYPE[2025], [7]))
    zaf = case_data("ZAF", [2025])
    hit = zaf[(zaf.A == 1) & (zaf[EXPOSURE[2025]] == 1)]
    out.update(zaf_flood=pct(hit, TYPE[2025], [1]), zaf_storm=pct(hit, TYPE[2025], [2]))
    sea = case_data("TUR", [2025])
    sea = sea[sea.region == SE_ANATOLIA]
    hit = sea[sea[EXPOSURE[2025]] == 1]
    sea = sea.assign(quake=yes100(sea[TYPE[2025]].where(sea[EXPOSURE[2025]] == 1, 0), 7))
    out.update(sea_impacted=wmean(sea, "exposure"), sea_n_impacted=len(hit), sea_earthquake=pct(hit, TYPE[2025], [7]),
               sea_earthquake_all=wmean(sea, "quake"))
    return out


@report.finding("X27")
def new_zealand_2025():
    d = case_data("NZL", [2025])
    hb = d[d.region == NZ_HAWKES_BAY]
    hit = hb[hb[EXPOSURE[2025]] == 1]
    hb = hb.assign(storm=yes100(hb[TYPE[2025]].where(hb[EXPOSURE[2025]] == 1, 0), 2))
    return {"affected": wmean(d[d.A == 1], "exposure"), "rest": wmean(d[d.A == 0], "exposure"),
            "hawkes_bay": wmean(hb, "exposure"), "hawkes_bay_n_impacted": len(hit),
            "hawkes_bay_storm": pct(hit, TYPE[2025], [2]), "hawkes_bay_storm_all": wmean(hb, "storm"),
            "hawkes_bay_n": len(hb)}


@report.finding("X28")
def other_countries_2025():
    out = {}
    for iso, var in (("MOZ", "REGION_MOZ"), ("PAK", "REGION_PAK"), ("ECU", "REGION_ECU")):
        d = merge_gallup(WAVE[2025][WAVE[2025].COUNTRY_ISO3 == iso], [var])
        d = d[d[var].notna() & ~d[var].isin([98, 99])]
        aff = d[var].isin(AFFECTED[iso])
        if iso == "MOZ":
            out.update(moz_nampula=wmean(d[d[var] == 6], "exposure"), moz_affected=wmean(d[aff], "exposure"))
        elif iso == "PAK":
            out.update(pak_kp=wmean(d[d[var] == 3], "exposure"), pak_sindh=wmean(d[aff], "exposure"))
        else:
            out.update(ecu_affected=wmean(d[aff], "exposure"), ecu_rest=wmean(d[~aff], "exposure"))
    return out


def vs_baseline(iso, m):
    d = three_wave(iso)
    if m == "confidence":
        d = with_confidence(d)
    g = gap_model(d, m)
    return g["gap_2025"] - g["gap_2021"]


@report.finding("X29")
def recovered_vs_baseline():
    return {"mar_index": vs_baseline("MAR", "index"), "tur_societal": vs_baseline("TUR", "societal")}


@report.finding("X30")
def recovered_vs_baseline_gallup():
    d = with_confidence(three_wave("ZAF"))
    returned = 0
    for m in MEASURES:
        g = gap_model(d, m)
        returned += np.sign(g["gap_2025"] - g["gap_2023"]) == np.sign(g["gap_2021"] - g["gap_2023"])
    return {"nzl_index": vs_baseline("NZL", "index"), "nzl_individual": vs_baseline("NZL", "individual"),
            "tur_confidence": vs_baseline("TUR", "confidence"), "zaf_community": vs_baseline("ZAF", "community"),
            "zaf_household": vs_baseline("ZAF", "household"), "zaf_protect": vs_baseline("ZAF", "protect"),
            "zaf_returned": int(returned)}


@report.finding("X31")
def kwazulu_natal_2023_2025():
    d = case_data("ZAF", [2023, 2025])
    gi, gn, gc = (gap_model(d, k) for k in ("index", "neighbours", "community"))
    return {"index_gap_2023": gi["gap_2023"], "index_gap_2025": gi["gap_2025"], "neighbours_gap_2023": gn["gap_2023"],
            "neighbours_change": gn["gap_2025"] - gn["gap_2023"], "community_change": gc["gap_2025"] - gc["gap_2023"]}


@report.finding("X32")
def turkiye_prepared():
    d = case_data("TUR", [2021, 2025])
    m = wmean(d, "prepared", by=["A", "wave"])
    d25 = d[d.wave == 2025]
    return {"affected_2021": m[(1, 2021)], "affected_2025": m[(1, 2025)], "rest_2021": m[(0, 2021)], "rest_2025": m[(0, 2025)],
            "local_affected": wmean(d25[d25.A == 1], "local_prepared"), "local_rest": wmean(d25[d25.A == 0], "local_prepared")}


@report.finding("X33")
def prepared_gallup():
    z = case_data("ZAF", [2021, 2025])
    m = wmean(z, "prepared", by=["A", "wave"])
    n = case_data("NZL", [2025])
    frames = stacked(["TUR", "NZL"], [2021, 2025])
    b, _ = pooled(frames, "prepared", {"a2025": a_t(2025)})
    return {"kzn_2021": m[(1, 2021)], "kzn_2025": m[(1, 2025)], "zaf_rest_2021": m[(0, 2021)], "zaf_rest_2025": m[(0, 2025)],
            "nzl_local_gap": wmean(n[n.A == 1], "local_prepared") - wmean(n[n.A == 0], "local_prepared"), "pooled_tur_nzl": b[0]}


@report.finding("X35")
def protect_cluster():
    out = {}
    for iso in ("MAR", "TUR"):
        d = three_wave(iso)
        h, c = gap_model(d, "protect"), gap_model(d, "protect", cluster="region")
        out[f"{iso}_hc1"] = "no" if h["lo"] <= 0 <= h["hi"] else "yes"
        out[f"{iso}_region"] = "no" if c["lo"] <= 0 <= c["hi"] else "yes"
    return out


def changes_2023_2025(iso):
    d = case_data(iso, [2023, 2025])
    return d, region_change(d, 2023, 2025)


@report.finding("C4_4")
def chart_4_4():
    d, ch = changes_2023_2025("MAR")
    out = {name: ch[code] for code, name in MAR_REGIONS.items() if code in ch and name not in ("tanger", "guelmim")}
    out.update(fell=int((ch < 0).sum()), n_guelmim_2023=n_region(d, 10, 2023), n_guelmim_2025=n_region(d, 10, 2025),
               n_draa_2023=n_region(d, 8, 2023), n_draa_2025=n_region(d, 8, 2025), n_souss_2023=n_region(d, 9, 2023),
               n_souss_2025=n_region(d, 9, 2025), n_saharan=int(d.region.isin([11, 12]).sum()))
    return out


@report.finding("C4_5")
def chart_4_5():
    d, ch = changes_2023_2025("TUR")
    out = {name: ch[code] for code, name in TUR_REGIONS.items()}
    rest = ch.drop([6, 11, SE_ANATOLIA])  # Southeast Anatolia is greyed: its 2023 sample is not comparable
    out.update(not_fallen=int((rest.map(r0) >= 0).sum()), n_nea_2023=n_region(d, 10, 2023), n_nea_2025=n_region(d, 10, 2025),
               n_ca_2023=n_region(d, 7, 2023), n_ca_2025=n_region(d, 7, 2025), n_ebs_2023=n_region(d, 9, 2023),
               n_ebs_2025=n_region(d, 9, 2025))
    return out


@report.finding("C4_6")
def chart_4_6():
    d, ch = changes_2023_2025("NZL")
    _, n = region_means(d)
    out = {name: ch[code] for code, name in NZL_REGIONS.items() if code in ch}
    out.update(n_hawkes_bay_2023=n_region(d, 6, 2023), n_hawkes_bay_2025=n_region(d, 6, 2025),
               n_east_cape_2023=n_region(d, 5, 2023), n_east_cape_2025=n_region(d, 5, 2025),
               hatched=int((n.reindex(NZL_REGIONS, fill_value=0).min(axis=1) < 50).sum()))
    return out


@report.finding("C4_7")
def chart_4_7():
    d, ch = changes_2023_2025("ZAF")
    aff, rest, _ = changes(d, "index", (2023, 2025))
    return {"kzn": aff, "rest": rest, "northern_cape": ch[8], "mpumalanga": ch[6], "north_west": ch[7], "western_cape": ch[9],
            "smallest_rise": ZAF_REGIONS[int(ch.idxmin())], "fell": int((ch < 0).sum()), "n_nc_2023": n_region(d, 8, 2023),
            "n_nc_2025": n_region(d, 8, 2025), "n_mp_2023": n_region(d, 6, 2023), "n_mp_2025": n_region(d, 6, 2025)}


def chart_4_8(iso):
    d = case_data(iso, [2025])
    a, r = wmean(d[d.A == 1], "worry"), wmean(d[d.A == 0], "worry")
    return {"affected": a, "rest": r, "gap": a - r, "n": int(((d.A == 1) & d.worry.notna()).sum())}


def chart_4_9(iso):
    g = gap_model(case_data(iso, [2021, 2025]), "prepared")
    return {"gap_2021": g["gap_2021"], "gap_2025": g["gap_2025"], "change": g["gap_2025"] - g["gap_2021"]}


for _iso in RECOVERY + ["ZAF"]:
    report.finding(f"C4_8_{_iso}")(lambda iso=_iso: chart_4_8(iso))
for _iso in ("TUR", "NZL", "ZAF"):
    report.finding(f"C4_9_{_iso}")(lambda iso=_iso: chart_4_9(iso))


@report.finding("C4_9_pooled")
def chart_4_9_pooled():
    frames = stacked(["TUR", "NZL", "ZAF"], [2021, 2025])
    b, _ = pooled(frames, "prepared", {"a2025": a_t(2025)})
    return b[0]


if __name__ == "__main__":
    sys.exit(report.run())
