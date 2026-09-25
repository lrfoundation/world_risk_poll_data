"""Optional Gallup World Poll (GWP) items that are not in the public release.

The World Risk Poll is fielded as part of the Gallup World Poll, and some
report findings combine World Risk Poll questions with core GWP items
(for example, confidence in institutions or feelings about household
income that are not in this release). Those GWP items are Gallup's
proprietary data: they are not included here and must be licensed from
Gallup directly (https://www.gallup.com/analytics/318875/global-research.aspx).

If you have them, point GALLUP_WP_PATH at a file (Parquet, CSV, SPSS .sav
or Stata .dta) holding WPID_RANDOM plus the GWP items a report needs. Rows
are matched to the World Risk Poll on WPID_RANDOM, so the file must carry
the same respondent IDs as the World Risk Poll release; confirm this with
Gallup when you request the data. Without the file, findings that need GWP
items are reported as SKIPPED and every other finding still runs.
"""

import os
from pathlib import Path

import pandas as pd

GALLUP_ENV = "GALLUP_WP_PATH"


class GallupDataRequired(RuntimeError):
    """A finding needs Gallup World Poll items that are not in the public data."""


def load_gallup(columns):
    """WPID_RANDOM plus `columns` from the user's licensed GWP file."""
    path = os.environ.get(GALLUP_ENV)
    if not path:
        raise GallupDataRequired(
            f"needs Gallup World Poll item(s) {', '.join(columns)}, which are not in the "
            f"public release; license them from Gallup and set {GALLUP_ENV}"
        )
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        gwp = pd.read_parquet(path)
    elif suffix == ".csv":
        gwp = pd.read_csv(path)
    elif suffix == ".sav":
        gwp = pd.read_spss(path, convert_categoricals=False)
    elif suffix == ".dta":
        gwp = pd.read_stata(path, convert_categoricals=False)
    else:
        raise ValueError(f"{GALLUP_ENV} must point to a .parquet, .csv, .sav or .dta file")
    wanted = ["WPID_RANDOM", *columns]
    missing = [c for c in wanted if c not in gwp.columns]
    if missing:
        raise GallupDataRequired(f"{path.name} does not contain {', '.join(missing)}")
    return gwp[wanted]


def merge_gallup(df, columns):
    """Left-join GWP `columns` onto World Risk Poll rows by WPID_RANDOM."""
    gwp = load_gallup(columns).drop_duplicates("WPID_RANDOM")
    merged = df.merge(gwp, on="WPID_RANDOM", how="left", validate="many_to_one")
    matched = merged[columns[0]].notna().mean()
    if matched < 0.9:
        print(f"  warning: only {matched:.0%} of rows matched a Gallup World Poll record")
    return merged
