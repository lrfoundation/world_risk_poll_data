"""Reproduce World Risk Poll 2024 Focus On: Risk perceptions and experiences of ocean workers.

Run from the repository root:
    python reports/WRP_2023/focus_on_ocean_workers/reproduce.py

The report compares ocean workers with other workers, using the 2023 poll.
The public release identifies ocean workers only through the Job Sector
(Coded) answer "Fishing"; the report's own group is not the same (see
README.md). Each function below computes one chart or text statement listed
in published_figures.csv.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, load_wave, pct  # noqa: E402

report = Report(__file__)

d = load_wave(2023, [
    "PROJWT", "EMP_2010", "WP23340", "WP22331", "WP20719", "WP20723", "WP22445",
    "WP22214", "WP22448", "WP23335", "WP23337", "WP23338",
])

# --- Derived variables ---------------------------------------------------------

# Ocean workers: Job Sector (Coded) WP23340 = 2 "Fishing", whatever the
# respondent's current employment status (478 respondents). The public
# release has no code for shipping, ports or offshore work.
OCEAN = 2
d["ocean"] = d.WP23340.eq(OCEAN)

# Other workers: the current workforce (EMP_2010 1-5: employed full or part
# time, self-employed or unemployed; not out of the workforce) who are not
# ocean workers. The sector charts use the same current workforce.
d["workforce"] = d.EMP_2010.isin([1, 2, 3, 4, 5])
d["group"] = np.select([d.ocean, d.workforce], [1, 2], default=np.nan)  # 1 = ocean, 2 = other workers

# Chart 1.2 compares ocean workers with every other respondent.
d["group_all"] = np.where(d.ocean, 1, 2)

# OSH training (Chart 2.4): 1 = trained in the past two years, 2 = trained
# more than two years ago, 3 = not trained, or trained with no answer on
# when. Base: everyone asked WP23337.
d["osh_timing"] = np.select(
    [d.WP23337.eq(1) & d.WP23338.eq(1), d.WP23337.eq(1) & d.WP23338.eq(2), d.WP23337.notna()],
    [1, 2, 3], default=np.nan,
)

# Unweighted count, for Chart 2.2 (see README).
d["UNWEIGHTED"] = 1.0

PERSONALLY = [1, 3]  # experienced harm: 1 = yes, personally; 3 = both personally and someone known
WORRIED = [1, 2]     # very or somewhat worried
SECTORS = {          # WP23340 codes of the other sectors in Charts 2.2 and 2.3
    "construction": 4, "mining": 5, "agriculture": 1, "market_services": 7,
    "non_market_services": 8, "manufacturing": 3, "utilities": 6,
}
SECTOR_NAMES = {"ocean": "Ocean workers", "construction": "Construction", "mining": "Mining and quarrying",
                "agriculture": "Agriculture (excluding fishing)", "market_services": "Market services",
                "non_market_services": "Non-market services", "manufacturing": "Manufacturing",
                "utilities": "Electricity, gas or water supply"}

# --- Helpers -------------------------------------------------------------------


def by_group(var, codes, groups="group"):
    """% of ocean workers and of other workers whose `var` is in `codes`."""
    r = pct(d, var, codes, by=groups)
    return {"ocean": r[1], "other": r[2]}


def by_sector(var, codes, weight="PROJWT"):
    """% by sector: ocean workers (PROJWT) and the current workforce of each other sector."""
    out = {"ocean": pct(d[d.ocean], var, codes)}
    workforce = d[d.workforce]
    for key, code in SECTORS.items():
        out[key] = pct(workforce[workforce.WP23340 == code], var, codes, weight=weight)
    return out


def work_worry_by_sector():
    """% very or somewhat worried about harm from work, as in Chart 2.2."""
    very = by_sector("WP22214", [1], weight="UNWEIGHTED")
    some = by_sector("WP22214", [2], weight="UNWEIGHTED")
    very["ocean"] = pct(d[d.ocean], "WP22214", [1])
    some["ocean"] = pct(d[d.ocean], "WP22214", [2])
    return very, some


def rank_of_ocean(values):
    """Rank of ocean workers (1 = highest) among the sectors in `values`."""
    return 1 + sum(v > values["ocean"] for k, v in values.items() if k != "ocean")


# --- Climate change and ocean workers ---------------------------------------------


@report.finding("X01")
def threat_global():
    return pct(d, "WP20719", [1, 2])


@report.finding("X02")
def climate_risk_global():
    return pct(d, "WP22331", [19])


@report.finding("X03")
def climate_risk_ocean():
    return by_group("WP22331", [19])["ocean"]


@report.finding("X04")
def climate_risk_gap():
    r = by_group("WP22331", [19])
    return r["ocean"] - r["other"]


@report.finding("X05")
def climate_risk_other():
    return by_group("WP22331", [19])["other"]


@report.finding("X06")
def climate_risk_ratio():
    r = by_group("WP22331", [19])
    return r["ocean"] / r["other"]


@report.finding("X07")
def threat_ocean():
    return by_group("WP20719", [1, 2])["ocean"]


@report.finding("X08")
def threat_other():
    return by_group("WP20719", [1, 2])["other"]


@report.finding("C1_1")
def chart_climate_risk():
    return by_group("WP22331", [19])


@report.finding("C1_2")
def chart_threat():
    out = {}
    for key, codes in {"very": [1], "somewhat": [2], "dk": [98, 99], "not": [3]}.items():
        for grp, value in by_group("WP20719", codes, groups="group_all").items():
            out[f"{grp}_{key}"] = value
    return out


@report.finding("X09")
def weather_worry_ocean():
    return by_group("WP20723", WORRIED)["ocean"]


@report.finding("X10")
def weather_worry_other():
    return by_group("WP20723", WORRIED)["other"]


@report.finding("X11")
def weather_very_ocean():
    return by_group("WP20723", [1])["ocean"]


@report.finding("X12")
def weather_very_other():
    return by_group("WP20723", [1])["other"]


@report.finding("X13")
def weather_very_global():
    return pct(d, "WP20723", [1])


@report.finding("X14")
def weather_harm_ocean():
    return by_group("WP22445", PERSONALLY)["ocean"]


@report.finding("X15")
def weather_harm_other():
    return by_group("WP22445", PERSONALLY)["other"]


@report.finding("C1_3")
def chart_weather_worry():
    very, some = by_group("WP20723", [1]), by_group("WP20723", [2])
    return {"ocean_very": very["ocean"], "ocean_somewhat": some["ocean"],
            "other_very": very["other"], "other_somewhat": some["other"]}


@report.finding("C1_4")
def chart_weather_harm():
    return by_group("WP22445", PERSONALLY)


# --- The cost of work at sea ----------------------------------------------------------


@report.finding("X16")
def work_risk_ocean():
    return by_group("WP22331", [17])["ocean"]


@report.finding("X17")
def work_risk_other():
    return by_group("WP22331", [17])["other"]


@report.finding("X18")
def work_risk_ratio():
    r = by_group("WP22331", [17])
    return r["ocean"] / r["other"]


@report.finding("C2_1")
def chart_work_risk():
    return by_group("WP22331", [17])


@report.finding("X19")
def work_worry_ocean():
    return by_group("WP22214", WORRIED)["ocean"]


@report.finding("X20")
def work_worry_other():
    return by_group("WP22214", WORRIED)["other"]


@report.finding("X21")
def work_very_ocean():
    return by_group("WP22214", [1])["ocean"]


@report.finding("X22")
def work_very_other():
    return by_group("WP22214", [1])["other"]


@report.finding("X23")
def work_worry_rank():
    very, some = work_worry_by_sector()
    return rank_of_ocean({k: very[k] + some[k] for k in very})


@report.finding("X24")
def work_worry_top_sector():
    very, some = work_worry_by_sector()
    total = {k: very[k] + some[k] for k in very}
    return SECTOR_NAMES[max(total, key=total.get)]


@report.finding("X25")
def work_harm_ocean():
    return by_group("WP22448", PERSONALLY)["ocean"]


@report.finding("X26")
def work_harm_other():
    return by_group("WP22448", PERSONALLY)["other"]


@report.finding("X27")
def work_harm_rank():
    return rank_of_ocean(by_sector("WP22448", PERSONALLY))


@report.finding("C2_2")
def chart_work_worry_by_sector():
    very, some = work_worry_by_sector()
    out = {}
    for key in very:
        out[f"{key}_very"] = very[key]
        out[f"{key}_somewhat"] = some[key]
    return out


@report.finding("C2_3")
def chart_work_harm_by_sector():
    out = by_sector("WP22448", PERSONALLY)
    out["global"] = pct(d[d.workforce], "WP22448", PERSONALLY)  # the current workforce, all sectors
    return out


@report.finding("X28")
def osh_ocean():
    return by_group("WP23337", [1])["ocean"]


@report.finding("X29")
def osh_other():
    return by_group("WP23337", [1])["other"]


@report.finding("X30")
def osh_recent_ocean():
    return by_group("osh_timing", [1])["ocean"]


@report.finding("C2_4")
def chart_osh():
    recent, older = by_group("osh_timing", [1]), by_group("osh_timing", [2])
    return {"ocean_recent": recent["ocean"], "ocean_older": older["ocean"],
            "other_recent": recent["other"], "other_older": older["other"]}


@report.finding("X31")
def told_ocean():
    return by_group("WP23335", [1])["ocean"]


@report.finding("X32")
def told_other():
    return by_group("WP23335", [1])["other"]


@report.finding("C2_5")
def chart_told():
    return by_group("WP23335", [1])


if __name__ == "__main__":
    sys.exit(report.run())
