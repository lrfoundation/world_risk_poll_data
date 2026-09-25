"""Reproduce World Risk Poll 2021 Focus On: Critical infrastructure resilience and
perceptions of disaster preparedness.

Run from the repository root:
    python reports/WRP_2021/focus_on_critical_infrastructure/reproduce.py

Each function below computes one chart, table or text statement listed in
published_figures.csv; see README.md for the method notes. Every finding uses
World Risk Poll questions in the public data.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, load_wave, pct  # noqa: E402

report = Report(__file__)

REGIONS = {  # GlobalRegion code -> key
    1: "eastern_africa", 2: "central_western_africa", 3: "north_africa", 4: "southern_africa",
    5: "latin_america_caribbean", 6: "northern_america", 7: "central_asia", 8: "east_asia",
    9: "south_eastern_asia", 10: "south_asia", 11: "middle_east", 12: "eastern_europe",
    13: "northern_western_europe", 14: "southern_europe", 15: "australia_nz",
}
# Went without for more than a day in the past 12 months (1 = yes).
SERVICES = {"electricity": "WP22254", "water": "WP22255", "food": "WP22256",
            "medicine": "WP22257", "telephone": "WP22258"}
EASTERN_AFRICA = ["MOZ", "TZA", "UGA", "ZWE", "ZMB", "KEN", "MUS"]  # Chart 7

d = load_wave(2021, [
    "PROJWT", "COUNTRY_ISO3", "GlobalRegion", "WP22245", "WP22241", "WP22526", "WP22244", "WP22252",
    *SERVICES.values(),
])

# --- Derived variables ---------------------------------------------------------

d["region"] = d.GlobalRegion.map(REGIONS)

# National government well prepared: WP22241. Myanmar was asked about "the
# government in power" (WP22526) instead; it is used there. That is what
# reproduces South-eastern Asia in Charts 3 and 4 (national 65%; 68% without Myanmar).
d["national"] = d.WP22241.fillna(d.WP22526)
LOCAL = "WP22244"  # local government well prepared (1 = yes, well prepared)

# Lost access to at least one of the five services (does not apply, DK and
# refused count as no; everyone is in the base).
d["lost_any"] = np.where(d[list(SERVICES.values())].eq(1).any(axis=1), 1, 2)
disaster = d[d.WP22245 == 1]  # experienced a disaster in the past five years
no_disaster = d[d.WP22245 == 2]
disaster_lost = disaster[disaster.lost_any == 1]

# --- Helpers -------------------------------------------------------------------


def national_minus_local(df, by=None):
    """Percentage-point gap: % national government well prepared minus % local.

    Each percentage uses the respondents asked that question, with DK and
    refused in the base.
    """
    gap = pct(df, "national", [1], by=by) - pct(df, LOCAL, [1], by=by)
    return gap if by is None else gap.dropna()


def mean_preparedness(df, by=None):
    """Mean perceived governmental preparedness: mean of the national and local %."""
    mean = (pct(df, "national", [1], by=by) + pct(df, LOCAL, [1], by=by)) / 2
    return mean if by is None else mean.dropna()


def over_services(fn, by=None):
    """Chart 7: the mean over the five services of fn() among those who
    experienced a disaster and lost that service."""
    parts = [fn(disaster[disaster[var] == 1], by=by) for var in SERVICES.values()]
    return sum(parts) / len(parts) if by is None else pd.concat(parts, axis=1).dropna().mean(axis=1)


def country_table():
    """Table 1: mean preparedness, % experienced a disaster and its rank, by country."""
    t = pd.DataFrame({"mean": mean_preparedness(d, by="COUNTRY_ISO3")})
    t["disaster"] = pct(d, "WP22245", [1], by="COUNTRY_ISO3")
    t["rank"] = t["disaster"].rank(ascending=False, method="min")  # 1 = most experience
    return t


def half_up(x):
    return np.floor(x + 0.5)


# --- Page 1: summary ---------------------------------------------------------------


@report.finding("X01")
def lost_any_service():
    return pct(d, "lost_any", [1])


@report.finding("X02")
def lost_any_service_disaster():
    return pct(disaster, "lost_any", [1])


@report.finding("X03")
def national_prepared():
    return pct(d, "national", [1])


@report.finding("X04")
def local_prepared():
    return pct(d, LOCAL, [1])


@report.finding("X05")
def gap_global():
    return national_minus_local(d)


@report.finding("X06")
def gap_lost_water():
    return national_minus_local(disaster[disaster[SERVICES["water"]] == 1])


# --- Page 2 ---------------------------------------------------------------------


@report.finding("X07")
def lost_any_service_disaster_intro():
    return pct(disaster, "lost_any", [1])


# --- Page 3: Charts 1 and 2 ----------------------------------------------------------


def lost_by_service(df):
    return {name: pct(df, var, [1]) for name, var in SERVICES.items()}


@report.finding("C1")
def lost_by_disaster():
    out = {}
    for name, value in lost_by_service(disaster).items():
        out[f"{name}_disaster"] = value
    for name, value in lost_by_service(no_disaster).items():
        out[f"{name}_no_disaster"] = value
    return out


@report.finding("X08")
def disaster_electricity():
    return lost_by_service(disaster)["electricity"]


@report.finding("X09")
def disaster_food():
    return lost_by_service(disaster)["food"]


@report.finding("X10")
def most_common_service():
    s = lost_by_service(disaster)
    return max(s, key=s.get)


@report.finding("X11")
def least_common_service():
    s = lost_by_service(disaster)
    return min(s, key=s.get)


@report.finding("C2")
def preparedness_and_agency():
    # One point per region: mean perceived governmental preparedness (x) against
    # % who could protect themselves or their family in a future disaster (y).
    x = mean_preparedness(d, by="region")
    y = pct(d, "WP22252", [1], by="region")[x.index]
    out = {"r2": np.corrcoef(x, y)[0, 1] ** 2}
    for region in x.index:
        out[f"{region}_preparedness"] = x[region]
        out[f"{region}_protect"] = y[region]
    return out


# --- Page 4: Chart 3 and Table 1 ----------------------------------------------------------


@report.finding("X12")
def mean_south_eastern_asia():
    return mean_preparedness(d, by="region")["south_eastern_asia"]


@report.finding("X13")
def mean_south_asia():
    return mean_preparedness(d, by="region")["south_asia"]


@report.finding("X14")
def mean_latin_america():
    return mean_preparedness(d, by="region")["latin_america_caribbean"]


@report.finding("X15")
def mean_central_western_africa():
    return mean_preparedness(d, by="region")["central_western_africa"]


@report.finding("C3")
def preparedness_by_region():
    local = pct(d, LOCAL, [1], by="region")
    national = pct(d, "national", [1], by="region")
    mean = mean_preparedness(d, by="region")
    out = {}
    for region in REGIONS.values():
        out[f"{region}_local"] = local[region]
        out[f"{region}_national"] = national[region]
        out[f"{region}_mean"] = mean[region]
    return out


@report.finding("X16")
def regions_local_higher():
    return int((national_minus_local(d, by="region") < 0).sum())


@report.finding("T1")
def table_1():
    t = country_table()
    shown = ["ARE", "BGD", "PHL", "IDN", "SGP", "ROU", "BOL", "PRY", "LBN", "AFG"]
    return {f"{iso}_{col}": t.loc[iso, col] for iso in shown for col in ("mean", "disaster", "rank")}


@report.finding("X17")
def countries_ranked():
    return len(country_table())


@report.finding("X18")
def five_highest():
    return ", ".join(sorted(country_table()["mean"].nlargest(5).index))


@report.finding("X19")
def five_lowest():
    return ", ".join(sorted(country_table()["mean"].nsmallest(5).index))


@report.finding("X20")
def lowest():
    return country_table()["mean"].idxmin()


@report.finding("X21")
def philippines_disaster():
    return country_table().loc["PHL", "disaster"]


# --- Page 5: Chart 4 ---------------------------------------------------------------------


@report.finding("C4")
def gap_by_region():
    gaps = national_minus_local(d, by="region")
    mean = mean_preparedness(d, by="region")
    return {"global": national_minus_local(d),
            **{region: gaps[region] for region in REGIONS.values()},
            **{f"mean_{region}": mean[region] for region in REGIONS.values()}}


@report.finding("X22")
def national_prepared_p5():
    return pct(d, "national", [1])


@report.finding("X23")
def local_prepared_p5():
    return pct(d, LOCAL, [1])


@report.finding("X24")
def gap_global_p5():
    return national_minus_local(d)


@report.finding("X25")
def regions_favour_local():
    # As printed: regions whose gap rounds to below zero.
    return int((half_up(national_minus_local(d, by="region")) < 0).sum())


# --- Page 6: Chart 5 ---------------------------------------------------------------------


def gap_by_service():
    return {name: national_minus_local(disaster[disaster[var] == 1]) for name, var in SERVICES.items()}


@report.finding("X26")
def gap_disaster_lost():
    return national_minus_local(disaster_lost)


@report.finding("X27")
def gap_water_text():
    return gap_by_service()["water"]


@report.finding("X28")
def gap_food_text():
    return gap_by_service()["food"]


@report.finding("C5")
def gap_services():
    return gap_by_service()


@report.finding("X29")
def north_africa_all():
    return national_minus_local(d, by="region")["north_africa"]


@report.finding("X30")
def north_africa_disaster_lost():
    return national_minus_local(disaster_lost, by="region")["north_africa"]


@report.finding("X31")
def north_africa_reduction():
    return north_africa_all() - north_africa_disaster_lost()


@report.finding("X32")
def nw_europe_all():
    return national_minus_local(d, by="region")["northern_western_europe"]


@report.finding("X33")
def nw_europe_disaster_lost():
    return national_minus_local(disaster_lost, by="region")["northern_western_europe"]


@report.finding("X34")
def nw_europe_shift():
    return nw_europe_all() - nw_europe_disaster_lost()


# --- Page 7: Charts 6 and 7 -----------------------------------------------------------------


@report.finding("C6")
def gap_by_region_disaster_lost():
    gaps = national_minus_local(disaster_lost, by="region")
    return {"global": national_minus_local(disaster_lost), **{r: gaps[r] for r in REGIONS.values()}}


@report.finding("X35")
def eastern_africa_disaster_lost():
    return national_minus_local(disaster_lost, by="region")["eastern_africa"]


@report.finding("C7")
def eastern_africa_countries():
    gaps = over_services(national_minus_local, by="COUNTRY_ISO3")
    mean = over_services(mean_preparedness, by="COUNTRY_ISO3")
    regional = over_services(national_minus_local, by="region")["eastern_africa"]
    return {"regional": regional,
            **{f"{iso}_gap": gaps[iso] for iso in EASTERN_AFRICA},
            **{f"{iso}_mean": mean[iso] for iso in EASTERN_AFRICA}}


# --- Pages 8-9: case studies ------------------------------------------------------------------


@report.finding("X36")
def tanzania_mean():
    return over_services(mean_preparedness, by="COUNTRY_ISO3")["TZA"]


@report.finding("X37")
def tanzania_gap():
    return over_services(national_minus_local, by="COUNTRY_ISO3")["TZA"]


@report.finding("X38")
def mauritius_mean():
    return over_services(mean_preparedness, by="COUNTRY_ISO3")["MUS"]


if __name__ == "__main__":
    sys.exit(report.run())
