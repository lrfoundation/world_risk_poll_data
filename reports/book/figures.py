"""Published figures for the book: look-up, formatting and the list of every figure used."""

import csv
import re
from functools import lru_cache
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parents[1]
REF = re.compile(r"\{([A-Za-z0-9_]+)(?::(words|abs))?\}")


@lru_cache(maxsize=None)
def published(folder):
    """finding_id -> row of the report's published_figures.csv."""
    with open(REPORTS_DIR / folder / "published_figures.csv", encoding="utf-8-sig", newline="") as f:
        return {row["finding_id"]: row for row in csv.DictReader(f)}


@lru_cache(maxsize=None)
def statuses(folder):
    """finding_id -> status in the report's RESULTS.md (MATCH, WITHIN_TOLERANCE and so on)."""
    out = {}
    for line in (REPORTS_DIR / folder / "RESULTS.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 8 and cells[1] and cells[1] not in ("ID", "---"):
            out[cells[1]] = (cells[5], cells[7])  # Python value, status
    return out


class Figures:
    """The figures of one report, remembering which ones the book used."""

    def __init__(self, folder, used):
        self.folder, self.rows, self.used = folder, published(folder), used

    def row(self, fid):
        if fid not in self.rows:
            raise KeyError(f"{fid} is not in {self.folder}/published_figures.csv")
        self.used.setdefault((self.folder, fid), self.rows[fid])
        return self.rows[fid]

    def number(self, fid):
        return float(self.row(fid)["published_value"])

    def text(self, fid, style=None):
        """The value as the report printed it: 34, 20.9, 125,911."""
        raw = self.row(fid)["published_value"].strip()
        try:
            value = float(raw)
        except ValueError:
            return raw
        if style == "abs":
            value, raw = abs(value), raw.lstrip("-")
        if style == "words" and abs(value) >= 1e6:
            for size, word in ((1e9, "billion"), (1e6, "million")):
                if abs(value) >= size:
                    return f"{value / size:g} {word}"
        if value == int(value) and "." not in raw:
            return f"{int(value):,}" if abs(value) >= 10000 else str(int(value))
        return raw

    def fill(self, text):
        """Replace every {ID} in text with its published value."""
        return REF.sub(lambda m: self.text(m.group(1), m.group(2)), text)
