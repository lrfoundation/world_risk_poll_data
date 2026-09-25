"""Reproduce World Risk Poll 2024 Report: Engineering safer workplaces (2023 data).

Run from the repository root:
    python reports/WRP_2023/core_engineering_safer_workplaces/reproduce.py

Almost every figure is among the current workforce (EMP_2010 codes 1-5).
Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import REPO_ROOT, Report, distribution, load_wave, pct  # noqa: E402

report = Report(__file__)

EXTERNAL = REPO_ROOT / "reports" / "external"
GDP_FILE = EXTERNAL / "core_engineering_safer_workplaces__worldbank_NY.GDP.PCAP.CD.csv"
MODE_FILE = EXTERNAL / "core_engineering_safer_workplaces__wrp_interview_mode.csv"

REGION = {1: "eastern_africa", 2: "central_western_africa", 3: "northern_africa", 4: "southern_africa",
          5: "latin_america", 6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia",
          10: "southern_asia", 11: "middle_east", 12: "eastern_europe", 13: "northern_western_europe",
          14: "southern_europe", 15: "anz"}
RCODE = {v: k for k, v in REGION.items()}
INCOME = {1: "low", 2: "lower_middle", 3: "upper_middle", 4: "high"}
SECTOR = {1: "agriculture", 2: "fishing", 3: "manufacturing", 4: "construction", 5: "mining",
          6: "electricity", 7: "market_services", 8: "non_market_services"}  # WP23340
SCODE = {v: k for k, v in SECTOR.items()}
SECTOR5 = ["construction", "agriculture", "market_services", "non_market_services", "manufacturing"]
TRAIN = {1: "past2", 2: "older", 3: "never"}
HARMED = [1, 3]  # WP22448: 1 = yes, personally; 3 = both (personally and know someone)
WORRIED = [1, 2]  # very or somewhat worried

d = load_wave(2023, [
    "WPID_RANDOM", "PROJWT", "Country", "COUNTRY_ISO3", "GlobalRegion", "CountryIncomeLevel",
    "Gender", "Age", "AgeGroups4", "Education", "EMP_2010", "INCOME_5", "REGION2_IND",
    "WP20720", "WP20721", "WP20722", "WP20723", "WP22213", "WP20726", "WP22214",
    "WP22442", "WP22443", "WP22444", "WP22445", "WP22446", "WP22447", "WP22448",
    "WP22228", "WP22229", "WP23335", "WP23336", "WP23337", "WP23338", "WP23340",
])
d21 = load_wave(2021, ["PROJWT", "Country", "COUNTRY_ISO3", "GlobalRegion", "EMP_2010", "WP22214", "WP22448"])
d19 = load_wave(2019, ["PROJWT", "COUNTRY_ISO3", "EMP_2010", "L19"])

# --- Derived variables ---------------------------------------------------------

# Current workforce: employed full- or part-time, self-employed or unemployed
# (EMP_2010 1-5); everyone out of the workforce (6) is excluded.
WORKFORCE = [1, 2, 3, 4, 5]

# Employment type (Charts 2.9, 3.2): part-time merges codes 3 and 5.
d["emptype"] = d.EMP_2010.map({1: 1, 2: 2, 3: 3, 5: 3, 4: 4})  # FT employer / FT self / PT / unemployed

# Financial resilience (Chart 2.8): how long the household could cover basic
# needs without income. Less than a week; one to four weeks; a month or more.
d["fin_res"] = np.select([d.WP22229.eq(1), d.WP22229.isin([2, 3]), d.WP22228.eq(2)], [1, 2, 3], default=np.nan)

# OSH training (Chapter 4): 1 = trained in the past two years; 2 = trained, but
# not in the past two years or not sure when (includes those with training who
# were not asked the follow-up); 3 = never; 9 = DK/refused (kept in the base).
d["train"] = np.select([d.WP23338.eq(1), d.WP23337.eq(1), d.WP23337.eq(2), d.WP23337.isin([98, 99])],
                       [1, 2, 3, 9], default=np.nan)

wf = d[d.EMP_2010.isin(WORKFORCE)].copy()
harmed = wf[wf.WP22448.isin(HARMED)].copy()  # base for reporting (WP23335)

# 2021 trend figures use each country's 2023 region and income group
# (Iran moves from Middle East to Southern Asia; seven countries change
# income group). Jamaica, surveyed only in 2021, keeps its 2021 region and
# has no 2023 income group.
first = d.groupby("COUNTRY_ISO3")[["GlobalRegion", "CountryIncomeLevel"]].first()
d21["region23"] = d21.COUNTRY_ISO3.map(first.GlobalRegion).fillna(d21.GlobalRegion)
d21["income23"] = d21.COUNTRY_ISO3.map(first.CountryIncomeLevel)
wf21 = d21[d21.EMP_2010.isin(WORKFORCE)].copy()

# 2019 asked "Have you ever been seriously injured while working?" (L19) of the employed.
wf19 = d19[d19.EMP_2010.isin(WORKFORCE)].copy()

# --- Helpers -------------------------------------------------------------------


def harm(df, by=None):
    """% personally harmed at work in the past two years (yes, personally, or both)."""
    return pct(df, "WP22448", HARMED, by=by)


def reported(df, by=None):
    """% of the harmed who told someone responsible for safety or health (WP23335 = yes)."""
    return pct(df, "WP23335", [1], by=by)


def named(series, names):
    """Rename a by-group Series with a code -> key mapping, keeping mapped groups only."""
    return {names[k]: v for k, v in series.items() if k in names}


def train_table(df, by):
    """% trained in the past two years / longer ago / never, by group: {<group>_<category>: %}."""
    table = distribution(df, "train", by=by)
    return {(g, TRAIN[c]): table.loc[g, c] for g in table.index for c in TRAIN if c in table.columns}


def country_change():
    """Harm among the current workforce by country in 2021 and 2023 (countries asked in both)."""
    t = pd.DataFrame({"r21": harm(wf21, "COUNTRY_ISO3"), "r23": harm(wf, "COUNTRY_ISO3")}).dropna()
    t["diff"] = t.r23 - t.r21
    return t


def interview_mode():
    """Survey mode by country from the WRP 2021 and 2023 methodology documents (external snapshot)."""
    return pd.read_csv(MODE_FILE).set_index("COUNTRY_ISO3")


# --- Executive summary -------------------------------------------------------------


@report.finding("X01")
def interviews():
    return len(d)


@report.finding("X02")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X03")
def harm_global():
    return harm(wf)


@report.finding("X04")
def harm_millions():
    # PROJWT sums to the adult (15+) population, so the weighted count of the
    # harmed current workforce estimates the number of people.
    return wf.loc[wf.WP22448.isin(HARMED), "PROJWT"].sum() / 1e6


@report.finding("X05")
def harm_low_income():
    return {k: harm(wf, "CountryIncomeLevel")[c] for c, k in ((1, "low"), (2, "lower_middle"))}


@report.finding("X06")
def reported_global():
    return reported(harmed)


@report.finding("X07")
def never_trained():
    return pct(wf, "train", [3])


@report.finding("X08")
def never_trained_income():
    r = pct(wf, "train", [3], by="CountryIncomeLevel")
    return {"lower_middle": r[2], "low": r[1]}


@report.finding("X09")
def trained_by_employment():
    r = pct(wf, "train", [1], by="emptype")
    return {"ft_employer": r[1], "part_time": r[3]}


@report.finding("X10")
def agriculture_training():
    ag = wf[wf.WP23340 == SCODE["agriculture"]]
    return {"never": pct(ag, "train", [3]), "past2": pct(ag, "train", [1])}


@report.finding("X11")
def fishing_never_trained():
    return pct(wf[wf.WP23340 == SCODE["fishing"]], "train", [3])


EXPOSURE = {4: "not_harmed", 2: "know_someone", 1: "personally", 3: "both"}  # WP22448 codes


@report.finding("X12")
def worry_by_exposure():
    # The worry-about-work question (WP22214) was asked only of the employed.
    return named(pct(wf, "WP22214", WORRIED, by="WP22448"), EXPOSURE)


# Chart 4.7 / X13 model: logistic regression of reporting harm (WP23335 yes vs
# no; not applicable, DK and refused dropped) among the current workforce
# harmed in the past two years, on training (never = reference), sex, age
# (years), education, job sector (WP23340, all codes) and log GDP per capita
# (current US$, 2023, World Bank). Unweighted. Rows missing age or GDP (Taiwan,
# Yemen) are dropped.
MODEL = ("reported ~ C(train, Treatment(3)) + C(Gender) + Age + C(Education) + C(WP23340) + np.log(gdp)")


def odds_ratios():
    gdp = pd.read_csv(GDP_FILE)
    gdp = gdp[(gdp.indicator == "NY.GDP.PCAP.CD") & (gdp.year == 2023)].set_index("iso3")["value"]
    m = harmed[harmed.WP23335.isin([1, 2]) & harmed.train.isin([1, 2, 3])].copy()
    m["reported"] = (m.WP23335 == 1).astype(int)
    m["gdp"] = m.COUNTRY_ISO3.map(gdp)
    m = m.dropna(subset=["Age", "gdp"])
    fit = smf.glm(MODEL, m, family=sm.families.Binomial()).fit()
    return {"past2": np.exp(fit.params["C(train, Treatment(3))[T.1.0]"]),
            "older": np.exp(fit.params["C(train, Treatment(3))[T.2.0]"])}


report.finding("X13")(odds_ratios)

# --- Chapter 2: Workplace harm ------------------------------------------------------


@report.finding("X14")
def harm_2021():
    return {"adults": harm(d21), "workforce": harm(wf21)}


@report.finding("X15")
def countries_2021():
    return d21.COUNTRY_ISO3.nunique()


@report.finding("X16")
def injured_2019():
    return pct(wf19, "L19", [1])


@report.finding("X17")
def harm_adults_2023():
    return harm(d)


@report.finding("X18")
def out_of_workforce():
    return pct(d, "EMP_2010", [6])


@report.finding("X19")
def harm_incl_recent_workers():
    # Adds those out of the workforce who last worked within the past two years (WP23336 = 1).
    return harm(d[d.EMP_2010.isin(WORKFORCE) | (d.EMP_2010.eq(6) & d.WP23336.eq(1))])


@report.finding("C2_1")
def harm_trend():
    return {"2019": pct(wf19, "L19", [1]), "2021": harm(wf21), "2023": harm(wf)}


def mode_groups():
    t = country_change().join(interview_mode())
    changed = t[(t.mode_2021 == "TEL") & (t.mode_2023 == "F2F")]
    unchanged = t[t.mode_2021 == t.mode_2023]
    return changed, unchanged


@report.finding("X20")
def mode_changed_count():
    return len(mode_groups()[0])


@report.finding("X21")
def mode_changed_mean():
    return mode_groups()[0]["diff"].mean()


@report.finding("X22")
def mode_unchanged_count():
    return len(mode_groups()[1])


@report.finding("X23")
def mode_unchanged_mean():
    return mode_groups()[1]["diff"].mean()


def region_trend(region):
    return {"2023": harm(wf, "GlobalRegion")[RCODE[region]], "2021": harm(wf21, "region23")[RCODE[region]]}


@report.finding("X24")
def southern_asia_trend():
    return region_trend("southern_asia")


@report.finding("X25")
def southern_europe_trend():
    return region_trend("southern_europe")


@report.finding("X26")
def italy_trend():
    return {"2023": harm(wf, "COUNTRY_ISO3")["ITA"], "2021": harm(wf21, "COUNTRY_ISO3")["ITA"],
            "2019": pct(wf19[wf19.COUNTRY_ISO3 == "ITA"], "L19", [1])}


@report.finding("X27")
def smallest_regional_decrease():
    r23, r21 = harm(wf, "GlobalRegion"), harm(wf21, "region23")
    return min(r21[RCODE[k]] - r23[RCODE[k]] for k in ("northern_africa", "latin_america", "northern_western_europe"))


@report.finding("X28")
def harm_anz_northern_america():
    return {k: harm(wf, "GlobalRegion")[RCODE[k]] for k in ("anz", "northern_america")}


@report.finding("X29")
def harm_eastern_asia():
    return harm(wf, "GlobalRegion")[RCODE["eastern_asia"]]


@report.finding("X30")
def harm_cw_africa_se_asia():
    return {k: harm(wf, "GlobalRegion")[RCODE[k]] for k in ("central_western_africa", "southeastern_asia")}


@report.finding("X31")
def harm_eastern_asia_countries():
    r = harm(wf, "COUNTRY_ISO3")
    return {iso: r[iso] for iso in ("CHN", "TWN", "JPN", "MNG", "HKG", "KOR")}


@report.finding("C2_2")
def harm_by_region():
    out = {}
    for code, key in REGION.items():
        out[f"{key}_2021"] = harm(wf21, "region23")[code]
        out[f"{key}_2023"] = harm(wf, "GlobalRegion")[code]
    return out


@report.finding("X32")
def income_fall():
    r23, r21 = harm(wf, "CountryIncomeLevel"), harm(wf21, "income23")
    return {"low": r21[1] - r23[1], "lower_middle": r21[2] - r23[2]}


@report.finding("X33")
def countries_changed_10_points():
    return int((country_change()["diff"].abs() >= 10).sum())


@report.finding("C2_3")
def harm_by_income():
    out = {}
    for code, key in INCOME.items():
        out[f"{key}_2021"] = harm(wf21, "income23")[code]
        out[f"{key}_2023"] = harm(wf, "CountryIncomeLevel")[code]
    return out


@report.finding("T2_1")
def countries_with_large_changes():
    t = country_change()
    t = t[t["diff"].abs() >= 10]
    return {f"{iso}_{col}": t.loc[iso, src] for iso in t.index
            for col, src in (("2021", "r21"), ("2023", "r23"), ("diff", "diff"))}


AFRICA_LABELLED = ["MAR", "DZA", "LBY", "EGY", "MRT", "MLI", "NER", "TCD", "NGA", "SLE", "LBR", "GHA",
                   "ETH", "SOM", "KEN", "COD", "UGA", "TZA", "COM", "MDG", "NAM", "ZAF"]


@report.finding("C2_4")
def harm_africa():
    africa = wf[wf.GlobalRegion.isin([1, 2, 3, 4])]
    r = harm(africa, "COUNTRY_ISO3")
    out = {iso: r[iso] for iso in AFRICA_LABELLED}
    out["legend_max"], out["legend_min"] = r.max(), r.min()
    return out


def country_names():
    return d.groupby("COUNTRY_ISO3").Country.first()


@report.finding("X34")
def highest_country():
    return country_names()[harm(wf, "COUNTRY_ISO3").idxmax()]


@report.finding("X35")
def sierra_leone():
    return {"2023": harm(wf, "COUNTRY_ISO3")["SLE"], "2021": harm(wf21, "COUNTRY_ISO3")["SLE"]}


@report.finding("X36")
def largest_increase():
    return country_names()[country_change()["diff"].idxmax()]


@report.finding("X37")
def high_harm_africa():
    r = harm(wf, "COUNTRY_ISO3")
    return {iso: r[iso] for iso in ("SOM", "TCD", "COM", "COD", "LBR", "UGA")}


@report.finding("X38")
def worry_work_trend():
    return {"2023": pct(wf, "WP22214", WORRIED), "2021": pct(wf21, "WP22214", WORRIED)}


@report.finding("X39")
def worry_top_regions():
    r = pct(wf, "WP22214", WORRIED, by="GlobalRegion")
    return {k: r[RCODE[k]] for k in ("southern_asia", "central_western_africa")}


@report.finding("X40")
def india_rank():
    r = harm(wf, "COUNTRY_ISO3").sort_values(ascending=False)
    return list(r.index).index("IND") + 1


@report.finding("X41")
def india_trend():
    return {"2023": harm(wf, "COUNTRY_ISO3")["IND"], "2021": harm(wf21, "COUNTRY_ISO3")["IND"]}


@report.finding("X42")
def india_regions():
    r = harm(wf[wf.COUNTRY_ISO3 == "IND"], "REGION2_IND")  # 1 central, 2 east, 3 west, 4 north, 5 south
    return named(r, {4: "north", 1: "central", 2: "east", 3: "west", 5: "south"})


@report.finding("C2_5")
def harm_and_worry_by_region():
    h = harm(wf, "GlobalRegion")
    w = pct(wf, "WP22214", WORRIED, by="GlobalRegion")
    return {**{f"{k}_harm": h[c] for c, k in REGION.items()}, **{f"{k}_worry": w[c] for c, k in REGION.items()}}


@report.finding("C2_6")
def worry_by_exposure_chart():
    return named(pct(wf, "WP22214", WORRIED, by="WP22448"), EXPOSURE)


RISKS = {"food": ("WP20720", "WP22442"), "water": ("WP20721", "WP22443"), "crime": ("WP20722", "WP22444"),
         "weather": ("WP20723", "WP22445"), "traffic": ("WP22213", "WP22446"),
         "mental_health": ("WP20726", "WP22447"), "work": ("WP22214", "WP22448")}


@report.finding("X43")
def worry_other_risks():
    return {k: pct(wf, RISKS[k][0], WORRIED) for k in ("traffic", "weather", "work", "water")}


@report.finding("C2_7")
def worry_vs_experience():
    # Scatter with no printed values: % worried and % personally harmed for each risk.
    out = {}
    for risk, (worry, experience) in RISKS.items():
        out[f"{risk}_worry"] = pct(wf, worry, WORRIED)
        out[f"{risk}_experience"] = pct(wf, experience, HARMED)
    return out


@report.finding("X44")
def harm_by_sex():
    r = harm(wf, "Gender")
    return {"men": r[1], "women": r[2]}


FIN_RES = {1: "less_week", 2: "week_month", 3: "month_plus"}


@report.finding("X45")
def harm_by_financial_resilience():
    return named(harm(wf, "fin_res"), FIN_RES)


@report.finding("C2_8")
def harm_by_demographics():
    out = {"global": harm(wf)}
    out.update(named(harm(wf, "Gender"), {1: "men", 2: "women"}))
    out.update(named(harm(wf, "AgeGroups4"), {1: "age_15_29", 2: "age_30_49", 3: "age_50_64", 4: "age_65plus"}))
    out.update(named(harm(wf, "Education"), {1: "primary", 2: "secondary", 3: "tertiary"}))
    out.update(named(harm(wf, "fin_res"), FIN_RES))
    return out


EMPTYPE = {1: "ft_employer", 2: "ft_self", 3: "part_time", 4: "unemployed"}


@report.finding("X46")
def harm_by_employment_text():
    return named(harm(wf, "emptype"), EMPTYPE)


@report.finding("C2_9")
def harm_by_employment():
    return named(harm(wf, "emptype"), EMPTYPE)


@report.finding("X47")
def harm_by_sector_text():
    r = harm(wf, "WP23340")
    return {k: r[SCODE[k]] for k in ("fishing", "construction", "mining", "market_services", "non_market_services")}


@report.finding("C2_10")
def harm_by_sector():
    return {"global": harm(wf), **named(harm(wf, "WP23340"), SECTOR)}


@report.finding("C2_11")
def sector_profile():
    # Scatter with no printed values: harm rate against the share of each
    # sector's workforce that is male, has primary education only, or could
    # cover basic needs for less than a week.
    out = {}
    for code, key in SECTOR.items():
        s = wf[wf.WP23340 == code]
        out[f"{key}_harm"] = harm(s)
        out[f"{key}_men"] = pct(s, "Gender", [1])
        out[f"{key}_primary"] = pct(s, "Education", [1])
        out[f"{key}_less_week"] = pct(s.assign(lw=s.WP22229.eq(1).astype(float)), "lw", [1])
    return out


def harm_sector_by(by, names):
    r = harm(wf, ["WP23340", by])
    return {f"{SECTOR[s]}_{names[g]}": v for (s, g), v in r.items() if s in SECTOR and g in names}


@report.finding("X48")
def services_by_sex():
    r = harm_sector_by("Gender", {1: "men", 2: "women"})
    return {k: r[k] for k in ("market_services_men", "market_services_women",
                              "non_market_services_men", "non_market_services_women")}


@report.finding("X49")
def sector_by_age():
    r = harm_sector_by("AgeGroups4", {1: "15_29", 4: "65plus"})
    return {k: r[k] for k in ("construction_15_29", "construction_65plus", "agriculture_15_29", "agriculture_65plus")}


@report.finding("C2_12")
def harm_sector_sex():
    r = harm_sector_by("Gender", {1: "men", 2: "women"})
    return {k: r[k] for s in SECTOR5 for k in (f"{s}_women", f"{s}_men")}


@report.finding("C2_13")
def harm_sector_income():
    r = harm(wf, ["CountryIncomeLevel", "WP23340"])
    return {f"{INCOME[i]}_{SECTOR[s]}": v for (i, s), v in r.items()
            if i in INCOME and s in SECTOR and SECTOR[s] in SECTOR5}


# --- Chapter 3: Reporting workplace harm ---------------------------------------------


@report.finding("C3_1")
def harm_and_reporting_by_region():
    # Scatter with no printed values.
    h, r = harm(wf, "GlobalRegion"), reported(harmed, "GlobalRegion")
    return {**{f"{k}_harm": h[c] for c, k in REGION.items()}, **{f"{k}_reported": r[c] for c, k in REGION.items()}}


@report.finding("X50")
def reporting_by_region():
    r = reported(harmed, "GlobalRegion")
    keys = ["anz", "northern_america", "northern_western_europe", "southeastern_asia", "central_western_africa",
            "southern_africa", "southern_asia", "northern_africa", "central_asia"]
    return {k: r[RCODE[k]] for k in keys}


@report.finding("X51")
def reporting_by_sex():
    return named(reported(harmed, "Gender"), {1: "men", 2: "women"})


@report.finding("X52")
def reporting_by_education():
    return named(reported(harmed, "Education"), {1: "primary", 2: "secondary", 3: "tertiary"})


@report.finding("X53")
def reporting_by_income_quintile():
    r = reported(harmed, "INCOME_5")
    return {"min": r.min(), "max": r.max()}


@report.finding("X54")
def reporting_by_age():
    return named(reported(harmed, "AgeGroups4"), {3: "age_50_64", 1: "age_15_29", 2: "age_30_49"})


@report.finding("X55")
def reporting_region_sex():
    r = reported(harmed, ["GlobalRegion", "Gender"])
    sexes = {1: "men", 2: "women"}
    return {f"{reg}_{sexes[s]}": r[(RCODE[reg], s)]
            for reg in ("northern_western_europe", "middle_east", "eastern_europe") for s in (2, 1)}


@report.finding("X56")
def reporting_region_age():
    r = reported(harmed, ["GlobalRegion", "AgeGroups4"])
    ages = {1: "15_29", 2: "30_49"}
    return {f"{reg}_{ages[a]}": r[(RCODE[reg], a)]
            for reg in ("northern_western_europe", "southern_asia", "southern_europe", "eastern_europe") for a in (1, 2)}


REP_EMP = {1: "ft_employer", 3: "part_time", 2: "self_employed"}


@report.finding("X57")
def reporting_by_employment_text():
    return named(reported(harmed, "emptype"), REP_EMP)


@report.finding("C3_2")
def reporting_by_employment():
    return named(reported(harmed, "emptype"), REP_EMP)


@report.finding("X58")
def reporting_by_sector():
    r = reported(harmed, "WP23340")
    return {k: r[SCODE[k]] for k in SECTOR5}


@report.finding("C3_3")
def harm_and_reporting_by_sector():
    # Scatter with no printed values (the five sectors with enough harmed respondents).
    h, r = harm(wf, "WP23340"), reported(harmed, "WP23340")
    return {**{f"{k}_harm": h[SCODE[k]] for k in SECTOR5}, **{f"{k}_reported": r[SCODE[k]] for k in SECTOR5}}


# --- Chapter 4: Occupational safety and health training -------------------------------


@report.finding("X59")
def ever_trained():
    return {"ever": pct(wf, "train", [1, 2]), "past2": pct(wf, "train", [1])}


@report.finding("C4_1")
def training_global():
    return named(distribution(wf, "train"), TRAIN)


@report.finding("X60")
def training_high_income():
    t = distribution(wf, "train", by="CountryIncomeLevel")
    return {"past2": t.loc[4, 1], "older": t.loc[4, 2]}


@report.finding("C4_2")
def training_by_income():
    return {f"{INCOME[g]}_{c}": v for (g, c), v in train_table(wf, "CountryIncomeLevel").items() if g in INCOME}


@report.finding("X61")
def ever_trained_top_regions():
    r = pct(wf, "train", [1, 2], by="GlobalRegion")
    return {k: r[RCODE[k]] for k in ("eastern_europe", "anz")}


@report.finding("C4_3")
def training_by_region():
    return {f"{REGION[g]}_{c}": v for (g, c), v in train_table(wf, "GlobalRegion").items()}


def training_by_country():
    return distribution(wf, "train", by="COUNTRY_ISO3")


@report.finding("X62")
def eastern_europe_in_top10():
    top = training_by_country()[1].sort_values(ascending=False).head(10).index
    region = d.groupby("COUNTRY_ISO3").GlobalRegion.first()
    return int((region[top] == RCODE["eastern_europe"]).sum())


@report.finding("X63")
def never_trained_lowest():
    never = training_by_country()[3]
    return {iso: never[iso] for iso in ("SEN", "MAR", "TGO", "CIV")}


@report.finding("T4_1")
def top_and_bottom_countries():
    t = training_by_country()
    top = t[1].sort_values(ascending=False).head(10)  # % trained in the past two years
    bottom = t[3].sort_values(ascending=False).head(10)  # % never trained
    return {**top.to_dict(), **bottom.to_dict()}


@report.finding("C4_4")
def training_by_income_and_education():
    quint = {1: "poorest", 2: "second", 3: "middle", 4: "fourth", 5: "richest"}
    edu = {1: "primary", 2: "secondary", 3: "tertiary"}
    out = {f"{quint[g]}_{c}": v for (g, c), v in train_table(wf, "INCOME_5").items() if g in quint}
    out.update({f"{edu[g]}_{c}": v for (g, c), v in train_table(wf, "Education").items() if g in edu})
    return out


@report.finding("C4_5")
def training_by_sector():
    return {f"{SECTOR[g]}_{c}": v for (g, c), v in train_table(wf, "WP23340").items() if g in SECTOR}


construction = wf[wf.WP23340 == SCODE["construction"]]


@report.finding("X64")
def construction_training_extremes():
    r = pct(construction, "train", [1], by="GlobalRegion")
    return {k: r[RCODE[k]] for k in ("anz", "northern_africa")}


@report.finding("X65")
def construction_harm_extremes():
    r = harm(construction, "GlobalRegion")
    return {k: r[RCODE[k]] for k in ("anz", "northern_africa")}


@report.finding("C4_6")
def construction_training_by_region():
    return {f"{REGION[g]}_{c}": v for (g, c), v in train_table(construction, "GlobalRegion").items()}


@report.finding("X66")
def harm_by_training():
    return named(harm(wf, "train"), TRAIN)


report.finding("C4_7")(odds_ratios)


if __name__ == "__main__":
    sys.exit(report.run())
