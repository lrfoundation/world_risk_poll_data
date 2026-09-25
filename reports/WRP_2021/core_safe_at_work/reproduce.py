"""Reproduce World Risk Poll 2021: Safe at Work? Global experiences of violence and harassment.

Run from the repository root:
    python reports/WRP_2021/core_safe_at_work/reproduce.py

Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, load_wave, merge_gallup, pct  # noqa: E402

report = Report(__file__)

SEX = {1: "men", 2: "women"}  # Gender: 1 = Male, 2 = Female
REGION = {  # GlobalRegion
    1: "eastern_africa", 2: "central_western_africa", 3: "northern_africa", 4: "southern_africa",
    5: "latin_america", 6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia",
    10: "southern_asia", 11: "middle_east", 12: "eastern_europe", 13: "northern_western_europe",
    14: "southern_europe", 15: "australia_nz",
}
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}  # CountryIncomeLevel
INCOME_LABEL = {1: "Low", 2: "Lower-middle", 3: "Upper-middle", 4: "High"}  # as printed in Table 1.1
EDUCATION = {3: "tertiary", 2: "secondary", 1: "primary"}  # Education
QUINTILE = {1: "poorest", 2: "second", 3: "middle", 4: "fourth", 5: "richest"}  # INCOME_5
BIRTH = {1: "native", 2: "foreign"}  # Gallup WP4657: 1 = born in this country, 2 = born in another country

VH = ["WP22400_ALL", "WP22403_ALL", "WP22406_ALL"]  # physical, psychological, sexual V&H at work: ever
TIMES = ["WP22401", "WP22404_ALL", "WP22407_ALL"]  # how many times (asked if yes)
WHEN = ["WP22402", "WP22405_ALL", "WP22408_ALL"]  # when last (asked if yes)
FORMS = dict(zip(["physical", "psychological", "sexual"], VH))
FORM_TIMES = dict(zip(["physical", "psychological", "sexual"], TIMES))
DISCRIMINATION = {"skin": "WP22259", "religion": "WP22260", "nationality": "WP22261",
                  "gender": "WP22262", "disability": "WP22263"}
TOLD_WHOM = {"employer": "WP22410", "coworker": "WP22411", "family": "WP22412", "union": "WP22413",
             "police": "WP22421", "social": "WP22414"}
NOT_TOLD = {"waste": "WP22415", "not_know": "WP22416", "procedures": "WP22417", "find_out": "WP22418",
            "punishment": "WP22419", "reputation": "WP22420"}

d = load_wave(2021, [
    "WPID_RANDOM", "PROJWT", "Gender", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel", "Education",
    "INCOME_5", "EMP_2010", *VH, *TIMES, *WHEN, "WP22406", "WP22409", *TOLD_WHOM.values(), *NOT_TOLD.values(),
    *DISCRIMINATION.values(),
])

# --- Derived variables ---------------------------------------------------------

# Never worked: "respondent has never worked" (code 7) at any of the three V&H
# questions. Everyone else is the report's base ("ever worked", 113,873
# respondents, Appendix 3). Unlike the Focus On: Risk and Gender report, China
# stays in the base: it was not asked the physical question, but was asked the
# psychological and (modified) sexual ones.
d["never_worked"] = np.where(d[VH].eq(7).any(axis=1), 1, 2)
ever = d[d.never_worked == 2].copy()

# Number of forms experienced and any V&H (1 = yes, 2 = no).
ever["n_forms"] = ever[VH].eq(1).sum(axis=1)
ever["any_vh"] = np.where(ever.n_forms > 0, 1, 2)

# When last experienced (Chart 1.1): the most recent timing over the forms
# experienced. 0 = never experienced, 8 = experienced but no timing given.
timing = ever[WHEN].where(ever[WHEN].isin([1, 2, 3]))
ever["when"] = np.where(ever.n_forms == 0, 0, timing.min(axis=1).fillna(8))

# Any discrimination: yes to any of the five types. As in the Focus On: Risk
# and Gender report, respondents in countries that were not asked count as no.
ever["any_discrimination"] = np.where(ever[list(DISCRIMINATION.values())].eq(1).any(axis=1), 1, 2)

# Those who experienced any V&H: the base for number of forms (Chart 2.1),
# telling someone (Chapter 3) and the frequency questions.
anyvh = ever[ever.n_forms > 0].copy()

# Combination of forms (Chart 2.2). This chart uses only respondents who
# answered yes or no to all three questions (see README).
complete = anyvh[anyvh[VH].isin([1, 2]).all(axis=1)].copy()
p, y, s = (complete[v].eq(1) for v in VH)
complete["combination"] = np.select(
    [p & ~y & ~s, y & ~p & ~s, s & ~p & ~y, p & y & ~s, s & y & ~p, s & p & ~y, p & y & s],
    [1, 2, 3, 4, 5, 6, 7],
)
complete["sexual_element"] = np.where(s, 1, 2)
COMBINATION = {"physical": 1, "psychological": 2, "sexual": 3, "psychological_physical": 4,
               "sexual_psychological": 5, "sexual_physical": 6, "all_three": 7}

# Question order (Appendix 3): physical, psychological, sexual; in China,
# which was not asked the physical question, psychological then sexual.
china = d.COUNTRY_ISO3.eq("CHN")
d["q1"] = np.where(china, d.WP22403_ALL, d.WP22400_ALL)
d["q2"] = np.where(china, d.WP22406_ALL, d.WP22403_ALL)
d["q3"] = np.where(china, np.nan, d.WP22406_ALL)
d["never_at"] = np.select([d.q1.eq(7), d.q2.eq(7), d.q3.eq(7)], [1, 2, 3], default=0)

# --- Helpers -------------------------------------------------------------------


def by(df, var, codes, group, names):
    """% with `var` in `codes` for each `group` code, keyed by names[code]."""
    r = pct(df, var, codes, by=group)
    return {name: r[code] for code, name in names.items()}


def by_sex(df, var, codes):
    return by(df, var, codes, "Gender", SEX)


def one(df, var, codes, group, code):
    """% with `var` in `codes` in one group."""
    return pct(df, var, codes, by=group)[code]


def two(df, var, codes, group1, code1, group2, code2):
    """% with `var` in `codes` in one cell of two groupings."""
    return pct(df[df[group1] == code1], var, codes, by=group2)[code2]


def gap(df, var, codes, group, higher, lower):
    r = pct(df, var, codes, by=group)
    return r[higher] - r[lower]


def categories(df, var, cats, group=None, names=None):
    """% in each named category of `var`: {"<name>_<cat>": %} (or {"<cat>": %} without `group`)."""
    if group is None:
        t = distribution(df, var)
        return {cat: t[t.index.intersection(codes)].sum() for cat, codes in cats.items()}
    t = distribution(df, var, by=group)
    return {f"{name}_{cat}": t.loc[code, t.columns.intersection(codes)].sum()
            for code, name in names.items() for cat, codes in cats.items()}


def three_plus(df, var):
    """Of those asked how often (those who experienced the form), % three or more times."""
    return pct(df, var, [2, 3])


def women(df):
    return df[df.Gender == 2]


def with_birth(df):
    """Add the Gallup World Poll 'born in this country' item (WP4657)."""
    return merge_gallup(df, ["WP4657"])


YES_NO = {"yes": [1], "no": [2]}
N_FORMS = {"one": [1], "two": [2], "three": [3]}

# --- Executive summary -----------------------------------------------------------


@report.finding("X01")
def respondents():
    return len(d)


@report.finding("X02")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X03")
def any_vh():
    return pct(ever, "any_vh", [1])


@report.finding("X04")
def more_than_once():
    # Each form experienced counts once: the share of experiences that
    # happened three or more times (see README for the alternatives).
    long = pd.concat([ever[[t, "PROJWT"]].rename(columns={t: "times"}) for t in TIMES])
    return pct(long, "times", [2, 3])


@report.finding("X05")
def any_vh_by_sex():
    return by_sex(ever, "any_vh", [1])


@report.finding("X06")
def each_form():
    return {form: pct(ever, var, [1]) for form, var in FORMS.items()}


@report.finding("X07")
def multiple_forms():
    return pct(anyvh, "n_forms", [2, 3])


@report.finding("X08")
def sexual_element():
    return by_sex(complete, "sexual_element", [1])


@report.finding("X09")
def australia_nz():
    return one(ever, "any_vh", [1], "GlobalRegion", 15)


@report.finding("X10")
def tertiary_women():
    return {"experienced": one(women(ever), "any_vh", [1], "Education", 3),
            "told": one(women(anyvh), "WP22409", [1], "Education", 3)}


@report.finding("X11")
def women_by_birth():
    return by(with_birth(women(ever)), "any_vh", [1], "WP4657", {2: "foreign", 1: "native"})


def birth_gap_by_quintile(df, var):
    """Foreign-born minus native-born, % with `var` = 1, by income quintile."""
    r = pct(with_birth(df), var, [1], by=["INCOME_5", "WP4657"])
    return {name: r[(q, 2)] - r[(q, 1)] for q, name in QUINTILE.items()}


@report.finding("X12")
def women_birth_gap_by_quintile():
    g = birth_gap_by_quintile(women(ever), "any_vh")
    return {"poorest": g["poorest"], "richest": g["richest"]}


# --- Chapter 1 -------------------------------------------------------------------

WHEN_CATS = {"last_year": [1], "two_five": [2], "five_plus": [3]}


@report.finding("X13")
def when_last():
    return categories(ever, "when", WHEN_CATS)


@report.finding("X14")
def when_unknown():
    return pct(ever, "when", [8])


@report.finding("C1_1")
def when_chart():
    return categories(ever, "when", {"no": [0], **WHEN_CATS})


@report.finding("C1_2")
def any_vh_chart_by_sex():
    return categories(ever, "any_vh", {"no": [2], "yes": [1]}, "Gender", SEX)


@report.finding("X15")
def ever_and_never_counts():
    return {"ever": int((d.never_worked == 2).sum()), "never": int((d.never_worked == 1).sum())}


@report.finding("X16")
def employed_count():
    return int(d.EMP_2010.isin([1, 2, 3, 5]).sum())


@report.finding("X17")
def regions_text():
    r = pct(ever, "any_vh", [1], by="GlobalRegion")
    rs = pct(ever, "any_vh", [1], by=["GlobalRegion", "Gender"])
    return {
        "northern_america": r[6], "australia_nz_women": rs[(15, 2)],
        "northern_america_gap": rs[(6, 2)] - rs[(6, 1)], "southern_africa_gap": rs[(4, 1)] - rs[(4, 2)],
        "central_asia": r[7], "central_asia_men": rs[(7, 1)], "central_asia_women": rs[(7, 2)],
    }


@report.finding("C1_3")
def regions_by_sex():
    rs = pct(ever, "any_vh", [1], by=["GlobalRegion", "Gender"])
    return {f"{region}_{sex}": rs[(r, s)] for r, region in REGION.items() for s, sex in SEX.items()}


def country(iso, var="any_vh", df=None):
    """(all, men, women) % with `var` = 1 in a country."""
    g = (ever if df is None else df)
    g = g[g.COUNTRY_ISO3 == iso]
    r = pct(g, var, [1], by="Gender")
    return pct(g, var, [1]), r[1], r[2]


@report.finding("X18")
def australia_finland():
    return {"AUS": country("AUS")[0], "AUS_men": country("AUS")[1], "FIN_women": country("FIN")[2]}


TABLE_1_1 = ["AUS", "FIN", "ISL", "NZL", "DNK", "USA", "NOR", "CAN", "GRC", "SWE",
             "KGZ", "LBN", "MYS", "UZB", "ARM", "IDN", "GEO", "KAZ", "PAK", "TJK"]


@report.finding("T1_1")
def highest_and_lowest_countries():
    out = {}
    for iso in TABLE_1_1:
        a, m, w = country(iso)
        out.update({f"{iso}_all": a, f"{iso}_men": m, f"{iso}_women": w, f"{iso}_diff": w - m})
        out[f"{iso}_income"] = INCOME_LABEL[int(ever.loc[ever.COUNTRY_ISO3 == iso, "CountryIncomeLevel"].iloc[0])]
    return out


@report.finding("X19")
def australia_2019():
    # World Risk Poll 2019: L21D, experienced harm while working in the past
    # two years from physical harassment or violence (asked of those who work).
    w19 = load_wave(2019, ["COUNTRY_ISO3", "PROJWT", "Gender", "L21D"])
    return by_sex(w19[w19.COUNTRY_ISO3 == "AUS"], "L21D", [1])


@report.finding("X20")
def finland():
    return country("FIN")[0]


@report.finding("X21")
def tajikistan():
    a, m, w = country("TJK")
    return {"all": a, "gap": w - m}


@report.finding("C1_4")
def income_by_sex():
    r = pct(ever, "any_vh", [1], by=["CountryIncomeLevel", "Gender"])
    return {f"{inc}_{sex}": r[(i, s)] for i, inc in INCOME.items() for s, sex in SEX.items()}


@report.finding("X22")
def income_text():
    out = by(ever, "any_vh", [1], "CountryIncomeLevel", INCOME)
    r = pct(ever, "any_vh", [1], by=["CountryIncomeLevel", "Gender"])
    return {"low": out["low"], "high": out["high"], "lower_middle": out["lower_middle"],
            "upper_middle": out["upper_middle"], "high_gap": r[(4, 2)] - r[(4, 1)]}


@report.finding("C1_5")
def never_worked_by_income():
    r = pct(d, "never_worked", [1], by=["CountryIncomeLevel", "Gender"])
    return {f"{inc}_{sex}": r[(i, s)] for i, inc in INCOME.items() for s, sex in SEX.items()}


@report.finding("X23")
def never_worked_text():
    s = by_sex(d, "never_worked", [1])
    r = pct(d, "never_worked", [1], by=["CountryIncomeLevel", "Gender"])
    return {"men": s["men"], "women": s["women"], "low_women": r[(1, 2)], "lower_middle_women": r[(2, 2)]}


@report.finding("X24")
def by_discrimination():
    return by(ever, "any_vh", [1], "any_discrimination", {1: "discrimination", 2: "none"})


@report.finding("C1_6")
def by_discrimination_chart():
    return categories(ever, "any_vh", {"no": [2], "yes": [1]}, "any_discrimination",
                      {1: "discrimination", 2: "none"})


@report.finding("C1_7")
def by_discrimination_type():
    # Both bars are % who experienced V&H: among those who said no (2) and yes
    # (1) to each type of discrimination.
    return {f"{kind}_{answer}": one(ever, "any_vh", [1], var, code)
            for kind, var in [("gender", "WP22262"), ("skin", "WP22259"), ("nationality", "WP22261"),
                              ("religion", "WP22260"), ("disability", "WP22263")]
            for answer, code in (("no", 2), ("yes", 1))}


@report.finding("X25")
def by_discrimination_type_text():
    def sex(kind, code):
        return two(ever, "any_vh", [1], DISCRIMINATION[kind], 1, "Gender", code)
    return {
        "gender": one(ever, "any_vh", [1], "WP22262", 1), "gender_men": sex("gender", 1),
        "gender_women": sex("gender", 2), "religion_men": sex("religion", 1), "religion_women": sex("religion", 2),
        "disability_men": sex("disability", 1), "disability_women": sex("disability", 2),
    }


@report.finding("C1_8")
def forms_chart():
    return {f"{form}_{answer}": pct(ever, var, codes)
            for form, var in [("sexual", "WP22406_ALL"), ("psychological", "WP22403_ALL"),
                              ("physical", "WP22400_ALL")]
            for answer, codes in YES_NO.items()}


def form_text(var, regions, extra=None):
    """% yes to one form: by sex, and for named regions (overall, by sex, gap)."""
    out = by_sex(ever, var, [1])
    r = pct(ever, var, [1], by="GlobalRegion")
    rs = pct(ever, var, [1], by=["GlobalRegion", "Gender"])
    for code, parts in regions.items():
        name = REGION[code]
        for part in parts:
            if part == "all":
                out[name] = r[code]
            elif part == "gap":
                out[f"{name}_gap"] = rs[(code, 2)] - rs[(code, 1)]
            else:
                out[f"{name}_{part}"] = rs[(code, 1 if part == "men" else 2)]
    return {**out, **(extra or {})}


@report.finding("X26")
def psychological_text():
    return form_text("WP22403_ALL", {15: ["all", "women", "men"], 6: ["all", "women", "men"], 7: ["all", "gap"]})


@report.finding("X27")
def physical_text():
    inc = pct(ever, "WP22400_ALL", [1], by="CountryIncomeLevel")
    return form_text("WP22400_ALL", {15: ["all"], 6: ["all", "women", "men"], 1: ["all", "men", "women"],
                                     2: ["all", "men", "women"], 7: ["all"]},
                     {"low_income": inc[1], "lower_middle_income": inc[2]})


@report.finding("X28")
def sexual_text():
    return form_text("WP22406_ALL", {6: ["all", "women", "men"], 15: ["all", "women", "men"]})


@report.finding("C1_9")
def forms_by_sex_chart():
    out = {}
    for form, var in [("sexual", "WP22406_ALL"), ("psychological", "WP22403_ALL"), ("physical", "WP22400_ALL")]:
        for key, value in categories(ever, var, YES_NO, "Gender", SEX).items():
            out[f"{form}_{key}"] = value
    return out


@report.finding("X29")
def frequency_text():
    def region(var, code):
        return one(ever, var, [2, 3], "GlobalRegion", code)
    phys, psych, sex = TIMES
    anz = ever[ever.GlobalRegion == 15]
    nam = ever[ever.GlobalRegion == 6]
    return {
        "psychological": three_plus(ever, psych), "psychological_more_five": pct(ever, psych, [3]),
        "psychological_australia_nz": region(psych, 15), "psychological_northern_america": region(psych, 6),
        "physical_NLD": three_plus(ever[ever.COUNTRY_ISO3 == "NLD"], phys),
        "sexual_BRA": three_plus(ever[ever.COUNTRY_ISO3 == "BRA"], sex),
        "physical": three_plus(ever, phys), "sexual": three_plus(ever, sex),
        "physical_australia_nz": region(phys, 15), "physical_central_western_africa": region(phys, 2),
        "sexual_australia_nz": region(sex, 15), "sexual_northern_america": region(sex, 6),
        "sexual_australia_nz_women": one(anz, sex, [2, 3], "Gender", 2),
        "sexual_australia_nz_men": one(anz, sex, [2, 3], "Gender", 1),
        "sexual_northern_america_gap": gap(nam, sex, [2, 3], "Gender", 2, 1),
    }


FREQUENCY = {"once_twice": [1], "three_five": [2], "more_five": [3]}


@report.finding("C1_10")
def frequency_chart():
    out = {}
    for form in ("sexual", "psychological", "physical"):
        for key, value in categories(ever, FORM_TIMES[form], FREQUENCY).items():
            out[f"{form}_{key}"] = value
    return out


@report.finding("T1_2")
def frequency_top_regions():
    out = {}
    for form, regions in [("physical", [15, 2, 8]), ("psychological", [15, 6, 12]), ("sexual", [6, 15, 7])]:
        r = pct(ever, FORM_TIMES[form], [2, 3], by="GlobalRegion")
        for code in regions:
            out[f"{form}_{REGION[code]}"] = r[code]
        top = r.sort_values(ascending=False).index[:3]
        out[f"{form}_top3"] = "; ".join(REGION[int(c)] for c in top)
    return out


# --- Chapter 2 -------------------------------------------------------------------


@report.finding("X30")
def number_of_forms():
    return categories(anyvh, "n_forms", N_FORMS)


@report.finding("X31")
def number_of_forms_countries():
    three = pct(anyvh, "n_forms", [3], by="COUNTRY_ISO3")
    return {"SEN_three": three["SEN"], "ZMB_three": three["ZMB"], "UGA_three": three["UGA"],
            "ZAF_three": three["ZAF"], "SEN_multiple": pct(anyvh, "n_forms", [2, 3], by="COUNTRY_ISO3")["SEN"]}


@report.finding("C2_1")
def number_of_forms_by_sex():
    return categories(anyvh, "n_forms", N_FORMS, "Gender", SEX)


@report.finding("X32")
def combinations_text():
    t = distribution(complete, "combination", by="Gender")
    items = [("men", "psychological"), ("men", "psychological_physical"), ("men", "physical"),
             ("women", "psychological"), ("women", "sexual"), ("women", "sexual_psychological")]
    return {f"{sex}_{c}": t.loc[1 if sex == "men" else 2, COMBINATION[c]] for sex, c in items}


@report.finding("C2_2")
def combinations_chart():
    out = categories(complete, "combination", {c: [code] for c, code in COMBINATION.items()}, "Gender", SEX)
    del out["men_sexual_physical"]  # not labelled in the chart
    return out


@report.finding("X33")
def forms_by_discrimination():
    multiple = pct(anyvh, "n_forms", [2, 3], by="any_discrimination")
    three = pct(anyvh, "n_forms", [3], by="any_discrimination")
    return {"multiple_discrimination": multiple[1], "multiple_none": multiple[2],
            "three_none": three[2], "three_discrimination": three[1]}


@report.finding("C2_3")
def forms_by_discrimination_chart():
    out = categories(anyvh, "n_forms", N_FORMS, "any_discrimination", {1: "discrimination", 2: "none"})
    del out["none_three"]  # not labelled in the chart
    return out


@report.finding("X34")
def multiple_forms_groups():
    def both(group, code):
        return (one(anyvh, "n_forms", [2, 3], group, code), one(anyvh, "n_forms", [3], group, code))
    out = {}
    for name, (group, code) in {"low_income": ("CountryIncomeLevel", 1), "eastern_africa": ("GlobalRegion", 1),
                                "southern_africa": ("GlobalRegion", 4)}.items():
        out[f"{name}_multiple"], out[f"{name}_three"] = both(group, code)
    return out


# --- Chapter 3 -------------------------------------------------------------------


@report.finding("X35")
def education_text():
    e = pct(ever, "any_vh", [1], by="Education")
    r = pct(ever, "any_vh", [1], by=["Education", "Gender"])
    return {
        "tertiary": e[3], "primary": e[1], "secondary": e[2], "men_tertiary": r[(3, 1)], "men_primary": r[(1, 1)],
        "women_primary": r[(1, 2)], "women_gap": r[(3, 2)] - r[(1, 2)], "men_gap": r[(3, 1)] - r[(1, 1)],
    }


@report.finding("C3_1")
def women_forms_by_education():
    return categories(women(ever), "n_forms", {"none": [0], "one": [1], "two": [2]}, "Education", EDUCATION)


@report.finding("X36")
def women_education_gap_countries():
    r = pct(women(ever), "any_vh", [1], by=["COUNTRY_ISO3", "Education"])
    return {iso: r[(iso, 3)] - r[(iso, 1)] for iso in ("DEU", "SWE", "ITA", "ISR")}


@report.finding("X37")
def told_text():
    r = pct(anyvh, "WP22409", [1], by=["Education", "Gender"])
    return {"women_secondary": r[(2, 2)], "women_primary": r[(1, 2)], "all": pct(anyvh, "WP22409", [1]),
            "men_primary": r[(1, 1)], "men_secondary": r[(2, 1)], "men_tertiary": r[(3, 1)]}


@report.finding("C3_2")
def women_told_by_education():
    return categories(women(anyvh), "WP22409", {"no": [2], "yes": [1]}, "Education", EDUCATION)


@report.finding("T3_1")
def women_told_whom_by_education():
    told = women(anyvh)[women(anyvh).WP22409 == 1]
    return {f"{edu}_{who}": one(told, var, [1], "Education", e)
            for e, edu in EDUCATION.items() for who, var in TOLD_WHOM.items()}


@report.finding("T3_2")
def women_reasons_by_education():
    not_told = women(anyvh)[women(anyvh).WP22409 == 2]
    return {f"{edu}_{reason}": one(not_told, NOT_TOLD[reason], [1], "Education", e)
            for e, edu in EDUCATION.items() for reason in ("find_out", "reputation", "waste")}


@report.finding("C3_3")
def by_birth_and_sex():
    r = pct(with_birth(ever), "any_vh", [1], by=["Gender", "WP4657"])
    return {f"{sex}_{birth}": r[(s, b)] for s, sex in ((2, "women"), (1, "men")) for b, birth in BIRTH.items()}


@report.finding("X38")
def by_birth_text():
    r = pct(with_birth(ever), "any_vh", [1], by=["Gender", "WP4657"])
    return {"men_foreign": r[(1, 2)], "men_native": r[(1, 1)], "women_native": r[(2, 1)]}


def birth_by(df, var, group, names):
    r = pct(with_birth(df), var, [1], by=[group, "WP4657"])
    return {f"{name}_{birth}": r[(g, b)] for g, name in names.items() for b, birth in BIRTH.items()}


@report.finding("C3_4")
def women_by_quintile_and_birth():
    return birth_by(women(ever), "any_vh", "INCOME_5", QUINTILE)


@report.finding("C3_5")
def women_by_income_and_birth():
    return birth_by(women(ever), "any_vh", "CountryIncomeLevel", INCOME)


@report.finding("X39")
def women_skin_discrimination_poorest():
    r = pct(with_birth(women(anyvh)), "WP22259", [1], by=["INCOME_5", "WP4657"])
    return {"foreign": r[(1, 2)], "native": r[(1, 1)]}


@report.finding("C3_6")
def women_skin_discrimination():
    return birth_by(women(anyvh), "WP22259", "INCOME_5", QUINTILE)


@report.finding("C3_7")
def women_nationality_discrimination():
    return birth_by(women(anyvh), "WP22261", "INCOME_5", QUINTILE)


@report.finding("X40")
def women_telling_by_birth():
    g = with_birth(women(anyvh))
    told = g[g.WP22409 == 1]
    not_told = g[g.WP22409 == 2]

    def birth(df, var):
        r = pct(df, var, [1], by="WP4657")
        return r[1], r[2]  # native, foreign

    out = {}
    out["told_native"], out["told_foreign"] = birth(g, "WP22409")
    q = pct(g, "WP22409", [1], by=["INCOME_5", "WP4657"])
    out["told_poorest_gap"] = q[(1, 1)] - q[(1, 2)]
    for key, (df, var) in {"employer": (told, "WP22410"), "coworker": (told, "WP22411"), "family": (told, "WP22412"),
                           "not_know": (not_told, "WP22416"), "procedures": (not_told, "WP22417"),
                           "punishment": (not_told, "WP22419")}.items():
        out[f"{key}_native"], out[f"{key}_foreign"] = birth(df, var)
    return out


@report.finding("C3_8")
def women_told_by_quintile_and_birth():
    return birth_by(women(anyvh), "WP22409", "INCOME_5", QUINTILE)


# --- Appendix 3: data filtering --------------------------------------------------


@report.finding("X41")
def never_worked_after_first_question():
    later = d[(d.never_worked == 1) & (d.never_at != 1)]
    return {"answered_first": len(later), "first_yes": int(later.q1.eq(1).sum()),
            "first_no": int(later.q1.eq(2).sum())}


@report.finding("X42")
def modified_sexual_question():
    # Not explained (see README): respondents outside China who reached the
    # sexual question in its modified wording (WP22406 missing, WP22406_ALL
    # answered, not never worked at an earlier question).
    reached = d.WP22406.isna() & d.WP22406_ALL.notna() & d.never_at.isin([0, 3])
    return int((reached & ~china).sum())


@report.finding("X43")
def never_at_third_women():
    third = d[d.never_at == 3]
    return 100 * (third.Gender == 2).mean()


@report.finding("X44")
def yes_before_never():
    return int(d.loc[d.never_worked == 1, VH].eq(1).sum().sum())


@report.finding("TA3_1")
def never_worked_by_question():
    counts = d.never_at.value_counts()
    return {"first": counts[1], "second": counts[2], "third": counts[3], "total": int((d.never_at > 0).sum())}


if __name__ == "__main__":
    sys.exit(report.run())
