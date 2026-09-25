"""Download the non-poll data that is not redistributed in this repository.

Run from the repository root:
    python reports/external/fetch_external.py              # every source
    python reports/external/fetch_external.py wjp ndgain   # some sources

Files are written to reports/external/downloaded/, which git ignores. The
report scripts find them there; without them, the findings that need them
are reported as EXTERNAL_ONLY. reports/external/README.md lists every
source, its licence and why it is or is not committed.

Requires pandas and openpyxl (for Excel files): pip install pandas openpyxl
Providers revise their data, so a fresh download can differ slightly from
what a report used; each fetcher pins the release the report used where the
provider keeps it online.
"""

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

DOWNLOADED = Path(__file__).resolve().parent / "downloaded"
FETCHERS = {}


def fetcher(key, filename):
    """Register a function that returns the DataFrame to save as `filename`."""
    def register(fn):
        FETCHERS[key] = (filename, fn)
        return fn
    return register


def download(url, referer=None):
    headers = {"User-Agent": "Mozilla/5.0 (World Risk Poll report reproduction)"}
    if referer:
        headers["Referer"] = referer
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
        return r.read()


@fetcher("wjp", "core_a_digital_world__wjp_rule_of_law_index_2021.csv")
def wjp_rule_of_law_index_2021():
    """World Justice Project Rule of Law Index 2021, overall score (A Digital World, Chart 3.3).

    Terms: free to download; WJP asks users to cite the WJP Rule of Law Index. No open licence.
    """
    url = ("https://worldjusticeproject.org/rule-of-law-index/downloads/"
           "2025_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx")
    sheet = pd.read_excel(io.BytesIO(download(url)), sheet_name="WJP ROL Index 2021 Scores",
                          header=None, index_col=0)
    return pd.DataFrame({
        "country": sheet.loc["Country"].values,
        "iso3": sheet.loc["Country Code"].values,
        "wjp_rule_of_law_index_2021": sheet.loc["WJP Rule of Law Index: Overall Score"].astype(float).values,
    })


@fetcher("ndgain", "core_alone_together__ndgain_vulnerability.csv")
def ndgain_vulnerability():
    """ND-GAIN Country Index 2024 release, vulnerability score by year (Alone Together, X57-X58).

    Terms: described as free and open-access, with no formal licence; cite the Notre Dame
    Global Adaptation Initiative Country Index (ND-GAIN), University of Notre Dame.
    """
    url = "https://gain.nd.edu/assets/581929/nd_gain_countryindex_2024.zip"
    page = "https://gain.nd.edu/our-work/country-index/download-data/"
    with zipfile.ZipFile(io.BytesIO(download(url, referer=page))) as z:
        name = next(n for n in z.namelist() if n.endswith("resources/vulnerability/vulnerability.csv"))
        return pd.read_csv(z.open(name))


def main(keys):
    unknown = [k for k in keys if k not in FETCHERS]
    if unknown:
        sys.exit(f"Unknown source(s): {', '.join(unknown)}. Choose from: {', '.join(FETCHERS)}")
    DOWNLOADED.mkdir(exist_ok=True)
    failed = []
    for key in keys or FETCHERS:
        filename, fn = FETCHERS[key]
        try:
            fn().to_csv(DOWNLOADED / filename, index=False)
            print(f"{key:10s} -> reports/external/downloaded/{filename}")
        except Exception as exc:  # report and carry on with the other sources
            failed.append(key)
            print(f"{key:10s} FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
