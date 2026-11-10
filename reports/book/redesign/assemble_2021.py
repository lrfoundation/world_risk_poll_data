"""Assemble the content files of the core reports of the 2021 poll.

    python reports/book/redesign/assemble_2021.py 2021_a_changed_world

Each of these reports stays one report, with its own preface, executive summary,
chapters and concluding remarks, in the original order. core_2021.py reads the
PDF; this script arranges what it finds as content/<report>.md, gives every
chart its specification from PLANS, and takes each chart's title, question text
and notes from the PDF. A chart with no specification yet is placed as a picture
of the original, so a draft is complete from the first run.
"""

import csv
import json
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import core_2021  # noqa: E402
from assemble_2019 import REGIONS as REGIONS_2019, join_urls, open_ended  # noqa: E402

REGIONS = dict(REGIONS_2019, eastern_africa="Eastern Africa", latin_america="Latin America & Caribbean")
NOTE_STARTS = r"(\*|†|Don’t know|Don't know|Due to rounding|Values under|Note:|Total may|Percentages may)"
PREFIX = {"Chart": "", "Table": "T", "Map": "M"}


class Ids:
    """The finding IDs of one report, in the order of its CSV (the printed order of each chart)."""

    def __init__(self, folder):
        with open(HERE.parents[1] / folder / "published_figures.csv", encoding="utf-8") as f:
            self.ids = [row["finding_id"] for row in csv.DictReader(f)]

    def keys(self, prefix, suffix="", names=None):
        """The middle parts of the IDs that start with prefix and end with suffix, in CSV order."""
        out = []
        for fid in self.ids:
            if fid.startswith(prefix) and fid.endswith(suffix):
                key = fid[len(prefix):len(fid) - len(suffix)]
                if key not in out and (names is None or key in names):
                    out.append(key)
        return out

    def regions(self, prefix, suffixes):
        """Rows by region: [label, [prefix + region + _suffix, ...]], or [label, id] when suffixes is None."""
        keys = self.keys(prefix, "_" + suffixes[0] if suffixes else "", REGIONS)
        assert keys, prefix
        return [[REGIONS[k], [f"{prefix}{k}_{s}" for s in suffixes] if suffixes else f"{prefix}{k}"] for k in keys]

    def named(self, prefix, suffix, names):
        """[(label, key)] for the keys between prefix and suffix, in CSV order."""
        return [(names[k], k) for k in self.keys(prefix, suffix, names)]

    def check(self, spec):
        """Every finding ID a specification names must be in the CSV."""
        def walk(value):
            if isinstance(value, str) and re.fullmatch(r"[CTMX]\d\w*", value):
                assert value in self.ids, f"no finding {value}"
            elif isinstance(value, (list, tuple)):
                for v in value:
                    walk(v)
        for field in ("rows", "panels", "top", "bottom"):
            walk(spec.get(field, []))


SAFE3_KEYS = ("more", "same", "less")
SAFE4 = dict(series=["More safe", "About as safe", "Less safe", "Don’t know/refused"], colours=["green", "teal", "fuchsia", "grey"])
THREAT4 = dict(series=["Very serious threat", "Somewhat serious threat", "Not a threat at all", "Don’t know/refused"], colours=["fuchsia", "green", "teal", "grey"])
RISKS = {
    "road": "Road-related accidents/injuries", "crime": "Crime/violence", "health": "Personal health (non-Covid-19)", "covid": "Covid-19/coronavirus related",
    "none": "Nothing/no risks", "financial": "Financial: not having enough money", "economic": "Economic: unemployment, high prices", "other": "Other",
    "climate": "Climate change or severe weather", "work": "Work-related injuries", "war": "War/terrorism", "politics": "Politics/corruption",
    "non_road": "Non-road transportation injuries", "cooking": "Cooking or other household accidents/injuries", "mental": "Mental stress/exhaustion",
    "disasters": "Non-weather-related natural disasters", "drugs": "Drugs/alcohol/smoking", "hunger": "Hunger/lack of food", "pollution": "Pollution",
    "water": "Unsafe water supply", "internet": "Internet/technology-related risks", "food": "Unsafe or contaminated food", "drowning": "Drowning",
}
RISK_COLUMNS = dict(RISKS, health="Personal health, non-Covid-19")
T1_2 = ("covid", "health", "road", "crime", "financial", "economic", "cooking", "none")
MONEY = {"comfortable": "living comfortably", "getting_by": "getting by", "difficult": "finding it difficult", "very_difficult": "finding it very difficult"}
AGES = {"15_29": "Age 15-29", "30_49": "Age 30-49", "50_64": "Age 50-64", "65plus": "Age 65+"}
QUINTILES = {"bottom": "Bottom 20% income", "second": "Second 20%", "middle": "Middle 20%", "fourth": "Fourth 20%", "top": "Top 20% income"}
EDUCATION = {"primary": "Primary education or less (0-8 years)", "secondary": "Secondary education (9-15 years)", "post_secondary": "Post-secondary education (16 years or more)"}
SCATTER = "the original plots every country without printing its value"

PLANS = {}


def urls(text):
    """Web addresses that the PDF broke across lines, joined up again."""
    text = join_urls(text)
    while True:
        joined = re.sub(r"(https?://\S*[/_-]) (?=[\w%])", r"\1", text)
        if joined == text:
            return text
        text = joined


def plan(key, **fields):
    PLANS[key] = fields


# ---------------------------------------------------------------- from items to content blocks

def sections(items):
    out, current = [], None
    for item in items:
        text = item["text"]
        if item["kind"] == "part":
            chapter = re.fullmatch(r"Chapter (\d+)", text)
            current = dict(kind="chapter" if chapter else "front", title=None if chapter else text, items=[])
            out.append(current)
        elif item["kind"] == "title":
            if current and current["kind"] == "chapter" and current["title"] is None:
                current["title"] = text
            else:
                seen_chapter = any(s["kind"] == "chapter" for s in out)
                current = dict(kind="back" if seen_chapter else "front", title=text, items=[])
                out.append(current)
        elif current is not None:
            current["items"].append(item)
    return out


def small_print(lines):
    """(question text, notes) of the small print under a chart."""
    question, notes = [], []
    for line in lines:
        (notes if notes or re.match(NOTE_STARTS, line) else question).append(line)
    text = re.sub(r"^Survey questions?: ?", "", " ".join(question))
    return text.strip(), " ".join(notes).strip()


def content(section, charts, doc, drop=(), heads=("# ", "## ")):
    """A section's items as content blocks (strings, and dicts for charts)."""
    out, chart, inside, last_small = [], None, False, None
    for item in section["items"]:
        kind, text = item["kind"], item["text"]
        if inside and item["page"] != chart["_page"]:
            inside = False
        if text in drop:
            continue
        if kind == "label":
            m = re.fullmatch(r"(Chart|Table|Map) (\d+\.\d+)", text)
            assert m, text
            chart = dict(id=PREFIX[m.group(1)] + m.group(2), number=m.group(2), _page=item["page"], _box=[item["x0"], item["y0"], item["x1"], item["y1"], item["y1"]])
            chart["as"] = m.group(1)
            inside, last_small = True, None
            out.append(chart)
        elif kind == "caption":
            if chart is None or not inside:
                continue
            if "title" not in chart:
                chart["title"] = text
                chart["_box"][0] = min(chart["_box"][0], item["x0"])
            else:
                chart["subtitle"] = (chart.get("subtitle", "") + " " + text).strip()
            chart["_box"][3] = chart["_box"][4] = item["y1"] + 2
        elif kind == "sub":
            if inside:
                chart["subtitle"] = (chart.get("subtitle", "") + " " + text).strip()
                chart["_box"][3] = chart["_box"][4] = item["y1"] + 2
            else:
                out.append(f"**{text}**")
        elif kind == "small":
            if chart is None:
                continue
            below = last_small is not None and item["page"] == last_small["page"] and 0 <= item["y0"] - last_small["y1"] < 8
            if text.startswith("Survey question") or below:
                question, notes = small_print(item["lines"])
                if below and not text.startswith("Survey question"):
                    question, notes = "", text
                if question:
                    chart["question"] = (chart.get("question", "") + " " + question).strip()
                if notes:
                    chart["note"] = (chart.get("note", "") + " " + notes).strip()
                chart["_box"][3] = item["y0"] - 3
                chart["_box"][2] = max(chart["_box"][2], item["x1"])
                inside, last_small = False, item
        elif kind in ("h1", "h2"):
            inside = False
            out.append(heads[kind == "h2"] + text)
        elif kind == "quote":
            if not inside:
                out.append("> " + text.strip("“”\" "))
        elif kind == "p":
            if inside:
                continue                         # the lettering of the chart, which the specification draws
            bullet = re.match(r"• ?", text)
            finding = re.match(r"(\d+)\) ?", text)
            style = item.get("style", "")
            if bullet or finding:
                body = text[(bullet or finding).end():]
                if style == "*":
                    body = f"*{body}*"
                elif style == "**" and finding:
                    body = f"**{body}**"
                out.append(("- " if bullet else f"{finding.group(1)}. ") + body)
                continue
            # A paragraph the original broke over a page, a column or a chart: put it back together.
            k = next((k for k in range(len(out) - 1, -1, -1) if isinstance(out[k], str)), None)
            if k is not None and not out[k].startswith(("#", ">", "*")) and open_ended(out[k].rstrip("*")) and style != "*":
                # (a list item with no full stop is only continued by text that starts in lower case)
                if text[:1].islower() or (not out[k + 1:] and not re.match(r"- |\d+\. ", out[k])):
                    out[k] += " " + text
                    continue
            out.append(f"*{text}*" if style == "*" else text)
    # A chart with no specification yet is a picture of the original.
    for block in out:
        if isinstance(block, dict):
            box, page = block.pop("_box"), block.pop("_page")
            spec = charts.get(block["id"])
            if spec is None:
                spec = dict(kind="original", why="it has not been redrawn yet")
                block["_todo"] = True
            if spec["kind"] == "original" and "clip" not in spec:
                # the picture runs from under the chart's title to the top of its small print
                left = box[0] - 4
                spec = dict(spec, page=page, clip=[round(left), round(box[4]), round(left + 470), round(box[3])])
            for field in ("title", "subtitle", "question", "note"):
                if field in spec and spec[field] is None:
                    block.pop(field, None)
            block.update({k: v for k, v in spec.items() if v is not None})
            if spec.get("subtitle") and block.get("title", "").endswith(spec["subtitle"]):
                block["title"] = block["title"][:-len(spec["subtitle"])].strip()       # the PDF sets both in one block
    return out


def dump(blocks):
    return ["```chart\n" + json.dumps(b, ensure_ascii=False, indent=1) + "\n```" if isinstance(b, dict) else b for b in blocks]


def assemble(key):
    p = PLANS[key]
    ids = Ids(p["folder"])
    p["charts"] = p["charts"](ids)
    for spec in p["charts"].values():
        ids.check(spec)
    doc = pymupdf.open(HERE.parent / ".cache" / "pdfs" / p["pdf"])
    items, notes = core_2021.stream(doc, *p["pages"])
    parts = sections(items)
    drop = set(p.get("drop", ()))

    edits = list(p.get("edits", []))
    meta = dict(
        key=key, wave=2021, folder=p["folder"], pdf=p["pdf"], title=p["title"], subtitle=p["subtitle"],
        series=f"Core report of the 2021 poll, first published {p['published']}",
        source=p["source"], copyright=p["copyright"], running=f"Re-set in 2026 from the report of {p['published']}",
        cover_image=p["cover_image"], numbering="chapter", contents_first=True, margins=[55, 800], edits=edits)
    for extra in ("chart_note", "queries", "pending"):
        if p.get(extra):
            meta[extra] = p[extra]

    out, todo, seen, chapter = [], [], set(), 0
    for section in parts:
        title = p.get("titles", {}).get(section["title"], section["title"])
        if section["kind"] == "chapter":
            chapter += 1
            opener = p["chapters"][chapter - 1]
            out.append(f"::chapter {title} | {opener['big']} | {opener['caption']}")
            blocks = content(section, p["charts"], doc, drop)
        else:
            out.append(f"::{section['kind']} {title}")
            has_h1 = any(i["kind"] == "h1" for i in section["items"])
            blocks = content(section, p["charts"], doc, drop, heads=("## ", "### ") if has_h1 else ("## ", "## "))
            blocks += p.get("after", {}).get(section["title"], [])
        for block in blocks:
            if isinstance(block, dict):
                seen.add(block["id"])
                if block.pop("_todo", False):
                    todo.append(block["id"])
        out += dump(blocks)
    missing = set(p["charts"]) - seen
    assert not missing, f"charts in the plan that the PDF never reached: {sorted(missing)}"

    text = "\n\n".join(out)
    for old, new in p.get("replace", {}).items():
        assert text.count(old) == 1, (text.count(old), old)
        text = text.replace(old, new)
    text = "---\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n---\n\n" + text
    text += "\n\n" + "\n\n".join(f"[^{n}]: {urls(body)}" for n, body in sorted(notes.items())) + "\n"
    (HERE / "content" / f"{key}.md").write_text(text, encoding="utf-8")
    print(f"{key}.md: {len(out)} blocks, {len(seen)} charts ({len(todo)} still pictures of the original: {' '.join(todo)}), {len(notes)} notes")


# ---------------------------------------------------------------- the reports

plan(
    "2021_a_changed_world",
    folder="WRP_2021/core_a_changed_world", pdf="core_a_changed_world.pdf", pages=(3, 50),
    title="A Changed World?", subtitle="Perceptions and experiences of risk in the Covid age", published="July 2022",
    source="World Risk Poll 2021: A Changed World? Perceptions and experiences of risk in the Covid age (Lloyd's Register Foundation, July 2022)",
    copyright="Copyright © 2022 Lloyd's Register Foundation. All rights reserved.",
    cover_image=[10, 0],
    chapters=[
        dict(big="34%", caption="of people worldwide felt ‘less safe’ in 2021 than they did five years earlier, up from 30% in 2019"),
        dict(big="24%", caption="of people worldwide said they or someone they know had experienced serious harm from the work they did"),
        dict(big="7%", caption="of people worldwide named Covid-19 as the greatest source of risk to their safety"),
        dict(big="25%", caption="of people worldwide said they or someone they know had experienced serious harm from mental health issues, up from 20% in 2019"),
        dict(big="67%", caption="of people viewed climate change as a threat to their country, down slightly from 69% in 2019"),
    ],
    after={"Preface": ["**Dr. Ruth Boumphrey**, Chief Executive, Lloyd’s Register Foundation"]},
    edits=[
        "The headline figure on each chapter's opening page is taken from that chapter's key findings; the original opens each chapter with a photograph.",
        "The sentences set in italics beside a green bar are the ones the original repeats in large type beside its photographs, in their original places.",
        "The name under the portrait in the preface is set as a line at the end of the preface.",
        "Footnotes are gathered as numbered references at the back, with their original numbers. Web addresses that the original broke across lines have been joined up.",
    ],
    pending="The three appendices of the original (the questionnaire, the references listed again by chapter, and the list of regions) are not in this draft.",
    charts=lambda ids: {
        "1.1": dict(kind="stacked", rows=[[y, [f"C1_1_{y}_{k}" for k in ("more", "same", "less", "dk")]] for y in ("2019", "2021")], **SAFE4),
        "1.2": dict(kind="stacked_pair", panels=["2019", "2021"], extra="‘Less safe’ difference", extra_unit=" pts",
                    rows=[[label, [f"C1_2_{k}_2019_{x}" for x in SAFE3_KEYS], [f"C1_2_{k}_2021_{x}" for x in SAFE3_KEYS], f"C1_2_{k}_diff"]
                          for label, k in ids.named("C1_2_", "_diff", REGIONS)],
                    series=SAFE4["series"][:3], colours=SAFE4["colours"][:3]),
        "T1.1": dict(kind="matrix", columns=["Less safe", "About as safe", "More safe"] * 2 + ["‘Less safe’ difference"], groups=[["2019", 3], ["2021", 3], ["", 1]],
                     unit=["%"] * 6 + [" pts"], plain=[6],
                     rows=[[name, [f"T1_1_{iso}_{y}_{k}" for y in ("2019", "2021") for k in ("less", "same", "more")] + [f"T1_1_{iso}_diff"]]
                           for iso, name in (("MMR", "Myanmar"), ("ARM", "Armenia"), ("VNM", "Vietnam"), ("NGA", "Nigeria"), ("TUR", "Turkey"))]),
        "1.3": dict(kind="grouped", zero="<0.5", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[RISKS[k], [i if i in ids.ids else None for i in (f"C1_3_{k}_2019", f"C1_3_{k}_2021")]] for k in ids.keys("C1_3_", "_2021")]),
        "1.4": dict(kind="hbar", rows=[[RISKS[k], f"C1_4_{k}"] for k in ids.keys("C1_4_")]),
        "T1.2": dict(kind="matrix", zero="<0.5", columns=[RISK_COLUMNS[k] for k in T1_2],
                     rows=[[label, [f"T1_2_{k}_{c}" for c in T1_2]] for label, k in ids.named("T1_2_", "_covid", REGIONS)]),
        "1.5": dict(kind="hbar", rows=ids.regions("C1_5_", None)),
        "T2.1": dict(kind="matrix", columns=["Very worried", "Have experienced or know someone who has experienced", "Ratio"] * 2, groups=[["2019", 3], ["2021", 3]],
                     unit=["%", "%", ":1"] * 2, decimals=[0, 0, 1] * 2, plain=[2, 5],
                     rows=[[label, [i if i in ids.ids else None for i in (f"T2_1_{k}_{y}_{c}" for y in ("2019", "2021") for c in ("very_worried", "experienced", "ratio"))]]
                           for k, label in (("work", "The work you do*"), ("mental", "Mental health issues"), ("food", "The food you eat"),
                                            ("traffic", "Traffic/roadside accidents*"), ("water", "The water you drink"), ("weather", "Severe weather events"),
                                            ("crime", "Violent crime"))]),
        "2.1": dict(kind="grouped", series=["Very worried about work-related harm", "Personally experienced work-related harm"], colours=["fuchsia", "navy"],
                    rows=ids.regions("C2_1_", ["very_worried", "experienced"])),
        "2.2": dict(kind="original", why=SCATTER, subtitle="Results among employed people in each country or territory"),
        "2.3": dict(kind="vgrouped", series=[f"Among those {x}" for x in MONEY.values()],
                    panels=[["", [["Have personally experienced work-related harm in the past two years", [f"C2_3_experienced_{k}" for k in MONEY]],
                                  ["Very worried about work-related harm", [f"C2_3_very_worried_{k}" for k in MONEY]]]]]),
        "T2.2": dict(kind="matrix", columns=[x[0].upper() + x[1:] for x in MONEY.values()],
                     rows=[[label, [f"T2_2_{k}_{c}" for c in MONEY]] for label, k in ids.named("T2_2_", "_comfortable", REGIONS)]),
        "2.4": dict(kind="original", why=SCATTER),
        "3.1": dict(kind="vgrouped", series=["Personal health (non-Covid-19)", "Covid-19/coronavirus related"], colours=["navy", "fuchsia"],
                    panels=[["", [[label, [f"C3_1_{k}_health", f"C3_1_{k}_covid"]] for k, label in AGES.items()]]]),
        "T3.1": dict(kind="matrix", zero="<0.5", columns=["Overall"] + list(QUINTILES.values()),
                     rows=[[label, [f"T3_1_{k}_{c}" for c in ["overall"] + list(QUINTILES)]] for label, k in ids.named("T3_1_", "_overall", REGIONS)]),
        "3.2": dict(kind="original", why=SCATTER),
        "M3.1": dict(kind="region_map", box=[91, -11.5, 128, 29],
                     rows=[[name, iso, f"M3_1_{iso}"] for iso, name in (("MMR", "Myanmar"), ("LAO", "Laos"), ("VNM", "Vietnam"), ("THA", "Thailand"), ("PHL", "Philippines"),
                                                                       ("MYS", "Malaysia"), ("KHM", "Cambodia"), ("SGP", "Singapore"), ("IDN", "Indonesia"))]),
        "4.1": dict(kind="grouped", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[label, [f"C4_1_{k}_2019", f"C4_1_{k}_2021"]] for k, label in (("weather", "Severe weather events"), ("mental", "Mental health issues"),
                                                                                       ("crime", "Violent crime"), ("food", "Eating food"), ("water", "Drinking water"))]),
        "4.2": dict(kind="grouped", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[label, [f"C4_2_{k}_2019", f"C4_2_{k}_2021"]] for k, label in (("weather", "Severe weather events"), ("crime", "Violent crime"),
                                                                                       ("mental", "Mental health issues"), ("food", "The food you eat"), ("water", "The water you drink"))]),
        "4.3": dict(kind="original", why="the original plots every country without printing its value; the four income-group totals it does print are in the text"),
        "4.4": dict(kind="vgrouped", series=["Among those very worried about severe weather", "Among those somewhat worried", "Among those not worried about severe weather"],
                    panels=[["", [[REGIONS[k], [f"C4_4_{k}_{c}" for c in ("very", "somewhat", "not")]] for k in ids.keys("C4_4_", "_very")]]]),
        "4.5": dict(kind="grouped", series=list(QUINTILES.values()),
                    rows=[[label, [f"C4_5_{k}_{c}" for c in QUINTILES]] for k, label in (("weather", "Severe weather events"), ("work", "The work you do"), ("mental", "Mental health issues"),
                                                                                       ("road", "Road-related accidents/injuries"), ("food", "Eating food"), ("water", "Drinking water"),
                                                                                       ("crime", "Violent crime"))]),
        "5.1": dict(kind="stacked", rows=[[y, [f"C5_1_{y}_{k}" for k in ("very", "somewhat", "not", "dk")]] for y in ("2019", "2021")], **THREAT4),
        "5.2": dict(kind="stacked", rows=[[label, [f"C5_2_{k}_{c}" for c in ("very", "somewhat", "not", "dk")]] for k, label in EDUCATION.items()], **THREAT4),
        "T5.1": dict(kind="matrix", columns=["Not a threat", "Don’t know", "Total*"] * 2, groups=[["2019", 3], ["2021", 3]],
                     rows=[[label, [f"T5_1_{k}_{y}_{c}" for y in ("2019", "2021") for c in ("not", "dk", "total")]] for label, k in ids.named("T5_1_", "_2019_not", REGIONS)]),
        "5.3": dict(kind="vgrouped", series=["Among those who had experienced harm from severe weather", "Among those who know someone who experienced harm from severe weather",
                                             "Among those who neither had experienced/know someone who experienced harm from severe weather"],
                    panels=[["", [[label, [f"C5_3_{k}_{c}" for c in ("experienced", "know_someone", "neither")]]
                                  for k, label in (("total", "Total"), ("primary", "Primary education or less (0-8 years)"), ("secondary", "Secondary education (9-15 years)"),
                                                   ("post_secondary", "Post-secondary education (16+ years)"))]]]),
    },
)


if __name__ == "__main__":
    assemble(sys.argv[1])
