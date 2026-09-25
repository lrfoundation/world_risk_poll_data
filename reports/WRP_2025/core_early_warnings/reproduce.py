"""Reproduce World Risk Poll 2026: From alert to agency: What turns warnings into action?

Run from the repository root:
    python reports/WRP_2025/core_early_warnings/reproduce.py

The report uses the 2025 poll's disaster questions: whether the respondent was
impacted by a disaster in the past five years (WP24213), the type of the most
impactful one (WP24180), whether they were warned through each of eight
channels (WP24181-WP24188), whether they could act on the warning (WP24215),
and two preparedness items: could protect yourself or your family (WP22252)
and a household disaster plan (WP23345). It compares a few figures with the
2023 poll. Each function below computes one chart or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

IMPACTED, TYPE, ACT = "WP24213", "WP24180", "WP24215"  # 1 = yes, 2 = no, 98/99 = DK/refused
AGENCY, PLAN = "WP22252", "WP23345"  # could protect self/family; household plan (1 = yes, 2 = no)
CHANNELS = {"internet": "WP24181", "radio": "WP24182", "tv": "WP24183", "newspapers": "WP24184",
            "whatsapp": "WP24185", "sms": "WP24186", "billboard": "WP24187", "loudspeaker": "WP24188"}
PHONE, INTERNET = "WP17626", "WP16056"  # Gallup World Poll items (not in the public release): 1 = yes
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # CountryIncomeLevel (9 = not classified)
REGIONS = {  # GlobalRegion codes -> keys
    1: "eastern_africa", 2: "cw_africa", 3: "northern_africa", 4: "southern_africa", 5: "latam",
    6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia", 10: "southern_asia",
    11: "middle_east", 12: "eastern_europe", 13: "nw_europe", 14: "southern_europe", 15: "anz",
}
TYPES = {  # WP24180 codes -> keys (98 don't know and 99 refused are combined as "dk")
    1: "flood", 2: "hurricane", 3: "tornado", 4: "thunder", 5: "tsunami", 6: "landslide", 7: "earthquake",
    8: "wildfire", 9: "volcano", 10: "blizzard", 50: "drought", 51: "heatwave", 52: "sandstorm", 53: "gale",
    96: "other_nature", 97: "other_not_nature", 98: "dk",
}
TYPE_CODE = {v: k for k, v in TYPES.items()}
CHART_2_5 = ["hurricane", "heatwave", "sandstorm", "blizzard", "other_nature", "thunder", "wildfire", "gale",
             "tornado", "flood", "volcano", "drought", "earthquake", "landslide"]  # no tsunami or non-natural
CHART_3_3 = [t for t in CHART_2_5 if t != "tornado"]  # the bubbles in Chart 3.3
PHL_REGIONS = {1: "ncr", 3: "balance_luzon", 4: "visayas", 5: "mindanao"}  # REGION2_PHL
# The UN Early Warnings for All initiative's initial priority countries that were surveyed in 2025
# (the 2023 report lists 17; Tajikistan, Ethiopia, Liberia and Ecuador have too few respondents).
EW4A = ["BGD", "KHM", "TCD", "COM", "ECU", "ETH", "GTM", "LAO", "LBR", "MDG", "MUS", "MOZ", "NPL", "NER",
        "SOM", "TJK", "UGA"]
MIN_N = 100  # "sufficient data": at least 100 respondents asked about warnings (in a country or region)
DIMS = {"index": "resilience_index", "individual": "resilience_idv", "household": "resilience_hhl",
        "community": "resilience_com", "societal": "resilience_soc"}

d = load_wave(2025, ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel", "Education",
                     "REGION2_PHL", IMPACTED, TYPE, *CHANNELS.values(), ACT, AGENCY, PLAN, *DIMS.values()])

# --- Derived variables ---------------------------------------------------------

# Resilience scores on 0-100.
for key, var in DIMS.items():
    d[key] = 100 * d[var]

# Disaster type with don't know and refused combined (Chart 1.2 shows them together).
d["type"] = d[TYPE].replace({99: 98})

# Warnings. The eight channel questions were asked of everyone impacted who named
# a disaster type (24,249 respondents; the 995 who answered don't know or refused
# to the type question were not asked). `nwarn` counts the channels answered yes;
# don't know, refused and "does not apply" count as no. warned: 1 = at least one
# warning, 2 = none; missing for those not asked.
asked = d[CHANNELS["internet"]].notna()
d["nwarn"] = np.where(asked, d[list(CHANNELS.values())].eq(1).sum(axis=1), np.nan)
d["nwarn6"] = d["nwarn"].clip(upper=6)  # 6 = six or more
d["warned"] = np.where(asked, np.where(d["nwarn"] > 0, 1, 2), np.nan)

# Household plan and agency (Chart 3.6): among the warned who answered yes or no
# to both questions ("it depends", don't know and refused are left out).
# 1 = plan and agency, 2 = plan only, 3 = agency only, 4 = neither.
yes_no = d[PLAN].isin([1, 2]) & d[AGENCY].isin([1, 2])
d["plan_agency"] = np.where(yes_no, 1 + 2 * d[PLAN].eq(2) + d[AGENCY].eq(2), np.nan)

imp = d[d[IMPACTED] == 1]            # impacted by a disaster (Charts 1.2, 1.6)
ew = d[d["warned"].notna()]          # impacted and asked about warnings (Chapter 2)
w = ew[ew["warned"] == 1]            # warned: asked whether they could act (Chapter 3)
unwarned = ew[ew["warned"] == 2]

# Country table: % impacted, % warned and the number asked about warnings.
country = pd.DataFrame({
    "impacted": pct(d, IMPACTED, [1], by="COUNTRY_ISO3"),
    "coverage": pct(ew, "warned", [1], by="COUNTRY_ISO3"),
    "n": ew.groupby("COUNTRY_ISO3").size(),
})
sufficient = country[country["n"] >= MIN_N]
ew4a = sufficient[sufficient.index.isin(EW4A)]

# 2023 comparison: experienced a disaster (WP23344), its type (WP22247), and at
# least one warning from the four 2023 sources (WP22248-WP22251), defined as in the
# 2023 report: yes to any source; no to at least one and yes to none; respondents
# with no yes or no answer to any source are left out.
d23 = load_wave(2023, ["PROJWT", "WP23344", "WP22247", "WP22248", "WP22249", "WP22250", "WP22251"])
src23 = d23[["WP22248", "WP22249", "WP22250", "WP22251"]]
d23["warned"] = np.select([src23.eq(1).any(axis=1), src23.eq(2).any(axis=1)], [1, 2], default=np.nan)
exp23 = d23[d23["WP23344"] == 1]

# --- Helpers -------------------------------------------------------------------


def by_income(df, var, codes, keys=None):
    r = pct(df, var, codes, by="CountryIncomeLevel")
    out = {INCOME[int(k)]: v for k, v in r.items() if int(k) in INCOME}
    return {k: out[k] for k in keys} if keys else out


def by_region(df, var, codes, keys=None):
    out = {REGIONS[int(k)]: v for k, v in pct(df, var, codes, by="GlobalRegion").items()}
    return {k: out[k] for k in keys} if keys else out


def by_type(df, var, codes, keys):
    r = pct(df, var, codes, by="type")
    return {k: r[TYPE_CODE[k]] for k in keys}


def pick(values, keys):
    return {k: values[k] for k in keys}


def impacted():
    return pct(d, IMPACTED, [1])


def type_share(keys):
    """% of the impacted naming each type as the most impactful."""
    dist = distribution(imp, "type")
    return {k: dist.get(TYPE_CODE[k], 0.0) for k in keys}


def coverage(df=ew):
    return pct(df, "warned", [1])


def able(df=w):
    return pct(df, ACT, [1])


def channel(keys):
    return {k: pct(ew, CHANNELS[k], [1]) for k in keys}


def n_warnings():
    """% by number of warnings (0-5, 6 = six or more) among those asked."""
    return distribution(ew, "nwarn6")


def able_by_n():
    return pct(w, ACT, [1], by="nwarn6")


def gains_after_three():
    """Gains from each channel after three, on rounded percentages as in Chart 3.5."""
    r = able_by_n().round()
    gains = [r[k] - r[k - 1] for k in (4, 5, 6)]
    return {"min": min(gains), "max": max(gains)}


def idv_by_n(keys):
    r = wmean(ew, "individual", by="nwarn6")
    return {str(k): r[k] for k in keys}


def by_action(dim):
    r = wmean(w, dim, by=ACT)
    return {"able": r[1], "not": r[2]}


def action_gap(dim):
    """Gap able minus not able, on rounded scores as in Chart 3.4."""
    r = by_action(dim)
    return round(r["able"]) - round(r["not"])


def plan_agency(keys):
    r = pct(w, ACT, [1], by="plan_agency")
    codes = {"both": 1, "plan": 2, "agency": 3, "neither": 4}
    return {k: r[codes[k]] for k in keys}


def regions_below_half():
    return int((pd.Series(by_region(ew, "warned", [1])) < 50).sum())


def income_ratio():
    r = by_income(d, IMPACTED, [1])
    return r["low"] / r["high"]


def low_income_education():
    r = pct(d[d.CountryIncomeLevel == 1], IMPACTED, [1], by="Education")
    return {"primary": r[1], "secondary": r[2], "tertiary": r[3]}


def countries(var, isos):
    return {iso: country.loc[iso, var] for iso in isos}


def phl(region_key=None):
    p = imp[imp.COUNTRY_ISO3 == "PHL"]
    if region_key is None:
        return distribution(p, "type")
    return distribution(p, "type", by="REGION2_PHL").loc[{v: k for k, v in PHL_REGIONS.items()}[region_key]]


def hazard_pair(hazard):
    return {"warned": by_type(ew, "warned", [1], [hazard])[hazard], "act": by_type(w, ACT, [1], [hazard])[hazard]}


def storms_floods():
    s, f = hazard_pair("hurricane"), hazard_pair("flood")
    return {"storm_warned": s["warned"], "flood_warned": f["warned"], "storm_act": s["act"], "flood_act": f["act"]}


def not_able():
    return pct(w, ACT, [2])


# Mobile phone ownership (Gallup WP17626) among the unwarned.
def unwarned_phone():
    return merge_gallup(unwarned, [PHONE])


def phone_share():
    return pct(unwarned_phone(), PHONE, [1])


def phone_millions():
    g = unwarned_phone()
    return g.loc[g[PHONE] == 1, "PROJWT"].sum() / 1e6


def phone_by_region():
    """Every region's % owning a phone, and whether it has 100+ unwarned respondents (shown in Chart 2.9)."""
    g = unwarned_phone()
    r = pct(g, PHONE, [1], by="GlobalRegion")
    n = unwarned.groupby("GlobalRegion").size()
    return pd.DataFrame({"phone": r, "shown": n.reindex(r.index) >= MIN_N}).rename(index=lambda k: REGIONS[int(k)])


def phone_90_regions():
    return int((phone_by_region()["phone"].round() >= 90).sum())


# --- Foreword ------------------------------------------------------------------------


@report.finding("X001")
def interviews():
    return len(d)


@report.finding("X002")
def n_countries():
    return d.COUNTRY_ISO3.nunique()


report.finding("X003")(coverage)
report.finding("X004")(regions_below_half)
report.finding("X005")(income_ratio)
report.finding("X006")(lambda: by_income(ew, "warned", [1])["low"])


@report.finding("X007")
def low_lower_middle_not_able():
    return pct(w[w.CountryIncomeLevel.isin([1, 2])], ACT, [2])


report.finding("X008")(phone_share)
report.finding("X009")(phone_millions)

# --- Executive summary -----------------------------------------------------------------

report.finding("X010")(interviews)
report.finding("X011")(n_countries)
report.finding("X012")(impacted)
report.finding("X013")(impacted)


@report.finding("X014")
def experienced_2023():
    return pct(d23, "WP23344", [1])


report.finding("X015")(lambda: by_income(d, IMPACTED, [1])["low"])
report.finding("X016")(lambda: by_income(d, IMPACTED, [1])["high"])
report.finding("X017")(income_ratio)
report.finding("X018")(lambda: by_income(d, IMPACTED, [1])["lower_middle"])
report.finding("X019")(lambda: by_income(d, IMPACTED, [1])["upper_middle"])
report.finding("X020")(low_income_education)
report.finding("X021")(lambda: by_region(d, IMPACTED, [1])["anz"])
report.finding("X022")(lambda: by_region(d, IMPACTED, [1], ["eastern_africa", "southeastern_asia"]))
report.finding("X023")(lambda: country.loc["PHL", "impacted"])
report.finding("X024")(lambda: country.loc["ISR", "impacted"])
report.finding("X025")(lambda: type_share(["flood", "hurricane", "earthquake"]))
report.finding("X026")(coverage)
report.finding("X027")(coverage)


@report.finding("X028")
def warned_2023():
    return pct(exp23[exp23["warned"].notna()], "warned", [1])


@report.finding("X029")
def channels_asked():
    return {"2025": len(CHANNELS), "2023": 4}  # WP24181-WP24188; WP22248-WP22251


report.finding("X030")(lambda: by_income(ew, "warned", [1]))
report.finding("X031")(lambda: by_region(ew, "warned", [1])["cw_africa"])


@report.finding("X032")
def ew4a_countries():
    return len(ew4a)


@report.finding("X033")
def ew4a_two_thirds():
    return int((ew4a["coverage"] >= 200 / 3).sum())


report.finding("X034")(lambda: countries("coverage", ["MOZ", "SOM"]))
report.finding("X035")(lambda: by_type(ew, "warned", [1], ["hurricane", "heatwave", "sandstorm", "earthquake",
                                                            "landslide"]))
report.finding("X036")(able)
report.finding("X037")(not_able)
report.finding("X038")(lambda: by_income(w, ACT, [1]))
report.finding("X039")(lambda: hazard_pair("sandstorm")["warned"])
report.finding("X040")(lambda: hazard_pair("sandstorm")["act"])
report.finding("X041")(storms_floods)
report.finding("X042")(lambda: by_action("index"))
report.finding("X043")(lambda: action_gap("index"))
report.finding("X044")(lambda: by_action("individual"))
report.finding("X045")(lambda: action_gap("societal"))
report.finding("X046")(coverage)
report.finding("X047")(lambda: {"1": n_warnings()[1], "6plus": n_warnings()[6]})
report.finding("X048")(lambda: channel(["internet", "tv", "sms"]))
report.finding("X049")(lambda: {str(k): able_by_n()[k] for k in (1, 2, 3)})
report.finding("X050")(gains_after_three)
report.finding("X051")(lambda: idv_by_n([1, 0, 2, 3]))
report.finding("X052")(lambda: plan_agency(["neither", "plan", "agency", "both"]))

# Policy implications
report.finding("X053")(lambda: country.loc["TCD", "coverage"])
report.finding("X054")(lambda: country.loc["TCD", "impacted"])
report.finding("X055")(phone_share)
report.finding("X056")(phone_millions)
report.finding("X057")(phone_90_regions)
report.finding("X058")(lambda: plan_agency(["neither", "both"]))

# --- Chapter 1: which disasters impact people the most? ------------------------------

report.finding("X059")(impacted)
report.finding("X060")(lambda: type_share(["flood"])["flood"])
report.finding("X061")(impacted)
report.finding("X062")(experienced_2023)
report.finding("X063")(impacted)


@report.finding("C1_1")
def chart_1_1():
    return {"yes": pct(d, IMPACTED, [1]), "no": pct(d, IMPACTED, [2])}


report.finding("X064")(lambda: type_share(["flood", "hurricane", "earthquake"]))
report.finding("X065")(lambda: type_share(["flood", "hurricane", "earthquake"]))


@report.finding("X066")
def types_2023():
    dist = distribution(exp23, "WP22247")
    return {"flood": dist[1], "hurricane": dist[2], "earthquake": dist[7]}


report.finding("X067")(lambda: type_share(["drought", "wildfire", "heatwave"]))
report.finding("X068")(lambda: type_share(["tornado", "blizzard", "landslide", "thunder", "volcano"]))
report.finding("X069")(lambda: type_share(["sandstorm", "tsunami"]))


@report.finding("C1_2")
def chart_1_2():
    return type_share(list(TYPES.values()))


report.finding("X070")(lambda: by_income(d, IMPACTED, [1], ["low", "high"]))
report.finding("X071")(income_ratio)


@report.finding("C1_3")
def chart_1_3():
    return by_income(d, IMPACTED, [1])


report.finding("X072")(lambda: by_income(d, IMPACTED, [1])["low"])
report.finding("X073")(lambda: by_income(d, IMPACTED, [1])["high"])
report.finding("X074")(lambda: 1 / income_ratio())
report.finding("X075")(lambda: by_income(d, IMPACTED, [1], ["lower_middle", "upper_middle"]))
report.finding("X076")(low_income_education)
report.finding("X077")(lambda: by_region(d, IMPACTED, [1], ["anz", "eastern_africa", "southeastern_asia",
                                                             "northern_africa", "central_asia"]))


@report.finding("C1_4")
def chart_1_4():
    return by_region(d, IMPACTED, [1])


report.finding("X078")(lambda: by_region(d, IMPACTED, [1])["anz"])
report.finding("X079")(lambda: by_region(d, IMPACTED, [1], ["eastern_africa", "southeastern_asia"]))
report.finding("X080")(lambda: by_region(d, IMPACTED, [1])["eastern_asia"])
report.finding("X081")(lambda: by_region(d, IMPACTED, [1])["southern_europe"])
report.finding("X082")(lambda: by_region(d, IMPACTED, [1], ["eastern_europe", "nw_europe"]))
report.finding("X083")(lambda: by_region(d, IMPACTED, [1], ["northern_africa", "central_asia"]))
report.finding("X084")(lambda: countries("impacted", ["PHL", "ISR"]))


@report.finding("C1_5")
def chart_1_5():
    # Every country's % impacted; the map labels 13 of them.
    return country["impacted"]


# The Philippines (page 7, Chart 1.6): shares of the impacted.


@report.finding("X085")
def phl_types():
    dist = phl()
    return {"hurricane": dist[2], "flood": dist[1], "earthquake": dist[7]}


report.finding("X086")(lambda: {k: phl(k)[2] for k in ("visayas", "balance_luzon", "ncr")})
report.finding("X087")(lambda: phl("ncr")[1])
report.finding("X088")(lambda: {k: phl("ncr")[1] / phl(k)[1] for k in ("balance_luzon", "mindanao")})
report.finding("X089")(lambda: phl("mindanao")[7])
report.finding("X090")(lambda: {"visayas_hurricane": phl("visayas")[2], "balance_luzon_hurricane": phl("balance_luzon")[2],
                                "ncr_flood": phl("ncr")[1], "mindanao_earthquake": phl("mindanao")[7]})


@report.finding("C1_6")
def chart_1_6():
    return {f"{r}_{h}": phl(r)[code] for r in PHL_REGIONS.values()
            for h, code in (("hurricane", 2), ("flood", 1), ("earthquake", 7))}


# --- Chapter 2: how prevalent are early warnings before disasters? --------------------

report.finding("X091")(coverage)
report.finding("X092")(coverage)
report.finding("X093")(warned_2023)
report.finding("X094")(channels_asked)
report.finding("X095")(lambda: by_income(ew, "warned", [1]))
report.finding("X096")(lambda: {"warned": coverage(), "none": pct(ew, "warned", [2])})


@report.finding("C2_1")
def chart_2_1():
    return {"warned": coverage(), "none": pct(ew, "warned", [2])}


report.finding("X097")(lambda: by_income(ew, "warned", [1], ["low", "upper_middle", "high"]))


@report.finding("C2_2")
def chart_2_2():
    return by_income(ew, "warned", [1])


report.finding("X098")(lambda: by_region(ew, "warned", [1], ["eastern_asia", "anz", "northern_america", "nw_europe"]))
report.finding("X099")(lambda: by_region(ew, "warned", [1])["cw_africa"])
report.finding("X100")(lambda: by_region(ew, "warned", [1], ["eastern_asia", "cw_africa"]))


@report.finding("C2_3")
def chart_2_3():
    return by_region(ew, "warned", [1])


# Countries (page 11): only countries with at least 100 respondents asked about warnings.
report.finding("X101")(lambda: countries("coverage", ["VNM", "HKG", "CHN"]))


@report.finding("X102")
def highest_coverage():
    return ", ".join(sorted(sufficient["coverage"].nlargest(3).index))


report.finding("X103")(lambda: countries("coverage", ["COG", "GAB"]))


@report.finding("X104")
def lowest_coverage():
    return ", ".join(sorted(sufficient["coverage"].nsmallest(2).index))


report.finding("X105")(ew4a_countries)
report.finding("X106")(lambda: int((ew4a["coverage"] < 200 / 3).sum()))
report.finding("X107")(lambda: countries("coverage", ["MOZ", "SOM", "MUS", "LAO", "KHM"]))
report.finding("X108")(lambda: int((ew4a["coverage"] < 50).sum()))
report.finding("X109")(lambda: countries("coverage", ["TCD", "NPL"]))
report.finding("X110")(lambda: country.loc["TCD", "impacted"])
report.finding("X111")(lambda: country.loc["NPL", "impacted"])
report.finding("X112")(lambda: country.loc["TCD", "coverage"])
report.finding("X113")(lambda: country.loc["TCD", "impacted"])


@report.finding("C2_4")
def chart_2_4():
    # Scatter of the 13 priority countries: no values are printed.
    return {f"{iso}_{v}": ew4a.loc[iso, v] for iso in ew4a.index for v in ("coverage", "impacted")}


report.finding("X114")(lambda: by_type(ew, "warned", [1], ["hurricane", "heatwave", "sandstorm"]))
report.finding("X115")(lambda: by_type(ew, "warned", [1], ["earthquake", "landslide"]))
report.finding("X116")(lambda: by_type(ew, "warned", [1], ["hurricane", "earthquake", "landslide"]))


@report.finding("C2_5")
def chart_2_5():
    return by_type(ew, "warned", [1], CHART_2_5)


report.finding("X117")(lambda: {"channels": len(CHANNELS), "ratio": len(CHANNELS) / 4})
report.finding("X118")(lambda: channel(["internet", "tv", "sms"]))
report.finding("X119")(lambda: channel(["radio"])["radio"])
report.finding("X120")(lambda: channel(["newspapers", "loudspeaker"]))
report.finding("X121")(lambda: channel(["billboard"])["billboard"])
report.finding("X122")(lambda: channel(["internet", "tv", "sms", "billboard"]))


@report.finding("C2_6")
def chart_2_6():
    return channel(list(CHANNELS))


report.finding("X123")(coverage)
report.finding("X124")(lambda: n_warnings()[1])
report.finding("X125")(lambda: n_warnings()[6])
report.finding("X126")(lambda: {"1": n_warnings()[1], "6plus": n_warnings()[6]})


@report.finding("C2_7")
def chart_2_7():
    r = n_warnings()
    out = {("6plus" if k == 6 else str(int(k))): v for k, v in r.items()}
    out["any"] = coverage()
    return out


report.finding("X127")(lambda: idv_by_n([1, 0]))
report.finding("X128")(lambda: idv_by_n([2])["2"])
report.finding("X129")(lambda: idv_by_n([3])["3"])
report.finding("X130")(lambda: idv_by_n([1, 2, 3]))


@report.finding("C2_8")
def chart_2_8():
    r = idv_by_n(range(7))
    return {("6plus" if k == "6" else k): v for k, v in r.items()}


# Mobile phones and the unwarned (page 16): needs Gallup's WP17626.
report.finding("X131")(lambda: pct(ew, "warned", [2]))
report.finding("X132")(phone_share)
report.finding("X133")(phone_millions)
report.finding("X134")(lambda: phone_by_region()["phone"][["northern_america", "anz"]])


@report.finding("X135")
def phone_above_90_shown():
    r = phone_by_region()
    return int((r.loc[r["shown"], "phone"].round() > 90).sum())


report.finding("X136")(lambda: phone_by_region()["phone"][["southern_asia", "eastern_africa"]])
report.finding("X137")(lambda: {"global": phone_share(), **phone_by_region()["phone"][["northern_america", "anz"]]})


@report.finding("C2_9")
def chart_2_9():
    # Regions with fewer than 100 unwarned respondents are not shown (Northern America,
    # Eastern Asia, Australia and New Zealand); they are still written to output/.
    return {"global": phone_share(), **phone_by_region()["phone"]}


report.finding("X138")(phone_share)

# --- Chapter 3: how effective are early warnings before a disaster? --------------------

report.finding("X139")(lambda: plan_agency(["both", "agency", "plan", "neither"]))
report.finding("X140")(coverage)
report.finding("X141")(able)
report.finding("X142")(not_able)
report.finding("X143")(lambda: {"able": able(), "not": not_able()})


@report.finding("C3_1")
def chart_3_1():
    return {"able": able(), "not": not_able()}


report.finding("X144")(lambda: by_income(w, ACT, [1], ["low", "lower_middle"]))
report.finding("X145")(lambda: by_income(w, ACT, [1], ["upper_middle", "high"]))
report.finding("X146")(lambda: by_region(w, ACT, [1])["northern_america"])
report.finding("X147")(lambda: by_region(w, ACT, [1], ["eastern_asia", "southeastern_asia", "anz", "nw_europe"]))
report.finding("X148")(lambda: by_region(w, ACT, [1], ["northern_africa", "eastern_africa", "cw_africa",
                                                        "southern_africa"]))
report.finding("X149")(lambda: by_region(w, ACT, [1], ["southern_europe", "latam", "eastern_europe"]))
report.finding("X150")(lambda: by_region(w, ACT, [1], ["central_asia", "southern_asia"]))
report.finding("X151")(lambda: by_region(w, ACT, [1], ["northern_america", "northern_africa", "eastern_africa",
                                                        "southern_africa"]))


@report.finding("C3_2")
def chart_3_2():
    return by_region(w, ACT, [1])


report.finding("X152")(lambda: hazard_pair("sandstorm")["warned"])
report.finding("X153")(lambda: hazard_pair("sandstorm")["act"])
report.finding("X154")(storms_floods)
report.finding("X155")(lambda: hazard_pair("earthquake")["act"])
report.finding("X156")(lambda: hazard_pair("earthquake")["warned"])
report.finding("X157")(lambda: hazard_pair("drought")["warned"])
report.finding("X158")(lambda: hazard_pair("drought")["act"])
report.finding("X159")(lambda: {"sandstorm_warned": hazard_pair("sandstorm")["warned"],
                                "sandstorm_act": hazard_pair("sandstorm")["act"],
                                "earthquake_warned": hazard_pair("earthquake")["warned"],
                                "earthquake_act": hazard_pair("earthquake")["act"]})


@report.finding("C3_3")
def chart_3_3():
    # Bubble chart: no values are printed.
    return {f"{h}_{k}": v for h in CHART_3_3 for k, v in hazard_pair(h).items()}


report.finding("X160")(lambda: by_action("index")["able"])
report.finding("X161")(lambda: action_gap("index"))
report.finding("X162")(lambda: by_action("index")["not"])
report.finding("X163")(lambda: action_gap("individual"))
report.finding("X164")(lambda: by_action("individual"))
report.finding("X165")(lambda: action_gap("household"))
report.finding("X166")(lambda: action_gap("community"))
report.finding("X167")(lambda: action_gap("societal"))
report.finding("X168")(lambda: {"index_able": by_action("index")["able"], "index_not": by_action("index")["not"],
                                "individual_able": by_action("individual")["able"],
                                "individual_not": by_action("individual")["not"]})


@report.finding("C3_4")
def chart_3_4():
    out = {}
    for dim in DIMS:
        r = by_action(dim)
        out.update({f"{dim}_not": r["not"], f"{dim}_able": r["able"], f"{dim}_gap": action_gap(dim)})
    return out


report.finding("X169")(lambda: able_by_n()[1])
report.finding("X170")(lambda: able_by_n().round()[2] - able_by_n().round()[1])
report.finding("X171")(lambda: able_by_n()[2])
report.finding("X172")(lambda: able_by_n().round()[3] - able_by_n().round()[2])
report.finding("X173")(lambda: able_by_n()[3])
report.finding("X174")(gains_after_three)
report.finding("X175")(lambda: {str(k): able_by_n()[k] for k in (1, 2, 3)})
report.finding("X176")(gains_after_three)


@report.finding("C3_5")
def chart_3_5():
    # Values by number of warnings; the gains are differences of the rounded values.
    r = able_by_n()
    key = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6plus"}
    out = {key[int(k)]: v for k, v in r.items()}
    out.update({f"gain_{key[k]}": round(r[k]) - round(r[k - 1]) for k in range(2, 7)})
    return out


def mean_warnings_by(item, keys):
    g = merge_gallup(ew, [item])
    r = wmean(g, "nwarn", by=item)
    return {keys[0]: r[1], keys[1]: r[2]}


report.finding("X177")(lambda: mean_warnings_by(PHONE, ["phone", "no_phone"]))
report.finding("X178")(lambda: mean_warnings_by(INTERNET, ["internet", "no_internet"]))
report.finding("X179")(lambda: plan_agency(["neither"])["neither"])
report.finding("X180")(lambda: plan_agency(["plan"])["plan"])
report.finding("X181")(lambda: plan_agency(["agency"])["agency"])
report.finding("X182")(lambda: plan_agency(["both"])["both"])
report.finding("X183")(lambda: plan_agency(["both", "neither"]))


@report.finding("C3_6")
def chart_3_6():
    return plan_agency(["both", "plan", "agency", "neither"])


# --- Turning the World Risk Poll into action, and conclusion ---------------------------

report.finding("X184")(lambda: int((ew4a["coverage"] < 50).sum()))
report.finding("X185")(lambda: country.loc["NPL", "coverage"])
report.finding("X186")(lambda: by_type(ew, "warned", [1], ["landslide"])["landslide"])
report.finding("X187")(lambda: phone_by_region()["phone"]["eastern_africa"])
report.finding("X188")(lambda: plan_agency(["both", "neither"]))
report.finding("X189")(coverage)
report.finding("X190")(regions_below_half)
report.finding("X191")(lambda: by_income(d, IMPACTED, [1], ["low", "high"]))
report.finding("X192")(income_ratio)
report.finding("X193")(lambda: low_income_education()["primary"])
report.finding("X194")(lambda: by_income(ew, "warned", [1], ["low", "upper_middle", "high"]))
report.finding("X195")(lambda: by_income(w, ACT, [1])["low"])


@report.finding("X196")
def low_income_individual_resilience():
    # Individual resilience in low-income countries, impacted (WP24213 = 1) vs not (= 2).
    r = wmean(d[d.CountryIncomeLevel == 1], "individual", by=IMPACTED)
    return {"impacted": r[1], "not_impacted": r[2]}


report.finding("X197")(not_able)
report.finding("X198")(lambda: plan_agency(["both", "neither"]))
report.finding("X199")(lambda: idv_by_n([1, 0]))
report.finding("X200")(lambda: able_by_n()[1])
report.finding("X201")(lambda: {str(k): able_by_n()[k] for k in (2, 3)})
report.finding("X202")(gains_after_three)
report.finding("X203")(phone_share)
report.finding("X204")(phone_millions)
report.finding("X205")(phone_90_regions)
report.finding("X206")(lambda: country.loc["TCD", "coverage"])
report.finding("X207")(lambda: country.loc["TCD", "impacted"])


if __name__ == "__main__":
    sys.exit(report.run())
