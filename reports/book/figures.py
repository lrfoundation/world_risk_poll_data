"""Published figures for the book: look-up, formatting and the list of every figure used."""

import csv
import re
from functools import lru_cache
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parents[1]
REF = re.compile(r"\{([A-Za-z0-9_]+)(?::(words|abs))?\}")
ACROSS = re.compile(r"\{(\w+:\w+)(?::(words|abs|rank|word))?\}")      # a finding of one of several reports: {report:ID}
NUMBERS = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
RANKS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]


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
        if style == "rank":
            return RANKS[int(value) - 1]
        if style == "word":
            return NUMBERS[int(value) - 1]
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


class Sources:
    """The figures of several reports, for writing that reads across them.

    A finding is named "report:ID", where report is a key of `folders` (short name -> report folder).
    """

    def __init__(self, folders, used):
        self.used = used
        self.reports = {name: Figures(folder, used) for name, folder in folders.items()}

    def of(self, ref):
        name, _, fid = ref.partition(":")
        if name not in self.reports:
            raise KeyError(f"{ref}: no report is called {name!r} (the reports are {', '.join(self.reports)})")
        return self.reports[name], fid

    def number(self, ref):
        report, fid = self.of(ref)
        return report.number(fid)

    def text(self, ref, style=None):
        report, fid = self.of(ref)
        return report.text(fid, style)

    def fill(self, text):
        """Replace every {report:ID} in text with its published value."""
        return ACROSS.sub(lambda m: self.text(m.group(1), m.group(2)), text)
