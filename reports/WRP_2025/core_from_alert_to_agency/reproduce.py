"""Reproduce World Risk Poll 2026: From alert to agency: What turns warnings into action?

Run from the repository root:
    python reports/WRP_2025/core_from_alert_to_agency/reproduce.py

The report follows disasters from impact to response: who was impacted by a
disaster in the past five years (Chapter 1), whether they were warned and
through which channels (Chapter 2), and whether the warning let them act
(Chapter 3). Each function below computes one chart or text statement listed
in published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

# --- Variables -------------------------------------------------------------------

IMPACTED = "WP24213"   # impacted by a disaster in the past five years: 1 yes, 2 no
TYPE = "WP24180"       # type of the most impactful disaster
ACTED = "WP24215"      # able to take action ahead of the disaster because of the warning: 1 yes, 2 no
AGENCY = "WP22252"     # could protect yourself or family in a future disaster: 1 yes, 2 no, 3 it depends
PLAN = "WP23345"       # household disaster plan known to all over 10 years old: 1 yes, 2 no
# The eight warning channels, asked of everyone impacted whose most impactful disaster has a known type.
CHANNELS = {"internet": "WP24181", "television": "WP24183", "sms": "WP24186", "radio": "WP24182",
            "print": "WP24184", "megaphone": "WP24188", "whatsapp": "WP24185", "billboard": "WP24187"}
# 2023: experienced a disaster, its type, and the four warning sources.
EXPERIENCED_2023 = "WP23344"
TYPE_2023 = "WP22247"
SOURCES_2023 = ["WP22248", "WP22249", "WP22250", "WP22251"]
MOBILE = "WP17626"     # Gallup World Poll: has a mobile phone (1 = yes)
INTERNET = "WP16056"   # Gallup World Poll: has access to the internet (1 = yes)
YES = [1]

TYPES = {1: "flood", 2: "hurricane", 3: "tornado", 4: "thunderstorm", 5: "tsunami", 6: "mudslide", 7: "earthquake",
         8: "wildfire", 9: "volcano", 10: "blizzard", 50: "drought", 51: "heatwave", 52: "sandstorm", 53: "gale",
         96: "other_nature", 97: "other_not_nature"}
TYPES_2023 = {1: "flood", 2: "hurricane", 7: "earthquake"}
REGION = {1: "east_africa", 2: "cw_africa", 3: "north_africa", 4: "southern_africa", 5: "latam",
          6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia", 10: "southern_asia",
          11: "middle_east", 12: "eastern_europe", 13: "nw_europe", 14: "southern_europe", 15: "anz"}
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # 9 = not classified: left out
EDUCATION = {1: "primary", 2: "secondary", 3: "tertiary"}
PHL_REGION = {1: "ncr", 3: "balance_luzon", 4: "visayas", 5: "mindanao"}
NWARN = {0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six_plus"}
DIMS = {"index": "resilience_index_100", "individual": "resilience_idv", "household": "resilience_hhl",
        "community": "resilience_com", "societal": "resilience_soc"}

# Early Warnings for All: the 30 initial priority countries announced in 2023. Those with at
# least MIN_N respondents asked about warnings are the 13 in Chart 2.4.
EW4A = ["ATG", "BGD", "BRB", "KHM", "TCD", "COM", "DJI", "ECU", "ETH", "FJI", "GTM", "GUY", "HTI", "KIR", "LAO",
        "LBR", "MDG", "MDV", "MUS", "MOZ", "NPL", "NER", "WSM", "SOM", "SSD", "SDN", "TON", "TUV", "UGA", "VUT"]
MIN_N = 100  # "sufficient data": at least 100 respondents (countries, EW4A countries, Chart 2.9 regions)

d = load_wave(2025, ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel", "Education",
                     "REGION2_PHL", IMPACTED, TYPE, ACTED, AGENCY, PLAN, *CHANNELS.values(), *DIMS.values()])
d23 = load_wave(2023, ["COUNTRY_ISO3", "PROJWT", EXPERIENCED_2023, TYPE_2023, *SOURCES_2023])

# --- Derived variables -----------------------------------------------------------

for key, var in DIMS.items():
    d[key] = d[var] if key == "index" else 100 * d[var]

# The warning questions were asked of everyone impacted whose most impactful disaster has a
# type (not don't know or refused). "Warned" = yes to at least one channel; DK counts as no.
ASKED = d[CHANNELS["internet"]].notna()
d["warned"] = np.where(ASKED, (d[list(CHANNELS.values())] == 1).any(axis=1), np.nan)
d["n_warnings"] = np.where(ASKED, (d[list(CHANNELS.values())] == 1).sum(axis=1), np.nan)
d["n_warnings_6"] = d["n_warnings"].clip(upper=6)
d["region"] = d.GlobalRegion.map(REGION)

impacted = d[d[IMPACTED] == 1]
asked = d[ASKED]
warned = d[d[ACTED].notna()]  # the action question was asked of everyone warned


# --- Helpers ---------------------------------------------------------------------


def r0(x):
    """Round half up to a whole number, as printed (same rule in the R script)."""
    return float(np.floor(float(x) + 0.5 + 1e-9))


def lt1(v):
    """The report prints '<1' for a percentage that rounds to 0."""
    return "<1" if r0(v) == 0 else v


def keyed(series, keys):
    """Rename a by-group result's index with readable keys, dropping unknown groups."""
    return {keys[k]: v for k, v in series.items() if k in keys}


def type_shares(df, var=TYPE):
    """% naming each disaster type, with don't know and refused combined."""
    t = distribution(df, var)
    out = {name: t.get(code, 0.0) for code, name in TYPES.items()}
    out["dk_refused"] = t.get(98, 0.0) + t.get(99, 0.0)
    return out


def country_warned():
    """% warned by country, for countries with at least MIN_N respondents asked."""
    n = asked.groupby("COUNTRY_ISO3").size()
    s = pct(asked, "warned", YES, by="COUNTRY_ISO3")
    return s[n.reindex(s.index) >= MIN_N]


def ew4a_countries():
    n = asked.groupby("COUNTRY_ISO3").size()
    return [iso for iso in EW4A if n.get(iso, 0) >= MIN_N]


def gallup(df, items):
    return merge_gallup(df, items)


def unwarned_mobile():
    """The unwarned (asked about warnings, no channel) with the Gallup mobile phone item."""
    return gallup(asked[asked.warned == 0], [MOBILE])


# --- Text figures ----------------------------------------------------------------


@report.finding("X01")
def interviews():
    return len(d)


@report.finding("X02")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X03")
def experienced_2023():
    return pct(d23, EXPERIENCED_2023, YES)


@report.finding("X04")
def types_2023():
    t = distribution(d23[d23[EXPERIENCED_2023] == 1], TYPE_2023)
    return {name: t.get(code, 0.0) for code, name in TYPES_2023.items()}


@report.finding("X05")
def warned_2023():
    a = d23[d23[SOURCES_2023[0]].notna()].copy()
    a["warned"] = (a[SOURCES_2023] == 1).any(axis=1).astype(float)
    return pct(a, "warned", YES)


@report.finding("X06")
def impacted_extremes():
    s = pct(d, IMPACTED, YES, by="COUNTRY_ISO3")
    return {"highest": s.idxmax(), "lowest": s.idxmin(), "ISR": lt1(s["ISR"])}


@report.finding("X07")
def low_income_by_education():
    low = d[d.CountryIncomeLevel == 1]
    return keyed(pct(low, IMPACTED, YES, by="Education"), EDUCATION)


@report.finding("X08")
def philippines_types():
    t = type_shares(impacted[impacted.COUNTRY_ISO3 == "PHL"])
    return {k: t[k] for k in ("hurricane", "flood", "earthquake")}


@report.finding("X09")
def country_warning_extremes():
    s = country_warned().sort_values()
    out = {iso: s[iso] for iso in ("VNM", "HKG", "CHN", "COG", "GAB")}
    out["top3"] = ", ".join(sorted(s.index[-3:]))
    out["bottom2"] = ", ".join(sorted(s.index[:2]))
    return out


@report.finding("X10")
def ew4a_counts():
    s = pct(asked, "warned", YES, by="COUNTRY_ISO3")[ew4a_countries()]
    return {"countries": len(s), "two_thirds": int((s >= 200 / 3).sum()), "under_half": int((s < 50).sum())}


@report.finding("X11")
def acted_by_income():
    return keyed(pct(warned, ACTED, YES, by="CountryIncomeLevel"), INCOME)


@report.finding("X12")
def low_income_individual_by_impact():
    low = d[(d.CountryIncomeLevel == 1) & d[IMPACTED].isin([1, 2])]
    return keyed(wmean(low, "individual", by=IMPACTED), {1: "impacted", 2: "not_impacted"})


@report.finding("X13")
def warnings_by_mobile():
    g = gallup(asked, [MOBILE])
    return keyed(wmean(g, "n_warnings", by=MOBILE), {1: "yes", 2: "no"})


@report.finding("X14")
def warnings_by_internet():
    g = gallup(asked, [INTERNET])
    return keyed(wmean(g, "n_warnings", by=INTERNET), {1: "yes", 2: "no"})


@report.finding("X15")
def unwarned_with_mobile_millions():
    g = unwarned_mobile()
    return g.loc[g[MOBILE] == 1, "PROJWT"].sum() / 1e6


@report.finding("X16")
def regions_90_plus():
    s = keyed(pct(unwarned_mobile(), MOBILE, YES, by="GlobalRegion"), REGION)
    return sum(r0(v) >= 90 for v in s.values())


@report.finding("X17")
def unwarned_mobile_small_regions():
    s = keyed(pct(unwarned_mobile(), MOBILE, YES, by="GlobalRegion"), REGION)
    return {k: s[k] for k in ("northern_america", "anz")}


# --- Chapter 1: who is impacted ------------------------------------------------------


@report.finding("C1_1")
def chart_1_1():
    t = distribution(d, IMPACTED)
    return {"yes": t.get(1, 0.0), "no": t.get(2, 0.0)}


@report.finding("C1_2")
def chart_1_2():
    return {k: lt1(v) for k, v in type_shares(impacted).items()}


@report.finding("C1_3")
def chart_1_3():
    return keyed(pct(d, IMPACTED, YES, by="CountryIncomeLevel"), INCOME)


@report.finding("C1_4")
def chart_1_4():
    return keyed(pct(d, IMPACTED, YES, by="GlobalRegion"), REGION)


@report.finding("C1_5")
def chart_1_5():
    return pct(d, IMPACTED, YES, by="COUNTRY_ISO3")


@report.finding("C1_6")
def chart_1_6():
    p = impacted[impacted.COUNTRY_ISO3 == "PHL"]
    return {(PHL_REGION[r], name): v for code, name in ((2, "hurricane"), (1, "flood"), (7, "earthquake"))
            for r, v in pct(p, TYPE, [code], by="REGION2_PHL").items() if r in PHL_REGION}


# --- Chapter 2: who is warned ----------------------------------------------------------


@report.finding("C2_1")
def chart_2_1():
    v = pct(asked, "warned", YES)
    return {"yes": v, "no": 100 - v}


@report.finding("C2_2")
def chart_2_2():
    return keyed(pct(asked, "warned", YES, by="CountryIncomeLevel"), INCOME)


@report.finding("C2_3")
def chart_2_3():
    return keyed(pct(asked, "warned", YES, by="GlobalRegion"), REGION)


@report.finding("C2_4")
def chart_2_4():
    isos = ew4a_countries()
    w = pct(asked, "warned", YES, by="COUNTRY_ISO3")
    i = pct(d, IMPACTED, YES, by="COUNTRY_ISO3")
    return {**{f"warned_{iso}": w[iso] for iso in isos}, **{f"impacted_{iso}": i[iso] for iso in isos}}


@report.finding("C2_5")
def chart_2_5():
    return keyed(pct(asked, "warned", YES, by=TYPE), TYPES)


@report.finding("C2_6")
def chart_2_6():
    return {k: pct(asked, var, YES) for k, var in CHANNELS.items()}


@report.finding("C2_7")
def chart_2_7():
    return keyed(distribution(asked, "n_warnings_6"), NWARN)


@report.finding("C2_8")
def chart_2_8():
    return keyed(wmean(asked, "individual", by="n_warnings_6"), NWARN)


@report.finding("C2_9")
def chart_2_9():
    g = unwarned_mobile()
    return {"global": pct(g, MOBILE, YES), **keyed(pct(g, MOBILE, YES, by="GlobalRegion"), REGION)}


# --- Chapter 3: who acts ---------------------------------------------------------------


@report.finding("C3_1")
def chart_3_1():
    v = pct(warned, ACTED, YES)
    return {"yes": v, "no": 100 - v}


@report.finding("C3_2")
def chart_3_2():
    return keyed(pct(warned, ACTED, YES, by="GlobalRegion"), REGION)


@report.finding("C3_3")
def chart_3_3():
    return keyed(pct(warned, ACTED, YES, by=TYPE), TYPES)


@report.finding("C3_4")
def chart_3_4():
    out = {}
    for key in DIMS:
        m = wmean(warned, key, by=ACTED)
        out[f"{key}_acted"], out[f"{key}_not_acted"] = m[1], m[2]
        out[f"{key}_gap"] = r0(m[1]) - r0(m[2])
    return out


@report.finding("C3_5")
def chart_3_5():
    s = keyed(pct(warned, ACTED, YES, by="n_warnings_6"), NWARN)
    order = list(NWARN.values())[1:]
    changes = {f"change_{b}": r0(s[b]) - r0(s[a]) for a, b in zip(order, order[1:])}
    return {**s, **changes}


@report.finding("C3_6")
def chart_3_6():
    # Agency yes/no and plan yes/no; "it depends", don't know and refused are left out.
    w = warned.assign(agency=warned[AGENCY].map({1: 1, 2: 0}), plan=warned[PLAN].map({1: 1, 2: 0}))
    s = pct(w.dropna(subset=["agency", "plan"]), ACTED, YES, by=["plan", "agency"])
    keys = {(1, 1): "both", (1, 0): "plan_only", (0, 1): "agency_only", (0, 0): "neither"}
    return {keys[k]: v for k, v in s.items()}


if __name__ == "__main__":
    sys.exit(report.run())
