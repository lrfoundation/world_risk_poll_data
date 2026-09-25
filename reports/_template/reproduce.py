"""Reproduce the findings of <REPORT TITLE> (<wave> data).

Run from the repository root:
    python reports/WRP_YYYY/<report_folder>/reproduce.py

Each function below computes one finding (or one chart/table) listed in
published_figures.csv, under the same finding_id. See README.md in this
folder for the method notes and any Gallup World Poll caveats.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # reports/, for `wrp`

from wrp import Report, load_wave, merge_gallup, pct  # noqa: E402

report = Report(__file__)

# Load only the columns this report needs; the data dictionary
# (WRP_YYYY/WRP_YYYY_data_dictionary.csv) gives every variable's codes.
df = load_wave(2019, ["WPID_RANDOM", "PROJWT", "Gender", "L5"])


@report.finding("F01")
def climate_very_serious():
    # L5: 1 = very serious threat. DK/refused stay in the base.
    return pct(df, "L5", [1])


@report.finding("F02")
def climate_very_serious_by_gender():
    # Returns one value per group -> recorded as F02_1 (men), F02_2 (women).
    return pct(df, "L5", [1], by="Gender")


@report.finding("F03")
def needs_gallup_item():
    # Needs a Gallup World Poll item that is not in the public release.
    # Without GALLUP_WP_PATH this is reported as GALLUP_ONLY.
    gwp = merge_gallup(df, ["WP_EXAMPLE"])
    return pct(gwp, "WP_EXAMPLE", [1])


if __name__ == "__main__":
    sys.exit(report.run())
