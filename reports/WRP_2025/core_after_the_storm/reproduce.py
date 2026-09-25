"""Reproduce World Risk Poll 2026: After the storm: How disasters reshape resilience and trust.

Run from the repository root:
    python reports/WRP_2025/core_after_the_storm/reproduce.py

The report follows seven disasters at the sub-national level. For each case
study it splits the country into the regions the disaster struck ("affected")
and every other region ("rest of the country"), and compares the change in
the two groups between the 2021 and 2023 polls (a difference-in-differences),
then follows four of them into 2025. Chapter 1 uses the 2025 poll globally.

Every finding in published_figures.csv is registered at the bottom of this
file: charts and tables in loops, and the text statements one per line. The
building blocks they call are defined first; see README.md for the method.
"""

import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, load_wave, merge_gallup, value_labels  # noqa: E402

report = Report(__file__)
Z = 1.959963984540054  # 97.5% point of the normal distribution

# --- Case studies ------------------------------------------------------------------

CASES = ["MAR", "MOZ", "NZL", "TUR", "PAK", "ZAF", "ECU"]
DIMS = ["index", "societal", "community", "household", "individual"]
QUESTIONS = ["confidence", "gov", "neighbours", "protect"]
NOT_ASKED = {"confidence": ["MAR", "PAK"]}  # confidence in national government, 2021 and 2023

# Region variable for each case study and wave. Morocco's 2021 variable is by
# province and is mapped to the 12 regions below. Two are not in the public
# release and come from Gallup: South Africa 2021 (the public 2021 file has no
# South African region) and New Zealand 2025 (the public 2025 file has only
# North and South Island). Both are assumed to use the 2023 release's codes.
REGION_VAR = {
    "MAR": {2021: "REGION_MAR", 2023: "REGION3_MAR", 2025: "REGION3_MAR"},
    "MOZ": {2021: "REGION_MOZ", 2023: "REGION_MOZ"},
    "NZL": {2021: "REGION_NZL", 2023: "REGION_NZL", 2025: "REGION_NZL"},
    "TUR": {2021: "REGION3_TUR", 2023: "REGION3_TUR", 2025: "REGION3_TUR"},  # 12 NUTS-1 regions
    "PAK": {2021: "REGION_PAK", 2023: "REGION_PAK"},
    "ZAF": {2021: "REGION_ZAF", 2023: "REGION_ZAF", 2025: "REGION_ZAF"},
    "ECU": {2021: "REGION_ECU", 2023: "REGION_ECU"},
}
GALLUP_REGION = {("ZAF", 2021), ("NZL", 2025)}
AFFECTED = {"MAR": [7],            # Marrakech-Safi
            "MOZ": [4, 8, 10],     # Manica, Sofala, Zambezia
            "NZL": [1, 2],         # Northland, Auckland
            "TUR": [6, 11],        # Mediterranean, Central East Anatolia
            "PAK": [1],            # Sindh
            "ZAF": [4],            # KwaZulu-Natal
            "ECU": [6, 8]}         # El Oro, Guayas
# Regions the disaster also reached, removed from both groups in the adjusted
# estimates: Southeast Anatolia; Waikato, Bay of Plenty, East Cape (Tairawhiti), Hawke's Bay.
ALSO_REACHED = {"TUR": [12], "NZL": [3, 4, 5, 6]}
MONTHS = {"MAR": 1, "MOZ": 6, "NZL": 7, "TUR": 10, "PAK": 14, "ZAF": 22, "ECU": 5}  # Table 2.1

# Morocco 2021: province (REGION_MAR) -> region (the REGION3_MAR codes of 2023).
MAR_REGION_PROVINCES = {
    1: ["TANGER ASSILAH", "M DIQ-FNIDEQ", "TETOUAN", "FAHS ANJRA", "LARACHE", "AL HOCEIMA", "CHEFCHAOUEN", "OUEZZANE"],
    2: ["OUJDA ANGAD", "NADOR", "DRIOUCH", "JERADA", "BERKANE", "TAOURIRT", "GUERCIF", "FIGUIG"],
    3: ["FES", "MEKNES", "EL HAJEB", "IFRANE", "MOULAY YACOUB", "SEFROU", "BOULEMANE", "TAOUNATE", "TAZA"],
    4: ["RABAT", "SALE", "SKHIRATE-TEMARA", "KENITRA", "KHEMISSET", "SIDI KACEM", "SIDI SLIMANE"],
    5: ["BENI MELLAL", "AZILAL", "FQUIH BEN SALAH", "KHENIFRA", "KHOURIBGA"],
    6: ["CASABLANCA", "MOHAMMEDIA", "EL JADIDA", "NOUACEUR", "MEDIOUNA", "BENSLIMANE", "BERRECHID", "SETTAT", "SIDI BENNOUR"],
    7: ["MARRAKECH", "CHICHAOUA", "AL HAOUZ", "EL KELAA DES SRAGHNA", "ESSAOUIRA", "REHAMNA", "SAFI", "YOUSSOUFIA"],
    8: ["ERRACHIDIA", "OUARZAZATE", "MIDELT", "TINGHIR", "ZAGORA"],
    9: ["AGADIR IDA OU TANAN", "INEZGANE AIT MELLOUL", "CHTOUKA AIT BAHA", "TAROUDANNT", "TIZNIT", "TATA"],
    10: ["GUELMIM", "ASSA ZAG", "TAN TAN", "SIDI IFNI"],
    11: ["LAAYOUNE", "BOUJDOUR", "TARFAYA", "ES SEMARA"],
    12: ["OUED ED-DAHAB", "AOUSSERD"],
}
_province_name = {name: region for region, names in MAR_REGION_PROVINCES.items() for name in names}
MAR_PROVINCE = {code: _province_name[label] for code, label in value_labels(2021, "REGION_MAR").items() if code < 98}

# Türkiye NUTS-2 units (REGION_TUR codes) and the officially affected provinces in each.
TUR_AFFECTED_PROVINCES = {12: 1,   # TR62 Adana (and Mersin)
                          13: 3,   # TR63 Hatay, Kahramanmaras, Osmaniye
                          22: 2,   # TRB1 Malatya, Elazig
                          24: 3,   # TRC1 Gaziantep, Adiyaman, Kilis
                          25: 2}   # TRC2 Sanliurfa, Diyarbakir
TUR_AFFECTED_UNITS = [12, 13, 22]  # affected units inside the two affected NUTS-1 regions

EXPOSURE = {2021: "WP22245", 2023: "WP23344", 2025: "WP24213"}  # experienced (2021, 2023) / impacted (2025)
PREPARED = {2021: "WP22241", 2025: "WP24198"}                    # national government well prepared
HAZARD = {2023: "WP22247", 2025: "WP24180"}                      # type of disaster named

# --- Data ----------------------------------------------------------------------------


@lru_cache(maxsize=None)
def wave(year):
    """One wave, all countries, with the report's measures on a 0-100 scale."""
    regions = sorted({v[year] for iso, v in REGION_VAR.items() if year in v and (iso, year) not in GALLUP_REGION})
    extra = {2021: ["REGION_TUR", "WP22241"], 2023: ["REGION_TUR", "WP22247"],
             2025: ["WP24198", "WP24199", "WP24180", "worry_index_published"]}[year]
    cols = ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "CountryIncomeLevel", "resilience_index", "resilience_soc",
            "resilience_com", "resilience_hhl", "resilience_idv", "WP22231", "WP22232", "WP22252", EXPOSURE[year]]
    d = load_wave(year, list(dict.fromkeys(cols + regions + extra)))
    out = pd.DataFrame({"wpid": d.WPID_RANDOM, "iso": d.COUNTRY_ISO3, "wave": year, "w": d.PROJWT,
                        "income": d.CountryIncomeLevel})
    for m, v in zip(DIMS, ["resilience_index", "resilience_soc", "resilience_com", "resilience_hhl", "resilience_idv"]):
        out[m] = 100 * d[v]
    yes = lambda v, code=1: np.where(d[v].notna(), 100.0 * (d[v] == code), np.nan)  # noqa: E731
    out["gov"] = yes("WP22231")          # government cares 'a lot'
    out["neighbours"] = yes("WP22232")   # neighbours care 'a lot'
    out["protect"] = yes("WP22252")      # could protect yourself/family (it depends, DK, refused in the base)
    out["depends"] = yes("WP22252", 3)
    out["expo"] = yes(EXPOSURE[year])
    out["expo_code"] = d[EXPOSURE[year]]
    out["prep"] = yes(PREPARED[year]) if year in PREPARED else np.nan
    out["local_prep"] = yes("WP24199") if year == 2025 else np.nan
    out["worry"] = 100 * d["worry_index_published"] if year == 2025 else np.nan
    out["hazard"] = d[HAZARD[year]] if year in HAZARD else np.nan
    out["nuts2"] = d["REGION_TUR"] if year in (2021, 2023) else np.nan
    for v in regions:
        out[v] = d[v]
    return out


def with_confidence(d):
    """Add Gallup's confidence in national government (WP139: 1 = yes)."""
    g = merge_gallup(d.rename(columns={"wpid": "WPID_RANDOM"}), ["WP139"]).rename(columns={"WPID_RANDOM": "wpid"})
    g["confidence"] = np.where(g.WP139.notna(), 100.0 * (g.WP139 == 1), np.nan)
    return g


@lru_cache(maxsize=None)
def case_wave(iso, year, confidence=False):
    """One case study in one wave, with its region, affected flag and measures."""
    d = wave(year)
    d = d[d.iso == iso].copy()
    var = REGION_VAR[iso][year]
    if (iso, year) in GALLUP_REGION:
        d = merge_gallup(d.rename(columns={"wpid": "WPID_RANDOM"}), [var]).rename(columns={"WPID_RANDOM": "wpid"})
    d["region_raw"] = d[var]
    if iso == "MAR" and year == 2021:
        # Province -> region. The 7 respondents whose province is "don't know" stay in
        # the rest of the country, which is what reproduces Tables A.1 and A.2.
        d["region"] = d[var].map(MAR_PROVINCE)
    else:
        d = d[d[var].notna() & (d[var] < 98)].copy()  # region don't know / refused: left out
        d["region"] = d[var].replace({6: 3}) if iso == "PAK" else d[var]  # former FATA -> Khyber Pakhtunkhwa
    d["aff"] = d.region.isin(AFFECTED[iso]).astype(float)
    if confidence:
        d = with_confidence(d)
    return d


def frame(iso, years, m="index"):
    """The case study stacked over `years`; merges Gallup data when `m` needs it."""
    return pd.concat([case_wave(iso, y, m == "confidence") for y in years], ignore_index=True)


# --- Estimation --------------------------------------------------------------------------


def wm(d, m):
    d = d[d[m].notna()]
    return float((d[m] * d.w).sum() / d.w.sum()) if len(d) else np.nan


def fit(y, X, w, cluster=None):
    """Weighted least squares with HC1 (or cluster-robust CR1) variance."""
    y, X, w = np.asarray(y, float), np.asarray(X, float), np.asarray(w, float)
    xtwx = X.T @ (X * w[:, None])
    beta = np.linalg.solve(xtwx, X.T @ (w * y))
    e = y - X @ beta
    n, k = X.shape
    inv = np.linalg.inv(xtwx)
    s = X * (w * e)[:, None]
    if cluster is None:
        meat, c = s.T @ s, n / (n - k)
    else:
        _, grp = np.unique(np.asarray(cluster).astype(str), return_inverse=True)
        S = np.zeros((grp.max() + 1, k))
        np.add.at(S, grp, s)
        G = S.shape[0]
        meat, c = S.T @ S, G / (G - 1) * (n - 1) / (n - k)
    return beta, c * inv @ meat @ inv


def estimate(beta, V, L):
    """Linear combination L'beta with its 95% interval."""
    L = np.asarray(L, float)
    est = float(L @ beta)
    se = float(np.sqrt(L @ V @ L))
    return {"est": est, "lo": est - Z * se, "hi": est + Z * se}


def case_design(d, waves):
    """Intercept, affected, wave dummies and affected x wave (the case regression)."""
    X = {"const": np.ones(len(d)), "aff": d.aff.values}
    for y in waves[1:]:
        X[f"w{y}"] = (d.wave == y).values.astype(float)
        X[f"aff{y}"] = X[f"w{y}"] * d.aff.values
    return pd.DataFrame(X)


def cluster_ids(d):
    return d.iso + "_" + d.region.fillna(-1).astype(int).astype(str)


@lru_cache(maxsize=None)
def did_all(iso, m, clustered=False):
    d = frame(iso, (2021, 2023), m)
    d = d[d[m].notna()]
    X = case_design(d, (2021, 2023))
    beta, V = fit(d[m], X, d.w, cluster_ids(d) if clustered else None)
    return estimate(beta, V, X.columns == "aff2023")


def did(iso, m, field="est"):
    """Difference-in-differences 2021 to 2023 (affected change minus rest change), HC1 interval."""
    return did_all(iso, m)[field]


def mean_in(iso, m, year, grp):
    d = frame(iso, (year,), m)
    return wm(d[d.aff == (1 if grp == "aff" else 0)], m)


def gap(iso, m, year):
    """Affected regions minus the rest of the country in one wave."""
    return mean_in(iso, m, year, "aff") - mean_in(iso, m, year, "rest")


def group_change(iso, grp, y0, y1, m="index"):
    return mean_in(iso, m, y1, grp) - mean_in(iso, m, y0, grp)


@lru_cache(maxsize=None)
def chg_all(iso, m, adjusted=False):
    """Change in the gap from 2023 to 2025, from the case regression over the waves."""
    waves = (2023, 2025) if iso == "ZAF" else (2021, 2023, 2025)  # South Africa 2021 regions are Gallup data
    d = frame(iso, waves, m)
    d = d[d[m].notna()]
    if adjusted:
        d = d[~d.region.isin(ALSO_REACHED[iso])]
    X = case_design(d, waves)
    beta, V = fit(d[m], X, d.w)
    L = (X.columns == "aff2025").astype(float) - (X.columns == "aff2023").astype(float)
    return estimate(beta, V, L)


def chg(iso, m, field="est"):
    if field.startswith("adj"):
        return chg_all(iso, m, True)[{"adj": "est", "adj_lo": "lo", "adj_hi": "hi"}[field]]
    return chg_all(iso, m)[field]


POOLED = {"seven": (CASES, (2021, 2023)), "six_noZAF": ([c for c in CASES if c != "ZAF"], (2021, 2023)),
          "six_noECU": ([c for c in CASES if c != "ECU"], (2021, 2023)),
          "prep3": (["TUR", "NZL", "ZAF"], (2021, 2025)), "prep2": (["TUR", "NZL"], (2021, 2025)),
          "three": (["MAR", "TUR", "NZL"], (2021, 2023, 2025)), "four": (["MAR", "TUR", "NZL", "ZAF"], (2021, 2023, 2025))}


def pooled_data(name, m, adjusted=False):
    """Stacked case studies with the projection weight rescaled to sum to 1 in each country-wave.
    Case studies where `m` was not asked in one of the waves are left out."""
    isos, waves = POOLED[name]
    parts = []
    for iso in isos:
        if m in NOT_ASKED and iso in NOT_ASKED[m]:
            continue
        d = frame(iso, waves, m)
        d = d[d[m].notna()]
        if adjusted and iso in ALSO_REACHED:
            d = d[~d.region.isin(ALSO_REACHED[iso])]
        if set(d.wave) == set(waves):
            parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    d["pw"] = d.w / d.groupby(["iso", "wave"]).w.transform("sum")
    return d


def pooled_design(d, waves, slope=None):
    """Country-by-wave and country-by-affected effects, plus affected x later wave(s)."""
    X = {}
    for iso in sorted(d.iso.unique()):
        for y in waves:
            X[f"{iso}_{y}"] = ((d.iso == iso) & (d.wave == y)).values.astype(float)
        X[f"{iso}_aff"] = ((d.iso == iso).values & (d.aff == 1).values).astype(float)
    for y in waves[1:]:
        X[f"aff{y}"] = ((d.aff == 1) & (d.wave == y)).values.astype(float)
    if slope is not None:
        X["slope"] = X[f"aff{waves[-1]}"] * d.iso.map(slope).values
    return pd.DataFrame(X)


@lru_cache(maxsize=None)
def pooled_all(name, m):
    isos, waves = POOLED[name]
    d = pooled_data(name, m)
    X = pooled_design(d, waves)
    L = X.columns == f"aff{waves[-1]}"
    beta, V = fit(d[m], X, d.pw)
    out = estimate(beta, V, L)
    return out, d, X, beta


def pooled(name, m, field="est"):
    """Pooled difference-in-differences (Table 2.2): fields est/lo/hi (HC1), clo/chi
    (clustered by region within country) and plo/phi (clustered by Gallup's PSU, WP12259)."""
    out, d, X, beta = pooled_all(name, m)
    if field in ("est", "lo", "hi"):
        return out[field]
    L = X.columns == f"aff{POOLED[name][1][-1]}"
    if field in ("clo", "chi"):
        _, V = fit(d[m], X, d.pw, cluster_ids(d))
    else:
        psu = merge_gallup(d[["wpid"]].rename(columns={"wpid": "WPID_RANDOM"}), ["WP12259"])
        _, V = fit(d[m], X, d.pw, d.iso + "_" + psu.WP12259.astype(str).values)
    return estimate(beta, V, L)[{"clo": "lo", "chi": "hi", "plo": "lo", "phi": "hi"}[field]]


@lru_cache(maxsize=None)
def pooled3_all(name, m, adjusted=False):
    isos, waves = POOLED[name]
    d = pooled_data(name, m, adjusted)
    X = pooled_design(d, waves)
    beta, V = fit(d[m], X, d.pw)
    a23, a25 = (X.columns == "aff2023").astype(float), (X.columns == "aff2025").astype(float)
    c23, c25, ch = estimate(beta, V, a23), estimate(beta, V, a25), estimate(beta, V, a25 - a23)
    return {"c2023": c23["est"], "c2023_lo": c23["lo"], "c2023_hi": c23["hi"], "c2025": c25["est"],
            "change": ch["est"], "lo": ch["lo"], "hi": ch["hi"]}


def pooled3(name, m, field):
    """Pooled three-wave model (Table A.4): affected x 2023 and affected x 2025 terms."""
    if field.startswith("adj"):
        return pooled3_all(name, m, True)[{"adj": "change", "adj_lo": "lo", "adj_hi": "hi"}[field]]
    return pooled3_all(name, m)[field]


@lru_cache(maxsize=None)
def slope_all(kind):
    """Seven-case Index model with the affected x 2023 term interacted with months since the
    event (Table 2.1) or with the exposure check (Table A.2)."""
    values = MONTHS if kind == "months" else {iso: did(iso, "expo") for iso in CASES}
    d = pooled_data("seven", "index")
    X = pooled_design(d, (2021, 2023), values)
    beta, V = fit(d["index"], X, d.pw)
    return estimate(beta, V, X.columns == "slope")


def slope(kind, field):
    return slope_all(kind)[field]


def significant(e):
    return e["lo"] > 0 or e["hi"] < 0


def n_negative_did(m):
    return sum(did(iso, m) < 0 for iso in CASES)


def n_positive_did(m):
    return sum(did(iso, m) > 0 for iso in CASES)


def n_sig_cases(m):
    return sum(significant(did_all(iso, m)) for iso in CASES)


def case_measures(iso):
    return [m for m in DIMS + QUESTIONS if iso not in NOT_ASKED.get(m, [])]


def n_significant(iso):
    """Measures (Index, dimensions and the four questions) whose HC1 interval excludes zero."""
    return sum(significant(did_all(iso, m)) for m in case_measures(iso))


def n_cluster_only_sig():
    """Per-case estimates whose region-clustered interval excludes zero while HC1's does not."""
    return sum(significant(did_all(iso, m, True)) and not significant(did_all(iso, m))
               for iso in CASES for m in case_measures(iso))


def n_multi_sig():
    """Pooled measures larger than the margin of error on more than one of the three errors."""
    count = 0
    for m in DIMS + QUESTIONS:
        hits = sum(pooled("seven", m, lo) > 0 or pooled("seven", m, hi) < 0
                   for lo, hi in [("lo", "hi"), ("clo", "chi"), ("plo", "phi")])
        count += hits > 1
    return count


def n_returned(iso):
    """Measures whose 2023-2025 change moved the gap back towards (or past) its 2021 level."""
    return sum(chg(iso, m) * (gap(iso, m, 2021) - gap(iso, m, 2023)) > 0 for m in DIMS + QUESTIONS)


# --- Regions -------------------------------------------------------------------------


def region_mean(iso, reg, year, m):
    d = frame(iso, (year,), m)
    return wm(d[d.region == reg], m)


def region_change(iso, reg, y0, y1, m="index"):
    return region_mean(iso, reg, y1, m) - region_mean(iso, reg, y0, m)


def region_n(iso, reg, year):
    """Respondents with an Index score (the map notes' base)."""
    d = frame(iso, (year,))
    return int(((d.region == reg) & d["index"].notna()).sum())


def region_counts(iso, y0, y1):
    """Index respondents per region in both waves, for regions with respondents in both (shaded)."""
    d = frame(iso, (y0, y1))
    d = d[d["index"].notna() & d.region.notna()]
    n = d.groupby(["region", "wave"]).size().unstack(fill_value=0).reindex(columns=[y0, y1], fill_value=0)
    return n[(n[y0] > 0) & (n[y1] > 0)]


def n_regions(iso, y0, y1):
    return len(region_counts(iso, y0, y1))


def n_hatched(iso, y0, y1):
    n = region_counts(iso, y0, y1)
    return int(((n[y0] < 50) | (n[y1] < 50)).sum())


def n_regions_50plus(iso, y0, y1):
    n = region_counts(iso, y0, y1)
    return int(((n[y0] >= 50) & (n[y1] >= 50)).sum())


def region_changes(iso, y0, y1, m="index"):
    return pd.Series({reg: region_change(iso, reg, y0, y1, m) for reg in region_counts(iso, y0, y1).index})


def n_regions_fell(iso, y0, y1):
    return int((region_changes(iso, y0, y1) < 0).sum())


def n_regions_rose(iso, y0, y1):
    return int((region_changes(iso, y0, y1) > 0).sum())


def min_region_n(iso, y0, y1):
    return int(region_counts(iso, y0, y1).values.min())


def max_region_n(iso, y0, y1):
    return int(region_counts(iso, y0, y1).values.max())


def expo_rise_rank(iso, reg):
    rise = region_changes(iso, 2021, 2023, "expo")
    return int(rise.rank(ascending=False)[reg])


def aff_n(iso, year):
    return int((frame(iso, (year,)).aff == 1).sum())


PUBLIC_CASE_WAVES = [(iso, y) for iso in CASES if iso != "ZAF" for y in (2021, 2023)] + \
    [("ZAF", 2023), ("ZAF", 2025), ("MAR", 2025), ("TUR", 2025)]


def aff_n_range(kind):
    n = [aff_n(iso, y) for iso, y in PUBLIC_CASE_WAVES]
    return min(n) if kind == "min" else max(n)


def n_valid(iso, m, year, grp):
    d = frame(iso, (year,), m)
    return int(((d.aff == (1 if grp == "aff" else 0)) & d[m].notna()).sum())


def share_in_region(iso, reg):
    """Unweighted share of the affected-region respondents (2021 and 2023) living in `reg`."""
    d = frame(iso, (2021, 2023))
    d = d[d.aff == 1]
    return 100 * float((d.region == reg).mean())


def _where(d, where):
    return d[d.aff == 1] if where == "aff" else d[d.region == where]


def hazard_share(iso, where, code):
    """Of those impacted by a disaster in 2025, % naming hazard `code`."""
    d = _where(frame(iso, (2025,)), where)
    d = d[d.expo_code == 1].assign(named=lambda x: 100.0 * (x.hazard == code))
    return wm(d, "named")


def hazard_all(iso, where, code):
    """% of all adults impacted in 2025 and naming hazard `code`."""
    d = _where(frame(iso, (2025,)), where).copy()
    d["named"] = 100.0 * ((d.expo_code == 1) & (d.hazard == code))
    return wm(d, "named")


def n_impacted(iso, where):
    return int((_where(frame(iso, (2025,)), where).expo_code == 1).sum())


def moe_pct(n):
    return 100 * Z * np.sqrt(0.25 / n)


def moe_index_gap(iso, year):
    """Half-width of the HC1 interval of the Index gap in one wave."""
    d = frame(iso, (year,))
    d = d[d["index"].notna()]
    beta, V = fit(d["index"], np.column_stack([np.ones(len(d)), d.aff]), d.w)
    return Z * float(np.sqrt(V[1, 1]))


# Türkiye's NUTS-2 units (REGION_TUR); the 2025 file has NUTS-1 only, so 2025 needs Gallup's variable.
def tur_units(year):
    d = case_wave("TUR", year)
    if year == 2025:
        g = merge_gallup(d.rename(columns={"wpid": "WPID_RANDOM"}), ["REGION_TUR"])
        d = d.assign(nuts2=g["REGION_TUR"].values)
    return d


def tur_unit_n(code, year):
    return int((tur_units(year).nuts2 == code).sum())


def tur_unit_mean(code, year, m):
    d = tur_units(year)
    return wm(d[d.nuts2 == code], m)


def tur_outside_expo(year):
    d = case_wave("TUR", year)
    return wm(d[~d.region.isin([6, 11, 12])], "expo")


def n_unsurveyed_units(year):
    return int(tur_units(year).nuts2.isin([13, 24, 25]).sum())


def n_affected_provinces_unsurveyed():
    """Officially affected provinces in NUTS-2 units with no 2023 respondents."""
    d = tur_units(2023)
    return sum(k for unit, k in TUR_AFFECTED_PROVINCES.items() if (d.nuts2 == unit).sum() == 0)


def tur_affected_share(year):
    """Unweighted % of the affected-region respondents living in officially affected NUTS-2 units."""
    d = tur_units(year)
    d = d[d.aff == 1]
    return 100 * float(d.nuts2.isin(TUR_AFFECTED_UNITS).mean())


PROVINCE_GROUPS = {("MOZ", "nampula"): [6], ("MOZ", "affected"): [4, 8, 10], ("PAK", "kp"): [3, 6],
                   ("PAK", "sindh"): [1], ("ECU", "affected"): [6, 8]}


def prov_expo_2025(iso, group):
    """2025 impacted share in provinces; needs Gallup's 2025 province variable REGION_<iso>."""
    d = wave(2025)
    d = d[d.iso == iso]
    var = f"REGION_{iso}"
    g = merge_gallup(d.rename(columns={"wpid": "WPID_RANDOM"}), [var])
    g = g[g[var].notna() & (g[var] < 98)]
    if (iso, group) in PROVINCE_GROUPS:
        g = g[g[var].isin(PROVINCE_GROUPS[(iso, group)])]
    else:  # the rest of the country
        g = g[~g[var].isin(PROVINCE_GROUPS[(iso, "affected")])]
    return wm(g, "expo")


# Month of each event (Table 2.1): Morocco earthquake, Cyclone Freddy's second landfall, Cyclone
# Gabrielle, Turkiye earthquakes, Pakistan's flood peak (onset June 2022), KwaZulu-Natal floods,
# Ecuador earthquake.
EVENT_MONTH = {"MAR": (2023, 9), "MOZ": (2023, 3), "NZL": (2023, 2), "TUR": (2023, 2), "PAK": (2022, 8),
               "ZAF": (2022, 4), "ECU": (2023, 3), "PAK_onset": (2022, 6)}


def months_to_fieldwork(iso, year, event=None):
    """Calendar months from the event to the country's main fieldwork month. Needs Gallup's
    interview date (FIELD_DATE, as in the 2019 release), which is not in the 2021-2025 files."""
    d = wave(year)
    d = merge_gallup(d[d.iso == iso][["wpid"]].rename(columns={"wpid": "WPID_RANDOM"}), ["FIELD_DATE"])
    dates = pd.to_datetime(d.FIELD_DATE.astype(str).str[:10])
    ym = (dates.dt.year * 12 + dates.dt.month - 1).value_counts()
    main = int(ym[ym == ym.max()].index.min())  # modal month (earliest if tied)
    ey, em = EVENT_MONTH[event or iso]
    return main - (ey * 12 + em - 1)


# --- National and global ------------------------------------------------------------------


def national(iso, m, year):
    d = wave(year)
    d = d[d.iso == iso]
    if m == "confidence":
        d = with_confidence(d)
    return wm(d, m)


def it_depends(iso, year):
    return national(iso, "depends", year)


def earthquake_share(iso, year):
    d = wave(year)
    d = d[(d.iso == iso) & (d.expo_code == 1)].assign(named=lambda x: 100.0 * (x.hazard == 7))
    return wm(d, "named")


def global_mean(dim, year):
    return wm(wave(year), dim)


INCOME = {"low": 1, "lower_middle": 2, "upper_middle": 3, "high": 4}


def income_idv(inc, grp):
    d = wave(2025)
    d = d[(d.income == INCOME[inc]) & (d.expo_code == (1 if grp == "impacted" else 2))]
    return wm(d, "individual")


def impacted_share():
    return wm(wave(2025), "expo")


def country_means(year, dim):
    d = wave(year)
    d = d[d[dim].notna()]
    return (d[dim] * d.w).groupby(d.iso).sum() / d.w.groupby(d.iso).sum()


def us_rank(dim):
    s = country_means(2025, dim)
    return int(s.rank(ascending=False)["USA"])


def n_ranked(dim):
    return len(country_means(2025, dim))


def country_score(year, dim):
    """Country Index = mean of its four dimension scores (Chapter 2's country counts)."""
    if dim != "index":
        return country_means(year, dim)
    return pd.concat([country_means(year, m) for m in DIMS[1:]], axis=1).dropna().mean(axis=1)


def n_countries_both():
    return len(set(wave(2021).iso) & set(wave(2023).iso))


def n_countries_change(dim, direction):
    change = (country_score(2023, dim) - country_score(2021, dim)).dropna()
    return int((change < 0).sum() if direction == "fell" else (change > 0).sum())


def n_resp():
    return len(wave(2025))


def n_countries():
    return wave(2025).iso.nunique()


def rdiff(a, b):
    """Difference of two scores rounded half up, as printed."""
    return float(np.floor(a + 0.5) - np.floor(b + 0.5))


def n_cases_asked(m):
    """Case studies whose country was asked `m` in both 2021 and 2023."""
    count = 0
    for iso in CASES:
        asked = []
        for y in (2021, 2023):
            d = wave(y)
            d = d[d.iso == iso]
            if m == "confidence":
                d = with_confidence(d)
            asked.append(d[m].notna().any())
        count += all(asked)
    return count


def n_pooled_resp(kind):
    """Respondents in the pooled countries in 2021 and 2023 (no region needed to count them)."""
    isos = CASES if kind == "seven" else ["MOZ", "NZL", "TUR", "ZAF", "ECU"]
    total = 0
    for y in (2021, 2023):
        d = wave(y)
        d = d[d.iso.isin(isos)]
        total += int(d["index"].notna().sum()) if kind == "seven" else len(d)
    return total


def n_clusters(kind):
    """Distinct regions per case study across 2021 and 2023 (South Africa: 2023, all nine provinces)."""
    counts = []
    for iso in CASES:
        years = (2023,) if iso == "ZAF" else (2021, 2023)
        regs = set()
        for y in years:
            d = case_wave(iso, y)
            r = d.region if (iso == "MAR" and y == 2021) else d.region_raw
            regs |= set(r.dropna().astype(int))
        counts.append(len(regs))
    return {"total": sum(counts), "min": min(counts), "max": max(counts)}[kind]


# --- Maps (no printed values; written to output/ only) -------------------------------------


def region_key(label):
    label = re.sub(r" region$", "", label.lower())
    return re.sub(r"[^a-z0-9]+", "_", label).strip("_")


LABEL_VAR = {"MAR": (2023, "REGION3_MAR"), "MOZ": (2023, "REGION_MOZ"), "NZL": (2023, "REGION_NZL"),
             "TUR": (2023, "REGION3_TUR"), "PAK": (2023, "REGION_PAK"), "ZAF": (2023, "REGION_ZAF"),
             "ECU": (2023, "REGION_ECU")}


def map_changes(iso, y0, y1):
    labels = value_labels(*LABEL_VAR[iso])
    return {region_key(labels[int(r)]): v for r, v in region_changes(iso, y0, y1).items()}


for i, iso in enumerate(["MAR", "MOZ", "NZL", "TUR", "PAK", "ZAF", "ECU"], start=1):
    report.finding(f"C2_{i}")(lambda iso=iso: map_changes(iso, 2021, 2023))
for i, iso in enumerate(["MAR", "TUR", "NZL", "ZAF"], start=4):
    report.finding(f"C4_{i}")(lambda iso=iso: map_changes(iso, 2023, 2025))
report.finding("C2_8_pooled6")(lambda: {m: pooled("six_noECU", m) for m in DIMS})  # Chart 2.8 'Pooled, six cases'

# --- Charts and tables ------------------------------------------------------------------------

F = {}  # finding id -> function

C11 = {"index": "index", "individual": "individual", "household": "household", "community": "community",
       "societal": "societal"}
for dim in C11:
    for y in (2021, 2023, 2025):
        F[f"C1_1_{dim}_{y}"] = lambda dim=dim, y=y: global_mean(dim, y)
for inc in INCOME:
    for grp in ("impacted", "not"):
        F[f"C1_2_{inc}_{grp}"] = lambda inc=inc, grp=grp: income_idv(inc, grp)

for iso in CASES:  # Table 2.1
    F[f"T2_1_{iso}_n2021"] = lambda iso=iso: aff_n(iso, 2021)
    F[f"T2_1_{iso}_n2023"] = lambda iso=iso: aff_n(iso, 2023)
    for f in ("est", "lo", "hi"):
        F[f"T2_1_{iso}_expo_{f}"] = lambda iso=iso, f=f: did(iso, "expo", f)
for m in DIMS + QUESTIONS:  # Table 2.2
    for f in ("est", "lo", "hi"):
        F[f"T2_2_{m}_{f}"] = lambda m=m, f=f: pooled("seven", m, f)


def bars(prefix, m, isos):
    """Paired bars (affected change, rest change) and the gap between them, 2021 to 2023."""
    for iso in isos:
        F[f"{prefix}_{iso}_aff"] = lambda iso=iso: group_change(iso, "aff", 2021, 2023, m)
        F[f"{prefix}_{iso}_rest"] = lambda iso=iso: group_change(iso, "rest", 2021, 2023, m)
        F[f"{prefix}_{iso}_gap"] = lambda iso=iso: did(iso, m)
    F[f"{prefix}_pooled"] = lambda: pooled("seven", m)


for iso in CASES:  # months from the event to fieldwork (Tables 2.1 and 4.1)
    F[f"T2_1_{iso}_months"] = lambda iso=iso: months_to_fieldwork(iso, 2023)
for iso in ("MAR", "TUR", "NZL", "ZAF"):
    F[f"T4_1_{iso}_months"] = lambda iso=iso: months_to_fieldwork(iso, 2025)
F["T2_1_PAK_onset_months"] = lambda: months_to_fieldwork("PAK", 2023, "PAK_onset")

for dim in DIMS[1:]:
    bars(f"C3_1_{dim}", dim, CASES)
bars("C3_2", "confidence", ["ECU", "MOZ", "NZL", "TUR", "ZAF"])
bars("C3_3", "neighbours", CASES)
bars("C3_5", "protect", CASES)
for iso in CASES + ["pooled"]:
    for m in ("community", "neighbours"):
        F[f"C3_4_{iso}_{m}"] = (lambda m=m: pooled("seven", m)) if iso == "pooled" else (lambda iso=iso, m=m: did(iso, m))
for iso in ("THA", "PHL", "LBN"):
    F[f"C3_6_{iso}"] = lambda iso=iso: national(iso, "confidence", 2023) - national(iso, "confidence", 2021)
for iso in ("ECU", "MOZ", "NZL", "TUR", "ZAF"):
    F[f"C3_6_{iso}"] = lambda iso=iso: did(iso, "confidence")
for iso in ("MAR", "TUR", "NZL", "ZAF"):  # Table 4.1, Chart 4.8
    for y in (2021, 2023, 2025):
        F[f"T4_1_{iso}_{y}"] = lambda iso=iso, y=y: aff_n(iso, y)
    F[f"C4_8_{iso}_aff"] = lambda iso=iso: mean_in(iso, "worry", 2025, "aff")
    F[f"C4_8_{iso}_rest"] = lambda iso=iso: mean_in(iso, "worry", 2025, "rest")
    F[f"C4_8_{iso}_gap"] = lambda iso=iso: gap(iso, "worry", 2025)
for iso in ("TUR", "NZL", "ZAF"):  # Chart 4.9
    F[f"C4_9_{iso}_gap2021"] = lambda iso=iso: gap(iso, "prep", 2021)
    F[f"C4_9_{iso}_gap2025"] = lambda iso=iso: gap(iso, "prep", 2025)
    F[f"C4_9_{iso}_change"] = lambda iso=iso: gap(iso, "prep", 2025) - gap(iso, "prep", 2021)
F["C4_9_pooled"] = lambda: pooled("prep3", "prep")
for iso in CASES:  # Tables A.1 and A.2
    for m in DIMS + QUESTIONS + ["expo"]:
        prefix = "TA_1" if m in DIMS else "TA_2"
        for f in ("est", "lo", "hi"):
            F[f"{prefix}_{iso}_{m}_{f}"] = lambda iso=iso, m=m, f=f: did(iso, m, f)
for iso in ("MAR", "TUR", "NZL", "ZAF"):  # Table A.3
    for m in DIMS + QUESTIONS:
        for y in (2021, 2023, 2025):
            F[f"TA_3_{iso}_{m}_gap{y}"] = lambda iso=iso, m=m, y=y: gap(iso, m, y)
        for f in ("est", "lo", "hi", "adj", "adj_lo", "adj_hi"):
            F[f"TA_3_{iso}_{m}_" + {"est": "change", "adj": "adj_est"}.get(f, f)] = lambda iso=iso, m=m, f=f: chg(iso, m, f)
for m in DIMS + QUESTIONS:  # Table A.4
    for f in ("c2023", "c2025", "change", "lo", "hi", "adj", "adj_lo", "adj_hi"):
        F[f"TA_4_{m}_" + ("adj_est" if f == "adj" else f)] = lambda m=m, f=f: pooled3("three", m, f)

# --- Text statements (one line each; the comment is the statement) ----------------------------

TEXT = {
"X001": lambda: n_resp(),  # Interviews in the 2025 Poll ('more than 143,000')
    "X002": lambda: n_countries(),  # Countries and territories in 2025
    "X003": lambda: mean_in("ZAF", "neighbours", 2023, "aff") / mean_in("ZAF", "neighbours", 2021, "aff"),  # KwaZulu-Natal: share saying neighbours care 'a lot' 'nearly tripled' after the 2022 floods (2023 / 2021)
    "X004": lambda: mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions: national government well prepared, 2021 ('roughly two in five')
    "X005": lambda: mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions: national government well prepared, 2025 ('fewer than one in ten')
    "X006": lambda: n_resp(),  # Interviews ('more than 143,000')
    "X007": lambda: n_countries(),  # Countries and territories
    "X008": lambda: did("TUR", "confidence", "est"),  # Türkiye: confidence in national government, difference-in-differences 2021-2023
    "X009": lambda: did("NZL", "confidence", "est"),  # New Zealand: confidence in national government, difference-in-differences
    "X010": lambda: did("MOZ", "gov", "est"),  # Mozambique: government cares 'a lot', difference-in-differences
    "X011": lambda: national("TUR", "index", 2021),  # Türkiye national Resilience Index, 2021
    "X012": lambda: national("TUR", "index", 2023),  # Türkiye national Resilience Index, 2023
    "X013": lambda: group_change("TUR", "aff", 2021, 2023, "index"),  # Türkiye earthquake regions: Index change 2021-2023
    "X014": lambda: group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye: Index change 2021-2023
    "X015": lambda: pooled("seven", "neighbours", "est"),  # Pooled seven cases: neighbours care 'a lot', difference-in-differences
    "X016": lambda: 100 * (1 - pooled("six_noZAF", "neighbours", "est") / pooled("seven", "neighbours", "est")),  # Share of the pooled neighbours rise that comes from KwaZulu-Natal ('half')
    "X017": lambda: mean_in("ZAF", "neighbours", 2023, "aff") / mean_in("ZAF", "neighbours", 2021, "aff"),  # KwaZulu-Natal: neighbours care 'a lot' 'nearly tripled' (2023 / 2021)
    "X018": lambda: chg("ZAF", "neighbours", "est"),  # KwaZulu-Natal: neighbours care 'a lot', change in the gap 2023-2025
    "X019": lambda: gap("ZAF", "neighbours", 2023),  # KwaZulu-Natal: neighbours care 'a lot', gap above the rest of South Africa in 2023
    "X020": lambda: gap("TUR", "confidence", 2023),  # Türkiye: confidence gap, 2023
    "X021": lambda: gap("TUR", "confidence", 2025),  # Türkiye: confidence gap, 2025
    "X022": lambda: chg("TUR", "confidence", "est"),  # Türkiye: confidence gap narrowing 2023-2025
    "X023": lambda: chg("NZL", "confidence", "est"),  # New Zealand: confidence gap narrowing 2023-2025
    "X024": lambda: mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions: well prepared, 2021
    "X025": lambda: mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions: well prepared, 2025
    "X026": lambda: mean_in("TUR", "prep", 2021, "rest"),  # Rest of Türkiye: well prepared, 2021
    "X027": lambda: mean_in("TUR", "prep", 2025, "rest"),  # Rest of Türkiye: well prepared, 2025
    "X028": lambda: pooled("prep3", "prep", "est"),  # Pooled three countries: well prepared, change in the gap 2021-2025
    "X029": lambda: pooled("seven", "index", "est"),  # Pooled seven cases: Resilience Index difference-in-differences ('about two points')
    "X030": lambda: n_negative_did("index"),  # Case studies where the Index fell relative to the rest of the country ('six of the seven')
    "X031": lambda: pooled("seven", "community", "est"),  # Pooled seven cases: community dimension ('about three points')
    "X032": lambda: did("TUR", "societal", "est"),  # Türkiye: societal dimension difference-in-differences
    "X033": lambda: did("MOZ", "societal", "est"),  # Mozambique: societal dimension difference-in-differences
    "X034": lambda: did("TUR", "confidence", "est"),  # Policy implications: Türkiye confidence difference-in-differences
    "X035": lambda: did("MOZ", "gov", "est"),  # Policy implications: Mozambique government cares 'a lot'
    "X036": lambda: pooled("seven", "neighbours", "est"),  # Policy implications: pooled neighbours care 'a lot'
    "X037": lambda: chg("TUR", "confidence", "est"),  # Policy implications: Türkiye confidence recovered 2023-2025
    "X038": lambda: mean_in("TUR", "prep", 2021, "aff"),  # Policy implications: Türkiye earthquake regions well prepared 2021
    "X039": lambda: mean_in("TUR", "prep", 2025, "aff"),  # Policy implications: Türkiye earthquake regions well prepared 2025
    "X040": lambda: mean_in("TUR", "prep", 2021, "rest"),  # Policy implications: rest of Türkiye well prepared 2021
    "X041": lambda: mean_in("TUR", "prep", 2025, "rest"),  # Policy implications: rest of Türkiye well prepared 2025
    "X042": lambda: us_rank("household"),  # United States: rank on household resilience, 2025
    "X043": lambda: us_rank("societal"),  # United States: rank on societal resilience, 2025
    "X044": lambda: n_ranked("societal"),  # Countries ranked on societal resilience, 2025
    "X045": lambda: global_mean("individual", 2025),  # Chart 1.1 subtitle: individual resilience 2025
    "X046": lambda: global_mean("societal", 2025),  # Chart 1.1 subtitle: societal resilience 2025
    "X047": lambda: global_mean("index", 2025),  # Chart 1.1 subtitle: Resilience Index 2025
    "X048": lambda: rdiff(global_mean("index", 2025), global_mean("index", 2023)),  # Chart 1.1 subtitle: Index 2025 minus 2023 ('level with 2023')
    "X049": lambda: rdiff(global_mean("index", 2025), global_mean("index", 2021)),  # Chart 1.1 subtitle: Index 2025 minus 2021 ('two points above')
    "X050": lambda: global_mean("index", 2025),  # Global Index 2025
    "X051": lambda: rdiff(global_mean("index", 2025), global_mean("index", 2023)),  # Global Index 2025 minus 2023 ('level with 2023')
    "X052": lambda: rdiff(global_mean("index", 2025), global_mean("index", 2021)),  # Global Index 2025 minus 2021 ('two points above 2021')
    "X053": lambda: global_mean("individual", 2021),  # Global individual dimension 2021
    "X054": lambda: global_mean("individual", 2023),  # Global individual dimension 2023
    "X055": lambda: global_mean("individual", 2025),  # Global individual dimension 2025
    "X056": lambda: global_mean("societal", 2021),  # Global societal dimension 2021
    "X057": lambda: global_mean("societal", 2023),  # Global societal dimension 2023
    "X058": lambda: global_mean("societal", 2025),  # Global societal dimension 2025
    "X059": lambda: global_mean("household", 2023),  # Global household dimension 2023
    "X060": lambda: global_mean("household", 2025),  # Global household dimension 2025
    "X061": lambda: rdiff(global_mean("household", 2025), global_mean("household", 2021)),  # Household 2025 minus 2021 ('one point above 2021')
    "X062": lambda: global_mean("community", 2021),  # Global community dimension 2021
    "X063": lambda: global_mean("community", 2023),  # Global community dimension 2023
    "X064": lambda: global_mean("community", 2025),  # Global community dimension 2025
    "X065": lambda: impacted_share(),  # Adults impacted by a disaster in the past five years, 2025 ('one adult in five (20%)')
    "X066": lambda: income_idv("low", "impacted"),  # Chart 1.2 subtitle: low income, impacted
    "X067": lambda: income_idv("low", "not"),  # Chart 1.2 subtitle: low income, not impacted
    "X068": lambda: income_idv("lower_middle", "impacted"),  # Individual resilience, lower_middle income, impacted
    "X069": lambda: income_idv("lower_middle", "not"),  # Individual resilience, lower_middle income, not impacted
    "X070": lambda: income_idv("upper_middle", "impacted"),  # Individual resilience, upper_middle income, impacted
    "X071": lambda: income_idv("upper_middle", "not"),  # Individual resilience, upper_middle income, not impacted
    "X072": lambda: income_idv("high", "impacted"),  # Individual resilience, high income, impacted
    "X073": lambda: income_idv("high", "not"),  # Individual resilience, high income, not impacted
    "X074": lambda: income_idv("low", "impacted"),  # Individual resilience, low income, impacted
    "X075": lambda: income_idv("low", "not"),  # Individual resilience, low income, not impacted
    "X076": lambda: national("TUR", "index", 2021),  # Türkiye national Index 2021
    "X077": lambda: national("TUR", "index", 2023),  # Türkiye national Index 2023
    "X078": lambda: group_change("TUR", "aff", 2021, 2023, "index"),  # Türkiye earthquake regions: Index change
    "X079": lambda: group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye: Index change
    "X080": lambda: global_mean("index", 2021),  # Global Index 2021
    "X081": lambda: global_mean("index", 2023),  # Global Index 2023
    "X082": lambda: n_countries_change("index", "fell"),  # Countries where the Index fell 2021-2023
    "X083": lambda: n_countries_both(),  # Countries measured in both 2021 and 2023
    "X084": lambda: n_countries_change("index", "rose"),  # Countries where the Index rose 2021-2023
    "X085": lambda: n_countries_change("individual", "fell"),  # Countries where the individual dimension fell 2021-2023
    "X086": lambda: share_in_region("TUR", 6),  # Share of Türkiye's affected respondents in the Mediterranean region ('two thirds')
    "X087": lambda: share_in_region("NZL", 2),  # Share of New Zealand's affected respondents in Auckland ('nine in ten')
    "X088": lambda: group_change("MAR", "aff", 2021, 2023, "index"),  # Chart 2.1 subtitle: Marrakech-Safi Index change 2021-2023
    "X089": lambda: group_change("MAR", "rest", 2021, 2023, "index"),  # Chart 2.1 subtitle: rest of Morocco Index change
    "X090": lambda: group_change("MAR", "aff", 2021, 2023, "index"),  # Marrakech-Safi Index change
    "X091": lambda: group_change("MAR", "rest", 2021, 2023, "index"),  # Rest of Morocco Index change
    "X092": lambda: n_regions_fell("MAR", 2021, 2023),  # Shaded regions that fell ('every shaded region fell'; 10 shaded)
    "X093": lambda: region_change("MAR", 4, 2021, 2023, "index"),  # Rabat-Salé-Kénitra Index change
    "X094": lambda: region_change("MAR", 9, 2021, 2023, "index"),  # Souss-Massa Index change
    "X095": lambda: did("MAR", "index", "est"),  # Gap between the two groups ('one point')
    "X096": lambda: region_n("MAR", 8, 2021),  # Draa-Tafilalet respondents 2021
    "X097": lambda: region_n("MAR", 8, 2023),  # Draa-Tafilalet respondents 2023
    "X098": lambda: region_n("MAR", 10, 2021),  # Guelmim-Oued Noun respondents 2021
    "X099": lambda: region_n("MAR", 10, 2023),  # Guelmim-Oued Noun respondents 2023
    "X100": lambda: group_change("MOZ", "aff", 2021, 2023, "index"),  # Chart 2.2 subtitle: cyclone-hit provinces Index change
    "X101": lambda: group_change("MOZ", "rest", 2021, 2023, "index"),  # Chart 2.2 subtitle: rest of Mozambique Index change
    "X102": lambda: region_change("MOZ", 8, 2021, 2023, "index"),  # Sofala Index change
    "X103": lambda: region_change("MOZ", 10, 2021, 2023, "index"),  # Zambezia Index change
    "X104": lambda: region_change("MOZ", 4, 2021, 2023, "index"),  # Manica Index change
    "X105": lambda: group_change("MOZ", "aff", 2021, 2023, "index"),  # Three affected provinces together
    "X106": lambda: group_change("MOZ", "rest", 2021, 2023, "index"),  # Rest of the country
    "X107": lambda: did("MOZ", "index", "est"),  # Gap ('one point')
    "X108": lambda: region_change("MOZ", 2, 2021, 2023, "index"),  # Gaza Index change
    "X109": lambda: region_change("MOZ", 7, 2021, 2023, "index"),  # Niassa Index change
    "X110": lambda: did("NZL", "index", "est"),  # Chart 2.3 subtitle: Northland and Auckland fell further ('three points')
    "X111": lambda: region_change("NZL", 1, 2021, 2023, "index"),  # Northland Index change
    "X112": lambda: region_change("NZL", 2, 2021, 2023, "index"),  # Auckland Index change
    "X113": lambda: group_change("NZL", "rest", 2021, 2023, "index"),  # Rest of New Zealand Index change
    "X114": lambda: did("NZL", "index", "est"),  # Gap ('three points')
    "X115": lambda: n_hatched("NZL", 2021, 2023),  # Regions hatched (fewer than 50 respondents in an edition)
    "X116": lambda: n_regions("NZL", 2021, 2023),  # Regions shaded
    "X117": lambda: region_n("NZL", 1, 2021),  # Northland respondents 2021
    "X118": lambda: region_n("NZL", 1, 2023),  # Northland respondents 2023
    "X119": lambda: region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
    "X120": lambda: region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
    "X121": lambda: region_n("NZL", 5, 2021),  # Tairāwhiti/Gisborne respondents 2021
    "X122": lambda: region_n("NZL", 5, 2023),  # Tairāwhiti/Gisborne respondents 2023
    "X123": lambda: region_change("TUR", 11, 2021, 2023, "index"),  # Chart 2.4 subtitle: Central East Anatolia Index change
    "X124": lambda: region_change("TUR", 6, 2021, 2023, "index"),  # Chart 2.4 subtitle: Mediterranean Index change
    "X125": lambda: n_affected_provinces_unsurveyed(),  # Chart 2.4 subtitle: affected provinces with no 2023 respondents
    "X126": lambda: region_change("TUR", 11, 2021, 2023, "index"),  # Central East Anatolia Index change
    "X127": lambda: region_n("TUR", 11, 2021),  # Central East Anatolia respondents 2021
    "X128": lambda: region_n("TUR", 11, 2023),  # Central East Anatolia respondents 2023
    "X129": lambda: region_change("TUR", 6, 2021, 2023, "index"),  # Mediterranean Index change
    "X130": lambda: group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye Index change
    "X131": lambda: group_change("TUR", "aff", 2021, 2023, "index"),  # Two affected regions together
    "X132": lambda: did("TUR", "index", "est"),  # Gap ('four points')
    "X133": lambda: min_region_n("TUR", 2021, 2023),  # Smallest regional sample
    "X134": lambda: max_region_n("TUR", 2021, 2023),  # Largest regional sample
    "X135": lambda: n_hatched("TUR", 2021, 2023),  # Regions hatched
    "X136": lambda: region_n("TUR", 11, 2021),  # Central East Anatolia respondents 2021 (note)
    "X137": lambda: region_n("TUR", 11, 2023),  # Central East Anatolia respondents 2023 (note)
    "X138": lambda: region_n("TUR", 10, 2021),  # Northeast Anatolia respondents 2021
    "X139": lambda: region_n("TUR", 10, 2023),  # Northeast Anatolia respondents 2023
    "X140": lambda: group_change("PAK", "aff", 2021, 2023, "index"),  # Chart 2.5 subtitle: Sindh Index change
    "X141": lambda: group_change("PAK", "rest", 2021, 2023, "index"),  # Chart 2.5 subtitle: rest of Pakistan
    "X142": lambda: group_change("PAK", "aff", 2021, 2023, "index"),  # Sindh Index change
    "X143": lambda: group_change("PAK", "rest", 2021, 2023, "index"),  # Rest of Pakistan Index change
    "X144": lambda: did("PAK", "index", "est"),  # Gap ('three points')
    "X145": lambda: region_change("PAK", 2, 2021, 2023, "index"),  # Punjab Index change
    "X146": lambda: region_change("PAK", 4, 2021, 2023, "index"),  # Balochistan Index change
    "X147": lambda: region_change("PAK", 3, 2021, 2023, "index"),  # Khyber Pakhtunkhwa Index change ('did not change')
    "X148": lambda: region_change("PAK", 8, 2021, 2023, "index"),  # Islamabad Index change
    "X149": lambda: region_n("PAK", 8, 2021),  # Islamabad respondents 2021 (text)
    "X150": lambda: region_n("PAK", 8, 2023),  # Islamabad respondents 2023 (text)
    "X151": lambda: region_n("PAK", 8, 2021),  # Islamabad respondents 2021 (note)
    "X152": lambda: region_n("PAK", 8, 2023),  # Islamabad respondents 2023 (note)
    "X153": lambda: group_change("ZAF", "aff", 2021, 2023, "index"),  # Chart 2.6 subtitle: KwaZulu-Natal Index change
    "X154": lambda: group_change("ZAF", "rest", 2021, 2023, "index"),  # Chart 2.6 subtitle: rest of South Africa
    "X155": lambda: group_change("ZAF", "aff", 2021, 2023, "index"),  # KwaZulu-Natal Index change
    "X156": lambda: group_change("ZAF", "rest", 2021, 2023, "index"),  # Rest of South Africa Index change
    "X157": lambda: did("ZAF", "index", "est"),  # Gap in the province's favour ('four points')
    "X158": lambda: region_change("ZAF", 9, 2021, 2023, "index"),  # Western Cape Index change
    "X159": lambda: region_n("ZAF", 8, 2021),  # Northern Cape respondents 2021 (text)
    "X160": lambda: region_n("ZAF", 8, 2023),  # Northern Cape respondents 2023 (text)
    "X161": lambda: region_n("ZAF", 8, 2021),  # Northern Cape respondents 2021 (note)
    "X162": lambda: region_n("ZAF", 8, 2023),  # Northern Cape respondents 2023 (note)
    "X163": lambda: group_change("ECU", "aff", 2021, 2023, "index"),  # Chart 2.7 subtitle: Guayas and El Oro Index change
    "X164": lambda: group_change("ECU", "rest", 2021, 2023, "index"),  # Chart 2.7 subtitle: rest of Ecuador
    "X165": lambda: did("ECU", "index", "est"),  # Chart 2.7 subtitle: gap
    "X166": lambda: region_change("ECU", 8, 2021, 2023, "index"),  # Guayas Index change
    "X167": lambda: region_change("ECU", 6, 2021, 2023, "index"),  # El Oro Index change
    "X168": lambda: group_change("ECU", "aff", 2021, 2023, "index"),  # Guayas and El Oro together
    "X169": lambda: group_change("ECU", "rest", 2021, 2023, "index"),  # Rest of Ecuador
    "X170": lambda: did("ECU", "index", "est"),  # Gap ('four points')
    "X171": lambda: region_change("ECU", 16, 2021, 2023, "index"),  # Pichincha Index change
    "X172": lambda: region_change("ECU", 12, 2021, 2023, "index"),  # Manabí Index change
    "X173": lambda: n_hatched("ECU", 2021, 2023),  # Provinces hatched
    "X174": lambda: n_regions("ECU", 2021, 2023),  # Provinces shaded
    "X175": lambda: region_n("ECU", 6, 2021),  # El Oro respondents 2021
    "X176": lambda: region_n("ECU", 6, 2023),  # El Oro respondents 2023
    "X177": lambda: n_regions_50plus("ECU", 2021, 2023),  # Provinces with 50 or more respondents in both editions
    "X178": lambda: did("TUR", "societal", "est"),  # Türkiye societal dimension difference-in-differences
    "X179": lambda: group_change("TUR", "aff", 2021, 2023, "societal"),  # Türkiye affected regions: societal change
    "X180": lambda: mean_in("TUR", "societal", 2021, "aff"),  # Türkiye affected regions: societal 2021
    "X181": lambda: mean_in("TUR", "societal", 2023, "aff"),  # Türkiye affected regions: societal 2023
    "X182": lambda: group_change("TUR", "rest", 2021, 2023, "societal"),  # Rest of Türkiye: societal change
    "X183": lambda: group_change("TUR", "aff", 2021, 2023, "confidence"),  # Türkiye affected regions: confidence change
    "X184": lambda: mean_in("TUR", "confidence", 2021, "aff"),  # Türkiye affected regions: confidence 2021
    "X185": lambda: mean_in("TUR", "confidence", 2023, "aff"),  # Türkiye affected regions: confidence 2023
    "X186": lambda: group_change("TUR", "rest", 2021, 2023, "confidence"),  # Rest of Türkiye: confidence change
    "X187": lambda: did("TUR", "confidence", "est"),  # Türkiye: confidence gap ('24 percentage points')
    "X188": lambda: did("TUR", "gov", "est"),  # Türkiye: government cares 'a lot' fell further
    "X189": lambda: aff_n("TUR", 2021),  # Türkiye affected respondents 2021
    "X190": lambda: aff_n("TUR", 2023),  # Türkiye affected respondents 2023
    "X191": lambda: n_affected_provinces_unsurveyed(),  # Officially affected provinces with no 2023 respondents
    "X192": lambda: group_change("ZAF", "aff", 2021, 2023, "expo"),  # KwaZulu-Natal: reported disaster experience change
    "X193": lambda: group_change("ZAF", "rest", 2021, 2023, "expo"),  # Rest of South Africa: reported disaster experience change
    "X194": lambda: mean_in("ZAF", "neighbours", 2021, "aff"),  # KwaZulu-Natal: neighbours care 'a lot' 2021
    "X195": lambda: mean_in("ZAF", "neighbours", 2023, "aff"),  # KwaZulu-Natal: neighbours care 'a lot' 2023
    "X196": lambda: did("ZAF", "neighbours", "est"),  # South Africa: neighbours difference-in-differences
    "X197": lambda: did("ZAF", "household", "est"),  # South Africa: household dimension difference-in-differences
    "X198": lambda: did("ZAF", "confidence", "est"),  # South Africa: confidence difference-in-differences
    "X199": lambda: did("ZAF", "index", "est"),  # South Africa: Index gap in the province's favour
    "X200": lambda: aff_n("ZAF", 2021),  # KwaZulu-Natal respondents 2021
    "X201": lambda: aff_n("ZAF", 2023),  # KwaZulu-Natal respondents 2023
    "X202": lambda: group_change("MAR", "rest", 2021, 2023, "expo"),  # Morocco: reported disaster experience rose where the earthquake did not strike
    "X203": lambda: n_significant("MOZ"),  # Mozambique: estimates larger than the margin of error
    "X204": lambda: did("MOZ", "societal", "est"),  # Mozambique: societal dimension
    "X205": lambda: did("MOZ", "gov", "est"),  # Mozambique: government cares 'a lot'
    "X206": lambda: n_significant("PAK"),  # Pakistan: estimates larger than the margin of error
    "X207": lambda: did("PAK", "societal", "est"),  # Pakistan: societal dimension
    "X208": lambda: did("NZL", "index", "est"),  # New Zealand: Index
    "X209": lambda: did("NZL", "confidence", "est"),  # New Zealand: confidence
    "X210": lambda: did("ECU", "index", "est"),  # Ecuador: Index gap
    "X211": lambda: did("ECU", "household", "est"),  # Ecuador: household dimension gap
    "X212": lambda: group_change("ECU", "aff", 2021, 2023, "confidence"),  # Ecuador: confidence change inside the affected provinces
    "X213": lambda: group_change("ECU", "rest", 2021, 2023, "confidence"),  # Ecuador: confidence change outside
    "X214": lambda: pooled("seven", "index", "est"),  # Chart 2.8 subtitle: pooled Index ('about two points lower')
    "X215": lambda: pooled("seven", "index", "est"),  # Pooled Index ('about two points lower')
    "X216": lambda: n_negative_did("index"),  # Case studies going that way ('six of the seven')
    "X217": lambda: mean_in("ZAF", "neighbours", 2021, "aff"),  # Box: KwaZulu-Natal neighbours 2021
    "X218": lambda: mean_in("ZAF", "neighbours", 2023, "aff"),  # Box: KwaZulu-Natal neighbours 2023
    "X219": lambda: did("ZAF", "neighbours", "est"),  # Box: South Africa neighbours relative change
    "X220": lambda: group_change("MAR", "aff", 2021, 2023, "neighbours"),  # Box: Marrakech-Safi neighbours rise
    "X221": lambda: group_change("MAR", "rest", 2021, 2023, "neighbours"),  # Box: rest of Morocco neighbours rise
    "X222": lambda: did("MAR", "neighbours", "est"),  # Box: rise specific to the earthquake region
    "X223": lambda: pooled("seven", "community", "est"),  # Pooled community dimension ('about three points')
    "X224": lambda: pooled("seven", "neighbours", "est"),  # Pooled neighbours care 'a lot'
    "X225": lambda: pooled("six_noZAF", "neighbours", "est") / pooled("seven", "neighbours", "est"),  # Pooled neighbours rise 'halves without KwaZulu-Natal' (ratio)
    "X226": lambda: n_affected_provinces_unsurveyed(),  # Officially affected Turkish provinces with no 2023 respondents
    "X227": lambda: n_unsurveyed_units(2021),  # Respondents in those provinces, 2021
    "X228": lambda: n_unsurveyed_units(2023),  # Respondents in those provinces, 2023
    "X229": lambda: national("TUR", "expo", 2021),  # Türkiye: reported disaster experience 2021
    "X230": lambda: national("TUR", "expo", 2023),  # Türkiye: reported disaster experience 2023
    "X231": lambda: region_change("TUR", 6, 2021, 2023, "expo"),  # Mediterranean region: rise in reported experience
    "X232": lambda: region_mean("TUR", 6, 2021, "expo"),  # Mediterranean region: reported experience 2021
    "X233": lambda: region_mean("TUR", 6, 2023, "expo"),  # Mediterranean region: reported experience 2023
    "X234": lambda: expo_rise_rank("TUR", 6),  # Mediterranean: rank of the rise among Türkiye's 12 regions ('largest rise anywhere')
    "X235": lambda: tur_unit_n(12, 2021),  # Adana and Mersin unit (TR62) respondents 2021
    "X236": lambda: tur_unit_n(12, 2023),  # Adana and Mersin unit respondents 2023
    "X237": lambda: tur_unit_mean(12, 2021, "expo"),  # Adana and Mersin unit: reported experience 2021
    "X238": lambda: tur_unit_mean(12, 2023, "expo"),  # Adana and Mersin unit: reported experience 2023
    "X239": lambda: tur_outside_expo(2021),  # Nine regions outside the earthquake zone: reported experience 2021
    "X240": lambda: tur_outside_expo(2023),  # Nine regions outside the earthquake zone: reported experience 2023
    "X241": lambda: region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
    "X242": lambda: region_n("NZL", 5, 2021),  # Tairāwhiti/Gisborne respondents 2021
    "X243": lambda: region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
    "X244": lambda: region_n("NZL", 5, 2023),  # Tairāwhiti/Gisborne respondents 2023
    "X245": lambda: region_mean("NZL", 6, 2021, "expo"),  # Hawke's Bay reported experience 2021
    "X246": lambda: region_mean("NZL", 6, 2023, "expo"),  # Hawke's Bay reported experience 2023
    "X247": lambda: group_change("MAR", "aff", 2021, 2023, "expo"),  # Marrakech-Safi: rise in reported experience
    "X248": lambda: group_change("MAR", "rest", 2021, 2023, "expo"),  # Rest of Morocco: rise in reported experience
    "X249": lambda: did("TUR", "societal", "est"),  # Türkiye societal dimension
    "X250": lambda: did("TUR", "confidence", "est"),  # Türkiye confidence
    "X251": lambda: did("MOZ", "gov", "est"),  # Mozambique government cares 'a lot'
    "X252": lambda: national("TUR", "index", 2021),  # Türkiye national Index 2021
    "X253": lambda: national("TUR", "index", 2023),  # Türkiye national Index 2023
    "X254": lambda: group_change("TUR", "aff", 2021, 2023, "index"),  # Türkiye earthquake regions Index change
    "X255": lambda: group_change("TUR", "rest", 2021, 2023, "index"),  # Rest of Türkiye Index change
    "X256": lambda: region_n("NZL", 6, 2023) + region_n("NZL", 5, 2023),  # Hawke's Bay and Tairāwhiti/Gisborne respondents 2023
    "X257": lambda: did("TUR", "community", "est"),  # Türkiye community dimension fell further
    "X258": lambda: did("TUR", "neighbours", "est"),  # Türkiye neighbours rose further
    "X259": lambda: pooled("seven", "neighbours", "est"),  # Pooled neighbours
    "X260": lambda: did("TUR", "societal", "est"),  # Türkiye societal
    "X261": lambda: did("MOZ", "societal", "est"),  # Mozambique societal
    "X262": lambda: did("PAK", "societal", "est"),  # Pakistan societal
    "X263": lambda: did("MAR", "societal", "est"),  # Morocco societal ('flat')
    "X264": lambda: pooled("seven", "societal", "est"),  # Pooled societal
    "X265": lambda: did("TUR", "community", "est"),  # Türkiye community
    "X266": lambda: did("NZL", "community", "est"),  # New Zealand community
    "X267": lambda: did("PAK", "community", "est"),  # Pakistan community
    "X268": lambda: max(abs(did("MAR", "community", "est")), abs(did("MOZ", "community", "est")), abs(did("ECU", "community", "est")), abs(did("ZAF", "community", "est"))),  # Other four case studies within three points of zero (largest absolute value)
    "X269": lambda: pooled("seven", "community", "est"),  # Pooled community
    "X270": lambda: n_sig_cases("household"),  # Household: case studies larger than the margin of error
    "X271": lambda: did("ZAF", "household", "est"),  # South Africa household
    "X272": lambda: did("ECU", "household", "est"),  # Ecuador household
    "X273": lambda: group_change("MAR", "aff", 2021, 2023, "household"),  # Marrakech-Safi household change
    "X274": lambda: group_change("MAR", "rest", 2021, 2023, "household"),  # Rest of Morocco household change
    "X275": lambda: pooled("seven", "household", "est"),  # Pooled household
    "X276": lambda: did("MAR", "individual", "est"),  # Morocco individual
    "X277": lambda: did("MOZ", "individual", "est"),  # Mozambique individual
    "X278": lambda: did("TUR", "individual", "est"),  # Türkiye individual
    "X279": lambda: pooled("seven", "individual", "est"),  # Pooled individual
    "X280": lambda: did("TUR", "societal", "est"),  # Chart 3.1 subtitle: Türkiye societal
    "X281": lambda: did("MOZ", "societal", "est"),  # Chart 3.1 subtitle: Mozambique societal
    "X282": lambda: pooled("seven", "community", "est"),  # Chart 3.1 subtitle: pooled community
    "X283": lambda: did("ZAF", "confidence", "est"),  # KwaZulu-Natal confidence relative rise
    "X284": lambda: pooled("seven", "confidence", "est"),  # Pooled five cases: confidence
    "X285": lambda: did("TUR", "confidence", "est"),  # Chart 3.2 subtitle: Türkiye
    "X286": lambda: did("ZAF", "confidence", "est"),  # Chart 3.2 subtitle: KwaZulu-Natal
    "X287": lambda: did("NZL", "confidence", "est"),  # New Zealand confidence gap
    "X288": lambda: did("MOZ", "confidence", "est"),  # Mozambique confidence rose further
    "X289": lambda: did("MOZ", "gov", "est"),  # Mozambique government cares 'a lot' rose further
    "X290": lambda: n_positive_did("neighbours"),  # Case studies where neighbours rose relative ('four of the seven')
    "X291": lambda: did("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours
    "X292": lambda: did("MOZ", "neighbours", "est"),  # Mozambique neighbours
    "X293": lambda: did("TUR", "neighbours", "est"),  # Türkiye neighbours
    "X294": lambda: did("MAR", "neighbours", "est"),  # Morocco neighbours
    "X295": lambda: did("NZL", "neighbours", "est"),  # New Zealand neighbours ('other way by five')
    "X296": lambda: did("PAK", "neighbours", "est"),  # Pakistan neighbours
    "X297": lambda: did("ECU", "neighbours", "est"),  # Ecuador neighbours
    "X298": lambda: pooled("seven", "neighbours", "est"),  # Pooled seven cases neighbours
    "X299": lambda: pooled("six_noZAF", "neighbours", "est"),  # Pooled without KwaZulu-Natal ('halves to four')
    "X300": lambda: pooled("seven", "neighbours", "est"),  # Chart 3.3 subtitle: pooled
    "X301": lambda: did("ZAF", "neighbours", "est"),  # Chart 3.3 subtitle: KwaZulu-Natal
    "X302": lambda: did("NZL", "neighbours", "est"),  # Northland and Auckland neighbours fell relative
    "X303": lambda: did("TUR", "community", "est"),  # Chart 3.4 subtitle: Türkiye community
    "X304": lambda: did("TUR", "neighbours", "est"),  # Chart 3.4 subtitle: Türkiye neighbours
    "X305": lambda: region_mean("PAK", 1, 2021, "neighbours"),  # Sindh neighbours 'a lot' 2021
    "X306": lambda: region_mean("PAK", 1, 2023, "neighbours"),  # Sindh neighbours 'a lot' 2023
    "X307": lambda: region_mean("PAK", 2, 2021, "neighbours"),  # Punjab neighbours 'a lot' 2021
    "X308": lambda: region_mean("PAK", 2, 2023, "neighbours"),  # Punjab neighbours 'a lot' 2023
    "X309": lambda: did("PAK", "neighbours", "est"),  # Pakistan neighbours gap change
    "X310": lambda: pooled("seven", "protect", "est"),  # Chart 3.5 subtitle: pooled could protect
    "X311": lambda: pooled("seven", "protect", "est"),  # Pooled could protect
    "X312": lambda: national("MAR", "protect", 2021),  # Morocco could protect, national 2021
    "X313": lambda: national("MAR", "protect", 2023),  # Morocco could protect, national 2023
    "X314": lambda: national("MAR", "protect", 2023) - national("MAR", "protect", 2021),  # Morocco national fall
    "X315": lambda: group_change("MAR", "aff", 2021, 2023, "protect"),  # Marrakech-Safi fall
    "X316": lambda: group_change("MAR", "rest", 2021, 2023, "protect"),  # Rest of Morocco fall
    "X317": lambda: did("MAR", "protect", "est"),  # Morocco gap
    "X318": lambda: group_change("TUR", "aff", 2021, 2023, "protect"),  # Türkiye earthquake regions change
    "X319": lambda: group_change("TUR", "rest", 2021, 2023, "protect"),  # Rest of Türkiye change
    "X320": lambda: did("ZAF", "protect", "est"),  # South Africa could protect relative
    "X321": lambda: did("ECU", "protect", "est"),  # Ecuador could protect relative
    "X322": lambda: national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Chart 3.6 subtitle: Thailand confidence rise
    "X323": lambda: national("THA", "expo", 2023),  # Thailand reported a disaster in past five years, 2023
    "X324": lambda: national("THA", "index", 2023) - national("THA", "index", 2021),  # Thailand Index change
    "X325": lambda: national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Thailand confidence change
    "X326": lambda: national("THA", "confidence", 2021),  # Thailand confidence 2021
    "X327": lambda: national("THA", "confidence", 2023),  # Thailand confidence 2023
    "X328": lambda: national("PHL", "confidence", 2023) - national("PHL", "confidence", 2021),  # Philippines confidence change
    "X329": lambda: national("PHL", "index", 2023) - national("PHL", "index", 2021),  # Philippines Index change
    "X330": lambda: national("LBN", "index", 2021),  # Lebanon Index 2021
    "X331": lambda: national("LBN", "index", 2023),  # Lebanon Index 2023
    "X332": lambda: national("LBN", "community", 2023) - national("LBN", "community", 2021),  # Lebanon community dimension change
    "X333": lambda: national("LBN", "household", 2023) - national("LBN", "household", 2021),  # Lebanon household dimension change
    "X334": lambda: national("LBN", "individual", 2023) - national("LBN", "individual", 2021),  # Lebanon individual dimension change
    "X335": lambda: national("LBN", "societal", 2023) - national("LBN", "societal", 2021),  # Lebanon societal dimension change
    "X336": lambda: national("LBN", "confidence", 2021),  # Lebanon confidence 2021
    "X337": lambda: national("LBN", "confidence", 2023),  # Lebanon confidence 2023
    "X338": lambda: national("LBN", "gov", 2021),  # Lebanon government cares 'a lot' 2021
    "X339": lambda: national("LBN", "gov", 2023),  # Lebanon government cares 'a lot' 2023
    "X340": lambda: national("LBN", "protect", 2021),  # Lebanon could protect 2021
    "X341": lambda: national("LBN", "protect", 2023),  # Lebanon could protect 2023
    "X342": lambda: national("LBN", "expo", 2021),  # Lebanon reported a disaster 2021
    "X343": lambda: national("LBN", "expo", 2023),  # Lebanon reported a disaster 2023
    "X344": lambda: national("LBN", "expo", 2023) / national("LBN", "expo", 2021),  # Lebanon reported disaster 'doubled' (2023 / 2021)
    "X345": lambda: earthquake_share("LBN", 2023),  # Lebanon 2023 disaster reports naming an earthquake
    "X346": lambda: pooled("seven", "neighbours", "est"),  # Pooled neighbours
    "X347": lambda: pooled("seven", "community", "est"),  # Pooled community ('about three points')
    "X348": lambda: pooled("seven", "protect", "est"),  # Pooled could protect
    "X349": lambda: national("MAR", "protect", 2023) - national("MAR", "protect", 2021),  # Morocco national fall in could protect
    "X350": lambda: gap("TUR", "confidence", 2023),  # Türkiye confidence gap 2023
    "X351": lambda: gap("TUR", "confidence", 2025),  # Türkiye confidence gap 2025
    "X352": lambda: gap("ZAF", "index", 2021),  # South Africa baseline Index gap ('three points below')
    "X353": lambda: gap("NZL", "index", 2021),  # New Zealand baseline Index gap ('two points above')
    "X354": lambda: mean_in("MAR", "expo", 2025, "aff"),  # Marrakech-Safi impacted by a disaster, 2025
    "X355": lambda: mean_in("MAR", "expo", 2025, "rest"),  # Rest of Morocco impacted, 2025
    "X356": lambda: hazard_share("MAR", "aff", 7),  # Marrakech-Safi impacted respondents naming an earthquake
    "X357": lambda: n_impacted("MAR", "aff"),  # Marrakech-Safi impacted respondents
    "X358": lambda: mean_in("ZAF", "expo", 2025, "aff"),  # KwaZulu-Natal impacted 2025
    "X359": lambda: mean_in("ZAF", "expo", 2025, "rest"),  # Rest of South Africa impacted 2025
    "X360": lambda: mean_in("NZL", "expo", 2025, "aff"),  # Northland and Auckland impacted 2025
    "X361": lambda: mean_in("NZL", "expo", 2025, "rest"),  # Rest of New Zealand impacted 2025
    "X362": lambda: mean_in("TUR", "expo", 2025, "aff"),  # Türkiye earthquake regions impacted 2025
    "X363": lambda: mean_in("TUR", "expo", 2025, "rest"),  # Rest of Türkiye impacted 2025
    "X364": lambda: region_mean("TUR", 12, 2025, "expo"),  # Southeast Anatolia impacted 2025
    "X365": lambda: hazard_share("TUR", 12, 7),  # Southeast Anatolia impacted respondents naming an earthquake
    "X366": lambda: n_impacted("TUR", 12),  # Southeast Anatolia impacted respondents
    "X367": lambda: hazard_all("TUR", 12, 7),  # Southeast Anatolia: all adults impacted by an earthquake
    "X368": lambda: region_mean("NZL", 6, 2025, "expo"),  # Hawke's Bay impacted 2025
    "X369": lambda: hazard_share("NZL", 6, 2),  # Hawke's Bay impacted respondents naming a tropical storm
    "X370": lambda: n_impacted("NZL", 6),  # Hawke's Bay impacted respondents
    "X371": lambda: hazard_all("NZL", 6, 2),  # Hawke's Bay: all adults impacted by a tropical storm
    "X372": lambda: region_n("NZL", 6, 2025),  # Hawke's Bay sample 2025
    "X373": lambda: gap("TUR", "index", 2021),  # Türkiye Index gap 2021
    "X374": lambda: gap("TUR", "index", 2023),  # Türkiye Index gap 2023
    "X375": lambda: gap("TUR", "index", 2025),  # Türkiye Index gap 2025
    "X376": lambda: gap("MAR", "index", 2025) - gap("MAR", "index", 2021),  # Marrakech-Safi ends above its own baseline (gap 2025 minus 2021)
    "X377": lambda: gap("NZL", "index", 2021),  # New Zealand Index gap 2021
    "X378": lambda: gap("NZL", "index", 2023),  # New Zealand Index gap 2023
    "X379": lambda: gap("NZL", "index", 2025),  # New Zealand Index gap 2025
    "X380": lambda: chg("NZL", "index", "est"),  # New Zealand Index gap change 2023-2025 ('no change at all')
    "X381": lambda: aff_n("NZL", 2025),  # New Zealand affected respondents 2025
    "X382": lambda: gap("NZL", "index", 2025) - gap("NZL", "index", 2021),  # New Zealand 2025 gap below the 2021 baseline
    "X383": lambda: moe_index_gap("MAR", 2023),  # Chart 4.1 note: margin of error on the Index gap at 132 respondents
    "X384": lambda: gap("TUR", "societal", 2023) - gap("TUR", "societal", 2021),  # Türkiye societal gap widened 2021-2023
    "X385": lambda: chg("TUR", "societal", "est"),  # Türkiye societal gap narrowed 2023-2025
    "X386": lambda: gap("TUR", "societal", 2025) - gap("TUR", "societal", 2021),  # Türkiye societal: remaining compared with 2021
    "X387": lambda: gap("MAR", "individual", 2023),  # Marrakech-Safi individual gap 2023
    "X388": lambda: gap("MAR", "individual", 2025),  # Marrakech-Safi individual gap 2025
    "X389": lambda: gap("MAR", "individual", 2025) - gap("MAR", "individual", 2021),  # Marrakech-Safi individual 2025 minus baseline ('level with its baseline')
    "X390": lambda: gap("NZL", "individual", 2023),  # New Zealand individual gap 2023
    "X391": lambda: gap("NZL", "individual", 2025),  # New Zealand individual gap 2025
    "X392": lambda: gap("NZL", "individual", 2025) - gap("NZL", "individual", 2021),  # New Zealand individual 2025 minus baseline
    "X393": lambda: gap("MAR", "household", 2025),  # Morocco household gap 2025
    "X394": lambda: gap("MAR", "household", 2021),  # Morocco household gap 2021
    "X395": lambda: max(abs(gap("TUR", "household", 2021)), abs(gap("TUR", "household", 2023)), abs(gap("TUR", "household", 2025))),  # Türkiye household gaps within about two points of zero (largest absolute)
    "X396": lambda: max(abs(gap("NZL", "household", 2021)), abs(gap("NZL", "household", 2023)), abs(gap("NZL", "household", 2025))),  # New Zealand household gaps within about two points of zero (largest absolute)
    "X397": lambda: gap("TUR", "community", 2023),  # Türkiye community gap 2023
    "X398": lambda: gap("TUR", "community", 2023) - gap("TUR", "community", 2021),  # Türkiye community 2023 below its 2021 baseline
    "X399": lambda: chg("TUR", "community", "est"),  # Türkiye community recovered 2023-2025
    "X400": lambda: chg("TUR", "confidence", "est"),  # Chart 4.3 subtitle: Türkiye confidence narrows
    "X401": lambda: chg("ZAF", "neighbours", "est"),  # Chart 4.3 subtitle: KwaZulu-Natal neighbours fall
    "X402": lambda: tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025
    "X403": lambda: gap("TUR", "confidence", 2021),  # Türkiye confidence gap 2021
    "X404": lambda: gap("TUR", "confidence", 2023),  # Türkiye confidence gap 2023
    "X405": lambda: gap("TUR", "confidence", 2025),  # Türkiye confidence gap 2025
    "X406": lambda: chg("TUR", "confidence", "est"),  # Türkiye confidence narrowing
    "X407": lambda: gap("TUR", "confidence", 2025) - gap("TUR", "confidence", 2021),  # Türkiye confidence gap remaining against 2021
    "X408": lambda: chg("NZL", "confidence", "est"),  # New Zealand confidence change
    "X409": lambda: chg("TUR", "gov", "est"),  # Türkiye government cares 'a lot' narrowing
    "X410": lambda: national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Thailand national confidence rise
    "X411": lambda: gap("TUR", "neighbours", 2023),  # Türkiye neighbours gap 2023
    "X412": lambda: gap("TUR", "neighbours", 2025),  # Türkiye neighbours gap 2025
    "X413": lambda: chg("TUR", "neighbours", "est"),  # Türkiye neighbours change
    "X414": lambda: pooled3("three", "neighbours", "change"),  # Pooled three: neighbours change 2023-2025
    "X415": lambda: chg("MAR", "protect", "est"),  # Morocco could protect change 2023-2025
    "X416": lambda: chg("TUR", "protect", "est"),  # Türkiye could protect change 2023-2025
    "X417": lambda: chg("NZL", "protect", "est"),  # New Zealand could protect change 2023-2025
    "X418": lambda: region_change("TUR", 11, 2023, 2025, "index"),  # Türkiye Central East Anatolia Index change 2023-2025
    "X419": lambda: region_change("TUR", 6, 2023, 2025, "index"),  # Türkiye Mediterranean Index change 2023-2025
    "X420": lambda: region_change("TUR", 3, 2023, 2025, "index"),  # Türkiye Aegean Index change 2023-2025
    "X421": lambda: region_change("TUR", 5, 2023, 2025, "index"),  # Türkiye West Anatolia Index change 2023-2025
    "X422": lambda: region_change("MAR", 7, 2023, 2025, "index"),  # Morocco Marrakech-Safi Index change 2023-2025
    "X423": lambda: region_change("MAR", 3, 2023, 2025, "index"),  # Morocco Fès-Meknès Index change 2023-2025
    "X424": lambda: region_change("MAR", 2, 2023, 2025, "index"),  # Morocco Oriental Index change 2023-2025
    "X425": lambda: region_change("MAR", 6, 2023, 2025, "index"),  # Morocco Casablanca-Settat Index change 2023-2025
    "X426": lambda: region_change("MAR", 9, 2023, 2025, "index"),  # Morocco Souss-Massa Index change 2023-2025
    "X427": lambda: region_change("MAR", 5, 2023, 2025, "index"),  # Morocco Béni Mellal-Khénifra Index change 2023-2025
    "X428": lambda: region_change("MAR", 4, 2023, 2025, "index"),  # Morocco Rabat-Salé-Kénitra Index change 2023-2025
    "X429": lambda: region_change("MAR", 8, 2023, 2025, "index"),  # Morocco Draa-Tafilalet Index change 2023-2025
    "X430": lambda: region_n("MAR", 8, 2025),  # Draa-Tafilalet sample ('about 50')
    "X431": lambda: gap("MAR", "index", 2023),  # Marrakech-Safi Index gap 2023
    "X432": lambda: abs(gap("MAR", "index", 2025)),  # Marrakech-Safi Index gap 2025 ('within two points')
    "X433": lambda: gap("MAR", "index", 2025) - gap("MAR", "index", 2021),  # Marrakech-Safi ends above its baseline
    "X434": lambda: gap("MAR", "individual", 2023),  # Marrakech-Safi individual gap 2023
    "X435": lambda: gap("MAR", "individual", 2025),  # Marrakech-Safi individual gap 2025
    "X436": lambda: chg("MAR", "individual", "est"),  # Marrakech-Safi individual recovery
    "X437": lambda: region_n("MAR", 10, 2025),  # Guelmim-Oued Noun sample ('about 20')
    "X438": lambda: region_change("MAR", 7, 2023, 2025, "index"),  # Chart 4.4 subtitle: Marrakech-Safi Index change
    "X439": lambda: gap("MAR", "index", 2023),  # Chart 4.4 subtitle: gap 2023
    "X440": lambda: abs(gap("MAR", "index", 2025)),  # Chart 4.4 subtitle: gap 2025 ('within two points')
    "X441": lambda: region_n("MAR", 10, 2023),  # Guelmim-Oued Noun respondents 2023
    "X442": lambda: region_n("MAR", 10, 2025),  # Guelmim-Oued Noun respondents 2025
    "X443": lambda: region_n("MAR", 8, 2023),  # Draa-Tafilalet respondents 2023
    "X444": lambda: region_n("MAR", 8, 2025),  # Draa-Tafilalet respondents 2025
    "X445": lambda: region_n("MAR", 9, 2023),  # Souss-Massa respondents 2023
    "X446": lambda: region_n("MAR", 9, 2025),  # Souss-Massa respondents 2025
    "X447": lambda: region_change("TUR", 11, 2023, 2025, "index"),  # Chart 4.5 subtitle: Central East Anatolia
    "X448": lambda: region_change("TUR", 6, 2023, 2025, "index"),  # Chart 4.5 subtitle: Mediterranean
    "X449": lambda: gap("TUR", "index", 2023),  # Chart 4.5 subtitle: gap 2023
    "X450": lambda: gap("TUR", "index", 2025),  # Chart 4.5 subtitle: gap 2025
    "X451": lambda: tur_unit_n(26, 2023),  # Southeast Anatolia 2023 respondents, all in the Mardin unit
    "X452": lambda: region_n("TUR", 12, 2025),  # Southeast Anatolia 2025 respondents
    "X453": lambda: tur_unit_n(13, 2023),  # Hatay, Kahramanmaraş and Osmaniye respondents 2023
    "X454": lambda: tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025
    "X455": lambda: region_n("TUR", 10, 2023),  # Northeast Anatolia respondents 2023
    "X456": lambda: region_n("TUR", 10, 2025),  # Northeast Anatolia respondents 2025
    "X457": lambda: region_n("TUR", 7, 2023),  # Central Anatolia respondents 2023
    "X458": lambda: region_n("TUR", 7, 2025),  # Central Anatolia respondents 2025
    "X459": lambda: region_n("TUR", 9, 2023),  # East Black Sea respondents 2023
    "X460": lambda: region_n("TUR", 9, 2025),  # East Black Sea respondents 2025
    "X461": lambda: region_change("TUR", 11, 2023, 2025, "index"),  # Türkiye Central East Anatolia Index change 2023-2025 (text)
    "X462": lambda: region_change("TUR", 6, 2023, 2025, "index"),  # Türkiye Mediterranean Index change 2023-2025 (text)
    "X463": lambda: region_change("TUR", 3, 2023, 2025, "index"),  # Türkiye Aegean Index change 2023-2025 (text)
    "X464": lambda: region_change("TUR", 5, 2023, 2025, "index"),  # Türkiye West Anatolia Index change 2023-2025 (text)
    "X465": lambda: region_change("TUR", 7, 2023, 2025, "index"),  # Türkiye Central Anatolia Index change 2023-2025 (text)
    "X466": lambda: region_change("TUR", 10, 2023, 2025, "index"),  # Türkiye Northeast Anatolia Index change 2023-2025 (text)
    "X467": lambda: region_change("TUR", 4, 2023, 2025, "index"),  # Türkiye East Marmara Index change 2023-2025 (text)
    "X468": lambda: region_change("TUR", 1, 2023, 2025, "index"),  # Türkiye Istanbul ('level') Index change 2023-2025 (text)
    "X469": lambda: gap("TUR", "index", 2021),  # Türkiye earthquake regions Index gap 2021
    "X470": lambda: gap("TUR", "index", 2023),  # Türkiye Index gap 2023
    "X471": lambda: gap("TUR", "index", 2025),  # Türkiye Index gap 2025
    "X472": lambda: did("TUR", "societal", "est"),  # Türkiye societal fell further by 2023
    "X473": lambda: chg("TUR", "societal", "est"),  # Türkiye societal recovered by 2025
    "X474": lambda: gap("TUR", "confidence", 2023),  # Türkiye confidence gap 2023
    "X475": lambda: gap("TUR", "confidence", 2025),  # Türkiye confidence gap 2025
    "X476": lambda: tur_unit_n(13, 2023),  # Hatay, Kahramanmaraş and Osmaniye respondents 2023 (text)
    "X477": lambda: tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025 (text)
    "X478": lambda: region_change("NZL", 1, 2023, 2025, "index"),  # Chart 4.6 subtitle: Northland Index change 2023-2025
    "X479": lambda: region_change("NZL", 2, 2023, 2025, "index"),  # Chart 4.6 subtitle: Auckland
    "X480": lambda: region_change("NZL", 1, 2023, 2025, "index"),  # New Zealand Northland Index change 2023-2025
    "X481": lambda: region_change("NZL", 2, 2023, 2025, "index"),  # New Zealand Auckland Index change 2023-2025
    "X482": lambda: region_change("NZL", 3, 2023, 2025, "index"),  # New Zealand Waikato Index change 2023-2025
    "X483": lambda: region_change("NZL", 4, 2023, 2025, "index"),  # New Zealand Bay of Plenty Index change 2023-2025
    "X484": lambda: region_change("NZL", 9, 2023, 2025, "index"),  # New Zealand Wellington ('flat') Index change 2023-2025
    "X485": lambda: region_change("NZL", 14, 2023, 2025, "index"),  # New Zealand Canterbury ('flat') Index change 2023-2025
    "X486": lambda: region_change("NZL", 15, 2023, 2025, "index"),  # New Zealand Otago ('flat') Index change 2023-2025
    "X487": lambda: chg("NZL", "index", "est"),  # New Zealand gap change 2023-2025 ('did not change at all')
    "X488": lambda: did("NZL", "index", "est"),  # Gap opened by 2023 ('three points')
    "X489": lambda: gap("NZL", "index", 2025) - gap("NZL", "index", 2021),  # Gap remains below 2021 ('three points')
    "X490": lambda: region_change("NZL", 6, 2023, 2025, "index"),  # Hawke's Bay Index change 2023-2025
    "X491": lambda: region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
    "X492": lambda: region_n("NZL", 6, 2025),  # Hawke's Bay respondents 2025
    "X493": lambda: region_change("NZL", 5, 2023, 2025, "index"),  # East Cape (Tairāwhiti) Index change 2023-2025
    "X494": lambda: region_n("NZL", 5, 2023),  # East Cape respondents 2023
    "X495": lambda: region_n("NZL", 5, 2025),  # East Cape respondents 2025
    "X496": lambda: n_hatched("NZL", 2023, 2025),  # Regions hatched ('ten of the 16')
    "X497": lambda: chg("NZL", "confidence", "est"),  # Confidence returned towards the rest of the country
    "X498": lambda: gap("NZL", "individual", 2023),  # Individual gap 2023
    "X499": lambda: gap("NZL", "individual", 2025),  # Individual gap 2025
    "X500": lambda: region_n("NZL", 1, 2023),  # Note: Northland respondents 2023
    "X501": lambda: region_n("NZL", 1, 2025),  # Note: Northland respondents 2025
    "X502": lambda: region_n("NZL", 6, 2023),  # Note: Hawke's Bay respondents 2023
    "X503": lambda: region_n("NZL", 6, 2025),  # Note: Hawke's Bay respondents 2025
    "X504": lambda: region_n("NZL", 5, 2023),  # Note: East Cape respondents 2023
    "X505": lambda: region_n("NZL", 5, 2025),  # Note: East Cape respondents 2025
    "X506": lambda: n_hatched("NZL", 2023, 2025),  # Note: regions hatched
    "X507": lambda: n_regions("NZL", 2023, 2025),  # Note: regions
    "X508": lambda: group_change("ZAF", "aff", 2023, 2025, "index"),  # Chart 4.7 subtitle: KwaZulu-Natal Index change 2023-2025
    "X509": lambda: group_change("ZAF", "rest", 2023, 2025, "index"),  # Chart 4.7 subtitle: rest of South Africa
    "X510": lambda: gap("ZAF", "index", 2023),  # Chart 4.7 subtitle: gap 2023 ('level')
    "X511": lambda: gap("ZAF", "index", 2025),  # Chart 4.7 subtitle: gap 2025
    "X512": lambda: did("ZAF", "index", "est"),  # KwaZulu-Natal Index difference-in-differences 2021-2023
    "X513": lambda: gap("ZAF", "index", 2021),  # KwaZulu-Natal Index gap 2021
    "X514": lambda: gap("ZAF", "index", 2023),  # KwaZulu-Natal Index gap 2023 ('level')
    "X515": lambda: did("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours relative rise 2021-2023
    "X516": lambda: mean_in("ZAF", "expo", 2025, "aff"),  # KwaZulu-Natal impacted 2025
    "X517": lambda: mean_in("ZAF", "expo", 2025, "rest"),  # Rest of South Africa impacted 2025
    "X518": lambda: hazard_share("ZAF", "aff", 1),  # KwaZulu-Natal impacted naming a flood
    "X519": lambda: hazard_share("ZAF", "aff", 2),  # KwaZulu-Natal impacted naming a tropical storm
    "X520": lambda: n_regions_rose("ZAF", 2023, 2025),  # Provinces that rose 2023-2025 ('every province')
    "X521": lambda: region_change("ZAF", 4, 2023, 2025, "index"),  # KwaZulu-Natal Index change 2023-2025
    "X522": lambda: region_change("ZAF", 8, 2023, 2025, "index"),  # Northern Cape Index change 2023-2025
    "X523": lambda: region_n("ZAF", 8, 2025),  # Northern Cape sample ('about 40')
    "X524": lambda: region_change("ZAF", 6, 2023, 2025, "index"),  # Mpumalanga Index change
    "X525": lambda: region_change("ZAF", 7, 2023, 2025, "index"),  # North West Index change
    "X526": lambda: region_change("ZAF", 9, 2023, 2025, "index"),  # Western Cape Index change
    "X527": lambda: gap("ZAF", "index", 2025),  # KwaZulu-Natal Index gap 2025
    "X528": lambda: gap("ZAF", "neighbours", 2023),  # Neighbours gap 2023
    "X529": lambda: chg("ZAF", "neighbours", "est"),  # Neighbours change 2023-2025
    "X530": lambda: chg("ZAF", "community", "est"),  # Community dimension change 2023-2025
    "X531": lambda: gap("ZAF", "community", 2025) - gap("ZAF", "community", 2021),  # Community gap 2025 below 2021 baseline
    "X532": lambda: did("ZAF", "confidence", "est"),  # Confidence relative rise 2021-2023
    "X533": lambda: gap("ZAF", "confidence", 2025),  # Confidence gap 2025
    "X534": lambda: n_returned("ZAF"),  # Measures that returned towards or past their 2021 position ('seven of the nine')
    "X535": lambda: gap("ZAF", "household", 2025) - gap("ZAF", "household", 2021),  # Household gap above 2021 baseline
    "X536": lambda: gap("ZAF", "protect", 2025) - gap("ZAF", "protect", 2021),  # Could protect gap above 2021 baseline
    "X537": lambda: region_n("ZAF", 8, 2023),  # Note: Northern Cape respondents 2023
    "X538": lambda: region_n("ZAF", 8, 2025),  # Note: Northern Cape respondents 2025
    "X539": lambda: region_n("ZAF", 6, 2023),  # Note: Mpumalanga respondents 2023
    "X540": lambda: region_n("ZAF", 6, 2025),  # Note: Mpumalanga respondents 2025
    "X541": lambda: pooled3("three", "index", "change"),  # Pooled three: Index gap narrower than in 2023
    "X542": lambda: pooled3("three", "confidence", "c2023"),  # Türkiye and New Zealand: confidence change in the gap by 2023
    "X543": lambda: pooled3("three", "confidence", "c2025"),  # Türkiye and New Zealand: confidence change in the gap by 2025
    "X544": lambda: pooled3("three", "confidence", "change"),  # Confidence narrowing ('11 percentage points')
    "X545": lambda: max(abs(pooled3("three", "household", "c2023")), abs(pooled3("three", "household", "c2025")), abs(pooled3("three", "household", "change")), abs(pooled3("three", "individual", "c2023")), abs(pooled3("three", "individual", "c2025")), abs(pooled3("three", "individual", "change"))),  # Household and individual change by a point or less (largest absolute)
    "X546": lambda: pooled3("three", "neighbours", "c2023"),  # Neighbours change in the gap by 2023
    "X547": lambda: mean_in("ZAF", "worry", 2025, "aff"),  # Chart 4.8 subtitle: KwaZulu-Natal Worry Index
    "X548": lambda: mean_in("ZAF", "worry", 2025, "rest"),  # Chart 4.8 subtitle: rest of South Africa Worry Index
    "X549": lambda: n_valid("MAR", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, MAR
    "X550": lambda: n_valid("TUR", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, TUR
    "X551": lambda: n_valid("NZL", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, NZL
    "X552": lambda: n_valid("ZAF", "worry", 2025, "aff"),  # Chart 4.8 note: affected-region respondents with a Worry Index score, ZAF
    "X553": lambda: gap("MAR", "worry", 2025),  # Morocco worry gap
    "X554": lambda: gap("TUR", "worry", 2025),  # Türkiye worry gap
    "X555": lambda: gap("NZL", "worry", 2025),  # New Zealand worry gap
    "X556": lambda: gap("ZAF", "worry", 2025),  # South Africa worry gap
    "X557": lambda: pooled("prep3", "prep", "est"),  # Chart 4.9 subtitle: pooled well prepared change
    "X558": lambda: mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions well prepared 2021
    "X559": lambda: mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions well prepared 2025
    "X560": lambda: mean_in("TUR", "prep", 2021, "rest"),  # Rest of Türkiye well prepared 2021
    "X561": lambda: mean_in("TUR", "prep", 2025, "rest"),  # Rest of Türkiye well prepared 2025
    "X562": lambda: gap("TUR", "prep", 2021),  # Türkiye well prepared gap 2021
    "X563": lambda: gap("TUR", "prep", 2025),  # Türkiye well prepared gap 2025
    "X564": lambda: gap("TUR", "prep", 2025) - gap("TUR", "prep", 2021),  # Türkiye well prepared change in the gap
    "X565": lambda: gap("NZL", "prep", 2025) - gap("NZL", "prep", 2021),  # New Zealand well prepared change in the gap
    "X566": lambda: mean_in("ZAF", "prep", 2021, "aff"),  # KwaZulu-Natal well prepared 2021
    "X567": lambda: mean_in("ZAF", "prep", 2025, "aff"),  # KwaZulu-Natal well prepared 2025
    "X568": lambda: mean_in("ZAF", "prep", 2021, "rest"),  # Rest of South Africa well prepared 2021
    "X569": lambda: mean_in("ZAF", "prep", 2025, "rest"),  # Rest of South Africa well prepared 2025
    "X570": lambda: pooled("prep3", "prep", "est"),  # Pooled three countries well prepared
    "X571": lambda: pooled("prep2", "prep", "est"),  # Pooled Türkiye and New Zealand well prepared
    "X572": lambda: mean_in("TUR", "local_prep", 2025, "aff"),  # Türkiye earthquake regions: local government well prepared 2025
    "X573": lambda: mean_in("TUR", "local_prep", 2025, "rest"),  # Rest of Türkiye: local government well prepared 2025
    "X574": lambda: gap("NZL", "local_prep", 2025),  # New Zealand local government well prepared gap 2025
    "X575": lambda: chg("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours fall
    "X576": lambda: n_returned("ZAF"),  # Measures returned towards 2021 ('seven of the nine')
    "X577": lambda: chg("TUR", "confidence", "est"),  # Türkiye confidence narrowing
    "X578": lambda: gap("TUR", "prep", 2025) - gap("TUR", "prep", 2021),  # Türkiye well prepared fell further 2021-2025
    "X579": lambda: gap("NZL", "prep", 2025) - gap("NZL", "prep", 2021),  # Northland and Auckland well prepared fell further
    "X580": lambda: chg("TUR", "confidence", "est"),  # Türkiye confidence narrowing (31 months)
    "X581": lambda: chg("NZL", "confidence", "est"),  # New Zealand confidence narrowing
    "X582": lambda: did("TUR", "confidence", "est"),  # Türkiye confidence fell further
    "X583": lambda: did("NZL", "confidence", "est"),  # New Zealand confidence fell further
    "X584": lambda: did("MOZ", "gov", "est"),  # Mozambique government cares 'a lot'
    "X585": lambda: national("THA", "confidence", 2023) - national("THA", "confidence", 2021),  # Thailand confidence rise
    "X586": lambda: n_positive_did("neighbours"),  # Neighbours rose in four of the seven case studies
    "X587": lambda: pooled("seven", "protect", "est"),  # Pooled could protect
    "X588": lambda: pooled3("three", "confidence", "change"),  # Confidence narrowing across Türkiye and New Zealand
    "X589": lambda: pooled("prep3", "prep", "est"),  # Pooled well prepared fell further
    "X590": lambda: pooled3("three", "index", "change"),  # Pooled three: Index gap narrowed
    "X591": lambda: chg("NZL", "index", "est"),  # New Zealand Index gap did not change
    "X592": lambda: chg("ZAF", "neighbours", "est"),  # KwaZulu-Natal neighbours fall
    "X593": lambda: national("TUR", "index", 2021),  # Türkiye national Index
    "X594": lambda: did("TUR", "societal", "est"),  # Türkiye societal fell further
    "X595": lambda: pooled("seven", "index", "est"),  # Pooled Index ('about two')
    "X596": lambda: n_negative_did("index"),  # Six of the seven
    "X597": lambda: chg("TUR", "confidence", "est"),  # Türkiye confidence narrowed
    "X598": lambda: mean_in("TUR", "prep", 2021, "aff"),  # Türkiye earthquake regions well prepared 2021
    "X599": lambda: mean_in("TUR", "prep", 2025, "aff"),  # Türkiye earthquake regions well prepared 2025
    "X600": lambda: mean_in("TUR", "prep", 2021, "rest"),  # Rest of Türkiye well prepared 2021
    "X601": lambda: mean_in("TUR", "prep", 2025, "rest"),  # Rest of Türkiye well prepared 2025
    "X602": lambda: pooled("seven", "neighbours", "est"),  # Pooled neighbours
    "X603": lambda: n_affected_provinces_unsurveyed(),  # Turkish affected provinces with no 2023 respondents
    "X604": lambda: n_cases_asked("confidence"),  # Case studies that asked confidence in national government in both waves
    "X605": lambda: min(n_cases_asked("gov"), n_cases_asked("neighbours"), n_cases_asked("protect")),  # Case studies that asked the other three questions
    "X606": lambda: it_depends("THA", 2023),  # 'It depends' on the protect question: Thailand, 2023
    "X607": lambda: it_depends("LBN", 2023),  # 'It depends' on the protect question: Lebanon, 2023
    "X608": lambda: did("ECU", "expo", "est"),  # Ecuador: reported experience fell faster inside Guayas and El Oro
    "X609": lambda: prov_expo_2025("MOZ", "nampula"),  # Mozambique 2025: Nampula impacted
    "X610": lambda: prov_expo_2025("MOZ", "affected"),  # Mozambique 2025: Zambezia, Sofala and Manica impacted
    "X611": lambda: prov_expo_2025("PAK", "kp"),  # Pakistan 2025: Khyber Pakhtunkhwa impacted
    "X612": lambda: prov_expo_2025("PAK", "sindh"),  # Pakistan 2025: Sindh impacted
    "X613": lambda: mean_in("ZAF", "expo", 2025, "aff"),  # KwaZulu-Natal impacted 2025
    "X614": lambda: mean_in("ZAF", "expo", 2025, "rest"),  # Rest of South Africa impacted 2025
    "X615": lambda: prov_expo_2025("ECU", "affected"),  # Ecuador 2025: Guayas and El Oro impacted
    "X616": lambda: prov_expo_2025("ECU", "rest"),  # Ecuador 2025: rest of Ecuador impacted
    "X617": lambda: pooled("six_noECU", "index", "est"),  # Without Ecuador: pooled Index ('about one')
    "X618": lambda: pooled("six_noECU", "index", "lo"),  # Without Ecuador: pooled Index, HC1 lower
    "X619": lambda: pooled("six_noECU", "index", "hi"),  # Without Ecuador: pooled Index, HC1 upper
    "X620": lambda: pooled("six_noECU", "community", "est"),  # Without Ecuador: community ('about three points')
    "X621": lambda: pooled("six_noECU", "community", "lo"),  # Without Ecuador: community, HC1 lower
    "X622": lambda: pooled("six_noECU", "community", "hi"),  # Without Ecuador: community, HC1 upper
    "X623": lambda: pooled("seven", "neighbours", "est"),  # Seven cases: neighbours ('seven')
    "X624": lambda: pooled("six_noECU", "neighbours", "est"),  # Without Ecuador: neighbours ('nine')
    "X625": lambda: pooled("six_noECU", "neighbours", "lo"),  # Without Ecuador: neighbours, HC1 lower
    "X626": lambda: pooled("six_noECU", "neighbours", "hi"),  # Without Ecuador: neighbours, HC1 upper
    "X627": lambda: slope("months", "est"),  # Slope of the Index change on months from event to fieldwork
    "X628": lambda: slope("months", "lo"),  # Months slope, 95% CI lower
    "X629": lambda: slope("months", "hi"),  # Months slope, 95% CI upper
    "X630": lambda: slope("expo", "est"),  # Slope on the strength of the exposure check
    "X631": lambda: slope("expo", "lo"),  # Exposure-check slope, 95% CI lower
    "X632": lambda: slope("expo", "hi"),  # Exposure-check slope, 95% CI upper
    "X633": lambda: n_pooled_resp("seven"),  # Respondents behind the seven-case estimates ('about 14,000')
    "X634": lambda: n_pooled_resp("five"),  # Respondents behind the confidence row ('about 10,000')
    "X635": lambda: n_clusters("total"),  # Region clusters across the seven countries
    "X636": lambda: n_clusters("min"),  # Fewest region clusters in a country
    "X637": lambda: n_clusters("max"),  # Most region clusters in a country
    "X638": lambda: n_cluster_only_sig(),  # Per-case estimates significant only with region clustering
    "X639": lambda: pooled("seven", "index", "lo"),  # Pooled seven cases, index: HC1 lower
    "X640": lambda: pooled("seven", "index", "hi"),  # Pooled seven cases, index: HC1 upper
    "X641": lambda: pooled("seven", "index", "clo"),  # Pooled seven cases, index: region-clustered lower
    "X642": lambda: pooled("seven", "index", "chi"),  # Pooled seven cases, index: region-clustered upper
    "X643": lambda: pooled("seven", "index", "plo"),  # Pooled seven cases, index: PSU-clustered lower
    "X644": lambda: pooled("seven", "index", "phi"),  # Pooled seven cases, index: PSU-clustered upper
    "X645": lambda: pooled("seven", "community", "lo"),  # Pooled seven cases, community: HC1 lower
    "X646": lambda: pooled("seven", "community", "hi"),  # Pooled seven cases, community: HC1 upper
    "X647": lambda: pooled("seven", "community", "clo"),  # Pooled seven cases, community: region-clustered lower
    "X648": lambda: pooled("seven", "community", "chi"),  # Pooled seven cases, community: region-clustered upper
    "X649": lambda: pooled("seven", "community", "plo"),  # Pooled seven cases, community: PSU-clustered lower
    "X650": lambda: pooled("seven", "community", "phi"),  # Pooled seven cases, community: PSU-clustered upper
    "X651": lambda: pooled("seven", "neighbours", "lo"),  # Pooled seven cases, neighbours: HC1 lower
    "X652": lambda: pooled("seven", "neighbours", "hi"),  # Pooled seven cases, neighbours: HC1 upper
    "X653": lambda: pooled("seven", "neighbours", "clo"),  # Pooled seven cases, neighbours: region-clustered lower
    "X654": lambda: pooled("seven", "neighbours", "chi"),  # Pooled seven cases, neighbours: region-clustered upper
    "X655": lambda: pooled("seven", "neighbours", "plo"),  # Pooled seven cases, neighbours: PSU-clustered lower
    "X656": lambda: pooled("seven", "neighbours", "phi"),  # Pooled seven cases, neighbours: PSU-clustered upper
    "X657": lambda: n_multi_sig(),  # Pooled measures significant on more than one of the three standard errors
    "X658": lambda: pooled3("three", "index", "c2023_lo"),  # Pooled three-wave: widening to 2023, HC1 lower
    "X659": lambda: pooled3("three", "index", "c2023_hi"),  # Pooled three-wave: widening to 2023, HC1 upper
    "X660": lambda: pooled3("three", "index", "lo"),  # Pooled three-wave: narrowing 2023-2025, HC1 lower
    "X661": lambda: pooled3("three", "index", "hi"),  # Pooled three-wave: narrowing 2023-2025, HC1 upper
    "X662": lambda: pooled3("four", "index", "change"),  # All four case studies: Index narrowing ('zero')
    "X663": lambda: pooled3("four", "neighbours", "c2023"),  # All four: neighbours above the 2021 baseline by 2023
    "X664": lambda: pooled3("four", "neighbours", "c2025"),  # All four: neighbours above the 2021 baseline by 2025
    "X665": lambda: aff_n("MAR", 2021),  # Smallest affected region: Morocco 2021
    "X666": lambda: aff_n("MAR", 2023),  # Morocco 2023
    "X667": lambda: aff_n("MAR", 2025),  # Morocco 2025
    "X668": lambda: tur_unit_n(12, 2021),  # Adana and Mersin unit respondents 2021
    "X669": lambda: tur_unit_n(12, 2023),  # Adana and Mersin unit respondents 2023
    "X670": lambda: region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
    "X671": lambda: region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
    "X672": lambda: n_impacted("MAR", "aff"),  # Marrakech-Safi impacted respondents 2025
    "X673": lambda: n_impacted("TUR", 12),  # Southeast Anatolia impacted respondents 2025
    "X674": lambda: n_impacted("NZL", 6),  # Hawke's Bay impacted respondents 2025
    "X675": lambda: region_n("NZL", 6, 2025),  # Hawke's Bay sample 2025
    "X676": lambda: aff_n_range("min"),  # Smallest affected-region sample
    "X677": lambda: aff_n_range("max"),  # Largest affected-region sample
    "X678": lambda: moe_pct(aff_n_range("min")),  # Margin of error on a percentage at 132 respondents ('about nine')
    "X679": lambda: moe_index_gap("MAR", 2023),  # Margin of error on an Index score at 132 respondents ('about three')
    "X680": lambda: moe_pct(aff_n_range("max")),  # Margin of error on a percentage at 418 respondents ('about five')
    "X681": lambda: moe_index_gap("NZL", 2023),  # Margin of error on an Index score at 418 respondents ('about two')
    "X682": lambda: aff_n("ZAF", 2025),  # KwaZulu-Natal respondents 2025
    "X683": lambda: moe_pct(aff_n("ZAF", 2025)),  # Margin of error at 181 respondents ('roughly seven')
    "X684": lambda: n_affected_provinces_unsurveyed(),  # Officially affected Turkish provinces with no 2023 respondents
    "X685": lambda: tur_affected_share(2021),  # Affected regions made up of officially affected NUTS-2 units, 2021
    "X686": lambda: tur_affected_share(2023),  # Same, 2023
    "X687": lambda: tur_affected_share(2025),  # Same, 2025
    "X688": lambda: tur_unit_n(13, 2021),  # Hatay, Kahramanmaraş and Osmaniye respondents 2021
    "X689": lambda: tur_unit_n(13, 2023),  # Hatay, Kahramanmaraş and Osmaniye respondents 2023
    "X690": lambda: tur_unit_n(13, 2025),  # Hatay, Kahramanmaraş and Osmaniye respondents 2025
    "X691": lambda: region_n("TUR", 12, 2021),  # Southeast Anatolia respondents 2021
    "X692": lambda: region_n("TUR", 12, 2023),  # Southeast Anatolia respondents 2023
    "X693": lambda: region_n("TUR", 12, 2025),  # Southeast Anatolia respondents 2025
    "X694": lambda: tur_unit_n(26, 2023),  # Southeast Anatolia 2023 respondents from the Mardin unit
    "X695": lambda: region_n("NZL", 6, 2021),  # Hawke's Bay respondents 2021
    "X696": lambda: region_n("NZL", 6, 2023),  # Hawke's Bay respondents 2023
    "X697": lambda: region_n("NZL", 5, 2021),  # Tairāwhiti/Gisborne respondents 2021
    "X698": lambda: region_n("NZL", 5, 2023),  # Tairāwhiti/Gisborne respondents 2023
}
F.update(TEXT)

# Register every published finding (functions defined above but not published are skipped).
for fid in report.published.finding_id:
    report.finding(fid)(F[fid])

if __name__ == "__main__":
    sys.exit(report.run())
