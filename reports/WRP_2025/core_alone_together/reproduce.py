"""Reproduce World Risk Poll 2026: Alone together: The hidden consensus on climate change.

Run from the repository root:
    python reports/WRP_2025/core_alone_together/reproduce.py

The report uses the 2025 poll. It compares two questions: whether climate
change is a threat to the country in the next 20 years (WP20719, the
"personal" view) and the new question on whether most other people in the
country see it as a threat (WP24225, the "perceived societal" view).
Chapter 1 trends the personal view back to 2019. Each function below
computes one chart, table or text statement listed in published_figures.csv;
see README.md for the method notes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import (  # noqa: E402
    Report, distribution, external_path, load_wave, merge_gallup, pct, value_labels, wmean,
)

report = Report(__file__)

DK = [98, 99]  # don't know, refused: kept in the base, and shown as "don't know" in the report
PERSONAL, PERCEIVED = "WP20719", "WP24225"  # 1 = very serious, 2 = somewhat serious, 3 = not a threat
LOW, LOWER_MIDDLE, UPPER_MIDDLE, HIGH = 1, 2, 3, 4  # CountryIncomeLevel
GROUPS = {LOW: "low", LOWER_MIDDLE: "lower_middle", UPPER_MIDDLE: "upper_middle", HIGH: "high"}
REGIONS = {  # GlobalRegion codes -> keys used in Chart 2.2
    1: "eastern_africa", 2: "cw_africa", 3: "northern_africa", 4: "southern_africa", 5: "latam",
    6: "northern_america", 7: "central_asia", 8: "eastern_asia", 9: "southeastern_asia", 10: "southern_asia",
    11: "middle_east", 12: "eastern_europe", 13: "nw_europe", 14: "southern_europe", 15: "anz",
}
EU = ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL",
      "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"]
THREAT = {"very": [1], "somewhat": [2], "dk": DK, "not": [3]}

d = load_wave(2025, ["WPID_RANDOM", "COUNTRY_ISO3", "PROJWT", "GlobalRegion", "CountryIncomeLevel",
                     PERSONAL, PERCEIVED])

# --- Derived variables ---------------------------------------------------------

# Alignment (Charts 2.2, 2.8): among respondents with a substantive answer
# (1-3) to both questions. A lower code is a more serious threat, so
# 1 = more personal than perceived societal concern, 2 = aligned (same
# answer), 3 = more perceived societal than personal concern.
both = d[PERSONAL].isin([1, 2, 3]) & d[PERCEIVED].isin([1, 2, 3])
d["alignment"] = np.select(
    [both & (d[PERSONAL] < d[PERCEIVED]), both & (d[PERSONAL] == d[PERCEIVED]), both & (d[PERSONAL] > d[PERCEIVED])],
    [1, 2, 3], default=np.nan,
)
d["answered_both"] = np.where(both, 1, 2)  # 2 = DK/refused to at least one question

# Income groups for the trend: the report classifies every wave's countries
# by the 2025 World Bank classification (CountryIncomeLevel in the 2025
# file). Countries not surveyed in 2025 get no group and drop out of Chart 1.2.
INCOME_2025 = d.groupby("COUNTRY_ISO3")["CountryIncomeLevel"].first()

# Trend file (Charts 1.1-1.4): the personal climate question in each wave.
CLIMATE = {2019: "L5", 2021: "WP20719", 2023: "WP20719", 2025: "WP20719"}
t = pd.concat([load_wave(y, ["COUNTRY_ISO3", "PROJWT", v]).rename(columns={v: "climate"}).assign(Year=y)
               for y, v in CLIMATE.items()], ignore_index=True)
t["income2025"] = t["COUNTRY_ISO3"].map(INCOME_2025)

# Country table (Charts 2.4, 2.5 and the country counts): % very serious,
# personal and perceived societal. The report's country gaps are the
# difference of the rounded percentages (this is what reproduces the
# Chart 2.5 gap column and the "110 of 140" count; see README).
country = pd.DataFrame({"personal": pct(d, PERSONAL, [1], by="COUNTRY_ISO3"),
                        "perceived": pct(d, PERCEIVED, [1], by="COUNTRY_ISO3")})
country["income"] = INCOME_2025
country["gap"] = country["personal"].round() - country["perceived"].round()
top10 = country.sort_values("gap", ascending=False, kind="stable").head(10)

# Change in % very serious, 2023 to 2025 (Chart 1.4), countries in both waves.
# `change` is unrounded (a "significant" change is more than 4 points, the
# chart's margin of error); `change_rounded` uses the rounded percentages,
# as the country annotations and the "eight high-income countries" do.
very = pct(t[t.Year.isin([2023, 2025])], "climate", [1], by=["COUNTRY_ISO3", "Year"]).unstack().dropna()
change = pd.DataFrame({"v2023": very[2023], "v2025": very[2025]})
change["change"] = change.v2025 - change.v2023
change["change_rounded"] = change.v2025.round() - change.v2023.round()
change["income"] = INCOME_2025

# ND-GAIN vulnerability (Chart 2.7): 2024 release, latest year. Not redistributed here:
# python reports/external/fetch_external.py ndgain downloads it.
NDGAIN = "core_alone_together__ndgain_vulnerability.csv"
NDGAIN_YEAR = "2022"

# --- Helpers -------------------------------------------------------------------


def income(df, var, codes, group):
    """% in `codes` of `var` for one CountryIncomeLevel group."""
    return pct(df, var, codes, by="CountryIncomeLevel")[group]


def trend_any(year, group):
    """% very or somewhat serious in `year`, for a 2025 income group."""
    return pct(t[t.Year == year], "climate", [1, 2], by="income2025")[group]


def isos(index):
    return ", ".join(sorted(index))


def aligned_by_region():
    return distribution(d, "alignment", by="GlobalRegion")


# --- Foreword and executive summary ------------------------------------------------


@report.finding("X01")
def interviews():
    return len(d)


@report.finding("X02")
def countries():
    return d.COUNTRY_ISO3.nunique()


@report.finding("X03")
def any_threat():
    return pct(d, PERSONAL, [1, 2])


@report.finding("X04")
def gap_over_30():
    return int((country.gap > 30).sum())


@report.finding("X05")
def very_serious():
    return pct(d, PERSONAL, [1])


@report.finding("X06")
def somewhat_serious():
    return pct(d, PERSONAL, [2])


@report.finding("X07")
def highest_wave():
    return int(pct(t, "climate", [1, 2], by="Year").idxmax())


@report.finding("X08")
def lower_middle_2019():
    return trend_any(2019, LOWER_MIDDLE)


@report.finding("X09")
def lower_middle_2025():
    return income(d, PERSONAL, [1, 2], LOWER_MIDDLE)


@report.finding("X10")
def upper_middle_2019():
    return trend_any(2019, UPPER_MIDDLE)


@report.finding("X11")
def upper_middle_2025():
    return income(d, PERSONAL, [1, 2], UPPER_MIDDLE)


@report.finding("X12")
def perceived_any():
    return pct(d, PERCEIVED, [1, 2])


@report.finding("X13")
def perceived_very():
    return pct(d, PERCEIVED, [1])


@report.finding("X14")
def high_income_very():
    return income(d, PERSONAL, [1], HIGH)


@report.finding("X15")
def high_income_perceived_very():
    return income(d, PERCEIVED, [1], HIGH)


@report.finding("X16")
def gap_40_plus():
    return int((country.gap >= 40).sum())


# --- Chapter 1: concern about climate change, 2019-2025 ------------------------------


def wave(year, codes):
    return pct(t[t.Year == year], "climate", codes)


@report.finding("X17")
def somewhat_2021():
    return wave(2021, [2])


@report.finding("X18")
def dk_2025():
    return wave(2025, DK)


@report.finding("X19")
def dk_2019():
    return wave(2019, DK)


@report.finding("X20")
def dk_2021():
    return wave(2021, DK)


@report.finding("X21")
def not_a_threat_2025():
    return wave(2025, [3])


@report.finding("C1_1")
def trend_global():
    out = {f"{key}_{y}": wave(y, codes) for key, codes in THREAT.items() for y in CLIMATE}
    out["any_2025"] = wave(2025, [1, 2])
    return out


@report.finding("C1_2")
def trend_by_income():
    out = {}
    for code, g in GROUPS.items():
        sub = t[t.income2025 == code]
        for key, codes in (("very", [1]), ("somewhat", [2])):
            for y in (2019, 2025):
                out[f"{g}_{key}_{y}"] = pct(sub[sub.Year == y], "climate", codes)
        out[f"{g}_peak"] = int(pct(sub, "climate", [1, 2], by="Year").idxmax())
    return out


@report.finding("X22")
def high_income_any():
    return income(d, PERSONAL, [1, 2], HIGH)


@report.finding("C1_3")
def selected_high_income():
    # No values are printed on Chart 1.3; recorded for Python/R comparison only.
    sel = ["ESP", "GBR", "IRL", "CAN", "NZL", "DNK", "HRV", "KWT"]
    r = pct(t[t.COUNTRY_ISO3.isin(sel)], "climate", [1], by=["COUNTRY_ISO3", "Year"])
    return {f"{c}_{y}": v for (c, y), v in r.items()}


def high_income_falls():
    hi = change[change.income == HIGH]
    return hi.index[hi.change_rounded <= -10]


@report.finding("X23")
def high_income_fall_10():
    return len(high_income_falls())


@report.finding("X24")
def high_income_fall_10_names():
    return isos(high_income_falls())


@report.finding("C1_4")
def change_2023_2025():
    hi = change[change.income == HIGH]
    lower = change[change.income.isin([LOW, LOWER_MIDDLE])]
    out = {
        "TUN_2023": change.v2023["TUN"], "TUN_change": change.change_rounded["TUN"],
        "VNM_2023": change.v2023["VNM"], "VNM_change": change.change_rounded["VNM"],
        "largest_fall": change.change.idxmin(), "largest_rise": change.change.idxmax(),
        "high_countries": len(hi), "high_fall": int((hi.change < -4).sum()),
        "lower_countries": len(lower), "lower_rise": int((lower.change > 4).sum()),
        "lower_fall_share": 100 * (lower.change < -4).mean(),
        "high_rise_share": 100 * (hi.change > 4).mean(),
    }
    # Every country's change (no values printed): for Python/R comparison only.
    out.update({f"change_{c}": v for c, v in change.change.items()})
    return out


# --- Chapter 2: second-order beliefs ---------------------------------------------------


@report.finding("X25")
def in_step():
    return pct(d, "alignment", [2])


@report.finding("X26")
def others_more_concerned():
    return pct(d, "alignment", [3])


@report.finding("X27")
def more_concerned_than_others():
    return pct(d, "alignment", [1])


@report.finding("C2_1")
def personal_and_perceived():
    out = {f"personal_{k}": pct(d, PERSONAL, c) for k, c in THREAT.items()}
    out.update({f"perceived_{k}": pct(d, PERCEIVED, c) for k, c in THREAT.items()})
    return out


@report.finding("X28")
def aligned():
    return pct(d, "alignment", [2])


@report.finding("X29")
def misaligned():
    return pct(d, "alignment", [1, 3])


@report.finding("X30")
def not_both_answered():
    return pct(d, "answered_both", [2])


@report.finding("X31")
def asia_aligned_70():
    r = aligned_by_region()[2]
    return int((r[[7, 8, 9, 10]] >= 70).sum())


@report.finding("X32")
def regions_majority_misaligned():
    return int((aligned_by_region()[2] < 50).sum())


@report.finding("X33")
def regions_more_personal_than_aligned():
    r = aligned_by_region()
    return int((r[1] > r[2]).sum())


@report.finding("C2_2")
def alignment_by_region():
    cats = {1: "more_personal", 2: "aligned", 3: "more_societal"}
    table = aligned_by_region()
    out = {f"global_{name}": pct(d, "alignment", [code]) for code, name in cats.items()}
    out.update({f"{REGIONS[int(reg)]}_{name}": table.loc[reg, code]
                for reg in table.index for code, name in cats.items()})
    return out


@report.finding("X34")
def low_income_any():
    return income(d, PERSONAL, [1, 2], LOW)


@report.finding("X35")
def high_income_perceived_any():
    return income(d, PERCEIVED, [1, 2], HIGH)


@report.finding("X36")
def high_income_gap_any():
    return income(d, PERSONAL, [1, 2], HIGH) - income(d, PERCEIVED, [1, 2], HIGH)


@report.finding("X37")
def other_groups_gap_any():
    return max(abs(income(d, PERSONAL, [1, 2], g) - income(d, PERCEIVED, [1, 2], g))
               for g in (LOW, LOWER_MIDDLE, UPPER_MIDDLE))


@report.finding("X38")
def other_groups_gap_very():
    return max(income(d, PERSONAL, [1], g) - income(d, PERCEIVED, [1], g) for g in (LOW, LOWER_MIDDLE, UPPER_MIDDLE))


@report.finding("C2_3")
def by_income_group():
    out = {}
    for code, g in GROUPS.items():
        for measure, var in (("perceived", PERCEIVED), ("personal", PERSONAL)):
            out[f"{g}_{measure}_very"] = income(d, var, [1], code)
            out[f"{g}_{measure}_somewhat"] = income(d, var, [2], code)
            out[f"{g}_{measure}_total"] = income(d, var, [1, 2], code)
    return out


@report.finding("C2_4")
def country_scatter():
    # No values are printed on Chart 2.4; recorded for Python/R comparison only.
    return {f"{c}_{m}": country.loc[c, m] for c in country.index for m in ("personal", "perceived")}


@report.finding("X39")
def countries_gap_5():
    return int((country.gap >= 5).sum())


@report.finding("X40")
def countries_reverse_gap_5():
    return int((country.gap <= -5).sum())


@report.finding("X41")
def countries_reverse_gap_5_names():
    return isos(country.index[country.gap <= -5])


@report.finding("X42")
def top10_high_income():
    return int((top10.income == HIGH).sum())


@report.finding("X43")
def top10_other_group():
    codes = top10.income[top10.income != HIGH]
    return "; ".join(value_labels(2025, "CountryIncomeLevel")[int(c)] for c in codes)


@report.finding("X44")
def gap_portugal():
    return country.gap["PRT"]


@report.finding("X45")
def gap_us():
    return country.gap["USA"]


@report.finding("X46")
def top10_smallest_gap():
    return top10.gap.min()


@report.finding("C2_5")
def widest_gaps():
    out = {"top10": isos(top10.index)}
    for c in top10.index:
        out.update({f"{c}_personal": top10.personal[c], f"{c}_perceived": top10.perceived[c], f"{c}_gap": top10.gap[c]})
    return out


def area(key):
    return d[d.COUNTRY_ISO3.isin(EU)] if key == "EU" else d[d.COUNTRY_ISO3 == key]


@report.finding("X47")
def china_any():
    return pct(area("CHN"), PERSONAL, [1, 2])


@report.finding("X48")
def us_any():
    return pct(area("USA"), PERSONAL, [1, 2])


@report.finding("X49")
def us_very():
    return pct(area("USA"), PERSONAL, [1])


@report.finding("X50")
def china_very():
    return pct(area("CHN"), PERSONAL, [1])


@report.finding("X51")
def us_perceived_very():
    return pct(area("USA"), PERCEIVED, [1])


@report.finding("X52")
def china_reverse_gap():
    return pct(area("CHN"), PERCEIVED, [1]) - pct(area("CHN"), PERSONAL, [1])


@report.finding("X53")
def india_dk_personal():
    return pct(area("IND"), PERSONAL, DK)


@report.finding("X54")
def india_dk_perceived():
    return pct(area("IND"), PERCEIVED, DK)


@report.finding("X55")
def eu_very():
    return pct(area("EU"), PERSONAL, [1])


@report.finding("X56")
def eu_perceived_very():
    return pct(area("EU"), PERCEIVED, [1])


@report.finding("C2_6")
def largest_emitters():
    out = {}
    for key in ("CHN", "IND", "EU", "USA"):
        for measure, var in (("perceived", PERCEIVED), ("personal", PERSONAL)):
            out.update({f"{key}_{measure}_{k}": pct(area(key), var, c) for k, c in THREAT.items()})
    return out


def vulnerability_correlation(measure):
    nd = pd.read_csv(external_path(NDGAIN)).set_index("ISO3")[NDGAIN_YEAR]
    m = country.join(nd.rename("vulnerability"), how="inner").dropna(subset=["vulnerability"])
    return m[measure].corr(m["vulnerability"])


@report.finding("X57")
def vulnerability_personal():
    return vulnerability_correlation("personal")


@report.finding("X58")
def vulnerability_perceived():
    return vulnerability_correlation("perceived")


@report.finding("C2_8")
def institutions_by_alignment():
    # Needs Gallup's National Institutions Index (INDEX_NI: confidence in the
    # national government, honesty of elections, the military, and the
    # judicial system and courts), which is not in the public release.
    g = merge_gallup(d[d.alignment.notna()], ["INDEX_NI"])
    r = wmean(g, "INDEX_NI", by=["CountryIncomeLevel", "alignment"])
    cats = {1: "more_personal", 2: "aligned", 3: "more_societal"}
    return {f"{GROUPS[int(i)]}_{cats[int(a)]}": v for (i, a), v in r.items() if int(i) in GROUPS}


# --- Conclusion ---------------------------------------------------------------------


@report.finding("X59")
def high_income_gap_very():
    return income(d, PERSONAL, [1], HIGH) - income(d, PERCEIVED, [1], HIGH)


if __name__ == "__main__":
    sys.exit(report.run())
