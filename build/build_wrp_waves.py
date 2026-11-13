#!/usr/bin/env python3
"""
Build one harmonised World Risk Poll data file per wave.

For each wave (2019, 2021, 2023, 2025) this produces a single dataset that
carries an identical leading block of harmonised design, demographic and index
variables, followed by that wave's own questionnaire variables unchanged.

Outputs per wave, in ./output/WRP_<year>/ and zipped to ./output/WRP_<year>.zip:
    WRP_<year>.sav
    WRP_<year>.parquet
    WRP_<year>.csv
    WRP_<year>_data_dictionary.csv

Run from the directory holding the supplied .sav files.
"""
from __future__ import annotations

import datetime as _dt
import os
import shutil
import zipfile

import numpy as np
import pandas as pd
import pyreadstat

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SRC, "output")

F_W1 = "19_wrp.sav"
F_W2 = "21_wrp.sav"
F_W3 = "LRF_WAVE_3_WITH_INDICES_FOR_PUBLIC_RELEASE_10082024_v2.sav"
F_W4 = "LRF_WAVE4_WITH_INDICES_FOR_PUBLIC_RELEASE.sav"
F_TREND2 = "trend_wrp_21_OLD.sav"   # 2019 + 2021 trend file: published wave 1/2 indices
F_TREND3 = "trended_wrp.sav"        # 2019 + 2021 + 2023 trend file: harmonised resilience

# --------------------------------------------------------------------------- #
# harmonised value labels
# --------------------------------------------------------------------------- #
VL_WAVE = {1.0: "2019 (Wave 1)", 2.0: "2021 (Wave 2)",
           3.0: "2023 (Wave 3)", 4.0: "2025 (Wave 4)"}
VL_REGION = {
    1.0: "Eastern Africa", 2.0: "Central/Western Africa", 3.0: "Northern Africa",
    4.0: "Southern Africa", 5.0: "Latin America & the Caribbean", 6.0: "Northern America",
    7.0: "Central Asia", 8.0: "Eastern Asia", 9.0: "Southeastern Asia",
    10.0: "Southern Asia", 11.0: "Middle East", 12.0: "Eastern Europe",
    13.0: "Northern/Western Europe", 14.0: "Southern Europe",
    15.0: "Australia & New Zealand",
}
VL_INCOME_LEVEL = {
    1.0: "Low income", 2.0: "Lower-middle income", 3.0: "Upper-middle income",
    4.0: "High income", 9.0: "Not classified",
}
VL_AGE3 = {1.0: "15-29", 2.0: "30-49", 3.0: "50 and over"}
VL_AGE4 = {1.0: "15-29", 2.0: "30-49", 3.0: "50-64", 4.0: "65 and over"}
VL_AGE5 = {1.0: "15-24", 2.0: "25-34", 3.0: "35-49", 4.0: "50-64", 5.0: "65 and over"}
VL_GENDER = {1.0: "Male", 2.0: "Female"}
VL_EDU = {1.0: "Primary or less (up to 8 years)", 2.0: "Secondary (9-15 years)",
          3.0: "Tertiary (16 years or more)", 9.0: "DK/Refused"}
VL_URB6 = {1.0: "A rural area or on a farm", 2.0: "A small town or village",
           3.0: "A large city", 6.0: "A suburb of a large city", 9.0: "DK/Refused"}
VL_URB2 = {1.0: "Rural area or small town", 2.0: "Large city or suburb", 9.0: "DK/Refused"}
VL_EMP = {
    1.0: "Employed full time for an employer", 2.0: "Employed full time for self",
    3.0: "Employed part time, does not want full time", 4.0: "Unemployed",
    5.0: "Employed part time, wants full time", 6.0: "Out of workforce",
}
VL_INCOME5 = {1.0: "Poorest 20%", 2.0: "Second 20%", 3.0: "Middle 20%",
              4.0: "Fourth 20%", 5.0: "Richest 20%"}
VL_HHSIZE = {1.0: "1-2 people", 2.0: "3-4 people", 3.0: "5-9 people",
             4.0: "10 or more", 9.0: "DK/Refused"}
VL_KIDS = {0.0: "None", 1.0: "One", 2.0: "Two", 3.0: "Three", 4.0: "Four",
           5.0: "Five or more", 9.0: "DK/Refused"}

# --------------------------------------------------------------------------- #
# harmonised item sets
# --------------------------------------------------------------------------- #
# five risk sources asked in identical form in every wave
W1_CORE5_W = ["L6A", "L6B", "L6C", "L6D", "L6G"]
W1_CORE5_E = ["L8A", "L8B", "L8C", "L8D", "L8G"]
CORE5_W = ["WP20720", "WP20721", "WP20722", "WP20723", "WP20726"]
CORE5_E = ["WP22442", "WP22443", "WP22444", "WP22445", "WP22447"]
# two further sources added from 2021: traffic accidents and work
CORE7_W_REQ = CORE5_W + ["WP22213"]   # asked of everyone
CORE7_W_OPT = ["WP22214"]             # worry about own work: workers only
CORE7_E = CORE5_E + ["WP22446", "WP22448"]


def worry_mean(df, required, optional=()):
    """Mean of worry items on 0-1 (very worried 1, somewhat 0.5, not worried 0).

    Every `required` item must be answered. `optional` items, which are put only
    to a subset of respondents (worry about your own work), count when present.
    """
    def rc(col):
        s = df[col]
        return s.where(s.isin([1, 2, 3])).map({1: 1.0, 2: 0.5, 3: 0.0})

    req = pd.concat([rc(c) for c in required], axis=1)
    allit = req if not optional else pd.concat(
        [req] + [rc(c) for c in optional], axis=1)
    score = allit.mean(axis=1)
    score[req.notna().sum(axis=1) < len(required)] = np.nan
    return score


def exp_mean(df, items, mode, wave1=False):
    """Proportion of experience items answered yes, on 0-1.

    mode 'any'  -> personally experienced, knows someone who has, or both
    mode 'self' -> personally experienced, or both
    Wave 1 offered a plain yes/no about the respondent only.
    """
    if wave1:
        mp = {1: 1.0, 2: 0.0}
    elif mode == "any":
        mp = {1: 1.0, 2: 1.0, 3: 1.0, 4: 0.0}
    else:
        mp = {1: 1.0, 2: 0.0, 3: 1.0, 4: 0.0}
    x = pd.concat([df[c].map(mp) for c in items], axis=1)
    score = x.mean(axis=1)
    score[x.notna().sum(axis=1) < len(items)] = np.nan
    return score


def age_bands(a):
    g3 = pd.Series(np.nan, index=a.index)
    g3[a.between(15, 29)] = 1.0
    g3[a.between(30, 49)] = 2.0
    g3[a >= 50] = 3.0
    g4 = pd.Series(np.nan, index=a.index)
    g4[a.between(15, 29)] = 1.0
    g4[a.between(30, 49)] = 2.0
    g4[a.between(50, 64)] = 3.0
    g4[a >= 65] = 4.0
    g5 = pd.Series(np.nan, index=a.index)
    g5[a.between(15, 24)] = 1.0
    g5[a.between(25, 34)] = 2.0
    g5[a.between(35, 49)] = 3.0
    g5[a.between(50, 64)] = 4.0
    g5[a >= 65] = 5.0
    return g3, g4, g5


def recode(s, mapping):
    """Replace only the listed source values; leave everything else untouched."""
    out = s.copy()
    for k, v in mapping.items():
        out = out.mask(s == k, v)
    return out


def urb6_to_urb2(u6):
    return recode(u6, {1: 1, 2: 1, 3: 2, 6: 2, 9: 9})


# --------------------------------------------------------------------------- #
# country / ISO lookup
# --------------------------------------------------------------------------- #
def country_lookup():
    a, _ = pyreadstat.read_sav(
        os.path.join(SRC, F_TREND3),
        usecols=["WP5", "Country", "COUNTRY_ISO2", "COUNTRY_ISO3"])
    b, _ = pyreadstat.read_sav(
        os.path.join(SRC, F_W4),
        usecols=["WP5", "Country", "COUNTRY_ISO2", "COUNTRY_ISO3"])
    lk = pd.concat([a, b]).drop_duplicates(subset=["WP5"]).set_index("WP5")
    # three countries appear only in 2019 and so carry no ISO code in any file
    for wp5, iso2, iso3 in [(71.0, "BY", "BLR"), (65.0, "RW", "RWA"),
                            (191.0, "TM", "TKM")]:
        lk.loc[wp5, "COUNTRY_ISO2"] = iso2
        lk.loc[wp5, "COUNTRY_ISO3"] = iso3
    return lk[["COUNTRY_ISO2", "COUNTRY_ISO3"]]


# --------------------------------------------------------------------------- #
# the harmonised block, identical in every wave file
# --------------------------------------------------------------------------- #
HARM_ORDER = [
    "WPID_RANDOM", "Wave", "Year", "WP5", "Country", "COUNTRY_ISO2", "COUNTRY_ISO3",
    "GlobalRegion", "CountryIncomeLevel", "WGT", "PROJWT",
    "Age", "AgeGroups3", "AgeGroups4", "AgeGroups5", "Gender", "Education",
    "Urbanicity", "Urbanicity2", "EMP_2010", "INCOME_5", "HouseholdSize",
    "ChildrenInHousehold",
    "worry_score", "worry_score_core7", "worry_index_published",
    "experience_score", "experience_score_self", "experience_score_core7",
    "experience_index_published", "worry_exp_gap",
    "resilience_index", "resilience_index_100",
    "resilience_idv", "resilience_hhl", "resilience_com", "resilience_soc",
]

HARM_VALUE_LABELS = {
    "Wave": VL_WAVE, "GlobalRegion": VL_REGION, "CountryIncomeLevel": VL_INCOME_LEVEL,
    "AgeGroups3": VL_AGE3, "AgeGroups4": VL_AGE4, "AgeGroups5": VL_AGE5,
    "Gender": VL_GENDER, "Education": VL_EDU, "Urbanicity": VL_URB6,
    "Urbanicity2": VL_URB2, "EMP_2010": VL_EMP, "INCOME_5": VL_INCOME5,
    "HouseholdSize": VL_HHSIZE, "ChildrenInHousehold": VL_KIDS,
}

WB_DEF = {2019: "World Bank FY2019-20", 2021: "World Bank FY2021-22",
          2023: "World Bank FY2023-24", 2025: "World Bank FY2024-25"}

HH_DEF = {2019: "Total people in household", 2021: "Total people in household",
          2023: "Residents aged 15+ in household",
          2025: "Household size as supplied in the wave 4 release"}


def harm_labels(year):
    return {
        "WPID_RANDOM": "Random unique case ID",
        "Wave": "World Risk Poll wave",
        "Year": "Year of fieldwork",
        "WP5": "Gallup country code",
        "Country": "Country/area name",
        "COUNTRY_ISO2": "Country ISO alpha-2 code",
        "COUNTRY_ISO3": "Country ISO alpha-3 code",
        "GlobalRegion": "Global region (World Risk Poll report definition)",
        "CountryIncomeLevel":
            "Country income group at time of fieldwork (%s)" % WB_DEF[year],
        "WGT": "Within-country survey weight",
        "PROJWT": "Population projection weight (single-year or time-series analysis)",
        "Age": "Age in years",
        "AgeGroups3": "Age - 3 bands",
        "AgeGroups4": "Age - 4 bands",
        "AgeGroups5": "Age - 5 bands",
        "Gender": "Gender",
        "Education": "Education level",
        "Urbanicity": "Urban/rural - 6 categories",
        "Urbanicity2": "Urban/rural - 2 categories",
        "EMP_2010": "Employment status",
        "INCOME_5": "Per capita income quintile",
        "HouseholdSize": "Household size (%s)" % HH_DEF[year],
        "ChildrenInHousehold": "Children under 15 in household",
        "worry_score": "Worry score, 5 common items, 0-1 (comparable across all waves)",
        "worry_score_core7": "Worry score, 7 items, 0-1 (comparable 2021-2025)",
        "worry_index_published": "Worry index as published by LRF for this wave",
        "experience_score":
            "Experience score, 5 common items, any experience, 0-1 (comparable across waves)",
        "experience_score_self":
            "Experience score, 5 common items, personally experienced, 0-1",
        "experience_score_core7":
            "Experience score, 7 items, any experience, 0-1 (comparable 2021-2025)",
        "experience_index_published": "Experience index as published by LRF for this wave",
        "worry_exp_gap": "worry_score minus experience_score",
        "resilience_index": "Resilience Index, 0-1",
        "resilience_index_100": "Resilience Index, 0-100",
        "resilience_idv": "Resilience: individual dimension, 0-1",
        "resilience_hhl": "Resilience: household dimension, 0-1",
        "resilience_com": "Resilience: community dimension, 0-1",
        "resilience_soc": "Resilience: society dimension, 0-1",
    }


# derivation notes, written into the data dictionary
def harm_notes(year):
    y = year
    n = {
        "WPID_RANDOM": "As supplied.",
        "Wave": "Constant.",
        "Year": "Constant.",
        "WP5": {2019: "From trend_wrp_21_OLD.sav; not held in 19_wrp.sav."}.get(y, "As supplied."),
        "Country": "As supplied.",
        "COUNTRY_ISO2": "Mapped from WP5. Belarus, Rwanda and Turkmenistan added by hand: they appear only in 2019.",
        "COUNTRY_ISO3": "Mapped from WP5. Belarus, Rwanda and Turkmenistan added by hand: they appear only in 2019.",
        "GlobalRegion": {2019: "From RegionReport; codes 1-15 are identical in every wave, only the label wording differed."}.get(
            y, "As supplied; label wording standardised to the 2025 release."),
        "CountryIncomeLevel": {
            2019: "From WBI (World Bank FY2019-20 classification).",
            2021: "From CountryIncomeLevel2021.",
            2023: "From CountryIncomeLevel2023.",
            2025: "From CountryIncomeLevel2025.",
        }[y] + " Classification contemporaneous with fieldwork.",
        "WGT": "As supplied.",
        "PROJWT": {
            2019: "From PROJWT_2019 in trend_wrp_21_OLD.sav; not held in 19_wrp.sav. Identical to PROJWT for 2019 in trended_wrp.sav.",
            2021: "From PROJWT_2021 as supplied in 21_wrp.sav.",
        }.get(y, "As supplied."),
        "Age": ({2019: "From trend_wrp_21_OLD.sav; not held in 19_wrp.sav. "}.get(y, "") +
                "Age 100 in the source files is Gallup's don't know/refused code and is set to missing here, matching LRF's own age-band treatment."),
        "AgeGroups3": "Derived from Age. Identical banding in all four waves.",
        "AgeGroups4": "Derived from Age. Identical banding in all four waves.",
        "AgeGroups5": "Derived from Age. Identical banding in all four waves.",
        "Gender": {2019: "From WP1219."}.get(y, "As supplied."),
        "Education": ("Codes 1-3 as supplied; don't know and refused collapsed to 9."
                      if y != 2021 else "As supplied (already 1-3 plus 9)."),
        "Urbanicity": {
            2019: "From WP14 (6-category). Don't know and refused collapsed to 9.",
            2021: "From trended_wrp.sav, which holds the 6-category version for 2021. Missing for the 505 Jamaica cases absent from that file; Urbanicity2 covers them.",
        }.get(y, "As supplied (6-category). Don't know and refused collapsed to 9."),
        "Urbanicity2": {
            2021: "Native 2-group variable from 21_wrp.sav; full coverage.",
        }.get(y, "Collapsed from Urbanicity: rural area and small town to 1, large city and suburb to 2."),
        "EMP_2010": "As supplied.",
        "INCOME_5": "As supplied.",
        "HouseholdSize": ("Codes 1-4 as supplied; don't know and refused collapsed to 9. "
                          "Note the definition is not identical across waves: see the wave notes."),
        "ChildrenInHousehold": {
            2019: "As supplied (already 0-5 plus 9; the value label in 19_wrp.sav was wrong).",
            2021: "Recoded from 1-6 plus 7 to 0-5 plus 9 to match the later waves.",
            2023: "As supplied.",
            2025: "Recoded: 99 (don't know/refused) to 9.",
        }[y],
        "worry_score": (
            "Mean of the five worry items asked in identical form in every wave (food, drinking water, "
            "violent crime, severe weather, mental health), scored very worried 1, somewhat worried 0.5, "
            "not worried 0. All five must be answered."),
        "worry_score_core7": (
            "Not available: worry about traffic accidents and about your own work were not asked in 2019."
            if y == 2019 else
            "As worry_score plus worry about traffic accidents and about your own work. The six items put "
            "to everyone must be answered; the work item, asked of workers only, counts where present."),
        "worry_index_published": {
            2019: "Worried.Index as published for wave 1: Rasch-weighted, min-max scaled, over the seven 2019 worry items (which include electrical power lines and household appliances, dropped after 2019).",
            2021: "Worried.Index as published for wave 2 (from trend_wrp_21_OLD.sav): Rasch-weighted, min-max scaled, over the seven 2021 worry items.",
            2023: "Q4_RMw_maxmin as published for wave 3: Rasch-weighted, min-max scaled, over the seven 2023 worry items.",
            2025: "worry_index as published for wave 4: simple mean of the ten 2025 worry items (the seven earlier ones plus air quality, prolonged severe weather and wildfires).",
        }[y] + " Not comparable across waves: both the item set and the construction change. Use worry_score for trends.",
        "experience_score": (
            "Proportion of the five common items on which the respondent reports harm in the past two years. "
            + ("2019 asked only whether the respondent had personally experienced harm, so this equals experience_score_self."
               if y == 2019 else
               "Counts personally experienced, knows someone who has, and both. This matches LRF's own harm_*_trended recode and is the series that lines up with 2019.")
            + " All five items must be answered."),
        "experience_score_self": (
            "Identical to experience_score in 2019: the question asked about the respondent only."
            if y == 2019 else
            "Counts personally experienced and both, excluding knows someone who has. Comparable 2021-2025 and "
            "consistent with the published wave 3 experience index. Against 2019 it drops sharply, because the "
            "added knows-someone option pulls self-reports out of the personal category."),
        "experience_score_core7": (
            "Not available: harm from traffic accidents and from work were not asked in 2019."
            if y == 2019 else
            "As experience_score plus harm from traffic accidents and from work. All seven items must be answered."),
        "experience_index_published": {
            2019: "Experienced.Index as published for wave 1: Rasch-weighted, min-max scaled, over the seven 2019 experience items.",
            2021: "Experienced.Index as published for wave 2 (from trend_wrp_21_OLD.sav).",
            2023: "Q5_RMw_maxmin as published for wave 3: Rasch-weighted, min-max scaled, personally-experienced definition.",
            2025: "Empty: LRF published no experience index for wave 4. Use experience_score or experience_score_core7.",
        }[y],
        "worry_exp_gap": "worry_score minus experience_score, both on the five common items.",
        "resilience_index": {
            2019: "Empty: the resilience questions began in 2021.",
            2021: "resilience_index from trended_wrp.sav, which recomputes the wave 2 index consistently with wave 3. Where that file has no row (505 Jamaica cases) the wave 2 release value is used. The two agree exactly for 98.7% of cases; they differ only in Vietnam and Myanmar, where the question wording differs.",
            2023: "As supplied (0-1).",
            2025: "As supplied, divided by 100: the wave 4 release carries it on a 0-100 scale.",
        }[y],
        "resilience_index_100": ("Empty: the resilience questions began in 2021."
                                 if y == 2019 else "resilience_index multiplied by 100."),
    }
    for dim, nm in [("idv", "individual"), ("hhl", "household"),
                    ("com", "community"), ("soc", "society")]:
        n["resilience_" + dim] = {
            2019: "Empty: the resilience questions began in 2021.",
            2021: "resilience_%s_0_100_scale from trended_wrp.sav, divided by 100. Missing for the 505 Jamaica cases absent from that file." % dim,
            2023: "As supplied (0-1).",
            2025: "As supplied, divided by 100.",
        }[y]
    return n


UNLABELLED_FIXES = {
    "Q4_RMw_projwt_byusertime":
        "Projection weight, cases with a valid worry index only (unlabelled in source)",
    "Q5_RMw_projwt_byusertime":
        "Projection weight, cases with a valid experience index only (unlabelled in source)",
    "Q4_mean_projwt_byusertime":
        "Projection weight, cases with a valid worry mean only (unlabelled in source)",
    "Q5_mean_projwt_byusertime":
        "Projection weight, cases with a valid experience mean only (unlabelled in source)",
}

WAVE_NOTES = {
    2019: [
        "Source: 19_wrp.sav (154,195 cases), with Age, WP5 and PROJWT_2019 merged in on WPID_RANDOM.",
        "Resilience was not measured in 2019.",
        "Worry about traffic accidents and about work, and harm from those two sources, were not asked in 2019; worry about electrical power lines and household appliances were asked in 2019 only.",
        "The 2019 experience question asked only whether the respondent had personally been harmed. From 2021 it also offers 'someone you know'.",
        "HouseholdSize is the total number of people in the household.",
    ],
    2021: [
        "Source: the 2021 rows of 21_wrp.sav (125,911 cases), with the published wave 2 worry and experience indices merged from trend_wrp_21_OLD.sav and resilience from trended_wrp.sav.",
        "21_wrp.sav also holds the 2019 rows; they are excluded here and are in the 2019 file instead.",
        "Urbanicity (6-category) and the four resilience dimensions are missing for the 505 Jamaica cases, which are absent from trended_wrp.sav. Urbanicity2 and resilience_index cover them.",
        "HouseholdSize is the total number of people in the household.",
    ],
    2023: [
        "Source: LRF_WAVE_3_WITH_INDICES_FOR_PUBLIC_RELEASE_10082024_v2.sav (146,910 cases), unchanged apart from the harmonised block.",
        "HouseholdSize counts residents aged 15 and over, not the whole household as in 2019 and 2021. Do not trend it.",
    ],
    2025: [
        "Source: LRF_WAVE4_WITH_INDICES_FOR_PUBLIC_RELEASE.sav (143,459 cases), unchanged apart from the harmonised block.",
        "LRF published no experience index for 2025. experience_score and experience_score_core7 fill that gap.",
        "The published worry_index for 2025 covers ten items and is a simple mean, so it is not comparable with the wave 1-3 published indices.",
        "Resilience in the source file is on a 0-100 scale; resilience_index here is 0-1, resilience_index_100 is 0-100.",
    ],
}


# --------------------------------------------------------------------------- #
# per-wave builders
# --------------------------------------------------------------------------- #
def read(fn, **kw):
    return pyreadstat.read_sav(os.path.join(SRC, fn), **kw)


def _blank_resilience(h):
    for c in ["resilience_index", "resilience_index_100", "resilience_idv",
              "resilience_hhl", "resilience_com", "resilience_soc"]:
        h[c] = np.nan


def build_wave1(lk):
    df, meta = read(F_W1)
    # 19_wrp.sav already carries the published wave 1 indices; take only the
    # variables it lacks (numeric age, Gallup country code, projection weight).
    aux, _ = read(F_TREND2, usecols=["WPID_RANDOM", "Year", "WP5", "Age",
                                     "PROJWT_2019"])
    aux = aux[aux.Year == 2019].drop(columns=["Year"])
    df = df.merge(aux, on="WPID_RANDOM", how="left", validate="one_to_one")

    h = pd.DataFrame(index=df.index)
    h["WPID_RANDOM"] = df.WPID_RANDOM
    h["Wave"] = 1.0
    h["Year"] = 2019.0
    h["WP5"] = df.WP5
    h["Country"] = df.countrynew
    h["COUNTRY_ISO2"] = df.WP5.map(lk.COUNTRY_ISO2)
    h["COUNTRY_ISO3"] = df.WP5.map(lk.COUNTRY_ISO3)
    h["GlobalRegion"] = df.RegionReport
    h["CountryIncomeLevel"] = df.WBI
    h["WGT"] = df.WGT
    h["PROJWT"] = df["PROJWT_2019"]
    h["Age"] = df.Age.mask(df.Age == 100)
    h["AgeGroups3"], h["AgeGroups4"], h["AgeGroups5"] = age_bands(h.Age)
    h["Gender"] = df.WP1219
    h["Education"] = recode(df.Education, {4: 9, 5: 9})
    h["Urbanicity"] = recode(df.WP14, {4: 9, 5: 9})
    h["Urbanicity2"] = urb6_to_urb2(h.Urbanicity)
    h["EMP_2010"] = df.EMP_2010
    h["INCOME_5"] = df.INCOME_5
    h["HouseholdSize"] = recode(df.HouseholdSize, {5: 9})
    h["ChildrenInHousehold"] = df.ChildrenInHousehold
    h["worry_score"] = worry_mean(df, W1_CORE5_W)
    h["worry_score_core7"] = np.nan
    h["worry_index_published"] = df["Worried.Index"]
    h["experience_score"] = exp_mean(df, W1_CORE5_E, "any", wave1=True)
    h["experience_score_self"] = h["experience_score"]
    h["experience_score_core7"] = np.nan
    h["experience_index_published"] = df["Experienced.Index"]
    h["worry_exp_gap"] = h.worry_score - h.experience_score
    _blank_resilience(h)

    consumed = ["WPID_RANDOM", "WP5AA", "countrynew", "YEAR_WAVE", "RegionReport",
                "WBI", "WGT", "WP1219", "Education", "AgeGroups", "Urbanicity",
                "WP14", "EMP_2010", "INCOME_5", "HouseholdSize",
                "ChildrenInHousehold", "Worried.Index", "Experienced.Index",
                "worry_exp_gap", "WP5", "Age", "PROJWT_2019"]
    return h, df, meta, consumed, 2019


def build_wave2(lk):
    df, meta = read(F_W2)
    df = df[df.Year == 2021].reset_index(drop=True)
    a2, _ = read(F_TREND2, usecols=["WPID_RANDOM", "Year", "resilience_index",
                                    "Worried.Index", "Experienced.Index"])
    a2 = (a2[a2.Year == 2021].drop(columns=["Year"])
          .rename(columns={"resilience_index": "resil_w2"}))
    a3, _ = read(F_TREND3, usecols=["WPID_RANDOM", "Year", "Urbanicity",
                                    "resilience_index",
                                    "resilience_idv_0_100_scale",
                                    "resilience_hhl_0_100_scale",
                                    "resilience_com_0_100_scale",
                                    "resilience_soc_0_100_scale"])
    a3 = (a3[a3.Year == 2021].drop(columns=["Year"])
          .rename(columns={"Urbanicity": "Urb6", "resilience_index": "resil_w3"}))
    df = df.merge(a2, on="WPID_RANDOM", how="left", validate="one_to_one")
    df = df.merge(a3, on="WPID_RANDOM", how="left", validate="one_to_one")

    h = pd.DataFrame(index=df.index)
    h["WPID_RANDOM"] = df.WPID_RANDOM
    h["Wave"] = 2.0
    h["Year"] = 2021.0
    h["WP5"] = df.WP5
    h["Country"] = df.Country
    h["COUNTRY_ISO2"] = df.WP5.map(lk.COUNTRY_ISO2)
    h["COUNTRY_ISO3"] = df.WP5.map(lk.COUNTRY_ISO3)
    h["GlobalRegion"] = df.GlobalRegion
    h["CountryIncomeLevel"] = df.CountryIncomeLevel2021
    h["WGT"] = df.WGT
    h["PROJWT"] = df.PROJWT_2021
    h["Age"] = df.Age.mask(df.Age == 100)
    h["AgeGroups3"], h["AgeGroups4"], h["AgeGroups5"] = age_bands(h.Age)
    h["Gender"] = df.Gender
    h["Education"] = recode(df.Education, {4: 9, 5: 9})
    h["Urbanicity"] = recode(df.Urb6, {4: 9, 5: 9})
    h["Urbanicity2"] = df.Urbanicity
    h["EMP_2010"] = df.EMP_2010
    h["INCOME_5"] = df.INCOME_5
    h["HouseholdSize"] = recode(df.HouseholdSize, {5: 9})
    h["ChildrenInHousehold"] = recode(df.ChildrenInHousehold - 1, {6: 9})
    h["worry_score"] = worry_mean(df, CORE5_W)
    h["worry_score_core7"] = worry_mean(df, CORE7_W_REQ, CORE7_W_OPT)
    h["worry_index_published"] = df["Worried.Index"]
    h["experience_score"] = exp_mean(df, CORE5_E, "any")
    h["experience_score_self"] = exp_mean(df, CORE5_E, "self")
    h["experience_score_core7"] = exp_mean(df, CORE7_E, "any")
    h["experience_index_published"] = df["Experienced.Index"]
    h["worry_exp_gap"] = h.worry_score - h.experience_score
    h["resilience_index"] = df.resil_w3.where(df.resil_w3.notna(), df.resil_w2)
    h["resilience_index_100"] = h.resilience_index * 100.0
    for tgt, src in [("resilience_idv", "resilience_idv_0_100_scale"),
                     ("resilience_hhl", "resilience_hhl_0_100_scale"),
                     ("resilience_com", "resilience_com_0_100_scale"),
                     ("resilience_soc", "resilience_soc_0_100_scale")]:
        h[tgt] = df[src] / 100.0

    consumed = ["WPID_RANDOM", "WP5", "Country", "WGT", "Year", "GlobalRegion",
                "CountryIncomeLevel2021", "CountryIncomeLevel2019",
                "PROJWT_2021", "PROJWT_2019", "Age", "AgeGroups4", "Gender",
                "Education", "Urbanicity", "EMP_2010", "INCOME_5",
                "HouseholdSize", "ChildrenInHousehold", "resil_w2", "resil_w3",
                "Urb6", "Worried.Index", "Experienced.Index",
                "resilience_idv_0_100_scale", "resilience_hhl_0_100_scale",
                "resilience_com_0_100_scale", "resilience_soc_0_100_scale"]
    return h, df, meta, consumed, 2021


def _build_late(fn, wave, year, inc_col, pub_worry, pub_exp, resil_div):
    df, meta = read(fn)
    h = pd.DataFrame(index=df.index)
    h["WPID_RANDOM"] = df.WPID_RANDOM
    h["Wave"] = float(wave)
    h["Year"] = float(year)
    h["WP5"] = df.WP5
    h["Country"] = df.Country
    h["COUNTRY_ISO2"] = df.COUNTRY_ISO2
    h["COUNTRY_ISO3"] = df.COUNTRY_ISO3
    h["GlobalRegion"] = df.GlobalRegion
    h["CountryIncomeLevel"] = df[inc_col]
    h["WGT"] = df.WGT
    h["PROJWT"] = df.PROJWT
    h["Age"] = df.Age.mask(df.Age == 100)
    h["AgeGroups3"], h["AgeGroups4"], h["AgeGroups5"] = age_bands(h.Age)
    h["Gender"] = df.Gender
    h["Education"] = recode(df.Education, {4: 9, 5: 9})
    h["Urbanicity"] = recode(df.Urbanicity, {4: 9, 5: 9})
    h["Urbanicity2"] = urb6_to_urb2(h.Urbanicity)
    h["EMP_2010"] = df.EMP_2010
    h["INCOME_5"] = df.INCOME_5
    h["HouseholdSize"] = recode(df.HouseholdSize, {5: 9})
    h["ChildrenInHousehold"] = recode(df.ChildrenInHousehold, {99: 9})
    h["worry_score"] = worry_mean(df, CORE5_W)
    h["worry_score_core7"] = worry_mean(df, CORE7_W_REQ, CORE7_W_OPT)
    h["worry_index_published"] = df[pub_worry]
    h["experience_score"] = exp_mean(df, CORE5_E, "any")
    h["experience_score_self"] = exp_mean(df, CORE5_E, "self")
    h["experience_score_core7"] = exp_mean(df, CORE7_E, "any")
    h["experience_index_published"] = df[pub_exp] if pub_exp else np.nan
    h["worry_exp_gap"] = h.worry_score - h.experience_score
    h["resilience_index"] = df.resilience_index / resil_div
    h["resilience_index_100"] = h.resilience_index * 100.0
    for c in ["resilience_idv", "resilience_hhl", "resilience_com", "resilience_soc"]:
        h[c] = df[c] / resil_div

    consumed = ["WPID_RANDOM", "WP5", "Country", "COUNTRY_ISO2", "COUNTRY_ISO3",
                "WGT", "PROJWT", "Year", "GlobalRegion", inc_col, "Gender", "Age",
                "AgeGroups5", "AgeGroups3", "Education", "Urbanicity", "EMP_2010",
                "INCOME_5", "HouseholdSize", "ChildrenInHousehold", pub_worry,
                "resilience_index", "resilience_idv", "resilience_hhl",
                "resilience_com", "resilience_soc"]
    if pub_exp:
        consumed.append(pub_exp)
    return h, df, meta, consumed, year


def build_wave3(lk):
    return _build_late(F_W3, 3, 2023, "CountryIncomeLevel2023",
                       "Q4_RMw_maxmin", "Q5_RMw_maxmin", 1.0)


def build_wave4(lk):
    return _build_late(F_W4, 4, 2025, "CountryIncomeLevel2025",
                       "worry_index", None, 100.0)


# --------------------------------------------------------------------------- #
# assembly and export
# --------------------------------------------------------------------------- #
def assemble(h, df, meta, consumed, year):
    """Harmonised block first, then the wave's own variables, unchanged."""
    keep = [c for c in df.columns if c not in set(consumed)]
    out = pd.concat([h[HARM_ORDER], df[keep]], axis=1)

    labels = dict(harm_labels(year))
    for c in keep:
        labels[c] = (meta.column_names_to_labels.get(c) or "").replace("\n", " ").strip()
    # four wave 3 variables arrive with no label; they are PROJWT restricted to the
    # cases carrying a valid index, so say that rather than ship a blank label
    for c, lab in UNLABELLED_FIXES.items():
        if c in labels and not labels[c]:
            labels[c] = lab

    vlabs = {k: dict(v) for k, v in HARM_VALUE_LABELS.items()}
    for c in keep:
        ln = meta.variable_to_label.get(c)
        if ln and meta.value_labels.get(ln):
            vlabs[c] = dict(meta.value_labels[ln])

    fmt = {}
    for c in keep:
        ot = meta.original_variable_types.get(c, "")
        if ot.startswith(("ADATE", "DATE", "SDATE", "EDATE", "TIME", "DATETIME")):
            fmt[c] = ot
    return out, labels, vlabs, fmt


def data_dictionary(out, labels, vlabs, notes, year, n_harm):
    rows = []
    for i, c in enumerate(out.columns, start=1):
        s = out[c]
        is_str = s.dtype == object and not isinstance(
            s.dropna().iloc[0] if s.notna().any() else None, (_dt.date, _dt.datetime))
        vt = "string" if is_str else ("date" if s.dtype == object else "numeric")
        vals = ""
        if c in vlabs:
            vals = " | ".join("%s = %s" % (
                int(k) if float(k).is_integer() else k, v)
                for k, v in sorted(vlabs[c].items(), key=lambda kv: float(kv[0])))
        mn = mx = mean = ""
        if vt == "numeric":
            sn = pd.to_numeric(s, errors="coerce")
            if sn.notna().any():
                mn = round(float(sn.min()), 6)
                mx = round(float(sn.max()), 6)
                if not vals:
                    mean = round(float(sn.mean()), 6)
        rows.append({
            "position": i,
            "variable": c,
            "label": labels.get(c, ""),
            "block": "harmonised" if i <= n_harm else "wave-specific",
            "type": vt,
            "n_valid": int(s.notna().sum()),
            "n_missing": int(s.isna().sum()),
            "min": mn,
            "max": mx,
            "mean": mean,
            "value_labels": vals,
            "derivation": notes.get(c, "As supplied in the source file for this wave."),
        })
    return pd.DataFrame(rows)


def clean_for_text(out):
    """Cast whole-number float columns to nullable ints so the CSV reads cleanly."""
    d = out.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            s = d[c].dropna()
            if len(s) and np.isfinite(s).all() and (s == s.round()).all() \
                    and s.abs().max() < 2 ** 62:
                d[c] = d[c].astype("Int64")
    return d


def export(out, labels, vlabs, fmt, dd, year, readme_lines):
    tag = "WRP_%d" % year
    folder = os.path.join(OUT, tag)
    os.makedirs(folder, exist_ok=True)

    sav = os.path.join(folder, tag + ".sav")
    pyreadstat.write_sav(
        out, sav,
        file_label="World Risk Poll %d, harmonised single-wave file" % year,
        column_labels=[labels.get(c, "") for c in out.columns],
        variable_value_labels={k: v for k, v in vlabs.items() if k in out.columns},
        variable_format=fmt or None,
        compress=True,
    )

    txt = clean_for_text(out)
    txt.to_parquet(os.path.join(folder, tag + ".parquet"), index=False,
                   compression="snappy")
    txt.to_csv(os.path.join(folder, tag + ".csv"), index=False,
               encoding="utf-8-sig", lineterminator="\n")
    dd.to_csv(os.path.join(folder, tag + "_data_dictionary.csv"), index=False,
              encoding="utf-8-sig", lineterminator="\n")
    readme = os.path.join(folder, tag + "_README.txt")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("\n".join(readme_lines) + "\n")

    zpath = os.path.join(OUT, tag + ".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for fn in sorted(os.listdir(folder)):
            z.write(os.path.join(folder, fn), fn)
    return folder, zpath


def readme_text(year, out, n_harm, dd):
    L = ["World Risk Poll %d - harmonised single-wave file" % year,
         "=" * 60, "",
         "Built %s by build_wrp_waves.py from the supplied SPSS files." % _dt.date.today().isoformat(),
         "",
         "Cases:     %s" % format(len(out), ","),
         "Variables: %s (%d harmonised, %d wave-specific)" % (
             format(out.shape[1], ","), n_harm, out.shape[1] - n_harm),
         "",
         "Files",
         "-----",
         "WRP_%d.sav                    SPSS, with variable and value labels" % year,
         "WRP_%d.parquet                Apache Parquet, same content" % year,
         "WRP_%d.csv                    CSV of numeric codes, UTF-8 with BOM" % year,
         "WRP_%d_data_dictionary.csv    One row per variable: label, codes, coverage, derivation" % year,
         "",
         "The three data files hold identical content. The CSV stores numeric codes,",
         "not labels; the data dictionary gives the code-to-label mapping for every",
         "categorical variable in its value_labels column.",
         "",
         "Structure",
         "---------",
         "The first %d variables are the harmonised block. They carry the same names," % n_harm,
         "codes and labels in all four wave files, so the waves stack directly.",
         "Everything after that is this wave's own questionnaire content, unchanged",
         "from the source file.",
         "",
         "Notes for this wave",
         "-------------------"]
    for n in WAVE_NOTES[year]:
        L.append("- " + n)
    L += ["",
          "Cross-wave comparability",
          "------------------------",
          "- worry_score and experience_score use the five risk sources asked in",
          "  identical form in every wave, so they trend across all four waves.",
          "- worry_score_core7 and experience_score_core7 add traffic accidents and",
          "  work, and so cover 2021 to 2025 only.",
          "- worry_index_published and experience_index_published are the figures LRF",
          "  published for each wave. They are not comparable between waves: the item",
          "  sets change and wave 4 switched from a Rasch-weighted, min-max scaled",
          "  index to a simple mean. Quote them for single-wave figures, use the",
          "  computed scores for trends.",
          "- experience_score counts harm to the respondent or to someone they know.",
          "  2019 asked about the respondent only, so its wording is not identical,",
          "  but this is the definition LRF itself uses to trend the series and the",
          "  one that produces a coherent trend. experience_score_self holds the",
          "  strictly personal definition, which is comparable 2021 to 2025.",
          "- Resilience was first measured in 2021, so the 2019 file has none.",
          "- Country coverage differs by wave: 142 countries and areas in 2019, 121",
          "  in 2021, 142 in 2023 and 140 in 2025. For a global trend, restrict to",
          "  the countries present in every wave you are comparing, otherwise part",
          "  of the change you see is a change in the sample of countries.",
          ""]
    return L


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)
    lk = country_lookup()
    n_harm = len(HARM_ORDER)
    summary = []
    for builder in (build_wave1, build_wave2, build_wave3, build_wave4):
        h, df, meta, consumed, year = builder(lk)
        out, labels, vlabs, fmt = assemble(h, df, meta, consumed, year)
        dd = data_dictionary(out, labels, vlabs, harm_notes(year), year, n_harm)
        folder, zpath = export(out, labels, vlabs, fmt, dd, year,
                               readme_text(year, out, n_harm, dd))
        summary.append((year, len(out), out.shape[1],
                        os.path.getsize(zpath) / 1e6))
        print("%d: %s cases, %d variables -> %s (%.1f MB zip)" % (
            year, format(len(out), ","), out.shape[1], os.path.basename(zpath),
            os.path.getsize(zpath) / 1e6))
        del h, df, out
    print("\nDone. Output in %s" % OUT)


if __name__ == "__main__":
    main()
