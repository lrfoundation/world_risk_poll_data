"""Country-level values for the maps in the book, computed from the public wave files.

Each function returns a Series indexed by COUNTRY_ISO3. The conventions are the
ones in reports/README.md: PROJWT weights, respondents who were not asked a
question are left out, and don't know and refused answers stay in the base.
Countries with fewer than MIN_N respondents in the base are left blank.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wrp import load_wave, pct, wmean  # noqa: E402

MIN_N = 100


def _share(year, var, codes, where=None, cols=()):
    d = load_wave(year, ["COUNTRY_ISO3", "PROJWT", var, *cols])
    if where is not None:
        d = d[where(d)]
    d = d[d[var].notna()]
    n = d.groupby("COUNTRY_ISO3").size()
    values = pct(d, var, codes, by="COUNTRY_ISO3")
    return values[n.reindex(values.index) >= MIN_N]


def less_safe_2019():
    return _share(2019, "L2", [2])


def injured_at_work_2019():
    return _share(2019, "L19", [1])


def climate_very_serious_2019():
    return _share(2019, "L5", [1])


def gov_food_not_good_2019():
    return _share(2019, "L16A", [2])


def gov_water_not_good_2019():
    return _share(2019, "L16B", [2])


def internet_use_2019():
    return _share(2019, "L26", [1])


def worried_false_info_2019():
    """Among internet users (the question was put only to them)."""
    return _share(2019, "L27B", [1])


def worried_fraud_2019():
    return _share(2019, "L27C", [1])


def less_safe_2021():
    return _share(2021, "WP20711", [2])


def could_protect_2021():
    return _share(2021, "WP22252", [1])


def ai_mostly_harm_2021():
    return _share(2021, "WP22227", [2])


def violence_harassment_2021():
    """Ever experienced any violence or harassment at work, among people who have ever worked."""
    vh = ["WP22400_ALL", "WP22403_ALL", "WP22406_ALL"]
    d = load_wave(2021, ["COUNTRY_ISO3", "PROJWT", *vh])
    d = d[d[vh].notna().any(axis=1) & ~d[vh].eq(7).any(axis=1)].copy()
    d["any_vh"] = np.where(d[vh].eq(1).any(axis=1), 1.0, 2.0)
    n = d.groupby("COUNTRY_ISO3").size()
    values = pct(d, "any_vh", [1], by="COUNTRY_ISO3")
    return values[n.reindex(values.index) >= MIN_N]


def _index(year):
    d = load_wave(year, ["COUNTRY_ISO3", "PROJWT", "resilience_index_100"])
    return wmean(d, "resilience_index_100", by="COUNTRY_ISO3").dropna()


def resilience_index_2023():
    return _index(2023)


def resilience_index_2025():
    return _index(2025)


def burns_waste_2023():
    return _share(2023, "WP23343", [1])


def harmed_at_work_2023():
    """Personally experienced serious harm at work in the past two years, current workforce."""
    return _share(2023, "WP22448", [1, 3], where=lambda d: d.EMP_2010.isin([1, 2, 3, 4, 5]), cols=["EMP_2010"])


def road_top_risk_2023():
    return _share(2023, "WP22331", [1])


def climate_concern_gap_2025():
    """Own 'very serious threat' minus the share who think most others see a very serious threat."""
    return _share(2025, "WP20719", [1]) - _share(2025, "WP24225", [1])


def harmed_prolonged_weather_2025():
    return _share(2025, "WP24177", [1, 3])


def impacted_by_disaster_2025():
    return _share(2025, "WP24213", [1])




# Country values that a report also prints, used to check the map calculations:
# (map function, country, report folder, finding in its published_figures.csv)
CHECKS = [
    ("injured_at_work_2019", "SLE", "WRP_2019/core_world_risk_poll_2019", "X5_14"),
    ("climate_very_serious_2019", "CHN", "WRP_2019/core_world_risk_poll_2019", "X6_04"),
    ("less_safe_2019", "LBN", "WRP_2019/core_world_risk_poll_2019", "T1_1_LBN_less"),
    ("gov_food_not_good_2019", "LBN", "WRP_2019/core_world_risk_poll_2019", "C9_6_LBN"),
    ("gov_water_not_good_2019", "LBN", "WRP_2019/core_world_risk_poll_2019", "C9_8_LBN"),
    ("worried_false_info_2019", "MWI", "WRP_2019/core_world_risk_poll_2019", "C8_4_MWI"),
    ("worried_fraud_2019", "MUS", "WRP_2019/core_world_risk_poll_2019", "C8_8_MUS"),
    ("burns_waste_2023", "IDN", "WRP_2023/core_a_world_of_waste", "X16"),
    ("impacted_by_disaster_2025", "PHL", "WRP_2025/core_from_alert_to_agency", "X023"),
    ("impacted_by_disaster_2025", "ISR", "WRP_2025/core_from_alert_to_agency", "X024"),
]


def check():
    """Compare map values with the same figures as published; returns the number that differ."""
    from figures import published
    wrong = 0
    for fn, iso, folder, fid in CHECKS:
        ours, theirs = globals()[fn]()[iso], float(published(folder)[fid]["published_value"])
        ok = abs(ours - theirs) <= 1
        wrong += not ok
        print(f"{'ok ' if ok else 'DIFFERENT'} {fn:28s} {iso}  map {ours:5.1f}  published {theirs:g}")
    gap = climate_concern_gap_2025()
    big = sorted(gap[gap >= 39.5].index)
    ok = big == ["PRT", "USA"]
    wrong += not ok
    print(f"{'ok ' if ok else 'DIFFERENT'} climate_concern_gap_2025: gap of 40 points or more in {big} (published: Portugal and the United States)")
    return wrong


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(check())
