"""Reproduce World Risk Poll 2021 Focus On: Risk and Gender.

Run from the repository root:
    python reports/WRP_2021/focus_on_risk_and_gender/reproduce.py

Every chart and table in the report compares women and men. Each function
below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, load_wave, merge_gallup, pct, wmean  # noqa: E402

report = Report(__file__)

SEX = {2: "women", 1: "men"}  # Gender: 1 = Male, 2 = Female
DK = [98, 99]
VH = ["WP22400_ALL", "WP22403_ALL", "WP22406_ALL"]  # physical, psychological, sexual V&H at work

d = load_wave(2021, [
    "WPID_RANDOM", "PROJWT", "Gender", "COUNTRY_ISO3", "EMP_2010", "resilience_index",
    "WP20711", "WP20719", "WP22331",
    "WP20720", "WP20721", "WP20722", "WP20723", "WP22213", "WP20726", "WP22214",
    "WP22442", "WP22443", "WP22444", "WP22445", "WP22446", "WP22447", "WP22448",
    "WP22228", "WP22229", "WP22230", "WP22245", "WP22241", "WP22244", "WP22242", "WP22243",
    "WP22240", "WP22252", "WP22253", "WP22254", "WP22255", "WP22256", "WP22257", "WP22258",
    "WP22259", "WP22260", "WP22261", "WP22262", "WP22263",
    "WP22222", "WP22223", "WP22225", "WP22224", "WP22226", "WP22227",
    *VH, "WP22401", "WP22404_ALL", "WP22407_ALL", "WP22409",
    "WP22410", "WP22411", "WP22412", "WP22413", "WP22421", "WP22414",
    "WP22415", "WP22416", "WP22417", "WP22418", "WP22419", "WP22420", "WP22422",
])

# --- Derived variables ---------------------------------------------------------

# Basic needs (Chart 2.2): the first question splits less / more than a month,
# follow-ups give weeks or months. 4 and 9 = follow-up missing or DK.
d["basic_needs"] = np.select(
    [d.WP22228.eq(1) & d.WP22229.isin([1, 2, 3]), d.WP22228.eq(1),
     d.WP22228.eq(2) & d.WP22230.isin([1, 2, 3, 4]), d.WP22228.eq(2)],
    [d.WP22229, 4, d.WP22230 + 4, 9], default=98,
)

# Any discrimination (Chart 2.8): yes to any of the five types. Respondents
# in countries that were not asked count as "no", which is what reproduces
# the published figures (see README).
DISCRIMINATION = ["WP22259", "WP22260", "WP22261", "WP22262", "WP22263"]
d["any_discrimination"] = np.where(d[DISCRIMINATION].eq(1).any(axis=1), 1, 2)

# Never worked (Chart 4.1): "respondent has never worked" (code 7) given at
# any of the three V&H questions. Chapter 4 charts use everyone else,
# including China, where the physical V&H question was not asked.
d["never_worked"] = np.where(d[VH].eq(7).any(axis=1), 1, 2)
ever = d[d.never_worked == 2].copy()

# Employment (Chart 4.2), among those who have ever worked.
ever["employment"] = ever.EMP_2010.map({1: 1, 2: 1, 3: 1, 5: 1, 4: 2, 6: 3})  # employed/unemployed/out
ever["employment_type"] = ever.EMP_2010.map({1: 1, 3: 2, 5: 2, 2: 3, 4: 4})  # FT/PT/self/unemployed

# Forms of V&H experienced (Charts 4.3, 4.4).
yes = ever[VH].eq(1)
ever["n_forms"] = yes.sum(axis=1)
# Chart 4.4 splits the combinations among those who answered yes or no to all
# three questions (so China, not asked about physical V&H, is left out).
answered_all = ever[VH].isin([1, 2]).all(axis=1)
anyvh = ever[(ever.n_forms > 0) & answered_all].copy()
p, y, s = (anyvh[v].eq(1) for v in VH)
anyvh["combination"] = np.select(
    [p & ~y & ~s, y & ~p & ~s, s & ~p & ~y, p & y & ~s, s & y & ~p, s & p & ~y, p & y & s],
    [1, 2, 3, 4, 5, 6, 7],
)
anyvh["sexual_element"] = np.where(s, 1, 2)

# --- Helpers -------------------------------------------------------------------


def by_sex(df, var, categories):
    """% in each named category of `var` for women and men: {"women_<name>": %, ...}."""
    table = distribution(df, var, by="Gender")
    return {
        f"{sex}_{name}": table.loc[code, table.columns.intersection(codes)].sum()
        for code, sex in SEX.items() for name, codes in categories.items()
    }


def gap(df, var, codes, higher="women"):
    """Percentage-point gap between the sexes: `higher` minus the other."""
    r = pct(df, var, codes, by="Gender")
    return r[2] - r[1] if higher == "women" else r[1] - r[2]


YES_NO = {"yes": [1], "no": [2]}
WORRY = {"very": [1], "somewhat": [2], "not": [3]}

# --- Introduction ----------------------------------------------------------------


@report.finding("X01")
def respondents():
    return len(d)


@report.finding("X02")
def women_respondents():
    return int((d.Gender == 2).sum())


@report.finding("X03")
def countries():
    return d.COUNTRY_ISO3.nunique()


def born_abroad_women_not_told(var):
    # Needs the Gallup World Poll "born in this country" item (WP4657:
    # 1 = born in this country, 2 = born in another country).
    g = merge_gallup(d[(d.Gender == 2) & (d.WP22409 == 2)], ["WP4657"])
    r = pct(g, var, [1], by="WP4657")
    return r[2], r[1]


@report.finding("X04")
def born_abroad_not_know():
    return born_abroad_women_not_told("WP22416")[0]


@report.finding("X05")
def native_born_not_know():
    return born_abroad_women_not_told("WP22416")[1]


@report.finding("X06")
def born_abroad_procedures():
    return born_abroad_women_not_told("WP22417")[0]


@report.finding("X07")
def native_born_procedures():
    return born_abroad_women_not_told("WP22417")[1]


@report.finding("X08")
def gap_more_safe_intro():
    return gap(d, "WP20711", [1], higher="men")


@report.finding("X09")
def gap_less_safe_intro():
    return gap(d, "WP20711", [2])


@report.finding("X10")
def gap_worry_crime_intro():
    return gap(d, "WP20722", [1])


@report.finding("X11")
def gap_experience_crime():
    return gap(d, "WP22444", [1])


@report.finding("X12")
def gap_worry_mental_intro():
    return gap(d, "WP20726", [1])


@report.finding("X13")
def women_experience_mental():
    return pct(d, "WP22447", [1], by="Gender")[2]


@report.finding("X14")
def gap_experience_mental():
    return gap(d, "WP22447", [1])


@report.finding("X15")
def gap_less_than_week():
    return gap(d, "basic_needs", [1])


@report.finding("X16")
def gap_month_or_less():
    return gap(d, "basic_needs", [1, 2, 3, 4, 5])


@report.finding("X17")
def gap_never_worked_intro():
    return gap(d, "never_worked", [1])


@report.finding("X18")
def women_unemployed_or_out():
    return pct(ever, "employment", [2, 3], by="Gender")[2]


@report.finding("X19")
def men_unemployed_or_out():
    return pct(ever, "employment", [2, 3], by="Gender")[1]


@report.finding("X20")
def gap_unemployed_or_out():
    return gap(ever, "employment", [2, 3])


# --- Chapter 1: A Changed World? -------------------------------------------------


@report.finding("C1_1")
def climate_threat():
    return by_sex(d, "WP20719", {"very": [1], "somewhat": [2], "not": [3], "dk": DK})


@report.finding("X21")
def gap_climate_not_a_threat():
    return gap(d, "WP20719", [3], higher="men")


@report.finding("C1_2")
def safer_than_five_years_ago():
    return by_sex(d, "WP20711", {"more": [1], "less": [2], "same": [3]})


@report.finding("X22")
def gap_more_safe():
    return gap(d, "WP20711", [1], higher="men")


@report.finding("X23")
def gap_less_safe():
    return gap(d, "WP20711", [2])


@report.finding("X24")
def gap_top_risk_crime():
    return gap(d, "WP22331", [3])


@report.finding("X25")
def gap_top_risk_road():
    return gap(d, "WP22331", [1], higher="men")


TOP_OF_MIND = {  # WP22331 codes shown in Table 1.1
    "road": [1], "other_transport": [2], "crime": [3], "war": [4], "health": [5], "covid": [7],
    "mental_stress": [8], "financial": [9], "economy": [10], "politics": [11], "technology": [12],
    "water": [13], "hunger": [15], "household": [16], "work": [17], "pollution": [18],
    "climate": [19], "disasters": [20],
}


@report.finding("T1_1")
def top_of_mind_risk():
    return by_sex(d, "WP22331", TOP_OF_MIND)


# Chart 1.3: worry item and experience item for each of the seven risks.
RISKS = {
    "food": ("WP20720", "WP22442"), "water": ("WP20721", "WP22443"),
    "crime": ("WP20722", "WP22444"), "weather": ("WP20723", "WP22445"),
    "traffic": ("WP22213", "WP22446"), "mental": ("WP20726", "WP22447"),
    "work": ("WP22214", "WP22448"),
}
EXPERIENCE = {"exp_personal": [1], "exp_know": [2], "exp_no": [4]}


@report.finding("C1_3")
def worry_and_experience():
    out = {}
    for risk, (worry, experience) in RISKS.items():
        for key, value in {**by_sex(d, worry, WORRY), **by_sex(d, experience, EXPERIENCE)}.items():
            sex, category = key.split("_", 1)
            out[f"{sex}_{risk}_{category}"] = value
    return out


@report.finding("X26")
def gaps_very_worried():
    return {risk: gap(d, worry, [1], higher="men" if risk == "work" else "women")
            for risk, (worry, _) in RISKS.items()}


@report.finding("X27")
def gaps_personal_experience():
    return {risk: gap(d, RISKS[risk][1], [1], higher="men") for risk in ("traffic", "work")}


# --- Chapter 2: A Resilient World? ---------------------------------------------


@report.finding("C2_1")
def resilience_index():
    r = wmean(d, "resilience_index", by="Gender")
    return {sex: r[code] for code, sex in SEX.items()}


@report.finding("C2_2")
def basic_needs():
    return by_sex(d, "basic_needs", {
        "lt_week": [1], "weeks_1_2": [2], "weeks_2_4": [3], "around_month": [5], "months_2": [6],
        "months_3": [7], "months_4plus": [8], "dk": [98], "month_or_less": [1, 2, 3, 4, 5],
    })


@report.finding("C2_3")
def experienced_disaster():
    return by_sex(d, "WP22245", YES_NO)


@report.finding("X28")
def gap_experienced_disaster():
    return gap(d, "WP22245", [1], higher="men")


PREPARED = {"national": "WP22241", "local": "WP22244", "hospitals": "WP22242", "family": "WP22243"}


@report.finding("C2_4")
def well_prepared():
    out = {}
    for who, var in PREPARED.items():
        for key, value in by_sex(d, var, YES_NO).items():
            sex, answer = key.split("_")
            out[f"{sex}_{who}_{answer}"] = value
    return out


@report.finding("X29")
def gaps_well_prepared():
    return {who: gap(d, var, [1], higher="men") for who, var in PREPARED.items()}


TRUST_MOST = {
    "weather_service": [1], "disaster_agency": [2], "local_news": [3], "religious": [4], "famous": [5],
    "emergency": [6], "internet": [7], "none": [8], "other": [9], "dk": DK,
}


@report.finding("T2_1")
def trust_most_disaster_information():
    return by_sex(d, "WP22240", TRUST_MOST)


@report.finding("X30")
def gaps_trust_most():
    return {
        "local_news": gap(d, "WP22240", [3]),
        "weather_service": gap(d, "WP22240", [1], higher="men"),
        "disaster_agency": gap(d, "WP22240", [2], higher="men"),
        "internet": gap(d, "WP22240", [7], higher="men"),
    }


@report.finding("C2_5")
def could_protect():
    return by_sex(d, "WP22252", {"yes": [1], "no": [2], "depends": [3], "dk": DK})


@report.finding("X31")
def gap_could_protect():
    return gap(d, "WP22252", [1], higher="men")


@report.finding("C2_6")
def disaster_plan():
    return by_sex(d, "WP22253", YES_NO)


@report.finding("X32")
def gap_disaster_plan():
    return gap(d, "WP22253", [1], higher="men")


VITAL_SERVICES = {"electricity": "WP22254", "water": "WP22255", "food": "WP22256",
                  "medical": "WP22257", "telephone": "WP22258"}


@report.finding("C2_7")
def lost_vital_services():
    out = {}
    for service, var in VITAL_SERVICES.items():
        for key, value in by_sex(d, var, YES_NO).items():
            sex, answer = key.split("_")
            out[f"{sex}_{service}_{answer}"] = value
    return out


@report.finding("X33")
def gaps_lost_vital_services():
    return {service: gap(d, VITAL_SERVICES[service], [1]) for service in ("food", "water", "medical")}


@report.finding("C2_8")
def any_discrimination():
    return by_sex(d, "any_discrimination", YES_NO)


@report.finding("X34")
def gap_any_discrimination():
    return gap(d, "any_discrimination", [1], higher="men")


DISCRIMINATION_TYPES = dict(zip(["skin", "religion", "nationality", "gender", "disability"], DISCRIMINATION))


@report.finding("C2_9")
def discrimination_by_type():
    out = {}
    for kind, var in DISCRIMINATION_TYPES.items():
        answers = {"yes": [1], "no": [2], "na": [97]} if kind == "disability" else YES_NO
        for key, value in by_sex(d, var, answers).items():
            sex, answer = key.split("_")
            out[f"{sex}_{kind}_{answer}"] = value
    return out


@report.finding("X35")
def gaps_discrimination_by_type():
    return {kind: gap(d, var, [1], higher="women" if kind in ("gender", "disability") else "men")
            for kind, var in DISCRIMINATION_TYPES.items()}


# --- Chapter 3: A Digital World --------------------------------------------------


@report.finding("C3_1")
def used_internet():
    return by_sex(d, "WP22222", YES_NO)


@report.finding("X36")
def gap_used_internet():
    return gap(d, "WP22222", [1], higher="men")


@report.finding("C3_2")
def worry_data_stolen():
    return by_sex(d, "WP22223", WORRY)


@report.finding("X37")
def gaps_worry_data_stolen():
    return {"very": gap(d, "WP22223", [1]), "somewhat": gap(d, "WP22223", [2])}


@report.finding("C3_3")
def worry_data_companies():
    return by_sex(d, "WP22225", WORRY)


@report.finding("X38")
def gaps_worry_data_companies():
    return {"very": gap(d, "WP22225", [1]), "somewhat": gap(d, "WP22225", [2])}


@report.finding("C3_4")
def worry_data_government():
    return by_sex(d, "WP22224", WORRY)


@report.finding("X39")
def gaps_worry_data_government():
    return {"somewhat": gap(d, "WP22224", [2]), "very": gap(d, "WP22224", [1])}


@report.finding("C3_5")
def driverless_car():
    return by_sex(d, "WP22226", {"yes": [1], "no": [2], "dk": DK})


@report.finding("X40")
def gap_driverless_car():
    return gap(d, "WP22226", [1], higher="men")


@report.finding("C3_6")
def artificial_intelligence():
    return by_sex(d, "WP22227", {"help": [1], "harm": [2], "no_opinion": [3], "dk": DK})


@report.finding("X41")
def gaps_artificial_intelligence():
    return {"help": gap(d, "WP22227", [1], higher="men"), "harm": gap(d, "WP22227", [2]),
            "no_opinion": gap(d, "WP22227", [3])}


# --- Chapter 4: Safe at Work? ------------------------------------------------------


@report.finding("C4_1")
def ever_worked():
    return by_sex(d, "never_worked", {"worked": [2], "never": [1]})


@report.finding("X42")
def gap_never_worked():
    return gap(d, "never_worked", [1])


@report.finding("C4_2")
def employment_status():
    status = by_sex(ever, "employment", {"employed": [1], "unemployed": [2], "out": [3]})
    kind = by_sex(ever, "employment_type",
                  {"ex_full_time": [1], "ex_part_time": [2], "ex_self": [3], "ex_unemployed": [4]})
    return {**status, **kind}


@report.finding("X43")
def gaps_employment():
    return {
        "out": gap(ever, "employment", [3]),
        "part_time": gap(ever, "employment_type", [2]),
        "full_time": gap(ever, "employment_type", [1], higher="men"),
        "self": gap(ever, "employment_type", [3], higher="men"),
    }


@report.finding("C4_3")
def number_of_forms():
    return by_sex(ever, "n_forms", {"none": [0], "one": [1], "two": [2]})


@report.finding("X44")
def gap_any_violence_harassment():
    return gap(ever, "n_forms", [1, 2, 3], higher="men")


@report.finding("C4_4")
def combinations():
    return by_sex(anyvh, "combination", {
        "physical": [1], "psych": [2], "sexual": [3], "psych_physical": [4],
        "sexual_psych": [5], "sexual_physical": [6], "all_three": [7],
    })


@report.finding("X45")
def sexual_element():
    r = pct(anyvh, "sexual_element", [1], by="Gender")
    return {sex: r[code] for code, sex in SEX.items()}


FREQUENCY = {"once_twice": [1], "three_five": [2], "more_five": [3]}
KINDS = {"C4_5": ("WP22400_ALL", "WP22401"), "C4_6": ("WP22403_ALL", "WP22404_ALL"),
         "C4_7": ("WP22406_ALL", "WP22407_ALL")}


def ever_and_frequency(chart):
    ever_var, times_var = KINDS[chart]
    return {**by_sex(ever, ever_var, YES_NO), **by_sex(d, times_var, FREQUENCY)}


@report.finding("C4_5")
def physical():
    return ever_and_frequency("C4_5")


@report.finding("C4_6")
def psychological():
    return ever_and_frequency("C4_6")


@report.finding("C4_7")
def sexual():
    return ever_and_frequency("C4_7")


@report.finding("X46")
def gap_physical():
    return gap(ever, "WP22400_ALL", [1], higher="men")


@report.finding("X47")
def gap_physical_three_plus():
    return gap(d, "WP22401", [2, 3])


@report.finding("X48")
def gap_psychological():
    return gap(ever, "WP22403_ALL", [1], higher="men")


@report.finding("X49")
def gap_psychological_three_plus():
    return gap(d, "WP22404_ALL", [2, 3], higher="men")


@report.finding("X50")
def gap_sexual():
    return gap(ever, "WP22406_ALL", [1])


@report.finding("X51")
def gap_sexual_three_plus():
    return gap(d, "WP22407_ALL", [2, 3])


@report.finding("C4_8")
def told_anyone():
    return by_sex(d, "WP22409", YES_NO)


@report.finding("X52")
def gap_told_anyone():
    return gap(d, "WP22409", [1])


WHOM_TOLD = {"employer": "WP22410", "union": "WP22413", "coworker": "WP22411",
             "police": "WP22421", "family": "WP22412", "social": "WP22414"}


@report.finding("C4_9")
def whom_told():
    out = {}
    for who, var in WHOM_TOLD.items():
        for key, value in by_sex(d, var, YES_NO).items():
            sex, answer = key.split("_")
            out[f"{sex}_{who}_{answer}"] = value
    return out


@report.finding("X53")
def gaps_whom_told():
    return {who: gap(d, WHOM_TOLD[who], [1], higher="women" if who == "family" else "men")
            for who in ("family", "employer", "coworker", "union", "police")}


REASONS = {"waste": "WP22415", "not_know": "WP22416", "procedures": "WP22417", "find_out": "WP22418",
           "punishment": "WP22419", "reputation": "WP22420", "trust": "WP22422"}


@report.finding("C4_10")
def reasons_not_told():
    out = {}
    for reason, var in REASONS.items():
        for key, value in by_sex(d, var, YES_NO).items():
            sex, answer = key.split("_")
            out[f"{sex}_{reason}_{answer}"] = value
    return out


@report.finding("X54")
def gaps_reasons_not_told():
    return {reason: gap(d, REASONS[reason], [1], higher="men" if reason in ("waste", "trust") else "women")
            for reason in ("not_know", "find_out", "punishment", "waste", "trust")}


if __name__ == "__main__":
    sys.exit(report.run())
