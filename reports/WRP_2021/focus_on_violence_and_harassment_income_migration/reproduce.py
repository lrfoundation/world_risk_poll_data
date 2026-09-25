"""Reproduce World Risk Poll 2021 Focus On: The impact of income and migration on
violence and harassment at work.

Run from the repository root:
    python reports/WRP_2021/focus_on_violence_and_harassment_income_migration/reproduce.py

The report compares foreign-born and native-born workers, and workers who feel
comfortable or find it difficult on their present income. Country of birth is a
Gallup World Poll item that is not in the public data (see README.md), so most
findings here are GALLUP_ONLY unless GALLUP_WP_PATH points to a file with it.
Each function below computes one chart or text statement listed in
published_figures.csv.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, distribution, load_wave, merge_gallup, pct  # noqa: E402

report = Report(__file__)

VH = ["WP22400_ALL", "WP22403_ALL", "WP22406_ALL"]  # physical, psychological, sexual V&H at work
REGIONS = {  # GlobalRegion code -> key
    1: "eastern_africa", 2: "central_western_africa", 3: "north_africa", 4: "southern_africa",
    5: "latin_america_caribbean", 6: "northern_america", 7: "central_asia", 8: "east_asia",
    9: "south_eastern_asia", 10: "south_asia", 11: "middle_east", 12: "eastern_europe",
    13: "northern_western_europe", 14: "southern_europe", 15: "australia_nz",
}
# Feelings about household income (footnote 5): living comfortably or getting by =
# comfortable; finding it difficult or very difficult = difficult; DK/refused = neither.
FIN = {1: "comfortable", 2: "comfortable", 3: "difficult", 4: "difficult"}
BIRTH = {1: "native", 2: "foreign"}  # GWP WP4657: 1 = born in this country, 2 = born in another country
SEX = {1: "men", 2: "women"}  # Gender: 1 = Male, 2 = Female
YES_NO = {"yes": [1], "no": [2]}
THREE_REGIONS = ["northern_america", "australia_nz", "northern_western_europe"]  # Charts 3-6

# Countries marked as having ratified ILO Convention 190 (in force or not yet in force)
# in the report's own table on page 13, as ISO3 codes.
C190_RATIFIED = [
    "ARG", "ECU", "FJI", "GRC", "ITA", "MUS", "NAM", "SOM", "ZAF", "GBR", "URY",  # in force
    "ALB", "ATG", "BHS", "BRB", "CAN", "CAF", "SLV", "IRL", "LSO", "MEX", "NGA",  # not yet in force
    "PAN", "PER", "SMR", "ESP",
]

d = load_wave(2021, [
    "WPID_RANDOM", "PROJWT", "Gender", "COUNTRY_ISO3", "GlobalRegion", "IncomeFeelings", *VH,
    "WP22409", "WP22415", "WP22416", "WP22417", "WP22419", "WP22420",
])

# --- Derived variables ---------------------------------------------------------

# Ever worked: not "respondent has never worked" (code 7) at any of the three
# V&H questions. Unlike the Risk and Gender report, this includes China, which
# was asked only the psychological and sexual questions: that is what
# reproduces East Asia in Chart 1 (23%; 18% without China).
d["never_worked"] = np.where(d[VH].eq(7).any(axis=1), 1, 2)
workers = d[d.never_worked == 2].copy()
workers["region"] = workers.GlobalRegion.map(REGIONS)
workers["fin"] = workers.IncomeFeelings.map(FIN)
workers["sex"] = workers.Gender.map(SEX)

# Any V&H: yes to at least one of the three forms (DK/refused count as no).
yes = workers[VH].eq(1)
workers["any_vh"] = np.where(yes.any(axis=1), 1, 2)
workers["n_forms"] = yes.sum(axis=1)

_cache = {}


def workers_by_birth():
    """Workers with a valid country of birth (footnote 4), labelled native/foreign.

    Needs the Gallup World Poll item "born in this country" (WP4657), which is
    not in the public release.
    """
    if "born" not in _cache:
        g = merge_gallup(workers, ["WP4657"])
        g = g[g.WP4657.isin([1, 2])].copy()
        g["born"] = g.WP4657.map(BIRTH)
        _cache["born"] = g
    return _cache["born"]


def told_base():
    """Workers with a valid country of birth who experienced V&H (asked WP22409)."""
    w = workers_by_birth()
    return w[w.any_vh == 1]


# --- Helpers -------------------------------------------------------------------


def _key(k):
    return "_".join(k) if isinstance(k, tuple) else k


def rate(df, var, codes, by):
    """Weighted % with `var` in `codes` for each group of the label column(s) `by`:
    {"northern_america_foreign": %, ...}."""
    cols = [by] if isinstance(by, str) else by
    df = df.dropna(subset=cols)
    return {_key(k): v for k, v in pct(df, var, codes, by=by).items()}


def shares(df, var, categories, by):
    """% in each named category of `var` for each group of `by`:
    {"<group>_<category>": %, ...}."""
    cols = [by] if isinstance(by, str) else by
    table = distribution(df.dropna(subset=cols), var, by=by)
    return {
        f"{_key(group)}_{name}": row[row.index.intersection(codes)].sum()
        for group, row in table.iterrows() for name, codes in categories.items()
    }


def only(values, prefixes):
    """Keep the keys that start with one of `prefixes` (e.g. the chart's regions)."""
    return {k: v for k, v in values.items() if k.startswith(tuple(prefixes))}


# --- Page 2: Introduction ---------------------------------------------------------


@report.finding("X01")
def all_workers_experienced():
    return pct(workers, "any_vh", [1])


@report.finding("X02")
def foreign_born_experienced_sidebar():
    return rate(workers_by_birth(), "any_vh", [1], "born")["foreign"]


# --- Page 3: Chart 1 --------------------------------------------------------------


@report.finding("C1")
def experience_by_region():
    return rate(workers, "any_vh", [1], "region")


@report.finding("X03")
def australia_nz():
    return rate(workers, "any_vh", [1], "region")["australia_nz"]


@report.finding("X04")
def northern_america():
    return rate(workers, "any_vh", [1], "region")["northern_america"]


@report.finding("X05")
def central_asia():
    return rate(workers, "any_vh", [1], "region")["central_asia"]


@report.finding("X06")
def south_eastern_asia():
    return rate(workers, "any_vh", [1], "region")["south_eastern_asia"]


# --- Page 4: Chart 2 --------------------------------------------------------------


def experience_by_birth():
    w = workers_by_birth()
    return {**rate(w, "any_vh", [1], "born"), **rate(w, "any_vh", [1], ["region", "born"])}


@report.finding("C2")
def gap_by_region():
    # The chart prints the size of the gap without its sign.
    r = experience_by_birth()
    out = {"global": abs(r["foreign"] - r["native"])}
    for region in REGIONS.values():
        out[region] = abs(r.get(f"{region}_foreign", np.nan) - r.get(f"{region}_native", np.nan))
    return out


@report.finding("X07")
def gap_east_asia():
    r = experience_by_birth()
    return r["east_asia_native"] - r["east_asia_foreign"]


@report.finding("X08")
def gap_eastern_europe():
    r = experience_by_birth()
    return r["eastern_europe_foreign"] - r["eastern_europe_native"]


@report.finding("X09")
def gap_global():
    r = experience_by_birth()
    return r["foreign"] - r["native"]


@report.finding("X10")
def native_global():
    return experience_by_birth()["native"]


@report.finding("X11")
def foreign_global():
    return experience_by_birth()["foreign"]


# --- Page 5: Charts 3 and 4 ----------------------------------------------------------


def told_by_birth():
    t = told_base()
    return {**rate(t, "WP22409", [1], "born"), **rate(t, "WP22409", [1], ["region", "born"])}


@report.finding("X12")
def told_native_global():
    return told_by_birth()["native"]


@report.finding("X13")
def told_foreign_global():
    return told_by_birth()["foreign"]


@report.finding("X14")
def told_gap_australia_nz():
    r = told_by_birth()
    return r["australia_nz_native"] - r["australia_nz_foreign"]


@report.finding("X15")
def told_gap_northern_america():
    r = told_by_birth()
    return r["northern_america_native"] - r["northern_america_foreign"]


@report.finding("X16")
def told_gap_northern_western_europe():
    r = told_by_birth()
    return r["northern_western_europe_native"] - r["northern_western_europe_foreign"]


@report.finding("C3")
def told_someone():
    return only(shares(told_base(), "WP22409", {"told": [1], "didnt": [2]}, ["region", "born"]), THREE_REGIONS)


REASONS = {"not_know": "WP22416", "procedures": "WP22417"}  # asked of those who did not tell anyone


def reasons_by_birth(reason):
    w = workers_by_birth()
    var = REASONS[reason]
    return {**rate(w, var, [1], "born"), **rate(w, var, [1], ["region", "born"])}


@report.finding("C4")
def reasons_not_told():
    out = {}
    for reason in REASONS:
        for key, value in only(reasons_by_birth(reason), THREE_REGIONS).items():
            out[f"{key}_{reason}"] = value
    return out


@report.finding("X17")
def not_know_foreign_northern_america():
    return reasons_by_birth("not_know")["northern_america_foreign"]


@report.finding("X18")
def not_know_gap_northern_america():
    r = reasons_by_birth("not_know")
    return r["northern_america_foreign"] - r["northern_america_native"]


@report.finding("X19")
def not_know_northern_america_vs_global():
    r = reasons_by_birth("not_know")
    return r["northern_america_foreign"] - r["foreign"]


@report.finding("X20")
def procedures_foreign_northern_america():
    return reasons_by_birth("procedures")["northern_america_foreign"]


@report.finding("X21")
def procedures_native_northern_america():
    return reasons_by_birth("procedures")["northern_america_native"]


@report.finding("X22")
def procedures_foreign_global():
    return reasons_by_birth("procedures")["foreign"]


# --- Pages 6-7: Charts 5 and 6 --------------------------------------------------------


@report.finding("X23")
def comfortable_global():
    return rate(workers, "any_vh", [1], "fin")["comfortable"]


@report.finding("X24")
def difficult_global():
    return rate(workers, "any_vh", [1], "fin")["difficult"]


@report.finding("X25")
def difficult_gap_global():
    r = rate(workers, "any_vh", [1], "fin")
    return r["difficult"] - r["comfortable"]


def experience_by_birth_fin():
    w = workers_by_birth()
    return {**rate(w, "any_vh", [1], ["born", "fin"]), **rate(w, "any_vh", [1], ["region", "born", "fin"])}


@report.finding("X26")
def foreign_comfortable_global():
    return experience_by_birth_fin()["foreign_comfortable"]


@report.finding("X27")
def foreign_difficult_global():
    return experience_by_birth_fin()["foreign_difficult"]


@report.finding("C5")
def experience_by_birth_and_income():
    return only(experience_by_birth_fin(), THREE_REGIONS)


@report.finding("X28")
def northern_america_foreign_difficult():
    return experience_by_birth_fin()["northern_america_foreign_difficult"]


@report.finding("X29")
def northern_america_difficult_gap_birth():
    r = experience_by_birth_fin()
    return r["northern_america_foreign_difficult"] - r["northern_america_native_difficult"]


@report.finding("X30")
def northern_america_foreign_gap_income():
    r = experience_by_birth_fin()
    return r["northern_america_foreign_difficult"] - r["northern_america_foreign_comfortable"]


@report.finding("X31")
def australia_nz_native_difficult():
    return experience_by_birth_fin()["australia_nz_native_difficult"]


@report.finding("X32")
def australia_nz_difficult_gap_birth():
    r = experience_by_birth_fin()
    return r["australia_nz_native_difficult"] - r["australia_nz_foreign_difficult"]


@report.finding("X33")
def australia_nz_native_gap_income():
    r = experience_by_birth_fin()
    return r["australia_nz_native_difficult"] - r["australia_nz_native_comfortable"]


@report.finding("X34")
def northern_western_europe_lowest():
    return min(only(experience_by_birth_fin(), ["northern_western_europe"]).values())


@report.finding("X35")
def northern_western_europe_highest():
    return max(only(experience_by_birth_fin(), ["northern_western_europe"]).values())


@report.finding("C6")
def told_by_birth_and_income():
    return only(rate(told_base(), "WP22409", [1], ["region", "born", "fin"]), THREE_REGIONS)


@report.finding("X36")
def told_northern_america_foreign_difficult():
    return rate(told_base(), "WP22409", [1], ["region", "born", "fin"])["northern_america_foreign_difficult"]


# --- Pages 9-12: South-eastern Asia and Latin America ------------------------------------


def region_by_birth(region):
    w = workers_by_birth()
    return w[w.region == region]


def experience_and_told(region):
    """Charts 7 and 9: experience (top) and told someone (bottom) by birth and income."""
    w = region_by_birth(region)
    exp = shares(w, "any_vh", YES_NO, ["born", "fin"])
    told = shares(w[w.any_vh == 1], "WP22409", YES_NO, ["born", "fin"])
    return {**{f"exp_{k}": v for k, v in exp.items()}, **{f"told_{k}": v for k, v in told.items()}}


def region_rates(region, var, codes, by):
    w = region_by_birth(region)
    if var == "WP22409":
        w = w[w.any_vh == 1]
    return rate(w, var, codes, by)


SEA, LAC = "south_eastern_asia", "latin_america_caribbean"


@report.finding("X37")
def south_eastern_asia_overall():
    return rate(workers, "any_vh", [1], "region")[SEA]


@report.finding("X38")
def sea_foreign_experienced():
    return region_rates(SEA, "any_vh", [1], "born")["foreign"]


@report.finding("X39")
def sea_native_experienced():
    return region_rates(SEA, "any_vh", [1], "born")["native"]


@report.finding("X40")
def sea_foreign_told():
    return region_rates(SEA, "WP22409", [1], "born")["foreign"]


@report.finding("X41")
def sea_native_told():
    return region_rates(SEA, "WP22409", [1], "born")["native"]


@report.finding("X42")
def sea_told_gap():
    r = region_rates(SEA, "WP22409", [1], "born")
    return r["foreign"] - r["native"]


@report.finding("C7")
def south_eastern_asia_chart():
    return experience_and_told(SEA)


@report.finding("X43")
def sea_foreign_difficult():
    return region_rates(SEA, "any_vh", [1], ["born", "fin"])["foreign_difficult"]


@report.finding("X44")
def sea_foreign_gap_income():
    r = region_rates(SEA, "any_vh", [1], ["born", "fin"])
    return r["foreign_difficult"] - r["foreign_comfortable"]


@report.finding("X45")
def sea_native_difficult():
    return region_rates(SEA, "any_vh", [1], ["born", "fin"])["native_difficult"]


@report.finding("X46")
def sea_native_comfortable():
    return region_rates(SEA, "any_vh", [1], ["born", "fin"])["native_comfortable"]


@report.finding("X47")
def sea_native_gap_income():
    r = region_rates(SEA, "any_vh", [1], ["born", "fin"])
    return r["native_difficult"] - r["native_comfortable"]


@report.finding("X48")
def sea_told_foreign_difficult():
    return region_rates(SEA, "WP22409", [1], ["born", "fin"])["foreign_difficult"]


@report.finding("X49")
def sea_told_foreign_comfortable():
    return region_rates(SEA, "WP22409", [1], ["born", "fin"])["foreign_comfortable"]


@report.finding("X50")
def sea_told_foreign_gap_income():
    r = region_rates(SEA, "WP22409", [1], ["born", "fin"])
    return r["foreign_difficult"] - r["foreign_comfortable"]


@report.finding("X51")
def sea_told_native_comfortable():
    return region_rates(SEA, "WP22409", [1], ["born", "fin"])["native_comfortable"]


SEA_REASONS = {"reputation": "WP22420", "waste": "WP22415"}


@report.finding("C8")
def sea_reasons():
    w = region_by_birth(SEA)
    return {f"{reason}_{k}": v for reason, var in SEA_REASONS.items()
            for k, v in shares(w, var, YES_NO, "born").items()}


@report.finding("X52")
def sea_reputation_native():
    return region_rates(SEA, "WP22420", [1], "born")["native"]


@report.finding("X53")
def sea_reputation_foreign():
    return region_rates(SEA, "WP22420", [1], "born")["foreign"]


@report.finding("X54")
def sea_reputation_gap():
    r = region_rates(SEA, "WP22420", [1], "born")
    return r["native"] - r["foreign"]


@report.finding("X55")
def sea_waste_foreign():
    return region_rates(SEA, "WP22415", [1], "born")["foreign"]


@report.finding("X56")
def sea_waste_native():
    return region_rates(SEA, "WP22415", [1], "born")["native"]


@report.finding("X57")
def latin_america_overall():
    return rate(workers, "any_vh", [1], "region")[LAC]


@report.finding("X58")
def lac_gap_birth():
    r = region_rates(LAC, "any_vh", [1], "born")
    return r["foreign"] - r["native"]


@report.finding("X59")
def lac_foreign_gap_income():
    r = region_rates(LAC, "any_vh", [1], ["born", "fin"])
    return r["foreign_difficult"] - r["foreign_comfortable"]


@report.finding("X60")
def lac_native_gap_income():
    r = region_rates(LAC, "any_vh", [1], ["born", "fin"])
    return r["native_difficult"] - r["native_comfortable"]


@report.finding("X61")
def lac_foreign_told():
    return region_rates(LAC, "WP22409", [1], "born")["foreign"]


@report.finding("X62")
def lac_native_told():
    return region_rates(LAC, "WP22409", [1], "born")["native"]


@report.finding("X63")
def lac_told_gap():
    r = region_rates(LAC, "WP22409", [1], "born")
    return r["foreign"] - r["native"]


@report.finding("X64")
def lac_told_foreign_comfortable():
    return region_rates(LAC, "WP22409", [1], ["born", "fin"])["foreign_comfortable"]


@report.finding("X65")
def lac_told_foreign_difficult():
    return region_rates(LAC, "WP22409", [1], ["born", "fin"])["foreign_difficult"]


@report.finding("C9")
def latin_america_chart():
    return experience_and_told(LAC)


FORMS = {"three": [3], "two": [2], "one": [1], "none": [0]}


@report.finding("C10")
def lac_number_of_forms():
    w = region_by_birth(LAC)
    by_sex = only(shares(w, "n_forms", FORMS, ["born", "sex"]), ["foreign_"])
    return {**shares(w, "n_forms", FORMS, "born"), **by_sex}


@report.finding("X66")
def lac_foreign_three():
    return region_rates(LAC, "n_forms", [3], "born")["foreign"]


@report.finding("X67")
def lac_native_three():
    return region_rates(LAC, "n_forms", [3], "born")["native"]


@report.finding("X68")
def lac_foreign_men_three():
    return region_rates(LAC, "n_forms", [3], ["born", "sex"])["foreign_men"]


@report.finding("X69")
def lac_foreign_women_three():
    return region_rates(LAC, "n_forms", [3], ["born", "sex"])["foreign_women"]


@report.finding("X70")
def lac_told_foreign_men():
    return region_rates(LAC, "WP22409", [1], ["born", "sex"])["foreign_men"]


@report.finding("X71")
def lac_told_native_men():
    return region_rates(LAC, "WP22409", [1], ["born", "sex"])["native_men"]


@report.finding("X72")
def lac_told_foreign_women():
    return region_rates(LAC, "WP22409", [1], ["born", "sex"])["foreign_women"]


@report.finding("X73")
def lac_punishment_foreign_men():
    return region_rates(LAC, "WP22419", [1], ["born", "sex"])["foreign_men"]


@report.finding("X74")
def lac_punishment_gap_sex():
    r = region_rates(LAC, "WP22419", [1], ["born", "sex"])
    return r["foreign_men"] - r["foreign_women"]


@report.finding("X75")
def lac_reputation_foreign_men():
    return region_rates(LAC, "WP22420", [1], ["born", "sex"])["foreign_men"]


@report.finding("X76")
def lac_reputation_gap_sex():
    r = region_rates(LAC, "WP22420", [1], ["born", "sex"])
    return r["foreign_men"] - r["foreign_women"]


# --- Page 13: Concluding remarks ---------------------------------------------------------


@report.finding("X77")
def lac_countries_ratified():
    countries = d.loc[d.GlobalRegion == 5, "COUNTRY_ISO3"].unique()
    return 100 * np.isin(countries, C190_RATIFIED).sum() / len(countries)


if __name__ == "__main__":
    sys.exit(report.run())
