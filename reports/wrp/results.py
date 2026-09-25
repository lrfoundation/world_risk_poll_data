"""Collect a report's reproduced figures and compare them with the published ones.

Each report folder holds:

- published_figures.csv  one row per published finding (the reference)
- reproduce.py / .R      one registered function per finding or chart
- output/                reproduced_python.csv / reproduced_r.csv (git-ignored)
- RESULTS.md             published vs Python vs R, written by reproduce.py

A registered function returns either one value, recorded under its
finding_id, or a dict/Series of values, recorded as "<finding_id>_<key>"
(for example one value per country in a chart).
"""

import math
import sys
from pathlib import Path

import pandas as pd

from .gallup import GallupDataRequired

STATUS_ORDER = ["MATCH", "WITHIN_TOLERANCE", "DIFFERENT", "GALLUP_ONLY", "ERROR", "NOT_RUN"]


def _key(key):
    """'F07' + key -> 'F07_1', 'F07_1_2' for (1, 2); 1.0 is written as 1."""
    parts = key if isinstance(key, tuple) else (key,)
    parts = [int(p) if isinstance(p, float) and p.is_integer() else p for p in parts]
    return "_".join(str(p) for p in parts)


def _decimals(text):
    return len(text.split(".")[1]) if "." in text else 0


def _is_number(text):
    try:
        float(text)
        return True
    except (TypeError, ValueError):
        return False


def compare(published, reproduced, tolerance):
    """Status of one numeric or text finding against its published value."""
    if not _is_number(published):
        return "MATCH" if str(reproduced).strip().lower() == published.strip().lower() else "DIFFERENT"
    pub, rep = float(published), float(reproduced)
    if math.isnan(rep):
        return "DIFFERENT"
    # MATCH: the reproduced value rounds to exactly the published figure.
    if round(rep, _decimals(published)) == pub:
        return "MATCH"
    return "WITHIN_TOLERANCE" if abs(rep - pub) <= tolerance + 1e-9 else "DIFFERENT"


class Report:
    """Registry of the findings a reproduce.py script computes."""

    def __init__(self, script_path):
        self.dir = Path(script_path).resolve().parent
        self.published = pd.read_csv(
            self.dir / "published_figures.csv", dtype=str, keep_default_na=False
        )
        self._functions = []

    def finding(self, finding_id):
        """Decorator registering a function that computes `finding_id`."""
        def register(fn):
            self._functions.append((finding_id, fn))
            return fn
        return register

    def _ids_for(self, finding_id):
        ids = self.published["finding_id"]
        return list(ids[(ids == finding_id) | ids.str.startswith(finding_id + "_")]) or [finding_id]

    def run(self):
        """Run every registered finding, write outputs, return an exit code."""
        rows = []
        for finding_id, fn in self._functions:
            try:
                value = fn()
            except GallupDataRequired as exc:
                rows += [(i, "", "GALLUP_ONLY", str(exc)) for i in self._ids_for(finding_id)]
                continue
            except Exception as exc:  # recorded, and makes the script exit non-zero
                rows += [(i, "", "ERROR", f"{type(exc).__name__}: {exc}") for i in self._ids_for(finding_id)]
                continue
            if isinstance(value, pd.DataFrame):
                value = value.stack()
            if isinstance(value, (dict, pd.Series)):
                rows += [(f"{finding_id}_{_key(k)}", v, "ok", "") for k, v in value.items()]
            else:
                rows.append((finding_id, value, "ok", ""))

        out = self.dir / "output"
        out.mkdir(exist_ok=True)
        reproduced = pd.DataFrame(rows, columns=["finding_id", "value", "status", "message"])
        reproduced.to_csv(out / "reproduced_python.csv", index=False)
        table = write_results(self.dir)
        print_summary(table)
        return 1 if (reproduced["status"] == "ERROR").any() else 0


def _load_reproduced(path):
    if not path.exists():
        return None
    return pd.read_csv(path, dtype={"value": str}, keep_default_na=False).set_index("finding_id")


def _fmt(value, published):
    if value == "" or not _is_number(value):
        return value
    digits = _decimals(published) + 1 if _is_number(published) else 3
    return f"{float(value):.{digits}f}"


def build_table(report_dir):
    """Published figures joined to the Python and (if run) R results."""
    report_dir = Path(report_dir)
    published = pd.read_csv(report_dir / "published_figures.csv", dtype=str, keep_default_na=False)
    py = _load_reproduced(report_dir / "output" / "reproduced_python.csv")
    r = _load_reproduced(report_dir / "output" / "reproduced_r.csv")

    records = []
    for _, row in published.iterrows():
        fid, pub = row["finding_id"], row["published_value"]
        tol = float(row["tolerance"]) if row.get("tolerance") else 1.0
        rec = {"finding_id": fid, "page": row.get("page", ""), "description": row["description"],
               "published": pub, "python": "", "r": "", "status": "NOT_RUN", "note": row.get("note", "")}
        if py is not None and fid in py.index:
            p = py.loc[fid]
            if p["status"] == "ok":
                rec["python"] = p["value"]
                rec["status"] = compare(pub, p["value"], tol)
            else:
                rec["status"] = p["status"]
                rec["note"] = rec["note"] or p["message"]
        if r is not None and fid in r.index and r.loc[fid, "status"] == "ok":
            rec["r"] = r.loc[fid, "value"]
            if rec["python"] and _is_number(rec["python"]) and _is_number(rec["r"]):
                if abs(float(rec["python"]) - float(rec["r"])) > 1e-6:
                    rec["note"] = ("Python and R differ. " + rec["note"]).strip()
        records.append(rec)
    return pd.DataFrame(records)


def _title(report_dir):
    readme = Path(report_dir) / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return Path(report_dir).name


def write_results(report_dir):
    """Write RESULTS.md for a report folder and return the comparison table."""
    table = build_table(report_dir)
    counts = table["status"].value_counts()
    lines = [
        f"# Results: {_title(report_dir)}",
        "",
        "Generated by `reproduce.py` (and `reproduce.R` for the R column). Do not edit by hand.",
        "",
        "| Status | Findings |",
        "| --- | --- |",
    ]
    lines += [f"| {s} | {counts[s]} |" for s in STATUS_ORDER if s in counts]
    lines += [f"| **Total** | **{len(table)}** |", ""]
    lines += [
        "MATCH: rounds to the published figure. WITHIN_TOLERANCE: within the row's tolerance "
        "(default ±1 point). GALLUP_ONLY: needs Gallup World Poll data that is not public. "
        "See `published_figures.csv` for each finding's source page.",
        "",
        "| ID | Page | Finding | Published | Python | R | Status | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for _, t in table.iterrows():
        cells = [t["finding_id"], t["page"], t["description"], t["published"],
                 _fmt(t["python"], t["published"]), _fmt(t["r"], t["published"]),
                 t["status"], t["note"]]
        lines.append("| " + " | ".join(str(c).replace("|", "/") for c in cells) + " |")
    (Path(report_dir) / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return table


def print_summary(table):
    counts = table["status"].value_counts()
    summary = ", ".join(f"{s} {counts[s]}" for s in STATUS_ORDER if s in counts)
    print(f"{len(table)} findings: {summary}")
    problems = table[table["status"].isin(["DIFFERENT", "ERROR", "NOT_RUN"])]
    for _, t in problems.iterrows():
        print(f"  {t['status']:<10} {t['finding_id']}: published {t['published']}, "
              f"reproduced {t['python'] or '-'}  {t['note']}", file=sys.stderr)
