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

REPO_ROOT = Path(__file__).resolve().parents[2]
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


@fetcher("freedomhouse", "core_world_risk_poll_2019__freedom_house.csv")
def freedom_house_2020():
    """Freedom House, Freedom in the World 2020 edition (WRP 2019 report, Chapter 2).

    Terms: free for non-commercial use with attribution; commercial use needs Freedom House's
    permission.
    """
    url = "https://freedomhouse.org/sites/default/files/2020-02/2020_All_Data_FIW_2013-2020.xlsx"
    fh = pd.read_excel(io.BytesIO(download(url)), sheet_name=1, skiprows=1)
    fh = fh[fh.Edition == 2020]
    wrp = pd.read_parquet(REPO_ROOT / "WRP_2019" / "WRP_2019.parquet", columns=["COUNTRY_ISO3", "Country"])
    iso3 = wrp.drop_duplicates("COUNTRY_ISO3").set_index("Country").COUNTRY_ISO3.to_dict()
    # Freedom House names that differ from the poll's. Palestine has two Freedom House
    # entries (West Bank, Gaza Strip) and is left unmatched.
    iso3.update({"Bosnia and Herzegovina": "BIH", "Cote d'Ivoire": "CIV", "Congo (Brazzaville)": "COG",
                 "The Gambia": "GMB"})
    return pd.DataFrame({
        "country": fh["Country/Territory"], "iso3": fh["Country/Territory"].map(iso3), "c_t": fh["C/T"],
        "edition": fh.Edition, "status": fh.Status, "pr": fh.PR, "cl": fh.CL, "total": fh.Total,
    })


@fetcher("who_seatbelt", "core_world_risk_poll_2019__who_seatbelt_laws.csv")
def who_seatbelt_laws():
    """WHO Global status report on road safety 2018, Table A7: seat-belt laws (WRP 2019, Chapter 4).

    Parsed from the report PDF, so it needs poppler's pdftotext. Licence: CC BY-NC-SA 3.0 IGO.
    """
    import json
    import re
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("pdftotext"):
        raise RuntimeError("needs pdftotext (poppler-utils) to read the WHO report PDF")
    pdf_url = "https://iris.who.int/server/api/core/bitstreams/9c866a4e-fda7-43bd-96df-27d7c3b509bc/content"
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "gsrrs2018.pdf"
        pdf.write_bytes(download(pdf_url))
        subprocess.run(["pdftotext", "-layout", str(pdf), str(pdf.with_suffix(".txt"))], check=True,
                       stderr=subprocess.DEVNULL)
        lines = pdf.with_suffix(".txt").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if "TABLE A7: SEAT-BELT" in line)
    end = next(i for i, line in enumerate(lines) if i > start and "TABLE A8" in line)
    row = re.compile(r"^\s*(\S.*?)\s{2,}(Yes|No)[a-z]?\s+(Yes|No|—)[a-z]?\s+(Yes|No|—)[a-z]?\s+(Yes|No|—)[a-z]?\s*$")
    rows = [m.groups() for line in lines[start:end] if (m := row.match(line))]

    gho = json.loads(download("https://ghoapi.azureedge.net/api/DIMENSION/COUNTRY/DimensionValues"))["value"]
    iso3 = {r["Title"]: r["Code"] for r in gho}
    iso3.update({"Côte d’Ivoire": "CIV", "Lao People’s Democratic Republic": "LAO", "Netherlands": "NLD",
                 "Republic of Macedonia": "MKD", "Turkey": "TUR", "United Kingdom": "GBR",
                 "West Bank and Gaza Strip": "PSE"})
    blank = {"—": ""}
    return pd.DataFrame([{
        "iso3": iso3[name], "who_country": name, "national_law": law,
        "drivers": blank.get(drv, drv), "front_seat": blank.get(front, front), "rear_seat": blank.get(rear, rear),
        "all_occupants": "Yes" if (law, drv, front, rear) == ("Yes", "Yes", "Yes", "Yes") else "No",
    } for name, law, drv, front, rear in rows])


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
